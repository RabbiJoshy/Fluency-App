#!/usr/bin/env python3
"""Run WSD v11-1 and complete release pipeline across 10k cards for pt, es, cs.

This script executes the complete production run for a language (or all 3):
1. Runs wsd_execute with profile {lang}-v11-1, execution cap 30, and surface ledger integration.
2. Imports the bundle into stage 04 via pipeline wsd-import.
3. Builds the inactive release candidate via pipeline build-run-release.
4. Validates the release via release validate.

Usage:
    .venv/bin/python scripts/run_v11_production.py --workspace ~/PycharmProjects/Fluency-Workspace --language pt
    .venv/bin/python scripts/run_v11_production.py --workspace ~/PycharmProjects/Fluency-Workspace --language es
    .venv/bin/python scripts/run_v11_production.py --workspace ~/PycharmProjects/Fluency-Workspace --language cs
    .venv/bin/python scripts/run_v11_production.py --workspace ~/PycharmProjects/Fluency-Workspace --language all
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
import time
from pathlib import Path


CONFIG = {
    "pt": {
        "profile_id": "pt-v11-1",
        "pos_batch_size": 64,
        "release_id": "pt-speech-v11-10000x10",
    },
    "es": {
        "profile_id": "es-v11-1",
        "pos_batch_size": 64,
        "release_id": "es-speech-v11-10000x10",
    },
    "cs": {
        "profile_id": "cs-v11-1",
        "pos_batch_size": None,
        "release_id": "cs-speech-v11-10000x10",
    },
}


def run_cmd(cmd: list[str], env: dict[str, str] | None = None) -> None:
    display = " ".join(cmd)
    print(f"\n>>> Running: {display}\n", flush=True)
    t0 = time.time()
    res = subprocess.run(cmd, env=env)
    elapsed = time.time() - t0
    if res.returncode != 0:
        print(f"FAILED (exit code {res.returncode}) after {elapsed:.1f}s", file=sys.stderr)
        sys.exit(res.returncode)
    print(f"SUCCESS in {elapsed:.1f}s", flush=True)


def run_pipeline_for_language(
    workspace: Path,
    language: str,
    python_bin: str = ".venv/bin/python",
    run_id: str | None = None,
    execution_cap: int = 30,
) -> None:
    if language not in CONFIG:
        raise ValueError(f"Unsupported language: {language}")

    cfg = CONFIG[language]
    runs_dir = workspace / "runs" / language / "speech"
    if run_id is None:
        marker = runs_dir / "LATEST_V11"
        if not marker.exists():
            raise FileNotFoundError(f"LATEST_V11 marker not found in {runs_dir}")
        run_id = marker.read_text().strip()

    run_dir = runs_dir / run_id
    if not run_dir.exists():
        raise FileNotFoundError(f"Run dir does not exist: {run_dir}")

    bundle_dir = workspace / "raw" / "wsd"
    bundle_dir.mkdir(parents=True, exist_ok=True)
    bundle_path = bundle_dir / f"{language}-v11-10000x10.json"

    env = os.environ.copy()
    env["PYTHONPATH"] = "src:."
    env["FLUENCY_WORKSPACE"] = str(workspace)

    print("=" * 70)
    print(f"STARTING PRODUCTION WSD V11-1 RUN FOR {language.upper()}")
    print(f"  Run ID:      {run_id}")
    print(f"  Run Dir:     {run_dir}")
    print(f"  Profile:     {cfg['profile_id']}")
    print(f"  Bundle:      {bundle_path}")
    print(f"  Release ID:  {cfg['release_id']}")
    print("=" * 70, flush=True)

    # 1. WSD Execute
    wsd_cmd = [
        python_bin,
        "-m",
        "fluency.speech.wsd_execute",
        "--run-dir",
        str(run_dir),
        "--out",
        str(bundle_path),
        "--profile-id",
        cfg["profile_id"],
        "--execution-cap",
        str(execution_cap),
    ]
    if cfg["pos_batch_size"] is not None:
        wsd_cmd.extend(["--pos-batch-size", str(cfg["pos_batch_size"])])

    run_cmd(wsd_cmd, env=env)

    # 2. Pipeline wsd-import into stage 04
    import_cmd = [
        python_bin,
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

    # 3. Pipeline build-run-release
    build_cmd = [
        python_bin,
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

    # 4. Release validate
    validate_cmd = [
        python_bin,
        "-m",
        "fluency",
        "release",
        "validate",
        cfg["release_id"],
        "--language",
        language,
    ]
    run_cmd(validate_cmd, env=env)

    print(f"\n>>> PRODUCTION RUN COMPLETE & VALIDATED FOR {language.upper()} <<<\n", flush=True)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--workspace",
        type=Path,
        default=Path("/Users/joshuathomasamar/PycharmProjects/Fluency-Workspace"),
        help="Path to workspace root",
    )
    parser.add_argument(
        "--language",
        choices=["pt", "es", "cs", "all"],
        default="all",
        help="Language to run (default: all)",
    )
    parser.add_argument(
        "--run-id",
        type=str,
        default=None,
        help="Specific run ID (defaults to LATEST_V11 for language)",
    )
    parser.add_argument(
        "--execution-cap",
        type=int,
        default=30,
        help="Max occurrences per card (default: 30)",
    )
    parser.add_argument(
        "--python-bin",
        type=str,
        default=".venv/bin/python",
        help="Python binary path",
    )
    args = parser.parse_args()

    languages = ["pt", "es", "cs"] if args.language == "all" else [args.language]
    for lang in languages:
        run_pipeline_for_language(
            workspace=args.workspace.resolve(),
            language=lang,
            python_bin=args.python_bin,
            run_id=args.run_id,
            execution_cap=args.execution_cap,
        )


if __name__ == "__main__":
    main()
