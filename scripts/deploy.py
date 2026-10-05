#!/usr/bin/env python3
"""Deploy the app: bring in origin/main, then push HEAD to main.

Usage:
    python scripts/deploy.py            # or: make deploy
    python scripts/deploy.py --sync     # or: make sync — bring in main, push nothing

Works the same from a local checkout or a cloud session, on main or on any
feature branch. The push to main starts .github/workflows/deploy-pages.yml,
which publishes app/ to gh-pages; this script never touches gh-pages itself.

It merges (never rebases) origin/main into HEAD so commits other sessions
already pushed are kept, and stops on a conflict for you to resolve.

Concurrent sessions share this checkout and leave uncommitted edits in it.
When those edits touch a file main also changed, git refuses the merge
outright. Merging somewhere else and pushing from there lands the change but
leaves this checkout behind main, and the next session builds on stale code.
So the edits are carried across the merge instead: rehearsed in a scratch
worktree first, then parked, merged under, and put back — only when the
rehearsal shows they re-apply cleanly. Otherwise nothing here is touched.
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
ACTIONS_URL = "https://github.com/RabbiJoshy/Fluency-App/actions/workflows/deploy-pages.yml"
# Every deploy prepends an entry to both changelogs, so two sessions deploying
# close together always conflict there. Those merges are resolved here.
CHANGELOGS = ("app/config/dev_changelog.json", "config/dev_changelog.json")
# The app shows only the newest few entries; git keeps the rest. Capping the
# merge stops a branch holding an older, longer file from restoring trimmed ones.
CHANGELOG_KEEP = 30


def git(*args: str, check: bool = True, cwd: Path = REPO_ROOT) -> subprocess.CompletedProcess[str]:
    res = subprocess.run(["git", *args], cwd=cwd, text=True, capture_output=True)
    if check and res.returncode != 0:
        sys.exit(f"git {' '.join(args)} failed:\n{res.stdout}{res.stderr}")
    return res


def unmerged(cwd: Path = REPO_ROOT) -> set[str]:
    return set(git("diff", "--name-only", "--diff-filter=U", cwd=cwd).stdout.split())


def resolve_changelog_conflicts(cwd: Path = REPO_ROOT) -> bool:
    """Finish a merge whose only conflicts are the changelogs: keep both sides' entries."""
    conflicted = unmerged(cwd)
    if not conflicted or not conflicted <= set(CHANGELOGS):
        return False
    for path in conflicted:
        ours = json.loads(git("show", f":2:{path}", cwd=cwd).stdout)
        theirs_raw = git("show", f":3:{path}", cwd=cwd).stdout
        theirs = json.loads(theirs_raw)
        seen, entries = set(), []
        for entry in ours.get("entries", []) + theirs.get("entries", []):
            key = (entry.get("timestamp"), entry.get("summary"))
            if key not in seen:
                seen.add(key)
                entries.append(entry)
        theirs["entries"] = sorted(entries, key=lambda e: e.get("timestamp", ""), reverse=True)[:CHANGELOG_KEEP]
        text = json.dumps(theirs, indent=2, ensure_ascii=False) + ("\n" if theirs_raw.endswith("\n") else "")
        (cwd / path).write_text(text, encoding="utf-8")
        git("add", path, cwd=cwd)
    git("commit", "--no-edit", cwd=cwd)
    return True


def merge_main(cwd: Path = REPO_ROOT) -> str:
    """Merge origin/main into HEAD at `cwd`: 'merged', 'blocked' by local edits, or 'conflict'."""
    merged = git("merge", "--no-edit", "origin/main", check=False, cwd=cwd)
    if merged.returncode == 0 or resolve_changelog_conflicts(cwd):
        return "merged"
    if not unmerged(cwd):
        # git stopped before merging anything: uncommitted edits sit in files
        # the merge would change. The checkout is exactly as it was.
        return "blocked"
    return "conflict"


def carry_local_edits_across_merge() -> None:
    """Merge origin/main under this checkout's uncommitted edits, keeping them uncommitted."""
    patch = git("diff", "--binary").stdout
    scratch = Path(tempfile.mkdtemp(prefix="deploy-rehearsal-"))
    worktree = scratch / "wt"
    try:
        git("worktree", "add", "-q", "--detach", str(worktree), "HEAD")
        if merge_main(worktree) != "merged":
            sys.exit("origin/main conflicts with this branch's commits outside the changelogs. "
                     "Resolve it, commit, run the app tests, and deploy again.")
        (scratch / "edits.patch").write_text(patch, encoding="utf-8")
        applied = git("apply", "--3way", str(scratch / "edits.patch"), check=False, cwd=worktree)
        clashes = unmerged(worktree)
        if applied.returncode != 0 or clashes:
            sys.exit(
                "This checkout is behind main, and uncommitted edits here (other sessions' work) "
                "clash with main in:\n  " + "\n  ".join(sorted(clashes) or ["(patch did not apply)"])
                + "\nNothing was changed. Those edits need resolving against main by their owner "
                "(or commit them first), then deploy again."
            )
    finally:
        git("worktree", "remove", "--force", str(worktree), check=False)
        shutil.rmtree(scratch, ignore_errors=True)

    # The rehearsal re-applied cleanly: do it for real. The stash is dropped
    # only once the edits are back, so a failure leaves them recoverable.
    label = f"deploy: uncommitted edits carried across a merge of main ({time.strftime('%H:%M:%S')})"
    git("stash", "push", "-q", "-m", label)
    if merge_main() != "merged":
        git("merge", "--abort", check=False)
        git("stash", "pop", "-q", check=False)
        sys.exit("Merging origin/main failed after the rehearsal succeeded; edits restored. Try again.")
    restored = git("stash", "apply", "-q", check=False)
    if restored.returncode != 0 or unmerged():
        sys.exit(
            "main is merged, but putting the uncommitted edits back clashed (they changed during "
            f"the merge). They are safe in the stash '{label}'; resolve the files above, "
            "then `git reset -q` and `git stash drop`."
        )
    git("reset", "-q")  # stash apply can stage paths; leave the edits uncommitted as they were
    git("stash", "drop", "-q")
    print("Merged origin/main under this checkout's uncommitted edits; they are back as they were.")


def bring_in_main() -> None:
    git("fetch", "-q", "origin", "main")
    if git("merge-base", "--is-ancestor", "origin/main", "HEAD", check=False).returncode == 0:
        return
    outcome = merge_main()
    if outcome == "blocked":
        carry_local_edits_across_merge()
    elif outcome == "conflict":
        sys.exit("origin/main conflicts with this branch outside the changelogs. "
                 "Resolve it, commit, run the app tests, and deploy again.")
    else:
        print("Merged origin/main into HEAD.")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--sync", action="store_true", help="bring in origin/main without pushing")
    args = parser.parse_args()

    if args.sync:
        bring_in_main()
        print("Up to date with main.")
        return

    dirty = git("status", "--porcelain", "--", "app/").stdout.strip()
    if dirty:
        print("Uncommitted changes under app/ are not deployed:\n" + dirty, file=sys.stderr)

    for attempt in range(4):
        bring_in_main()
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
