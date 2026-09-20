"""Build conjugation-layer/v1 records from pinned verbecc XML. ML stays off."""

from __future__ import annotations

from pathlib import Path
import shutil
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


PROVIDER = "verbecc"
LICENSE = "GPL-2.0-or-later"
SUPPORTED = frozenset({"pt", "fr"})
UNSUPPORTED = {
    "cs": "Czech is not in verbecc; use the pinned Kaikki conjugation source.",
    "nl": "Dutch has no live speech menu or release, and verbecc has no nl language.",
}

# Bounded simple tenses. Compounds stay out of the first layer, matching Jehle.
BOUNDED_TENSES = {
    "pt": {
        ("indicativo", "presente"),
        ("indicativo", "pretérito-perfeito"),
        ("indicativo", "pretérito-imperfeito"),
        ("indicativo", "futuro-do-presente"),
        ("condicional", "futuro-do-pretérito"),
        ("subjuntivo", "presente"),
        ("subjuntivo", "pretérito-imperfeito"),
        ("subjuntivo", "futuro"),
        ("imperativo", "afirmativo"),
        ("imperativo", "negativo"),
    },
    "fr": {
        ("indicatif", "présent"),
        ("indicatif", "imparfait"),
        ("indicatif", "futur-simple"),
        ("indicatif", "passé-simple"),
        ("conditionnel", "présent"),
        ("subjonctif", "présent"),
        ("subjonctif", "imparfait"),
        ("imperatif", "imperatif-présent"),
    },
}

PERSON_PREFERENCE = {
    "pt": {
        "1s": ("eu",),
        "2s": ("tu",),
        "3s": ("ele", "você", "ela"),
        "1p": ("nós",),
        "2p": ("vós",),
        "3p": ("eles", "elas", "vocês"),
    },
    "fr": {
        "1s": ("je",),
        "2s": ("tu",),
        "3s": ("il", "elle", "on"),
        "1p": ("nous",),
        "2p": ("vous",),
        "3p": ("ils", "elles"),
    },
}


def pin_verbecc_snapshot(
    workspace: Workspace,
    *,
    language: str,
    verbs_xml: Path,
    conjugations_xml: Path,
    snapshot_id: str,
) -> Path:
    """Pin the exact verbecc XML pair used to generate one language layer."""

    language = language.strip().casefold()
    if language in UNSUPPORTED:
        raise ConjugationLayerError(UNSUPPORTED[language])
    if language not in SUPPORTED:
        raise ConjugationLayerError(f"verbecc conjugation snapshots are not defined for {language}")
    snapshot_id = _safe_snapshot_id(snapshot_id)
    verbs_xml = verbs_xml.expanduser().resolve()
    conjugations_xml = conjugations_xml.expanduser().resolve()
    if not verbs_xml.is_file() or not conjugations_xml.is_file():
        raise ConjugationLayerError("verbecc XML source files are unavailable")
    target = workspace.root / "raw/conjugations" / language / PROVIDER / snapshot_id
    if target.exists():
        raise ConjugationLayerError(f"conjugation source snapshot already exists: {target}")
    target.mkdir(parents=True)
    verbs_payload = target / "verbs.xml"
    conjugations_payload = target / "conjugations.xml"
    shutil.copy2(verbs_xml, verbs_payload)
    shutil.copy2(conjugations_xml, conjugations_payload)
    verb_digest = file_content_id(verbs_payload)
    conj_digest = file_content_id(conjugations_payload)
    manifest = {
        "schema_version": SOURCE_MANIFEST_VERSION,
        "artifact_kind": "conjugation_source",
        "language": language,
        "mode_scope": None,
        "provider": PROVIDER,
        "snapshot_id": snapshot_id,
        "provenance_status": "observed",
        "license": LICENSE,
        "source_uris": ["https://github.com/bretttolbert/verbecc"],
        "recovered_at": _timestamp(),
        "recovered_from": str(verbs_xml.parent),
        "content_files": [
            {
                "path": verbs_payload.name,
                "sha256": verb_digest.removeprefix("sha256:"),
                "bytes": verbs_payload.stat().st_size,
            },
            {
                "path": conjugations_payload.name,
                "sha256": conj_digest.removeprefix("sha256:"),
                "bytes": conjugations_payload.stat().st_size,
            },
        ],
        "notes": [
            "XML templates derived from Verbiste / mlconjug; library license is LGPLv3.",
            "Machine-learning template prediction is disabled; missing headwords stay listed.",
            "Kaikki Wiktionary tables exist for the same languages and remain the provider-native alternative.",
        ],
    }
    (target / "artifact.json").write_bytes(json_bytes(manifest))
    return target


def installed_verbecc_xml(language: str) -> tuple[Path, Path]:
    try:
        import verbecc
    except ImportError as error:
        raise ConjugationLayerError("verbecc is not installed") from error
    root = Path(verbecc.__file__).resolve().parent / "data" / "xml"
    verbs = root / "verbs" / f"verbs-{language}.xml"
    conjugations = root / "conjugations" / f"conjugations-{language}.xml"
    if not verbs.is_file() or not conjugations.is_file():
        raise ConjugationLayerError(f"installed verbecc XML is missing for {language}")
    return verbs, conjugations


def _disable_verbecc_ml() -> None:
    import verbecc.src.defs.types.data.verbs as verbs_mod
    verbs_mod.config.ENABLE_ML_PREDICTION = False


