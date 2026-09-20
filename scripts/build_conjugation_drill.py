#!/usr/bin/env python3
"""Build the conjugation-drill deck from a conjugation-layer/v1 artifact.

Reads a built ``conjugation-layer/v1`` object, derives a *lesson signature*
for every form, joins an optional frequency-rank file, and writes a
browser-loadable deck for ``app/conjugation/``.

Nothing here is hand-tabulated per language and nothing is hand-tagged. The
one primitive is the **lesson signature**, five fields per form:

    (class, tense, person, ending, stem_delta)

``ending`` is the commonest ending observed for verbs of that class in that
tense and person. ``stem_delta`` is the minimal edit from the infinitive's
stem to the stem actually realised in the form, once that ending is removed:
``pens`` → ``piens`` is ``e>ie``, ``busc`` → ``busqu`` is ``c>qu``,
``ten`` → ``teng`` is ``0>g``. Two forms teach the same thing exactly when
their five fields match, so a deck of tens of thousands of cards collapses to
a curriculum of a few hundred lessons.

The familiar verb types are read off the delta rather than stored separately:

    0 regular        delta is empty
    1 spelling       the realised stem folds back to the citation stem
    2 stem-change    any other delta
    3 irregular      the ending itself does not match (delta ``*``)
    4 unclassified   no model available (declared, never guessed)

Usage:
    python scripts/build_conjugation_drill.py \
        --layer <path to conjugations.json> \
        --language es \
        [--ranks <path to frequency-ranks.json>] \
        [--out app/conjugation/data]
"""

from __future__ import annotations

import argparse
import json
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

DECK_VERSION = "conjugation-drill/v2"

REGULAR, SPELLING, STEM_CHANGE, IRREGULAR, UNCLASSIFIED = 0, 1, 2, 3, 4

OPAQUE = "*"    # the ending did not match the model at all
EMPTY = "0"     # an insertion or deletion side of a delta

# Person labels shown on the card front. A language absent from this table
# still builds; the drill falls back to the bare person code.
PRONOUNS: dict[str, dict[str, str]] = {
    "es": {
        "1s": "yo",
        "2s": "tú",
        "3s": "él / ella / usted",
        "1p": "nosotros",
        "2p": "vosotros",
        "3p": "ellos / ellas / ustedes",
    },
    "pt": {
        "1s": "eu",
        "2s": "tu",
        "3s": "ele / ela / você",
        "1p": "nós",
        "2p": "vós",
        "3p": "eles / elas / vocês",
    },
    "fr": {
        "1s": "je",
        "2s": "tu",
        "3s": "il / elle / on",
        "1p": "nous",
        "2p": "vous",
        "3p": "ils / elles",
    },
    "cs": {
        "1s": "já",
        "2s": "ty",
        "3s": "on / ona / ono",
        "1p": "my",
        "2p": "vy",
        "3p": "oni / ony / ona",
    },
}

# Clitics and particles that ride along with a form and are not part of the
# conjugated word itself.
PARTICLES: dict[str, set[str]] = {
    "es": {"no", "me", "te", "se", "nos", "os"},
    "pt": {"não", "nao", "me", "te", "se", "nos", "vos", "que"},
    "fr": {"ne", "me", "te", "se", "nous", "vous", "n'", "que"},
    "cs": {"se", "si", "ne"},
}

# Stem spellings that change for pronunciation rather than morphology. Applied
# to the END of a stem, longest key first.
SPELLING_SWAPS: dict[str, dict[str, str]] = {
    "es": {"qu": "c", "gu": "g", "gü": "gu", "z": "c", "c": "z", "j": "g", "y": "i"},
    "pt": {"qu": "c", "gu": "g", "ç": "c", "c": "ç", "j": "g", "g": "j"},
    "fr": {"ge": "g", "ç": "c", "c": "ç", "ll": "l", "tt": "t", "è": "e"},
    "cs": {},
}

