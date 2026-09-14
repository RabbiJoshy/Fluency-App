"""Corpus-first masked-substitute WSI feasibility probe.

This experiment reads only source-language sentences at inference time.  It
clusters masked-LM substitute distributions, then maps each cluster to the
closed dictionary menu using source-language dictionary examples.  Cluster
stability and mapping collisions are first-class outputs: a visually plausible
partition is not evidence that it represents reusable senses.
"""

from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import json
import math
from pathlib import Path
import random
import re
from typing import Any, Iterable, Mapping, Sequence

import numpy as np
from sklearn.cluster import KMeans
from sklearn.metrics import adjusted_rand_score, silhouette_score

from .contrastive_probe import (
    Fingerprint,
    _candidate_order,
    _collect_panel_spans,
    _collect_source_spans,
    _panel,
)
from .profiles import CandidateSense, Meaning, deaccent, group_meanings, load_menu, write_jsonl


def _corpus_text(record: Mapping[str, Any]) -> str:
    if isinstance(record.get("es"), str):
        return str(record["es"])
    target = record.get("target")
    return str(target.get("text") or "") if isinstance(target, Mapping) else ""


def _corpus_title(record: Mapping[str, Any]) -> str:
    provenance = record.get("provenance")
    if isinstance(provenance, Mapping):
        return str(provenance.get("title_id") or record.get("id") or "")
    source = record.get("source")
    if isinstance(source, Mapping):
        document = source.get("document")
        if isinstance(document, Mapping):
            return str(document.get("title_id") or record.get("sentence_id") or "")
    return str(record.get("id") or record.get("sentence_id") or "")


def _corpus_id(record: Mapping[str, Any]) -> str:
    return str(record.get("id") or record.get("sentence_id") or "")


