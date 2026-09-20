#!/usr/bin/env python3
"""Stamp v12 assignment POS onto a copy of a pre-WSD pairs document.

Does not rewrite the hashed v1 set. Writes `<prewsd-dir>-v2` with a hardlinked
`examples.json` and a new `pairs.json` (`prewsd-pairs/v2`).
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from fluency.surfaces.prewsd import ID_PREFIX, _write, occurrence_pos_lookup  # noqa: E402

PAIRS_VERSION = "prewsd-pairs/v2"


def _sentence_ids(examples: dict) -> list[str]:
    return [
        i if str(i).startswith(ID_PREFIX) else ID_PREFIX + str(i)
        for i in examples["columns"]["sentence_id"]
    ]


def load_assignment_pos(path: Path) -> tuple[dict[tuple[str, str], str], str | None]:
    found: dict[tuple[str, str], str] = {}
    pin = None
    with path.open(encoding="utf-8") as fh:
        for line in fh:
            if not line.strip():
                continue
            row = json.loads(line)
            if pin is None:
                pin = (row.get("model_revisions") or {}).get("occurrence_pos")
            tag = ((row.get("evidence") or {}).get("candidate_preparation") or {}).get(
                "observed_pos"
            )
            form = row.get("surface_form")
            sid = row.get("sentence_id")
            if tag and form and sid:
                found[(form, sid)] = str(tag)
    return found, pin


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--prewsd", type=Path, required=True)
    ap.add_argument("--assignments", type=Path, required=True)
    ap.add_argument("--out", type=Path)
    args = ap.parse_args()
    src = args.prewsd
    out = args.out or src.parent / (src.name + "-v2")
    examples = json.loads((src / "examples.json").read_text(encoding="utf-8"))
    pairs = json.loads((src / "pairs.json").read_text(encoding="utf-8"))
    ids = _sentence_ids(examples)
    index = {sid: n for n, sid in enumerate(ids)}
    tags, pin = load_assignment_pos(args.assignments)
    filled = 0
    surfaces = {}
    for form, entry in pairs["surfaces"].items():
        eligible = list(entry["eligible"])
        n = len(eligible)
        column = list(entry.get("occurrence_pos") or [None] * n)
        if len(column) != n:
            column = [None] * n
        for i, sent_index in enumerate(eligible):
            sid = ids[sent_index]
            tag = tags.get((form, sid))
            if tag:
                column[i] = tag
                filled += 1
        row = dict(entry)
        row["occurrence_pos"] = column
        surfaces[form] = row
    out.mkdir(parents=True, exist_ok=True)
    dest_examples = out / "examples.json"
    if dest_examples.exists() or dest_examples.is_symlink():
        dest_examples.unlink()
    try:
        os.link(src / "examples.json", dest_examples)
    except OSError:
        shutil.copy2(src / "examples.json", dest_examples)
    examples_record = {
        "path": "examples.json",
        "bytes": dest_examples.stat().st_size,
        "sha256": __import__("hashlib").sha256(dest_examples.read_bytes()).hexdigest(),
    }
    pairs_record = _write(out / "pairs.json", {
        "document_version": PAIRS_VERSION,
        "language": pairs.get("language"),
        "run_id": pairs.get("run_id"),
        "occurrence_pos_model": pin or pairs.get("occurrence_pos_model"),
        "surfaces": surfaces,
    })
    src_manifest = json.loads((src / "manifest.json").read_text(encoding="utf-8"))
    manifest = {
        **src_manifest,
        "documents": [examples_record, pairs_record],
        "note": src_manifest.get("note", "")
        + " occurrence_pos is (word, sentence) under occurrence_pos_model.",
    }
    (out / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=1) + "\n", encoding="utf-8"
    )
    lookup = occurrence_pos_lookup(
        examples, json.loads((out / "pairs.json").read_text(encoding="utf-8"))
    )
    print(f"assignment tags: {len(tags):,}")
    print(f"stamped onto eligible pairs: {filled:,}  lookup size: {len(lookup):,}")
    print(f"model: {pin}")
    print(f"-> {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
