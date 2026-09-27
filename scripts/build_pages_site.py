#!/usr/bin/env python3
"""Lay the committed app/ tree over a checkout of gh-pages.

Usage:
    python scripts/build_pages_site.py --dest <gh-pages checkout> [--ref main]

This is the one place that decides what the live site contains. The GitHub
Actions workflow (.github/workflows/deploy-pages.yml) runs it on every push
to main; nothing else should write to gh-pages.

Every file tracked under app/ at --ref is written, byte for byte, to both the
site root and the app/ mirror. It writes the whole tree, not the files one
commit touched, so a deploy never depends on which commit ran it. It deletes
nothing: gh-pages also holds data that is not in this repository
(cognates/<lang>/ for languages other than es, coverage/<lang>/), which the
app reads through config.json's cognatesPath and coveragePath.
"""

from __future__ import annotations

import argparse
import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

# Tracked under app/ but not part of the site: credentials, and the lyrics
# audit datasets (8 MB, a research tool, never served).
EXCLUDED_PREFIXES = ("backend/", "lyrics-audit/")
EXCLUDED_NAMES = (".DS_Store",)


def git(*args: str) -> bytes:
    return subprocess.run(
        ["git", *args], cwd=REPO_ROOT, check=True, capture_output=True
    ).stdout


def tracked_app_files(ref: str) -> list[tuple[str, str]]:
    """(blob sha, path relative to app/) for every file under app/ at ref."""
    out = git("ls-tree", "-r", "-z", ref, "--", "app/")
    files = []
    for entry in out.split(b"\0"):
        if not entry:
            continue
        meta, path = entry.decode("utf-8").split("\t", 1)
        mode, kind, sha = meta.split()
        if kind != "blob" or mode == "120000":
            continue
        rel = path[len("app/"):]
        if rel.startswith(EXCLUDED_PREFIXES) or Path(rel).name in EXCLUDED_NAMES:
            continue
        files.append((sha, rel))
    return files


def build(dest: Path, ref: str) -> int:
    files = tracked_app_files(ref)
    if not any(rel == "index.html" for _, rel in files):
        raise SystemExit(f"{ref}:app/index.html missing; refusing to build the site")
    written = 0
    for sha, rel in files:
        content = git("cat-file", "blob", sha)
        for target in (dest / rel, dest / "app" / rel):
            if target.exists() and target.read_bytes() == content:
                continue
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(content)
            written += 1
    (dest / ".nojekyll").touch()
    return written


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--dest", required=True, type=Path, help="gh-pages checkout")
    parser.add_argument("--ref", default="HEAD", help="commit whose app/ to publish")
    args = parser.parse_args()
    if not (args.dest / ".git").exists():
        raise SystemExit(f"{args.dest} is not a git checkout of gh-pages")
    written = build(args.dest, args.ref)
    print(f"{written} site files updated from {args.ref}")


if __name__ == "__main__":
    main()
