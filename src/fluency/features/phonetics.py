"""How alike two words sound, from the IPA a dictionary already records.

The form axis has until now been spelling: normalised edit distance, with an
ordered rewrite table per pair mapping both orthographies onto a shared
alphabet. That works, and it has two costs. It is crude — every substitution
costs 1, so Czech ``h``/Polish ``g`` is as expensive as ``h``/``z`` even though
one is a real correspondence and the other is not. And it does not scale: each
new pair needs its rewrite rules written by hand before it scores properly.

Pronunciation removes both costs at once, because the rules a skeleton encodes
by hand are *already implied* by the phonetics. Czech ``š`` and Polish ``sz`` are
different letters and the same sound; ``čas``/``czas`` differ in two characters
of three and not at all in speech. So this module scores the sounds, and does it
with a substitution cost that reflects how far apart two sounds actually are:

    p / b   voicing alone                  cheap
    p / t   place alone                    moderate
    p / k   place, further                 dearer
    p / a   consonant against vowel        maximal

Coverage is what makes this practical rather than theoretical. Wiktionary
carries IPA for 98.3% of Czech lemma entries and 99.3% of its inflected ones, so
this works at surface level — which is the level cards live at.

Two things this deliberately does not do. It does not replace the orthographic
axis: this feature is about *reading* recognition, and ``central``/``central``
is transparent on the page while being said quite differently in French and
English. And it does not model a listener — a learner reading a flashcard is
not hearing it. Sound is evidence *about* recognisability, taken alongside
spelling rather than instead of it.
"""

from __future__ import annotations

import re
import unicodedata
from typing import Iterable, Sequence


# Ordinal, front of the mouth to the back, so |a - b| is a real distance rather
# than a category mismatch: p/t are neighbours and p/k are not.
PLACES = {
    "bilabial": 0,
    "labiodental": 1,
    "dental": 2,
    "alveolar": 3,
    "postalveolar": 4,
    "retroflex": 5,
    "palatal": 6,
    "velar": 7,
    "uvular": 8,
    "pharyngeal": 9,
    "glottal": 10,
}
_PLACE_SPAN = max(PLACES.values())

# Manners are categories, not a scale, so nearness is stated directly. Only
# pairs that are genuinely confusable are listed; everything else is maximally
# far apart.
MANNER_NEARNESS = {
    frozenset({"stop", "affricate"}): 0.65,
    frozenset({"affricate", "fricative"}): 0.70,
    frozenset({"stop", "nasal"}): 0.45,
    frozenset({"fricative", "approximant"}): 0.45,
    frozenset({"approximant", "lateral"}): 0.60,
    frozenset({"trill", "lateral"}): 0.45,
    frozenset({"trill", "approximant"}): 0.50,
    frozenset({"nasal", "lateral"}): 0.35,
}

