"""Split the app examples monolith into per-study-set shards.

The learner studies 20 cards at a time. The live speech payload still ships
one 80 MB examples file, so opening any set parses the whole deck. Shards
let the app fetch the current set and greedily prefetch the next one.

The monolith remains in place as a fallback for older clients.

With ``slim=True`` each shard example keeps only what the app reads
(``slim_example``), and strings shared by a whole source (OPUS attribution,
licence, URL) move into the manifest once. The full records stay in the
monolith and ``deck.json``; ``expandSlimExample`` in app/js/vocab.js restores
the shape the app consumes. Measured on the Portuguese 30-example deck: 11x
smaller on disk, 2.7x smaller gzipped.
"""

from __future__ import annotations

import json
from pathlib import Path
from collections import Counter
from typing import Any


MANIFEST_VERSION = "example-shards/v1"
SLIM_MANIFEST_VERSION = "example-shards/v2"
SLIM_FORMAT = "slim-example/v1"
_EXAMPLE_PREFIX = "example_"
_SENTENCE_PREFIX = "sentence_"
_AGREE = "cheap_leaf_choices_agree"
# Every field a full example may carry, and whether the slim record keeps it.
# An unknown field fails the build rather than vanishing from the app.
_DROPPED_TOP = frozenset({"easiness", "metadata"})
_KEPT_TOP = frozenset({
    "target", "english", "source", "assignment_method", "example_id", "attribution",
    "license", "source_url", "sentence_url", "source_record_id", "contributor",
    "provenance", "source_title", "translation_source",
})
_KNOWN_METADATA = frozenset({
    "sentence_id", "source", "target", "translation", "wsd", "selection_metrics",
    "selection_policy", "source_title",
})
_SOURCE_DEFAULT_FIELDS = ("attribution", "license", "url")
SHARD_DIRECTORY = "vocabulary.examples.shards"
MANIFEST_NAME = "vocabulary.examples.manifest.json"


class ExampleShardError(ValueError):
    """Raised when examples cannot be split along the study structure."""


