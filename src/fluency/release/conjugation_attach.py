"""Attach a conjugation layer to an existing speech release, as a successor release.

Used when only the card-back tables change (French moving from verbecc to
Wiktionary on 2026-10-04): the source release stays untouched and every other
layer is carried as it is.
"""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

from fluency.core.artifacts import artifact_directory, verify_artifact
from fluency.core.workspace import Workspace
from fluency.release.composition import compose_release, load_json_object
from fluency.release.index_shards import shard_app_index
from fluency.release.lexical_relations import _copy_example_shards
from fluency.release.validation import validate_release_bundle

LAYER_VERSION = "conjugation-layer/v1"


class ConjugationAttachError(ValueError):
    """Raised when a conjugation layer cannot be joined onto a release."""


def attach_conjugations(
    workspace: Workspace,
    *,
    language: str,
    mode: str,
    source_release_id: str,
    target_release_id: str,
    artifact_id: str,
) -> Path:
    source = workspace.root / "releases" / language / mode / source_release_id
    validate_release_bundle(source)
    deck = load_json_object(source / "deck.json")
    composition = load_json_object(source / "composition.json")
    metadata = verify_artifact(workspace, artifact_id)
    if metadata.schema != LAYER_VERSION:
        raise ConjugationAttachError("selected conjugations artifact has the wrong schema")
    layer = load_json_object(artifact_directory(workspace, metadata.artifact_id) / metadata.filename)
    sense_menu_id = composition["layers"]["sense_menu"]["artifact_id"]
    if layer.get("inputs", {}).get("sense_menu_content_id") != sense_menu_id:
        raise ConjugationAttachError("conjugation layer was built from another sense menu")

    deck["release_id"] = target_release_id
    composition["release_id"] = target_release_id
    composition["created_at"] = datetime.now(UTC).isoformat().replace("+00:00", "Z")
    composition["publication_status"] = "inactive_audit"
    composition["label"] = f"{composition.get('label', target_release_id)} · conjugations"
    composition["omitted_layers"] = [
        item for item in composition.get("omitted_layers") or [] if item.get("layer") != "conjugations"
    ]
    composition.setdefault("layers", {})["conjugations"] = {
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
    validate_release_bundle(directory)
    return directory
