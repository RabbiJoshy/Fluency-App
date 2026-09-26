#!/usr/bin/env python3
"""Package and finalize Lyrics WSD v18 releases with manifests and asset parity."""

import hashlib
import json
import os
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
WORKSPACE = REPO_ROOT.parent / "Fluency-Workspace"
sys.path.insert(0, str(REPO_ROOT / "src"))

from fluency.artist.release import (
    LYRICS_COMPOSITION_VERSION,
    LYRICS_MANIFEST_VERSION,
    validate_lyrics_release,
)
from fluency.core.hashing import file_content_id


def json_bytes(payload) -> bytes:
    return json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True).encode("utf-8")


def release_files(app_root: Path) -> list[dict]:
    records = []
    for path in sorted(app_root.rglob("*")):
        if not path.is_file() or path.name.startswith("."):
            continue
        rel = f"app/{path.relative_to(app_root).as_posix()}"
        records.append({
            "path": rel,
            "bytes": path.stat().st_size,
            "content_id": file_content_id(path),
        })
    return records


def main():
    v7_dir = WORKSPACE / "deployments" / "fluency-next-static-20260909-live" / "site" / "releases" / "lyrics" / "lyrics-all-artists-v7-native-20260825b"
    v18_base = WORKSPACE / "releases" / "lyrics" / "lyrics-all-artists-v18"
    v18_app = v18_base / "app"

    print("1. Assembling asset parity in lyrics-all-artists-v18...")

    # Copy config/artists.json filtered to artists in this release
    (v18_app / "config").mkdir(parents=True, exist_ok=True)
    raw_catalog = json.loads((REPO_ROOT / "app" / "config" / "artists.json").read_text(encoding="utf-8"))
    v18_catalog = {slug: info for slug, info in raw_catalog.items() if info.get("releaseId") == "lyrics-all-artists-v18"}
    (v18_app / "config" / "artists.json").write_bytes(json_bytes(v18_catalog))

    # Copy spotify_tracks.json
    v7_artists = v7_dir / "app" / "Artists"
    shutil.copy2(v7_artists / "spotify_tracks.json", v18_app / "Artists" / "spotify_tracks.json")
    if (v18_app / "Artists" / "fr").exists():
        shutil.rmtree(v18_app / "Artists" / "fr")

    # Copy Bad Bunny Images and albums.json
    bb_images_src = v7_artists / "es" / "bad-bunny" / "Images"
    bb_images_dst = v18_app / "Artists" / "es" / "bad-bunny" / "Images"
    if bb_images_src.exists() and not bb_images_dst.exists():
        shutil.copytree(bb_images_src, bb_images_dst)
        print("  -> Copied Bad Bunny Images")
    shutil.copy2(v7_artists / "es" / "bad-bunny" / "albums.json", v18_app / "Artists" / "es" / "bad-bunny" / "albums.json")

    # Copy Rosalia Images and albums.json
    ros_images_src = v7_artists / "es" / "rosalia" / "Images"
    ros_images_dst = v18_app / "Artists" / "es" / "rosalia" / "Images"
    if ros_images_src.exists() and not ros_images_dst.exists():
        shutil.copytree(ros_images_src, ros_images_dst)
        print("  -> Copied Rosalía Images")
    shutil.copy2(v7_artists / "es" / "rosalia" / "albums.json", v18_app / "Artists" / "es" / "rosalia" / "albums.json")

    # Copy spanish-test-playlist
    test_src = WORKSPACE / "releases" / "lyrics" / "lyrics-test-playlist-v16-20260925" / "app" / "Artists" / "es" / "spanish-test-playlist"
    test_dst = v18_app / "Artists" / "es" / "spanish-test-playlist"
    if test_src.is_dir() and not test_dst.exists():
        shutil.copytree(test_src, test_dst)
        print("  -> Copied spanish-test-playlist")

    # Build manifest and composition for lyrics-all-artists-v18
    print("2. Generating composition.json and manifest.json for lyrics-all-artists-v18...")
    created_at = datetime.now(timezone.utc).isoformat()
    catalog = json.loads((v18_app / "config" / "artists.json").read_text(encoding="utf-8"))

    artist_records = []
    layers = {}

    for slug, info in catalog.items():
        lang = info.get("language", "spanish")
        lang_code = "es" if lang == "spanish" else "fr"
        artist_dir = v18_app / "Artists" / lang_code / slug
        if not artist_dir.exists():
            continue

        idx_path = artist_dir / "index.json"
        ex_path = artist_dir / "examples.json"
        m_path = artist_dir / "vocabulary_master.json"
        wsd_path = artist_dir / "wsd-evidence.json"
        songs_path = artist_dir / "songs.json"

        idx = json.loads(idx_path.read_text(encoding="utf-8")) if idx_path.exists() else []
        songs = json.loads(songs_path.read_text(encoding="utf-8")) if songs_path.exists() else {}

        idx_cid = file_content_id(idx_path)
        ex_cid = file_content_id(ex_path)
        m_cid = file_content_id(m_path)
        wsd_cid = file_content_id(wsd_path) if wsd_path.exists() else None

        record = {
            "assignment_bridge_status": "native_v7_forced_and_supported_available" if slug == "rosalia" else "forced_leaf_preserved_supported_specificity_not_recorded",
            "card_count": len(idx),
            "example_card_count": len(idx),
            "examples_content_id": ex_cid,
            "index_content_id": idx_cid,
            "language": lang_code,
            "master_content_id": m_cid,
            "migration_status": "retained_materialized_output_for_product_parity",
            "name": info.get("name", slug),
            "slug": slug,
            "song_count": len(songs.get("songs", [])),
            "source_id": f"wsd_v18_plant_{slug}",
            "wsd_evidence_content_id": wsd_cid,
        }
        artist_records.append(record)

        layers[f"artist:{slug}"] = {
            "artifact_ids": {
                "examples": ex_cid,
                "index": idx_cid,
                "master": m_cid,
                **({"wsd_evidence": wsd_cid} if wsd_cid else {}),
            },
            "requires": {},
            "source_id": f"wsd_v18_plant_{slug}",
            "source_type": "retained_materialized_output",
        }

    composition = {
        "artists": artist_records,
        "composition_version": LYRICS_COMPOSITION_VERSION,
        "conflict_policy": "error",
        "created_at": created_at,
        "fallback_policy": "none",
        "layers": layers,
        "mode": "lyrics",
        "omitted_layers": [
            {
                "layer": "clean_artist_pipeline_rebuild",
                "reason": "materialized parity assets retained; assignments were not recomputed",
            }
        ],
        "publication_status": "production_release",
        "release_id": "lyrics-all-artists-v18",
    }

    comp_path = v18_base / "composition.json"
    comp_path.write_bytes(json_bytes(composition))

    catalog_path = v18_app / "config" / "artists.json"
    manifest = {
        "artist_count": len(artist_records),
        "assignment_status": "native_v7_and_retained_forced_leaf_assignments",
        "card_count": sum(r["card_count"] for r in artist_records),
        "catalog_content_id": file_content_id(catalog_path),
        "catalog_path": "app/config/artists.json",
        "composition_content_id": file_content_id(comp_path),
        "composition_path": "composition.json",
        "created_at": created_at,
        "files": release_files(v18_app),
        "languages": sorted({r["language"] for r in artist_records}),
        "manifest_version": LYRICS_MANIFEST_VERSION,
        "mode": "lyrics",
        "publication_status": "production_release",
        "release_id": "lyrics-all-artists-v18",
        "supported_specificity_status": "available_for_native_v7_artists",
    }

    manifest_path = v18_base / "manifest.json"
    manifest_path.write_bytes(json_bytes(manifest))

    print("3. Validating lyrics-all-artists-v18 release...")
    m, c = validate_lyrics_release(v18_base)
    print(f"  [VALIDATED] manifest has {m['artist_count']} artists, {m['card_count']} cards, {len(m['files'])} files.")

    # Also generate manifest/composition for per-artist decks
    for slug in ["bad-bunny", "rosalia", "young-miko"]:
        artist_rel = WORKSPACE / "releases" / "lyrics" / f"lyrics-{slug}-v18"
        artist_app = artist_rel / "app"
        if not artist_rel.exists():
            continue

        # Copy images if any
        if slug == "bad-bunny":
            bb_img_dst = artist_app / "Artists" / "es" / slug / "Images"
            if not bb_img_dst.exists() and bb_images_src.exists():
                shutil.copytree(bb_images_src, bb_img_dst)
            shutil.copy2(v7_artists / "es" / slug / "albums.json", artist_app / "Artists" / "es" / slug / "albums.json")
        elif slug == "rosalia":
            ros_img_dst = artist_app / "Artists" / "es" / slug / "Images"
            if not ros_img_dst.exists() and ros_images_src.exists():
                shutil.copytree(ros_images_src, ros_img_dst)
            shutil.copy2(v7_artists / "es" / slug / "albums.json", artist_app / "Artists" / "es" / slug / "albums.json")

        # Copy single artist config and spotify_tracks.json
        (artist_app / "config").mkdir(parents=True, exist_ok=True)
        shutil.copy2(v7_artists / "spotify_tracks.json", artist_app / "Artists" / "spotify_tracks.json")
        single_cat = {slug: dict(catalog[slug])}
        single_cat[slug]["releaseId"] = f"lyrics-{slug}-v18"
        (artist_app / "config" / "artists.json").write_bytes(json_bytes(single_cat))

        single_rec = [r for r in artist_records if r["slug"] == slug]
        single_comp = {
            "artists": single_rec,
            "composition_version": LYRICS_COMPOSITION_VERSION,
            "conflict_policy": "error",
            "created_at": created_at,
            "fallback_policy": "none",
            "layers": {f"artist:{slug}": layers[f"artist:{slug}"]},
            "mode": "lyrics",
            "omitted_layers": [],
            "publication_status": "candidate_release",
            "release_id": f"lyrics-{slug}-v18",
        }
        (artist_rel / "composition.json").write_bytes(json_bytes(single_comp))

        single_manifest = {
            "artist_count": len(single_rec),
            "assignment_status": "native_v7_and_retained_forced_leaf_assignments" if slug == "rosalia" else "forced_leaf_assignments_preserved_in_dual_view_contract",
            "card_count": sum(r["card_count"] for r in single_rec),
            "catalog_content_id": file_content_id(artist_app / "config" / "artists.json"),
            "catalog_path": "app/config/artists.json",
            "composition_content_id": file_content_id(artist_rel / "composition.json"),
            "composition_path": "composition.json",
            "created_at": created_at,
            "files": release_files(artist_app),
            "languages": ["es"],
            "manifest_version": LYRICS_MANIFEST_VERSION,
            "mode": "lyrics",
            "publication_status": "candidate_release",
            "release_id": f"lyrics-{slug}-v18",
            "supported_specificity_status": "available_for_native_v7_artists" if slug == "rosalia" else "not_recorded_in_materialized_sources",
        }
        (artist_rel / "manifest.json").write_bytes(json_bytes(single_manifest))

        validate_lyrics_release(artist_rel)
        print(f"  [VALIDATED] lyrics-{slug}-v18 manifest and composition verified.")

    print("\nAll v18 releases packaged and validated cleanly!")


if __name__ == "__main__":
    main()
