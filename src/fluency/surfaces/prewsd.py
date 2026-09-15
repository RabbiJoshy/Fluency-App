"""The frozen pre-WSD artifact set: three documents WSD reads and nothing else.

WSD should not reach back into a run. Everything it needs is here, pinned by
content hash, in a shape that makes retrieval an array index rather than a scan.

Measured on Spanish before this existed: ledger.json 34MB, examples.jsonl
131MB, pools.json 236MB -- 402MB, of which almost none was information. 60% of
the examples file was repeated JSON field names, and 57% of the ledger was
41-character sentence-id strings. Two structural fixes follow from that:

**A sentence's identity is its row index.** The examples document is a fixed
order, so a sentence is an integer. That removes the id strings from every
document that references one, and makes lookup `column[i]`.

**Columns, not rows.** Field names are written once per document rather than
once per row.

Order is part of the contract. A reader may assume index i means the same
sentence in every file of the set, which is what the manifest's hashes pin.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

SET_VERSION = "prewsd-set/v1"
EXAMPLES_VERSION = "prewsd-examples/v1"
PAIRS_VERSION = "prewsd-pairs/v1"


def _write(path: Path, payload: Mapping[str, Any]) -> dict[str, Any]:
    """Write compactly and return the record the manifest pins it by."""

    body = json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
    path.write_text(body, encoding="utf-8")
    return {"path": path.name,
            "bytes": len(body.encode("utf-8")),
            "sha256": hashlib.sha256(body.encode("utf-8")).hexdigest()}


def build(
    out_dir: Path,
    *,
    language: str,
    run_id: str,
    sentences: Sequence[Mapping[str, Any]],
    surfaces: Mapping[str, Mapping[str, Any]],
) -> dict[str, Any]:
    """Write the set. `sentences` fixes the order; `surfaces` references it.

    Each surface entry supplies `eligible`, a list of sentence indices, and the
    per-pair metrics parallel to it. Those metrics are properties of the
    pairing, not of the sentence: the same sentence costs 16.41 against `que`
    and 9.06 against `lo`, because burden counts words harder than *that*
    card's rank. They cannot be folded into the examples document.
    """

    out_dir.mkdir(parents=True, exist_ok=True)

    # --- examples: one column per field, index is the sentence ---
    source_names: list[str] = []
    grammar_names: list[str] = []
    variety_names: list[str] = []
    length_names: list[str] = []

    def intern(table: list[str], value: str | None) -> int:
        if value is None:
            return -1
        if value not in table:
            table.append(value)
        return table.index(value)

    cols: dict[str, list[Any]] = {
        "target": [], "translation": [], "source": [], "alignment": [],
        "target_tokens": [], "grammar": [], "grammar_penalty": [],
        "translation_length_ratio": [], "variety": [], "length_band": [],
    }
    for row in sentences:
        cols["target"].append(row.get("target") or "")
        cols["translation"].append(row.get("translation") or "")
        cols["source"].append(intern(source_names, row.get("source")))
        cols["alignment"].append(row.get("alignment"))
        cols["target_tokens"].append(row.get("target_tokens"))
        cols["grammar"].append([intern(grammar_names, g)
                                for g in (row.get("grammar") or ())])
        cols["grammar_penalty"].append(row.get("grammar_penalty"))
        cols["translation_length_ratio"].append(row.get("translation_length_ratio"))
        cols["variety"].append(intern(variety_names, row.get("variety")))
        cols["length_band"].append(intern(length_names, row.get("length_band")))

    examples = _write(out_dir / "examples.json", {
        "document_version": EXAMPLES_VERSION,
        "language": language,
        "run_id": run_id,
        "count": len(sentences),
        "dictionaries": {"source": source_names, "grammar": grammar_names,
                         "variety": variety_names,
                         "length_band": length_names},
        "columns": cols,
    })

    # --- pairs: per surface, arrays parallel to that surface's eligible list ---
    pairs = _write(out_dir / "pairs.json", {
        "document_version": PAIRS_VERSION,
        "language": language,
        "run_id": run_id,
        "surfaces": {k: dict(v) for k, v in surfaces.items()},
    })

    manifest = {
        "set_version": SET_VERSION,
        "language": language,
        "run_id": run_id,
        "sentences": len(sentences),
        "surfaces": len(surfaces),
        "documents": [examples, pairs],
        "note": "Index i means the same sentence in every document of this set.",
    }
    (out_dir / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    return manifest


def verify(set_dir: Path) -> list[str]:
    """Names of documents whose bytes no longer match the manifest."""

    manifest = json.loads((set_dir / "manifest.json").read_text(encoding="utf-8"))
    bad = []
    for record in manifest["documents"]:
        target = set_dir / record["path"]
        if not target.is_file():
            bad.append(record["path"])
            continue
        if hashlib.sha256(target.read_bytes()).hexdigest() != record["sha256"]:
            bad.append(record["path"])
    return bad
