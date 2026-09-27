#!/usr/bin/env python3
"""Package lyrics v20 releases: all-artists plus one per artist, validated.

v19's packager (package_lyrics_release_v19.py) combined two v19 decks with
Rosalía and Young Miko copied from v18. All four decks are v20 here, planted
by scripts/plant_artist_v20.py into ``lyrics-<artist>-v20``. Each release gets
the artist decks, their album art and albums.json where the retained v7 deck
has them, spotify_tracks.json, a filtered config/artists.json naming the
release, and a composition and manifest checked by validate_lyrics_release.
"""

import json
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
WORKSPACE = REPO_ROOT.parent / "Fluency-Workspace"
sys.path.insert(0, str(REPO_ROOT / "src"))

from fluency.artist.release import (  # noqa: E402
    LYRICS_COMPOSITION_VERSION,
    LYRICS_MANIFEST_VERSION,
    validate_lyrics_release,
)
from fluency.core.hashing import file_content_id  # noqa: E402

LYRICS = WORKSPACE / "releases" / "lyrics"
V7_ARTISTS = (WORKSPACE / "deployments" / "fluency-next-static-20260909-live" / "site" / "releases" / "lyrics"
              / "lyrics-all-artists-v7-native-20260825b" / "app" / "Artists")
DECKS = {
    "bad-bunny": "lyrics-bad-bunny-v20",
    "spanish-test-playlist": "lyrics-test-playlist-v20",
    "rosalia": "lyrics-rosalia-v20",
    "young-miko": "lyrics-young-miko-v20",
}
ALL = "lyrics-all-artists-v20"


def json_bytes(payload) -> bytes:
    return json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True).encode("utf-8")


def release_files(app_root: Path) -> list[dict]:
    return [
        {"path": f"app/{p.relative_to(app_root).as_posix()}", "bytes": p.stat().st_size, "content_id": file_content_id(p)}
        for p in sorted(app_root.rglob("*")) if p.is_file() and not p.name.startswith(".")
    ]


def deck_dir(slug: str) -> Path:
    return LYRICS / DECKS[slug] / "app" / "Artists" / "es" / slug


def add_artist_assets(artist_dir: Path, slug: str) -> None:
    images = V7_ARTISTS / "es" / slug / "Images"
    if images.is_dir() and not (artist_dir / "Images").exists():
        shutil.copytree(images, artist_dir / "Images")
    albums = V7_ARTISTS / "es" / slug / "albums.json"
    if albums.is_file():
        shutil.copy2(albums, artist_dir / "albums.json")


def package(release_id: str, slugs: list[str], catalog: dict, publication_status: str) -> dict:
    base = LYRICS / release_id
    app = base / "app"
    artists_root = app / "Artists" / "es"
    for slug in slugs:
        dst = artists_root / slug
        if dst != deck_dir(slug):
            if dst.exists():
                shutil.rmtree(dst)
            shutil.copytree(deck_dir(slug), dst)
        add_artist_assets(dst, slug)
    shutil.copy2(V7_ARTISTS / "spotify_tracks.json", app / "Artists" / "spotify_tracks.json")
    (app / "config").mkdir(parents=True, exist_ok=True)
    sub = {slug: {**catalog[slug], "releaseId": release_id} for slug in slugs}
    (app / "config" / "artists.json").write_bytes(json_bytes(sub))

    created_at = datetime.now(timezone.utc).isoformat()
    records, layers = [], {}
    for slug in slugs:
        d = artists_root / slug
        idx = json.loads((d / "index.json").read_text(encoding="utf-8"))
        songs = json.loads((d / "songs.json").read_text(encoding="utf-8"))
        ids = {k: file_content_id(d / f) for k, f in (("index", "index.json"), ("examples", "examples.json"),
                                                        ("master", "vocabulary_master.json"),
                                                        ("wsd_evidence", "wsd-evidence.json"))}
        records.append({
            "assignment_bridge_status": "forced_leaf_preserved_supported_specificity_not_recorded",
            "card_count": len(idx), "example_card_count": len(idx),
            "examples_content_id": ids["examples"], "index_content_id": ids["index"],
            "language": "es", "master_content_id": ids["master"],
            "migration_status": "lyrics_v20_shared_resolver_rebuild",
            "name": catalog[slug].get("name", slug), "slug": slug,
            "song_count": len(songs.get("songs", [])),
            "source_id": f"wsd_v20_plant_{slug}", "wsd_evidence_content_id": ids["wsd_evidence"],
        })
        layers[f"artist:{slug}"] = {"artifact_ids": ids, "requires": {}, "source_id": f"wsd_v20_plant_{slug}",
                                    "source_type": "lyrics_v20_plant"}
    composition = {
        "artists": records, "composition_version": LYRICS_COMPOSITION_VERSION, "conflict_policy": "error",
        "created_at": created_at, "fallback_policy": "none", "layers": layers, "mode": "lyrics",
        "omitted_layers": [], "publication_status": publication_status, "release_id": release_id,
        "wsd_profile": "es-lyrics-v20-1",
    }
    (base / "composition.json").write_bytes(json_bytes(composition))
    manifest = {
        "artist_count": len(records), "assignment_status": "lyrics_v20_margin_confidence",
        "card_count": sum(r["card_count"] for r in records),
        "catalog_content_id": file_content_id(app / "config" / "artists.json"),
        "catalog_path": "app/config/artists.json",
        "composition_content_id": file_content_id(base / "composition.json"),
        "composition_path": "composition.json", "created_at": created_at, "files": release_files(app),
        "languages": ["es"], "manifest_version": LYRICS_MANIFEST_VERSION, "mode": "lyrics",
        "publication_status": publication_status, "release_id": release_id,
        "supported_specificity_status": "not_recorded_in_materialized_sources",
    }
    (base / "manifest.json").write_bytes(json_bytes(manifest))
    m, _ = validate_lyrics_release(base)
    print(f"  [VALIDATED] {release_id}: {m['artist_count']} artists, {m['card_count']:,} cards, {len(m['files'])} files")
    return m


def main() -> None:
    catalog = json.loads((REPO_ROOT / "app" / "config" / "artists.json").read_text(encoding="utf-8"))
    package(ALL, list(DECKS), catalog, "production_release")
    for slug, release_id in DECKS.items():
        package(release_id, [slug], catalog, "candidate_release")


if __name__ == "__main__":
    main()
