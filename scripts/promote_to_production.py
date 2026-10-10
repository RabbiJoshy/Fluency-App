#!/usr/bin/env python3
"""Deliberately promote the exact reviewed staging version to production.

Usage:
    python3 scripts/promote_to_production.py [--sha <reviewed_sha>] [--confirm]
    # or: make promote

Ensures that only the exact reviewed commit is promoted to production.
Unrelated changes made after staging are detected and prevented from silently entering.
"""

from __future__ import annotations

import argparse
import datetime
import json
import os
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
STAGING_RECORD_FILE = REPO_ROOT / ".airlock" / "staging_release.json"
PROMOTION_HISTORY_FILE = REPO_ROOT / ".airlock" / "promotion_history.json"
PRODUCTION_URL = "https://rabbijoshy.github.io/Fluency-App/"
ACTIONS_URL = "https://github.com/RabbiJoshy/Fluency-App/actions/workflows/deploy-pages.yml"


def git(*args: str, check: bool = True, cwd: Path = REPO_ROOT) -> subprocess.CompletedProcess[str]:
    res = subprocess.run(["git", *args], cwd=cwd, text=True, capture_output=True)
    if check and res.returncode != 0:
        sys.exit(f"git {' '.join(args)} failed:\n{res.stdout}{res.stderr}")
    return res


def run_tests() -> None:
    print("Running app test suite before production promotion...")
    env = {**os.environ, "PYTHONPATH": "src"}
    res = subprocess.run(
        [sys.executable, "-m", "unittest", "discover", "-s", "tests/app", "-t", "."],
        cwd=REPO_ROOT,
        env=env,
        capture_output=True,
        text=True,
    )
    if res.returncode != 0:
        print("App test suite failed:\n" + res.stdout + res.stderr, file=sys.stderr)
        sys.exit(1)
    print("App test suite passed.")


def record_promotion(meta: dict) -> None:
    history = []
    if PROMOTION_HISTORY_FILE.exists():
        try:
            history = json.loads(PROMOTION_HISTORY_FILE.read_text(encoding="utf-8"))
            if not isinstance(history, list):
                history = []
        except Exception:
            history = []
    history.append(meta)
    PROMOTION_HISTORY_FILE.parent.mkdir(parents=True, exist_ok=True)
    PROMOTION_HISTORY_FILE.write_text(json.dumps(history, indent=2) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--sha", help="specific commit SHA to promote (must match the reviewed staging SHA)")
    parser.add_argument("--confirm", action="store_true", help="confirm promotion to production without interactive prompt")
    parser.add_argument("--skip-tests", action="store_true", help="skip running the app test suite")
    args = parser.parse_args()

    # 1. Read last staging record
    if not STAGING_RECORD_FILE.exists():
        sys.exit(
            "No recorded staging deployment found in .airlock/staging_release.json.\n"
            "Deploy to staging for review first: `make stage` or `python3 scripts/deploy_staging.py`"
        )

    try:
        staging_data = json.loads(STAGING_RECORD_FILE.read_text(encoding="utf-8"))
    except Exception as e:
        sys.exit(f"Failed to read staging record: {e}")

    staged_sha = staging_data.get("sha", "").strip()
    if not staged_sha:
        sys.exit("Staging record is missing 'sha'. Please re-stage.")

    if args.sha and args.sha != staged_sha and not staged_sha.startswith(args.sha):
        sys.exit(
            f"Specified --sha ({args.sha}) does not match the active staging deployment ({staged_sha}).\n"
            "Only the version tested on staging can be promoted."
        )

    short_sha = staged_sha[:8]
    subject = staging_data.get("subject", git("log", "-1", "--format=%s", staged_sha).stdout.strip())
    staged_at = staging_data.get("staged_at", "unknown")

    # 2. Check for commits added after staging
    head_sha = git("rev-parse", "HEAD").stdout.strip()
    if head_sha != staged_sha:
        unreviewed = git("log", "--oneline", f"{staged_sha}..HEAD").stdout.strip()
        if unreviewed:
            print("=" * 60)
            print("NOTICE: Commits were made after the reviewed staging build:")
            print(unreviewed)
            print(f"Promotion will promote ONLY the reviewed staging commit: {short_sha}")
            print("Unreviewed commits will remain on their current branch and NOT reach production.")
            print("=" * 60)

    # 3. Explicit Approval Guard
    if not args.confirm:
        print("=" * 60)
        print("DELIBERATE PROMOTION CONFIRMATION REQUIRED")
        print(f"Target commit:  {short_sha}: {subject}")
        print(f"Staged at:      {staged_at}")
        print(f"Destination:    Production ({PRODUCTION_URL})")
        print("=" * 60)
        if not sys.stdin.isatty():
            print("Non-interactive session: pass --confirm to authorize promotion.", file=sys.stderr)
            sys.exit(1)
        answer = input(f"Promote commit {short_sha} to production? [y/N]: ").strip().lower()
        if answer not in ("y", "yes"):
            print("Promotion cancelled. Production remains untouched.")
            sys.exit(0)

    # 4. Run tests
    if not args.skip_tests:
        run_tests()

    # 5. Bring in origin/main and verify ancestry
    print("Checking origin/main...")
    git("fetch", "-q", "origin", "main")
    # Check if origin/main has commits not in staged_sha
    main_ahead = git("log", "--oneline", f"{staged_sha}..origin/main").stdout.strip()
    if main_ahead:
        sys.exit(
            f"origin/main has moved ahead with commits not present in the reviewed staging build:\n{main_ahead}\n"
            "Sync and review on staging again before promoting."
        )

    # 6. Push to origin/main
    print(f"Pushing reviewed commit {short_sha} to origin/main...")
    pushed = git("push", "origin", f"{staged_sha}:main", check=False)
    if pushed.returncode != 0:
        sys.exit(f"Failed to push to origin/main:\n{pushed.stderr}")

    # 7. Record promotion
    promo_meta = {
        "promoted_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "sha": staged_sha,
        "short_sha": short_sha,
        "subject": subject,
        "production_url": PRODUCTION_URL,
    }
    record_promotion(promo_meta)

    print("=" * 60)
    print("PROMOTION TO PRODUCTION COMPLETE")
    print(f"Promoted:      {short_sha}: {subject}")
    print(f"Live App:      {PRODUCTION_URL}")
    print(f"Pages Action:  {ACTIONS_URL}")
    print("=" * 60)


if __name__ == "__main__":
    main()
