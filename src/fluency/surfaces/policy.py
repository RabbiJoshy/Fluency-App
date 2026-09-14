"""Folding observations into a verdict, which is a separate question.

"dallas is capitalised in 100% of its 38 occurrences" is a fact and stays true.
"therefore it does not belong in the deck" is an opinion, and opinions differ:
Czech may well want Praha, Spanish does not want Dallas, and whether a deck
teaches naturalised loanwords is a choice about the deck rather than about the
word. Storing the opinion would mean re-deriving the evidence every time the
opinion changed, which is the cost this whole store exists to avoid.

So verdicts are computed at read time from the events plus a per-language
policy file, and every policy starts identical. A language differs from the
default only where a measurement says it should -- not because a decision was
taken about it once and never revisited.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Iterable, Mapping

KEEP, REVIEW, EXCLUDE = "keep", "review", "exclude"
_ORDER = {KEEP: 0, REVIEW: 1, EXCLUDE: 2}

# Identical for every language until evidence says otherwise. A reason code
# absent from a policy is "keep": silence about a fact is not grounds to drop a
# word.
DEFAULT_POLICY: dict[str, str] = {
    "english_wordlist": REVIEW,
    "foreign_frequency_list": REVIEW,
    # On its own this means only "another surface in the list carries accents
    # over these letters", which is true of "a" beside "a-grave" and "de"
    # beside "de-acute" -- minimal pairs where both spellings are real words.
    # Taken as grounds to exclude it deletes the commonest words in the
    # language. It becomes conclusive only in company: see COMBINATIONS.
    "accent_stripped_duplicate": REVIEW,
    "abbreviation_form": KEEP,
    "capitalised_in_corpus": REVIEW,
    "low_harvest_yield": KEEP,
    "dictionary_absent": KEEP,
    "dictionary_entry_language": REVIEW,
    "dictionary_spelling_substitution": KEEP,
    "dictionary_pos_gloss_mismatch": EXCLUDE,
    "lemma_resolved": KEEP,
    "lemma_absent_from_dictionary": KEEP,
    "human_review": EXCLUDE,
}


# Evidence that is inconclusive alone and conclusive together. An unaccented
# spelling that no dictionary knows, sitting beside an accented one that it
# does, is a stripping rather than a word -- "radio" for "radio-acute",
# "atras" for "atras-acute". The same unaccented spelling WITH an entry of its
# own is simply a different word, and survives.
COMBINATIONS: list[tuple[frozenset[str], str]] = [
    (frozenset({"capitalised_in_corpus", "dictionary_pos_gloss_mismatch"}), EXCLUDE),
    (frozenset({"english_wordlist", "dictionary_entry_language"}), EXCLUDE),
]

# Facts that settle the question the other way: whatever else is suspected, a
# surface an external morphology source resolved to a lemma is a word. Czech
# needs this -- its dictionary is absent for 43% of surfaces, so "dictionary
# has no entry" carries almost no information there, and combining it with
# anything produced verdicts against "policii", "filmu" and "stalo".
VETOES = frozenset({"lemma_resolved", "abbreviation_form"})

# Note on accent stripping: there is no reliable automatic test. "radio" for
# "radio-acute" is a stripping; "estas" beside "estas-acute", and the clitics
# "ma" and "ta", are words in their own right that no dictionary here lists.
# The observer records the coincidence and the policy leaves it at review --
# the exclusions that were actually made came from reading them, and are
# recorded as human_review rather than dressed up as derivation.


def load_policy(path: Path | None) -> dict[str, str]:
    policy = dict(DEFAULT_POLICY)
    if path and path.exists():
        declared = json.loads(path.read_text(encoding="utf-8"))
        policy.update(declared.get("reason_codes") or {})
    return policy


def verdict(
    events: Iterable[Mapping[str, Any]], policy: Mapping[str, str]
) -> dict[str, Any]:
    """The strictest verdict any single observation warrants, and why.

    Strictest wins because the codes describe independent evidence: a surface
    that is both an English word and capitalised throughout is not less
    suspicious than one that is only capitalised.
    """
    events = list(events)
    decision, reasons = KEEP, []
    present = {event.get("reason_code") for event in events}
    for event in events:
        code = event.get("reason_code")
        outcome = policy.get(code, KEEP)
        if outcome != KEEP:
            reasons.append(code)
        if _ORDER[outcome] > _ORDER[decision]:
            decision = outcome
    for codes, outcome in COMBINATIONS:
        if codes <= present and _ORDER[outcome] > _ORDER[decision]:
            decision = outcome
            reasons.extend(codes)
    if decision == EXCLUDE and (present & VETOES) and "human_review" not in present:
        decision = REVIEW
        reasons.append("vetoed_by:" + ",".join(sorted(present & VETOES)))
    return {
        "verdict": decision,
        "reason_codes": sorted(set(reasons)),
        "observations": len(events),
    }


def fold(
    grouped: Mapping[str, list[Mapping[str, Any]]], policy: Mapping[str, str]
) -> dict[str, dict[str, Any]]:
    return {surface: verdict(events, policy) for surface, events in grouped.items()}
