"""Decide how SPECIFIC an answer to emit, rather than whether to emit one.

This is the only genuinely new idea in the v6 method, and it exists because of a
measured dead end: every attempt to decide *better* failed, and every attempt to
decide *offline which errors are harmless* failed for the same reason — whether a
mistake matters depends on the sentence, not on the pair of senses. Declining to
over-claim is the one move that is always available and never wrong.

A system that must always emit a leaf turns every uncertainty into a wrong card.
A system that can emit less turns it into a vaguer one:

    confident throughout       ->  leaf       "está — is (location)"
    unsure which context       ->  glosskey   "está — is"
    unsure which gloss too     ->  tuple      "estar — to be"
    unsure of the word itself  ->  unresolved / escalate / redraw

The three levels are a lattice over the same selection, not different answers.
The selected sense never changes; only how much of it is published does.

## Why escalation keys on the tuple alone

Being torn between two synonyms is not worth a model call — once the answer is
published at glosskey level the learner never sees the difference. Being unsure
which *word* this is always is worth one, because that is the error a learner
does notice.

The two axes also want different remedies, and picking the wrong one does
nothing at all:

    gloss uncertain  ->  emit less        rejection does not help here; leaf
                                          accuracy is flat across the whole
                                          rejection curve
    tuple uncertain  ->  reject & redraw  this is what rejection actually buys
                                          (tuple accuracy 82% -> 98% at 50%
                                          rejection), and it is free wherever the
                                          corpus is harvestable
                     ->  escalate         where it is not: a user's fixed corpus
                                          cannot supply another sentence

`decide` reports which axis is weak and leaves the remedy to the caller, because
the remedy is a property of the corpus, not of the algorithm.

## Calibration status

The thresholds are UNMEASURED and default to zero, which means "always emit a
leaf" — exactly the behaviour of the stage this replaces. The gloss backoff has
been validated in the reference repository (backing off 28% of a hard panel
lifted glosskey precision from 78% to 85%); the tuple trigger has NOT — the tuple
margin proved non-monotonic against tuple correctness, confounded by
single-analysis items whose errors are inventory gaps rather than choice errors.
Method agreement is the measured alternative and is not implemented here.

Do not enable `tuple_minimum` on the strength of the margin alone.
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
import math
from typing import Literal, Mapping, Sequence

from fluency.wsd.gloss_scoring import LeafScore
from fluency.wsd.menus import MenuAnalysis, require_analysis


EmitLevel = Literal["leaf", "glosskey", "tuple", "unresolved"]
UncertainAxis = Literal["none", "gloss", "tuple"]
UnresolvedOutcome = Literal["assign", "abstain"]
CrossAnalysisVote = Literal["provider_order", "gloss_margin"]
CrossAnalysisOutcome = Literal["order_agrees", "clear", "shared_translation", "contested"]

EMIT_LEVELS: tuple[EmitLevel, ...] = ("leaf", "glosskey", "tuple", "unresolved")


@dataclass(frozen=True, slots=True)
class CommitPolicy:
    """How much of the forced selection may be published.

    ``margin`` preserves the original v7 behavior. ``rank_agreement`` publishes
    only the deepest level shared by the dictionary-order choice and the raw
    sentence/gloss choice. It has no fitted threshold and never changes the
    forced selection.

    ``phrase_winner_skips_provider_order`` is the v14 exception: a PHRASE is
    not a dictionary-menu leaf, so provider order cannot license it. When the
    combined winner is a multiword analysis, agreement is raw gloss versus
    forced selection only. Word-leaf commit is unchanged.

    ``unresolved_falls_back_to_phrase`` is the other v14 exception. v13 abstain
    was built for a word menu: unresolved meant publish nothing. With phrases
    on the menu, an unlicensed word must not discard a competing PHRASE.

    ``cross_analysis_vote`` says what may overrule the gloss BETWEEN analyses
    (different headword or part of speech). ``provider_order`` is the v9-v15
    rule: the first-listed leaf of the whole menu votes, so a gloss winner in
    any other analysis is unresolved. That order carries no information across
    analyses -- Wiktionary's is alphabetical (ten before ty, name before noun)
    and SpanishDict's is page order (ser before saber) -- and it cost cs 99.7%
    of its abstentions. ``gloss_margin`` keeps dictionary order as a vote only
    inside the gloss winner's analysis, and between analyses asks the gloss to
    win by ``cross_analysis_margin`` (raw scores, no menu prior). A rival within
    the margin that renders the same English commits at glosskey (vy/ty "you").
    Order can no longer veto the gloss, but it still confirms it: any line the
    ``provider_order`` rule would publish is published exactly as it would
    be, so only lines that rule abstains on can change. (A margin on every
    line made es more cautious, not less: que CCONJ/PRON and querer/quererse
    are split entries of one word that order used to settle, and 3,255 es
    lines v15 published through a shared English gloss met a third entry
    inside the margin.)
    """

    leaf_minimum: float = 0.0
    glosskey_minimum: float = 0.0
    tuple_minimum: float = 0.0
    temperature: float = 0.02
    strategy: Literal["margin", "rank_agreement"] = "margin"
    evidence_guards: bool = False
    unresolved_outcome: UnresolvedOutcome = "assign"
    shared_translation_licenses_glosskey: bool = False
    phrase_winner_skips_provider_order: bool = False
    unresolved_falls_back_to_phrase: bool = False
    cross_analysis_vote: CrossAnalysisVote = "provider_order"
    cross_analysis_margin: float = 0.0
    # A contested cross-analysis line abstains even where unresolved lines are
    # otherwise assigned. fi assigns unresolved lines (its dictionary-POS
    # guard fires on correct menus: entä conj tagged ADV), but a close call
    # between entries published et as "and".
    contested_abstains: bool = False

    def __post_init__(self) -> None:
        for name, value in (
            ("leaf_minimum", self.leaf_minimum),
            ("glosskey_minimum", self.glosskey_minimum),
            ("tuple_minimum", self.tuple_minimum),
        ):
            if not 0.0 <= value <= 1.0:
                raise ValueError(f"{name} must be a margin between zero and one")
        if self.temperature <= 0:
            raise ValueError("temperature must be positive")
        if self.strategy not in {"margin", "rank_agreement"}:
            raise ValueError("unsupported commit strategy")
        if self.unresolved_outcome not in {"assign", "abstain"}:
            raise ValueError("unsupported unresolved outcome")
        if self.cross_analysis_vote not in {"provider_order", "gloss_margin"}:
            raise ValueError("unsupported cross-analysis vote")
        if not 0.0 <= self.cross_analysis_margin <= 1.0:
            raise ValueError("cross_analysis_margin must be between zero and one")

    @property
    def enabled(self) -> bool:
        return self.strategy != "margin" or any(
            value > 0
            for value in (self.leaf_minimum, self.glosskey_minimum, self.tuple_minimum)
        )


@dataclass(frozen=True, slots=True)
class CommitDecision:
    level: EmitLevel
    uncertain_axis: UncertainAxis
    margins: Mapping[str, float]
    escalate: bool
    cross_analysis: CrossAnalysisOutcome | None = None


def cross_analysis_license(
    raw_scores: Sequence[LeafScore],
    analyses: Sequence[MenuAnalysis],
    winner: tuple[str, str],
    margin: float,
) -> CrossAnalysisOutcome:
    """Does the gloss winner's analysis beat every other analysis by ``margin``?

    Scores are raw gloss scores, so no menu-order prior can decide it. A rival
    inside the margin whose English matches the winner's is no contest for a
    learner, so it licenses the shared rendering rather than blocking it.
    """

    winner_analysis_id, winner_sense_id = winner
    winner_analysis = require_analysis(analyses, winner_analysis_id)

    def translation(analysis_id: str, sense_id: str) -> str:
        sense = require_analysis(analyses, analysis_id).sense(sense_id)
        return (sense.translation or "").casefold().strip()

    own = [item.score for item in raw_scores if item.menu_analysis_id == winner_analysis_id]
    if not own:
        return "clear"
    best_own = max(own)
    rivals = [
        item for item in raw_scores
        if item.menu_analysis_id != winner_analysis_id and item.score > best_own - margin
    ]
    if not rivals:
        return "clear"
    shared = translation(winner_analysis.menu_analysis_id, winner_sense_id)
    if shared and all(
        translation(item.menu_analysis_id, item.sense_id) == shared for item in rivals
    ):
        return "shared_translation"
    return "contested"


def _probabilities(scores: Sequence[LeafScore], temperature: float) -> dict[tuple[str, str], float]:
    top = max(item.score for item in scores)
    weights = {
        (item.menu_analysis_id, item.sense_id): math.exp((item.score - top) / temperature)
        for item in scores
    }
    total = sum(weights.values()) or 1.0
    return {key: value / total for key, value in weights.items()}


def _margin(distribution: Mapping[object, float]) -> float:
    if not distribution:
        return 0.0
    ordered = sorted(distribution.values(), reverse=True)
    return ordered[0] - (ordered[1] if len(ordered) > 1 else 0.0)


def axis_margins(
    scores: Sequence[LeafScore],
    analyses: Sequence[MenuAnalysis],
    *,
    temperature: float = 0.02,
) -> dict[str, float]:
    """Top-two margin on each of the three axes.

    Aggregation is MAX, never sum. Max over per-key maxima reproduces the global
    argmax exactly, so these margins add confidence without moving any pick. Sum
    pools mass across leaves sharing a key and is a largest-analysis prior in
    disguise: it scored +8 items on a panel stratified toward large analyses, +1
    on an unstratified one, and -8 on a uniform-over-senses dictionary panel.
    """

    if not scores:
        return {"leaf": 0.0, "glosskey": 0.0, "tuple": 0.0}
    probabilities = _probabilities(scores, temperature)
    leaf: dict[tuple[str, str], float] = {}
    glosskey: dict[tuple[str, str, str], float] = defaultdict(float)
    tuples: dict[tuple[str, str], float] = defaultdict(float)
    for item in scores:
        key = (item.menu_analysis_id, item.sense_id)
        probability = probabilities[key]
        leaf[key] = max(leaf.get(key, 0.0), probability)
        analysis = require_analysis(analyses, item.menu_analysis_id)
        sense = analysis.sense(item.sense_id)
        gloss_key = (
            analysis.part_of_speech,
            sense.translation or "<EMPTY>",
            analysis.headword.casefold(),
        )
        tuple_key = (analysis.part_of_speech, analysis.headword.casefold())
        glosskey[gloss_key] = max(glosskey[gloss_key], probability)
        tuples[tuple_key] = max(tuples[tuple_key], probability)
    return {
        "leaf": _margin(leaf),
        "glosskey": _margin(glosskey),
        "tuple": _margin(tuples),
    }


def decide(
    scores: Sequence[LeafScore],
    analyses: Sequence[MenuAnalysis],
    policy: CommitPolicy,
    *,
    rank_agreement_refs: Sequence[tuple[str, str]] = (),
    raw_scores: Sequence[LeafScore] = (),
    menu_first: tuple[str, str] | None = None,
) -> CommitDecision:
    """Most specific level the scores support, plus which axis is weak.

    ``raw_scores`` feeds the ``gloss_margin`` cross-analysis vote; the caller
    passes it empty where that vote does not apply (a PHRASE winner).
    """

    margins = axis_margins(scores, analyses, temperature=policy.temperature)
    if policy.strategy == "rank_agreement":
        if len(rank_agreement_refs) < 2:
            raise ValueError("rank-agreement commit requires at least two choices")
        if policy.cross_analysis_vote == "gloss_margin" and raw_scores:
            # Whatever the provider-order rule would publish, publish unchanged:
            # v21 only rescues lines that rule abstains on.
            if menu_first is not None and len(rank_agreement_refs) == 3:
                ordered = _rank_agreement_level(
                    analyses, policy, (menu_first, *rank_agreement_refs[1:]), margins
                )
                if ordered.level != "unresolved":
                    return CommitDecision(
                        ordered.level, ordered.uncertain_axis, margins, ordered.escalate,
                        "order_agrees",
                    )
            decision = _rank_agreement_level(analyses, policy, rank_agreement_refs, margins)
            if decision.level == "unresolved":
                return decision
            outcome = cross_analysis_license(
                raw_scores, analyses, tuple(rank_agreement_refs[1]),
                policy.cross_analysis_margin,
            )
            if outcome == "contested":
                return CommitDecision("unresolved", "tuple", margins, True, outcome)
            if outcome == "shared_translation" and decision.level == "leaf":
                return CommitDecision("glosskey", "gloss", margins, False, outcome)
            return CommitDecision(
                decision.level, decision.uncertain_axis, margins, decision.escalate, outcome
            )
        return _rank_agreement_level(analyses, policy, rank_agreement_refs, margins)
    if margins["tuple"] < policy.tuple_minimum:
        return CommitDecision(
            level="unresolved", uncertain_axis="tuple", margins=margins, escalate=True
        )
    if margins["glosskey"] < policy.glosskey_minimum:
        return CommitDecision(
            level="tuple", uncertain_axis="gloss", margins=margins, escalate=False
        )
    if margins["leaf"] < policy.leaf_minimum:
        return CommitDecision(
            level="glosskey", uncertain_axis="gloss", margins=margins, escalate=False
        )
    return CommitDecision(
        level="leaf", uncertain_axis="none", margins=margins, escalate=False
    )


def _rank_agreement_level(
    analyses: Sequence[MenuAnalysis],
    policy: CommitPolicy,
    rank_agreement_refs: Sequence[tuple[str, str]],
    margins: Mapping[str, float],
) -> CommitDecision:
    """Deepest level every cheap choice shares."""

    leaves = []
    glosskeys = []
    tuples = []
    translations = []
    for menu_analysis_id, sense_id in rank_agreement_refs:
        analysis = require_analysis(analyses, menu_analysis_id)
        sense = analysis.sense(sense_id)
        leaves.append((menu_analysis_id, sense_id))
        glosskeys.append(
            (
                analysis.part_of_speech,
                analysis.headword.casefold(),
                sense.translation or "<EMPTY>",
            )
        )
        tuples.append((analysis.part_of_speech, analysis.headword.casefold()))
        translations.append((sense.translation or "").casefold().strip())
    if len(set(leaves)) == 1:
        return CommitDecision("leaf", "none", margins, False)
    if len(set(glosskeys)) == 1:
        return CommitDecision("glosskey", "gloss", margins, False)
    if len(set(tuples)) == 1:
        return CommitDecision("tuple", "gloss", margins, False)
    if (
        policy.shared_translation_licenses_glosskey
        and translations
        and all(translations)
        and len(set(translations)) == 1
    ):
        return CommitDecision("glosskey", "gloss", margins, False)
    return CommitDecision("unresolved", "tuple", margins, True)


def published_fields(level: EmitLevel, analysis: MenuAnalysis, sense_id: str) -> dict[str, object]:
    """What a card may show at this level. The selection itself never changes."""

    leaf = analysis.sense(sense_id)
    if level == "unresolved":
        return {}
    if level == "tuple":
        return {"headword": analysis.headword, "part_of_speech": analysis.part_of_speech}
    payload: dict[str, object] = {
        "headword": analysis.headword,
        "part_of_speech": analysis.part_of_speech,
        "translation": leaf.translation,
    }
    if level == "leaf":
        payload["definition"] = leaf.definition
    return payload
