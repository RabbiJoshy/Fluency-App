"""Unified English Inflection Engine for Spanish Lexical Menus.

Inflects base English translations (from SpanishDict, Wiktionary, or curated overlays)
into natural surface-appropriate English based on Spanish verb conjugations, attached
clitics, and noun plurals.
"""

from __future__ import annotations

import re
import unicodedata
from typing import Any, Mapping, Sequence


PERSON_TO_INDEX: dict[str, int] = {
    "1s": 0, "2s": 1, "3s": 2, "1p": 3, "2p": 4, "3p": 5
}
ENGLISH_PRONOUNS: list[str] = ["I", "you", "he/she", "we", "you (pl)", "they"]

IRREGULAR_ENGLISH_PLURALS: dict[str, str] = {
    "child": "children",
    "foot": "feet",
    "goose": "geese",
    "louse": "lice",
    "man": "men",
    "mouse": "mice",
    "ox": "oxen",
    "person": "people",
    "tooth": "teeth",
    "woman": "women",
}

INVARIANT_ENGLISH_PLURALS: frozenset[str] = frozenset({
    "deer", "fish", "means", "offspring", "series", "sheep", "species"
})

IRREGULAR_ENGLISH_PRESENT: dict[str, list[str]] = {
    "be": ["am", "are", "is", "are", "are", "are"],
    "have": ["have", "have", "has", "have", "have", "have"],
    "do": ["do", "do", "does", "do", "do", "do"],
    "go": ["go", "go", "goes", "go", "go", "go"],
}

IRREGULAR_ENGLISH_PAST: dict[str, str | list[str]] = {
    "be": ["was", "were", "was", "were", "were", "were"],
    "have": "had", "do": "did", "go": "went", "say": "said", "make": "made",
    "take": "took", "come": "came", "see": "saw", "know": "knew", "get": "got",
    "give": "gave", "find": "found", "think": "thought", "tell": "told",
    "become": "became", "leave": "left", "feel": "felt", "put": "put",
    "keep": "kept", "let": "let", "begin": "began", "hear": "heard",
    "sit": "sat", "stand": "stood", "win": "won", "lose": "lost", "run": "ran",
    "eat": "ate", "drink": "drank", "write": "wrote", "read": "read",
    "speak": "spoke", "sleep": "slept", "fall": "fell", "hold": "held",
    "bring": "brought", "buy": "bought", "catch": "caught", "teach": "taught",
    "build": "built", "send": "sent", "spend": "spent", "pay": "paid",
    "sell": "sold", "meet": "met", "lead": "led", "break": "broke",
    "choose": "chose", "drive": "drove", "grow": "grew", "hide": "hid",
    "ride": "rode", "rise": "rose", "sing": "sang", "swim": "swam",
    "throw": "threw", "wear": "wore", "forget": "forgot", "understand": "understood",
}

IRREGULAR_ENGLISH_PP: dict[str, str] = {
    "be": "been", "have": "had", "do": "done", "go": "gone", "say": "said",
    "make": "made", "take": "taken", "come": "come", "see": "seen", "know": "known",
    "get": "got", "give": "given", "find": "found", "think": "thought", "tell": "told",
    "speak": "spoken", "write": "written", "eat": "eaten", "break": "broken",
    "choose": "chosen", "drive": "driven", "forget": "forgotten",
}

CLITIC_ENGLISH: dict[str, str] = {
    "me": "me",
    "te": "you",
    "se": "oneself",
    "nos": "us",
    "os": "you",
    "lo": "it/him",
    "la": "it/her",
    "los": "them",
    "las": "them",
    "le": "him/her",
    "les": "them",
}

CLITIC_REFLEXIVE: dict[str, str] = {
    "me": "myself",
    "te": "yourself",
    "se": "himself/herself/oneself",
    "nos": "ourselves",
    "os": "yourselves",
}


