#!/usr/bin/env python3
"""Run complete 3,000-word (10 examples) deck pipeline with WSD v11-1 for PT, ES, CS."""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
PYTHON_BIN = REPO_ROOT / ".venv/bin/python"

CONFIG = {
    "pt": {
        "profile": "config/pipelines/pt/speech/v11-3000x10.json",
        "inv_snapshot": "raw/frequency/subtlex-pt-2026-09-13/pt_ranked.txt",
        "inv_snapshot_id": "subtlex-pt-2026-09-13-r3",
        "menu_snapshot": "raw/wiktionary/enwiktionary-2026-08-20/kaikki.org-dictionary-Portuguese.jsonl",
        "menu_snapshot_id": "enwiktionary-2026-08-20",
        "harvest_sources": [
            ("tatoeba", "raw/tatoeba/pt-en/tatoeba-weekly-retrieved-2026-08-24-pt-en"),
            ("opensubtitles", "raw/opensubtitles/opensubtitles-v2018-en-pt-2015plus"),
        ],
        "wsd_profile": "pt-v11-1",
        "pos_batch_size": 64,
        "release_id": "pt-speech-v11-3000x10",
    },
    "es": {
        "profile": "config/pipelines/es/speech/v11-3000x10.json",
        "inv_snapshot": "raw/frequency/espal-subtitles-2026-09-13/es_ranked.txt",
        "inv_snapshot_id": "espal-subtitles-2026-09-13-r3",
        "menu_snapshot": "raw/dictionaries/es/spanishdict/spanishdict-complete-menu-2026-09-15-v3",
        "menu_snapshot_id": "spanishdict-complete-menu-2026-09-15-v3",
        "harvest_sources": [
            ("tatoeba", "raw/tatoeba/es-en/tatoeba-weekly-retrieved-2026-09-08-es-en"),
            ("opensubtitles", "raw/opensubtitles/opensubtitles-v2018-en-es-2016plus"),
        ],
        "wsd_profile": "es-v11-1",
        "pos_batch_size": 64,
        "release_id": "es-speech-v11-3000x10",
    },
    "cs": {
        "profile": "config/pipelines/cs/speech/v11-3000x10.json",
        "inv_snapshot": "raw/frequency/frequencywords-cs-filtered-2026-09-13/cs_ranked.txt",
        "inv_snapshot_id": "frequencywords-cs-filtered-2026-09-13",
        "menu_snapshot": "raw/wiktionary/enwiktionary-2026-09-06/kaikki.org-dictionary-Czech.jsonl",
        "menu_snapshot_id": "enwiktionary-2026-09-06",
        "harvest_sources": [
            ("tatoeba", "raw/tatoeba/cs-en/tatoeba-weekly-retrieved-2026-09-08-cs-en"),
            ("opensubtitles", "raw/opensubtitles/opensubtitles-v2018-en-cs-2016plus"),
        ],
        "wsd_profile": "cs-v11-1",
        "pos_batch_size": None,
        "release_id": "cs-speech-v11-3000x10",
    },
}


