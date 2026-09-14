#!/usr/bin/env python3
"""Build conditioned, tagged pools from a finished harvest.

Runs once at the end of harvesting. Reads the sentence bank, the candidate
list, and (if present) the alignment scores, and writes one pool per card in
which every candidate carries its tags and an explicit verdict. WSD then reads
the pool and does WSD only.

    python scripts/condition_pools.py --run-dir <run> [--alignment-floor 0.70]
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from fluency.harvest.alignment import DEFAULT_ALIGNMENT_FLOOR  # noqa: E402
from fluency.harvest.conditioning import (  # noqa: E402
    POOL_VERSION,
    condition_candidate,
    pool_report,
)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-dir", type=Path, required=True)
    parser.add_argument("--alignment", type=Path)
    parser.add_argument("--alignment-floor", type=float, default=DEFAULT_ALIGNMENT_FLOOR)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()

    harvest = args.run_dir / "stages/03_sentence_harvest/output"
    alignment_path = args.alignment or (
        args.run_dir / "stages/03b_alignment/output/alignment.json"
    )
    out = args.out or (args.run_dir / "stages/03c_pools/output/pools.json")

    bank: dict[str, tuple[str, str]] = {}
    with (harvest / "sentence-bank.jsonl").open(encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            row = json.loads(line)
            bank[row["sentence_id"]] = (
                (row.get("target") or {}).get("text") or "",
                (row.get("source") or {}).get("name") or "",
            )

    scores: dict[str, float] = {}
    if alignment_path.exists():
        scores = {
            str(k): float(v)
            for k, v in json.loads(alignment_path.read_text())["scores"].items()
        }
        print(f"alignment: {len(scores):,} scored, floor {args.alignment_floor}")
    else:
        print(f"alignment: no scores at {alignment_path}; variety and hardness only")

    candidates = json.loads((harvest / "candidates.json").read_text(encoding="utf-8"))
    cards = []
    for card in candidates["cards"]:
        conditioned = []
        for item in card.get("candidates", []):
            sentence_id = str(item["sentence_id"])
            text, source = bank.get(sentence_id, ("", ""))
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