# (manner, place, voiced)
CONSONANTS: dict[str, tuple[str, str, bool]] = {
    "p": ("stop", "bilabial", False),
    "b": ("stop", "bilabial", True),
    "t": ("stop", "alveolar", False),
    "d": ("stop", "alveolar", True),
    "ʈ": ("stop", "retroflex", False),
    "ɖ": ("stop", "retroflex", True),
    "c": ("stop", "palatal", False),
    "ɟ": ("stop", "palatal", True),
    "k": ("stop", "velar", False),
    "ɡ": ("stop", "velar", True),
    "g": ("stop", "velar", True),
    "q": ("stop", "uvular", False),
    "ʔ": ("stop", "glottal", False),
    "m": ("nasal", "bilabial", True),
    "ɱ": ("nasal", "labiodental", True),
    "n": ("nasal", "alveolar", True),
    "ɲ": ("nasal", "palatal", True),
    "ŋ": ("nasal", "velar", True),
    "f": ("fricative", "labiodental", False),
    "v": ("fricative", "labiodental", True),
    "θ": ("fricative", "dental", False),
    "ð": ("fricative", "dental", True),
    "s": ("fricative", "alveolar", False),
    "z": ("fricative", "alveolar", True),
    "ʃ": ("fricative", "postalveolar", False),
    "ʒ": ("fricative", "postalveolar", True),
    "ʂ": ("fricative", "retroflex", False),
    "ʐ": ("fricative", "retroflex", True),
    "ɕ": ("fricative", "palatal", False),
    "ʑ": ("fricative", "palatal", True),
    "ç": ("fricative", "palatal", False),
    "ʝ": ("fricative", "palatal", True),
    "x": ("fricative", "velar", False),
    "ɣ": ("fricative", "velar", True),
    "χ": ("fricative", "uvular", False),
    "ʁ": ("fricative", "uvular", True),
    "h": ("fricative", "glottal", False),
    "ɦ": ("fricative", "glottal", True),
    "ʋ": ("approximant", "labiodental", True),
    "ɹ": ("approximant", "alveolar", True),
    "j": ("approximant", "palatal", True),
    "w": ("approximant", "velar", True),
    "ɰ": ("approximant", "velar", True),
    "l": ("lateral", "alveolar", True),
    "ʎ": ("lateral", "palatal", True),
    "ɫ": ("lateral", "velar", True),
    "r": ("trill", "alveolar", True),
    "ʀ": ("trill", "uvular", True),
    "ɾ": ("trill", "alveolar", True),
    "ř": ("trill", "alveolar", True),
    "ts": ("affricate", "alveolar", False),
    "dz": ("affricate", "alveolar", True),
    "tʃ": ("affricate", "postalveolar", False),
    "dʒ": ("affricate", "postalveolar", True),
    "tʂ": ("affricate", "retroflex", False),
    "dʐ": ("affricate", "retroflex", True),
    "tɕ": ("affricate", "palatal", False),
    "dʑ": ("affricate", "palatal", True),
}

# (height 0 close .. 3 open, backness 0 front .. 2 back, rounded)
VOWELS: dict[str, tuple[float, float, bool]] = {
    "i": (0.0, 0.0, False),
    "y": (0.0, 0.0, True),
    "ɪ": (0.5, 0.25, False),
    "ʏ": (0.5, 0.25, True),
    "e": (1.0, 0.0, False),
    "ø": (1.0, 0.0, True),
    "ɛ": (1.5, 0.0, False),
    "œ": (1.5, 0.0, True),
    "æ": (2.5, 0.0, False),
    "a": (3.0, 0.0, False),
    "ɐ": (2.5, 1.0, False),
    "ə": (1.5, 1.0, False),
    "ɜ": (1.5, 1.0, False),
    "ɨ": (0.0, 1.0, False),
    "ʉ": (0.0, 1.0, True),
    "ɯ": (0.0, 2.0, False),
    "u": (0.0, 2.0, True),
    "ʊ": (0.5, 1.75, True),
    "o": (1.0, 2.0, True),
    "ɔ": (1.5, 2.0, True),
    "ɑ": (3.0, 2.0, False),
    "ɒ": (3.0, 2.0, True),
    "ʌ": (1.5, 2.0, False),
}
_HEIGHT_SPAN = 3.0
_BACK_SPAN = 2.0

# Stress, length, syllable breaks, tone and the slashes or brackets a citation
# is wrapped in: notation about the sounds rather than the sounds themselves.
_IPA_NOTATION = re.compile(r"[/\[\]()ˈˌːˑ.\-‿|‖↗↘\s]")
# Tie bars join the halves of an affricate; the halves are what we read.
_TIE_BARS = str.maketrans("", "", "͜͡")

# Two-character affricates, longest first so ``t͡ʃ`` is not read as ``t`` + ``ʃ``.
_DIGRAPHS = tuple(sorted((key for key in CONSONANTS if len(key) == 2), key=len, reverse=True))


def normalise_ipa(text: str) -> str:
    """Strip the notation, keep the sounds.

    Combining diacritics go too. They carry real detail — palatalisation,
    devoicing, nasality — but modelling them properly means modelling how each
    interacts with its base, and reading them as separate segments (which is
    what a naive pass does) is worse than dropping them: it inserts a phantom
    sound into the alignment and makes two near-identical words look different.
    """

    if not text:
        return ""
    stripped = _IPA_NOTATION.sub("", text).translate(_TIE_BARS)
    decomposed = unicodedata.normalize("NFD", stripped)
    return "".join(ch for ch in decomposed if not unicodedata.combining(ch))


