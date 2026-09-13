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
_EXACT_FRAMES: dict[str, tuple[str, str]] = {
    "used in progressive constructions": ("auxiliary_frame", "progressive construction"),
    "used in compound tenses": ("auxiliary_frame", "compound tense"),
    "used in place of another verb": ("substitution_frame", "another verb"),
    "used with a participle to describe a state": ("complement_form", "participle describing a state"),
    "with dates": ("argument_type", "dates"),
    "used with quantities": ("argument_type", "quantities"),
    "with pronouns": ("argument_type", "pronouns"),
    "used with first or full names": ("argument_type", "first or full names"),
    "used with negatives": ("polarity_context", "negative"),
    "used in comparisons": ("clause_context", "comparisons"),
    "with indirect questions": ("clause_context", "indirect questions"),
    "used in questions or suggestions": ("clause_context", "questions or suggestions"),
    "used in interjections": ("clause_context", "interjections"),
    "used in a correlation": ("clause_context", "correlation"),
}


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
    if exact := _EXACT_FRAMES.get(lowered):
        return SpecialistFeature("construction", exact[0], exact[1], text)
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
