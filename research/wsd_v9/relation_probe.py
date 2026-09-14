"""Compare presence, frame, and target-anchored relation evidence on hard_200.

This is deliberately not a production scorer.  It learns no occurrence labels,
does not inspect aligned English, and does not alter the WSD runner.  Sense
profiles come only from the source-language examples already stored in the
dictionary menu.  The evidence/prior tradeoff is selected out-of-fold with all
occurrences of a surface kept in the same fold.
"""

from __future__ import annotations

import argparse
from collections import Counter, OrderedDict, defaultdict
from dataclasses import dataclass
import json
import math
from pathlib import Path
import random
from typing import Any, Callable, Mapping, Sequence

import numpy as np
from sklearn.model_selection import GroupKFold

from .profiles import (
    AnchoredFeatures,
    CandidateSense,
    Meaning,
    build_profiles,
    extract_anchored_features,
    feature_idf,
    find_target_token,
    group_meanings,
    load_menu,
    normalized_lexeme_vector,
    profile_index,
    slot_similarity,
    weighted_jaccard,
    write_jsonl,
)


POS_BRIDGE = {
    "DET": frozenset({"ADJ", "DET", "PRON"}),
    "PRON": frozenset({"PRON", "ADJ", "DET"}),
    "NUM": frozenset({"ADJ", "NOUN", "DET"}),
    "PART": frozenset({"ADV", "ADP", "PRON"}),
    "PROPN": frozenset({"PROPN", "NOUN"}),
    "ADV": frozenset({"ADV", "PRON", "ADJ"}),
    "AUX": frozenset({"VERB", "AUX", "PHRASE"}),
}
ORTHOGONAL_POS = frozenset({"PHRASE", "CONTRACTION"})
TRUSTED_POS = frozenset({"VERB", "NOUN", "ADJ", "ADV", "INTJ"})
EVIDENCE_WEIGHTS = (0.0, 0.125, 0.25, 0.5, 1.0, 2.0, 4.0, 8.0, 16.0)
METHODS = ("presence", "frame", "relation_exact", "relation_semantic")
SELECTIVE_THRESHOLDS = (
    0.0,
    0.01,
    0.02,
    0.03,
    0.05,
    0.075,
    0.10,
    0.125,
    0.15,
    0.175,
    0.20,
    0.225,
    0.25,
    0.275,
    0.30,
    0.35,
    0.40,
    0.50,
    math.inf,
)
SELECTIVE_METHODS = tuple(f"{method}_selective" for method in METHODS)


@dataclass(frozen=True, slots=True)
class ItemScores:
    item: Mapping[str, Any]
    candidates: tuple[Meaning, ...]
    components: Mapping[str, tuple[float, ...]]


def sense_compatible(sense_pos: str, observed_pos: str) -> bool:
    sense_pos = str(sense_pos or "").upper()
    observed_pos = str(observed_pos or "").upper()
    if sense_pos in ORTHOGONAL_POS:
        return True
    bridged = POS_BRIDGE.get(observed_pos)
    if bridged is not None:
        return sense_pos in bridged
    if sense_pos == observed_pos:
        return True
    if observed_pos in TRUSTED_POS:
        return False
    return sense_pos not in TRUSTED_POS


def _parse_panel(path: Path) -> list[dict[str, Any]]:
    return [
        json.loads(line)
        for line in path.read_text().splitlines()
        if line.strip()
    ]


def _meaning_rank(group: Sequence[CandidateSense]) -> int:
    return min(candidate.rank for candidate in group)


def _candidate_profiles(
    surface: str,
    group: Sequence[CandidateSense],
    index: Mapping[tuple[str, str], Sequence[AnchoredFeatures]],
) -> tuple[AnchoredFeatures, ...]:
    return tuple(
        profile
        for candidate in group
        for profile in index.get((surface, candidate.sense_id), ())
    )


def _max_profile_score(
    occurrence: AnchoredFeatures,
    profiles: Sequence[AnchoredFeatures],
    scorer: Callable[[AnchoredFeatures, AnchoredFeatures], float],
) -> float:
    return max((scorer(occurrence, profile) for profile in profiles), default=0.0)


