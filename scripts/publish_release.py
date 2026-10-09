#!/usr/bin/env python3
"""Publish release directories to their segment's release site.

Usage:
    python scripts/publish_release.py --segment es \\
        --release <workspace>/releases/es/speech/es-speech-v16-10000x10 [--release ...] \\
        [--keep <release id> ...] [--dry-run]

`releases/<segment>/<path>` is served from repository
RabbiJoshy/Fluency-Releases-<segment>, branch gh-pages, at
https://rabbijoshy.github.io/Fluency-Releases-<segment>/<path>
(app/js/release-host.js; docs/decisions/0026-release-repos-per-language.md).

A release directory is one that holds an `app/` directory. Each --release is
copied to the path after its last `<segment>` component (so
`…/es/speech/<id>` lands at `speech/<id>`), or to an explicit `SRC:DEST`.

Nothing is removed unless --prune is given. With it, a release stays only if
its directory name appears as a quoted string or path segment in
app/config/*.json (not the changelog) or app/js/*.js, was published in this
run, or is passed with --keep. Preview releases opened by URL
(`?lyricsRelease=<id>`) are named nowhere in the app, so --keep them, and hold
a rollback the same way. Run with --dry-run first to see what would go.

The result is pushed as a single commit replacing gh-pages. These sites hold
generated output, so history is not kept and the repository stays the size of
the site. Unchanged releases are carried over by reference, so a publish only
uploads the files it adds; nothing else is downloaded.
"""

from __future__ import annotations

import argparse
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
OWNER = "RabbiJoshy"
BRANCH = "gh-pages"
MAX_FILE_BYTES = 100 * 1000 * 1000
README = """# Fluency-Releases-{segment}

Published Fluency release files for `releases/{segment}/`, served at
https://rabbijoshy.github.io/Fluency-Releases-{segment}/.

Generated output. Written only by `scripts/publish_release.py` in
RabbiJoshy/Fluency-App, which replaces this branch with one commit per publish
(docs/decisions/0026-release-repos-per-language.md there).
"""


def repo_url(segment: str) -> str:
    return f"https://github.com/{OWNER}/Fluency-Releases-{segment}"


def run(cmd: list[str], cwd: Path, *, env: dict | None = None, stdin: str | None = None) -> str:
    res = subprocess.run(cmd, cwd=cwd, env=env, input=stdin, text=True, capture_output=True)
    if res.returncode != 0:
        sys.exit(f"{' '.join(cmd)} failed:\n{res.stdout}{res.stderr}")
    return res.stdout


def app_reference_text() -> str:
    parts = []
    for pattern in ("app/config/*.json", "app/js/*.js"):
        for path in sorted(REPO_ROOT.glob(pattern)):
            if path.name == "dev_changelog.json":
                continue
            parts.append(path.read_text(encoding="utf-8", errors="replace"))
    return "\n".join(parts)


def is_referenced(release_id: str, text: str) -> bool:
    # Quoted, or a path segment: prose in comments does not keep a release.
    return re.search(rf"(?<=[\"'`/]){re.escape(release_id)}(?=[\"'`/])", text) is not None


def release_roots(paths: list[str]) -> set[str]:
    """Directories that hold an app/ directory, from a flat list of file paths."""
    roots = set()
    for path in paths:
        parts = path.split("/")
        if "app" in parts[1:]:
            roots.add("/".join(parts[: parts.index("app", 1)]))
    return roots


