"""Attach a pinned IMDb title snapshot to an existing speech release."""

from __future__ import annotations

from datetime import UTC, datetime
import json
from pathlib import Path
from typing import Any

from fluency.core.hashing import file_content_id
from fluency.core.workspace import Workspace
from fluency.harvest.source_titles import example_title_id, iter_deck_examples
from fluency.release.composition import compose_release
from fluency.release.validation import validate_release_bundle


class SourceTitlesError(ValueError):
    """Raised when a source-title snapshot cannot be joined onto a release."""


def _object(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise SourceTitlesError(f"JSON file must contain an object: {path}")
    return value


def load_source_titles(path: Path) -> dict[str, dict[str, Any]]:
    titles = _object(path)
    for title_id, metadata in titles.items():
        if not isinstance(title_id, str) or not isinstance(metadata, dict) or not metadata.get("title"):
            raise SourceTitlesError("source titles snapshot contains an invalid record")
    return titles


def attach_title_to_example(
    example: dict[str, Any],
    titles: dict[str, dict[str, Any]],
) -> str:
    """Join a human title onto one OpenSubtitles example. Mutates in place."""

    title_id = example_title_id(example)
    if not title_id:
        return "ignored"
    metadata = example.get("metadata")
    if not isinstance(metadata, dict):
        metadata = {}
        example["metadata"] = metadata
    record = titles.get(title_id)
    if record is None:
        return "unresolved"
    metadata["source_title"] = record
    return "resolved"


def attach_source_titles(
    workspace: Workspace,
    *,
    language: str,
    mode: str,
    source_release_id: str,
    target_release_id: str,
    source_titles_path: Path,
) -> tuple[Path, dict[str, int]]:
    """Publish a new inactive release; the source release remains untouched."""

    source_titles_path = source_titles_path.expanduser().resolve()
    try:
        source_titles_path.relative_to((workspace.root / "raw").resolve())
    except ValueError as error:
        raise SourceTitlesError("source titles snapshot must be inside workspace/raw") from error
    titles = load_source_titles(source_titles_path)
    source = workspace.root / "releases" / language / mode / source_release_id
    validate_release_bundle(source)
    deck = _object(source / "deck.json")
    composition = _object(source / "composition.json")
    stats = {"opensubtitles": 0, "resolved": 0, "unresolved": 0}
    for example in iter_deck_examples(deck):
        result = attach_title_to_example(example, titles)
        if result == "ignored":
            continue
        stats["opensubtitles"] += 1
        stats[result] += 1
    now = datetime.now(UTC).isoformat().replace("+00:00", "Z")
    deck["release_id"] = target_release_id
    composition["release_id"] = target_release_id
    composition["created_at"] = now
    composition["publication_status"] = "inactive_audit"
    composition["label"] = f"{composition.get('label', target_release_id)} · source titles"
    composition.setdefault("layers", {})["source_titles"] = {
        "selection_version": "layer-selection/v1",
        "source_type": "snapshot",
        "source_id": source_titles_path.parent.name,
        "artifact_id": file_content_id(source_titles_path),
        "record_count": len(titles),
        "requires": {
            "sentences": composition["layers"]["sentences"]["artifact_id"]
        },
    }
    return compose_release(workspace, composition, deck), stats
