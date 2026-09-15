"""Bound how many occurrences per surface card ever reach expensive WSD.

Harvesting deliberately keeps every eligible occurrence, because an occurrence
that was never recorded cannot later be reconsidered. Disambiguation is the
opposite: a card needs a handful of good examples, so running contextual
embeddings over every occurrence of a common word buys nothing and costs
proportionally to how frequent the word is — the frequent words, which are the
ones with the most occurrences and the least need for more of them.

A provisional lyrics run made this concrete: 463 executions across 162 cards,
45 of them for `arriba` alone. The mature pipeline bounded this per word, and
this restores that principle explicitly rather than as a side effect.

## What this is not

It is NOT the study-example cap. That decides how many examples a learner
finally sees and is applied much later, after assignment, from the assignments
that succeeded. This one decides how many occurrences are worth *asking about*.
Collapsing the two would make the number of examples a card can show depend on
how many occurrences happened to be disambiguated, which is backwards.

## Every occurrence still gets an outcome

An occurrence above the cap is reported as ``not_evaluated_example_cap``. It is
not dropped and it is never described as sense-assigned. The distinction the
auditor has to preserve is between "no model looked at this" and "a model looked
and could not decide", because they mean opposite things about the inventory.

## Deterministic by construction

Selection ranks by the harvest score already computed upstream and breaks ties
on sentence ID, so the same run re-executed selects the same occurrences without
storing a seed. The policy, the cap, the ranking signal and the selected IDs all
go into the run record.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import AbstractSet, Any, Iterable, Mapping, Sequence


SAMPLING_POLICY_VERSION = "wsd-occurrence-sampling/v1"

# The mature historical default. Configurable, but changing it changes what a
# run costs and what its coverage means, so it is recorded per run.
DEFAULT_EXECUTION_CAP = 10


@dataclass(frozen=True, slots=True)
class OccurrenceSamplingPolicy:
    cap_per_surface: int = DEFAULT_EXECUTION_CAP
    # Ascending: a LOWER harvest score is an easier, better example. The label
    # previously said "desc" while the code sorted ascending -- the behaviour was
    # right and the provenance was wrong, which is the worse of the two failures
    # because it cannot be detected from the output.
    ranking_signal: str = "harvest_score_asc_easiest_first_then_sentence_id"

    def __post_init__(self) -> None:
        if self.cap_per_surface < 1:
            raise ValueError("the WSD execution cap must admit at least one occurrence")

    def to_dict(self) -> dict[str, Any]:
        return {
            "policy_version": SAMPLING_POLICY_VERSION,
            "cap_per_surface": self.cap_per_surface,
            "ranking_signal": self.ranking_signal,
            "overflow_outcome": "not_evaluated_example_cap",
            "note": "separate from the later study-example cap",
        }


@dataclass(frozen=True, slots=True)
class SurfaceSelection:
    card_id: str
    selected: tuple[str, ...]
    overflow: tuple[str, ...]

    @property
    def considered(self) -> int:
        return len(self.selected) + len(self.overflow)


ALIGNMENT_BAND = 0.05
MIN_LENGTH_RATIO = 0.35
MAX_LENGTH_RATIO = 2.80


def is_admissible_candidate(item: Mapping[str, Any]) -> bool:
    """Sanity checks: exact full token and reasonable length ratio."""
    metrics = item.get("metrics") or {}
    if metrics.get("surface_position") is None and "surface_position" in metrics:
        return False
    ratio = metrics.get("translation_length_ratio")
    if ratio is not None:
        if ratio < MIN_LENGTH_RATIO or ratio > MAX_LENGTH_RATIO:
            return False
    return True


def order_candidates_for_wsd(
    items: Sequence[Mapping[str, Any]],
    *,
    alignment_band: float = ALIGNMENT_BAND,
    min_candidates_floor: int = 10,
) -> list[Mapping[str, Any]]:
    """Deterministically order candidates for WSD evaluation.

    1. Filter out candidate tail anomalies (missing token position, extreme length ratios).
       If filtered candidates < min_candidates_floor, fall back to admitting all eligible.
    2. Sort by alignment band descending (0.05 bins), then difficulty ascending, then sentence_id.
    """
    eligible = [i for i in items if i.get("eligible", True)]
    admissible = [i for i in eligible if is_admissible_candidate(i)]
    pool = (
        admissible
        if len(admissible) >= min_candidates_floor or len(admissible) >= len(eligible)
        else eligible
    )

    def get_band(i: Mapping[str, Any]) -> int:
        tags = i.get("tags") or {}
        align = tags.get("alignment") or 0.0
        return int(round(float(align) / alignment_band))

    def get_difficulty(i: Mapping[str, Any]) -> float:
        metrics = i.get("metrics") or {}
        if "difficulty" in metrics and metrics["difficulty"] is not None:
            return float(metrics["difficulty"])
        score = float(metrics.get("score") or 0.0)
        penalty = float(metrics.get("grammar_penalty") or 0.0)
        return round(score + penalty, 6)

    return sorted(
        pool,
        key=lambda i: (
            -get_band(i),
            get_difficulty(i),
            str(i.get("sentence_id") or ""),
        ),
    )


def _rank_key(candidate: Mapping[str, Any]) -> tuple[float, str]:
    metrics = candidate.get("metrics") or {}
    score = metrics.get("difficulty") if metrics.get("difficulty") is not None else metrics.get("score")
    # Lower harvest score/difficulty means an easier, better example.
    ordered = float(score) if isinstance(score, (int, float)) else float("inf")
    return (ordered, str(candidate.get("sentence_id") or ""))


def select_occurrences(
    candidates: Sequence[Mapping[str, Any]],
    policy: OccurrenceSamplingPolicy,
    *,
    card_id: str,
    ineligible: AbstractSet[str] | None = None,
    preferred_order: Sequence[str] | None = None,
) -> SurfaceSelection:
    """Deterministically choose which occurrences reach WSD for one card.

    `ineligible` names sentences the conditioning step ruled out at the end of
    harvesting -- a translation that failed the alignment floor, say. The
    verdict is read, never re-derived here: WSD judges senses and nothing else.
    They are dropped before the cap rather than ranked below it, because
    embedding one spends a model call on a pair that must not be displayed
    whatever WSD says about it. Supply absorbs the loss: the Portuguese harvest
    holds 40 eligible candidates a card against the 10 a card shows. They are
    reported as overflow, which is already the channel for "harvested, not
    evaluated".

    `preferred_order` names the exact sentence order supplied by the surface
    ledger -- taking alignment bands ahead of raw score, and passing an empty
    sequence for excluded surfaces so their sentences are entirely withheld.
    """

    if preferred_order is not None:
        candidates_by_id = {str(item["sentence_id"]): item for item in candidates}
        eligible_items = [
            candidates_by_id[sid]
            for sid in preferred_order
            if sid in candidates_by_id and (not ineligible or sid not in ineligible)
        ]
        chosen = eligible_items[: policy.cap_per_surface]
        chosen_ids = {str(item["sentence_id"]) for item in chosen}
        # Every occurrence not chosen is reported as overflow to maintain complete accounting
        rest = [item for item in candidates if str(item["sentence_id"]) not in chosen_ids]
        return SurfaceSelection(
            card_id=card_id,
            selected=tuple(str(item["sentence_id"]) for item in chosen),
            overflow=tuple(str(item["sentence_id"]) for item in rest),
        )

    ordered = order_candidates_for_wsd(candidates)
    if ineligible:
        eligible = [item for item in ordered if str(item["sentence_id"]) not in ineligible]
        rejected = [item for item in ordered if str(item["sentence_id"]) in ineligible]
    else:
        eligible, rejected = list(ordered), []
    chosen = eligible[: policy.cap_per_surface]
    chosen_ids = {str(item["sentence_id"]) for item in chosen}
    rest = [item for item in candidates if str(item["sentence_id"]) not in chosen_ids]
    return SurfaceSelection(
        card_id=card_id,
        selected=tuple(str(item["sentence_id"]) for item in chosen),
        overflow=tuple(str(item["sentence_id"]) for item in rest),
    )


def sampling_report(selections: Iterable[SurfaceSelection], policy: OccurrenceSamplingPolicy) -> dict[str, Any]:
    selections = list(selections)
    selected = sum(len(item.selected) for item in selections)
    overflow = sum(len(item.overflow) for item in selections)
    capped_cards = sum(1 for item in selections if item.overflow)
    return {
        "policy": policy.to_dict(),
        "surface_cards": len(selections),
        "occurrences_considered": selected + overflow,
        "occurrences_selected": selected,
        "occurrences_not_evaluated": overflow,
        "surface_cards_reaching_cap": capped_cards,
    }


def sole_leaf(analyses: Sequence[Any]) -> tuple[Any, Any] | None:
    """The single (analysis, leaf) pair when the closed menu offers no choice.

    A one-sense menu is not disambiguation and must not consume a model call or
    be reported as though something was decided. Returns None whenever a genuine
    choice exists.
    """

    total = sum(len(analysis.senses) for analysis in analyses)
    if total != 1:
        return None
    analysis = next(item for item in analyses if item.senses)
    return analysis, analysis.senses[0]