def _pick(scores: ItemScores, method: str, evidence_weight: float) -> Meaning:
    components = scores.components[method]
    selected = max(
        range(len(scores.candidates)),
        key=lambda index: (
            1.0 / (index + 1) + evidence_weight * components[index],
            -index,
        ),
    )
    return scores.candidates[selected]


def _correct(item: Mapping[str, Any], meaning: Meaning) -> bool:
    return meaning in {tuple(value) for value in item["acceptable"]}


def _choose_weight(rows: Sequence[ItemScores], method: str) -> float:
    ranked = []
    for weight in EVIDENCE_WEIGHTS:
        correct = sum(_correct(row.item, _pick(row, method, weight)) for row in rows)
        ranked.append((correct, -weight, weight))
    return max(ranked)[2]


def _component_winner(scores: ItemScores, method: str) -> tuple[Meaning, float]:
    ranked = sorted(
        enumerate(scores.components[method]),
        key=lambda item: (item[1], -item[0]),
        reverse=True,
    )
    best_index, best_score = ranked[0]
    runner_up = ranked[1][1] if len(ranked) > 1 else 0.0
    return scores.candidates[best_index], best_score - runner_up


def _selective_pick(scores: ItemScores, method: str, threshold: float) -> Meaning:
    selected, margin = _component_winner(scores, method)
    if margin < threshold:
        return scores.candidates[0]
    return selected


def _choose_threshold(rows: Sequence[ItemScores], method: str) -> float:
    ranked = []
    for threshold in SELECTIVE_THRESHOLDS:
        selected = [_selective_pick(row, method, threshold) for row in rows]
        correct = sum(
            _correct(row.item, meaning) for row, meaning in zip(rows, selected, strict=True)
        )
        changes = sum(
            meaning != row.candidates[0]
            for row, meaning in zip(rows, selected, strict=True)
        )
        # Equal accuracy chooses the more conservative operating point.
        ranked.append((correct, -changes, threshold))
    return max(ranked)[2]


def _stratum_table(predictions: Sequence[Mapping[str, Any]], method: str) -> dict[str, Any]:
    table: dict[str, Any] = {}
    for cls in ("AUX", "REFL", "POLY", "ALL"):
        rows = [
            row
            for row in predictions
            if cls == "ALL" or row["cls"] == cls
        ]
        correct = sum(bool(row["correct"][method]) for row in rows)
        table[cls] = {
            "n": len(rows),
            "correct": correct,
            "accuracy": correct / len(rows) if rows else 0.0,
        }
    return table


def _bootstrap_delta(
    predictions: Sequence[Mapping[str, Any]], method: str, *, samples: int = 10_000
) -> dict[str, float]:
    rng = random.Random(90210)
    paired = [
        (int(row["correct"][method]), int(row["correct"]["prior_pos"]))
        for row in predictions
    ]
    deltas = []
    for _ in range(samples):
        sample = [paired[rng.randrange(len(paired))] for _ in paired]
        deltas.append(sum(left - right for left, right in sample) / len(sample))
    deltas.sort()
    return {
        "delta": sum(left - right for left, right in paired) / len(paired),
        "ci95_low": deltas[int(0.025 * samples)],
        "ci95_high": deltas[int(0.975 * samples)],
    }


