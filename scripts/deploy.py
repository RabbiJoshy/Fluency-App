#!/usr/bin/env python3
"""Deploy the app: bring in origin/main, then push HEAD to main.

Usage:
    python scripts/deploy.py            # or: make deploy

Works the same from a local checkout or a cloud session, on main or on any
feature branch. The push to main starts .github/workflows/deploy-pages.yml,
which publishes app/ to gh-pages; this script never touches gh-pages itself.

It merges (never rebases) origin/main into HEAD so commits other sessions
already pushed are kept, and stops on a conflict for you to resolve.
"""

from __future__ import annotations

import subprocess
import sys
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
ACTIONS_URL = "https://github.com/RabbiJoshy/Fluency-App/actions/workflows/deploy-pages.yml"


def git(*args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    res = subprocess.run(["git", *args], cwd=REPO_ROOT, text=True, capture_output=True)
    if check and res.returncode != 0:
        sys.exit(f"git {' '.join(args)} failed:\n{res.stdout}{res.stderr}")
    return res


def main() -> None:
    dirty = git("status", "--porcelain", "--", "app/").stdout.strip()
    if dirty:
        print("Uncommitted changes under app/ are not deployed:\n" + dirty, file=sys.stderr)

    for attempt in range(4):
        git("fetch", "-q", "origin", "main")
        if git("merge-base", "--is-ancestor", "origin/main", "HEAD", check=False).returncode != 0:
            merged = git("merge", "--no-edit", "origin/main", check=False)
            if merged.returncode != 0:
                sys.exit(
                    "origin/main conflicts with this branch. Resolve the conflict "
                    "(for version tags, take a fresh tag and a higher CACHE_NAME), "
                    "commit, run the app tests, and deploy again.\n" + merged.stdout
                )
            print("Merged origin/main into HEAD.")
        pushed = git("push", "origin", "HEAD:main", check=False)
        if pushed.returncode == 0:
            head = git("rev-parse", "--short", "HEAD").stdout.strip()
            print(f"Pushed {head} to main. Pages deploy: {ACTIONS_URL}")
            return
        # Rejected because main moved (another session pushed), or a network
        # error: fetch, merge again and retry.
        time.sleep(2 ** (attempt + 1))
    sys.exit("Push to main failed after retries:\n" + pushed.stderr)


if __name__ == "__main__":
    main()