CLASS_SUFFIXES: dict[str, tuple[str, ...]] = {
    "es": ("ar", "er", "ir", "ír"),
    "pt": ("ar", "er", "ir", "or"),
    "fr": ("er", "ir", "re", "oir"),
    "cs": ("at", "it", "et", "ét", "ovat", "nout", "ít"),
}

REFLEXIVE_SUFFIXES: dict[str, tuple[str, ...]] = {
    "es": ("se",),
    "pt": ("-se", "se"),
    "fr": (),
    "cs": (),
}

# Display order and English names for tenses.
#
# The source names a tense in its own language and in its own order (the
# Spanish layer is alphabetical, so it opens on the imperative). A learner
# wants the indicative present first and the archaic tenses last, under
# English headings. Keys are the source's own (mood, tense) strings.
#
# A mood or tense absent from this table keeps the source's name, sorts after
# everything mapped, and is treated as uncommon — declared unknown rather
# than silently ranked.
#
# Each entry is: (mood label, mood order, tense label, tense order, common).
# "common" is what a learner meets in a first course; the rest stay behind a
# "more" toggle instead of padding the list.
TENSE_DISPLAY: dict[str, dict[tuple[str, str], tuple[str, int, str, int, bool]]] = {
    "es": {
        ("Indicativo", "Presente"): ("Indicative", 1, "Present", 1, True),
        ("Indicativo", "Pretérito"): ("Indicative", 1, "Preterite", 2, True),
        ("Indicativo", "Imperfecto"): ("Indicative", 1, "Imperfect", 3, True),
        ("Indicativo", "Futuro"): ("Indicative", 1, "Future", 4, True),
        ("Indicativo", "Condicional"): ("Indicative", 1, "Conditional", 5, True),
        ("Indicativo", "Pretérito perfecto"): ("Indicative", 1, "Present perfect", 6, True),
        ("Indicativo", "Pluscuamperfecto"): ("Indicative", 1, "Past perfect", 7, False),
        ("Indicativo", "Futuro perfecto"): ("Indicative", 1, "Future perfect", 8, False),
        ("Indicativo", "Condicional perfecto"): ("Indicative", 1, "Conditional perfect", 9, False),
        ("Indicativo", "Pretérito anterior"): ("Indicative", 1, "Preterite perfect", 10, False),
        ("Subjuntivo", "Presente"): ("Subjunctive", 2, "Present", 1, True),
        ("Subjuntivo", "Imperfecto"): ("Subjunctive", 2, "Imperfect", 2, True),
        ("Subjuntivo", "Pretérito perfecto"): ("Subjunctive", 2, "Present perfect", 3, False),
        ("Subjuntivo", "Pluscuamperfecto"): ("Subjunctive", 2, "Past perfect", 4, False),
        ("Subjuntivo", "Futuro"): ("Subjunctive", 2, "Future", 5, False),
        ("Subjuntivo", "Futuro perfecto"): ("Subjunctive", 2, "Future perfect", 6, False),
        # Both imperatives are one mood to a learner, so they are folded into
        # a single heading with the polarity as the tense.
        ("Imperativo Afirmativo", "Presente"): ("Imperative", 3, "Affirmative", 1, True),
        ("Imperativo Negativo", "Presente"): ("Imperative", 3, "Negative", 2, True),
    },
    "pt": {
        ("indicativo", "presente"): ("Indicative", 1, "Present", 1, True),
        ("indicativo", "pretérito-perfeito"): ("Indicative", 1, "Preterite", 2, True),
        ("indicativo", "pretérito-imperfeito"): ("Indicative", 1, "Imperfect", 3, True),
        ("indicativo", "futuro-do-presente"): ("Indicative", 1, "Future", 4, True),
        ("condicional", "futuro-do-pretérito"): ("Conditional", 2, "Conditional", 1, True),
        ("subjuntivo", "presente"): ("Subjunctive", 3, "Present", 1, True),
        ("subjuntivo", "pretérito-imperfeito"): ("Subjunctive", 3, "Imperfect", 2, True),
        ("subjuntivo", "futuro"): ("Subjunctive", 3, "Future", 3, True),
        ("imperativo", "afirmativo"): ("Imperative", 4, "Affirmative", 1, True),
        ("imperativo", "negativo"): ("Imperative", 4, "Negative", 2, True),
    },
    "fr": {
        ("indicatif", "présent"): ("Indicative", 1, "Present", 1, True),
        ("indicatif", "imparfait"): ("Indicative", 1, "Imperfect", 2, True),
        ("indicatif", "futur-simple"): ("Indicative", 1, "Future", 3, True),
        ("indicatif", "passé-simple"): ("Indicative", 1, "Simple past", 4, False),
        ("conditionnel", "présent"): ("Conditional", 2, "Conditional", 1, True),
        ("subjonctif", "présent"): ("Subjunctive", 3, "Present", 1, True),
        ("subjonctif", "imparfait"): ("Subjunctive", 3, "Imperfect", 2, False),
        ("imperatif", "imperatif-présent"): ("Imperative", 4, "Imperative", 1, True),
    },
    "cs": {
        ("indicative", "present"): ("Indicative", 1, "Present", 1, True),
        ("imperative", "present"): ("Imperative", 2, "Imperative", 1, True),
    },
}

