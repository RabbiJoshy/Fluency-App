#!/usr/bin/env python3
"""Compare two surface scorers on what cognate mode would actually skip.

Decision 0027: the shipped scorer is provisional. A replacement is judged here,
on words rather than on a single number. For one language and release it
builds the per-sense map with each scorer, applies the app's rule (every shown
sense must be a free cognate; expressions never are), and prints, for the
first N cards, the words each scorer skips that the other keeps.

    PYTHONPATH=src python scripts/eval_surface_scorer.py --language es \
        --release-index <workspace>/releases/es/speech/<id>/app/vocabulary.index.json \
        --a edit-distance/v1 --b legacy-max4/v1
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

from fluency.enrichments.cognates import build_app_cognates_by_sense

ROOT = Path(__file__).resolve().parents[1]
EXPRESSION_ROUTES = {"deterministic_bypass", "invariant", "competitive_wsd", "ambiguous"}


def is_expression(meaning: dict, word: str) -> bool:
    # Mirrors isExpressionSenseForLemma in app/js/vocab.js.
    pos = meaning.get("pos") or ""
    if pos in {"MWE", "CLITIC"}:
        return True
    metadata = meaning.get("metadata") or {}
    evidence = (metadata.get("multiword_evidence") or [{}])[0]
    if (evidence.get("wsd_routing") or evidence.get("route")) in EXPRESSION_ROUTES:
        return True
    head = str(meaning.get("headword") or "")
    return pos == "PHRASE" and " " in head and head.lower() != word.lower()


def alternatives(translation: str) -> set[str]:
    out = set()
    for part in re.split(r"[,;]", re.sub(r"\([^)]*\)", " ", translation or "")):
        text = re.sub(r"\s+", " ", re.sub(r"[^a-z' ]+", " ", part.lower())).strip()
        text = re.sub(r"^(?:to|the|a|an)\s+", "", text)
        if text and " " not in text:
            out.add(text)
    return out


def skipped(rows: list[dict], payload: dict) -> dict[str, tuple[float, str | None]]:
    cutoff = payload["thresholds"]["en"]
    out = {}
    for row in rows:
        word = str(row.get("word") or "")
        by_headword = payload["scores"].get(word.lower())
        meanings = [m for m in row.get("meanings") or [] if str(m.get("translation") or "").strip()]
        if not by_headword or not meanings:
            continue
        weakest = None
        for meaning in meanings:
            best = (0.0, None)
            if not is_expression(meaning, word):
                headword = str(meaning.get("headword") or "").lower()
                buckets = [by_headword.get(headword), by_headword.get("")] if headword else list(by_headword.values())
                for alt in alternatives(meaning["translation"]):
                    for bucket in buckets:
                        score = (bucket or {}).get(alt, 0.0)
                        if score > best[0]:
                            best = (score, alt)
            if weakest is None or best[0] < weakest[0]:
                weakest = best
        if weakest and weakest[0] >= cutoff:
            out[word] = weakest
    return out


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--language", required=True)
    parser.add_argument("--release-index", type=Path, required=True)
    parser.add_argument("--a", required=True, help="scorer id, e.g. edit-distance/v1")
    parser.add_argument("--b", required=True)
    parser.add_argument("--first", type=int, default=2000)
    parser.add_argument("--workspace", type=Path, default=ROOT.parent / "Fluency-Workspace")
    args = parser.parse_args()

    rows = json.loads(args.release_index.read_text(encoding="utf-8"))
    rows = sorted(rows, key=lambda row: row.get("rank") or 10**9)[: args.first]
    results = {}
    for scorer in (args.a, args.b):
        payload = build_app_cognates_by_sense(
            language=args.language,
            config_root=ROOT / "config",
            raw_root=args.workspace / "raw",
            release_rows=rows,
            surface_scorer=scorer,
        )
        results[scorer] = skipped(rows, payload)
    a, b = results[args.a], results[args.b]
    print(f"{args.language}, first {len(rows)} cards: {args.a} skips {len(a)}, {args.b} skips {len(b)}")
    for name, mine, other in ((args.a, a, b), (args.b, b, a)):
        only = [f"{w}({mine[w][1]} {mine[w][0]:.2f})" for w in mine if w not in other]
        print(f"\nonly {name} ({len(only)}):\n  " + ", ".join(only))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
