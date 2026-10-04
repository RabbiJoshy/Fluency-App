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
PERSON_ORDER = ("1s", "2s", "3s", "1p", "2p", "3p")
PERSON_TAGS = frozenset({"first-person", "second-person", "third-person", "singular", "plural"})

# Languages whose Wiktionary tables are read in full rather than as present +
# imperative. Each paradigm is (mood, tense, tags a form must carry, tags it
# must not). Mood and tense are the labels the drill and the card back key
# on. Several forms can match one person (``tienes`` informal, ``tenés``
# vos-form, a Brazil-only variant): the one carrying the fewest extra tags
# wins, so the standard form beats its regional or register variants.
FULL_PARADIGMS: dict[str, tuple[tuple[str, str, frozenset[str], frozenset[str]], ...]] = {
    "es": (
        ("indicativo", "presente", frozenset({"indicative", "present"}), frozenset()),
        ("indicativo", "pretérito", frozenset({"indicative", "preterite"}), frozenset()),
        ("indicativo", "imperfecto", frozenset({"indicative", "imperfect"}), frozenset()),
        ("indicativo", "futuro", frozenset({"indicative", "future"}), frozenset()),
        ("indicativo", "condicional", frozenset({"conditional"}), frozenset()),
        ("subjuntivo", "presente", frozenset({"subjunctive", "present"}), frozenset()),
        ("subjuntivo", "imperfecto", frozenset({"subjunctive", "imperfect"}), frozenset({"imperfect-se"})),
        ("subjuntivo", "futuro", frozenset({"subjunctive", "future"}), frozenset()),
        ("imperativo", "afirmativo", frozenset({"imperative"}), frozenset({"negative"})),
        ("imperativo", "negativo", frozenset({"imperative", "negative"}), frozenset()),
    ),
    "pt": (
        ("indicativo", "presente", frozenset({"indicative", "present"}), frozenset()),
        ("indicativo", "pretérito-perfeito", frozenset({"indicative", "preterite"}), frozenset()),
        ("indicativo", "pretérito-imperfeito", frozenset({"indicative", "imperfect"}), frozenset()),
        ("indicativo", "pretérito-mais-que-perfeito", frozenset({"indicative", "pluperfect"}), frozenset()),
        ("indicativo", "futuro-do-presente", frozenset({"indicative", "future"}), frozenset()),
        ("condicional", "futuro-do-pretérito", frozenset({"conditional"}), frozenset()),
        ("subjuntivo", "presente", frozenset({"subjunctive", "present"}), frozenset()),
        ("subjuntivo", "pretérito-imperfeito", frozenset({"subjunctive", "imperfect"}), frozenset()),
        ("subjuntivo", "futuro", frozenset({"subjunctive", "future"}), frozenset()),
        ("imperativo", "afirmativo", frozenset({"imperative"}), frozenset({"negative"})),
        ("imperativo", "negativo", frozenset({"imperative", "negative"}), frozenset()),
    ),
    # Wiktionary spells French compound tenses as "avoir + past participle"
    # rows (multiword-construction); only the simple tenses are cells here.
    "fr": (
        ("indicatif", "présent", frozenset({"indicative", "present"}), frozenset()),
        ("indicatif", "imparfait", frozenset({"indicative", "imperfect"}), frozenset()),
        ("indicatif", "passé-simple", frozenset({"indicative", "historic", "past"}), frozenset({"anterior"})),
        ("indicatif", "futur-simple", frozenset({"indicative", "future"}), frozenset({"perfect"})),
        ("conditionnel", "présent", frozenset({"conditional"}), frozenset({"perfect"})),
        ("subjonctif", "présent", frozenset({"subjunctive", "present"}), frozenset()),
        ("subjonctif", "imparfait", frozenset({"subjunctive", "imperfect"}), frozenset()),
        ("imperatif", "imperatif-présent", frozenset({"imperative"}), frozenset()),
    ),
}
# Never a cell of the six-person table: object-clitic combinations, voseo,
# the formal imperative repeated under "second-person-semantically", and the
# non-finite rows.
FULL_EXCLUDED_TAGS = frozenset({
    "combined-form", "vos-form", "second-person-semantically", "participle", "gerund",
    "infinitive", "obsolete", "archaic", "misspelling", "nonstandard", "multiword-construction",
})
# Wiktionary prints the Spanish negative imperative without its "no"
# (Portuguese prints "não"). The drill strips both as particles.
NEGATIVE_PREFIX = {"es": "no "}
# Compound tenses are not in the tables: they are the auxiliary's simple tense
# plus the past participle, built here and labelled as derived.
COMPOUND_TENSES: dict[str, tuple[str, tuple[tuple[str, str, str, str], ...]]] = {
    "es": ("haber", (
        ("indicativo", "pretérito perfecto", "indicativo", "presente"),
        ("indicativo", "pluscuamperfecto", "indicativo", "imperfecto"),
        ("indicativo", "futuro perfecto", "indicativo", "futuro"),
        ("indicativo", "condicional perfecto", "indicativo", "condicional"),
        ("indicativo", "pretérito anterior", "indicativo", "pretérito"),
        ("subjuntivo", "pretérito perfecto", "subjuntivo", "presente"),
        ("subjuntivo", "pluscuamperfecto", "subjuntivo", "imperfecto"),
        ("subjuntivo", "futuro perfecto", "subjuntivo", "futuro"),
    )),
}


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
    directory.
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