UNMAPPED_ORDER = 99


def tense_display(
    language: str, mood: str, tense: str
) -> tuple[str, int, str, int, bool]:
    """English heading, order and commonness for a source (mood, tense)."""
    mapped = TENSE_DISPLAY.get(language, {}).get((mood, tense))
    if mapped:
        return mapped
    return (mood, UNMAPPED_ORDER, tense, UNMAPPED_ORDER, False)


VOWELS = set("aeiouáéíóúàèìòùâêîôûäëïöüãõy")


def strip_accents(value: str) -> str:
    decomposed = unicodedata.normalize("NFD", value)
    return "".join(c for c in decomposed if unicodedata.category(c) != "Mn")


def split_headword(headword: str, language: str) -> tuple[str, bool]:
    """Return (base infinitive, is_reflexive)."""
    for suffix in REFLEXIVE_SUFFIXES.get(language, ()):
        if headword.endswith(suffix) and len(headword) > len(suffix):
            base = headword[: -len(suffix)].rstrip("-")
            if any(base.endswith(s) for s in CLASS_SUFFIXES.get(language, ())):
                return base, True
    return headword, False


def verb_class(base: str, language: str) -> str:
    suffixes = sorted(CLASS_SUFFIXES.get(language, ()), key=len, reverse=True)
    for suffix in suffixes:
        if base.endswith(suffix):
            return suffix
    return "other"


def strip_particles(form: str, language: str) -> tuple[str, list[str]]:
    """Peel leading clitics/negators off a form. Returns (core, particles)."""
    particles = PARTICLES.get(language, set())
    tokens = form.split()
    lead: list[str] = []
    while len(tokens) > 1 and tokens[0].lower() in particles:
        lead.append(tokens.pop(0))
    return " ".join(tokens), lead


def normalise_stem(value: str, language: str) -> str:
    """Fold a stem to its spelling-insensitive shape."""
    folded = strip_accents(value).lower()
    swaps = SPELLING_SWAPS.get(language, {})
    for src in sorted(swaps, key=len, reverse=True):
        if folded.endswith(strip_accents(src)):
            return folded[: -len(strip_accents(src))] + swaps[src]
    return folded


def tense_id(mood: str, tense: str) -> str:
    return f"{mood}::{tense}"