def strip_accents(text: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFD", text) if unicodedata.category(c) != "Mn")


def split_attached_clitics(form: str) -> tuple[str, list[str]]:
    stem = form.lower().strip()
    clitics: list[str] = []
    direct = next((v for v in ["los", "las", "lo", "la"] if stem.endswith(v)), None)
    if direct:
        clitics.insert(0, direct)
        stem = stem[:-len(direct)]
        indirect = next((v for v in ["nos", "les", "me", "te", "se", "os", "le"] if stem.endswith(v)), None)
        if indirect:
            clitics.insert(0, indirect)
            stem = stem[:-len(indirect)]
    else:
        single = next((v for v in ["nos", "les", "los", "las", "me", "te", "se", "os", "lo", "la", "le"] if stem.endswith(v)), None)
        if single:
            clitics.append(single)
            stem = stem[:-len(single)]
    return stem, clitics


def third_person_singular(verb: str) -> str:
    lower = verb.lower()
    if re.search(r"(?:s|x|z|ch|sh)$", lower):
        return f"{lower}es"
    if re.search(r"[^aeiou]y$", lower):
        return f"{lower[:-1]}ies"
    return f"{lower}s"


def inflect_english_present(verb: str, person_idx: int) -> str:
    lower = verb.lower()
    irregular = IRREGULAR_ENGLISH_PRESENT.get(lower)
    if irregular:
        return irregular[person_idx]
    return third_person_singular(lower) if person_idx == 2 else lower


def inflect_english_past(verb: str, person_idx: int) -> str:
    lower = verb.lower()
    irregular = IRREGULAR_ENGLISH_PAST.get(lower)
    if isinstance(irregular, list):
        return irregular[person_idx]
    if isinstance(irregular, str):
        return irregular
    if lower.endswith("e"):
        return f"{lower}d"
    if re.search(r"[^aeiou]y$", lower):
        return f"{lower[:-1]}ied"
    return f"{lower}ed"


def english_ing(verb: str) -> str:
    lower = verb.lower()
    if lower == "be":
        return "being"
    if lower.endswith("ie"):
        return f"{lower[:-2]}ying"
    if lower.endswith("e") and not lower.endswith("ee"):
        return f"{lower[:-1]}ing"
    return f"{lower}ing"


def english_past_participle(verb: str) -> str:
    lower = verb.lower()
    if lower in IRREGULAR_ENGLISH_PP:
        return IRREGULAR_ENGLISH_PP[lower]
    return inflect_english_past(lower, 0)


def pluralize_english_noun(gloss: str) -> str:
    word = gloss.strip()
    # Handle phrasal nouns e.g. "altar boy" -> "altar boys"
    tokens = word.split()
    if not tokens:
        return word
    head = tokens[-1]
    lower = head.lower()
    if lower in IRREGULAR_ENGLISH_PLURALS:
        plural_head = IRREGULAR_ENGLISH_PLURALS[lower]
    elif lower in INVARIANT_ENGLISH_PLURALS:
        plural_head = lower
    elif re.search(r"[^aeiou]y$", lower):
        plural_head = f"{lower[:-1]}ies"
    elif re.search(r"(?:s|x|z|ch|sh)$", lower):
        plural_head = f"{lower}es"
    else:
        plural_head = f"{lower}s"

    if head and head[0].isupper():
        plural_head = plural_head.capitalize()
    tokens[-1] = plural_head
    return " ".join(tokens)


def parse_infinitive_gloss(gloss: str) -> tuple[str, str] | None:
    text = gloss.strip()
    # Strip terminal punctuation
    text = re.sub(r"[.,;!]+$", "", text).strip()
    if not text.lower().startswith("to "):
        # Check if bare verb or phrasal verb without "to"
        return None
    body = text[3:].strip()
    if not body:
        return None
    tokens = body.split(None, 1)
    head = tokens[0]
    rest = f" {tokens[1]}" if len(tokens) > 1 else ""
    return head, rest


def inflect_single_verb_gloss(
    gloss: str,
    mood: str,
    tense: str,
    person_idx: int | None,
    clitics: Sequence[str] = (),
) -> str | None:
    parts = parse_infinitive_gloss(gloss)
    if not parts:
        # If it doesn't start with "to ", treat the first word as the head if imperative
        tokens = gloss.strip().split(None, 1)
        if not tokens:
            return None
        head = tokens[0]
        rest = f" {tokens[1]}" if len(tokens) > 1 else ""
    else:
        head, rest = parts

    base = head.lower()
    tail = rest

    # Add clitic objects to tail if present and not already mentioned
    clitic_additions: list[str] = []
    for cl in clitics:
        cl_clean = cl.lower()
        # In imperative commands (e.g. dame -> give me, dímelo -> tell me it):
        # me, te, le, nos, les are usually indirect/direct objects.
        if mood == "imperativo":
            pron = CLITIC_ENGLISH.get(cl_clean, cl_clean)
            if cl_clean == "lo":
                pron = "it"
            elif cl_clean == "los" or cl_clean == "las":
                pron = "them"
            elif cl_clean == "la":
                pron = "it"
            # Intransitive phrasal verbs with reflexive te (e.g. go away + te -> go away!)
            if cl_clean in {"te", "se"} and (not tail or base in {"go", "leave", "beat", "get"}):
                pron = None
            if pron and not re.search(r"\b" + re.escape(pron) + r"\b", tail, re.IGNORECASE):
                clitic_additions.append(pron)
        elif cl_clean in {"te", "me", "se", "nos", "os"}:
            if re.search(r"\b(?:to|with|for|at|on)\s*$", tail, re.IGNORECASE):
                pron = CLITIC_ENGLISH.get(cl_clean, cl_clean)
                clitic_additions.append(pron)
            elif not tail and base not in {"go", "leave", "beat", "get"}:
                pron = CLITIC_REFLEXIVE.get(cl_clean, cl_clean)
                clitic_additions.append(pron)
        else:
            pron = CLITIC_ENGLISH.get(cl_clean, cl_clean)
            if cl_clean == "lo":
                pron = "it"
            if not re.search(r"\b" + re.escape(pron) + r"\b", tail, re.IGNORECASE):
                clitic_additions.append(pron)

    clitic_tail = f" {' '.join(clitic_additions)}" if clitic_additions else ""

    if mood == "imperativo":
        if person_idx == 3:  # 1p (nosotros)
            return f"let's {base}{tail}{clitic_tail}!"
        return f"{base}{tail}{clitic_tail}!"

    if mood in {"gerundio", "gerund"}:
        return f"{english_ing(base)}{tail}{clitic_tail}"

    if mood in {"participo", "participio", "participle"}:
        return f"{english_past_participle(base)}{tail}{clitic_tail}"

    if person_idx is None or person_idx < 0 or person_idx >= len(ENGLISH_PRONOUNS):
        return None

    subj = ENGLISH_PRONOUNS[person_idx]

    if tense == "presente" or (mood == "indicativo" and tense == "present"):
        form = inflect_english_present(base, person_idx)
        return f"{subj} {form}{tail}{clitic_tail}"
    elif "pretérito" in tense or tense in {"past", "pretérito-perfecto-simple"}:
        form = inflect_english_past(base, person_idx)
        return f"{subj} {form}{tail}{clitic_tail}"
    elif "imperfecto" in tense or tense == "imperfect":
        aux = "was" if person_idx in (0, 2) else "were"
        return f"{subj} {aux} {english_ing(base)}{tail}{clitic_tail}"
    elif tense in {"futuro", "future"}:
        return f"{subj} will {base}{tail}{clitic_tail}"
    elif tense in {"condicional", "conditional"}:
        return f"{subj} would {base}{tail}{clitic_tail}"

    return None


def inflect_verb_translation(
    translation: str,
    morph_list: Sequence[Mapping[str, Any]],
    clitics: Sequence[str] = (),
) -> str:
    """Inflect a verb translation string (potentially containing multiple senses or semicolons)."""
    if not morph_list:
        return translation

    # Try matching first valid morphology
    for morph in morph_list:
        mood = str(morph.get("mood", "")).lower()
        tense = str(morph.get("tense", "")).lower()
        person = str(morph.get("person", "")).lower()
        person_idx = PERSON_TO_INDEX.get(person)

        # Break semicolon/comma items
        clauses = [c.strip() for c in translation.split(";") if c.strip()]
        inflected_clauses = []
        for clause in clauses:
            inf = inflect_single_verb_gloss(clause, mood, tense, person_idx, clitics)
            if inf:
                inflected_clauses.append(inf)
            else:
                inflected_clauses.append(clause)

        if any(inflected_clauses[i] != clauses[i] for i in range(len(clauses))):
            return "; ".join(inflected_clauses)

    return translation


def inflect_card_senses(
    surface: str,
    lemma: str,
    senses: Sequence[dict[str, Any]],
    conj_rev: Mapping[str, Sequence[Mapping[str, Any]]],
) -> list[dict[str, Any]]:
    """Produce inflected copies of senses for an inflected surface form."""
    surf_norm = surface.strip().lower()
    lem_norm = lemma.strip().lower()

    if not surf_norm or surf_norm == lem_norm:
        return list(senses)

    # 1. Check if surface is a regular noun/adjective plural
    is_plural = False
    candidates = {f"{lem_norm}s", f"{lem_norm}es"}
    if lem_norm.endswith("z"):
        candidates.add(f"{lem_norm[:-1]}ces")
    if surf_norm in candidates:
        is_plural = True

    # 2. Check verb conjugation and clitics
    morph_entries: list[Mapping[str, Any]] = []
    clitics: list[str] = []

    # Direct query in conj_rev
    if surf_norm in conj_rev:
        morph_entries = [m for m in conj_rev[surf_norm] if m.get("lemma", "").lower() == lem_norm or not lem_norm]
    elif strip_accents(surf_norm) in conj_rev:
        morph_entries = [m for m in conj_rev[strip_accents(surf_norm)] if m.get("lemma", "").lower() == lem_norm or not lem_norm]

    # Clitic splitting
    if not morph_entries:
        stem, extracted_clitics = split_attached_clitics(surf_norm)
        if extracted_clitics:
            clitics = extracted_clitics
            stem_norm = strip_accents(stem)
            matches = conj_rev.get(stem) or conj_rev.get(stem_norm) or []
            lem_base = lem_norm[:-2] if lem_norm.endswith("se") else lem_norm
            morph_entries = [
                m for m in matches
                if not lem_norm or m.get("lemma", "").lower() in {lem_norm, lem_base}
            ]
            if not morph_entries:
                # If lemma matches stem or pronominal lemma, synthesize imperative
                if stem_norm == lem_base or stem_norm == strip_accents(lem_base):
                    morph_entries = [{"mood": "imperativo", "tense": "afirmativo", "person": "2s"}]

    out_senses = []
    for s in senses:
        s_copy = dict(s)
        pos = str(s.get("pos", "")).upper()
        trans = s.get("translation") or s.get("gloss") or ""

        if pos in {"VERB", "AUX"} and morph_entries:
            inf = inflect_verb_translation(trans, morph_entries, clitics)
            if "translation" in s:
                s_copy["translation"] = inf
            if "gloss" in s or "translation" not in s:
                s_copy["gloss"] = inf
            s_copy["inflected_surface"] = surface
        elif pos in {"NOUN", "ADJ"} and is_plural:
            inf = pluralize_english_noun(trans)
            if "translation" in s:
                s_copy["translation"] = inf
            if "gloss" in s or "translation" not in s:
                s_copy["gloss"] = inf
            s_copy["inflected_surface"] = surface

        out_senses.append(s_copy)

    return out_senses


def inflect_clitic_memberships(
    clitic_memberships: Sequence[Mapping[str, Any]],
    card_lemma: str,
    base_verb_translation: str,
    conj_rev: Mapping[str, Sequence[Mapping[str, Any]]],
) -> list[dict[str, Any]]:
    """Ensure every clitic membership row carries an idiomatic inflected English translation."""
    updated = []
    for item in clitic_memberships:
        row = dict(item)
        form = row.get("form", "")
        existing_trans = row.get("translation", "")
        # If translation is just the bare lemma or missing, inflect it
        senses = [{"headword": card_lemma, "pos": "VERB", "translation": existing_trans or base_verb_translation}]
        inflected = inflect_card_senses(form, card_lemma, senses, conj_rev)
        if inflected and inflected[0].get("translation"):
            row["translation"] = inflected[0]["translation"]
        updated.append(row)
    return updated

