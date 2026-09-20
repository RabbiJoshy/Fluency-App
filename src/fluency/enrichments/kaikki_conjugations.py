"""Build conjugation-layer/v1 records from a pinned Kaikki Wiktionary dump."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from fluency.core.hashing import file_content_id
from fluency.core.io import json_bytes
from fluency.core.workspace import Workspace
from fluency.enrichments.conjugations import (
    ConjugationLayerError,
    SOURCE_MANIFEST_VERSION,
    _safe_snapshot_id,
    _timestamp,
)


PROVIDER = "kaikki"
LICENSE = "CC-BY-SA AND GFDL"
VERB_POS = frozenset({"verb", "aux"})
NOISE_TAGS = frozenset({"table-tags", "inflection-template", "error-unrecognized-form"})
NOISE_FORMS = frozenset({
    "", "-", "—", "future", "future present", "no-table-tags", "inflection-box-top",
})


def pin_kaikki_snapshot(
    workspace: Workspace,
    *,
    source: Path,
    language: str,
    snapshot_id: str,
) -> Path:
    """Pin one Kaikki JSONL dump as conjugation source evidence.

    Dumps already inside the workspace are referenced by relative path so the
    193 MB Czech extract is not copied. Outside dumps are copied into the pin
    directory, matching the Jehle recovery path.
    """

    if not language or any(character not in "abcdefghijklmnopqrstuvwxyz" for character in language):
        raise ConjugationLayerError("language must be a lowercase ISO code")
    snapshot_id = _safe_snapshot_id(snapshot_id)
    source = source.expanduser().resolve()
    if not source.is_file():
        raise ConjugationLayerError(f"Kaikki dump is unavailable: {source}")
    target = workspace.root / "raw/conjugations" / language / PROVIDER / snapshot_id
    if target.exists():
        raise ConjugationLayerError(f"conjugation source snapshot already exists: {target}")
    target.mkdir(parents=True)
    try:
        relative = source.relative_to(workspace.root)
        payload = source
        stored_path = relative.as_posix()
        recovered_from = stored_path
    except ValueError:
        payload = target / source.name
        payload.write_bytes(source.read_bytes())
        stored_path = payload.name
        recovered_from = str(source)
    digest = file_content_id(payload)
    manifest = {
        "schema_version": SOURCE_MANIFEST_VERSION,
        "artifact_kind": "conjugation_source",
        "language": language,
        "mode_scope": None,
        "provider": PROVIDER,
        "snapshot_id": snapshot_id,
        "provenance_status": "observed",
        "license": LICENSE,
        "source_uris": ["https://kaikki.org/dictionary/"],
        "recovered_at": _timestamp(),
        "recovered_from": recovered_from,
        "content_files": [{
            "path": stored_path,
            "sha256": digest.removeprefix("sha256:"),
            "bytes": payload.stat().st_size,
        }],
        "notes": [
            "Wiktionary conjugation tables extracted by Kaikki/wiktextract.",
            "Join key is the lemma page headword, never the observed surface.",
            "Missing headwords stay listed; no morphology lexicon is consulted.",
        ],
    }
    (target / "artifact.json").write_bytes(json_bytes(manifest))
    return target


def resolve_kaikki_payload(workspace: Workspace | None, snapshot: Path, manifest: dict[str, Any]) -> Path:
    content = (manifest.get("content_files") or [{}])[0]
    stored = str(content.get("path") or "")
    if not stored:
        raise ConjugationLayerError("Kaikki conjugation source is missing its content path")
    candidates = [snapshot / stored]
    if workspace is not None:
        candidates.append(workspace.root / stored)
    recovered = manifest.get("recovered_from")
    if isinstance(recovered, str) and recovered:
        candidates.append(Path(recovered))
    for candidate in candidates:
        if candidate.is_file():
            if content.get("sha256") != file_content_id(candidate).removeprefix("sha256:"):
                raise ConjugationLayerError("conjugation source bytes do not match the manifest")
            return candidate
    raise ConjugationLayerError(f"Kaikki conjugation dump is unavailable: {stored}")


def _person(tags: set[str]) -> str | None:
    if "first-person" in tags:
        person = "1"
    elif "second-person" in tags:
        person = "2"
    elif "third-person" in tags:
        person = "3"
    else:
        return None
    if "singular" in tags:
        number = "s"
    elif "plural" in tags:
        number = "p"
    else:
        return None
    return person + number


def _usable_form(form: object, tags: set[str]) -> str | None:
    if not isinstance(form, str):
        return None
    text = form.strip()
    if not text or text in NOISE_FORMS or tags & NOISE_TAGS:
        return None
    if text.startswith("-") and len(text) <= 3:
        return None
    return text


def _translation(row: dict[str, Any]) -> str | None:
    for sense in row.get("senses") or []:
        if not isinstance(sense, dict):
            continue
        glosses = sense.get("glosses")
        if isinstance(glosses, list) and glosses and isinstance(glosses[0], str) and glosses[0].strip():
            return glosses[0].strip()
    return None


def _record_from_row(row: dict[str, Any]) -> dict[str, Any] | None:
    headword = str(row.get("word") or "").strip().casefold()
    if not headword or row.get("pos") not in VERB_POS:
        return None
    present: dict[str, str] = {}
    imperative: dict[str, str] = {}
    past_participle = None
    for item in row.get("forms") or []:
        if not isinstance(item, dict):
            continue
        tags = {tag for tag in item.get("tags") or [] if isinstance(tag, str)}
        form = _usable_form(item.get("form"), tags)
        if form is None:
            continue
        person = _person(tags)
        if person and "indicative" in tags and "present" in tags and "participle" not in tags and "imperative" not in tags:
            present.setdefault(person, form)
        elif person and "imperative" in tags:
            imperative.setdefault(person, form)
        elif (
            past_participle is None
            and "participle" in tags
            and "past" in tags
            and "masculine" in tags
            and "singular" in tags
        ):
            past_participle = form
    paradigms = []
    if present:
        paradigms.append({
            "mood": "indicative",
            "tense": "present",
            "forms": [{"person": person, "form": present[person]} for person in ("1s", "2s", "3s", "1p", "2p", "3p") if person in present],
        })
    if imperative:
        paradigms.append({
            "mood": "imperative",
            "tense": "present",
            "forms": [{"person": person, "form": imperative[person]} for person in ("1s", "2s", "3s", "1p", "2p", "3p") if person in imperative],
        })
    if not paradigms:
        return None
    return {
        "headword": headword,
        "translation": _translation(row),
        "nonfinite": {"gerund": None, "past_participle": past_participle},
        "paradigms": paradigms,
        "_present_count": len(present),
    }


def kaikki_records(payload: Path, requested: set[str]) -> dict[str, dict[str, Any]]:
    """Stream one dump and keep the best verb table per requested headword."""

    if not requested:
        return {}
    wanted = {item.casefold() for item in requested}
    records: dict[str, dict[str, Any]] = {}
    try:
        with payload.open(encoding="utf-8") as stream:
            for line in stream:
                if not line.strip():
                    continue
                row = json.loads(line)
                word = str(row.get("word") or "").strip().casefold()
                if word not in wanted:
                    continue
                record = _record_from_row(row)
                if record is None:
                    continue
                previous = records.get(word)
                if previous is None or record["_present_count"] > previous["_present_count"]:
                    records[word] = record
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise ConjugationLayerError(f"Kaikki conjugation dump is unreadable: {payload}") from error
    for record in records.values():
        record.pop("_present_count", None)
    return records