def stem_delta(stem: str, realised: str) -> str:
    """Minimal edit from the citation stem to the realised one.

    Trim the shared prefix and the shared suffix; what is left on each side is
    the alternation. ``ten``/``tien`` gives ``e>ie``; ``ten``/``teng`` gives
    ``0>g``; identical stems give the empty string.
    """
    if stem == realised:
        return ""
    head = 0
    while head < len(stem) and head < len(realised) and stem[head] == realised[head]:
        head += 1
    tail = 0
    while (
        tail < len(stem) - head
        and tail < len(realised) - head
        and stem[len(stem) - 1 - tail] == realised[len(realised) - 1 - tail]
    ):
        tail += 1
    left = stem[head : len(stem) - tail] or EMPTY
    right = realised[head : len(realised) - tail] or EMPTY
    return f"{left}>{right}"


def delta_code(delta: str, stem: str, realised: str, language: str) -> int:
    """Read the familiar verb type off a delta. One rule, no separate table."""
    if delta == OPAQUE:
        return IRREGULAR
    if delta == "":
        return REGULAR
    if normalise_stem(realised, language) == normalise_stem(stem, language):
        return SPELLING
    return STEM_CHANGE


def delta_is_vowel(delta: str) -> bool:
    if delta in ("", OPAQUE):
        return False
    left, _, right = delta.partition(">")
    return any(c in VOWELS for c in left + right if c != EMPTY)


def collect_model_endings(
    records: list[dict[str, Any]], language: str
) -> tuple[dict[tuple[str, str, str], str], dict[str, str]]:
    """Derive the modal ending per (class, tense, person), and per-class participle."""
    ending_votes: dict[tuple[str, str, str], Counter] = defaultdict(Counter)
    participle_votes: dict[str, Counter] = defaultdict(Counter)

    for record in records:
        base, reflexive = split_headword(record["headword"], language)
        cls = verb_class(base, language)
        if cls == "other":
            continue
        stem = base[: -len(cls)]
        if not stem:
            continue

        participle = (record.get("nonfinite") or {}).get("past_participle")
        if participle and " " not in participle and participle.startswith(stem):
            participle_votes[cls][participle[len(stem) :]] += 1

        for paradigm in record["paradigms"]:
            tid = tense_id(paradigm["mood"], paradigm["tense"])
            for entry in paradigm["forms"]:
                core, lead = strip_particles(entry["form"], language)
                if " " in core:  # compound tense: modelled via the participle
                    continue
                if reflexive and not lead:  # enclitic imperative: lávate
                    continue
                if core.startswith(stem):
                    ending_votes[(cls, tid, entry["person"])][core[len(stem) :]] += 1

    endings = {
        key: votes.most_common(1)[0][0]
        for key, votes in ending_votes.items()
        if votes and votes.most_common(1)[0][1] >= 3
    }
    participles = {
        cls: votes.most_common(1)[0][0]
        for cls, votes in participle_votes.items()
        if votes and votes.most_common(1)[0][1] >= 3
    }
    return endings, participles


def best_rank(headword: str, base: str, ranks: dict[str, int]) -> int | None:
    """Rank of the infinitive itself.

    Deliberately not the best rank across inflected forms: those collide with
    homographic function words (``para``, ``una``, ``no``) and rank common
    prepositions as common verbs. A verb whose infinitive never appears is
    declared unranked rather than guessed.
    """
    for candidate in (headword, base):
        if candidate in ranks:
            return ranks[candidate]
    return None


class LessonTable:
    """The curriculum: one entry per distinct (class, tense, person, ending, delta)."""

    def __init__(self) -> None:
        self.index: dict[tuple[str, str, str, str, str], int] = {}
        self.rows: list[dict[str, Any]] = []

    def id_for(
        self, cls: str, tid: str, person: str, ending: str, delta: str, headword: str
    ) -> int:
        key = (cls, tid, person, ending, delta)
        if key not in self.index:
            self.index[key] = len(self.rows)
            self.rows.append(
                {
                    "k": cls,
                    "t": tid,
                    "p": person,
                    "e": ending,
                    "d": delta,
                    "n": 0,
                    "v": [],      # a few example verbs, for the drill's chip
                }
            )
        row = self.rows[self.index[key]]
        row["n"] += 1
        if headword not in row["v"] and len(row["v"]) < 6:
            row["v"].append(headword)
        return self.index[key]


