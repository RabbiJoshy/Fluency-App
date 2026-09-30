#!/usr/bin/env python3
"""x30 runs: show up to thirty examples per card on the live v21 Speech decks.

Every v21 run scored thirty sentences per card in stage 04 (the assignment
evidence records cap_per_surface 30) but its profile displayed ten, so twenty
sense-assigned sentences per card were never shown. Nothing upstream of
selection changes: each new run carries stages 01-04 byte-for-byte from the v21
run behind the live release, and only selection and the release are rebuilt.

    python scripts/x30_runs.py --step plan      # new runs, stages 01-04 carried
    python scripts/x30_runs.py --step release   # inactive candidates, validated, sharded

The first x30 build showed ~21 per card: selection kept only the lower two
thirds of each pool by burden. Selection now fills from the rest after those,
and shards are slim (example-shards/v2), so this second set of runs is
published as <release>-slim.

Nothing is activated or published.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO / "scripts"))

import v21_runs  # noqa: E402

DISPLAY = 30
RUNS_FILE = "x30-slim-runs.json"
LIVE_RELEASE = {lang: f"{lang}/speech/{rid}" for lang, rid in v21_runs.RELEASE_ID.items()}
RELEASE_ID = {lang: rid.replace("x10", f"x{DISPLAY}") + "-slim"
              for lang, rid in v21_runs.RELEASE_ID.items()}
STAGES = ("01_inventory", "02_sense_menu", "03_sentence_harvest", "04_wsd_assignments")


def step_plan(args, ws: Path, out: Path) -> int:
    from fluency.core.workspace import Workspace
    from fluency.pipeline.planning import create_pipeline_plan
    workspace = Workspace.load(ws)
    runs = v21_runs._json(out / RUNS_FILE) if (out / RUNS_FILE).exists() else {}
    sources = v21_runs._json(out / v21_runs.RUNS_FILE)
    for lang in args.language or list(RELEASE_ID):
        if lang in runs:
            v21_runs._say(f"{lang}: run {runs[lang]} already planned")
            continue
        source = ws / "runs" / lang / "speech" / sources[lang]
        profile = v21_runs._json(source / "profile.json")
        profile["profile_id"] = f"{profile['profile_id']}-x{DISPLAY}"
        profile["scope"]["display_examples_per_card"] = DISPLAY
        profile["scope"]["note"] = (
            f"Up to {DISPLAY} examples per card: every sentence stage 04 assigned a sense "
            f"(execution cap 30), carried unchanged from v21 run {source.name}.")
        # Record the cap stage 04 actually ran with; the v21 profile said 20
        # while every assignment row's evidence says 30.
        profile["wsd"]["execution_cap_per_card"] = 30
        surfaces = profile["scope"]["surface_limit"]
        profile["wsd"]["max_wsd_units_per_run"] = max(
            profile["wsd"].get("max_wsd_units_per_run", 0), surfaces * 30 + surfaces)
        run = create_pipeline_plan(workspace, profile)
        for stage in STAGES:
            v21_runs._carry_stage(source, run, stage)
            contract_path = run / "stages" / stage / "contract.json"
            contract = v21_runs._json(contract_path)
            contract["carried_note"] = (f"carried byte-for-byte from {source.name}; "
                                        f"x{DISPLAY} changes selection only")
            v21_runs._write(contract_path, contract)
        runs[lang] = run.name
        v21_runs._write(out / RUNS_FILE, runs)
        v21_runs._say(f"{lang}: planned run {run.name} (stages 01-04 carried from {source.name})")
    return 0


def step_release(args, ws: Path, out: Path) -> int:
    import functools
    from fluency.release import example_shards
    # v21_runs imports shard_app_examples at call time, so this reaches it.
    example_shards.shard_app_examples = functools.partial(example_shards.shard_app_examples, slim=True)
    v21_runs.SOURCES = {lang: (None, None, LIVE_RELEASE[lang]) for lang in RELEASE_ID}
    v21_runs.RELEASE_ID = RELEASE_ID
    v21_runs.RUNS_FILE = RUNS_FILE
    return v21_runs.step_release(args, ws, out)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--step", required=True, choices=["plan", "release"])
    ap.add_argument("--language", nargs="+", choices=sorted(RELEASE_ID))
    ap.add_argument("--workspace", type=Path, default=REPO.parent / "Fluency-Workspace")
    args = ap.parse_args()
    ws = args.workspace.resolve()
    out = ws / "raw/wsd"
    return {"plan": step_plan, "release": step_release}[args.step](args, ws, out)


if __name__ == "__main__":
    raise SystemExit(main())
