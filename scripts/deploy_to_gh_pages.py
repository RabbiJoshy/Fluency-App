#!/usr/bin/env python3
"""Deploy the current commit's app changes to the GitHub Pages worktree and push.

Usage:
    python scripts/deploy_to_gh_pages.py [optional commit message]

Follows the deploy procedure in CLAUDE.md:
1. Ensures the gh-pages worktree exists at /private/tmp/fluency-pages-deploy.
2. Pulls latest origin/gh-pages.
3. Copies changed files under app/ or config/ from HEAD into both root and app/ mirrors.
4. Commits on gh-pages and pushes to origin/gh-pages.
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

WORKTREE_PATH = Path("/private/tmp/fluency-pages-deploy")


def run(cmd: list[str], cwd: Path | None = None, check: bool = True) -> str:
    res = subprocess.run(cmd, cwd=cwd, text=True, capture_output=True)
    if check and res.returncode != 0:
        print(f"Error running: {' '.join(cmd)}", file=sys.stderr)
        print(f"Stdout:\n{res.stdout}", file=sys.stderr)
        print(f"Stderr:\n{res.stderr}", file=sys.stderr)
        sys.exit(res.returncode)
    return res.stdout.strip()


def main() -> None:
    repo_root = Path(__file__).resolve().parent.parent

    # 1. Ensure worktree exists
    if not WORKTREE_PATH.exists():
        print(f"Creating gh-pages worktree at {WORKTREE_PATH}...")
        run(["git", "worktree", "add", str(WORKTREE_PATH), "gh-pages"], cwd=repo_root)

    # 2. Update gh-pages
    print("Fetching and pulling latest gh-pages...")
    run(["git", "fetch", "origin", "gh-pages"], cwd=WORKTREE_PATH)
    run(["git", "pull", "--rebase", "origin", "gh-pages"], cwd=WORKTREE_PATH)

    # 3. Find files touched in HEAD
    head_msg = run(["git", "log", "-1", "--pretty=%s"], cwd=repo_root)
    commit_msg = sys.argv[1] if len(sys.argv) > 1 else f"Deploy: {head_msg}"

    touched_files = run(["git", "diff-tree", "--no-commit-id", "--name-only", "-r", "HEAD"], cwd=repo_root).splitlines()

    deployed_count = 0
    for file_path in touched_files:
        file_path = file_path.strip()
        if not file_path:
            continue

        # Skip tests, docs, scripts, schemas, and releases
        if file_path.startswith(("tests/", "docs/", "scripts/", "schemas/", "src/", ".git")):
            continue
        if "releases/" in file_path:
            continue

        # Get file content from HEAD
        content = run(["git", "show", f"HEAD:{file_path}"], cwd=repo_root)

        # Determine target paths on gh-pages
        targets: list[Path] = []
        if file_path.startswith("app/"):
            rel = file_path[4:]  # strip 'app/'
            targets.append(WORKTREE_PATH / "app" / rel)
            targets.append(WORKTREE_PATH / rel)
        elif file_path.startswith("config/"):
            rel = file_path[7:]  # strip 'config/'
            targets.append(WORKTREE_PATH / "config" / rel)
            targets.append(WORKTREE_PATH / "app" / "config" / rel)
        else:
            targets.append(WORKTREE_PATH / file_path)
            targets.append(WORKTREE_PATH / "app" / file_path)

        for target in targets:
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(content, encoding="utf-8")
            run(["git", "add", str(target)], cwd=WORKTREE_PATH)
            deployed_count += 1
            print(f"  -> Synced: {target.relative_to(WORKTREE_PATH)}")

    if deployed_count == 0:
        print("No deployable app or config files found in HEAD.")
        return

    # 4. Check if there are changes to commit
    status = run(["git", "status", "--porcelain"], cwd=WORKTREE_PATH)
    if not status:
        print("gh-pages is already up to date with this commit. Nothing to deploy.")
        return

    # 5. Commit and push
    print(f"Committing on gh-pages: '{commit_msg}'...")
    run(["git", "commit", "-m", commit_msg], cwd=WORKTREE_PATH)

    print("Pushing to origin gh-pages...")
    run(["git", "push", "origin", "gh-pages"], cwd=WORKTREE_PATH)
    print("Deployment to GitHub Pages complete!")


if __name__ == "__main__":
    main()
