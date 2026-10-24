#!/usr/bin/env python3
"""Lay the committed app/ tree over a checkout of gh-pages.

Usage:
    python scripts/build_pages_site.py --dest <gh-pages checkout> [--ref main]

This is the one place that decides what the live site contains. The GitHub
Actions workflow (.github/workflows/deploy-pages.yml) runs it on every push
to main; nothing else should write to gh-pages.

Every file tracked under app/ at --ref is written, byte for byte, to both the
site root and the app/ mirror. It writes the whole tree, not the files one
commit touched, so a deploy never depends on which commit ran it. Files the
app no longer ships are removed, except under EXTERNAL_DATA: gh-pages also
holds data that is not in this repository (cognates/<lang>/ for languages
other than es, coverage/<lang>/), which the app reads through config.json's
cognatesPath and coveragePath. Those are never deleted.

Cache busting is stamped here, not by hand. Every `.js`/`.css` `?v=` tag, the
`*ASSET_VERSION` constants and the service worker's CACHE_NAME are rewritten to
carry the deployed commit (--stamp), so one deploy busts every changed asset
and no two sessions can claim the same version. The committed tags stay as
they are; they only serve local runs.
"""

from __future__ import annotations

import argparse
import re
import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

# Tracked under app/ but not part of the site: credentials, and the lyrics
# audit datasets (8 MB, a research tool, never served).
EXCLUDED_PREFIXES = ("backend/", "lyrics-audit/")
EXCLUDED_NAMES = (".DS_Store",)
EXCLUDED_PATTERNS = (
    "-headway-",
    "verify-turbo",
    "_probe_songs.json",
    "data/bridge/es.json",
    "data/bridge/es-fw1.json",
    "data/bridge/es-fw1-ds25.json",
    "data/bridge/pt.json",
    "data/bridge/pt-fw1.json",
    "data/bridge/pt-fw1-ds25.json",
    "data/bridge/cs.json",
    "data/bridge/fr.json",
    "data/bridge/fr-fw1.json",
    "data/bridge/fr-fw1-ds25.json",
)
STAMPED_SUFFIXES = (".html", ".js", ".css")
# Published data with no source in this repository; see the docstring.
EXTERNAL_DATA = ("cognates/", "coverage/", "app/cognates/", "app/coverage/")

# manifest.json is versioned too: production's old service worker keeps serving
# its cached manifest (and so an old home-screen name) until the learner accepts
# the update, but it cannot have cached a URL it has never seen.
_ASSET_TAG = re.compile(r"(\.(?:js|css|md)|manifest\.json)\?v=[A-Za-z0-9_.-]+")
_VERSION_CONST = re.compile(r"(const [A-Z_]*ASSET_VERSION\s*=\s*)(['\"])[^'\"]*\2")
_CACHE_NAME = re.compile(r"(const CACHE_NAME\s*=\s*)(['\"])(flashcards-v\d+)[^'\"]*\2")


def stamp(text: str, version: str) -> str:
    """Point every asset tag, version constant and CACHE_NAME at `version`."""
    text = _ASSET_TAG.sub(rf"\g<1>?v={version}", text)
    text = _VERSION_CONST.sub(rf"\g<1>\g<2>{version}\g<2>", text)
    return _CACHE_NAME.sub(rf"\g<1>\g<2>\g<3>-{version}\g<2>", text)


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
        if any(pat in rel for pat in EXCLUDED_PATTERNS):
            continue
        files.append((sha, rel))
    return files


# Staging installs alongside production on a home screen, so it gets its own
# name and icon: "Fluency β" (Fβ, app/icons/staging/) instead of "Fluency" (Fλ).
STAGING_IDENTITY_FILES = ("index.html", "manifest.json", "service-worker.js")
STAGING_NAME_SWAPS = (
    ('<meta name="apple-mobile-web-app-title" content="Fluency">', '<meta name="apple-mobile-web-app-title" content="Fluency β">'),
    ("<title>Fluency</title>", "<title>Fluency β</title>"),
    ('"name": "Fluency"', '"name": "Fluency β"'),
    ('"short_name": "Fluency"', '"short_name": "Fluency β"'),
)


STAGING_NOT_FOUND = (
    b'<!DOCTYPE html>\n<html lang="en"><head><meta charset="utf-8">'
    b"<title>Not found</title></head>\n"
    b'<body><p>Not found. <a href="/">Open Fluency</a></p></body></html>\n'
)


def staging_identity(rel: str, content: bytes) -> bytes:
    if rel not in STAGING_IDENTITY_FILES:
        return content
    for old, new in STAGING_NAME_SWAPS:
        content = content.replace(old.encode("utf-8"), new.encode("utf-8"))
    content = content.replace(b"icons/apple-touch-icon.png", b"icons/staging/apple-touch-icon.png")
    return content.replace(b"icons/icon-", b"icons/staging/icon-")


