"""All-or-nothing noun merging, decided on complete, uninflected menus.

No gloss stemming, WSD shares, or displayed translations participate. Missing
counterparts and missing provider relationships are deliberately not approvals.
"""

from __future__ import annotations

from collections import defaultdict
from typing import Any

from fluency.core.hashing import canonical_content_id

RULE_VERSION = "noun-merge/v2"


def _token(value: Any) -> str:
    return str(value or "").strip().casefold()


def is_noun(pos: Any) -> bool:
    return _token(pos) == "noun" or "noun" in _token(pos).split()


def _lexical(analyses: list[dict]) -> list[dict]:
    return [a for a in analyses if _token(a.get("part_of_speech")) not in
            {"mwe", "clitic"} and a.get("senses")]


def _headwords(analyses: list[dict]) -> set[str]:
    # Dictionary phrase senses participate in the equality test, but do not
    # name a second noun lemma. Corpus MWE attachments are excluded above.
    return {_token(a.get("headword")) for a in analyses
            if _token(a.get("part_of_speech")) != "phrase"}


def _entries(analyses: list[dict]) -> set[tuple[str, str]]:
    # Equal spellings do not make a noun and verb the same dictionary entry.
    # Multiple provider analyses of the same noun entry are still one entry.
    return {(_token(a.get("headword")),
             "noun" if is_noun(a.get("part_of_speech")) else _token(a.get("part_of_speech")))
            for a in analyses if _token(a.get("part_of_speech")) != "phrase"}


def _restricted(analysis: dict, sense: dict) -> bool:
    if not is_noun(analysis.get("part_of_speech")):
        return False
    provider = sense.get("provider_metadata") or {}
    marks = set(provider.get("tags") or []) | set(provider.get("entry_tags") or [])
    if marks & {"plural-only", "singular-only", "in-plural", "plural-normally", "no-plural"}:
        return True
    if "plural" in _token(analysis.get("part_of_speech")).split():
        return True
    features = sense.get("specialist_features") or (sense.get("metadata") or {}).get("features") or []
    return any(f.get("kind") != "surface_mark" and
               str(f.get("value", "")).startswith("number=") for f in features)


def _sense_set(analyses: list[dict]) -> tuple[set[str], bool]:
    identities: set[str] = set()
    restricted = False
    for analysis in analyses:
        for sense in analysis["senses"]:
            reference = sense.get("source_reference")
            if not reference or not sense.get("translation"):
                return set(), True
            # Old SpanishDict caches normalized away the original POS label,
            # including "plural noun". They cannot certify unrestricted use.
            if (analysis.get("source_adapter") == "spanishdict-sense-menu/v1"
                    and not (sense.get("provider_metadata") or {}).get("spanishdict", {}).get("part_of_speech_label")):
                return set(), True
            if (analysis.get("source_adapter") == "wiktionary-sense-menu/v1"
                    and "entry_tags" not in (sense.get("provider_metadata") or {})):
                return set(), True
            restricted |= _restricted(analysis, sense)
            features = sense.get("specialist_features") or (sense.get("metadata") or {}).get("features") or []
            # Keep semantic qualifiers; only surface grammar is irrelevant.
            lexical_features = sorted({canonical_content_id(f) for f in features
                                       if f.get("kind") != "surface_mark"})
            identities.add(canonical_content_id([
                analysis.get("source_adapter"), _token(analysis.get("headword")),
                _token(analysis.get("part_of_speech")), reference,
                sense.get("translation"), sense.get("definition", ""), lexical_features,
            ]))
    return identities, restricted


def _declared_form(analyses: list[dict], surface: str, lemma: str) -> bool:
    if surface == lemma:
        return True
    nouns = [a for a in analyses if is_noun(a.get("part_of_speech"))]
    return bool(nouns) and all(
        (a.get("provider_metadata") or {}).get("spanishdict", {}).get("declared_plural")
        or ((a.get("provider_metadata") or {}).get("resolution") == "structured_form_of"
            and "plural" in ((a.get("provider_metadata") or {}).get("surface_grammar") or []))
        for a in nouns
    )


def _non_number_form(analyses: list[dict], surface: str, lemma: str) -> bool:
    if surface == lemma:
        return False
    nouns = [a for a in analyses if is_noun(a.get("part_of_speech"))]
    for analysis in nouns:
        provider = analysis.get("provider_metadata") or {}
        grammar = set(provider.get("surface_grammar") or [])
        types = provider.get("spanishdict", {}).get("inflection_types") or []
        if (provider.get("resolution") == "structured_form_of" and grammar
                and "plural" not in grammar and grammar & {"singular", "feminine", "masculine"}):
            continue
        if types and all("singular" in _token(value).split() and "plural" not in _token(value).split() for value in types):
            continue
        return False
    return bool(nouns)


def stamp_noun_merge(cards: list[dict]) -> None:
    """Stamp a compact verdict on every noun card; a mismatch blocks its group.

    A canonical singular menu must be present. This compares all dictionary
    senses before consumers cap menus or remove unassigned/rare definitions.
    """
    groups: dict[str, list[tuple[dict, list[dict]]]] = defaultdict(list)
    for card in cards:
        analyses = _lexical(card.get("analyses") or [])
        heads = {_token(a.get("headword")) for a in analyses if is_noun(a.get("part_of_speech"))}
        if not heads:
            continue
        card["noun_merge"] = {"rule_version": RULE_VERSION, "allowed": False,
                              "reason": "ambiguous_headwords", "lemma": ""}
        for head in heads:
            if _non_number_form(analyses, _token(card.get("surface_form")), head):
                card["noun_merge"]["reason"] = "not_a_plural_relationship"
                continue
            groups[head].append((card, analyses))

    for lemma, members in groups.items():
        signatures = [_sense_set(analyses) for _, analyses in members]
        reason = "same_complete_menu"
        if any(_headwords(analyses) != {lemma} for _, analyses in members):
            reason = "ambiguous_headwords"
        elif any(c.get("noun_merge_refresh_failure") for c, _ in members):
            reason = next(c["noun_merge_refresh_failure"] for c, _ in members
                          if c.get("noun_merge_refresh_failure"))
        elif any(_entries(analyses) != {(lemma, "noun")} for _, analyses in members):
            reason = "multiple_dictionary_entries"
        elif not any(_token(c.get("surface_form")) == lemma for c, _ in members):
            reason = "missing_singular_menu"
        elif any(restricted for _, restricted in signatures):
            reason = "number_specific_or_incomplete_sense"
        elif any(not _declared_form(a, _token(c.get("surface_form")), lemma) for c, a in members):
            reason = "unverified_form_relationship"
        elif any(senses != signatures[0][0] for senses, _ in signatures):
            reason = "different_sense_sets"
        allowed = reason == "same_complete_menu"
        for card, analyses in members:
            # An ambiguous card participates in all candidate groups but can
            # never be approved by one of them.
            if len(_headwords(analyses)) != 1:
                continue
            card["noun_merge"] = {"rule_version": RULE_VERSION, "lemma": lemma,
                                  "allowed": allowed, "reason": reason}
            if allowed:
                card["noun_merge"]["sense_set"] = canonical_content_id(sorted(signatures[0][0]))
