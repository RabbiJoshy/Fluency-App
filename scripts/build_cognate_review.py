#!/usr/bin/env python3
"""Create a human calibration queue from one generated cognate layer."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--layer", type=Path, required=True)
    parser.add_argument("--known-language", default="en")
    parser.add_argument("--review-floor", type=float, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()

    layer = json.loads(args.layer.read_text(encoding="utf-8"))
    code = args.known_language
    policy = (layer.get("policies") or {}).get(code) or {}
    threshold = float(policy["default_threshold"])
    rows = []
    for surface, by_language in (layer.get("scores") or {}).items():
        score = (by_language or {}).get(code)
        if not isinstance(score, dict) or float(score.get("score", 0)) < args.review_floor:
            continue
        rows.append({
            "review_version": "cognate-calibration-review/v1",
            "language": layer["language"],
            "known_language": code,
            "surface": surface,
            "matched_word": score.get("known_word"),
            "score": score.get("score"),
            "form_score": score.get("form"),
            "meaning_score": score.get("meaning"),
            "ships_at_current_cutoff": float(score["score"]) >= threshold,
            "review": {
                "status": "pending",
                "decision": None,
                "reason": None,
                "reviewer": None,
                "reviewed_at": None
            },
            "allowed_decisions": ["true_cognate", "false_friend", "unrelated", "exclude_target"]
        })
    rows.sort(key=lambda row: (-float(row["score"]), row["surface"]))
    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False, separators=(",", ":")) + "\n")
    print(
        f"{layer['language']}->{code}: {len(rows)} pending pairs at or above "
        f"{args.review_floor:.2f}; current cutoff {threshold:.2f}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
