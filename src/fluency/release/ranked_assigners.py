"""Ranked WSD assigners: a release takes each example's sense from the first assigner that has one.

Stage 04 of the run being released is the assigner named ``NORMAL``. Any other
assigner is a directory holding ``manifest.json`` (``wsd-assigner/v1``) and a
sparse ``assignments.jsonl``: rows for some (card, sentence) pairs only. A
release declares the order, highest first, e.g. ``[DEEPSEEK v25, NORMAL]`` or
later ``[NORMAL v26, DEEPSEEK v25]``. Nothing is written back to any run, so an
assigner can never be carried into a later run as if WSD had decided it.

An assigner row applies only when its card's sense menu is byte-identical to the
one the run's row was decided against (``sense_menu_content_id``) and its sense
is on that menu; otherwise it is skipped and counted. It replaces the sense, not
the row: status, evidence and function-word labels stay as stage 04 has them.
"""

from __future__ import annotations

import json
from collections import Counter, defaultdict
from copy import deepcopy
from pathlib import Path
from typing import Any, Sequence

from fluency.core.hashing import file_content_id

NORMAL = "NORMAL"
MANIFEST_VERSION = "wsd-assigner/v1"
ROW_VERSION = "wsd-assigner-row/v1"
SENSE_FIELDS = ("menu_analysis_id", "selected_sense_id", "selected_tuple", "emitted_level")


class RankedAssignerError(ValueError):
    pass


