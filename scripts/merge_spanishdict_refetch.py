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
    ap.add_argument(
        "--refetch", action="append", default=None,
        help="Refetch JSONL to merge, relative to the spanishdict directory or "
             "absolute. Repeatable. Defaults to every refetch-*.jsonl present, "
             "because naming one by hand is how the other one gets forgotten.")
    args = ap.parse_args()

    root = args.workspace / "raw/dictionaries/es/spanishdict"
    base = root / args.snapshot
    out = root / args.out_id

    # Defaulting to "whatever refetches exist" rather than to one hardcoded
    # filename: a merge that silently skips a file it did not know about looks
    # exactly like a merge that worked.
    if args.refetch:
        refetches = [Path(r) if Path(r).is_absolute() else root / r for r in args.refetch]
    else:
        refetches = sorted(root.glob("refetch-*.jsonl"))
    missing = [r for r in refetches if not r.exists()]
    if missing:
        print("no refetch at " + ", ".join(str(m) for m in missing)); return 1
    if not refetches:
        print(f"no refetch-*.jsonl under {root}"); return 1
    print("merging: " + ", ".join(r.name for r in refetches))
    if out.exists():
        shutil.rmtree(out)
    shutil.copytree(base, out)

    cache = json.loads((out / "surface_cache.json").read_text(encoding="utf-8"))
    before = len(cache)
    merged = skipped = 0
    per_file: dict[str, int] = {}
    for refetch in refetches:
        for line in refetch.open(encoding="utf-8"):
            row = json.loads(line)
            if row.get("flags"):
                skipped += 1
                continue
            analyses = row.get("analyses") or []
            # Rows written since the fetcher kept SpanishDict's relation label
            # carry possible results as objects. One that declares a conjugation
            # or inflection is a lemma statement even with no senses of its own
            # -- the menu is the lemma's. Older rows hold bare strings, whose
            # relation was lost, and are merged exactly as before.
            possible = [
                ({"headword": item.get("headword") or item.get("result"),
                  "heuristic": item.get("heuristic") or ""}
                 if isinstance(item, dict) else {"result": item})
                for item in row.get("possible_results") or []
            ]
            declares = any(p.get("heuristic") in {"conjugation", "inflection"} for p in possible)
            if not analyses and not declares:
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
                "possible_results": possible,
                "merged_from": refetch.stem,
            }
            merged += 1
            per_file[refetch.name] = per_file.get(refetch.name, 0) + 1
    (out / "surface_cache.json").write_text(
        json.dumps(cache, ensure_ascii=False), encoding="utf-8")

    # The snapshot records a hash per file and the menu build checks them, so a
    # merged cache with a stale hash is refused -- correctly. Recompute the ones
    # that changed rather than weakening the check.
    import hashlib

    artifact = json.loads((out / "artifact.json").read_text(encoding="utf-8"))
    for record in artifact.get("content_files") or []:
        target = out / record["path"]
        if not target.exists():
            continue
        digest = hashlib.sha256(target.read_bytes()).hexdigest()
        if digest != record.get("sha256"):
            record["sha256"] = digest
            record["bytes"] = target.stat().st_size
    # The copy is a new snapshot, so it must say so. Leaving the source's
    # snapshot_id in place produced a directory that claimed to be the artifact
    # it was derived from, and the menu build rejected it -- correctly, since
    # the id is what pins a run to its evidence.
    artifact["snapshot_id"] = args.out_id
    artifact["derived_from_snapshot_id"] = args.snapshot
    artifact["coverage"]["surface_cache_entries"] = len(cache)
    artifact.setdefault("notes", []).append(
        "Extended by " + ", ".join(f"{name} (+{n})" for name, n in sorted(per_file.items()))
        + f": {merged} surfaces added, {skipped} withheld because SpanishDict "
        "substituted a spelling or answered in English.")
    artifact["provenance_status"] = "reconstructed_then_extended"
    (out / "artifact.json").write_text(
        json.dumps(artifact, ensure_ascii=False, indent=1), encoding="utf-8")

    for name, n in sorted(per_file.items()):
        print(f"  {name}: +{n}")
    print(f"surface cache {before:,} -> {len(cache):,}  (+{merged} merged, {skipped} withheld)")
    print(f"wrote {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