def _sample_corpus(
    path: Path,
    surfaces: Sequence[str],
    *,
    per_surface: int,
) -> tuple[dict[str, list[Fingerprint]], dict[Fingerprint, dict[str, Any]]]:
    patterns = {
        surface: re.compile(rf"(?<!\w){re.escape(surface)}(?!\w)", re.IGNORECASE)
        for surface in surfaces
    }
    rng = random.Random(55109)
    reservoirs: dict[str, list[Fingerprint]] = {surface: [] for surface in surfaces}
    seen_titles: dict[str, set[str]] = {surface: set() for surface in surfaces}
    eligible = Counter()
    metadata: dict[Fingerprint, dict[str, Any]] = {}

    with path.open(encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            record = json.loads(line)
            sentence = _corpus_text(record)
            if not sentence:
                continue
            title = _corpus_title(record)
            for surface, pattern in patterns.items():
                match = pattern.search(sentence)
                if match is None or title in seen_titles[surface]:
                    continue
                seen_titles[surface].add(title)
                eligible[surface] += 1
                fingerprint = (sentence, match.start(), match.end())
                row = {
                    "kind": "corpus",
                    "surface_form": surface,
                    "sentence_id": _corpus_id(record),
                    "title_id": title,
                }
                if len(reservoirs[surface]) < per_surface:
                    reservoirs[surface].append(fingerprint)
                    metadata[fingerprint] = row
                else:
                    index = rng.randrange(eligible[surface])
                    if index < per_surface:
                        reservoirs[surface][index] = fingerprint
                        metadata[fingerprint] = row
    return reservoirs, metadata


def _substitute_distributions(
    fingerprints: Iterable[Fingerprint],
    *,
    model_name: str,
    device: str,
    batch_size: int,
    top_k: int,
    max_length: int = 96,
) -> dict[Fingerprint, dict[str, float]]:
    import torch
    from transformers import AutoModelForMaskedLM, AutoTokenizer

    fingerprints = list(fingerprints)
    tokenizer_options = (
        {"fix_mistral_regex": True}
        if model_name == "bert-base-multilingual-cased"
        else {}
    )
    tokenizer = AutoTokenizer.from_pretrained(
        model_name, local_files_only=True, **tokenizer_options
    )
    model = AutoModelForMaskedLM.from_pretrained(model_name, local_files_only=True)
    model.eval().to(device)
    masked = [
        sentence[:start] + tokenizer.mask_token + sentence[end:]
        for sentence, start, end in fingerprints
    ]
    output: dict[Fingerprint, dict[str, float]] = {}
    with torch.no_grad():
        for start in range(0, len(masked), batch_size):
            chunk = masked[start : start + batch_size]
            encoded = tokenizer(
                chunk,
                return_tensors="pt",
                padding=True,
                truncation=True,
                max_length=max_length,
            )
            mask_positions = encoded["input_ids"].eq(tokenizer.mask_token_id)
            encoded = {key: value.to(device) for key, value in encoded.items()}
            logits = model(**encoded).logits.cpu()
            for offset, text in enumerate(chunk):
                positions = mask_positions[offset].nonzero(as_tuple=False).flatten()
                fingerprint = fingerprints[start + offset]
                if len(positions) != 1:
                    continue
                row = logits[offset, int(positions[0])]
                values, indices = row.topk(min(top_k * 3, row.shape[0]))
                original = deaccent(fingerprint[0][fingerprint[1] : fingerprint[2]])
                kept_tokens: list[str] = []
                kept_logits: list[float] = []
                for value, index in zip(values.tolist(), indices.tolist(), strict=True):
                    token = tokenizer.convert_ids_to_tokens(int(index))
                    if (
                        not token
                        or token.startswith("##")
                        or token in tokenizer.all_special_tokens
                        or deaccent(token) == original
                        or re.search(r"[^\W\d_]", token, re.UNICODE) is None
                    ):
                        continue
                    kept_tokens.append(token)
                    kept_logits.append(float(value))
                    if len(kept_tokens) >= top_k:
                        break
                if not kept_tokens:
                    continue
                probabilities = np.exp(
                    np.asarray(kept_logits, dtype=np.float64) - max(kept_logits)
                )
                probabilities /= probabilities.sum()
                output[fingerprint] = {
                    token: float(probability)
                    for token, probability in zip(
                        kept_tokens, probabilities.tolist(), strict=True
                    )
                }
    return output


def _matrix(
    fingerprints: Sequence[Fingerprint],
    distributions: Mapping[Fingerprint, Mapping[str, float]],
    vocabulary: Sequence[str],
) -> np.ndarray:
    index = {token: position for position, token in enumerate(vocabulary)}
    matrix = np.zeros((len(fingerprints), len(vocabulary)), dtype=np.float32)
    for row, fingerprint in enumerate(fingerprints):
        for token, value in distributions.get(fingerprint, {}).items():
            if token in index:
                matrix[row, index[token]] = value
    norms = np.linalg.norm(matrix, axis=1, keepdims=True)
    norms[norms == 0] = 1.0
    return matrix / norms


def _cluster_runs(matrix: np.ndarray) -> tuple[list[dict[str, Any]], KMeans]:
    candidates: list[tuple[float, int, dict[str, Any], KMeans]] = []
    maximum = min(6, len(matrix) - 1)
    for clusters in range(2, maximum + 1):
        models = [
            KMeans(n_clusters=clusters, n_init=20, random_state=seed).fit(matrix)
            for seed in range(5)
        ]
        reference = models[0]
        if len(set(reference.labels_.tolist())) < 2:
            continue
        counts = Counter(reference.labels_.tolist())
        silhouette = float(silhouette_score(matrix, reference.labels_, metric="cosine"))
        stability = float(
            np.mean(
                [
                    adjusted_rand_score(reference.labels_, model.labels_)
                    for model in models[1:]
                ]
            )
        )
        row = {
            "clusters": clusters,
            "silhouette_cosine": silhouette,
            "seed_stability_ari": stability,
            "smallest_cluster_fraction": min(counts.values()) / len(matrix),
            "cluster_sizes": [counts[index] for index in range(clusters)],
        }
        candidates.append((silhouette, -clusters, row, reference))
    if not candidates:
        raise RuntimeError("substitute matrix has no non-degenerate clustering")
    best = max(candidates, key=lambda item: (item[0], item[1]))
    return [item[2] for item in candidates], best[3]


def _meaning_fingerprints(
    surface: str,
    cards: Mapping[str, Sequence[CandidateSense]],
    by_sense: Mapping[tuple[str, str], Sequence[Fingerprint]],
) -> dict[Meaning, tuple[Fingerprint, ...]]:
    result: dict[Meaning, tuple[Fingerprint, ...]] = {}
    for meaning, candidates in group_meanings(cards.get(surface, ())).items():
        values = tuple(
            dict.fromkeys(
                fingerprint
                for candidate in candidates
                for fingerprint in by_sense.get((surface, candidate.sense_id), ())
            )
        )
        if values:
            result[meaning] = values
    return result


def _normalized_mean(matrix: np.ndarray) -> np.ndarray:
    vector = matrix.mean(axis=0)
    norm = float(np.linalg.norm(vector))
    return vector / norm if norm else vector


def run(args: argparse.Namespace) -> dict[str, Any]:
    import spacy

    panel = _panel(args.panel) if args.panel else []
    if args.surfaces == "@panel":
        surfaces = tuple(
            dict.fromkeys(
                str(item["word"])
                for item in panel
                if not item.get("no_answer")
            )
        )
    else:
        surfaces = tuple(
            dict.fromkeys(
                value.strip() for value in args.surfaces.split(",") if value.strip()
            )
        )
    cards = load_menu(args.menu)
    missing = [surface for surface in surfaces if surface not in cards]
    if missing:
        raise ValueError(f"surfaces missing from menu: {missing}")
    nlp = spacy.load(args.span_model)
    by_sense, source_fingerprints, source_span_status = _collect_source_spans(
        cards, surfaces, nlp=nlp
    )
    corpus_by_surface, corpus_metadata = _sample_corpus(
        args.corpus, surfaces, per_surface=args.occurrences
    )

    panel = [item for item in panel if str(item["word"]) in surfaces]
    panel_spans, panel_span_status = (
        _collect_panel_spans(panel, nlp=nlp) if panel else ({}, {})
    )
    candidate_order = (
        _candidate_order(args.candidate_predictions)
        if args.candidate_predictions
        else {}
    )
    all_fingerprints = (
        source_fingerprints
        | {value for values in corpus_by_surface.values() for value in values}
        | set(panel_spans.values())
    )
    distributions = _substitute_distributions(
        all_fingerprints,
        model_name=args.encoder,
        device=args.device,
        batch_size=args.batch_size,
        top_k=args.top_k,
    )

    surface_reports: dict[str, Any] = {}
    panel_predictions: list[dict[str, Any]] = []
    audit_rows: list[dict[str, Any]] = []
    for surface in surfaces:
        corpus_fingerprints = [
            fingerprint
            for fingerprint in corpus_by_surface[surface]
            if fingerprint in distributions
        ]
        meaning_fingerprints = _meaning_fingerprints(surface, cards, by_sense)
        source_rows = [
            fingerprint
            for fingerprints in meaning_fingerprints.values()
            for fingerprint in fingerprints
            if fingerprint in distributions
        ]
        panel_items = [item for item in panel if str(item["word"]) == surface]
        panel_rows = [
            panel_spans[item["id"]]
            for item in panel_items
            if item["id"] in panel_spans and panel_spans[item["id"]] in distributions
        ]
        vocabulary = sorted(
            {
                token
                for fingerprint in corpus_fingerprints + source_rows + panel_rows
                for token in distributions[fingerprint]
            }
        )
        if len(corpus_fingerprints) < 10 or not vocabulary:
            surface_reports[surface] = {
                "status": "insufficient_corpus_support",
                "corpus_occurrences": len(corpus_fingerprints),
            }
            continue

        corpus_matrix = _matrix(corpus_fingerprints, distributions, vocabulary)
        cluster_metrics, best_model = _cluster_runs(corpus_matrix)
        centroids = best_model.cluster_centers_.astype(np.float32)
        centroid_norms = np.linalg.norm(centroids, axis=1, keepdims=True)
        centroid_norms[centroid_norms == 0] = 1.0
        centroids /= centroid_norms

        sense_prototypes: dict[Meaning, np.ndarray] = {}
        for meaning, fingerprints in meaning_fingerprints.items():
            usable = [value for value in fingerprints if value in distributions]
            if usable:
                sense_prototypes[meaning] = _normalized_mean(
                    _matrix(usable, distributions, vocabulary)
                )
        mappings: list[Meaning | None] = []
        mapping_margins: list[float] = []
        for centroid in centroids:
            ranked = sorted(
                (
                    (float(centroid @ prototype), meaning)
                    for meaning, prototype in sense_prototypes.items()
                ),
                reverse=True,
            )
            mappings.append(ranked[0][1] if ranked else None)
            mapping_margins.append(
                ranked[0][0] - ranked[1][0] if len(ranked) > 1 else 0.0
            )

        one_centroid = _normalized_mean(corpus_matrix)
        one_mapping = max(
            sense_prototypes,
            key=lambda meaning: float(one_centroid @ sense_prototypes[meaning]),
            default=None,
        )
        surface_reports[surface] = {
            "status": "ok",
            "corpus_occurrences": len(corpus_fingerprints),
            "dictionary_meanings": len(meaning_fingerprints),
            "dictionary_meanings_with_substitute_profile": len(sense_prototypes),
            "cluster_metrics": cluster_metrics,
            "best_cluster_metrics": next(
                row
                for row in cluster_metrics
                if row["clusters"] == best_model.n_clusters
            ),
            "selected_clusters": best_model.n_clusters,
            "cluster_menu_mappings": [list(value) if value else None for value in mappings],
            "unique_mapped_meanings": len(set(value for value in mappings if value)),
            "mapping_uniqueness_ratio": (
                len(set(value for value in mappings if value)) / len(mappings)
            ),
            "mapping_margins": mapping_margins,
            "one_cluster_mapping": list(one_mapping) if one_mapping else None,
        }

        for fingerprint, label in zip(corpus_fingerprints, best_model.labels_, strict=True):
            audit_rows.append(
                {
                    **corpus_metadata[fingerprint],
                    "cluster": int(label),
                    "mapped_meaning": list(mappings[int(label)]) if mappings[int(label)] else None,
                    "top_substitutes": sorted(
                        distributions[fingerprint].items(),
                        key=lambda item: item[1],
                        reverse=True,
                    )[:12],
                    "sentence": fingerprint[0],
                }
            )

        for item in panel_items:
            fingerprint = panel_spans.get(item["id"])
            if fingerprint not in distributions:
                continue
            candidates = candidate_order.get(item["id"], tuple(sense_prototypes))
            query = _matrix([fingerprint], distributions, vocabulary)[0]
            available = [meaning for meaning in candidates if meaning in sense_prototypes]
            direct = max(
                available,
                key=lambda meaning: float(query @ sense_prototypes[meaning]),
                default=candidates[0],
            )
            cluster = int(np.argmax(centroids @ query))
            clustered = mappings[cluster]
            if clustered not in candidates:
                clustered = candidates[0]
            one = one_mapping if one_mapping in candidates else candidates[0]
            acceptable = {tuple(value) for value in item["acceptable"]}
            selected = {
                "prior_pos": candidates[0],
                "direct_substitute": direct,
                "one_cluster": one,
                "wsi_cluster": clustered,
            }
            panel_predictions.append(
                {
                    "id": item["id"],
                    "cls": item["cls"],
                    "word": surface,
                    "sentence": item["sentence"],
                    "acceptable": item["acceptable"],
                    "selected": {key: list(value) for key, value in selected.items()},
                    "correct": {key: value in acceptable for key, value in selected.items()},
                    "cluster": cluster,
                    "top_substitutes": sorted(
                        distributions[fingerprint].items(),
                        key=lambda value: value[1],
                        reverse=True,
                    )[:12],
                }
            )

    panel_summary: dict[str, Any] = {}
    if panel_predictions:
        for method in ("prior_pos", "direct_substitute", "one_cluster", "wsi_cluster"):
            correct = sum(row["correct"][method] for row in panel_predictions)
            baseline = sum(row["correct"]["prior_pos"] for row in panel_predictions)
            panel_summary[method] = {
                "n": len(panel_predictions),
                "correct": correct,
                "accuracy": correct / len(panel_predictions),
                "delta_correct_vs_prior_pos": correct - baseline,
            }

    report = {
        "schema": "wsd-v9-substitution-wsi/v1",
        "language": args.language,
        "menu": str(args.menu),
        "corpus": str(args.corpus),
        "surfaces": list(surfaces),
        "encoder": args.encoder,
        "runtime_inputs": "source sentence and target span only",
        "aligned_english_used": False,
        "mapping_source": "source-language dictionary examples",
        "source_span_status": source_span_status,
        "panel_span_status": panel_span_status,
        "substitute_distributions": len(distributions),
        "surface_reports": surface_reports,
        "panel_subset": panel_summary,
    }
    args.output_dir.mkdir(parents=True, exist_ok=True)
    (args.output_dir / "report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    )
    write_jsonl(args.output_dir / "cluster-audit.jsonl", audit_rows)
    if panel_predictions:
        write_jsonl(args.output_dir / "panel-predictions.jsonl", panel_predictions)
    return report


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--language", required=True)
    parser.add_argument("--menu", type=Path, required=True)
    parser.add_argument("--corpus", type=Path, required=True)
    parser.add_argument("--surfaces", required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--panel", type=Path)
    parser.add_argument("--candidate-predictions", type=Path)
    parser.add_argument("--span-model", required=True)
    parser.add_argument("--encoder", required=True)
    parser.add_argument("--device", default="cpu")
    parser.add_argument("--batch-size", type=int, default=32)
    parser.add_argument("--top-k", type=int, default=64)
    parser.add_argument("--occurrences", type=int, default=100)
    args = parser.parse_args()
    if bool(args.panel) != bool(args.candidate_predictions):
        parser.error("--panel and --candidate-predictions must be supplied together")
    report = run(args)
    print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
