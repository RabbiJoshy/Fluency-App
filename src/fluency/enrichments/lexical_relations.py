"""Bounded optional synonym/antonym layer, joined by dictionary headword."""

from __future__ import annotations

from datetime import UTC, datetime
import json
from pathlib import Path
import shutil
from typing import Any

from fluency.core.artifacts import ArtifactMetadata, store_artifact_bytes
from fluency.core.hashing import file_content_id
from fluency.core.io import json_bytes
from fluency.core.workspace import Workspace


LAYER_VERSION = "lexical-relations/v1"
SOURCE_MANIFEST_VERSION = "retained-source-artifact/v1"
DEFAULT_LOCALES = {
    "es": "es-ES",
    "pt": "pt-PT",
    "fr": "fr-FR",
    "cs": "cs-CZ",
}


class LexicalRelationsError(ValueError):
    """Raised when a lexical-relation source or menu is malformed."""


def _timestamp() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")


def _safe_snapshot_id(value: str) -> str:
    allowed = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789._-")
    if not value or any(character not in allowed for character in value):
        raise LexicalRelationsError("snapshot ID contains unsafe characters")
    return value


def _read_manifest(snapshot: Path) -> dict[str, Any]:
    snapshot = snapshot.expanduser().resolve()
    try:
        manifest = json.loads((snapshot / "artifact.json").read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise LexicalRelationsError("lexical-relation source manifest is unavailable") from error
    if (
        manifest.get("schema_version") != SOURCE_MANIFEST_VERSION
        or manifest.get("artifact_kind") != "lexical_relation_source"
    ):
        raise LexicalRelationsError("lexical-relation source manifest is incompatible")
    return manifest


def _payload_path(snapshot: Path, manifest: dict[str, Any], workspace: Workspace) -> Path:
    files = manifest.get("content_files") or []
    if not isinstance(files, list) or not files or not isinstance(files[0], dict):
        raise LexicalRelationsError("lexical-relation source manifest has no content file")
    stored = str(files[0].get("path") or "")
    if not stored:
        raise LexicalRelationsError("lexical-relation source path is missing")
    candidate = snapshot / stored
    if not candidate.is_file():
        candidate = workspace.root / stored
    if not candidate.is_file():
        raise LexicalRelationsError(f"lexical-relation source is unavailable: {stored}")
    expected = files[0].get("sha256")
    if expected != file_content_id(candidate).removeprefix("sha256:"):
        raise LexicalRelationsError("lexical-relation source bytes do not match the manifest")
    return candidate


def requested_headwords(menu: dict[str, Any]) -> set[str]:
    if menu.get("menu_version") != "sense-menu/v1":
        raise LexicalRelationsError("sense menu is not a sense-menu/v1 artifact")
    language = menu.get("language")
    if not isinstance(language, str) or not language:
        raise LexicalRelationsError("sense menu is missing a language")
    requested: set[str] = set()
    for card in menu.get("cards", []):
        if not isinstance(card, dict):
            continue
        surface = str(card.get("surface_form") or card.get("surface_key") or "").strip()
        if surface:
            requested.add(surface.casefold())
        for analysis in card.get("analyses") or []:
            if not isinstance(analysis, dict):
                continue
            headword = str(analysis.get("headword") or "").strip()
            if headword:
                requested.add(headword.casefold())
    return requested


def normalize_relation_item(raw: Any) -> dict[str, Any] | None:
    if isinstance(raw, str):
        word = raw.strip()
        return {"word": word} if word else None
    if not isinstance(raw, dict):
        return None
    word = str(raw.get("word") or raw.get("wd") or "").strip()
    if not word:
        return None
    item: dict[str, Any] = {"word": word}
    strength = raw.get("strength")
    if isinstance(strength, int) and strength in (1, 2):
        item["strength"] = strength
    context = str(raw.get("context") or raw.get("sense") or "").strip()
    if context:
        item["context"] = context
    return item


def _merge_items(existing: list[dict[str, Any]], incoming: list[Any]) -> list[dict[str, Any]]:
    keyed: dict[tuple[str, int], dict[str, Any]] = {}
    for item in existing:
        word = str(item.get("word") or "").strip()
        if not word:
            continue
        keyed[(word.casefold(), int(item.get("strength") or 0))] = item
    for raw in incoming:
        item = normalize_relation_item(raw)
        if item is None:
            continue
        key = (item["word"].casefold(), int(item.get("strength") or 0))
        previous = keyed.get(key)
        if previous is None or (not previous.get("context") and item.get("context")):
            keyed[key] = item
    return sorted(
        keyed.values(),
        key=lambda item: (-int(item.get("strength") or 0), item["word"].casefold()),
    )


def _empty_record(headword: str) -> dict[str, Any]:
    return {"headword": headword, "synonyms": [], "antonyms": []}


def _spanishdict_records(payload: Path, requested: set[str]) -> dict[str, dict[str, Any]]:
    try:
        table = json.loads(payload.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise LexicalRelationsError("SpanishDict thesaurus fold is unavailable") from error
    if not isinstance(table, dict):
        raise LexicalRelationsError("SpanishDict thesaurus fold must be an object")
    by_key = {
        str(lemma).strip().casefold(): value
        for lemma, value in table.items()
        if isinstance(lemma, str) and str(lemma).strip()
    }
    records: dict[str, dict[str, Any]] = {}
    for headword in requested:
        raw = by_key.get(headword)
        if not isinstance(raw, dict):
            continue
        record = _empty_record(headword)
        record["synonyms"] = _merge_items([], raw.get("synonyms") or [])
        record["antonyms"] = _merge_items([], raw.get("antonyms") or [])
        if record["synonyms"] or record["antonyms"]:
            records[headword] = record
    return records


def _kaikki_records(payload: Path, requested: set[str]) -> dict[str, dict[str, Any]]:
    records: dict[str, dict[str, Any]] = {}
    try:
        stream = payload.open(encoding="utf-8")
    except OSError as error:
        raise LexicalRelationsError("Kaikki dump is unavailable") from error
    with stream:
        for line in stream:
            if not line.strip():
                continue
            row = json.loads(line)
            if not isinstance(row, dict):
                continue
            word = str(row.get("word") or "").strip()
            if not word:
                continue
            headword = word.casefold()
            if headword not in requested:
                continue
            record = records.setdefault(headword, _empty_record(headword))
            for sense in row.get("senses") or []:
                if not isinstance(sense, dict):
                    continue
                record["synonyms"] = _merge_items(record["synonyms"], sense.get("synonyms") or [])
                record["antonyms"] = _merge_items(record["antonyms"], sense.get("antonyms") or [])
    return {
        headword: record
        for headword, record in records.items()
        if record["synonyms"] or record["antonyms"]
    }


def pin_spanishdict_fold(
    workspace: Workspace,
    *,
    source: Path,
    snapshot_id: str,
) -> Path:
    """Pin the recovered SpanishDict thesaurus fold as reconstructed source."""

    snapshot_id = _safe_snapshot_id(snapshot_id)
    source = source.expanduser().resolve()
    if not source.is_file():
        raise LexicalRelationsError(f"SpanishDict thesaurus fold is unavailable: {source}")
    table = json.loads(source.read_text(encoding="utf-8"))
    if not isinstance(table, dict) or not table:
        raise LexicalRelationsError("SpanishDict thesaurus fold must be a non-empty object")
    target = workspace.root / "raw/lexical-relations/es/spanishdict" / snapshot_id
    if target.exists():
        raise LexicalRelationsError(f"lexical-relation source snapshot already exists: {target}")
    target.mkdir(parents=True)
    payload = target / "synonyms.json"
    shutil.copy2(source, payload)
    digest = file_content_id(payload)
    manifest = {
        "schema_version": SOURCE_MANIFEST_VERSION,
        "artifact_kind": "lexical_relation_source",
        "language": "es",
        "mode_scope": None,
        "provider": "spanishdict",
        "snapshot_id": snapshot_id,
        "provenance_status": "reconstructed",
        "license": "unknown",
        "source_uris": [],
        "recovered_at": _timestamp(),
        "recovered_from": str(source),
        "content_files": [{
            "path": payload.name,
            "sha256": digest.removeprefix("sha256:"),
            "bytes": payload.stat().st_size,
            "record_count": len(table),
        }],
        "notes": [
            "Recovered from Fluency/Data/Spanish/layers/synonyms.json.",
            "That file is the tool_5e fold of a SpanishDict thesaurus cache that is no longer on disk.",
            "Strength is SpanishDict's |relationship| (2 strong, 1 weak).",
        ],
    }
    (target / "artifact.json").write_bytes(json_bytes(manifest))
    return target


def pin_kaikki_dump(
    workspace: Workspace,
    *,
    source: Path,
    language: str,
    snapshot_id: str,
) -> Path:
    """Pin a Kaikki JSONL dump as Wiktionary relation evidence.

    Dumps already inside the workspace are referenced by relative path so the
    extract is not copied.
    """

    if not language or any(character not in "abcdefghijklmnopqrstuvwxyz" for character in language):
        raise LexicalRelationsError("language must be a lowercase ISO code")
    snapshot_id = _safe_snapshot_id(snapshot_id)
    source = source.expanduser().resolve()
    if not source.is_file():
        raise LexicalRelationsError(f"Kaikki dump is unavailable: {source}")
    target = workspace.root / "raw/lexical-relations" / language / "kaikki" / snapshot_id
    if target.exists():
        raise LexicalRelationsError(f"lexical-relation source snapshot already exists: {target}")
    target.mkdir(parents=True)
    try:
        relative = source.relative_to(workspace.root)
        payload = source
        stored_path = relative.as_posix()
        recovered_from = stored_path
    except ValueError:
        payload = target / source.name
        shutil.copy2(source, payload)
        stored_path = payload.name
        recovered_from = str(source)
    digest = file_content_id(payload)
    manifest = {
        "schema_version": SOURCE_MANIFEST_VERSION,
        "artifact_kind": "lexical_relation_source",
        "language": language,
        "mode_scope": None,
        "provider": "kaikki",
        "snapshot_id": snapshot_id,
        "provenance_status": "observed",
        "license": "CC-BY-SA AND GFDL",
        "source_uris": ["https://kaikki.org/dictionary/"],
        "recovered_at": _timestamp(),
        "recovered_from": recovered_from,
        "content_files": [{
            "path": stored_path,
            "sha256": digest.removeprefix("sha256:"),
            "bytes": payload.stat().st_size,
        }],
        "notes": [
            "Wiktionary has no SpanishDict-style strength; strength is omitted.",
            "Only synonyms and antonyms are folded. related/hypernyms stay unused.",
        ],
    }
    (target / "artifact.json").write_bytes(json_bytes(manifest))
    return target


def build_lexical_relations_layer(
    workspace: Workspace,
    *,
    sense_menu: Path,
    source_snapshot: Path,
    locale: str | None = None,
) -> tuple[ArtifactMetadata, dict[str, Any]]:
    """Build and store one exact layer for headwords requested by a clean menu."""

    try:
        menu = json.loads(sense_menu.read_bytes())
    except (OSError, json.JSONDecodeError) as error:
        raise LexicalRelationsError("sense menu is unavailable") from error
    if not isinstance(menu, dict):
        raise LexicalRelationsError("sense menu must contain an object")
    language = str(menu.get("language") or "")
    requested = requested_headwords(menu)
    snapshot = source_snapshot.expanduser().resolve()
    manifest = _read_manifest(snapshot)
    if manifest.get("language") != language:
        raise LexicalRelationsError("lexical-relation source language does not match the sense menu")
    payload = _payload_path(snapshot, manifest, workspace)
    provider = manifest.get("provider")
    if provider == "spanishdict":
        available = _spanishdict_records(payload, requested)
    elif provider == "kaikki":
        available = _kaikki_records(payload, requested)
    else:
        raise LexicalRelationsError(f"unsupported lexical-relation provider: {provider}")
    records = [available[headword] for headword in sorted(requested) if headword in available]
    missing = sorted(requested - available.keys())
    resolved_locale = locale or DEFAULT_LOCALES.get(language)
    if not resolved_locale:
        raise LexicalRelationsError(f"no default locale for lexical-relation language {language}")
    layer = {
        "layer_version": LAYER_VERSION,
        "language": language,
        "locale": resolved_locale,
        "layer_kind": "lexical_relations",
        "join_key": "headword",
        "source": {
            "provider": manifest["provider"],
            "snapshot_id": manifest["snapshot_id"],
            "content_id": file_content_id(payload),
            "provenance_status": manifest["provenance_status"],
        },
        "inputs": {
            "sense_menu_content_id": file_content_id(sense_menu),
            "sense_menu_snapshot_id": menu.get("snapshot_id"),
        },
        "coverage": {
            "requested_headwords": len(requested),
            "covered_headwords": len(records),
            "missing_headwords": missing,
        },
        "records": records,
    }
    metadata = store_artifact_bytes(
        workspace,
        json_bytes(layer),
        filename="lexical-relations.json",
        media_type="application/json",
        schema=LAYER_VERSION,
        created_by_stage="enrichment_lexical_relations",
        row_count=len(records),
    )
    return metadata, layer["coverage"]


def _lookup_keys_for_card(card: dict[str, Any]) -> list[str]:
    keys: list[str] = []
    seen: set[str] = set()
    for meaning in list(card.get("meanings") or []) + list(card.get("unused_menu_senses") or []):
        if not isinstance(meaning, dict):
            continue
        headword = str(meaning.get("headword") or "").strip()
        folded = headword.casefold()
        if headword and folded not in seen:
            seen.add(folded)
            keys.append(folded)
    word = str(card.get("word") or card.get("lemma") or "").strip()
    folded = word.casefold()
    if word and folded not in seen:
        keys.append(folded)
    return keys


def apply_lexical_relations_to_index(
    index: list[dict[str, Any]],
    layer: dict[str, Any],
) -> dict[str, int]:
    """Stamp synonyms/antonyms onto app index cards. Mutates in place."""

    if layer.get("layer_version") != LAYER_VERSION:
        raise LexicalRelationsError("unsupported lexical-relations layer")
    by_headword = {
        str(record.get("headword") or "").casefold(): record
        for record in layer.get("records") or []
        if isinstance(record, dict) and record.get("headword")
    }
    stamped = 0
    for card in index:
        if not isinstance(card, dict):
            continue
        synonyms: list[dict[str, Any]] = []
        antonyms: list[dict[str, Any]] = []
        for key in _lookup_keys_for_card(card):
            record = by_headword.get(key)
            if record is None:
                continue
            synonyms = _merge_items(synonyms, record.get("synonyms") or [])
            antonyms = _merge_items(antonyms, record.get("antonyms") or [])
        if synonyms:
            card["synonyms"] = synonyms
        else:
            card.pop("synonyms", None)
        if antonyms:
            card["antonyms"] = antonyms
        else:
            card.pop("antonyms", None)
        if synonyms or antonyms:
            stamped += 1
    return {"cards": len(index), "stamped": stamped, "records": len(by_headword)}
