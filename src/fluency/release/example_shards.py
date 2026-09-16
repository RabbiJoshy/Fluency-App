"""Split the app examples monolith into per-study-set shards.

The learner studies 20 cards at a time. The live speech payload still ships
one 80 MB examples file, so opening any set parses the whole deck. Shards
let the app fetch the current set and greedily prefetch the next one.

The monolith remains in place as a fallback for older clients.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


MANIFEST_VERSION = "example-shards/v1"
SHARD_DIRECTORY = "vocabulary.examples.shards"
MANIFEST_NAME = "vocabulary.examples.manifest.json"


class ExampleShardError(ValueError):
    """Raised when examples cannot be split along the study structure."""


def _object(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ExampleShardError(f"JSON file must contain an object: {path}")
    return value


def _object_list(path: Path) -> list[Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, list):
        raise ExampleShardError(f"JSON file must contain a list: {path}")
    return value


def _json_bytes(value: object) -> bytes:
    return (json.dumps(value, ensure_ascii=False, separators=(",", ":")) + "\n").encode("utf-8")


def shard_app_examples(release_app_dir: Path) -> dict[str, Any]:
    """Write one shard per study set beside the existing examples monolith."""

    app_dir = release_app_dir.expanduser().resolve()
    examples_path = app_dir / "vocabulary.examples.json"
    index_path = app_dir / "vocabulary.index.json"
    structure_path = app_dir / "study-structure.json"
    if not examples_path.is_file() or not index_path.is_file() or not structure_path.is_file():
        raise ExampleShardError(f"release app directory is missing examples, index, or study structure: {app_dir}")

    examples = _object(examples_path)
    index = _object_list(index_path)
    structure = _object(structure_path)
    id_by_surface = {
        str(card.get("surface_card_id") or ""): str(card.get("id") or "")
        for card in index
        if isinstance(card, dict)
    }
    shard_dir = app_dir / SHARD_DIRECTORY
    shard_dir.mkdir(parents=True, exist_ok=True)
    shards: list[dict[str, Any]] = []
    missing = 0
    for level in structure.get("levels") or []:
        if not isinstance(level, dict):
            continue
        for study_set in level.get("sets") or []:
            if not isinstance(study_set, dict):
                continue
            set_id = str(study_set.get("set_id") or "")
            if not set_id:
                raise ExampleShardError("study set is missing set_id")
            payload: dict[str, Any] = {}
            for card_id in study_set.get("card_ids") or []:
                app_id = id_by_surface.get(str(card_id), "")
                if not app_id or app_id not in examples:
                    missing += 1
                    continue
                payload[app_id] = examples[app_id]
            filename = f"{set_id}.json"
            (shard_dir / filename).write_bytes(_json_bytes(payload))
            shards.append(
                {
                    "set_id": set_id,
                    "start_rank": int(study_set["start_rank"]),
                    "end_rank": int(study_set["end_rank"]),
                    "path": f"{SHARD_DIRECTORY}/{filename}",
                    "cards": len(payload),
                }
            )
    if not shards:
        raise ExampleShardError("study structure contains no sets")
    manifest = {
        "manifest_version": MANIFEST_VERSION,
        "fallback": "vocabulary.examples.json",
        "shard_count": len(shards),
        "missing_cards": missing,
        "shards": shards,
    }
    (app_dir / MANIFEST_NAME).write_bytes(_json_bytes(manifest))
    return manifest
