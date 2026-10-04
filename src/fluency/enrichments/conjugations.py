"""Build a bounded, language-neutral conjugation layer from a pinned source.

The only source is Wiktionary (Kaikki), since 2026-10-04: Fred Jehle (es) and
verbecc (pt, fr) were removed. Layers already built from them stay valid
artifacts; they can no longer be rebuilt.
"""

from __future__ import annotations

from datetime import UTC, datetime
import json
from pathlib import Path
from typing import Any

from fluency.core.artifacts import ArtifactMetadata, store_artifact_bytes
from fluency.core.hashing import file_content_id
from fluency.core.workspace import Workspace
from fluency.core.io import json_bytes


LAYER_VERSION = "conjugation-layer/v1"
SOURCE_MANIFEST_VERSION = "retained-source-artifact/v1"
VERB_POS = frozenset({"VERB", "AUX", "verb", "aux"})
DEFAULT_LOCALES = {
    "es": "es-ES",
    "pt": "pt-PT",
    "fr": "fr-FR",
    "cs": "cs-CZ",
}


class ConjugationLayerError(ValueError):
    """Raised when conjugation source or menu evidence is malformed."""


def _timestamp() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")


def _safe_snapshot_id(value: str) -> str:
    if not value or any(character not in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789._-" for character in value):
        raise ConjugationLayerError("snapshot ID contains unsafe characters")
    return value


def _read_manifest(snapshot: Path) -> dict[str, Any]:
    snapshot = snapshot.expanduser().resolve()
    try:
        manifest = json.loads((snapshot / "artifact.json").read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise ConjugationLayerError("conjugation source manifest is unavailable") from error
    if (
        manifest.get("schema_version") != SOURCE_MANIFEST_VERSION
        or manifest.get("artifact_kind") != "conjugation_source"
    ):
        raise ConjugationLayerError("conjugation source manifest is incompatible")
    return manifest


def _requested_headwords(menu: dict[str, Any]) -> set[str]:
    if menu.get("menu_version") != "sense-menu/v1":
        raise ConjugationLayerError("sense menu is not a sense-menu/v1 artifact")
    language = menu.get("language")
    if not isinstance(language, str) or not language:
        raise ConjugationLayerError("sense menu is missing a language")
    requested: set[str] = set()
    for card in menu.get("cards", []):
        for analysis in card.get("analyses", []):
            if analysis.get("part_of_speech") not in VERB_POS:
                continue
            headword = str(analysis.get("headword", "")).strip().casefold()
            if headword:
                requested.add(headword)
    return requested


def _source_records(
    workspace: Workspace,
    snapshot: Path,
    manifest: dict[str, Any],
    requested: set[str],
) -> tuple[dict[str, dict[str, Any]], Path]:
    provider = manifest.get("provider")
    if provider == "kaikki":
        from fluency.enrichments.kaikki_conjugations import kaikki_records, resolve_kaikki_payload
        payload = resolve_kaikki_payload(workspace, snapshot, manifest)
        return kaikki_records(payload, requested, str(manifest.get("language") or "")), payload
    raise ConjugationLayerError(f"unsupported conjugation source provider: {provider}")


def build_conjugation_layer(
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
        raise ConjugationLayerError("sense menu is unavailable") from error
    if not isinstance(menu, dict):
        raise ConjugationLayerError("sense menu must contain an object")
    language = str(menu.get("language") or "")
    requested = _requested_headwords(menu)
    snapshot = source_snapshot.expanduser().resolve()
    manifest = _read_manifest(snapshot)
    if manifest.get("language") != language:
        raise ConjugationLayerError("conjugation source language does not match the sense menu")
    available, source_payload = _source_records(workspace, snapshot, manifest, requested)
    records = [available[headword] for headword in sorted(requested) if headword in available]
    missing = sorted(requested - available.keys())
    resolved_locale = locale or DEFAULT_LOCALES.get(language)
    if not resolved_locale:
        raise ConjugationLayerError(f"no default locale for conjugation language {language}")
    layer = {
        "layer_version": LAYER_VERSION,
        "language": language,
        "locale": resolved_locale,
        "layer_kind": "conjugations",
        "join_key": "headword",
        "source": {
            "provider": manifest["provider"],
            "snapshot_id": manifest["snapshot_id"],
            "content_id": file_content_id(source_payload),
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
        filename="conjugations.json",
        media_type="application/json",
        schema=LAYER_VERSION,
        created_by_stage="enrichment_conjugations",
        row_count=len(records),
    )
    return metadata, layer["coverage"]
