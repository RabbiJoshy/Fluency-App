"""Split the app vocabulary index into skinny columns plus per-set rows.

Setup and stats need id/word/rank for the whole deck. Senses and leftover
menu leaves are only needed for the twenty cards in the active set. The
monolith remains as a fallback for older clients.

With ``slim=True`` row shards drop what the app never reads (``slim_index_row``):
etymology and raw glosses, analysis bookkeeping ids, WSD count tables it does
not use, and the second copy of provider metadata and specialist features that
the release carries in two places. Nothing is added or renamed, so the app
reads a slim row exactly as a full one; the monolith keeps everything.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any


MANIFEST_VERSION = "index-shards/v1"
SLIM_MANIFEST_VERSION = "index-shards/v2"
SLIM_ROW_FORMAT = "slim-index-row/v1"
# Read by nothing in app/js (checked field by field); the audit copy is the
# monolith and deck.json.
_UNREAD_SENSE_FIELDS = ("menu_analysis_id", "source_sense_id")
_UNREAD_METADATA_FIELDS = ("source_analysis_key", "source_edition")
_UNREAD_SENSE_METADATA_FIELDS = ("coverage", "ignored", "unclassified")
_UNREAD_PROVIDER_FIELDS = ("etymology_text", "raw_glosses")
# vocab.js projectedSenseFrequency and the card model read only these.
_READ_DISTRIBUTION_FIELDS = ("distribution_version", "denominator",
                             "supported_leaf_counts", "supported_level_counts")
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
    """The app's assignedHeadwordOf: the headword of the most frequent meaning."""

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


def _spelling(value: str) -> str:
    return re.sub(r"[\s\-‐]+", "", value).casefold()


def card_lemma(card: dict[str, Any]) -> str:
    """The shipped ``lemma`` column: the assigned headword among the meanings
    that can name this word's lemma.

    A headword with more words than the card's surface names an expression the
    word occurs in, not its lemma: ``não é`` on é, ``por qué`` on por. It used to
    win whenever the phrase was the single most frequent meaning, so é shipped
    lemma ``não é`` though its six ``ser`` meanings outweigh it. The same
    spelling written apart still counts (porfavor, ``por favor``). With no
    meaning left the column is empty and the app keeps the card on its own.
    """

    word = str(card.get("word") or "")
    words = max(len(word.split()), 1)
    meanings = [
        meaning
        for meaning in card.get("meanings") or []
        if isinstance(meaning, dict)
        and (
            len(str(meaning.get("headword") or "").split()) <= words
            or _spelling(str(meaning.get("headword"))) == _spelling(word)
        )
    ]
    return assigned_headword(meanings)


def _slim_sense(sense: Any) -> Any:
    if not isinstance(sense, dict):
        return sense
    sense = {key: value for key, value in sense.items() if key not in _UNREAD_SENSE_FIELDS}
    metadata = sense.get("metadata")
    if not isinstance(metadata, dict):
        return sense
    metadata = {key: value for key, value in metadata.items() if key not in _UNREAD_METADATA_FIELDS}
    provider = metadata.get("sense_provider_metadata")
    if isinstance(provider, dict):
        provider = {k: v for k, v in provider.items() if k not in _UNREAD_PROVIDER_FIELDS}
        metadata["sense_provider_metadata"] = provider
    canonical = metadata.get("sense_metadata")
    if isinstance(canonical, dict):
        canonical = {k: v for k, v in canonical.items() if k not in _UNREAD_SENSE_METADATA_FIELDS}
        source = canonical.get("source_metadata")
        if isinstance(source, dict):
            source = {k: v for k, v in source.items() if k not in _UNREAD_PROVIDER_FIELDS}
            # Every reader tries sense_provider_metadata when this is absent.
            if source == provider:
                canonical.pop("source_metadata")
            else:
                canonical["source_metadata"] = source
        # The pills concatenate both lists and drop repeats; one copy suffices.
        if metadata.get("specialist_features") == canonical.get("features"):
            metadata.pop("specialist_features", None)
        metadata["sense_metadata"] = canonical
    sense["metadata"] = metadata
    return sense


def slim_index_row(row: dict[str, Any]) -> dict[str, Any]:
    """A row shard entry without the fields the app never reads."""

    slim = dict(row)
    for field in ("meanings", "unused_menu_senses"):
        if isinstance(slim.get(field), list):
            slim[field] = [_slim_sense(sense) for sense in slim[field]]
    distribution = slim.get("wsd_distribution")
    if isinstance(distribution, dict):
        slim["wsd_distribution"] = {k: distribution[k] for k in _READ_DISTRIBUTION_FIELDS if k in distribution}
    return slim


def shard_app_index(release_app_dir: Path, *, slim: bool = False) -> dict[str, Any]:
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
                values.append(card_lemma(card) or None)
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
                payload[app_id] = slim_index_row(fat) if slim else fat
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
        "manifest_version": SLIM_MANIFEST_VERSION if slim else MANIFEST_VERSION,
        "fallback": "vocabulary.index.json",
        "columns": COLUMNS_NAME,
        "fat_fields": list(FAT_FIELDS),
        "shard_count": len(shards),
        "missing_cards": missing,
        "shards": shards,
    }
    if slim:
        manifest["row_format"] = SLIM_ROW_FORMAT
    (app_dir / MANIFEST_NAME).write_bytes(_json_bytes(manifest))
    return manifest
