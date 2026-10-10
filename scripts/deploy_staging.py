#!/usr/bin/env python3
"""Publish the app to Staging on Cloudflare Pages.

Usage:
    python3 scripts/deploy_staging.py [--ref HEAD] [--dry-run]
    # or: make stage

Builds the staging site with scripts/build_pages_site.py using --env staging,
isolated storage namespaces, staging service-worker cache busting, and
clear environment indicators, then deploys to Cloudflare Pages project 'fluency-staging'.

Accessible at: https://fluency-staging.pages.dev/
"""

from __future__ import annotations

import argparse
import datetime
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
STAGING_URL = "https://fluency-staging.pages.dev"
STAGING_METADATA_DIR = REPO_ROOT / ".airlock"
STAGING_RECORD_FILE = STAGING_METADATA_DIR / "staging_release.json"


def git(*args: str, check: bool = True, cwd: Path = REPO_ROOT) -> subprocess.CompletedProcess[str]:
    res = subprocess.run(["git", *args], cwd=cwd, text=True, capture_output=True)
    if check and res.returncode != 0:
        sys.exit(f"git {' '.join(args)} failed:\n{res.stdout}{res.stderr}")
    return res


def run_tests() -> None:
    print("Running app test suite before staging deployment...")
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


def record_staging_release(meta: dict) -> None:
    STAGING_METADATA_DIR.mkdir(parents=True, exist_ok=True)
    STAGING_RECORD_FILE.write_text(json.dumps(meta, indent=2) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--ref", default="HEAD", help="git ref or commit to deploy to staging (default: HEAD)")
    parser.add_argument("--dry-run", action="store_true", help="build the staging site without deploying to Cloudflare")
    parser.add_argument("--skip-tests", action="store_true", help="skip running the app test suite")
    args = parser.parse_args()

    # 1. Resolve commit details
    full_sha = git("rev-parse", args.ref).stdout.strip()
    short_sha = full_sha[:8]
    subject = git("log", "-1", "--format=%s", full_sha).stdout.strip()
    author = git("log", "-1", "--format=%an", full_sha).stdout.strip()
    dirty = git("status", "--porcelain", "--", "app/").stdout.strip()
    if dirty:
        print(f"Notice: Working tree has uncommitted edits under app/:\n{dirty}\nStaging will build committed ref {short_sha}.")

    # 2. Run tests
    if not args.skip_tests and not args.dry_run:
        run_tests()

    # 3. Build staging site into a temporary directory
    build_dir = Path(tempfile.mkdtemp(prefix="fluency-staging-build-"))
    version_stamp = f"stg-{short_sha}"
    try:
        from build_pages_site import build as build_site
        print(f"Building staging site for {short_sha} stamped {version_stamp}...")
        written = build_site(build_dir, ref=full_sha, version=version_stamp, env="staging")
        print(f"Staging build complete ({written} files).")

        if args.dry_run:
            print(f"[dry-run] Staging site built at {build_dir}. Skipping Cloudflare Pages deployment.")
            return

        # 4. Deploy to Cloudflare Pages
        print(f"Deploying to Cloudflare Pages project 'fluency-staging'...")
        deploy_cmd = [
            "npx", "wrangler", "pages", "deploy",
            str(build_dir),
            "--project-name", "fluency-staging",
            "--commit-dirty=true",
            "--commit-hash", full_sha,
            "--commit-message", f"Staging: {subject}",
        ]
        deploy_res = subprocess.run(deploy_cmd, cwd=REPO_ROOT, text=True, capture_output=True)
        if deploy_res.returncode != 0:
            print(f"Cloudflare Pages deployment failed:\n{deploy_res.stdout}{deploy_res.stderr}", file=sys.stderr)
            sys.exit(1)
        print("Cloudflare Pages deployment succeeded.")

        # 5. Record metadata
        meta = {
            "environment": "staging",
            "url": STAGING_URL,
            "sha": full_sha,
            "short_sha": short_sha,
            "subject": subject,
            "author": author,
            "version": version_stamp,
            "staged_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        }
        record_staging_release(meta)

        # 6. Update local staging git ref
        git("update-ref", "refs/heads/staging", full_sha, check=False)

        print("=" * 60)
        print(f"STAGING PUBLISHED SUCCESSFULLY")
        print(f"URL:        {STAGING_URL}")
        print(f"Commit:     {short_sha}: {subject}")
        print(f"Version:    {version_stamp}")
        print(f"Isolation:  IndexedDB ('fluency-offline-staging'), Wire sync ('stg_*')")
        print(f"Review on:  Laptop browser & Actual Phone Safari/Chrome at {STAGING_URL}")
        print("=" * 60)
    finally:
        shutil.rmtree(build_dir, ignore_errors=True)


if __name__ == "__main__":
    main()
