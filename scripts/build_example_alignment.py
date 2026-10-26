#!/usr/bin/env python3
"""Export cached alignment scores for an existing release, without changing it.

One companion shard per example shard keeps the normal set load small. Each
score is joined by immutable sentence id, never by text or array position.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from fluency.release.translation_alignment import load_translation_alignment


def write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, separators=(",", ":")) + "\n", encoding="utf-8")


def build_companion(workspace: Path, examples_path: str, cache_path: Path, output: Path) -> dict:
    cache = load_translation_alignment(cache_path)
    source_dir = (workspace / examples_path).parent
    manifest_path = source_dir / "vocabulary.examples.manifest.json"
    source_manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    card_shards = {}
    total = scored = 0
    for shard in source_manifest["shards"]:
        source = json.loads((source_dir / shard["path"]).read_text(encoding="utf-8"))
        scores = {}
        filename = Path(shard["path"]).name
        for card_id, card in source.items():
            card_shards[card_id] = filename
            examples = [example for group in card.get("m", []) for example in group] + (card.get("u") or [])
            for example in examples:
                if source_manifest.get("example_format") == "slim-example/v1" and "t" in example:
                    value = example.get("i")
                    sentence_id = (value[1:] if value.startswith("=") else "sentence_" + value) if value else None
                else:
                    sentence_id = (example.get("metadata") or {}).get("sentence_id")
                total += 1
                score = cache["scores"].get(sentence_id)
                if score is not None:
                    scores[sentence_id] = score
                    scored += 1
        write_json(output / filename, scores)
    manifest = {
        "schema": "example-alignment/v1", "examplesPath": examples_path,
        "model": cache["model"], "alignment_version": cache["alignment_version"],
        "cache_content_id": cache.get("content_id"),
        "examples_manifest_content_id": "sha256:" + hashlib.sha256(manifest_path.read_bytes()).hexdigest(),
        "card_shards": card_shards, "example_count": total, "scored_example_count": scored,
    }
    write_json(output / "manifest.json", manifest)
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workspace", type=Path, required=True)
    parser.add_argument("--examples-path", required=True)
    parser.add_argument("--cache", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = build_companion(args.workspace, args.examples_path, args.cache, args.output)
    print(f"{result['scored_example_count']}/{result['example_count']} examples; {args.output / 'manifest.json'}")


if __name__ == "__main__":
    main()
