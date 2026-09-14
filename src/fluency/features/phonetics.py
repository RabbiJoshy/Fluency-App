"""How alike two words sound, from the IPA a dictionary already records.

The form axis was spelling alone: normalised edit distance, with an ordered
rewrite table per pair mapping two orthographies onto a shared alphabet. That
works, and it misses every correspondence nobody wrote down. Czech ``š`` and
Polish ``sz`` are different letters and the same sound; ``čas``/``czas`` differ
in two characters of three and not at all in speech.

Scoring is delegated to **panphon**, whose feature table covers 6,367 IPA
segments against the eighty a hand-written table here managed. The metric is
``dolgo_prime`` — Dolgopolsky sound classes, ten groups that collapse exactly
the correspondences cognates drift along, which is why it was devised for
cognate detection and why it beats a fine-grained feature distance at this job:

    metric              AUC     positives   negatives
    panphon dolgo      0.985        0.856       0.350
    hand-built table   0.986        0.817       0.384
    panphon hamming    0.959        0.881       0.566

AUC is nearly identical; what matters is what each ADDS, because the form axis
takes the best of its readings. Against ``max(orthography, skeleton)`` at a 0.80
cutoff, dolgo lifts recall 0.626 -> 0.768 where the hand table reached 0.717,
both at 0.998 precision or better.

What stays local is the notation handling: panphon wants sounds, and a
dictionary gives citation slashes, stress marks, tie bars and combining
diacritics. ``normalise_ipa`` strips those, and it is verified against panphon's
own segmenter — ``t͡ʃas`` and ``t͡ʂas`` both reduce to the class string ``TSVS``.

Coverage is what makes this practical: Wiktionary carries IPA for 98.3% of Czech
lemma entries and 99.3% of its inflected ones, so this works at the level cards
live at. It covers only 57.2% of one deck's surfaces, though, which is why this
is one tier of several rather than the answer.

Two things this deliberately does not do. It does not replace the orthographic
axis — the feature is about *reading* recognition, and ``central``/``central`` is
transparent on the page while being said quite differently. And it does not
model a listener: a learner reading a flashcard is not hearing it. Sound is
evidence *about* recognisability, taken alongside spelling rather than instead
of it.
"""

from __future__ import annotations

import re
import unicodedata
from typing import Iterable, Sequence


# Stress, length, syllable breaks, tone and the slashes or brackets a citation
# is wrapped in: notation about the sounds rather than the sounds themselves.
_IPA_NOTATION = re.compile(r"[/\[\]()ˈˌːˑ.\-‿|‖↗↘\s]")
# Tie bars join the halves of an affricate; the halves are what we read.
_TIE_BARS = str.maketrans("", "", "͜͡")

# Affricates written as two characters once the tie bar is gone. Listed longest
# first so ``t͡ʃ`` is read as one sound rather than as ``t`` + ``ʃ``.
_DIGRAPHS = ("ts", "dz", "tʃ", "dʒ", "tʂ", "dʐ", "tɕ", "dʑ")


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


_DISTANCE = None


def _distance():
    """panphon builds a 6,367-row feature table on construction, so build once."""

    global _DISTANCE
    if _DISTANCE is None:
        import panphon.distance

        _DISTANCE = panphon.distance.Distance()
    return _DISTANCE


def sound_classes(ipa: str) -> str:
    """The Dolgopolsky class string for a transcription, or "" if unreadable."""

    text = normalise_ipa(ipa)
    if not text:
        return ""
    try:
        return _distance().map_to_dolgo_prime(text)
    except Exception:
        # A transcription panphon cannot segment is unreadable, not similar.
        return ""


def phonetic_similarity(left: str, right: str) -> float:
    """1.0 for the same sound classes, 0.0 for nothing shared or nothing read.

    Absence returns 0.0 rather than raising: a word with no transcription has
    not been judged unrelated, and the caller combines this with max(), so a
    zero here withdraws the tier instead of arguing against the pair.
    """

    if not normalise_ipa(left) or not normalise_ipa(right):
        return 0.0
    try:
        distance = _distance().dolgo_prime_distance_div_maxlen(
            normalise_ipa(left), normalise_ipa(right)
        )
    except Exception:
        return 0.0
    return max(0.0, min(1.0, 1.0 - distance))


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
