"""Carry existing translation-pair measurements into display metadata.

This module never scores, selects, filters or reorders sentences. The cache is
an input, identified by its content hash when used by a release or companion.
"""
from __future__ import annotations

import json
import hashlib
import math
from pathlib import Path
from typing import Any


def load_translation_alignment(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {"model": None, "alignment_version": None, "scores": {}}
    raw = path.read_bytes()
    payload = json.loads(raw)
    if not payload.get("model") or not payload.get("alignment_version"):
        raise ValueError("translation alignment cache lacks model/version provenance")
    scores = payload.get("scores")
    if not isinstance(scores, dict):
        raise ValueError("translation alignment cache lacks a score mapping")
    for sentence_id, score in scores.items():
        if (not isinstance(sentence_id, str) or isinstance(score, bool)
                or not isinstance(score, (int, float)) or not math.isfinite(score)
                or not -1 <= score <= 1):
            raise ValueError(f"invalid translation alignment score for {sentence_id}")
    return {**payload, "content_id": "sha256:" + hashlib.sha256(raw).hexdigest()}


def translation_alignment_metadata(cache: dict[str, Any], sentence_id: str) -> dict[str, Any] | None:
    score = cache["scores"].get(sentence_id)
    if score is None:
        return None
    return {"score": score, "model": cache["model"], "version": cache["alignment_version"]}
