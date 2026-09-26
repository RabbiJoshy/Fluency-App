#!/usr/bin/env python3
"""Package and finalize Lyrics WSD v19 releases with manifests and asset parity."""

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
    v19_base = WORKSPACE / "releases" / "lyrics" / "lyrics-all-artists-v19"
    v19_app = v19_base / "app"
    v19_artists = v19_app / "Artists" / "es"

    print("1. Assembling asset parity in lyrics-all-artists-v19...")
    v19_artists.mkdir(parents=True, exist_ok=True)

    # 1. Bad Bunny (from v19 release)
    bb_src = WORKSPACE / "releases" / "lyrics" / "lyrics-bad-bunny-v19" / "app" / "Artists" / "es" / "bad-bunny"
    bb_dst = v19_artists / "bad-bunny"
    if bb_dst.exists():
        shutil.rmtree(bb_dst)
    shutil.copytree(bb_src, bb_dst)
    print("  -> Copied bad-bunny from lyrics-bad-bunny-v19")

    # 2. Spanish Test Playlist (from v19 release)
    test_src = WORKSPACE / "releases" / "lyrics" / "lyrics-test-playlist-v19" / "app" / "Artists" / "es" / "spanish-test-playlist"
    test_dst = v19_artists / "spanish-test-playlist"
    if test_dst.exists():
        shutil.rmtree(test_dst)
    shutil.copytree(test_src, test_dst)
    print("  -> Copied spanish-test-playlist from lyrics-test-playlist-v19")

    # 3. Rosalia (from v18 base)
    ros_src = v18_base / "app" / "Artists" / "es" / "rosalia"
    ros_dst = v19_artists / "rosalia"
    if ros_dst.exists():
        shutil.rmtree(ros_dst)
    shutil.copytree(ros_src, ros_dst)
    print("  -> Copied rosalia from lyrics-all-artists-v18")

    # 4. Young Miko (from v18 base)
    miko_src = v18_base / "app" / "Artists" / "es" / "young-miko"
    miko_dst = v19_artists / "young-miko"
    if miko_dst.exists():
        shutil.rmtree(miko_dst)
    shutil.copytree(miko_src, miko_dst)
    print("  -> Copied young-miko from lyrics-all-artists-v18")

    # Copy config/artists.json filtered to artists present in this release
    (v19_app / "config").mkdir(parents=True, exist_ok=True)
    raw_catalog = json.loads((REPO_ROOT / "app" / "config" / "artists.json").read_text(encoding="utf-8"))
    v19_catalog = {
        slug: dict(info)
        for slug, info in raw_catalog.items()
        if (v19_artists / slug).is_dir()
    }
    for slug, info in v19_catalog.items():
        if info.get("language") == "spanish":
            info["releaseId"] = "lyrics-all-artists-v19"
    (v19_app / "config" / "artists.json").write_bytes(json_bytes(v19_catalog))

    # Copy spotify_tracks.json
    v7_artists = v7_dir / "app" / "Artists"
    shutil.copy2(v7_artists / "spotify_tracks.json", v19_app / "Artists" / "spotify_tracks.json")

    # Copy Bad Bunny Images and albums.json
    bb_images_src = v7_artists / "es" / "bad-bunny" / "Images"
    bb_images_dst = bb_dst / "Images"
    if bb_images_src.exists() and not bb_images_dst.exists():
        shutil.copytree(bb_images_src, bb_images_dst)
    shutil.copy2(v7_artists / "es" / "bad-bunny" / "albums.json", bb_dst / "albums.json")

    # Copy Rosalia Images and albums.json
    ros_images_src = v7_artists / "es" / "rosalia" / "Images"
    ros_images_dst = ros_dst / "Images"
    if ros_images_src.exists() and not ros_images_dst.exists():
        shutil.copytree(ros_images_src, ros_images_dst)
    shutil.copy2(v7_artists / "es" / "rosalia" / "albums.json", ros_dst / "albums.json")

    # Build manifest and composition for lyrics-all-artists-v19
    print("2. Generating composition.json and manifest.json for lyrics-all-artists-v19...")
    created_at = datetime.now(timezone.utc).isoformat()
    catalog = json.loads((v19_app / "config" / "artists.json").read_text(encoding="utf-8"))

    artist_records = []
    layers = {}

    for slug, info in catalog.items():
        lang = info.get("language", "spanish")
        lang_code = "es" if lang == "spanish" else "fr"
        artist_dir = v19_app / "Artists" / lang_code / slug
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
            "source_id": f"wsd_v19_plant_{slug}",
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
            "source_id": f"wsd_v19_plant_{slug}",
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
        "release_id": "lyrics-all-artists-v19",
    }

    comp_path = v19_base / "composition.json"
    comp_path.write_bytes(json_bytes(composition))

    catalog_path = v19_app / "config" / "artists.json"
    manifest = {
        "artist_count": len(artist_records),
        "assignment_status": "native_v7_and_retained_forced_leaf_assignments",
        "card_count": sum(r["card_count"] for r in artist_records),
        "catalog_content_id": file_content_id(catalog_path),
        "catalog_path": "app/config/artists.json",
        "composition_content_id": file_content_id(comp_path),
        "composition_path": "composition.json",
        "created_at": created_at,
        "files": release_files(v19_app),
        "languages": sorted({r["language"] for r in artist_records}),
        "manifest_version": LYRICS_MANIFEST_VERSION,
        "mode": "lyrics",
        "publication_status": "production_release",
        "release_id": "lyrics-all-artists-v19",
        "supported_specificity_status": "available_for_native_v7_artists",
    }

    manifest_path = v19_base / "manifest.json"
    manifest_path.write_bytes(json_bytes(manifest))

    print("3. Validating lyrics-all-artists-v19 release...")
    m, c = validate_lyrics_release(v19_base)
    print(f"  [VALIDATED] manifest has {m['artist_count']} artists, {m['card_count']} cards, {len(m['files'])} files.")

    # Also package single release for bad-bunny
    bb_rel = WORKSPACE / "releases" / "lyrics" / "lyrics-bad-bunny-v19"
    (bb_rel / "app" / "config").mkdir(parents=True, exist_ok=True)
    shutil.copy2(v7_artists / "spotify_tracks.json", bb_rel / "app" / "Artists" / "spotify_tracks.json")
    if not (bb_rel / "app" / "Artists" / "es" / "bad-bunny" / "Images").exists():
        shutil.copytree(bb_images_src, bb_rel / "app" / "Artists" / "es" / "bad-bunny" / "Images")
    shutil.copy2(v7_artists / "es" / "bad-bunny" / "albums.json", bb_rel / "app" / "Artists" / "es" / "bad-bunny" / "albums.json")
    bb_cat = {"bad-bunny": dict(catalog["bad-bunny"])}
    bb_cat["bad-bunny"]["releaseId"] = "lyrics-bad-bunny-v19"
    (bb_rel / "app" / "config" / "artists.json").write_bytes(json_bytes(bb_cat))
    bb_rec = [r for r in artist_records if r["slug"] == "bad-bunny"]
    bb_comp = {
        "artists": bb_rec,
        "composition_version": LYRICS_COMPOSITION_VERSION,
        "conflict_policy": "error",
        "created_at": created_at,
        "fallback_policy": "none",
        "layers": {"artist:bad-bunny": layers["artist:bad-bunny"]},
        "mode": "lyrics",
        "omitted_layers": [],
        "publication_status": "candidate_release",
        "release_id": "lyrics-bad-bunny-v19",
    }
    (bb_rel / "composition.json").write_bytes(json_bytes(bb_comp))
    bb_manifest = {
        "artist_count": 1,
        "assignment_status": "forced_leaf_assignments_preserved_in_dual_view_contract",
        "card_count": bb_rec[0]["card_count"],
        "catalog_content_id": file_content_id(bb_rel / "app" / "config" / "artists.json"),
        "catalog_path": "app/config/artists.json",
        "composition_content_id": file_content_id(bb_rel / "composition.json"),
        "composition_path": "composition.json",
        "created_at": created_at,
        "files": release_files(bb_rel / "app"),
        "languages": ["es"],
        "manifest_version": LYRICS_MANIFEST_VERSION,
        "mode": "lyrics",
        "publication_status": "candidate_release",
        "release_id": "lyrics-bad-bunny-v19",
        "supported_specificity_status": "not_recorded_in_materialized_sources",
    }
    (bb_rel / "manifest.json").write_bytes(json_bytes(bb_manifest))
    validate_lyrics_release(bb_rel)
    print("  [VALIDATED] lyrics-bad-bunny-v19 manifest and composition verified.")


if __name__ == "__main__":
    main()
