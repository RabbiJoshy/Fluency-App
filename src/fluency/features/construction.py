"""Canonical construction frames shared by dictionary-provider adapters."""

from __future__ import annotations

import re

from fluency.features.contract import SpecialistFeature


_OBJECT_ROLE = re.compile(r"^(?:as an?\s+)?(?P<role>direct|indirect) objects?\b", re.I)
_POSITION = re.compile(
    r"^(?P<position>before|after|preceding|following)\s+(?:an?\s+|the\s+)?"
    r"(?P<form>adjectives?|common nouns?|gerunds?|infinitives?|nouns?|participles?|pronouns?|verbs?)$",
    re.I,
)
_COMPLEMENT = re.compile(
    r"^(?:used\s+)?with\s+(?:an?\s+|the\s+)?"
    r"(?P<form>adjectives?|clauses?|gerunds?|infinitives?|nouns?|participles?|pronouns?|verbs?)$",
    re.I,
)
_BRACKETED_COMPLEMENT = re.compile(
    r"^\[with\s+(?P<form>adjective|clause|gerund|infinitive|noun|participle|pronoun|verb)\]$",
    re.I,
)


def _singular(value: str) -> str:
    lowered = value.casefold()
    return {
        "adjectives": "adjective", "clauses": "clause", "gerunds": "gerund",
        "infinitives": "infinitive", "nouns": "noun", "participles": "participle",
        "pronouns": "pronoun", "verbs": "verb", "common nouns": "common noun",
    }.get(lowered, lowered)


def structured_construction(text: str) -> SpecialistFeature | None:
    """Normalize only closed, provider-independent frame wordings."""

    lowered = text.casefold().strip(" .;:()")
    if match := _OBJECT_ROLE.match(lowered):
        return SpecialistFeature("construction", "object_role", f"{match.group('role')} object", text)
    if match := _POSITION.fullmatch(lowered):
        position = "before" if match.group("position") == "preceding" else (
            "after" if match.group("position") == "following" else match.group("position")
        )
        return SpecialistFeature("construction", "position", f"{position} {_singular(match.group('form'))}", text)
    match = _COMPLEMENT.fullmatch(lowered) or _BRACKETED_COMPLEMENT.fullmatch(lowered)
    if match:
        return SpecialistFeature("construction", "complement_form", _singular(match.group("form")), text)
    return None