def destination(src: Path, segment: str) -> str:
    parts = src.resolve().parts
    if segment not in parts:
        sys.exit(f"cannot place {src}: no '{segment}' directory in its path; pass SRC:DEST")
    index = len(parts) - 1 - parts[::-1].index(segment)
    dest = "/".join(parts[index + 1:])
    if not dest:
        sys.exit(f"cannot place {src}: it is the segment directory itself")
    return dest


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--segment", required=True, help="es, pt, cs, fi, fr, lyrics, …")
    parser.add_argument("--release", action="append", default=[], metavar="SRC[:DEST]")
    parser.add_argument("--prune", action="store_true", help="remove releases the app no longer names")
    parser.add_argument("--keep", action="append", default=[], metavar="RELEASE_ID",
                        help="with --prune: keep this release anyway")
    parser.add_argument("--message", help="commit message")
    parser.add_argument("--dry-run", action="store_true", help="show the plan, push nothing")
    args = parser.parse_args()
    segment = args.segment

    releases: list[tuple[Path, str]] = []
    for spec in args.release:
        src_text, _, dest = spec.partition(":")
        src = Path(src_text).resolve()
        if not (src / "app").is_dir():
            sys.exit(f"{src} is not a release directory (no app/ inside)")
        releases.append((src, dest.strip("/") or destination(src, segment)))

    with tempfile.TemporaryDirectory(prefix=f"publish-{segment}-") as tmp:
        work = Path(tmp) / "site"
        env = dict(os.environ, GIT_INDEX_FILE=str(Path(tmp) / "index"))
        existing = run(["git", "ls-remote", "--heads", repo_url(segment), BRANCH], cwd=Path(tmp)).strip()
        if existing:
            # Trees only: carried-over releases are referenced, never downloaded.
            run(["git", "clone", "-q", "--depth", "1", "--filter=blob:none", "--no-checkout",
                 "--branch", BRANCH, repo_url(segment), str(work)], cwd=Path(tmp))
            run(["git", "read-tree", "HEAD"], cwd=work, env=env)
        else:
            # A new site: pushing gh-pages is what turns its Pages on.
            print(f"Fluency-Releases-{segment} has no {BRANCH} yet; starting it.")
            work.mkdir()
            run(["git", "init", "-q"], cwd=work)
            run(["git", "remote", "add", "origin", repo_url(segment)], cwd=work)

        for _, dest in releases:
            run(["git", "rm", "-q", "-r", "--cached", "--ignore-unmatch", "--", dest], cwd=work, env=env)
        for src, dest in releases:
            files = sorted(p for p in src.rglob("*") if p.is_file() and p.name != ".DS_Store")
            # GitHub refuses files over 100 MB (deck.json has been one); the
            # app does not read them from the published site.
            too_big = [p for p in files if p.stat().st_size > MAX_FILE_BYTES]
            for p in too_big:
                print(f"  ! skipped {dest}/{p.relative_to(src).as_posix()} "
                      f"({p.stat().st_size / 1e6:.0f} MB, over GitHub's 100 MB file limit)")
            files = [p for p in files if p not in too_big]
            oids = run(["git", "hash-object", "-w", "--stdin-paths"], cwd=work,
                       stdin="\n".join(str(p) for p in files) + "\n").split()
            info = "".join(
                f"{'100755' if os.access(p, os.X_OK) else '100644'} {oid}\t{dest}/{p.relative_to(src).as_posix()}\n"
                for p, oid in zip(files, oids))
            run(["git", "update-index", "--add", "--index-info"], cwd=work, env=env, stdin=info)
            print(f"  + {dest} ({len(files)} files)")

        for name, content in (("README.md", README.format(segment=segment)), (".nojekyll", "")):
            oid = run(["git", "hash-object", "-w", "--stdin"], cwd=work, stdin=content).strip()
            run(["git", "update-index", "--add", "--cacheinfo", f"100644,{oid},{name}"], cwd=work, env=env)

        text = app_reference_text()
        published = {dest.rsplit("/", 1)[-1] for _, dest in releases}
        paths = run(["git", "ls-files", "--cached"], cwd=work, env=env).splitlines()
        for root in sorted(release_roots(paths)):
            release_id = root.rsplit("/", 1)[-1]
            if (not args.prune or release_id in published or release_id in args.keep
                    or is_referenced(release_id, text)):
                print(f"  = {root}")
                continue
            print(f"  - {root} (not named by the app, not --keep)")
            run(["git", "rm", "-q", "-r", "--cached", "--", root], cwd=work, env=env)

        tree = run(["git", "write-tree"], cwd=work, env=env).strip()
        if existing and tree == run(["git", "rev-parse", "HEAD^{tree}"], cwd=work).strip():
            print(f"Fluency-Releases-{segment} already matches; nothing to publish.")
            return
        if args.dry_run:
            print("Dry run: nothing pushed.")
            return
        message = args.message or "Publish " + (", ".join(sorted(published)) or "a pruned site")
        commit = run(["git", "-c", "user.name=Fluency release", "-c", "user.email=releases@fluency.invalid",
                      "commit-tree", tree, "-m", message], cwd=work).strip()
        run(["git", "push", "-q", "--force", "origin", f"{commit}:refs/heads/{BRANCH}"], cwd=work)
        print(f"Pushed {commit[:8]} to Fluency-Releases-{segment} {BRANCH}; "
              f"Pages build: {repo_url(segment)}/actions")


if __name__ == "__main__":
    main()
