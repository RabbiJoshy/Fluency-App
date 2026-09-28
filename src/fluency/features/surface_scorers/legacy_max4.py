"""The original form axis: the best of up to six readings of one question.

Kept verbatim so the pairs calibrated on it (Czech-Polish, whose recall table
is below) keep their numbers. It is no longer the default for English pairs:
taking the maximum always takes the most lenient reading, and Jaro-Winkler is
generous on short words (toho/the 0.75, este/east 0.85). See decision 0027.

    tier                        needs                 cs-pl recall @ 0.80
    raw spelling (Levenshtein + JW)  nothing                       0.479
    learned correspondences     nothing                            0.616
    hand skeleton               rules someone wrote                0.670
    pronunciation               IPA on both sides                  0.776
"""

from __future__ import annotations

from typing import Iterable

SCORER_ID = "legacy-max4/v1"


def score(
    target_word: str,
    known_word: str,
    policy,
    *,
    target_sounds: Iterable[str] = (),
    known_sounds: Iterable[str] = (),
    correspondences=None,
) -> float:
    from fluency.features.cognates import (
        jaro_winkler_similarity,
        similarity,
        skeleton,
        strip_accents,
    )
    from fluency.features.phonetics import best_pronunciation_similarity

    left, right = strip_accents(target_word), strip_accents(known_word)
    skel_left = skeleton(target_word, policy.target_skeleton)
    skel_right = skeleton(known_word, policy.known_skeleton)
    best = max(
        similarity(left, right),
        jaro_winkler_similarity(left, right),
        similarity(skel_left, skel_right),
        jaro_winkler_similarity(skel_left, skel_right),
    )
    if correspondences is not None and best < 1.0:
        best = max(best, correspondences.similarity(left, right))
    if policy.use_pronunciation and best < 1.0:
        best = max(best, best_pronunciation_similarity(target_sounds, known_sounds))
    return best