def run_cmd(cmd: list[str], env: dict[str, str] | None = None) -> str:
    display = " ".join(cmd)
    print(f"\n>>> Running: {display}\n", flush=True)
    t0 = time.time()
    res = subprocess.run(cmd, env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    elapsed = time.time() - t0
    print(res.stdout, flush=True)
    if res.returncode != 0:
        print(f"FAILED (exit code {res.returncode}) after {elapsed:.1f}s", file=sys.stderr)
        sys.exit(res.returncode)
    print(f"SUCCESS in {elapsed:.1f}s", flush=True)
    return res.stdout


def run_pipeline_for_language(workspace: Path, language: str, run_id: str | None = None) -> str:
    cfg = CONFIG[language]
    env = os.environ.copy()
    env["PYTHONPATH"] = f"{REPO_ROOT / 'src'}:{REPO_ROOT}"
    env["FLUENCY_WORKSPACE"] = str(workspace)

    print("=" * 70)
    print(f"PIPELINE: 3000-WORD DECK RUN FOR {language.upper()}")
    print("=" * 70)

    # 1. Plan if no run_id
    if run_id is None:
        plan_cmd = [
            str(PYTHON_BIN),
            "-m",
            "fluency",
            "pipeline",
            "plan",
            "--workspace",
            str(workspace),
            "--profile",
            str(REPO_ROOT / cfg["profile"]),
        ]
        out = run_cmd(plan_cmd, env=env)
        match = re.search(r"/runs/[a-z]+/speech/([0-9A-Za-z_-]+)", out)
        if not match:
            raise RuntimeError("Could not determine run_id from plan output")
        run_id = match.group(1)

    run_dir = workspace / "runs" / language / "speech" / run_id
    marker = workspace / "runs" / language / "speech" / "LATEST_V11"
    marker.write_text(run_id)
    print(f"Active Run ID: {run_id}")

    # 2. Inventory
    inv_cmd = [
        str(PYTHON_BIN),
        "-m",
        "fluency",
        "pipeline",
        "inventory",
        "--workspace",
        str(workspace),
        "--run-id",
        run_id,
        "--language",
        language,
        "--mode",
        "speech",
        "--snapshot",
        str(workspace / cfg["inv_snapshot"]),
        "--snapshot-id",
        str(cfg["inv_snapshot_id"]),
    ]
    run_cmd(inv_cmd, env=env)

    # 3. Sense Menu
    menu_cmd = [
        str(PYTHON_BIN),
        "-m",
        "fluency",
        "pipeline",
        "sense-menu",
        "--workspace",
        str(workspace),
        "--run-id",
        run_id,
        "--language",
        language,
        "--mode",
        "speech",
        "--snapshot",
        str(workspace / cfg["menu_snapshot"]),
        "--snapshot-id",
        str(cfg["menu_snapshot_id"]),
    ]
    run_cmd(menu_cmd, env=env)

    # 4. Harvest
    harvest_cmd = [
        str(PYTHON_BIN),
        "-m",
        "fluency",
        "pipeline",
        "harvest",
        "--workspace",
        str(workspace),
        "--run-id",
        run_id,
        "--language",
        language,
        "--mode",
        "speech",
    ]
    for name, rel_path in cfg["harvest_sources"]:
        harvest_cmd.extend(["--source", f"{name}={workspace / rel_path}"])
    run_cmd(harvest_cmd, env=env)

    # 5. Condition Pools
    cond_cmd = [
        str(PYTHON_BIN),
        str(REPO_ROOT / "scripts/condition_pools.py"),
        "--run-dir",
        str(run_dir),
    ]
    run_cmd(cond_cmd, env=env)

    # 6. Materialise Surfaces Ledger
    ledger_cmd = [
        str(PYTHON_BIN),
        str(REPO_ROOT / "scripts/materialise_surfaces.py"),
        "--workspace",
        str(workspace),
        "--language",
        language,
    ]
    run_cmd(ledger_cmd, env=env)

    # 7. WSD Execute
    bundle_path = workspace / "raw/wsd" / f"{language}-v11-3000x10.json"
    bundle_path.parent.mkdir(parents=True, exist_ok=True)
    wsd_cmd = [
        str(PYTHON_BIN),
        "-m",
        "fluency.speech.wsd_execute",
        "--run-dir",
        str(run_dir),
        "--out",
        str(bundle_path),
        "--profile-id",
        cfg["wsd_profile"],
        "--execution-cap",
        "30",
        "--ledger",
        str(workspace / "raw/surfaces" / language / "ledger.json"),
        "--pools",
        str(run_dir / "stages/04_pools/output/pools.json"),
    ]
    if cfg["pos_batch_size"] is not None:
        wsd_cmd.extend(["--pos-batch-size", str(cfg["pos_batch_size"])])
    run_cmd(wsd_cmd, env=env)

    # 8. WSD Import
    import_cmd = [
        str(PYTHON_BIN),
        "-m",
        "fluency",
        "pipeline",
        "wsd-import",
        "--workspace",
        str(workspace),
        "--run-id",
        run_id,
        "--language",
        language,
        "--mode",
        "speech",
        "--bundle",
        str(bundle_path),
    ]
    run_cmd(import_cmd, env=env)

    # 9. Build Run Release
    build_cmd = [
        str(PYTHON_BIN),
        "-m",
        "fluency",
        "pipeline",
        "build-run-release",
        "--workspace",
        str(workspace),
        "--run-id",
        run_id,
        "--release-id",
        cfg["release_id"],
        "--language",
        language,
        "--mode",
        "speech",
    ]
    run_cmd(build_cmd, env=env)

    # 10. Validate Release
    validate_cmd = [
        str(PYTHON_BIN),
        "-m",
        "fluency",
        "release",
        "validate",
        cfg["release_id"],
        "--workspace",
        str(workspace),
        "--language",
        language,
        "--mode",
        "speech",
    ]
    run_cmd(validate_cmd, env=env)

    # 11. Activate Release
    activate_cmd = [
        str(PYTHON_BIN),
        "-m",
        "fluency",
        "release",
        "activate",
        cfg["release_id"],
        "--workspace",
        str(workspace),
        "--language",
        language,
        "--mode",
        "speech",
    ]
    run_cmd(activate_cmd, env=env)

    print(f"\nCompleted and Activated: {cfg['release_id']}\n")
    return cfg["release_id"]


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--workspace", type=Path, default=Path(os.environ.get("FLUENCY_WORKSPACE", "~/PycharmProjects/Fluency-Workspace")).expanduser())
    ap.add_argument("--language", choices=("pt", "es", "cs", "all"), default="all")
    ap.add_argument("--run-id", help="Optional existing run_id to resume")
    args = ap.parse_args()

    languages = ["pt", "es", "cs"] if args.language == "all" else [args.language]
    for lang in languages:
        t0 = time.time()
        run_pipeline_for_language(args.workspace, lang, run_id=args.run_id if len(languages) == 1 else None)
        print(f"Total time for {lang.upper()}: {time.time() - t0:.1f}s")


if __name__ == "__main__":
    main()
