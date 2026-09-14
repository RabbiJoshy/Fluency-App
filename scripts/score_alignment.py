#!/usr/bin/env python3
"""Score every harvested pair for translation alignment, before WSD runs.

Reads a run's sentence bank and candidate list, scores each (target,
translation) pair with LaBSE, and writes one artifact keyed by sentence id.
Pass that file to wsd_execute --alignment so misaligned pairs are dropped
before the execution cap, rather than after an embedding has been spent.

Runs locally on the GPU; no API calls, nothing billed. Measured at ~440
pairs/second on MPS, so a 10,000-card Portuguese harvest (445,770 candidates)
takes about 17 minutes.

    python scripts/score_alignment.py --run-dir <run> [--out <path>]
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from fluency.harvest.alignment import (  # noqa: E402
    DEFAULT_ALIGNMENT_FLOOR,
    read_cache,
    score_pairs,
    write_cache,
)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-dir", type=Path, required=True)
    parser.add_argument("--out", type=Path)
    parser.add_argument("--batch-size", type=int, default=256)
    parser.add_argument("--device")
    parser.add_argument("--floor", type=float, default=DEFAULT_ALIGNMENT_FLOOR)
    args = parser.parse_args()

    harvest = args.run_dir / "stages/03_sentence_harvest/output"
    out = args.out or (args.run_dir / "stages/03b_alignment/output/alignment.json")

    bank: dict[str, tuple[str, str]] = {}
    with (harvest / "sentence-bank.jsonl").open(encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            row = json.loads(line)
            target = (row.get("target") or {}).get("text") or ""
            english = (row.get("translation") or {}).get("text") or row.get("english") or ""
            if target and english:
                bank[row["sentence_id"]] = (target, english)
    print(f"bank: {len(bank):,} sentences")

    candidates = json.loads((harvest / "candidates.json").read_text(encoding="utf-8"))
    needed = {
        str(item["sentence_id"])
        for card in candidates["cards"]
        for item in card.get("candidates", [])
    }
    needed &= bank.keys()

    # Scoring is deterministic per sentence, so a rerun only pays for what is new.
    known = read_cache(out)
    todo = sorted(needed - known.keys())
    print(f"candidates: {len(needed):,} ({len(known):,} cached, {len(todo):,} to score)")
    if todo:
        started = time.time()
        scores = score_pairs(
            [bank[sentence_id] for sentence_id in todo],
            device=args.device,
            batch_size=args.batch_size,
        )
        elapsed = time.time() - started
        print(f"scored {len(todo):,} in {elapsed:.0f}s ({len(todo)/max(elapsed,1e-9):,.0f}/s)")
        known.update(dict(zip(todo, scores)))
    write_cache(out, known)

    values = [known[k] for k in needed if k in known]
    below = sum(1 for v in values if v < args.floor)
    print(f"wrote {out}")
    print(f"below floor {args.floor}: {below:,} of {len(values):,} ({100*below/max(len(values),1):.2f}%)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