def _build_item_scores(
    panel: Sequence[Mapping[str, Any]],
    cards: Mapping[str, Sequence[CandidateSense]],
    *,
    profile_records: Sequence[Any],
    relation_nlp: Any,
    pos_nlp: Any,
) -> tuple[list[ItemScores], dict[str, int]]:
    profiles = profile_index(profile_records)
    idfs = {
        family: feature_idf(profile_records, family)
        for family in ("presence", "frame", "relation")
    }
    vector_cache: dict[str, np.ndarray | None] = {}

    def vector_for(lemma: str) -> np.ndarray | None:
        if lemma not in vector_cache:
            vector_cache[lemma] = normalized_lexeme_vector(relation_nlp, lemma)
        return vector_cache[lemma]

    relation_docs = list(
        relation_nlp.pipe((str(item["sentence"]) for item in panel), batch_size=64)
    )
    pos_docs = list(pos_nlp.pipe((str(item["sentence"]) for item in panel), batch_size=32))
    rows: list[ItemScores] = []
    coverage = Counter()

    for item, relation_doc, pos_doc in zip(panel, relation_docs, pos_docs, strict=True):
        if item.get("no_answer"):
            coverage["no_answer"] += 1
            continue
        surface = str(item["word"])
        candidates = cards.get(surface, ())
        if not candidates:
            coverage["menu_missing"] += 1
            continue
        grouped = group_meanings(candidates)
        first_headword = candidates[0].headword
        occurrence_target = find_target_token(
            relation_doc,
            surface_form=surface,
            headword=first_headword,
        )
        pos_target = find_target_token(pos_doc, surface_form=surface, headword=first_headword)
        if occurrence_target is None:
            coverage["occurrence_target_not_located"] += 1
            continue
        occurrence = extract_anchored_features(relation_doc, occurrence_target)
        observed_pos = pos_target.pos_ if pos_target is not None else occurrence_target.pos_

        allowed = OrderedDict(
            (meaning, group)
            for meaning, group in grouped.items()
            if sense_compatible(meaning[0], observed_pos)
        )
        if not allowed:
            allowed = grouped
            coverage["pos_empty_fallback"] += 1

        ordered = sorted(allowed.items(), key=lambda entry: _meaning_rank(entry[1]))
        meanings = tuple(meaning for meaning, _ in ordered)
        component_rows: dict[str, list[float]] = {method: [] for method in METHODS}
        for _, group in ordered:
            candidates_profiles = _candidate_profiles(surface, group, profiles)
            if candidates_profiles:
                coverage["candidate_meanings_with_profile"] += 1
            component_rows["presence"].append(
                _max_profile_score(
                    occurrence,
                    candidates_profiles,
                    lambda left, right: weighted_jaccard(
                        left.presence, right.presence, idfs["presence"]
                    ),
                )
            )
            component_rows["frame"].append(
                _max_profile_score(
                    occurrence,
                    candidates_profiles,
                    lambda left, right: weighted_jaccard(
                        left.frame, right.frame, idfs["frame"]
                    ),
                )
            )
            component_rows["relation_exact"].append(
                _max_profile_score(
                    occurrence,
                    candidates_profiles,
                    lambda left, right: weighted_jaccard(
                        left.relation, right.relation, idfs["relation"]
                    ),
                )
            )
            component_rows["relation_semantic"].append(
                _max_profile_score(
                    occurrence,
                    candidates_profiles,
                    lambda left, right: (
                        0.20
                        * weighted_jaccard(left.frame, right.frame, idfs["frame"])
                        + 0.30
                        * weighted_jaccard(left.relation, right.relation, idfs["relation"])
                        + 0.50 * slot_similarity(left, right, vector_for=vector_for)
                    ),
                )
            )

        rows.append(
            ItemScores(
                item=item,
                candidates=meanings,
                components={key: tuple(value) for key, value in component_rows.items()},
            )
        )
        coverage["scored"] += 1
    return rows, dict(coverage)