def _full_record_from_row(row: dict[str, Any], language: str) -> dict[str, Any] | None:
    headword = str(row.get("word") or "").strip().casefold()
    if not headword or row.get("pos") not in VERB_POS:
        return None
    paradigms = FULL_PARADIGMS[language]
    best: dict[tuple[int, str], tuple[int, str]] = {}
    gerund = past_participle = None
    participle_rank = 2
    for item in row.get("forms") or []:
        if not isinstance(item, dict):
            continue
        tags = {tag for tag in item.get("tags") or [] if isinstance(tag, str)}
        form = _usable_form(item.get("form"), tags)
        if form is None:
            continue
        plain = not tags & {"multiword-construction", "combined-form"}
        # Spanish tags the gerund alone; French tags it "gerund participle present".
        if gerund is None and plain and "gerund" in tags and not tags & PERSON_TAGS:
            gerund = form
        # Masculine singular where gender is marked (es, pt); else the bare
        # past-participle row (fr). Lower rank wins; ties keep the first seen.
        if plain and {"participle", "past"} <= tags and not tags & {"feminine", "plural"}:
            rank = 0 if {"masculine", "singular"} <= tags else 1
            if past_participle is None or rank < participle_rank:
                past_participle, participle_rank = form, rank
        if tags & FULL_EXCLUDED_TAGS:
            continue
        person = _person(tags)
        if person is None:
            continue
        for index, (_mood, _tense, required, excluded) in enumerate(paradigms):
            if required <= tags and not tags & excluded:
                extra = len(tags - required - PERSON_TAGS)
                key = (index, person)
                if key not in best or extra < best[key][0]:
                    best[key] = (extra, form)
    prefix = NEGATIVE_PREFIX.get(language, "")
    built = []
    for index, (mood, tense, _required, _excluded) in enumerate(paradigms):
        forms = []
        for person in PERSON_ORDER:
            if (index, person) not in best:
                continue
            form = best[(index, person)][1]
            if tense == "negativo" and prefix and not form.startswith(prefix):
                form = prefix + form
            forms.append({"person": person, "form": form})
        if forms:
            built.append({"mood": mood, "tense": tense, "forms": forms})
    if not built:
        return None
    return {
        "headword": headword,
        "translation": _translation(row),
        "nonfinite": {"gerund": gerund, "past_participle": past_participle},
        "paradigms": built,
        "_present_count": sum(len(p["forms"]) for p in built),
    }


