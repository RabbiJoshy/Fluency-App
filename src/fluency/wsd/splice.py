"""One complete WSD bundle from carried rows, fresh rows and declared rows.

MEND re-resolves a named set of cards and must not redo WSD for the rest.
The importer accepts only a complete bundle whose inputs match the run, so
the new run's Stage 04 is assembled here from three sources, each labelled:

- **carried** rows: another run's Stage 04 for cards whose menu is byte-identical
  in the new run. Each row keeps its decision and says where it came from and
  which menu and method produced it (Invariant 1: label the carriage).
- **fresh** rows: this run's WSD over the re-resolved cards only.
- **declared** rows: cards whose whole menu is one hand-written sense (a gloss or
  an entity). No model looks at them, and each row says so
  (``deterministic_default``, no model revisions).

The bundle then goes through the ordinary importer, so every check it makes on
a whole-deck bundle still applies.
"""

from __future__ import annotations

from collections import Counter
from copy import deepcopy
from typing import Any, Iterable, Mapping

from fluency.wsd.importer import DECLARED_ASSIGNMENT_METHOD

NOT_EVALUATED = "not_evaluated_example_cap"


def carried_row(
    row: Mapping[str, Any], *, source_run_id: str, source_method: Mapping[str, Any],
    sense_menu_content_id: str,
) -> dict[str, Any]:
    out = deepcopy(dict(row))
    evidence = dict(out.get("evidence") or {})
    evidence["carried"] = {
        "from_run": source_run_id,
        "source_sense_menu_content_id": out.get("sense_menu_content_id"),
        "source_method": {k: source_method.get(k) for k in
                          ("profile_id", "implementation_version", "implementation_content_id")},
        "why": "card menu byte-identical in the new run; decision carried, not recomputed",
    }
    out["evidence"] = evidence
    if out.get("status") != "no_menu":
        out["sense_menu_content_id"] = sense_menu_content_id
    return out


def declared_row(
    *, card_id: str, surface_form: str, sentence_id: str, menu_card: Mapping[str, Any],
    sense_menu_content_id: str,
) -> dict[str, Any]:
    analyses = menu_card.get("analyses") or []
    senses = [(a, s) for a in analyses for s in a.get("senses") or []]
    if len(senses) != 1:
        raise ValueError(f"{surface_form}: a declared row needs a one-sense menu, found {len(senses)}")
    analysis, sense = senses[0]
    resolution = menu_card.get("resolution") or {}
    tuple_ = {"headword": analysis["headword"], "part_of_speech": analysis["part_of_speech"]}
    projection = {
        "menu_analysis_id": analysis["menu_analysis_id"],
        "selected_sense_id": sense["sense_id"],
        "selected_tuple": tuple_,
        "source_kind": "provider",
        "selected_score": 1.0,
        "runner_up_score": None,
        "raw_margin": None,
        "rank": 1,
        "emitted_level": "leaf",
        "raw_axis_margins": {"leaf": 1.0, "glosskey": 1.0, "tuple": 1.0},
    }
    return {
        "assignment_version": "wsd-assignment/v1",
        "card_id": card_id,
        "surface_form": surface_form,
        "sentence_id": sentence_id,
        "status": "assigned",
        "sense_menu_content_id": sense_menu_content_id,
        "menu_analysis_id": analysis["menu_analysis_id"],
        "selected_sense_id": sense["sense_id"],
        "selected_tuple": tuple_,
        "decision_path": ["commit"],
        "evidence": {
            "assignment_method": DECLARED_ASSIGNMENT_METHOD,
            "declared_entry_id": (resolution.get("entry") or {}).get("entry_id"),
            "resolver_strategy": resolution.get("strategy"),
            "why": "the card's whole menu is one hand-written sense; there is nothing to choose",
        },
        "confidence": None,
        "model_revisions": {},
        "emitted_level": "leaf",
        "decision_kind": "deterministic_default",
        "selection_projections": {"provider_only": projection, "mwe_augmented": deepcopy(projection)},
        "active_selection_projection": "provider_only",
    }


def sampling_from_rows(rows: Iterable[Mapping[str, Any]], policy: Mapping[str, Any]) -> dict[str, Any]:
    counts = Counter(str(r.get("status")) for r in rows)
    considered = sum(counts.values())
    not_evaluated = counts.get(NOT_EVALUATED, 0)
    return {
        "policy": dict(policy),
        "occurrences_considered": considered,
        "occurrences_selected": considered - not_evaluated,
        "occurrences_not_evaluated": not_evaluated,
    }


def splice_bundle(
    *, run_id: str, language: str, mode: str, inputs: Mapping[str, str], method: Mapping[str, Any],
    sampling_policy: Mapping[str, Any], carried: Iterable[Mapping[str, Any]],
    fresh: Iterable[Mapping[str, Any]], declared: Iterable[Mapping[str, Any]],
) -> tuple[dict[str, Any], dict[str, Any]]:
    """The bundle, and a report of where every row came from."""
    rows: dict[tuple[str, str], dict[str, Any]] = {}
    origin: Counter[str] = Counter()
    for label, group in (("carried", carried), ("fresh", fresh), ("declared", declared)):
        for row in group:
            key = (row["card_id"], row["sentence_id"])
            if key in rows:
                raise ValueError(f"{key} appears in two parts of the splice")
            rows[key] = dict(row)
            origin[label] += 1
    ordered = [rows[key] for key in sorted(rows)]
    bundle = {
        "bundle_version": "wsd-assignment-bundle/v1",
        "run_id": run_id,
        "language": language,
        "mode": mode,
        "coverage": "complete_candidate_pool",
        "method": dict(method),
        "inputs": dict(inputs),
        "sampling": sampling_from_rows(ordered, sampling_policy),
        "assignments": ordered,
    }
    report = {
        "rows_by_origin": dict(origin),
        "statuses": dict(Counter(str(r.get("status")) for r in ordered)),
    }
    return bundle, report
