#!/usr/bin/env python3
"""Build the compact card-ID index behind the admin assignment filters.

The release index carries the sense menu, but not whether a card has a single
sense or whether DeepSeek corrected it, so the app reads this small list of
short card IDs instead. Jev needs no list: the Jev sidecar already names its
cards. Card IDs are untouched; nothing here writes to a release or to progress.

    python scripts/build_assignment_filter_index.py RELEASE_APP_DIR ASSIGNER_DIR OUT.json

DeepSeek means at least one accepted correction: an assigner row whose chosen
sense differs from the one it replaces. Single-sense means one sense on the
card's complete menu (selected plus unused), so a sense that no example
selected still counts.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path


def build(release_app: Path, assigner: Path) -> dict:
    index = json.loads((release_app / "vocabulary.index.json").read_text(encoding="utf-8"))
    release_id = release_app.parent.name
    short = {row["surface_card_id"]: row["id"] for row in index}
    single = [row["id"] for row in index
              if len(row.get("meanings", [])) + len(row.get("unused_menu_senses", [])) == 1]
    corrected = set()
    with (assigner / "assignments.jsonl").open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row["selected_sense_id"] != row["replaces_sense_id"] and row["card_id"] in short:
                corrected.add(short[row["card_id"]])
    return {"schema": "assignment-filter-index/v1", "release_id": release_id,
            "single_sense": sorted(single), "deepseek": sorted(corrected)}


if __name__ == "__main__":
    app_dir, assigner_dir, out = (Path(arg) for arg in sys.argv[1:4])
    payload = build(app_dir, assigner_dir)
    out.write_text(json.dumps(payload, separators=(",", ":")) + "\n", encoding="utf-8")
    print(f"{out}: {len(payload['single_sense'])} single-sense, {len(payload['deepseek'])} DeepSeek")