def run(args: argparse.Namespace) -> dict[str, Any]:
    import spacy

    panel = _parse_panel(args.panel)
    cards = load_menu(args.menu)
    surfaces = sorted({str(item["word"]) for item in panel})

    relation_nlp = spacy.load(args.relation_model)
    profile_records = build_profiles(cards, nlp=relation_nlp, surfaces=surfaces)
    pos_nlp = relation_nlp if args.pos_model == args.relation_model else spacy.load(args.pos_model)
    item_scores, coverage = _build_item_scores(
        panel,
        cards,
        profile_records=profile_records,
        relation_nlp=relation_nlp,
        pos_nlp=pos_nlp,
    )

    if len(item_scores) < 5:
        raise RuntimeError(f"only {len(item_scores)} scorable panel items")
    folds = GroupKFold(n_splits=5)
    groups = [str(row.item["word"]) for row in item_scores]
    oof_weights: dict[str, list[float]] = defaultdict(list)
    oof_thresholds: dict[str, list[float | str]] = defaultdict(list)
    predictions: list[dict[str, Any] | None] = [None] * len(item_scores)

    for train_indices, test_indices in folds.split(item_scores, groups=groups):
        training = [item_scores[index] for index in train_indices]
        weights = {method: _choose_weight(training, method) for method in METHODS}
        thresholds = {
            method: _choose_threshold(training, method) for method in METHODS
        }
        for method, weight in weights.items():
            oof_weights[method].append(weight)
        for method, threshold in thresholds.items():
            oof_thresholds[method].append(
                "no_change" if math.isinf(threshold) else threshold
            )
        for index in test_indices:
            row = item_scores[index]
            selected = {
                "prior_pos": row.candidates[0],
                **{
                    method: _pick(row, method, weights[method])
                    for method in METHODS
                },
                **{
                    f"{method}_selective": _selective_pick(
                        row, method, thresholds[method]
                    )
                    for method in METHODS
                },
            }
            predictions[index] = {
                "id": row.item["id"],
                "cls": row.item["cls"],
                "word": row.item["word"],
                "sentence": row.item["sentence"],
                "acceptable": row.item["acceptable"],
                "selected": {key: list(value) for key, value in selected.items()},
                "correct": {
                    key: _correct(row.item, value) for key, value in selected.items()
                },
                "components": {
                    method: {
                        "winner_margin": _component_winner(row, method)[1],
                        "candidates": [
                            {"meaning": list(meaning), "score": score}
                            for meaning, score in zip(
                                row.candidates, row.components[method], strict=True
                            )
                        ],
                    }
                    for method in METHODS
                },
            }

    final_predictions = [row for row in predictions if row is not None]
    all_methods = ("prior_pos",) + METHODS + SELECTIVE_METHODS
    report: dict[str, Any] = {
        "schema": "wsd-v9-relation-probe/v1",
        "panel": str(args.panel),
        "menu": str(args.menu),
        "relation_model": args.relation_model,
        "pos_model": args.pos_model,
        "label_use": "evaluation and out-of-fold evidence-weight selection only",
        "runtime_inputs": "source sentence, target surface, closed dictionary menu",
        "aligned_english_used": False,
        "scored": len(final_predictions),
        "coverage": coverage,
        "fold_weights": dict(oof_weights),
        "fold_selective_thresholds": dict(oof_thresholds),
        "results": {
            method: _stratum_table(final_predictions, method)
            for method in all_methods
        },
        "paired_vs_prior_pos": {
            method: {
                **_bootstrap_delta(final_predictions, method),
                "fixes": sum(
                    row["correct"][method] and not row["correct"]["prior_pos"]
                    for row in final_predictions
                ),
                "breaks": sum(
                    not row["correct"][method] and row["correct"]["prior_pos"]
                    for row in final_predictions
                ),
            }
            for method in METHODS + SELECTIVE_METHODS
        },
        "historical_v7_target": {
            "accuracy": 0.784,
            "correct_of_199": 156,
            "note": "Recorded shipped-stack score; exact item predictions are unavailable here.",
        },
    }
    args.output_dir.mkdir(parents=True, exist_ok=True)
    write_jsonl(
        args.output_dir / "spanishdict-relation-profiles.jsonl",
        (record.to_json() for record in profile_records),
    )
    write_jsonl(args.output_dir / "predictions.jsonl", final_predictions)
    (args.output_dir / "report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    )
    return report


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--panel", type=Path, required=True)
    parser.add_argument("--menu", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--relation-model", default="es_core_news_lg")
    parser.add_argument("--pos-model", default="es_dep_news_trf")
    args = parser.parse_args()
    report = run(args)
    print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