def _cell_form(cell: Any) -> str | None:
    if isinstance(cell, str):
        text = cell.strip()
        return text or None
    if not isinstance(cell, dict):
        return None
    raw = cell.get("c") or cell.get("conjugations")
    if isinstance(raw, list) and raw:
        text = str(raw[0]).strip()
    elif isinstance(raw, str):
        text = raw.strip()
    else:
        return None
    if not text or text in {"-", "—"}:
        return None
    pronoun = str(cell.get("pr") or "").strip()
    if pronoun:
        prefix = pronoun + " "
        if text.lower().startswith(prefix.lower()):
            text = text[len(prefix):].strip()
        elif pronoun.casefold() == "je" and text.lower().startswith("j'"):
            text = text[2:].strip()
    return text or None


def _cells(value: Any) -> list[dict[str, Any]]:
    if isinstance(value, list):
        return [item for item in value if isinstance(item, dict) or isinstance(item, str)]
    if isinstance(value, dict):
        if "c" in value or "pr" in value:
            return [value]
        cells: list[Any] = []
        for item in value.values():
            cells.extend(_cells(item))
        return [item for item in cells if isinstance(item, (dict, str))]
    return []


def collapse_person_forms(cells: list[Any], language: str) -> list[dict[str, str]]:
    prefs = PERSON_PREFERENCE[language]
    indexed: dict[str, Any] = {}
    for cell in cells:
        if isinstance(cell, dict):
            pronoun = str(cell.get("pr") or "").strip().casefold()
            if pronoun:
                indexed.setdefault(pronoun, cell)
    forms: list[dict[str, str]] = []
    for person, names in prefs.items():
        cell = next((indexed[name] for name in names if name in indexed), None)
        if cell is None:
            continue
        form = _cell_form(cell)
        if form:
            forms.append({"person": person, "form": form})
    return forms


def _mood_name(value: Any) -> str:
    return str(getattr(value, "value", value)).strip()


def _nonfinite(moods: dict[str, Any], language: str) -> dict[str, str | None]:
    gerund = None
    participle = None
    if language == "pt":
        gerund_cells = _cells((moods.get("gerúndio") or moods.get("gerundio") or {}).get("gerúndio") or (moods.get("gerúndio") or {}).get("gerundio"))
        part_cells = _cells((moods.get("particípio") or moods.get("participio") or {}).get("particípio") or (moods.get("particípio") or {}).get("participio"))
    else:
        participe = moods.get("participe") or {}
        gerund_cells = _cells(participe.get("participe-présent") or participe.get("participe-present"))
        part_cells = _cells(participe.get("participe-passé") or participe.get("participe-passe"))
    if gerund_cells:
        gerund = _cell_form(gerund_cells[0] if not isinstance(gerund_cells[0], str) else {"c": [gerund_cells[0]]})
    if part_cells:
        participle = _cell_form(part_cells[0] if not isinstance(part_cells[0], str) else {"c": [part_cells[0]]})
    return {"gerund": gerund, "past_participle": participle}


def _conjugate_one(conjugator: Any, headword: str) -> dict[str, Any] | None:
    from verbecc.src.defs.types.exceptions import VerbNotFoundError
    try:
        payload = conjugator.conjugate(headword)
    except VerbNotFoundError:
        return None
    data = payload.get_data() if hasattr(payload, "get_data") else payload
    if not isinstance(data, dict):
        return None
    return data


def verbecc_records(
    *,
    language: str,
    requested: set[str],
    verbs_xml: Path,
    conjugations_xml: Path,
) -> dict[str, dict[str, Any]]:
    language = language.strip().casefold()
    if language in UNSUPPORTED:
        raise ConjugationLayerError(UNSUPPORTED[language])
    if language not in SUPPORTED:
        raise ConjugationLayerError(f"verbecc conjugation snapshots are not defined for {language}")
    try:
        from verbecc import CompleteConjugator
        from verbecc.src.defs.types.lang_code import LangCodeISO639_1
    except ImportError as error:
        raise ConjugationLayerError("verbecc is not installed") from error
    installed_verbs, installed_conj = installed_verbecc_xml(language)
    if file_content_id(installed_verbs) != file_content_id(verbs_xml):
        raise ConjugationLayerError("pinned verbecc verbs XML does not match the installed package")
    if file_content_id(installed_conj) != file_content_id(conjugations_xml):
        raise ConjugationLayerError("pinned verbecc conjugations XML does not match the installed package")
    _disable_verbecc_ml()
    conjugator = CompleteConjugator(lang=getattr(LangCodeISO639_1, language))
    allowed = BOUNDED_TENSES[language]
    records: dict[str, dict[str, Any]] = {}
    for headword in sorted(requested):
        data = _conjugate_one(conjugator, headword)
        if not data or data.get("verb", {}).get("predicted"):
            continue
        moods = data.get("moods") or {}
        paradigms = []
        for mood_key, tenses in moods.items():
            mood = _mood_name(mood_key).casefold()
            if not isinstance(tenses, dict):
                continue
            for tense_key, cells in tenses.items():
                tense = _mood_name(tense_key).casefold()
                if (mood, tense) not in allowed:
                    continue
                forms = collapse_person_forms(_cells(cells), language)
                if forms:
                    paradigms.append({"mood": mood, "tense": tense, "forms": forms})
        if not paradigms:
            continue
        verb = data.get("verb") or {}
        records[headword] = {
            "headword": headword,
            "translation": verb.get("translation_en") or None,
            "nonfinite": _nonfinite(moods, language),
            "paradigms": paradigms,
        }
    return records
