#!/usr/bin/env python3
"""Fold the refetched SpanishDict pages into the menu snapshot.

The recovered snapshot shipped with a 6,513-entry surface cache against a
10,000-card deck, and no HTTP client to extend it. The refetch filled that gap
for the surfaces that had no menu; this merges the result so the menu build
can see it.

Flagged rows are not merged. A spelling substitution means SpanishDict has no
entry and answered about a different word, and an English entry means it
answered in the wrong language -- both are recorded in the surface store as
evidence, and neither is a menu.

Writes a new snapshot directory rather than editing the pinned one.
"""

from __future__ import annotations

import argparse, json, shutil, sys
from pathlib import Path


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--workspace", type=Path, required=True)
    ap.add_argument("--snapshot", default="spanishdict-complete-menu-2026-08-23-v1")
    ap.add_argument("--out-id", default="spanishdict-complete-menu-2026-09-14-v2")
    args = ap.parse_args()

    base = args.workspace / "raw/dictionaries/es/spanishdict" / args.snapshot
    out = args.workspace / "raw/dictionaries/es/spanishdict" / args.out_id
    refetch = args.workspace / "raw/dictionaries/es/spanishdict/refetch-menuless.jsonl"
    if not refetch.exists():
        print(f"no refetch at {refetch}"); return 1
    if out.exists():
        shutil.rmtree(out)
    shutil.copytree(base, out)

    cache = json.loads((out / "surface_cache.json").read_text(encoding="utf-8"))
    before = len(cache)
    merged = skipped = 0
    for line in refetch.open(encoding="utf-8"):
        row = json.loads(line)
        if row.get("flags"):
            skipped += 1
            continue
        analyses = row.get("analyses") or []
        if not analyses:
            continue
        cache[row["word"]] = {
            "query": row["word"],
            "entry_lang": row.get("entry_lang") or "es",
            "dictionary_analyses": [
                {"headword": a.get("headword") or row["word"],
                 "senses": [{"pos": a.get("part") or "", "translation": a.get("translation") or "",
                             "source": "spanishdict", "headword": a.get("headword") or row["word"],
                             "context": a.get("context") or "",
                             "regions": a.get("regions") or []}]}
                for a in analyses
            ],
            "possible_results": [{"result": h} for h in row.get("possible_results") or []],
            "merged_from": "refetch-menuless-2026-09-14",
        }
        merged += 1
    (out / "surface_cache.json").write_text(
        json.dumps(cache, ensure_ascii=False), encoding="utf-8")

    artifact = json.loads((out / "artifact.json").read_text(encoding="utf-8"))
    artifact["coverage"]["surface_cache_entries"] = len(cache)
    artifact.setdefault("notes", []).append(
        f"Extended by refetch-menuless-2026-09-14: {merged} surfaces added, "
        f"{skipped} withheld because SpanishDict substituted a spelling or answered in English.")
    artifact["provenance_status"] = "reconstructed_then_extended"
    (out / "artifact.json").write_text(
        json.dumps(artifact, ensure_ascii=False, indent=1), encoding="utf-8")

    print(f"surface cache {before:,} -> {len(cache):,}  (+{merged} merged, {skipped} withheld)")
    print(f"wrote {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
