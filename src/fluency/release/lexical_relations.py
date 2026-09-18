"""Attach a pinned lexical-relations layer to an existing speech release."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
import shutil
from typing import Any

from fluency.core.artifacts import artifact_directory, verify_artifact
from fluency.core.workspace import Workspace
from fluency.enrichments.lexical_relations import LAYER_VERSION
from fluency.release.composition import compose_release, load_json_object
from fluency.release.index_shards import shard_app_index
from fluency.release.validation import validate_release_bundle


class LexicalRelationsAttachError(ValueError):
    """Raised when a lexical-relations layer cannot be joined onto a release."""


def attach_lexical_relations(
    workspace: Workspace,
    *,
    language: str,
    mode: str,
    source_release_id: str,
    target_release_id: str,
    artifact_id: str,
) -> tuple[Path, dict[str, int]]:
    """Publish a new inactive release; the source release remains untouched."""

    source = workspace.root / "releases" / language / mode / source_release_id
    validate_release_bundle(source)
    deck = load_json_object(source / "deck.json")
    composition = load_json_object(source / "composition.json")
    metadata = verify_artifact(workspace, artifact_id)
    if metadata.schema != LAYER_VERSION:
        raise LexicalRelationsAttachError("selected lexical-relations artifact has the wrong schema")
    layer_path = artifact_directory(workspace, metadata.artifact_id) / metadata.filename
    layer = load_json_object(layer_path)
    if layer.get("language") != language:
        raise LexicalRelationsAttachError("lexical-relations language does not match the release")
    sense_menu_id = composition["layers"]["sense_menu"]["artifact_id"]
    if layer.get("inputs", {}).get("sense_menu_content_id") != sense_menu_id:
        raise LexicalRelationsAttachError("lexical-relations artifact was built from another sense menu")

    now = datetime.now(UTC).isoformat().replace("+00:00", "Z")
    deck["release_id"] = target_release_id
    composition["release_id"] = target_release_id
    composition["created_at"] = now
    composition["publication_status"] = "inactive_audit"
    composition["label"] = f"{composition.get('label', target_release_id)} · lexical relations"
    omitted = [
        item
        for item in composition.get("omitted_layers") or []
        if item.get("layer") != "lexical_relations"
    ]
    composition["omitted_layers"] = omitted
    composition.setdefault("layers", {})["lexical_relations"] = {
        "selection_version": "layer-selection/v1",
        "source_type": "snapshot",
        "source_id": str(layer.get("source", {}).get("snapshot_id") or metadata.artifact_id),
        "artifact_id": metadata.artifact_id,
        "record_count": metadata.row_count or len(layer.get("records") or []),
        "requires": {"sense_menu": sense_menu_id},
    }
    directory = compose_release(workspace, composition, deck)
    if (source / "app" / "vocabulary.index.manifest.json").is_file():
        shard_app_index(directory / "app")
    if (source / "app" / "vocabulary.examples.manifest.json").is_file():
        _copy_example_shards(source / "app", directory / "app")
    stats = {
        "records": int(metadata.row_count or 0),
        "index_bytes": (directory / "app" / "vocabulary.index.json").stat().st_size,
    }
    return directory, stats


def _copy_example_shards(source_app: Path, target_app: Path) -> None:
    manifest_name = "vocabulary.examples.manifest.json"
    shard_dir_name = "vocabulary.examples.shards"
    shutil.copy2(source_app / manifest_name, target_app / manifest_name)
    source_dir = source_app / shard_dir_name
    target_dir = target_app / shard_dir_name
    if not source_dir.is_dir():
        return
    target_dir.mkdir(parents=True, exist_ok=True)
    for path in source_dir.iterdir():
        if path.is_file():
            shutil.copy2(path, target_dir / path.name)
