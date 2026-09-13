"""Canonical semantic and pragmatic functions shared by dictionary adapters."""

from __future__ import annotations

from fluency.features.contract import SpecialistFeature


# Exact aliases are deliberately conservative. Provider prose outside this
# vocabulary remains a functional usage_note with its original value until an
# audit establishes that two descriptions really express the same concept.
_ALIASES: dict[str, tuple[str, str]] = {}


def _declare(kind: str, value: str, *phrases: str) -> None:
    for phrase in phrases:
        _ALIASES[phrase] = (kind, value)


_declare("modality", "obligation", "used to indicate an obligation", "used to express obligation")
_declare("modality", "moral obligation", "used to indicate moral obligation")
_declare("modality", "capability", "used to indicate capability")
_declare("modality", "possibility", "used to indicate possibility", "used to express possibility", "used to describe a possibility")
_declare("modality", "supposition", "used to indicate supposition")

_declare("temporal_relation", "time", "used to express time", "used to indicate time", "used to refer to time", "indicating time")
_declare("temporal_relation", "future", "used to indicate the future", "used to indicate a future action", "used to denote future action")
_declare("temporal_relation", "duration", "used to indicate duration", "used to indicate a range of time", "used to indicate a period of time")
_declare("temporal_relation", "exact time", "used to indicate an exact moment", "indicating moment in time")
_declare("temporal_relation", "frequency", "used to indicate frequency", "used to express frequency")
_declare("temporal_relation", "age", "used to express age")
_declare("temporal_relation", "imminence", "used to express imminence")

_declare("semantic_relation", "location", "used to indicate place", "used to express location", "used to indicate location", "indicating place", "indicating location")
_declare("semantic_relation", "position", "used to indicate position", "indicating position")
_declare("semantic_relation", "direction", "used to talk about directions", "used to indicate direction", "used to express direction", "indicating direction")
_declare("semantic_relation", "movement", "used to indicate movement")
_declare("semantic_relation", "origin", "used to indicate origin", "used to indicate point of departure", "used to indicate starting point")
_declare("semantic_relation", "destination", "used to indicate destination")
_declare("semantic_relation", "distance or level", "used to indicate distance or level")
_declare("semantic_relation", "possession", "used to indicate possession", "used to express possession", "used to indicate relationship or possession")
_declare("semantic_relation", "cause", "used to indicate cause", "used to express cause", "indicating cause")
_declare("semantic_relation", "purpose", "used to express purpose", "used to indicate aim")
_declare("semantic_relation", "manner", "used to express manner", "indicating manner", "used to indicate mode", "indicating mode")
_declare("semantic_relation", "quantity", "expressing quantity")
_declare("semantic_relation", "characteristic", "used to express characteristics", "used to talk about characteristics", "used to indicate characteristics")
_declare("semantic_relation", "quality", "used to express a quality")

_declare("discourse_function", "emphasis", "used to express emphasis", "used for emphasis", "used to emphasize", "indicating emphasis")
_declare("discourse_function", "negation", "used to negate")
_declare("discourse_function", "alternative", "used to introduce alternatives", "used to express alternatives", "used to give alternatives")
_declare("discourse_function", "contrast", "used to indicate contrast", "indicating contradiction", "expressing opposition")
_declare("discourse_function", "filler", "used as a filler", "used to fill space in a conversation")

_declare("speech_act", "request", "used to ask for something or permission")
_declare("speech_act", "suggestion", "used to make a suggestion")
_declare("speech_act", "warning", "used to warn")
_declare("speech_act", "apology", "used to apologize", "used to ask forgiveness")
_declare("speech_act", "agreement", "used to express agreement", "used to indicate assent", "used to express confirmation")
_declare("speech_act", "attention", "used to attract attention", "used to call attention", "used to call someone's attention", "used to request attention")
_declare("speech_act", "encouragement", "used to encourage someone to do something", "used to express encouragement")
_declare("speech_act", "command", "used as a command", "used to give orders")
_declare("speech_act", "phone answer", "used to answer the phone", "used when answering the phone")

_declare("emotion", "surprise", "used to express surprise", "expressing surprise")
_declare("emotion", "annoyance", "used to express annoyance", "used to express irritation")
_declare("emotion", "approval", "used to express approval")
_declare("emotion", "desire", "used to express a desire")


def functional_feature(text: str) -> SpecialistFeature:
    """Return a canonical purpose when known, otherwise preserve usage prose."""

    clean = text.strip()
    canonical = _ALIASES.get(clean.casefold().strip(" .;:()[]"))
    if canonical:
        return SpecialistFeature("functional", canonical[0], canonical[1], clean)
    return SpecialistFeature("functional", "usage_note", clean, clean)
