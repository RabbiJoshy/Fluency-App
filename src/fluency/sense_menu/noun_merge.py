"""All-or-nothing noun merging, decided on complete, uninflected menus.

No gloss stemming, WSD shares, or displayed translations participate. Missing
counterparts and missing provider relationships are deliberately not approvals.
"""

from __future__ import annotations

from collections import defaultdict
from typing import Any

from fluency.core.hashing import canonical_content_id

RULE_VERSION = "noun-merge/v3"
# v3: a gender form is an inflection like a plural (querida, feminine of
# querido); only the noun's own entries are compared, so a participle's verb
# on the same menu (querido: querer) no longer blocks it. Whether that other
# word is used enough to keep the form apart is decided later, on real use
# (decision 0033's 3-example, 10% bar). A noun and an adjective of the same
# headword are one word.
INFLECTION_GRAMMAR = {"feminine", "masculine", "singular", "plural", "participle"}


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
    nouns = [a for a in analyses if is_noun(a.get("part_of_speech")) and _token(a.get("headword")) == lemma]
    declared = {"plural", "feminine", "masculine"}

    def form_of(a: dict) -> bool:
        provider = a.get("provider_metadata") or {}
        types = {t for value in provider.get("spanishdict", {}).get("inflection_types") or []
                 for t in _token(value).split()}
        return bool(provider.get("spanishdict", {}).get("declared_plural")
                    or types & declared
                    or (provider.get("resolution") == "structured_form_of"
                        and set(provider.get("surface_grammar") or []) & declared))
    return bool(nouns) and all(form_of(a) for a in nouns)


def _non_number_form(analyses: list[dict], surface: str, lemma: str) -> bool:
    """True when the surface is declared as something other than a gender or
    number form of the lemma (a diminutive, say)."""
    if surface == lemma:
        return False
    nouns = [a for a in analyses if is_noun(a.get("part_of_speech")) and _token(a.get("headword")) == lemma]
    for analysis in nouns:
        provider = analysis.get("provider_metadata") or {}
        grammar = set(provider.get("surface_grammar") or [])
        types = provider.get("spanishdict", {}).get("inflection_types") or []
        if provider.get("resolution") == "structured_form_of" and grammar - INFLECTION_GRAMMAR:
            return True
        if any(set(_token(value).split()) - INFLECTION_GRAMMAR for value in types):
            return True
    return False


def _feminine_form(analyses: list[dict]) -> bool:
    for analysis in analyses:
        if not is_noun(analysis.get("part_of_speech")):
            continue
        provider = analysis.get("provider_metadata") or {}
        types = {t for value in provider.get("spanishdict", {}).get("inflection_types") or []
                 for t in _token(value).split()}
        if "feminine" in set(provider.get("surface_grammar") or []) | types:
            return True
    return False


def stamp_noun_merge(cards: list[dict]) -> None:
    """Stamp a compact verdict on every noun card; a mismatch blocks its group.

    A canonical singular menu must be present. This compares all dictionary
    senses before consumers cap menus or remove unassigned/rare definitions.
    """
    groups: dict[str, list[tuple[dict, list[dict]]]] = defaultdict(list)
    heads_of: dict[int, set[str]] = {}
    for card in cards:
        analyses = _lexical(card.get("analyses") or [])
        heads = {_token(a.get("headword")) for a in analyses if is_noun(a.get("part_of_speech"))}
        if not heads:
            continue
        heads_of[id(card)] = heads
        card["noun_merge"] = {"rule_version": RULE_VERSION, "allowed": False,
                              "reason": "ambiguous_headwords", "lemma": ""}
        for head in heads:
            if _non_number_form(analyses, _token(card.get("surface_form")), head):
                card["noun_merge"]["reason"] = "not_an_inflection"
                continue
            groups[head].append((card, analyses))

    for lemma, members in groups.items():
        members = [(card, [a for a in analyses if _token(a.get("headword")) == lemma])
                   for card, analyses in members]
        signatures = [_sense_set(analyses) for _, analyses in members]
        # A feminine form joins only when its senses match the base form's;
        # a mismatch refuses that form alone (prisionera), not the plural pair.
        base = next((sig for (c, _), sig in zip(members, signatures)
                     if _token(c.get("surface_form")) == lemma), None)
        if base is not None:
            kept = []
            for (card, analyses), sig in zip(members, signatures):
                if _feminine_form(analyses) and sig[0] != base[0] and heads_of[id(card)] == {lemma}:
                    card["noun_merge"] = {"rule_version": RULE_VERSION, "lemma": lemma,
                                          "allowed": False, "reason": "different_sense_sets"}
                else:
                    kept.append(((card, analyses), sig))
            members = [m for m, _ in kept]
            signatures = [sig for _, sig in kept]
        reason = "same_complete_menu"
        if any(c.get("noun_merge_refresh_failure") for c, _ in members):
            reason = next(c["noun_merge_refresh_failure"] for c, _ in members
                          if c.get("noun_merge_refresh_failure"))
        elif any(not ({(lemma, "noun")} <= _entries(analyses) <= {(lemma, "noun"), (lemma, "adj")})
                 for _, analyses in members):
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
            # A card with two nouns of different headwords stays ambiguous.
            if len(heads_of[id(card)]) != 1:
                continue
            card["noun_merge"] = {"rule_version": RULE_VERSION, "lemma": lemma,
                                  "allowed": allowed, "reason": reason}
            if allowed:
                card["noun_merge"]["sense_set"] = canonical_content_id(sorted(signatures[0][0]))
