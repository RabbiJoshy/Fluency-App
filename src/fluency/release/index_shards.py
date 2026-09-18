"""Split the app vocabulary index into skinny columns plus per-set rows.

Setup and stats need id/word/rank for the whole deck. Senses and leftover
menu leaves are only needed for the twenty cards in the active set. The
monolith remains as a fallback for older clients.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


MANIFEST_VERSION = "index-shards/v1"
COLUMNS_SCHEMA = "vocabulary-index-columns/v1"
COLUMNS_NAME = "vocabulary.index.columns.json"
SHARD_DIRECTORY = "vocabulary.index.rows"
MANIFEST_NAME = "vocabulary.index.manifest.json"
FAT_FIELDS = ("meanings", "unused_menu_senses", "wsd_distribution", "synonyms", "antonyms")


class IndexShardError(ValueError):
    """Raised when the index cannot be split along the study structure."""


def _object(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise IndexShardError(f"JSON file must contain an object: {path}")
    return value


def _object_list(path: Path) -> list[Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, list):
        raise IndexShardError(f"JSON file must contain a list: {path}")
    return value


def _json_bytes(value: object) -> bytes:
    return (json.dumps(value, ensure_ascii=False, separators=(",", ":")) + "\n").encode("utf-8")


def assigned_headword(meanings: Any) -> str:
    """Match the app's assignedHeadwordOf grouping key for Merge Lemmas."""

    scored: list[tuple[float, str]] = []
    first = ""
    for meaning in meanings or []:
        if not isinstance(meaning, dict):
            continue
        headword = str(meaning.get("headword") or "").strip()
        if not headword:
            continue
        if not first:
            first = headword
        try:
            frequency = float(meaning.get("percentage") if meaning.get("percentage") is not None else meaning.get("frequency") or 0)
        except (TypeError, ValueError):
            frequency = 0.0
        if frequency > 0:
            scored.append((frequency, headword))
    if scored:
        return max(scored, key=lambda item: item[0])[1]
    return first


def shard_app_index(release_app_dir: Path) -> dict[str, Any]:
    """Write columnar identity fields and one fat-row shard per study set."""

    app_dir = release_app_dir.expanduser().resolve()
    index_path = app_dir / "vocabulary.index.json"
    structure_path = app_dir / "study-structure.json"
    if not index_path.is_file() or not structure_path.is_file():
        raise IndexShardError(f"release app directory is missing index or study structure: {app_dir}")

    index = _object_list(index_path)
    structure = _object(structure_path)
    by_surface: dict[str, dict[str, Any]] = {}
    skinny_fields: set[str] = set()
    for card in index:
        if not isinstance(card, dict):
            continue
        surface = str(card.get("surface_card_id") or "")
        if surface:
            by_surface[surface] = card
        skinny_fields.update(key for key in card if key not in FAT_FIELDS)

    ordered_fields = [
        field
        for field in ("id", "word", "rank", "surface_card_id", "lemma")
        if field in skinny_fields or field == "lemma"
    ]
    for field in sorted(skinny_fields):
        if field not in ordered_fields:
            ordered_fields.append(field)

    columns: dict[str, Any] = {
        "schema": COLUMNS_SCHEMA,
        "n": len(index),
    }
    for field in ordered_fields:
        values = []
        for card in index:
            if not isinstance(card, dict):
                values.append(None)
                continue
            if field == "lemma" and "lemma" not in card:
                values.append(assigned_headword(card.get("meanings")) or None)
            else:
                values.append(card.get(field))
        columns[field] = values
    (app_dir / COLUMNS_NAME).write_bytes(_json_bytes(columns))

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
                raise IndexShardError("study set is missing set_id")
            payload: dict[str, Any] = {}
            for card_id in study_set.get("card_ids") or []:
                card = by_surface.get(str(card_id))
                if not isinstance(card, dict):
                    missing += 1
                    continue
                app_id = str(card.get("id") or "")
                if not app_id:
                    missing += 1
                    continue
                fat = {field: card[field] for field in FAT_FIELDS if field in card}
                payload[app_id] = fat
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
        raise IndexShardError("study structure contains no sets")
    manifest = {
        "manifest_version": MANIFEST_VERSION,
        "fallback": "vocabulary.index.json",
        "columns": COLUMNS_NAME,
        "fat_fields": list(FAT_FIELDS),
        "shard_count": len(shards),
        "missing_cards": missing,
        "shards": shards,
    }
    (app_dir / MANIFEST_NAME).write_bytes(_json_bytes(manifest))
    return manifest
