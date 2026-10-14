#!/usr/bin/env python3
"""Write a ranked WSD assigner (wsd-assigner/v1) from LLM picks.

An assigner is a sparse set of sense picks a release can rank above or below
stage 04 (`fluency.release.ranked_assigners`). It never writes to a run. Rows
come from an LLM pick file (one JSON object per call with `leaves` and `items`,
as research/cascade/oneoff_pt.py writes) and, optionally, a head-to-head check
(duel.jsonl): with --duel, only picks the check kept are written. Rows whose
pick equals the stage 04 pick are left out; they would change nothing.

    python3 scripts/write_wsd_assigner.py --workspace ../Fluency-Workspace --language pt \\
        --run 20261013T133630Z-12746d8c --label DEEPSEEK --version v25 \\
        --picks raw/wsd/pt/oneoff-deepseek-2026-10-14/results.jsonl \\
        --duel raw/wsd/pt/oneoff-deepseek-2026-10-14/duel.jsonl \\
        --out raw/wsd/pt/assigners/deepseek-v25-20261014 --description "..."
"""

from __future__ import annotations

import argparse
import json
from datetime import UTC, datetime
from pathlib import Path


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--workspace", type=Path, required=True)
    ap.add_argument("--language", required=True)
    ap.add_argument("--mode", default="speech")
    ap.add_argument("--run", required=True, help="run whose stage 04 the picks were made against")
    ap.add_argument("--label", required=True)
    ap.add_argument("--version", required=True)
    ap.add_argument("--picks", required=True)
    ap.add_argument("--duel")
    ap.add_argument("--out", required=True)
    ap.add_argument("--model", default="deepseek-flash")
    ap.add_argument("--description", default="")
    args = ap.parse_args()

    ws = args.workspace.resolve()
    run = ws / "runs" / args.language / args.mode / args.run
    out = ws / args.out
    if out.exists():
        raise SystemExit(f"{out} exists; an assigner is immutable, write a new one")

    keep = None
    if args.duel:
        keep = {(r["card_id"], r["sentence_id"]) for r in map(json.loads, (ws / args.duel).open())
                if r.get("duel") == "new"}
    picks = {}
    for line in (ws / args.picks).open():
        call = json.loads(line)
        for it in call["items"]:
            key = (it["card_id"], it["sentence_id"])
            new = it.get("deepseek_pick") or it.get("pick")
            if not new or new == it["embedding_pick"] or (keep is not None and key not in keep):
                continue
            picks[key] = new

    menu = json.loads((run / "stages/02_sense_menu/output/sense-menu.json").read_text())
    where = {}
    for card in menu["cards"]:
        for an in card.get("analyses") or []:
            for s in an.get("senses") or []:
                where[(card["card_id"], s["sense_id"])] = an
    rows, missing = [], 0
    with (run / "stages/04_wsd_assignments/output/assignments.jsonl").open() as fh:
        for line in fh:
            if not picks:
                break
            a = json.loads(line)
            key = (a["card_id"], a["sentence_id"])
            if key not in picks:
                continue
            sense = picks.pop(key)
            an = where.get((a["card_id"], sense))
            if an is None:
                missing += 1
                continue
            rows.append({
                "row_version": "wsd-assigner-row/v1", "card_id": a["card_id"], "sentence_id": a["sentence_id"],
                "sense_menu_content_id": a["sense_menu_content_id"], "menu_analysis_id": an["menu_analysis_id"],
                "selected_sense_id": sense,
                "selected_tuple": {"headword": an["headword"], "part_of_speech": an["part_of_speech"]},
                "emitted_level": "leaf", "replaces_sense_id": a.get("selected_sense_id"),
            })
    missing += len(picks)

    out.mkdir(parents=True)
    with (out / "assignments.jsonl").open("w") as fh:
        for r in rows:
            fh.write(json.dumps(r, ensure_ascii=False) + "\n")
    (out / "manifest.json").write_text(json.dumps({
        "assigner_version": "wsd-assigner/v1", "assigner_id": out.name, "label": args.label,
        "version": args.version, "language": args.language, "mode": args.mode, "model": args.model,
        "built_against_run": args.run, "picks": args.picks, "duel": args.duel, "rows": len(rows),
        "created_at": datetime.now(UTC).isoformat(timespec="seconds"), "description": args.description,
    }, indent=1) + "\n")
    print(f"{out}: {len(rows):,} rows; {missing} picks not found on the run's menu or stage 04")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
