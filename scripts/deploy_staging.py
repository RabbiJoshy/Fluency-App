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
import contextlib
import datetime
import fcntl
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
STAGING_URL = "https://fluency-staging.pages.dev"
STAGING_METADATA_DIR = REPO_ROOT / ".airlock"
STAGING_RECORD_FILE = STAGING_METADATA_DIR / "staging_release.json"
STAGING_LOCK_FILE = STAGING_METADATA_DIR / "staging_deploy.lock"


@contextlib.contextmanager
def staging_deployment_lock(timeout_seconds: int = 180, poll_interval: float = 2.0):
    """Acquire an exclusive process lock so concurrent staging deploys run consecutively without clashing."""
    STAGING_METADATA_DIR.mkdir(parents=True, exist_ok=True)
    fd = os.open(STAGING_LOCK_FILE, os.O_CREAT | os.O_RDWR, 0o644)
    start_time = time.time()
    locked = False
    printed_wait_msg = False
    try:
        while True:
            try:
                fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
                locked = True
                if printed_wait_msg:
                    now_str = datetime.datetime.now().strftime("%H:%M:%S")
                    print(f"[{now_str}] Lock acquired! Resuming staging deployment.")
                break
            except (BlockingIOError, OSError):
                if not printed_wait_msg:
                    now_str = datetime.datetime.now().strftime("%H:%M:%S")
                    print(
                        f"[{now_str}] Another staging deployment is currently in progress.\n"
                        f"Queued — waiting for lock to release so this deploy runs consecutively (timeout: {timeout_seconds}s)..."
                    )
                    printed_wait_msg = True
                if time.time() - start_time > timeout_seconds:
                    raise TimeoutError(
                        f"Timed out after {timeout_seconds}s waiting for staging deployment lock at {STAGING_LOCK_FILE}."
                    )
                time.sleep(poll_interval)
        yield
    finally:
        if locked:
            try:
                fcntl.flock(fd, fcntl.LOCK_UN)
            except OSError:
                pass
        os.close(fd)


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


def check_staging_ancestry(full_sha: str) -> None:
    """Parallel checkouts must preserve the changes already published to staging."""
    staged = git("rev-parse", "--verify", "refs/heads/staging", check=False)
    if staged.returncode != 0:
        return
    staged_sha = staged.stdout.strip()
    included = git("merge-base", "--is-ancestor", staged_sha, full_sha, check=False)
    if included.returncode != 0:
        sys.exit(
            f"Staging deployment blocked: {full_sha[:8]} does not include the current "
            f"staging release {staged_sha[:8]}. Merge staging into your branch first "
            "so another chat's fixes are preserved. Use --allow-replace-staging only "
            "for an intentional replacement."
        )


def warn_or_check_staging_ancestry(full_sha: str, strict: bool = False) -> None:
    """Check ancestry against recent staging release, warning by default or blocking if strict."""
    if strict:
        check_staging_ancestry(full_sha)
        return
    staged = git("rev-parse", "--verify", "refs/heads/staging", check=False)
    if staged.returncode != 0:
        return
    staged_sha = staged.stdout.strip()
    included = git("merge-base", "--is-ancestor", staged_sha, full_sha, check=False)
    if included.returncode != 0:
        print(
            f"Notice: Staging was recently deployed with commit {staged_sha[:8]} by another chat/branch.\n"
            f"Deploying commit {full_sha[:8]} consecutively so you can review your changes at {STAGING_URL}."
        )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--ref", default="HEAD", help="git ref or commit to deploy to staging (default: HEAD)")
    parser.add_argument("--dry-run", action="store_true", help="build the staging site without deploying to Cloudflare")
    parser.add_argument("--skip-tests", action="store_true", help="skip running the app test suite")
    parser.add_argument("--strict-ancestry", action="store_true", help="block deployment if ref is not an ancestor of current staging release")
    parser.add_argument("--allow-replace-staging", action="store_true", help="intentionally replace staging with a divergent or older ref")
    parser.add_argument("--lock-timeout", type=int, default=180, help="seconds to wait for lock if another deploy is in progress (default: 180)")
    parser.add_argument("--no-lock", action="store_true", help="skip acquiring deployment lock")
    args = parser.parse_args()

    # 1. Resolve commit details
    full_sha = git("rev-parse", args.ref).stdout.strip()
    if not args.dry_run and not args.allow_replace_staging:
        warn_or_check_staging_ancestry(full_sha, strict=args.strict_ancestry)
    short_sha = full_sha[:8]
    subject = git("log", "-1", "--format=%s", full_sha).stdout.strip()
    author = git("log", "-1", "--format=%an", full_sha).stdout.strip()
    dirty = git("status", "--porcelain", "--", "app/").stdout.strip()
    if dirty:
        print(f"Notice: Working tree has uncommitted edits under app/:\n{dirty}\nStaging will build committed ref {short_sha}.")

    # 2. Run tests outside lock (CPU-bound test suites can run in parallel)
    if not args.skip_tests and not args.dry_run:
        run_tests()

    # 3. Build staging site and deploy inside exclusive process lock
    lock_ctx = (
        contextlib.nullcontext()
        if (args.dry_run or args.no_lock)
        else staging_deployment_lock(timeout_seconds=args.lock_timeout)
    )
    with lock_ctx:
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
                # This is the staging project's canonical branch, not the real
                # production app. Pin it so feature branches update STAGING_URL.
                "--branch", "main",
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
