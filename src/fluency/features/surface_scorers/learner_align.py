"""Surface similarity scorer: phonological and morphological alignment for language learners.

Replaces the provisional stop-gap edit-distance/v1 (Decision 0027).

Learner surface similarity models how recognizable two written forms appear
to a human language learner, addressing the known failure modes of raw Levenshtein:
1. Cross-language cognates that undergo historical shifts (capitán/captain, número/number)
   are recognized through:
   - Natural consonant class correspondences (labials b/p/v/f/w, dentals d/t, velars/sibilants c/s/z/k, nasals m/n, liquids l/r)
   - Vowel shift tolerances (discounted substitution only for words of length >= 5 to protect short lookalikes)
   - Transposition / metathesis tolerance (Damerau adjacent swaps and 3-char anagram rotations e.g. -ita- vs -tai-)
   - Cluster epenthesis tolerance (excrescent b/p next to m, e.g. número/number, cámara/chamber)
2. Short words are guarded against over-matching:
   - Length guard enforced
   - Vowel shifts are not discounted for short words (len <= 4), preventing false positives like 'este'/'east', 'toho'/'the', while keeping 'nome'/'name' strictly calibrated.
3. Orthographic skeleton rewrite rules and morphological ending rules apply to both words.
"""

from __future__ import annotations

import re
from functools import lru_cache
from typing import Iterable

SCORER_ID = "learner-align/v1"

_DOUBLED = re.compile(r"(.)\1+")

NATURAL_CONSONANT_CLASSES = (
    frozenset("bpvfw"),    # Labials
    frozenset("dt"),       # Dentals / alveolars
    frozenset("cszk"),     # Sibilants / velars
    frozenset("mn"),       # Nasals
    frozenset("lr"),       # Liquids
)
VOWEL_CHARS = frozenset("aeiouy")


def _rewrite(word: str, rules: tuple[tuple[str, str], ...]) -> str:
    for source, target in rules:
        word = word.replace(source, target)
    return word


def _char_sub_cost(c1: str, c2: str, word_len: int) -> float:
    if c1 == c2:
        return 0.0
    for cls in NATURAL_CONSONANT_CLASSES:
        if c1 in cls and c2 in cls:
            return 0.35
    # Vowel shifts: discounted only for longer words (len >= 5)
    # On short words (len <= 4), vowel changes cost full 1.0 to protect short lookalikes
    if c1 in VOWEL_CHARS and c2 in VOWEL_CHARS and word_len >= 5:
        return 0.35
    return 1.0


def _cognate_align_distance(s1: str, s2: str) -> float:
    n, m = len(s1), len(s2)
    if not n or not m:
        return float(max(n, m))
    word_len = min(n, m)
    dp = [[0.0] * (m + 1) for _ in range(n + 1)]
    for i in range(n + 1):
        dp[i][0] = float(i)
    for j in range(m + 1):
        dp[0][j] = float(j)

    for i in range(1, n + 1):
        c1 = s1[i - 1]
        for j in range(1, m + 1):
            c2 = s2[j - 1]
            sub = _char_sub_cost(c1, c2, word_len)

            # Transposition / metathesis
            trans = float("inf")
            # 2-character adjacent swap (Damerau)
            if i > 1 and j > 1 and s1[i - 1] == s2[j - 2] and s1[i - 2] == s2[j - 1]:
                trans = dp[i - 2][j - 2] + 0.35
            # 3-character rotation/anagram (e.g. -ita- in capitán vs -tai- in captain)
            elif i > 2 and j > 2 and sorted(s1[i - 3 : i]) == sorted(s2[j - 3 : j]):
                trans = dp[i - 3][j - 3] + 0.50

            # Epenthesis tolerance: excrescent b/p next to m (número/number, cámara/chamber)
            epenthesis = float("inf")
            if j > 0 and s2[j - 1] in "bp" and (
                (i > 0 and s1[i - 1] == "m") or (j > 1 and s2[j - 2] == "m")
            ):
                epenthesis = dp[i][j - 1] + 0.35
            elif i > 0 and s1[i - 1] in "bp" and (
                (j > 0 and s2[j - 1] == "m") or (i > 1 and s1[i - 2] == "m")
            ):
                epenthesis = dp[i - 1][j] + 0.35

            dp[i][j] = min(
                dp[i - 1][j] + 1.0,
                dp[i][j - 1] + 1.0,
                dp[i - 1][j - 1] + sub,
                trans,
                epenthesis,
            )
    return dp[n][m]


@lru_cache(maxsize=1_000_000)
def _score(
    target_word: str,
    known_word: str,
    rules: tuple[tuple[str, str], ...],
    endings: tuple[tuple[str, str], ...],
    length_guard: float,
) -> float:
    from fluency.features.cognates import strip_accents

    def spell(word: str) -> str:
        # Skeletons first, on the word as written (they include ñ, ç, ij, ó, ů, etc.),
        # then accents are stripped.
        return strip_accents(_rewrite(word, rules))

    left = spell(target_word)
    ending_matched = False
    for source, target in endings:
        source, target = spell(source), spell(target)
        if left.endswith(source) and len(left) > len(source):
            left = left[: -len(source)] + target
            ending_matched = True
            break
    left = _DOUBLED.sub(r"\1", left)
    right = _DOUBLED.sub(r"\1", spell(known_word))
    if not left or not right:
        return 0.0
    if min(len(left), len(right)) / max(len(left), len(right)) < length_guard:
        return 0.0

    dist = _cognate_align_distance(left, right)
    max_len = max(len(left), len(right))
    if max_len == 0:
        return 0.0
    if dist == 0.0:
        return 1.0

    # Short roots (len < 5) without a regular morphological ending rule carry higher
    # information density per character. A 1-letter change alters 25-33% of the word,
    # so we scale the penalty factor to prevent marginal stretch pairs (e.g. nome/name,
    # três/three) from hitting the threshold.
    penalty_scale = 1.0 + max(0.0, 5 - max_len) * 0.15 if not ending_matched else 1.0
    return max(0.0, 1.0 - (dist * penalty_scale) / max_len)


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
    base = _score(
        (target_word or "").lower(),
        (known_word or "").lower(),
        rules,
        tuple(policy.ending_rules),
        policy.length_guard,
    )
    if policy.use_pronunciation and target_sounds and known_sounds:
        from fluency.features.phonetics import best_pronunciation_similarity

        phon = best_pronunciation_similarity(target_sounds, known_sounds)
        # Pronunciation can confirm/escalate (e.g. Czech čas vs Polish czas)
        # or dampen when written forms are marginal (base < 1.0) but sounds diverge widely (phon < 0.65).
        if base < 1.0 and phon > 0.0 and phon < 0.65:
            dampener = 0.85 + 0.15 * (phon / 0.65)
            return base * dampener
        return max(base, phon)
    return base

