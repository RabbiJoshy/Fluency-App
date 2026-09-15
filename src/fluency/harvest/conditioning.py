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
    # Frequency burden scores the words; this scores the grammar, which the
    # words alone do not reveal: six common words in the imperfect subjunctive
    # score as easy as the present tense.
    #
    # Added as its own columns rather than folded into `score`. The harvest's
    # score keeps meaning exactly what it meant, and a downstream consumer
    # chooses whether to spend the grammar signal -- which is the point of
    # putting it in the ledger rather than acting on it here.
    penalty, constructions = grammar_load(text, language)
    metrics = {
        **metrics,
        "grammar_penalty": penalty,
        "difficulty": round(score + penalty, 6),
    }
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
            "grammar": list(constructions),
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


# --- grammatical difficulty -------------------------------------------------
#
# Frequency burden asks whether a learner knows the *words*. It says nothing
# about whether they can read the *grammar*, so a sentence of six common words
# in the imperfect subjunctive scores as easy as one in the present tense. That
# is wrong for the first few hundred cards, where the grammar is the obstacle.
#
# These are deliberately narrow. A wide net here costs good sentences, and the
# ambiguous endings are the tempting ones: Spanish `-ara`/`-iera` are imperfect
# subjunctive but also ordinary nouns (`cara`, `manera`, `espera`), and
# Portuguese `-ara`/`-era` are pluperfect but also `para`, `era`. Those are
# omitted rather than guessed at. Missing a hard sentence costs a little;
# penalising `cara` costs a lot, on every card that uses it.

_GRAMMAR: dict[str, tuple[tuple[str, "re.Pattern[str]", float], ...]] = {
    "es": (
        # Unambiguous imperfect-subjunctive endings, plus the irregular stems
        # that carry most of its real use.
        ("imperfect_subjunctive", re.compile(
            r"\b\w{3,}(?:ase|ese|iese|ásemos|ésemos|iésemos|aseis|eseis|ieseis|asen|esen|iesen)\b"
            r"|\b(?:hubiera|hubiese|hubieran|hubiesen|fuera|fuese|fueran|fuesen|tuviera|tuviese"
            r"|estuviera|estuviese|pudiera|pudiese|quisiera|quisiese|hiciera|hiciese|dijera"
            r"|dijese|viniera|viniese|supiera|supiese)\b", re.I), 1.2),
        ("conditional_perfect", re.compile(
            r"\b(?:habría|habrías|habríamos|habrían|habríais)\b", re.I), 1.0),
        # Peninsular second-person plural. Correct Spanish, but absent from
        # Latin American input and an extra paradigm a beginner does not need.
        ("vosotros", re.compile(
            r"\bvosotros\b|\b\w{3,}(?:áis|éis)\b|\bos\s+\w+(?:áis|éis|ad|ed|id)\b", re.I), 0.8),
        # The stem must carry a written accent, which an enclitic verb always
        # does and an ordinary noun does not. Without it `caramelos`,
        # `pasteles` and `carteles` all parse as stem + two clitics.
        ("stacked_clitics", re.compile(
            r"\b\w*[áéíóú]\w*(?:me|te|se|nos|os)(?:lo|la|los|las|le|les)\b", re.I), 0.9),
    ),
    "pt": (
        ("imperfect_subjunctive", re.compile(
            r"\b\w{3,}(?:asse|esse|isse|ássemos|êssemos|íssemos|assem|essem|issem"
            r"|asses|esses|isses)\b", re.I), 1.2),
        # Mesoclisis: the pronoun inside the verb. Rare, and very hard.
        ("mesoclisis", re.compile(
            r"\b\w{2,}-(?:me|te|lhe|lhes|nos|vos|o|a|os|as)-(?:ei|ás|á|emos|eis|ão|ia|ias|íamos|iam)\b",
            re.I), 1.5),
        ("conditional_perfect", re.compile(
            r"\b(?:teria|terias|teríamos|teriam|haveria|haveriam)\b", re.I), 1.0),
        # European second person singular, absent from Brazilian input.
        # Only the unambiguous endings. `-ares`, `-eres`, `-ires` and `-estes`
        # are future subjunctive, but far more often ordinary plurals --
        # `dolares`, `mulheres`, `lugares`, `milhares`, `estes`.
        ("tu_conjugation", re.compile(
            r"\b\w{3,}(?:sses|astes|istes)\b", re.I), 0.7),
    ),
    "cs": (
        # Conditional auxiliaries. Unambiguous closed class.
        ("conditional", re.compile(
            r"\b(?:bych|bys|bychom|byste|abych|abys|abychom|abyste|kdybych|kdybys"
            r"|kdybychom|kdybyste)\b", re.I), 1.0),
        # `-án`, `-ána` and `-ěna` are dropped: kapitán, oceán, odměna.
        ("passive_participle", re.compile(
            r"\b\w{3,}(?:áno|ěno|ováno|ována|ěn|eni|ěni)\b", re.I), 0.8),
    ),
}


def grammar_load(text: str, language: str) -> tuple[float, tuple[str, ...]]:
    """Extra difficulty from grammar the words alone do not reveal.

    Returns the penalty and the constructions found, so a card can be audited
    on why a sentence was judged hard rather than only on the number.
    """

    found: list[str] = []
    penalty = 0.0
    for name, pattern, weight in _GRAMMAR.get(language, ()):
        if pattern.search(text):
            found.append(name)
            penalty += weight
    return round(penalty, 6), tuple(found)
