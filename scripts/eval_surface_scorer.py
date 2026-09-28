#!/usr/bin/env python3
"""Compare two surface scorers on what cognate mode would actually skip.

Decision 0027: the shipped scorer is provisional. A replacement is judged here,
on words rather than on a single number. For one language and release it
builds the per-sense map with each scorer, applies the app's rule (every shown
sense must be a free cognate; expressions never are), and prints, for the
first N cards, the words each scorer skips that the other keeps.

    PYTHONPATH=src python scripts/eval_surface_scorer.py --language es \
        --release-index <workspace>/releases/es/speech/<id>/app/vocabulary.index.json \
        --a edit-distance/v1 --b legacy-max4/v1

    # any other known language: add --known pl --known-extract <kaikki-Polish.jsonl>
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from fluency.enrichments.card_rules import card_cognate
from fluency.enrichments.cognates import build_app_cognates_by_sense

ROOT = Path(__file__).resolve().parents[1]


def skipped(rows: list[dict], payload: dict, code: str) -> dict[str, tuple[float, str | None]]:
    """The cards the app would set aside for a reader of ``code``."""

    cutoff = payload["thresholds"][code]
    out = {}
    for row in rows:
        surface = str(row.get("word") or "").lower()
        verdict = card_cognate(row, payload["scores"].get(surface), code, payload["matches"].get(surface))
        if verdict and verdict[0] >= cutoff:
            out[row["word"]] = verdict
    return out


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--language", required=True)
    parser.add_argument("--release-index", type=Path, required=True)
    parser.add_argument("--a", required=True, help="scorer id, e.g. edit-distance/v1")
    parser.add_argument("--b", required=True)
    parser.add_argument("--first", type=int, default=2000)
    parser.add_argument("--known", default="en", help="known language, e.g. pl")
    parser.add_argument("--known-extract", type=Path, help="its English-glossed extract (not for en)")
    parser.add_argument("--workspace", type=Path, default=ROOT.parent / "Fluency-Workspace")
    args = parser.parse_args()

    rows = json.loads(args.release_index.read_text(encoding="utf-8"))
    rows = sorted(rows, key=lambda row: row.get("rank") or 10**9)[: args.first]
    results = {}
    for scorer in (args.a, args.b):
        payload = build_app_cognates_by_sense(
            language=args.language,
            config_root=ROOT / "config",
            raw_root=args.workspace / "raw",
            release_rows=rows,
            known_extracts={args.known: args.known_extract},
            surface_scorer=scorer,
        )
        results[scorer] = skipped(rows, payload, args.known)
    a, b = results[args.a], results[args.b]
    print(f"{args.language} read by {args.known}, first {len(rows)} cards: {args.a} skips {len(a)}, {args.b} skips {len(b)}")
    for name, mine, other in ((args.a, a, b), (args.b, b, a)):
        only = [f"{w}({mine[w][1]} {mine[w][0]:.2f})" for w in mine if w not in other]
        print(f"\nonly {name} ({len(only)}):\n  " + ", ".join(only))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
