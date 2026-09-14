"""Train a tiny sibling-contrastive metric over frozen BETO target vectors.

The encoder is the same compact Spanish model already used by the historical
prototype experiments.  Only a logistic pair scorer is learned.  Positives and
negatives come from source-language dictionary examples; hard negatives are
other meanings of the same surface.  A random-negative control tests whether
the learner merely recognizes the lemma instead of separating siblings.
"""

from __future__ import annotations

import argparse
from collections import defaultdict
from dataclasses import dataclass
import hashlib
import json
import math
from pathlib import Path
import random
from typing import Any, Iterable, Mapping, Sequence

import joblib
import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import GroupKFold
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

from .profiles import CandidateSense, Meaning, find_target_token, group_meanings, load_menu, write_jsonl


METHODS = ("cosine", "random_contrastive", "sibling_contrastive")
BLEND_WEIGHTS = (0.0, 0.125, 0.25, 0.5, 1.0, 2.0, 4.0, 8.0, 16.0)
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


Fingerprint = tuple[str, int, int]


@dataclass(frozen=True, slots=True)
class ScoredItem:
    item: Mapping[str, Any]
    candidates: tuple[Meaning, ...]
    components: Mapping[str, tuple[float, ...]]


def _panel(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def _candidate_order(path: Path) -> dict[str, tuple[Meaning, ...]]:
    rows = [json.loads(line) for line in path.read_text().splitlines() if line.strip()]
    ordered: dict[str, tuple[Meaning, ...]] = {}
    for row in rows:
        candidates = row["components"]["frame"]["candidates"]
        ordered[row["id"]] = tuple(tuple(value["meaning"]) for value in candidates)
    return ordered


def _collect_source_spans(
    cards: Mapping[str, Sequence[CandidateSense]],
    surfaces: Iterable[str],
    *,
    nlp: Any,
) -> tuple[
    dict[tuple[str, str], tuple[Fingerprint, ...]],
    set[Fingerprint],
    dict[str, int],
]:
    pending: list[tuple[CandidateSense, Any]] = []
    for surface in surfaces:
        for candidate in cards.get(surface, ()):
            pending.extend((candidate, example) for example in candidate.examples)

    by_sense: dict[tuple[str, str], list[Fingerprint]] = defaultdict(list)
    fingerprints: set[Fingerprint] = set()
    status = defaultdict(int)
    docs = nlp.pipe((example.text for _, example in pending), batch_size=128)
    for (candidate, example), doc in zip(pending, docs, strict=True):
        target = find_target_token(
            doc,
            surface_form=candidate.surface_form,
            headword=candidate.headword,
            target_start=example.target_start,
            target_end=example.target_end,
        )
        if target is None:
            status["target_not_located"] += 1
            continue
        fingerprint = (example.text, target.idx, target.idx + len(target.text))
        fingerprints.add(fingerprint)
        by_sense[(candidate.surface_form, candidate.sense_id)].append(fingerprint)
        status["located"] += 1
    return (
        {key: tuple(dict.fromkeys(values)) for key, values in by_sense.items()},
        fingerprints,
        dict(status),
    )


def _collect_panel_spans(
    panel: Sequence[Mapping[str, Any]], *, nlp: Any
) -> tuple[dict[str, Fingerprint], dict[str, int]]:
    found: dict[str, Fingerprint] = {}
    status = defaultdict(int)
    docs = nlp.pipe((str(item["sentence"]) for item in panel), batch_size=64)
    for item, doc in zip(panel, docs, strict=True):
        target = find_target_token(
            doc,
            surface_form=str(item["word"]),
            headword=str(item["word"]),
        )
        if target is None:
            status["target_not_located"] += 1
            continue
        found[str(item["id"])] = (
            str(item["sentence"]),
            target.idx,
            target.idx + len(target.text),
        )
        status["located"] += 1
    return found, dict(status)


def _encode_spans(
    fingerprints: Iterable[Fingerprint],
    *,
    model_name: str,
    device: str,
    batch_size: int,
    max_length: int = 96,
    layers: int = 4,
) -> dict[Fingerprint, np.ndarray]:
    import torch
    from transformers import AutoModel, AutoTokenizer

    grouped: dict[str, list[Fingerprint]] = defaultdict(list)
    for fingerprint in fingerprints:
        grouped[fingerprint[0]].append(fingerprint)
    sentences = list(grouped)

    tokenizer = AutoTokenizer.from_pretrained(model_name, local_files_only=True)
    model = AutoModel.from_pretrained(
        model_name,
        local_files_only=True,
        output_hidden_states=True,
    )
    model.eval().to(device)
    vectors: dict[Fingerprint, np.ndarray] = {}
    with torch.no_grad():
        for start in range(0, len(sentences), batch_size):
            chunk = sentences[start : start + batch_size]
            encoded = tokenizer(
                chunk,
                return_tensors="pt",
                padding=True,
                truncation=True,
                max_length=max_length,
                return_offsets_mapping=True,
            )
            offsets = encoded.pop("offset_mapping")
            encoded = {key: value.to(device) for key, value in encoded.items()}
            outputs = model(**encoded)
            hidden = torch.stack(outputs.hidden_states[-layers:]).mean(0).cpu().numpy()
            for batch_index, sentence in enumerate(chunk):
                token_offsets = offsets[batch_index].numpy()
                for fingerprint in grouped[sentence]:
                    _, char_start, char_end = fingerprint
                    selected = [
                        index
                        for index, (left, right) in enumerate(token_offsets)
                        if right > left and left < char_end and right > char_start
                    ]
                    if not selected:
                        continue
                    vector = hidden[batch_index][selected].mean(0).astype(np.float32)
                    norm = float(np.linalg.norm(vector))
                    if norm:
                        vectors[fingerprint] = vector / norm
    return vectors


def _meaning_vectors(
    cards: Mapping[str, Sequence[CandidateSense]],
    surfaces: Iterable[str],
    by_sense: Mapping[tuple[str, str], Sequence[Fingerprint]],
    vectors: Mapping[Fingerprint, np.ndarray],
) -> dict[tuple[str, Meaning], tuple[np.ndarray, ...]]:
    output: dict[tuple[str, Meaning], tuple[np.ndarray, ...]] = {}
    for surface in surfaces:
        for meaning, candidates in group_meanings(cards.get(surface, ())).items():
            fingerprints = dict.fromkeys(
                fingerprint
                for candidate in candidates
                for fingerprint in by_sense.get((surface, candidate.sense_id), ())
                if fingerprint in vectors
            )
            rows = tuple(vectors[fingerprint] for fingerprint in fingerprints)
            if rows:
                output[(surface, meaning)] = rows
    return output


def _prototype(rows: Sequence[np.ndarray]) -> np.ndarray:
    vector = np.mean(np.stack(rows), axis=0).astype(np.float32)
    norm = float(np.linalg.norm(vector))
    return vector / norm if norm else vector


def _pair_features(query: np.ndarray, prototype: np.ndarray) -> np.ndarray:
    return np.concatenate(
        (
            np.asarray([query @ prototype], dtype=np.float32),
            np.abs(query - prototype),
            query * prototype,
        )
    )


def _training_pairs(
    meaning_vectors: Mapping[tuple[str, Meaning], Sequence[np.ndarray]],
    *,
    negative_mode: str,
    negatives_per_positive: int = 4,
) -> tuple[np.ndarray, np.ndarray, dict[str, int]]:
    rng = random.Random(71451)
    prototypes = {key: _prototype(rows) for key, rows in meaning_vectors.items()}
    keys = list(prototypes)
    by_surface: dict[str, list[tuple[str, Meaning]]] = defaultdict(list)
    for key in keys:
        by_surface[key[0]].append(key)

    features: list[np.ndarray] = []
    labels: list[int] = []
    positives = negatives = 0
    for key, rows in meaning_vectors.items():
        if len(rows) < 2:
            continue
        surface = key[0]
        for query_index, query in enumerate(rows):
            positive_rows = [row for index, row in enumerate(rows) if index != query_index]
            positive = _prototype(positive_rows)
            features.append(_pair_features(query, positive))
            labels.append(1)
            positives += 1

            if negative_mode == "sibling":
                pool = [candidate for candidate in by_surface[surface] if candidate != key]
                pool.sort(key=lambda candidate: float(query @ prototypes[candidate]), reverse=True)
                chosen = pool[:negatives_per_positive]
            elif negative_mode == "random":
                pool = [candidate for candidate in keys if candidate[0] != surface]
                chosen = rng.sample(pool, min(negatives_per_positive, len(pool)))
            else:
                raise ValueError(negative_mode)
            for candidate in chosen:
                features.append(_pair_features(query, prototypes[candidate]))
                labels.append(0)
                negatives += 1
    if not positives or not negatives:
        raise RuntimeError(f"insufficient {negative_mode} training pairs")
    return (
        np.stack(features).astype(np.float32),
        np.asarray(labels, dtype=np.int8),
        {"positives": positives, "negatives": negatives},
    )


def _fit_pair_model(features: np.ndarray, labels: np.ndarray) -> Any:
    model = make_pipeline(
        StandardScaler(),
        LogisticRegression(
            C=0.25,
            class_weight="balanced",
            max_iter=300,
            random_state=90210,
            solver="lbfgs",
        ),
    )
    model.fit(features, labels)
    return model


def _normalize_scores(values: Sequence[float]) -> tuple[float, ...]:
    finite = [value for value in values if math.isfinite(value)]
    if not finite:
        return tuple(0.0 for _ in values)
    low, high = min(finite), max(finite)
    if high == low:
        return tuple(0.0 if math.isfinite(value) else -1.0 for value in values)
    return tuple(
        (value - low) / (high - low) if math.isfinite(value) else -1.0
        for value in values
    )


def _correct(item: Mapping[str, Any], meaning: Meaning) -> bool:
    return meaning in {tuple(value) for value in item["acceptable"]}


def _blend_pick(row: ScoredItem, method: str, weight: float) -> Meaning:
    index = max(
        range(len(row.candidates)),
        key=lambda candidate: (
            1.0 / (candidate + 1) + weight * row.components[method][candidate],
            -candidate,
        ),
    )
    return row.candidates[index]


def _component_winner(row: ScoredItem, method: str) -> tuple[Meaning, float]:
    ranked = sorted(
        enumerate(row.components[method]),
        key=lambda item: (item[1], -item[0]),
        reverse=True,
    )
    index, score = ranked[0]
    runner_up = ranked[1][1] if len(ranked) > 1 else 0.0
    return row.candidates[index], score - runner_up


def _selective_pick(row: ScoredItem, method: str, threshold: float) -> Meaning:
    selected, margin = _component_winner(row, method)
    return selected if margin >= threshold else row.candidates[0]


def _choose_blend(rows: Sequence[ScoredItem], method: str) -> float:
    options = []
    for weight in BLEND_WEIGHTS:
        correct = sum(_correct(row.item, _blend_pick(row, method, weight)) for row in rows)
        options.append((correct, -weight, weight))
    return max(options)[2]


def _choose_threshold(rows: Sequence[ScoredItem], method: str) -> float:
    options = []
    for threshold in SELECTIVE_THRESHOLDS:
        selected = [_selective_pick(row, method, threshold) for row in rows]
        correct = sum(
            _correct(row.item, meaning) for row, meaning in zip(rows, selected, strict=True)
        )
        changes = sum(
            meaning != row.candidates[0]
            for row, meaning in zip(rows, selected, strict=True)
        )
        options.append((correct, -changes, threshold))
    return max(options)[2]


def _bootstrap_delta(
    predictions: Sequence[Mapping[str, Any]], method: str, samples: int = 10_000
) -> dict[str, float]:
    rng = random.Random(77411)
    pairs = [
        (int(row["correct"][method]), int(row["correct"]["prior_pos"]))
        for row in predictions
    ]
    deltas = []
    for _ in range(samples):
        sample = [pairs[rng.randrange(len(pairs))] for _ in pairs]
        deltas.append(sum(left - right for left, right in sample) / len(sample))
    deltas.sort()
    return {
        "delta": sum(left - right for left, right in pairs) / len(pairs),
        "ci95_low": deltas[int(samples * 0.025)],
        "ci95_high": deltas[int(samples * 0.975)],
    }


def _results(predictions: Sequence[Mapping[str, Any]], method: str) -> dict[str, Any]:
    output: dict[str, Any] = {}
    for cls in ("AUX", "REFL", "POLY", "ALL"):
        rows = [row for row in predictions if cls == "ALL" or row["cls"] == cls]
        correct = sum(row["correct"][method] for row in rows)
        output[cls] = {
            "n": len(rows),
            "correct": correct,
            "accuracy": correct / len(rows) if rows else 0.0,
        }
    return output


def run(args: argparse.Namespace) -> dict[str, Any]:
    import spacy

    panel = _panel(args.panel)
    candidate_order = _candidate_order(args.candidate_predictions)
    cards = load_menu(args.menu)
    surfaces = sorted({str(item["word"]) for item in panel})
    nlp = spacy.load(args.span_model)

    by_sense, source_fingerprints, source_span_status = _collect_source_spans(
        cards, surfaces, nlp=nlp
    )
    panel_spans, panel_span_status = _collect_panel_spans(panel, nlp=nlp)
    all_fingerprints = source_fingerprints | set(panel_spans.values())
    vectors = _encode_spans(
        all_fingerprints,
        model_name=args.encoder,
        device=args.device,
        batch_size=args.batch_size,
    )
    meaning_vectors = _meaning_vectors(cards, surfaces, by_sense, vectors)
    prototypes = {key: _prototype(rows) for key, rows in meaning_vectors.items()}

    training: dict[str, Any] = {}
    models: dict[str, Any] = {}
    for mode in ("random", "sibling"):
        features, labels, counts = _training_pairs(
            meaning_vectors, negative_mode=mode
        )
        models[mode] = _fit_pair_model(features, labels)
        counts.update(
            {
                "rows": len(labels),
                "dimensions": features.shape[1],
                "training_accuracy": float(models[mode].score(features, labels)),
            }
        )
        training[mode] = counts

    rows: list[ScoredItem] = []
    coverage = defaultdict(int)
    for item in panel:
        if item.get("no_answer") or item["id"] not in candidate_order:
            continue
        fingerprint = panel_spans.get(str(item["id"]))
        query = vectors.get(fingerprint) if fingerprint is not None else None
        if query is None:
            coverage["query_vector_missing"] += 1
            continue
        candidates = candidate_order[str(item["id"])]
        raw: dict[str, list[float]] = {method: [] for method in METHODS}
        for meaning in candidates:
            prototype = prototypes.get((str(item["word"]), meaning))
            if prototype is None:
                coverage["candidate_prototype_missing"] += 1
                for method in METHODS:
                    raw[method].append(float("-inf"))
                continue
            pair = _pair_features(query, prototype).reshape(1, -1)
            raw["cosine"].append(float(query @ prototype))
            raw["random_contrastive"].append(
                float(models["random"].decision_function(pair)[0])
            )
            raw["sibling_contrastive"].append(
                float(models["sibling"].decision_function(pair)[0])
            )
        rows.append(
            ScoredItem(
                item=item,
                candidates=candidates,
                components={method: _normalize_scores(values) for method, values in raw.items()},
            )
        )
        coverage["scored"] += 1

    folds = GroupKFold(n_splits=5)
    groups = [str(row.item["word"]) for row in rows]
    predictions: list[dict[str, Any] | None] = [None] * len(rows)
    fold_weights: dict[str, list[float]] = defaultdict(list)
    fold_thresholds: dict[str, list[float | str]] = defaultdict(list)
    for train_indices, test_indices in folds.split(rows, groups=groups):
        training_rows = [rows[index] for index in train_indices]
        weights = {method: _choose_blend(training_rows, method) for method in METHODS}
        thresholds = {
            method: _choose_threshold(training_rows, method) for method in METHODS
        }
        for method in METHODS:
            fold_weights[method].append(weights[method])
            fold_thresholds[method].append(
                "no_change" if math.isinf(thresholds[method]) else thresholds[method]
            )
        for index in test_indices:
            row = rows[index]
            selected = {
                "prior_pos": row.candidates[0],
                **{
                    method: _blend_pick(row, method, weights[method])
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
                    key: _correct(row.item, meaning) for key, meaning in selected.items()
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
    scored_methods = ("prior_pos",) + METHODS + tuple(
        f"{method}_selective" for method in METHODS
    )
    report = {
        "schema": "wsd-v9-sibling-contrastive/v1",
        "panel": str(args.panel),
        "menu": str(args.menu),
        "encoder": args.encoder,
        "runtime_inputs": "source sentence, target span, closed dictionary menu",
        "aligned_english_used": False,
        "training_source": "source-language dictionary examples only",
        "source_span_status": source_span_status,
        "panel_span_status": panel_span_status,
        "encoded_fingerprints": len(vectors),
        "meaning_prototypes": len(prototypes),
        "training": training,
        "coverage": dict(coverage),
        "fold_weights": dict(fold_weights),
        "fold_selective_thresholds": dict(fold_thresholds),
        "results": {
            method: _results(final_predictions, method) for method in scored_methods
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
            for method in scored_methods
            if method != "prior_pos"
        },
        "historical_v7_target": {
            "accuracy": 0.784,
            "correct_of_199": 156,
        },
    }

    args.output_dir.mkdir(parents=True, exist_ok=True)
    write_jsonl(args.output_dir / "predictions.jsonl", final_predictions)
    (args.output_dir / "report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    )
    joblib.dump(models, args.output_dir / "pair-models.joblib")
    prototype_rows = sorted(prototypes.items(), key=lambda item: (item[0][0], item[0][1]))
    np.savez_compressed(
        args.output_dir / "sense-prototypes.npz",
        vectors=np.stack([value for _, value in prototype_rows]),
    )
    prototype_manifest = {
        "schema": "wsd-v9-source-only-prototypes/v1",
        "encoder": args.encoder,
        "menu_sha256": hashlib.sha256(args.menu.read_bytes()).hexdigest(),
        "rows": [
            {"index": index, "surface_form": key[0], "meaning": list(key[1])}
            for index, (key, _) in enumerate(prototype_rows)
        ],
    }
    (args.output_dir / "sense-prototypes.json").write_text(
        json.dumps(prototype_manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    )
    return report


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--panel", type=Path, required=True)
    parser.add_argument("--menu", type=Path, required=True)
    parser.add_argument("--candidate-predictions", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--span-model", default="es_core_news_lg")
    parser.add_argument("--encoder", default="dccuchile/bert-base-spanish-wwm-cased")
    parser.add_argument("--device", default="cpu")
    parser.add_argument("--batch-size", type=int, default=32)
    args = parser.parse_args()
    report = run(args)
    print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