def segments(ipa: str) -> tuple[str, ...]:
    """Split normalised IPA into phones, reading affricates as one sound."""

    text = normalise_ipa(ipa)
    out: list[str] = []
    index = 0
    while index < len(text):
        for digraph in _DIGRAPHS:
            if text.startswith(digraph, index):
                out.append(digraph)
                index += len(digraph)
                break
        else:
            out.append(text[index])
            index += 1
    return tuple(out)


def _manner_cost(left: str, right: str) -> float:
    if left == right:
        return 0.0
    return 1.0 - MANNER_NEARNESS.get(frozenset({left, right}), 0.0)


def phone_distance(left: str, right: str) -> float:
    """How far apart two phones are, in [0, 1]."""

    if left == right:
        return 0.0
    left_consonant, right_consonant = CONSONANTS.get(left), CONSONANTS.get(right)
    left_vowel, right_vowel = VOWELS.get(left), VOWELS.get(right)

    if left_consonant and right_consonant:
        manner_left, place_left, voiced_left = left_consonant
        manner_right, place_right, voiced_right = right_consonant
        place = abs(PLACES[place_left] - PLACES[place_right]) / _PLACE_SPAN
        manner = _manner_cost(manner_left, manner_right)
        voice = 0.0 if voiced_left == voiced_right else 1.0
        # Voicing is the cheapest single difference a consonant can carry, so
        # its weight must sit below the cost of the smallest place step
        # (0.50 / 10 x 3 = 0.15 for p/t). A test pins that ordering.
        return min(1.0, 0.50 * place + 0.40 * manner + 0.10 * voice)

    if left_vowel and right_vowel:
        height_left, back_left, round_left = left_vowel
        height_right, back_right, round_right = right_vowel
        height = abs(height_left - height_right) / _HEIGHT_SPAN
        back = abs(back_left - back_right) / _BACK_SPAN
        rounded = 0.0 if round_left == round_right else 1.0
        return min(1.0, 0.50 * height + 0.30 * back + 0.20 * rounded)

    # A consonant against a vowel, or a symbol not in the tables. Unknown is
    # treated as maximally different rather than as a free match, so a gap in
    # the inventory can never manufacture similarity.
    return 1.0


def _weighted_distance(left: Sequence[str], right: Sequence[str]) -> float:
    """Levenshtein where substitution costs what the two phones differ by."""

    if not left:
        return float(len(right))
    if not right:
        return float(len(left))
    previous = [float(index) for index in range(len(right) + 1)]
    for row, phone_left in enumerate(left, 1):
        current = [float(row)]
        for column, phone_right in enumerate(right, 1):
            current.append(
                min(
                    previous[column] + 1.0,
                    current[column - 1] + 1.0,
                    previous[column - 1] + phone_distance(phone_left, phone_right),
                )
            )
        previous = current
    return previous[-1]


def phonetic_similarity(left: str, right: str) -> float:
    """1.0 for the same pronunciation, and a floor rather than 0.0 for nothing.

    Feature-weighted substitution gives partial credit on every pair of phones,
    so two unrelated words of similar shape land around 0.3-0.4 rather than at
    zero. That is inherent to scoring sounds by how they are made, and it is
    harmless here for two reasons: the floor sits far below any pair's cutoff,
    and the form axis takes the *best* of its three readings, so a phonetic
    score can only ever raise a pair that spelling already judged — never
    lower one.
    """

    left_phones, right_phones = segments(left), segments(right)
    if not left_phones or not right_phones:
        return 0.0
    longest = max(len(left_phones), len(right_phones))
    return max(0.0, 1.0 - _weighted_distance(left_phones, right_phones) / longest)


def best_pronunciation_similarity(
    left_forms: Iterable[str],
    right_forms: Iterable[str],
) -> float:
    """The closest any recorded pronunciation of one is to any of the other.

    A word may be recorded with several pronunciations — regional, or simply
    two transcriptions of the same thing. Taking the best is the same choice
    the orthographic axis makes between raw and skeleton spelling: the question
    is whether the learner *could* recognise it, not whether every variant is
    equally close.
    """

    rights = [right for right in right_forms if right]
    if not rights:
        return 0.0
    best = 0.0
    for left in left_forms:
        if not left:
            continue
        for right in rights:
            score = phonetic_similarity(left, right)
            if score > best:
                best = score
                if best >= 1.0:
                    return best
    return best