# Spanish pronominal verbs Wiktionary files only under the base verb
# (acostarse under acostar): their table is the base table with the
# reflexive pronoun, and their affirmative imperative is the base entry's
# combined form with that pronoun attached (acuéstate, acuéstese, ...).
REFLEXIVE_PRONOUNS = {"es": {"1s": "me", "2s": "te", "3s": "se", "1p": "nos", "2p": "os", "3p": "se"}}
REFLEXIVE_IMPERATIVE = {  # person -> (tags the combined form carries, tags it must not, clitic it ends in)
    "es": {
        "2s": (frozenset({"imperative", "informal", "with-tú", "object-second-person", "object-singular"}), frozenset(), "te"),
        "3s": (frozenset({"imperative", "formal", "object-third-person", "object-singular"}), frozenset(), "se"),
        "1p": (frozenset({"imperative", "object-first-person", "object-plural"}), frozenset({"formal", "informal"}), "nos"),
        "2p": (frozenset({"imperative", "informal", "object-second-person", "object-plural"}),
               frozenset({"with-tú", "with-vos"}), "os"),
        "3p": (frozenset({"imperative", "formal", "object-third-person", "object-plural"}), frozenset(), "nse"),
    },
}


def _reflexive_extras(row: dict[str, Any], language: str) -> dict[str, Any]:
    """The base entry's attached-reflexive imperatives and gerund, and a reflexive gloss."""
    wanted = REFLEXIVE_IMPERATIVE[language]
    imperative: dict[str, str] = {}
    gerund = None
    for item in row.get("forms") or []:
        if not isinstance(item, dict):
            continue
        tags = {tag for tag in item.get("tags") or [] if isinstance(tag, str)}
        form = str(item.get("form") or "").strip()
        if "combined-form" not in tags or not form or form == "-":
            continue
        if gerund is None and "gerund" in tags and form.endswith("se"):
            gerund = form
        for person, (required, excluded, clitic) in wanted.items():
            if person in imperative or not required <= tags or tags & excluded:
                continue
            # 3s "se" must not take the 3p "-nse" form, and vice versa.
            if form.endswith(clitic) and not (clitic == "se" and form.endswith("nse")):
                imperative[person] = form
    translation = None
    for sense in row.get("senses") or []:
        tags = set(sense.get("tags") or [])
        glosses = sense.get("glosses") or []
        if tags & {"reflexive", "pronominal"} and glosses and isinstance(glosses[0], str):
            translation = glosses[0].strip()
            break
    return {"imperative": imperative, "gerund": gerund, "translation": translation}


def _reflexive_from_base(headword: str, base: dict[str, Any], extras: dict[str, Any],
                         language: str) -> dict[str, Any] | None:
    pronouns = REFLEXIVE_PRONOUNS[language]
    paradigms = []
    for paradigm in base["paradigms"]:
        if paradigm.get("derived"):
            continue
        if paradigm["mood"] == "imperativo" and paradigm["tense"] == "afirmativo":
            forms = [{"person": person, "form": extras["imperative"][person]}
                     for person in PERSON_ORDER if person in extras["imperative"]]
        elif paradigm["mood"] == "imperativo":
            forms = [{"person": f["person"],
                      "form": "no " + pronouns[f["person"]] + " " + f["form"].removeprefix("no ")}
                     for f in paradigm["forms"]]
        else:
            forms = [{"person": f["person"], "form": pronouns[f["person"]] + " " + f["form"]}
                     for f in paradigm["forms"]]
        if forms:
            paradigms.append({**paradigm, "forms": forms})
    # The attached imperatives come from the base's combined forms, which a
    # base without its own affirmative row can still list.
    if extras["imperative"] and not any(
        (p["mood"], p["tense"]) == ("imperativo", "afirmativo") for p in paradigms
    ):
        paradigms.append({"mood": "imperativo", "tense": "afirmativo", "forms": [
            {"person": person, "form": extras["imperative"][person]}
            for person in PERSON_ORDER if person in extras["imperative"]]})
    if not paradigms:
        return None
    return {
        "headword": headword,
        "translation": extras["translation"] or base["translation"],
        "nonfinite": {"gerund": extras["gerund"], "past_participle": base["nonfinite"].get("past_participle")},
        "paradigms": paradigms,
        "derived": f"reflexive of {base['headword']}: its Wiktionary table with the reflexive pronoun",
    }