def load_assigner(path: Path) -> dict[str, Any]:
    """Read one assigner directory into {manifest, artifact_id, rows}."""

    path = Path(path)
    manifest = json.loads((path / "manifest.json").read_text(encoding="utf-8"))
    if manifest.get("assigner_version") != MANIFEST_VERSION:
        raise RankedAssignerError(f"{path}: not a {MANIFEST_VERSION} assigner")
    for field in ("label", "version", "language"):
        if not isinstance(manifest.get(field), str) or not manifest[field]:
            raise RankedAssignerError(f"{path}: manifest lacks {field}")
    rows_path = path / "assignments.jsonl"
    rows: dict[tuple[str, str], dict[str, Any]] = {}
    for number, line in enumerate(rows_path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        row = json.loads(line)
        if row.get("row_version") != ROW_VERSION:
            raise RankedAssignerError(f"{rows_path}: row {number} is not {ROW_VERSION}")
        key = (row.get("card_id"), row.get("sentence_id"))
        if not all(key) or key in rows:
            raise RankedAssignerError(f"{rows_path}: row {number} has a missing or duplicate identity")
        if not all(row.get(field) for field in (*SENSE_FIELDS, "sense_menu_content_id")):
            raise RankedAssignerError(f"{rows_path}: row {number} lacks a sense field")
        rows[key] = row
    return {"manifest": manifest, "artifact_id": file_content_id(rows_path), "rows": rows,
            "name": f"{manifest['label']} {manifest['version']}"}


def _menu_senses(menu_card: dict[str, Any]) -> dict[str, set[str]]:
    return {a["menu_analysis_id"]: {s["sense_id"] for s in a.get("senses") or []}
            for a in menu_card.get("analyses") or []}


class _DictBase:
    """Stage 04 loaded whole (a dict keyed by (card, sentence)) with the card lookup too."""

    def __init__(self, rows: dict[tuple[str, str], dict[str, Any]]):
        self.rows = rows
        self.by_card: dict[str, dict[str, dict[str, Any]]] = defaultdict(dict)
        for (card, sentence), row in rows.items():
            self.by_card[card][sentence] = row
        self.counts = Counter(row.get("status") for row in rows.values())

    def __bool__(self):
        return bool(self.rows)

    def get(self, key, default=None):
        if isinstance(key, tuple):
            return self.rows.get(key, default)
        return self.by_card.get(key, default)


class RankedAssignments:
    """The base (stage 04) assignments seen through a ranked assigner order.

    Offers the interface the release builder uses on stage 04: ``get((card,
    sentence))``, ``get(card)`` for a card's rows, ``counts`` and truthiness.
    """

    def __init__(self, base, order: Sequence[Any], menu_by_card: dict[str, dict[str, Any]], language: str):
        if not order or sum(1 for item in order if item == NORMAL) != 1:
            raise RankedAssignerError("assigner order must name NORMAL exactly once")
        self.base = _DictBase(base) if isinstance(base, dict) else base
        self.assigners = []
        names = []
        for item in order:
            if item == NORMAL:
                names.append(NORMAL)
                continue
            assigner = item if isinstance(item, dict) else load_assigner(Path(item))
            if assigner["manifest"]["language"] != language:
                raise RankedAssignerError(f"{assigner['name']} is for {assigner['manifest']['language']}, not {language}")
            names.append(assigner["name"])
            self.assigners.append(assigner)
        if len(set(names)) != len(names):
            raise RankedAssignerError("an assigner is named twice in the order")
        self.order = names
        self.normal_rank = names.index(NORMAL)
        self.stats = {a["name"]: Counter() for a in self.assigners}
        self.winners: dict[str, dict[str, dict[str, Any]]] = defaultdict(dict)
        self.counts = Counter(self.base.counts)
        self._decide(menu_by_card)

    def _base_row(self, card: str, sentence: str):
        return self.base.get((card, sentence))

    def _decide(self, menu_by_card):
        keys = sorted({key for a in self.assigners for key in a["rows"]})
        senses_cache: dict[str, dict[str, set[str]]] = {}
        for card, sentence in keys:
            base_row = self._base_row(card, sentence)
            normal_assigned = bool(base_row) and base_row.get("status") == "assigned"
            if card not in senses_cache:
                senses_cache[card] = _menu_senses(menu_by_card.get(card) or {})
            winner = None
            for rank, name in enumerate(self.order):
                if name == NORMAL:
                    if normal_assigned:
                        break
                    continue
                assigner = self.assigners[rank - (rank > self.normal_rank)]
                row = assigner["rows"].get((card, sentence))
                if row is None:
                    continue
                stat = self.stats[name]
                if winner is not None:
                    stat["outranked"] += 1
                    continue
                if base_row is None:
                    stat["skipped_no_stage04_row"] += 1
                    continue
                if row["sense_menu_content_id"] != base_row.get("sense_menu_content_id"):
                    stat["skipped_menu_changed"] += 1
                    continue
                if row["selected_sense_id"] not in senses_cache[card].get(row["menu_analysis_id"], ()):
                    stat["skipped_sense_not_on_menu"] += 1
                    continue
                winner = (assigner, row)
            # Rows of lower assigners NORMAL outranked, for the report.
            for name in self.order[self.normal_rank + 1:] if normal_assigned else ():
                assigner = self.assigners[self.order.index(name) - 1]
                if (card, sentence) in assigner["rows"]:
                    self.stats[name]["outranked_by_normal"] += 1
            if winner is None:
                continue
            assigner, row = winner
            merged = deepcopy(base_row)
            changed = merged.get("selected_sense_id") != row["selected_sense_id"]
            for field in SENSE_FIELDS:
                merged[field] = deepcopy(row[field])
            if merged.get("status") != "assigned":
                self.counts[merged.get("status")] -= 1
                self.counts["assigned"] += 1
                merged["status"] = "assigned"
            evidence = dict(merged.get("evidence") or {})
            if changed:
                # A phrase the run selected no longer describes the new sense.
                evidence.pop("selected_multiword", None)
            evidence["assigner"] = {"label": assigner["manifest"]["label"],
                                    "version": assigner["manifest"]["version"],
                                    "artifact_id": assigner["artifact_id"]}
            merged["evidence"] = evidence
            self.winners[card][sentence] = merged
            self.stats[assigner["name"]]["applied_changed" if changed else "applied_same"] += 1

    def __bool__(self):
        return bool(self.base)

    def get(self, key, default=None):
        if isinstance(key, tuple):
            card, sentence = key
            won = self.winners.get(card, {}).get(sentence)
            return won if won is not None else self.base.get(key, default)
        rows = self.base.get(key, None)
        if rows is None:
            return default
        if key not in self.winners:
            return rows
        merged = dict(rows)
        merged.update(self.winners[key])
        return merged

    def layers(self, sense_menu_artifact: str) -> dict[str, dict[str, Any]]:
        """One composition layer per assigner, saying what it supplied or why not."""

        out = {}
        for rank, name in enumerate(self.order):
            if name == NORMAL:
                continue
            a = self.assigners[rank - (rank > self.normal_rank)]
            out[f"wsd_assigner:{name}"] = {
                "selection_version": "layer-selection/v1",
                "source_type": "snapshot",
                "source_id": a["manifest"].get("assigner_id") or name,
                "artifact_id": a["artifact_id"],
                "record_count": len(a["rows"]),
                "requires": {"sense_menu": sense_menu_artifact},
                "parameters": {
                    "rank": rank + 1,
                    "label": a["manifest"]["label"],
                    "version": a["manifest"]["version"],
                    "description": a["manifest"].get("description", ""),
                    **dict(sorted(self.stats[name].items())),
                },
            }
        return out
