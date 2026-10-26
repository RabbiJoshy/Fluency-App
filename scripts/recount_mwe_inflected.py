#!/usr/bin/env python3
"""Recount an expression inventory with the inflecting matcher (decision 0034).

The inventory's `corpus_freq` was counted on exact strings, so a verb-led
expression only ever seen inflected (dar-se conta: "me dei conta") counted 0
and was excluded as `zero_freq`, which also keeps it out of WSD. This writes a
new snapshot beside the source: every expression is counted over a sentence
pool with ExpressionInflector, a `zero_freq` exclusion that now occurs is
readmitted (compositional exclusions stay out), and a verb-led expression is
attached to its verb. The source snapshot is never edited.

    python scripts/recount_mwe_inflected.py --language pt \\
        --inventory <workspace>/raw/mwe/mwe-pt-20261003-v15/mwe_merged.json \\
        --paradigms <workspace>/cache/reflexives/forms-pt.json \\
        --requests <review>/requests.json [--requests ...] \\
        --out <workspace>/raw/mwe/mwe-pt-20261026-v15-inflected/mwe_merged.json
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from datetime import UTC, datetime
import hashlib
import json
from pathlib import Path
import re
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from fluency.wsd.multiword import _WORD, _flatten, load_expression_inflector  # noqa: E402


def sentence_pool(paths: list[Path]) -> list[str]:
    texts: set[str] = set()
    for path in paths:
        for req in json.loads(path.read_text(encoding="utf-8")):
            texts.update(req["body"]["state"]["sentences"].values())
    return sorted(texts)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--language", required=True)
    ap.add_argument("--inventory", type=Path, required=True)
    ap.add_argument("--paradigms", type=Path, required=True)
    ap.add_argument("--requests", type=Path, action="append", required=True)
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()
    if args.out.exists():
        raise SystemExit(f"{args.out} exists; snapshots are immutable")
    source_bytes = args.inventory.read_bytes()
    payload = json.loads(source_bytes)
    mwes = payload["mwes"]
    inflector = load_expression_inflector(args.paradigms)

    heads = {expression: inflector.head(expression) for expression in mwes}
    by_word: dict[str, set[str]] = defaultdict(set)
    for expression, row in mwes.items():
        for word in row.get("attach_words") or ():
            by_word[str(word).casefold()].add(expression)
        if heads[expression]:
            by_word[heads[expression][0]].add(expression)

    pool = sentence_pool(args.requests)
    counts: Counter[str] = Counter()
    for text in pool:
        flattened = _flatten(text)
        candidates: set[str] = set()
        for match in _WORD.finditer(text):
            token = match.group(0).casefold()
            candidates |= by_word.get(token, set())
            for lemma in inflector.lemmas_of(token):
                candidates |= by_word.get(lemma, set())
        for expression in candidates:
            if heads[expression] and inflector.match(expression, text):
                counts[expression] += 1
            elif f" {expression.casefold()} " in flattened:
                counts[expression] += 1

    readmitted = []
    for expression, row in mwes.items():
        row["corpus_freq_exact"] = int(row.get("corpus_freq", 0) or 0)
        row["corpus_freq_inflected_pool"] = counts[expression]
        if row["corpus_freq_exact"] == 0 and counts[expression] > 0:
            row["corpus_freq"] = counts[expression]
            if row.get("verdict") == "exclude" and row.get("reason") == "zero_freq":
                row["verdict"], row["reason"] = "keep", "inflected_recount"
                readmitted.append(expression)
        if heads[expression]:
            row["attach_words"] = sorted({*(row.get("attach_words") or ()), heads[expression][0]})
    payload["derived_from"] = {
        "inventory_content_id": "sha256:" + hashlib.sha256(source_bytes).hexdigest(),
        "paradigm_content_id": inflector.content_id,
        "sentence_pool": [str(p) for p in args.requests], "sentence_pool_size": len(pool),
        "rule": "inflected recount (decision 0034); zero_freq exclusions that occur are readmitted",
        "created_at": datetime.now(UTC).isoformat(),
    }
    args.out.parent.mkdir(parents=True)
    args.out.write_text(json.dumps(payload, ensure_ascii=False) + "\n", encoding="utf-8")
    occurring = sum(1 for c in counts.values() if c)
    print(f"{len(pool):,} sentences; {occurring:,} expressions occur; {len(readmitted)} readmitted "
          f"(e.g. {', '.join(sorted(readmitted, key=lambda e: -counts[e])[:12])}) -> {args.out}")


if __name__ == "__main__":
    main()
