"""Repair prose-only form rows without changing their learning/example identity.

The old leaf identifies a grammatical reading of a verb, not a lexical meaning.
Keep that scope explicit: a learner gloss is a broad verb cue, never a claim
that the old WSD picked one of the infinitive's finer dictionary senses.
"""
from __future__ import annotations

from copy import deepcopy
from typing import Any

from fluency.sense_menu.kaikki import _normalize_linked_finite_forms


def correction_plan(
    index: list[dict[str, Any]], source_rows: list[dict[str, Any]],
    glosses: dict[str, str], conjugations: dict[str, Any],
) -> dict[str, dict[str, Any]]:
    evidence = {}
    for row in source_rows:
        normalized = _normalize_linked_finite_forms(row)
        for old, new in zip(row.get("senses", []), normalized.get("senses", [])):
            if old != new:
                evidence[old["id"]] = (row["word"], old, new)
    plan = {}
    for card in index:
        for meaning in card.get("meanings", []):
            match = evidence.get(meaning.get("source_sense_id"))
            if not match:
                continue
            surface, old, new = match
            if meaning.get("headword") != card["word"]:
                continue
            if card["word"] != surface or meaning["translation"] != old["glosses"][0]:
                raise ValueError(f"source form evidence disagrees with released row: {card['word']} / {surface} / {meaning['translation']}")
            target = new["form_of"][0]["word"]
            if target not in glosses or target not in conjugations:
                raise ValueError(f"missing reviewed gloss or conjugation table: {target}")
            entry = conjugations[target]
            forms = {part.strip() for values in entry.get("tenses", {}).values()
                     for value in values for part in value.split("/")}
            if surface not in forms:
                raise ValueError(f"{surface} is absent from {target}'s conjugations")
            plan[meaning["sense_id"]] = {
                "surface": surface, "headword": target, "translation": glosses[target],
                "source_sense_id": old["id"], "source_gloss": old["glosses"][0],
                "source_form_tags": new["tags"],
                "scope": "verb-level-grammatical-reading",
                "method": "linked-finite-form-learner-cue/v1",
            }
    return plan


def repair_meaning(meaning: dict[str, Any], plan: dict[str, Any]) -> dict[str, Any]:
    correction = plan.get(meaning.get("sense_id"))
    if not correction:
        return meaning
    result = deepcopy(meaning)
    result["headword"] = correction["headword"]
    result["translation"] = correction["translation"]
    metadata = result.setdefault("metadata", {})
    metadata["learner_cue_correction"] = correction
    # Preserve the old source/analysis evidence. The explicit correction above
    # records why lookup/display now differ, without inventing a new WSD leaf.
    return result
