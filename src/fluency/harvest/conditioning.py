"""Turn a raw harvest into conditioned, tagged pools.

The harvest gathers; it does not judge beyond the form rules it applies while
scanning. Everything after that -- alignment, variety, hardness -- used to be
decided inside the WSD step, which meant WSD was doing three jobs and the
reasons for its choices were not written down anywhere a later stage could
read.

This layer sits between them. It reads a harvest and writes one pool per card
in which every candidate carries its tags and an explicit verdict. WSD then
disambiguates and nothing else, and selection can prefer or avoid a tag without
re-deriving it.

Rejected candidates stay in the pool with a reason rather than being deleted.
A floor is a judgement that may be revised; a deletion is not revisable, and
the reason a sentence is absent is exactly what is wanted when a card comes up
short.
"""

from __future__ import annotations

import re
from typing import Any, Mapping, Sequence

POOL_VERSION = "conditioned-pool/v1"

# --- variety -------------------------------------------------------------
# European Portuguese says "estar a + infinitive" where Brazilian says
# "estar + gerund"; the two also differ in everyday lexis and in the
# consonants the 1990 orthographic agreement made optional. Measured on the
# Portuguese bank (375,598 sentences): Tatoeba is 17.4% Brazilian against 2.6%
# European, OpenSubtitles 14.8% European against 8.5% Brazilian. For a European
# deck Tatoeba is the source that pulls the wrong way, which is the reverse of
# what its alignment quality suggests. 76% of sentences signal neither.
_BRAZILIAN = (
    (re.compile(r"\b(est(ou|á|ás|amos|ão|ava|ivemos)|t(ô|o))\s+\w+ndo\b", re.I), "gerund_progressive"),
    (re.compile(r"\b(ônibus|trem|celular|banheiro|geladeira|sorvete|bonde|xícara|aeromoça|grampo)\b", re.I), "brazilian_lexis"),
    (re.compile(r"\ba\s+gente\s+\w+", re.I), "a_gente"),
    (re.compile(r"\b(ato|ação|adoção|batizar|anistia|úmido|registro)\b", re.I), "brazilian_orthography"),
)
_EUROPEAN = (
    (re.compile(r"\b(est(ou|á|ás|amos|ão|ava)|and(o|a|amos))\s+a\s+\w+(ar|er|ir)\b", re.I), "estar_a_infinitive"),
    (re.compile(r"\b(autocarro|comboio|telemóvel|casa\s+de\s+banho|frigorífico|chávena|relva|equipa|peúga|miúd[oa]s?|fixe|puto|rapariga)\b", re.I), "european_lexis"),
    (re.compile(r"\b(facto|acto|acção|adopção|baptizar|amnistia|húmido|registo)\b", re.I), "european_orthography"),
    (re.compile(r"\w+-(te|me|lhe|nos|lo|la|los|las)\b", re.I), "enclisis"),
)


# The patterns below are Portuguese. Run against Spanish they match ordinary
# grammar -- "estoy haciendo" is not Brazilian, it is how Spanish forms the
# progressive -- so the tag is only meaningful for the language it describes.
_VARIETY_LANGUAGES = {"pt"}


def variety(text: str, language: str = "pt") -> tuple[str, tuple[str, ...]]:
    """Which side of the Atlantic a Portuguese sentence sounds like, and why.

    Returns "not_applicable" for any other language rather than a tag derived
    from patterns that do not describe it.

    "fato" is deliberately in neither list: it is a suit in Lisbon and a fact
    in Sao Paulo, so it says nothing on its own.
    """
    if language not in _VARIETY_LANGUAGES:
        return "not_applicable", ()
    brazilian = tuple(name for pattern, name in _BRAZILIAN if pattern.search(text))
    european = tuple(name for pattern, name in _EUROPEAN if pattern.search(text))
    if brazilian and european:
        return "mixed", european + brazilian
    if brazilian:
        return "brazilian", brazilian
    if european:
        return "european", european
    return "neutral", ()


# --- hardness ------------------------------------------------------------
# The harvest already computes an easiness score; banding it makes the number
# usable as a filter without anyone having to know its scale.
def hardness_band(score: float) -> str:
    if score <= 0.5:
        return "easy"
    if score <= 2.0:
        return "moderate"
    return "hard"


def length_band(tokens: int) -> str:
    if tokens < 5:
        return "short"
    if tokens <= 14:
        return "comfortable"
    return "long"


def condition_candidate(
    candidate: Mapping[str, Any],
    *,
    text: str,
    source: str,
    alignment: float | None,
    alignment_floor: float,
    language: str = "pt",
) -> dict[str, Any]:
    metrics = candidate.get("metrics") or {}
    score = float(metrics.get("score") or 0.0)
    kind, evidence = variety(text, language)
    # An unscored pair keeps its place: silence is not evidence of misalignment.
    rejected = (
        "below_alignment_floor"
        if alignment is not None and alignment < alignment_floor
        else None
    )
    return {
        "sentence_id": candidate["sentence_id"],
        "metrics": dict(metrics),
        "tags": {
            "source": source,
            "alignment": None if alignment is None else round(alignment, 6),
            "variety": kind,
            "variety_evidence": list(evidence),
            "hardness": hardness_band(score),
            "length": length_band(int(metrics.get("target_tokens") or 0)),
        },
        "eligible": rejected is None,
        "rejected_for": rejected,
    }


def pool_report(cards: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    from collections import Counter

    verdicts: Counter = Counter()
    varieties: Counter = Counter()
    eligible_per_card = []
    for card in cards:
        eligible = 0
        for item in card["candidates"]:
            verdicts[item["rejected_for"] or "eligible"] += 1
            varieties[item["tags"]["variety"]] += 1
            eligible += bool(item["eligible"])
        eligible_per_card.append(eligible)
    eligible_per_card.sort()
    return {
        "pool_version": POOL_VERSION,
        "cards": len(cards),
        "verdicts": dict(verdicts),
        "variety": dict(varieties),
        "eligible_per_card": {
            "mean": round(sum(eligible_per_card) / max(len(eligible_per_card), 1), 2),
            "min": eligible_per_card[0] if eligible_per_card else 0,
            "cards_under_10": sum(1 for n in eligible_per_card if n < 10),
            "cards_under_15": sum(1 for n in eligible_per_card if n < 15),
        },
    }