def _add_compound_tenses(records: dict[str, dict[str, Any]], auxiliary: dict[str, Any] | None,
                         language: str) -> None:
    if language not in COMPOUND_TENSES or auxiliary is None:
        return
    aux_name, compounds = COMPOUND_TENSES[language]
    aux_tables = {
        (p["mood"], p["tense"]): {f["person"]: f["form"] for f in p["forms"]}
        for p in auxiliary["paradigms"]
    }
    for record in records.values():
        participle = record["nonfinite"].get("past_participle")
        if not participle:
            continue
        for mood, tense, aux_mood, aux_tense in compounds:
            table = aux_tables.get((aux_mood, aux_tense))
            if not table:
                continue
            pronouns = (
                REFLEXIVE_PRONOUNS.get(language, {})
                if record["headword"].endswith("se") and language in REFLEXIVE_PRONOUNS
                else {}
            )
            record["paradigms"].append({
                "mood": mood,
                "tense": tense,
                "derived": f"{aux_name} {aux_mood} {aux_tense} + past participle",
                "forms": [{"person": person,
                           "form": " ".join(filter(None, (pronouns.get(person), table[person], participle)))}
                          for person in PERSON_ORDER if person in table],
            })


def kaikki_records(payload: Path, requested: set[str], language: str | None = None) -> dict[str, dict[str, Any]]:
    """Stream one dump and keep the best verb table per requested headword.

    For a language in ``FULL_PARADIGMS`` every simple tense is read (plus the
    derived compound tenses); otherwise present and imperative only.
    """

    if not requested:
        return {}
    full = language in FULL_PARADIGMS
    wanted = {item.casefold() for item in requested}
    auxiliary_name = COMPOUND_TENSES[language][0] if language in COMPOUND_TENSES else None
    auxiliary: dict[str, Any] | None = None
    reflexive = full and language in REFLEXIVE_PRONOUNS
    bases_wanted = {word[:-2] for word in wanted if reflexive and word.endswith("se") and len(word) > 3}
    bases: dict[str, tuple[dict[str, Any], dict[str, Any]]] = {}
    records: dict[str, dict[str, Any]] = {}
    try:
        with payload.open(encoding="utf-8") as stream:
            for line in stream:
                if not line.strip():
                    continue
                row = json.loads(line)
                word = str(row.get("word") or "").strip().casefold()
                if word not in wanted and word != auxiliary_name and word not in bases_wanted:
                    continue
                record = _full_record_from_row(row, language) if full else _record_from_row(row)
                if record is None:
                    continue
                if word == auxiliary_name and (
                    auxiliary is None or record["_present_count"] > auxiliary["_present_count"]
                ):
                    auxiliary = record
                if word in bases_wanted and (
                    word not in bases or record["_present_count"] > bases[word][0]["_present_count"]
                ):
                    bases[word] = (record, _reflexive_extras(row, language))
                if word not in wanted:
                    continue
                previous = records.get(word)
                if previous is None or record["_present_count"] > previous["_present_count"]:
                    records[word] = record
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise ConjugationLayerError(f"Kaikki conjugation dump is unreadable: {payload}") from error
    for word in sorted(wanted - records.keys()):
        if word[:-2] in bases and word.endswith("se"):
            base, extras = bases[word[:-2]]
            derived = _reflexive_from_base(word, base, extras, language)
            if derived is not None:
                records[word] = derived
    for record in records.values():
        record.pop("_present_count", None)
    if full:
        _add_compound_tenses(records, auxiliary, language)
    return records
