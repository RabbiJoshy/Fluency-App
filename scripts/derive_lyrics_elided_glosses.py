#!/usr/bin/env python3
"""Derive a lyrics release whose elided spellings carry inflected glosses.

v20 inflected each card's English glosses from its display spelling, and an
elided lyric spelling (seguimo', queda', tiene') is not in the conjugation
table, so those cards kept "to follow" where "we follow" belongs
(`card_surfaces` in plant_artist_v20.py now inflects for the restored word).
Glosses are display only: WSD scored the uninflected `gloss_base`, so this
re-inflects just those cards from `gloss_base`, with the same conjugation
table and plural data the build used, and leaves every other byte as it was.

    python scripts/derive_lyrics_elided_glosses.py \\
        --source <workspace>/releases/lyrics/lyrics-all-artists-v20 \\
        --release-id lyrics-all-artists-v20-1
"""
from __future__ import annotations

import argparse
from datetime import UTC, datetime
import hashlib
import json
from pathlib import Path
import shutil
import sys

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "src"))

from fluency.lyrics.inflector import inflect_card_senses  # noqa: E402

WORKSPACE = REPO_ROOT.parent / "Fluency-Workspace"
PROFILE = REPO_ROOT / "config/wsd/models/es-lyrics-v20-1.json"


def content_id(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def elided(card: dict) -> bool:
    return str(card.get("display_form") or "").endswith(("'", "’"))


def reinflect(master: dict, conj_rev: dict, surf_cache: dict) -> list[tuple[str, list[str], list[str]]]:
    changed = []
    for card in master.values():
        if not elided(card):
            continue
        word = str(card.get("word") or "").strip()
        # Only a restored word the conjugation table knows: an unrestored
        # d-dropped participle (tiraos, dormíos) would be misread as verb +
        # pronoun ("he/she throws yourselves").
        if word.casefold() not in conj_rev:
            continue
        is_plural = any(pr.get("inflection_type") == "plural"
                        for pr in (surf_cache.get(word.casefold()) or {}).get("possible_results", []))
        before = [s.get("translation", "") for s in card["senses"]]
        after = []
        for sense in card["senses"]:
            base = sense.get("gloss_base")
            # Verbs only: a noun's plural reading belongs to its own headword
            # (eres is also the plural of ere, "the letter r", not of "being").
            if not base or sense.get("source") not in ("spanishdict", "wiktionary") \
                    or str(sense.get("pos", "")).upper() not in ("VERB", "AUX"):
                after.append(sense.get("translation", ""))
                continue
            redone = inflect_card_senses(word, sense["headword"], [{**sense, "translation": base}],
                                         conj_rev, is_plural=is_plural)[0]["translation"]
            after.append(redone)
        if after != before:
            for sense, text in zip(card["senses"], after):
                sense["translation"] = text
            changed.append((word, before, after))
    return changed


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--release-id", required=True)
    args = parser.parse_args()
    source = args.source.resolve()
    target = source.parent / args.release_id
    if target.exists():
        raise SystemExit(f"{target} exists; releases are immutable")
    snapshot = WORKSPACE / json.loads(PROFILE.read_text())["menu"]["spanishdict_snapshot"]
    conj_rev = json.loads((snapshot / "conjugation_reverse.json").read_text(encoding="utf-8"))
    surf_cache = json.loads((snapshot / "surface_cache.json").read_text(encoding="utf-8"))

    shutil.copytree(source, target)
    report = {}
    composition = json.loads((target / "composition.json").read_text(encoding="utf-8"))
    for artist_dir in sorted((target / "app/Artists/es").iterdir()):
        master_path = artist_dir / "vocabulary_master.json"
        if not master_path.is_file():
            continue
        master = json.loads(master_path.read_text(encoding="utf-8"))
        changed = reinflect(master, conj_rev, surf_cache)
        master_path.write_text(json.dumps(master, ensure_ascii=False, indent=2), encoding="utf-8")
        report[artist_dir.name] = changed
        for entry in composition.get("artists", []):
            if str(entry.get("master_path", "")).endswith(f"/{artist_dir.name}/vocabulary_master.json") \
                    or entry.get("slug") == artist_dir.name:
                entry["master_content_id"] = content_id(master_path)
        print(f"{artist_dir.name}: {len(changed)} elided cards re-glossed")

    # The release's own catalog names the release its artists load from.
    catalog_path = target / "app/config/artists.json"
    if catalog_path.is_file():
        catalog_path.write_text(catalog_path.read_text(encoding="utf-8")
                                .replace(f'"{source.name}"', f'"{args.release_id}"'), encoding="utf-8")
    composition["release_id"] = args.release_id
    composition["derived_from"] = {
        "release_id": source.name,
        "change": "elided lyric spellings re-inflected for their restored word (display glosses only)",
        "conjugation_snapshot": str(snapshot.relative_to(WORKSPACE)),
    }
    (target / "composition.json").write_text(json.dumps(composition, ensure_ascii=False, indent=2) + "\n",
                                             encoding="utf-8")
    manifest = json.loads((target / "manifest.json").read_text(encoding="utf-8"))
    manifest["release_id"] = args.release_id
    manifest["created_at"] = datetime.now(UTC).isoformat()
    manifest["derived_from"] = composition["derived_from"]
    manifest["composition_content_id"] = content_id(target / "composition.json")
    if catalog_path.is_file():
        manifest["catalog_content_id"] = content_id(catalog_path)
    for item in manifest["files"]:
        path = target / item["path"]
        item["content_id"] = content_id(path)
        item["bytes"] = path.stat().st_size
    (target / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
                                          encoding="utf-8")
    (target / "derivation-report.json").write_text(json.dumps(
        {artist: [{"word": w, "before": b, "after": a} for w, b, a in rows] for artist, rows in report.items()},
        ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"wrote {target}")


if __name__ == "__main__":
    main()
