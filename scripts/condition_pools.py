#!/usr/bin/env python3
"""The cleaning step: harvest table in, same table plus tag columns out.

There are three stages, not four. The harvest produces a table of candidates;
this adds columns to it; WSD reads a filtered view. Alignment is not a stage of
its own -- it is one column-producer here alongside variety, hardness and
length. It is merely the expensive one, which is a caching question rather than
an architectural one, and the cache lives outside the run so it is paid once.

Nothing is deleted. A candidate ruled out keeps its row and gains a reason, so
the table stays auditable and a floor stays revisable: when a card comes up
short, why a sentence is missing is exactly what is wanted.

    python scripts/condition_pools.py --run-dir <run> --alignment-floor 0.70
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from fluency.harvest.alignment import (  # noqa: E402
    DEFAULT_ALIGNMENT_FLOOR,
    read_cache,
    score_pairs,
    write_cache,
)
from fluency.harvest.conditioning import (  # noqa: E402
    POOL_VERSION,
    condition_candidate,
    pool_report,
)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-dir", type=Path, required=True)
    parser.add_argument("--alignment-cache", type=Path,
                        help="cross-run score store (default: <workspace>/embeddings/alignment/<lang>.json)")
    parser.add_argument("--skip-alignment", action="store_true",
                        help="tag variety, hardness and length only; leave alignment unscored")
    parser.add_argument("--alignment-floor", type=float, default=DEFAULT_ALIGNMENT_FLOOR)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()

    harvest = args.run_dir / "stages/03_sentence_harvest/output"
    out = args.out or (args.run_dir / "stages/04_pools/output/pools.json")
    language = args.run_dir.resolve().parents[1].name
    cache_path = args.alignment_cache or (
        args.run_dir.resolve().parents[3] / f"embeddings/alignment/{language}.json"
    )

    bank: dict[str, tuple[str, str, str]] = {}
    with (harvest / "sentence-bank.jsonl").open(encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            row = json.loads(line)
            bank[row["sentence_id"]] = (
                (row.get("target") or {}).get("text") or "",
                (row.get("translation") or {}).get("text") or row.get("english") or "",
                (row.get("source") or {}).get("name") or "",
            )

    candidates = json.loads((harvest / "candidates.json").read_text(encoding="utf-8"))
    needed = {
        str(item["sentence_id"])
        for card in candidates["cards"]
        for item in card.get("candidates", [])
    } & bank.keys()

    scores: dict[str, float] = {}
    if not args.skip_alignment:
        import time

        scores = read_cache(cache_path)
        todo = sorted(needed - scores.keys())
        print(f"alignment cache: {cache_path} ({len(scores):,} known)")
        print(f"  {len(needed):,} candidates, {len(todo):,} to score")
        if todo:
            started = time.time()
            fresh = score_pairs([(bank[s][0], bank[s][1]) for s in todo])
            scores.update(dict(zip(todo, fresh)))
            write_cache(cache_path, scores)
            spent = time.time() - started
            print(f"  scored {len(todo):,} in {spent:.0f}s ({len(todo)/max(spent,1e-9):,.0f}/s)")
        print(f"  floor {args.alignment_floor}")
    else:
        print("alignment: skipped; variety, hardness and length only")
    cards = []
    for card in candidates["cards"]:
        conditioned = []
        for item in card.get("candidates", []):
            sentence_id = str(item["sentence_id"])
            text, _translation, source = bank.get(sentence_id, ("", "", ""))
            if not text:
                continue
            conditioned.append(
                condition_candidate(
                    item,
                    text=text,
                    source=source,
                    alignment=scores.get(sentence_id),
                    alignment_floor=args.alignment_floor,
                )
            )
        cards.append(
            {
                "card_id": card["card_id"],
                "display_form": card.get("display_form"),
                "rank": card.get("rank"),
                "candidates": conditioned,
            }
        )

    report = pool_report(cards)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(
        json.dumps(
            {
                "pool_version": POOL_VERSION,
                "language": candidates.get("language"),
                "alignment_floor": args.alignment_floor,
                "report": report,
                "cards": cards,
            },
            ensure_ascii=False,
        )
    )
    print(f"wrote {out}")
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
