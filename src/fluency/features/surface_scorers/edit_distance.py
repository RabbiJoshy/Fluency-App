"""Provisional: one normalised edit distance, after both words are spelled alike.

PROVISIONAL. The owner is not satisfied with this scorer; it is the simplest
thing that behaves predictably, chosen so the cognate cutoff means the same at
every word length. Decision 0027 records the open question and what a
replacement must beat.

    1. the pair's rewrite rules applied to BOTH words (target and known rules
       together), so a rule can never help one side and hurt the other -- the
       one-sided c -> k rule is what made comunicar/communicate score 0.55;
       then accents stripped
    2. the target's regular endings rewritten to English ones (policy
       ``ending_rules``: idad -> ity, ción -> tion), target side only
    3. doubled letters collapsed (communicate -> comunicate)
    4. the length guard, inside the score: a pair that fails it scores 0

then ``1 - edits / longer length``. No Jaro-Winkler, no maximum over readings.
"""

from __future__ import annotations

import re
from functools import lru_cache
from typing import Iterable

SCORER_ID = "edit-distance/v1"

_DOUBLED = re.compile(r"(.)\1+")


def _rewrite(word: str, rules: tuple[tuple[str, str], ...]) -> str:
    for source, target in rules:
        word = word.replace(source, target)
    return word


@lru_cache(maxsize=1_000_000)
def _score(
    target_word: str,
    known_word: str,
    rules: tuple[tuple[str, str], ...],
    endings: tuple[tuple[str, str], ...],
    length_guard: float,
) -> float:
    from fluency.features.cognates import similarity, strip_accents

    def spell(word: str) -> str:
        # Rules first, on the word as written (they include ñ, ç, ij), then
        # accents go. The ending rules pass through the same spelling so that
        # "ción" and "tion" are compared in the alphabet the words end up in.
        return strip_accents(_rewrite(word, rules))

    left = spell(target_word)
    for source, target in endings:
        source, target = spell(source), spell(target)
        if left.endswith(source) and len(left) > len(source):
            left = left[: -len(source)] + target
            break
    left = _DOUBLED.sub(r"\1", left)
    right = _DOUBLED.sub(r"\1", spell(known_word))
    if not left or not right:
        return 0.0
    if min(len(left), len(right)) / max(len(left), len(right)) < length_guard:
        return 0.0
    return similarity(left, right)


def score(
    target_word: str,
    known_word: str,
    policy,
    *,
    target_sounds: Iterable[str] = (),
    known_sounds: Iterable[str] = (),
    correspondences=None,
) -> float:
    rules = tuple(policy.target_skeleton) + tuple(policy.known_skeleton)
    return _score(
        (target_word or "").lower(),
        (known_word or "").lower(),
        rules,
        tuple(policy.ending_rules),
        policy.length_guard,
    )