def read_blobs_batch(shas: list[str]) -> dict[str, bytes]:
    """Read multiple git blobs in a single streaming process instead of spawning git per file."""
    unique_shas = list(dict.fromkeys(shas))
    if not unique_shas:
        return {}
    proc = subprocess.Popen(
        ["git", "cat-file", "--batch"],
        cwd=REPO_ROOT,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
    )
    proc.stdin.write("\n".join(unique_shas).encode("ascii") + b"\n")
    proc.stdin.flush()
    proc.stdin.close()
    blobs = {}
    for sha in unique_shas:
        header = proc.stdout.readline()
        if not header:
            break
        parts = header.decode("ascii").split()
        if len(parts) >= 3 and parts[1] == "blob":
            size = int(parts[2])
            data = proc.stdout.read(size)
            proc.stdout.read(1)  # trailing newline
            blobs[sha] = data
        else:
            blobs[sha] = b""
    proc.wait()
    return blobs


def build(dest: Path, ref: str, version: str | None = None, env: str = "production") -> int:
    files = tracked_app_files(ref)
    if not any(rel == "index.html" for _, rel in files):
        raise SystemExit(f"{ref}:app/index.html missing; refusing to build the site")
    blobs = read_blobs_batch([sha for sha, _ in files])
    written = 0
    for sha, rel in files:
        content = blobs[sha]
        if version and rel.endswith(STAMPED_SUFFIXES):
            text = stamp(content.decode("utf-8"), version)
            content = text.encode("utf-8")
        if env == "staging" and rel == "index.html":
            content = content.replace(b"<head>", b"<head>\n    <script>window.__FLUENCY_ENV__ = 'staging';</script>")
        if env == "staging":
            content = staging_identity(rel, content)
        for target in (dest / rel, dest / "app" / rel):
            if target.exists() and target.read_bytes() == content:
                continue
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(content)
            written += 1
    (dest / ".nojekyll").touch()
    extra_shipped = set()
    if env == "staging":
        import datetime
        import json
        env_meta = json.dumps({
            "environment": "staging",
            "ref": ref,
            "version": version or "",
            "built_at": datetime.datetime.now(datetime.timezone.utc).isoformat()
        }, indent=2).encode("utf-8")
        for target in (dest / "config" / "app_environment.json", dest / "app" / "config" / "app_environment.json"):
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(env_meta)
            written += 1
        extra_shipped.update({"config/app_environment.json", "app/config/app_environment.json"})
        # Without a top-level 404.html, Cloudflare Pages answers every missing
        # path with index.html, carrying a Link header that preloads its 37
        # modules by *relative* URL. A missing file such as
        # Artists/spotify_tracks.json then preloads Artists/js/main.js, which is
        # missing too, and so on one folder deeper, forever: ~500 requests a
        # minute per open tab. A real 404 ends it, as GitHub Pages does in
        # production. It must not preload anything itself.
        (dest / "404.html").write_bytes(STAGING_NOT_FOUND)
        written += 1
        extra_shipped.add("404.html")

    shipped = {".nojekyll"} | {rel for _, rel in files} | {f"app/{rel}" for _, rel in files} | extra_shipped
    for path in sorted(p for p in dest.rglob("*") if p.is_file() and ".git" not in p.relative_to(dest).parts):
        rel = path.relative_to(dest).as_posix()
        if rel in shipped or rel.startswith(EXTERNAL_DATA):
            continue
        path.unlink()
        written += 1
        print(f"  removed {rel}")
    return written


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--dest", required=True, type=Path, help="site destination directory")
    parser.add_argument("--ref", default="HEAD", help="commit whose app/ to publish")
    parser.add_argument("--stamp", help="version stamped into ?v= tags and CACHE_NAME "
                        "(default: the ref's short commit id; pass '' to keep the committed tags)")
    parser.add_argument("--env", default="production", choices=["production", "staging"],
                        help="environment being built (production or staging)")
    parser.add_argument("--allow-dir", action="store_true",
                        help="allow output destination without a .git checkout (used for staging exports)")
    args = parser.parse_args()
    if not (args.dest / ".git").exists() and not args.allow_dir and args.env == "production":
        raise SystemExit(f"{args.dest} is not a git checkout of gh-pages (pass --allow-dir to override)")
    version = args.stamp
    if version is None:
        version = git("rev-parse", "--short=8", args.ref).decode().strip()
    written = build(args.dest, args.ref, version or None, env=args.env)
    print(f"{written} site files updated from {args.ref} ({args.env}), stamped {version or '(none)'}")


if __name__ == "__main__":
    main()