def build_deck(
    layer: dict[str, Any], ranks: dict[str, int], language: str
) -> dict[str, Any]:
    records = layer["records"]
    endings, participle_models = collect_model_endings(records, language)

    tenses: dict[str, dict[str, Any]] = {}
    for record in records:
        for paradigm in record["paradigms"]:
            tid = tense_id(paradigm["mood"], paradigm["tense"])
            compound = any(
                " " in strip_particles(f["form"], language)[0] for f in paradigm["forms"]
            )
            mood_label, mood_order, tense_label, tense_order, common = tense_display(
                language, paradigm["mood"], paradigm["tense"]
            )
            existing = tenses.setdefault(
                tid,
                {
                    "id": tid,
                    "mood": mood_label,
                    "tense": tense_label,
                    "source_mood": paradigm["mood"],
                    "source_tense": paradigm["tense"],
                    "mood_order": mood_order,
                    "order": tense_order,
                    "common": common,
                    "compound": compound,
                    "persons": [],
                },
            )
            for entry in paradigm["forms"]:
                if entry["person"] not in existing["persons"]:
                    existing["persons"].append(entry["person"])
            existing["compound"] = existing["compound"] or compound

    person_order = ["1s", "2s", "3s", "1p", "2p", "3p"]
    for tense in tenses.values():
        tense["persons"].sort(key=person_order.index)

    lessons = LessonTable()
    verbs: list[dict[str, Any]] = []
    counts = Counter()
    total_forms = 0

    for record in records:
        headword = record["headword"]
        base, reflexive = split_headword(headword, language)
        cls = verb_class(base, language)
        stem = base[: -len(cls)] if cls != "other" else base
        nonfinite = record.get("nonfinite") or {}
        participle = nonfinite.get("past_participle")

        participle_model = participle_models.get(cls)
        if participle and participle_model and participle.startswith(stem):
            participle_delta = stem_delta(stem, participle[: -len(participle_model)]) \
                if participle.endswith(participle_model) else OPAQUE
        elif participle and participle_model:
            participle_delta = OPAQUE
        else:
            participle_delta = None

        paradigms: dict[str, dict[str, Any]] = {}

        for paradigm in record["paradigms"]:
            tid = tense_id(paradigm["mood"], paradigm["tense"])
            by_person = {f["person"]: f["form"] for f in paradigm["forms"]}
            forms: list[str | None] = []
            codes: list[str] = []
            lesson_ids: list[int | None] = []

            for person in tenses[tid]["persons"]:
                raw = by_person.get(person)
                if raw is None:
                    forms.append(None)
                    codes.append("-")
                    lesson_ids.append(None)
                    continue

                forms.append(raw)
                total_forms += 1
                core, lead = strip_particles(raw, language)
                model = endings.get((cls, tid, person))

                if " " in core:
                    # Compound: the auxiliary is the same for everyone, so the
                    # lesson is the participle.
                    if participle_delta is None:
                        code, lesson = UNCLASSIFIED, None
                    else:
                        code = delta_code(
                            participle_delta, stem, participle or stem, language
                        )
                        lesson = lessons.id_for(
                            cls, tid, person, "·participle", participle_delta, headword
                        )
                elif reflexive and not lead:
                    # An affirmative imperative carries its pronoun glued on
                    # (lávate, lavémonos). The ending is regular underneath,
                    # but the model cannot see past the enclitic.
                    code, lesson = UNCLASSIFIED, None
                elif model is None:
                    code, lesson = UNCLASSIFIED, None
                elif not stem:
                    # A two-letter infinitive leaves no stem to alternate.
                    code = REGULAR if core == model else IRREGULAR
                    delta = "" if core == model else OPAQUE
                    lesson = lessons.id_for(cls, tid, person, model, delta, headword)
                elif model and not core.endswith(model):
                    code = IRREGULAR
                    lesson = lessons.id_for(cls, tid, person, model, OPAQUE, headword)
                else:
                    realised = core[: -len(model)] if model else core
                    delta = stem_delta(stem, realised)
                    code = delta_code(delta, stem, realised, language)
                    lesson = lessons.id_for(cls, tid, person, model, delta, headword)

                counts[code] += 1
                codes.append(str(code))
                lesson_ids.append(lesson)

            paradigms[tid] = {"f": forms, "c": "".join(codes), "l": lesson_ids}

        verbs.append(
            {
                "h": headword,
                "t": record.get("translation"),
                "k": cls,
                "s": stem,
                "r": reflexive,
                "g": nonfinite.get("gerund"),
                "pp": participle,
                "n": best_rank(headword, base, ranks),
                "p": paradigms,
            }
        )

    verbs.sort(key=lambda v: (v["n"] is None, v["n"] or 0, v["h"]))

    # Distinct alternations, for the pattern picker. Ordered by how much of
    # the deck each one accounts for.
    patterns: dict[str, dict[str, Any]] = {}
    for row in lessons.rows:
        entry = patterns.setdefault(
            row["d"],
            {"d": row["d"], "n": 0, "lessons": 0, "v": [], "vowel": delta_is_vowel(row["d"])},
        )
        entry["n"] += row["n"]
        entry["lessons"] += 1
        for verb in row["v"]:
            if verb not in entry["v"] and len(entry["v"]) < 6:
                entry["v"].append(verb)

    return {
        "deck_version": DECK_VERSION,
        "language": layer["language"],
        "locale": layer["locale"],
        "source": layer["source"],
        "layer_inputs": layer["inputs"],
        "pronouns": PRONOUNS.get(language, {}),
        "person_order": person_order,
        "code_labels": {
            "0": "regular",
            "1": "spelling change",
            "2": "stem change",
            "3": "irregular",
            "4": "unclassified",
        },
        "tenses": sorted(
            tenses.values(),
            key=lambda t: (t["mood_order"], t["order"], t["source_tense"]),
        ),
        "lessons": lessons.rows,
        "patterns": sorted(patterns.values(), key=lambda p: -p["n"]),
        "ranked_verbs": sum(1 for v in verbs if v["n"] is not None),
        "unclassified_forms": counts[UNCLASSIFIED],
        "total_forms": total_forms,
        "verbs": verbs,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--layer", required=True, type=Path)
    parser.add_argument("--language", required=True)
    parser.add_argument("--ranks", type=Path, default=None)
    parser.add_argument("--out", type=Path, default=Path("app/conjugation/data"))
    args = parser.parse_args()

    layer = json.loads(args.layer.read_text(encoding="utf-8"))
    if layer.get("layer_version") != "conjugation-layer/v1":
        raise SystemExit(f"not a conjugation-layer/v1 artifact: {args.layer}")

    ranks: dict[str, int] = {}
    if args.ranks and args.ranks.exists():
        raw = json.loads(args.ranks.read_text(encoding="utf-8"))
        ranks = {k: int(v) for k, v in raw.items()} if isinstance(raw, dict) else {}

    deck = build_deck(layer, ranks, args.language)

    args.out.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(deck, ensure_ascii=False, separators=(",", ":"))
    target = args.out / f"{args.language}.js"
    target.write_text(
        f"// Generated by scripts/build_conjugation_drill.py — do not edit.\n"
        f"window.registerConjugationDeck({payload});\n",
        encoding="utf-8",
    )

    print(f"wrote {target} ({target.stat().st_size / 1024:.0f} KB)")
    print(f"  verbs            {len(deck['verbs'])}")
    print(f"  tenses           {len(deck['tenses'])}")
    print(f"  forms            {deck['total_forms']}")
    print(f"  lessons          {len(deck['lessons'])}")
    print(f"  alternations     {len(deck['patterns'])}")
    print(f"  unclassified     {deck['unclassified_forms']}")
    print(f"  with a rank      {deck['ranked_verbs']}")


if __name__ == "__main__":
    main()
