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
_declare("modality", "unknown", "used to express that something is yet to be known")
_declare("modality", "uncertainty", "used to express lack of certainty about what's going to be said", "used to express indecision")
_declare("modality", "intention", "used to express intention or design")
_declare("modality", "condition", "used to express condition")

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
_declare("semantic_relation", "progress", "used to indicate progress")
_declare("semantic_relation", "closeness", "indicating closeness")
_declare("semantic_relation", "limit", "used to indicate limit")
_declare("semantic_relation", "comparison", "used to express comparison", "indicating superiority")
_declare("semantic_relation", "result", "indicating a result", "indicating a solution")
_declare("semantic_relation", "sequence", "indicating sequence")
_declare("semantic_relation", "space", "indicating space")
_declare("semantic_relation", "preference", "indicating preference")
_declare("semantic_relation", "material", "used to indicate material")
_declare("semantic_relation", "content", "used to indicate content")
_declare("semantic_relation", "instrument", "indicating instrument")
_declare("semantic_relation", "accompaniment", "indicating accompaniment")
_declare("semantic_relation", "passive agent", "used to indicate the agent in the passive")
_declare("semantic_relation", "subject definition", "used to define the subject")
_declare("semantic_relation", "object definition", "used to define the object")
_declare("semantic_relation", "characteristic", "used to express characteristics", "used to talk about characteristics", "used to indicate characteristics")
_declare("semantic_relation", "quality", "used to express a quality")

_declare("discourse_function", "emphasis", "used to express emphasis", "used for emphasis", "used to emphasize", "indicating emphasis")
_declare("discourse_function", "negation", "used to negate")
_declare("discourse_function", "alternative", "used to introduce alternatives", "used to express alternatives", "used to give alternatives")
_declare("discourse_function", "contrast", "used to indicate contrast", "indicating contradiction", "expressing opposition")
_declare("discourse_function", "filler", "used as a filler", "used to fill space in a conversation")
_declare("discourse_function", "introducer", "used to introduce a statement or question", "used to introduce a subordinate clause", "used to introduce an example")
_declare("discourse_function", "reinforcement", "used to reinforce a question or statement", "used to underscore that something is obvious")
_declare("discourse_function", "interrogation", "used to express interrogation")
_declare("discourse_function", "negative alternative", "used to give a negative alternative")
_declare("discourse_function", "opposite", "used to express the opposite")
_declare("discourse_function", "habitual action", "used to express a habitual action")
_declare("discourse_function", "present action", "used to express a specific action in the present", "indicating an action")
_declare("discourse_function", "approximation", "used to express that something is not exact")

_declare("speech_act", "request", "used to ask for something or permission")
_declare("speech_act", "suggestion", "used to make a suggestion")
_declare("speech_act", "warning", "used to warn")
_declare("speech_act", "apology", "used to apologize", "used to ask forgiveness")
_declare("speech_act", "agreement", "used to express agreement", "used to indicate assent", "used to express confirmation")
_declare("speech_act", "attention", "used to attract attention", "used to call attention", "used to call someone's attention", "used to request attention")
_declare("speech_act", "encouragement", "used to encourage someone to do something", "used to express encouragement")
_declare("speech_act", "command", "used as a command", "used to give orders")
_declare("speech_act", "phone answer", "used to answer the phone", "used when answering the phone")
_declare("speech_act", "reproach", "used to indicate a reproach")
_declare("speech_act", "calming", "used to tell someone to be calm")
_declare("speech_act", "repeat request", "used to ask someone to repeat something", "used to ask for something to be repeated")
_declare("speech_act", "information request", "used to ask whether something exists", "used to elicit further information")
_declare("speech_act", "acceptance", "used to agree to a request or accept an invitation")
_declare("speech_act", "information", "used to give information")
_declare("speech_act", "urging", "used to urge someone")
_declare("speech_act", "silence request", "used to ask for silence")
_declare("speech_act", "leave command", "used to tell someone to leave")
_declare("speech_act", "permission to pass", "used to ask permission to go past")
_declare("speech_act", "objection", "used to object or disagree", "used to express disagreement")
_declare("speech_act", "congratulation", "used to congratulate someone")
_declare("speech_act", "reply", "used as a reply")
_declare("speech_act", "toast", "used to toast")
_declare("speech_act", "shoot command", "used to order someone to shoot")
_declare("speech_act", "address man", "used to address a man")
_declare("speech_act", "address male friend", "used to address a male friend")
_declare("speech_act", "address attractive woman", "used to address an attractive woman")
_declare("speech_act", "address young girl", "used to address a young girl")

_declare("emotion", "surprise", "used to express surprise", "expressing surprise")
_declare("emotion", "annoyance", "used to express annoyance", "used to express irritation")
_declare("emotion", "approval", "used to express approval")
_declare("emotion", "desire", "used to express a desire")
_declare("emotion", "danger", "used to express danger")
_declare("emotion", "pain", "used to express pain")
_declare("emotion", "disbelief", "used to express disbelief")
_declare("emotion", "dismay", "used to express dismay")
_declare("emotion", "confusion", "used to express confusion")
_declare("emotion", "anger", "used to express anger", "used to express anger or surprise")
_declare("emotion", "anger or annoyance", "used to express anger or annoyance")
_declare("emotion", "exasperation", "used to express exasperation")
_declare("emotion", "compassion", "used to express compassion")
_declare("emotion", "joy", "used to express joy")
_declare("emotion", "admiration", "used to express admiration")
_declare("emotion", "sarcasm", "used to express sarcasm")
_declare("emotion", "goodwill", "used to express good will")
_declare("emotion", "displeasure", "expressing displeasure")
_declare("emotion", "surprise or pity", "used to express surprise or pity")
_declare("emotion", "surprise or fright", "used to express surprise or fright")
_declare("emotion", "surprise or anger", "expressing surprise or anger")
_declare("emotion", "joy or amazement", "used to express joy or amazement")

# These phrases clarify the lexical scope of a dictionary sense rather than
# giving the learner a compact grammatical or pragmatic cue. Keeping them typed
# helps later WSD, but the card should leave their original prose beside the
# gloss instead of duplicating it as a metadata pill.
_declare("semantic_scope", "visit or stay", "used to talk about a visit or stay")
_declare("semantic_scope", "process", "used to discuss a process")
_declare("semantic_scope", "prices", "used to talk about prices")
_declare("semantic_scope", "emotion or state", "used to express an emotion or state", "used to express a state")
_declare("semantic_scope", "pair", "expressing one of two people or things", "used to refer to a couple")
_declare("semantic_scope", "several relatives", "used to refer to several relatives")
_declare("semantic_scope", "known referent", "used to refer to something known or mentioned")
_declare("semantic_scope", "perceived description", "used to describe how something or someone is perceived")
_declare("semantic_scope", "general or specific", "indicating something specific", "indicating something in general")
_declare("semantic_scope", "function or role", "used to indicate a function or use", "used to indicate a role or position")


def functional_feature(text: str) -> SpecialistFeature:
    """Return a canonical purpose when known, otherwise preserve usage prose."""

    clean = text.strip()
    canonical = _ALIASES.get(clean.casefold().strip(" .;:()[]"))
    if canonical:
        return SpecialistFeature("functional", canonical[0], canonical[1], clean)
    return SpecialistFeature("functional", "usage_note", clean, clean)
