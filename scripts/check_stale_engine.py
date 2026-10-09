#!/usr/bin/env python3
"""Check live releases for stale WSD engines.

Output 4 of UNISON Part 2: Lists live releases built on an older engine than
the current profile.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import sys
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent
WORKSPACE = REPO_ROOT.parent / "Fluency-Workspace"
RELEASES_ROOT = WORKSPACE / "releases"
MODELS_DIR = REPO_ROOT / "config" / "wsd" / "models"

# Active engine profile targets per (mode, language)
ACTIVE_PROFILES = {
    ("speech", "es"): "es-v23-1",
    ("speech", "pt"): "pt-v23-1",
    ("speech", "cs"): "cs-v21-1",
    ("speech", "fi"): "fi-v21-1",
    ("speech", "fr"): "fr-v7-1",
    ("lyrics", "es"): "es-lyrics-v23-1",
}


def _extract_version_number(id_str: str) -> int | None:
    match = re.search(r"\bv(\d+)\b", id_str) or re.search(r"-v(\d+)-", id_str) or re.search(r"-v(\d+)$", id_str)
    return int(match.group(1)) if match else None


def find_active_releases(releases_root: Path) -> list[dict[str, Any]]:
    releases = []
    if not releases_root.is_dir():
        return releases

    for active_file in releases_root.glob("**/active.json"):
        try:
            data = json.loads(active_file.read_text(encoding="utf-8"))
        except Exception:
            continue

        release_id = data.get("release_id")
        manifest_rel = data.get("manifest_path")
        mode = data.get("mode", "speech")
        lang = data.get("language")

        if not lang and "releases" in str(active_file):
            parts = active_file.relative_to(releases_root).parts
            if parts and parts[0] in ("es", "pt", "cs", "fi", "fr", "nl"):
                lang = parts[0]
            elif parts and parts[0] == "lyrics":
                lang = "es"

        manifest_path = active_file.parent / manifest_rel if manifest_rel else None
        manifest_data = {}
        if manifest_path and manifest_path.is_file():
            try:
                manifest_data = json.loads(manifest_path.read_text(encoding="utf-8"))
            except Exception:
                pass

        wsd_info = manifest_data.get("wsd", {})
        source_id = wsd_info.get("source_id", "")

        releases.append({
            "mode": mode,
            "language": lang or "unknown",
            "release_id": release_id or active_file.parent.name,
            "source_id": source_id,
            "active_file": str(active_file.relative_to(releases_root)),
            "manifest_path": str(manifest_path.relative_to(releases_root)) if manifest_path and manifest_path.is_file() else None,
        })
    return releases


def evaluate_release(release: dict[str, Any]) -> dict[str, Any]:
    mode = release["mode"]
    lang = release["language"]
    target_profile_id = ACTIVE_PROFILES.get((mode, lang))

    current_version = None
    if target_profile_id:
        current_version = _extract_version_number(target_profile_id)

    rel_id = release["release_id"]
    source_id = release["source_id"]

    release_version = _extract_version_number(rel_id) or _extract_version_number(source_id)

    is_stale = False
    reason = "up-to-date"

    if current_version is not None and release_version is not None:
        if release_version < current_version:
            is_stale = True
            reason = f"built on v{release_version} < target v{current_version} ({target_profile_id})"
        else:
            reason = f"matches target v{current_version} ({target_profile_id})"
    elif not target_profile_id:
        reason = f"no target profile defined for {mode}/{lang}"
    else:
        reason = f"could not parse version from release_id {rel_id!r}"

    return {
        **release,
        "current_target_profile": target_profile_id,
        "release_version": f"v{release_version}" if release_version else "unknown",
        "target_version": f"v{current_version}" if current_version else "unknown",
        "is_stale": is_stale,
        "status": "STALE" if is_stale else "OK",
        "reason": reason,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Check live releases for stale WSD engines.")
    parser.add_argument("--releases-dir", type=Path, default=RELEASES_ROOT, help="Releases root directory")
    parser.add_argument("--fail-on-stale", action="store_true", help="Exit with code 1 if stale releases found")
    args = parser.parse_args()

    releases = find_active_releases(args.releases_dir)
    if not releases:
        print(f"No active releases found in {args.releases_dir}")
        return 0

    evaluated = [evaluate_release(rel) for rel in releases]

    print("\n" + "=" * 95)
    print(f"{'Mode':<8} {'Lang':<6} {'Status':<8} {'Release ID':<35} {'Target Profile':<20} {'Reason'}")
    print("=" * 95)

    stale_count = 0
    for item in sorted(evaluated, key=lambda x: (x["mode"], x["language"], x["release_id"])):
        if item["is_stale"]:
            stale_count += 1
        status_col = f"\033[91m{item['status']}\033[0m" if item["is_stale"] else f"\033[92m{item['status']}\033[0m"
        print(f"{item['mode']:<8} {item['language']:<6} {status_col:<17} {item['release_id']:<35} {str(item['current_target_profile']):<20} {item['reason']}")

    print("=" * 95)
    print(f"Total active releases: {len(evaluated)} | Stale: {stale_count} | Up-to-date: {len(evaluated) - stale_count}\n")

    if args.fail_on_stale and stale_count > 0:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