def _object(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ExampleShardError(f"JSON file must contain an object: {path}")
    return value


def _object_list(path: Path) -> list[Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, list):
        raise ExampleShardError(f"JSON file must contain a list: {path}")
    return value


def _json_bytes(value: object) -> bytes:
    return (json.dumps(value, ensure_ascii=False, separators=(",", ":")) + "\n").encode("utf-8")


def _source_defaults(examples: dict[str, Any]) -> dict[str, dict[str, str]]:
    """The commonest attribution, licence and URL of each source."""

    counts: dict[tuple[str, str], Counter[str]] = {}
    for card in examples.values():
        for group in card.get("m") or []:
            for example in group:
                source = str(example.get("source") or "")
                meta_source = (example.get("metadata") or {}).get("source") or {}
                for field in _SOURCE_DEFAULT_FIELDS:
                    value = example.get(field) if field != "url" else meta_source.get("url")
                    if isinstance(value, str) and value:
                        counts.setdefault((source, field), Counter())[value] += 1
    defaults: dict[str, dict[str, str]] = {}
    for (source, field), counter in counts.items():
        value, seen = counter.most_common(1)[0]
        if seen > 1:
            defaults.setdefault(source, {})[field] = value
    return defaults


def slim_example(example: dict[str, Any], defaults: dict[str, dict[str, str]]) -> dict[str, Any]:
    """Keep what the app reads, keyed short; see expandSlimExample in vocab.js."""

    unknown = set(example) - _KEPT_TOP - _DROPPED_TOP
    metadata = example.get("metadata") or {}
    unknown |= {f"metadata.{key}" for key in set(metadata) - _KNOWN_METADATA}
    if unknown:
        raise ExampleShardError(f"slim examples do not know how to carry: {sorted(unknown)}")
    source = str(example.get("source") or "")
    source_defaults = defaults.get(source, {})
    meta_source = metadata.get("source") or {}
    record: dict[str, Any] = {"t": example.get("target", ""), "e": example.get("english", ""), "s": source}
    if example.get("assignment_method", source) != source:
        record["a"] = example.get("assignment_method")
    for key, field, prefix in (("x", example.get("example_id"), _EXAMPLE_PREFIX),
                               ("i", metadata.get("sentence_id"), _SENTENCE_PREFIX)):
        if field:
            record[key] = field[len(prefix):] if field.startswith(prefix) else "=" + field
    for key, field in (("r", "source_record_id"), ("c", "contributor"), ("su", "source_url"),
                       ("ul", "sentence_url"), ("ts", "translation_source")):
        if example.get(field):
            record[key] = example[field]
    for key, value, field in (("b", example.get("attribution"), "attribution"),
                              ("l", example.get("license"), "license"),
                              ("o", meta_source.get("url"), "url")):
        if value and value != source_defaults.get(field):
            record[key] = value
    target_meta = metadata.get("target") or {}
    if target_meta.get("url"):
        # 1: the sentence's own page is the source URL (Tatoeba's is both).
        record["tu"] = 1 if target_meta["url"] == meta_source.get("url") else target_meta["url"]
    if target_meta.get("contributor") and target_meta.get("contributor") != example.get("contributor"):
        record["tc"] = target_meta["contributor"]
    provenance = example.get("provenance") if isinstance(example.get("provenance"), dict) else {}
    document = meta_source.get("document") or {}
    fields = [str(provenance.get(k) or document.get(k) or "") for k in ("title_id", "subtitle_id", "line")]
    if any(fields):
        record["d"] = fields
    if provenance and (provenance.get("corpus") or source) != source:
        record["pc"] = provenance.get("corpus")
    title = example.get("source_title") or metadata.get("source_title")
    if title:
        record["st"] = title
    wsd = metadata.get("wsd") or {}
    level = wsd.get("supported_level")
    agree = (wsd.get("gemini_recommendation") or {}).get("reason") == _AGREE
    if level or agree:
        record["w"] = [level or "", 1 if agree else 0]
    return record


def shard_app_examples(release_app_dir: Path, *, slim: bool = False) -> dict[str, Any]:
    """Write one shard per study set beside the existing examples monolith."""

    app_dir = release_app_dir.expanduser().resolve()
    examples_path = app_dir / "vocabulary.examples.json"
    index_path = app_dir / "vocabulary.index.json"
    structure_path = app_dir / "study-structure.json"
    if not examples_path.is_file() or not index_path.is_file() or not structure_path.is_file():
        raise ExampleShardError(f"release app directory is missing examples, index, or study structure: {app_dir}")

    examples = _object(examples_path)
    index = _object_list(index_path)
    structure = _object(structure_path)
    id_by_surface = {
        str(card.get("surface_card_id") or ""): str(card.get("id") or "")
        for card in index
        if isinstance(card, dict)
    }
    defaults = _source_defaults(examples) if slim else {}
    shard_dir = app_dir / SHARD_DIRECTORY
    shard_dir.mkdir(parents=True, exist_ok=True)
    shards: list[dict[str, Any]] = []
    missing = 0
    for level in structure.get("levels") or []:
        if not isinstance(level, dict):
            continue
        for study_set in level.get("sets") or []:
            if not isinstance(study_set, dict):
                continue
            set_id = str(study_set.get("set_id") or "")
            if not set_id:
                raise ExampleShardError("study set is missing set_id")
            payload: dict[str, Any] = {}
            for card_id in study_set.get("card_ids") or []:
                app_id = id_by_surface.get(str(card_id), "")
                if not app_id or app_id not in examples:
                    missing += 1
                    continue
                card = examples[app_id]
                if slim:
                    card = {**card, "m": [[slim_example(example, defaults) for example in group]
                                          for group in card.get("m") or []]}
                payload[app_id] = card
            filename = f"{set_id}.json"
            (shard_dir / filename).write_bytes(_json_bytes(payload))
            shards.append(
                {
                    "set_id": set_id,
                    "start_rank": int(study_set["start_rank"]),
                    "end_rank": int(study_set["end_rank"]),
                    "path": f"{SHARD_DIRECTORY}/{filename}",
                    "cards": len(payload),
                }
            )
    if not shards:
        raise ExampleShardError("study structure contains no sets")
    manifest = {
        "manifest_version": SLIM_MANIFEST_VERSION if slim else MANIFEST_VERSION,
        "fallback": "vocabulary.examples.json",
        "shard_count": len(shards),
        "missing_cards": missing,
        "shards": shards,
    }
    if slim:
        manifest["example_format"] = SLIM_FORMAT
        manifest["sources"] = defaults
    (app_dir / MANIFEST_NAME).write_bytes(_json_bytes(manifest))
    return manifest
