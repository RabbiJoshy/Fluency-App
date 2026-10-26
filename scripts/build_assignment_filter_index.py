#!/usr/bin/env python3
"""Build the compact card-ID index behind the admin assignment filters.

The release index carries the sense menu, but not which model assigned a card
or how sure it was, so the app reads this small list of short card IDs instead.
Card IDs are untouched; nothing here writes to a release or to progress.

    python scripts/build_assignment_filter_index.py RELEASE_DIR OUT.json \
        --answers decide=ANSWERS.jsonl --answers jev=ANSWERS.jsonl

Each answers file is one model's per-sentence output (card_id, sentence_id,
choice, probabilities). A card has a gap when any of its sentences kept
NONE (P(NONE) >= 0.8, as the release build does); those sentences are never
published. Confidence is the lowest best-sense probability among the sentences
the deck publishes, so it matches what the card shows. Single-sense means one sense
on the card's complete menu (selected plus unused).
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

NONE_THRESHOLD = 0.8


def build(release: Path, answers: dict[str, Path]) -> dict:
    index = json.loads((release / "app" / "vocabulary.index.json").read_text(encoding="utf-8"))
    deck = json.loads((release / "deck.json").read_text(encoding="utf-8"))
    cards = deck["cards"] if isinstance(deck, dict) else deck
    short = {row["surface_card_id"]: row["id"] for row in index}
    published = {(card["card_id"], ex.get("metadata", {}).get("sentence_id"))
                 for card in cards for ex in card.get("examples") or []}
    single = [row["id"] for row in index
              if len(row.get("meanings", [])) + len(row.get("unused_menu_senses", [])) == 1]
    sources: dict[str, set[str]] = {}
    confidence: dict[str, float] = {}
    unresolved: set[str] = set()
    for name, path in answers.items():
        ids = sources.setdefault(name, set())
        with path.open(encoding="utf-8") as handle:
            for line in handle:
                row = json.loads(line)
                card = short.get(row["card_id"])
                if card is None:
                    continue
                ids.add(card)
                probs = row.get("probabilities") or {}
                if probs.get("NONE", 0.0) >= NONE_THRESHOLD:
                    unresolved.add(card)
                    continue
                if (row["card_id"], row["sentence_id"]) not in published:
                    continue
                best = max((p for k, p in probs.items() if k != "NONE"), default=None)
                if best is not None:
                    confidence[card] = round(min(confidence.get(card, 1.0), best), 3)
    overlap = set.intersection(*sources.values()) if len(sources) > 1 else set()
    if overlap:
        raise SystemExit(f"{len(overlap)} cards appear in more than one answers file")
    return {"schema": "assignment-filter-index/v2", "release_id": release.name,
            "single_sense": sorted(single),
            "sources": {name: sorted(ids) for name, ids in sources.items()},
            "min_confidence": dict(sorted(confidence.items())),
            "unresolved": sorted(unresolved)}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("release", type=Path)
    parser.add_argument("out", type=Path)
    parser.add_argument("--answers", action="append", required=True, metavar="NAME=PATH")
    args = parser.parse_args()
    answers = {name: Path(path) for name, path in (a.split("=", 1) for a in args.answers)}
    payload = build(args.release, answers)
    args.out.write_text(json.dumps(payload, separators=(",", ":")) + "\n", encoding="utf-8")
    counts = ", ".join(f"{len(v)} {k}" for k, v in payload["sources"].items())
    print(f"{args.out}: {len(payload['single_sense'])} single-sense, {counts}, "
          f"{len(payload['min_confidence'])} with confidence, {len(payload['unresolved'])} with gaps")
