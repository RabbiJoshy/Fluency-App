#!/usr/bin/env python3
"""Sync the JSON suites into app/js/function-word-card.js so the app works offline.

Only the three embedded data blocks are replaced: PORTUGUESE_GRAMMAR_WORDS,
SPANISH_GRAMMAR_WORDS and FW_SYNTAX_TRIAL. The renderer around them lives in the
JS file itself and is edited there. (Until 2026-10-19 this script held its own
copy of the renderer and rewrote the whole file, so running it silently reverted
any renderer change made since that copy was taken.)
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PT_FILE = ROOT / "app/data/grammar-words/pt.json"
ES_FILE = ROOT / "app/data/grammar-words/es.json"
TRIAL_FILE = ROOT / "app/data/grammar-words/syntax-trial.json"
JS_FILE = ROOT / "app/js/function-word-card.js"


def load_suite(path: Path) -> dict:
    data = json.loads(path.read_text())
    for entry in data.values():
        entry["uses"] = entry.get("relations", [])
    return data


def replace_block(source: str, start: str, end: str, body: str) -> str:
    """Replace the text between the `start` line and the line beginning `end`."""
    pattern = re.compile(rf"(^{re.escape(start)})(.*?)(?=^{re.escape(end)})", re.S | re.M)
    if len(pattern.findall(source)) != 1:
        sys.exit(f"Could not find exactly one block starting {start!r} before {end!r} in {JS_FILE}")
    return pattern.sub(lambda m: m.group(1) + body + ";\n\n", source)


def main() -> None:
    pt_compact = json.dumps(load_suite(PT_FILE), ensure_ascii=False, separators=(",", ":"))
    es_compact = json.dumps(load_suite(ES_FILE), ensure_ascii=False, separators=(",", ":"))
    trial_compact = json.dumps(json.loads(TRIAL_FILE.read_text()), ensure_ascii=False, separators=(",", ":"))

    pt_expr = f"JSON.parse({json.dumps(pt_compact)})"
    es_expr = f"JSON.parse({json.dumps(es_compact)})"
    trial_expr = f"JSON.parse({json.dumps(trial_compact)})"

    source = JS_FILE.read_text()
    source = replace_block(source, "export const PORTUGUESE_GRAMMAR_WORDS = ",
                           "// Curated deterministic relational definitions for Spanish", pt_expr)
    source = replace_block(source, "export const SPANISH_GRAMMAR_WORDS = ",
                           "export const GRAMMAR_WORDS = ", es_expr)
    source = replace_block(source, "const FW_SYNTAX_TRIAL = ",
                           "function syntaxTrialEnabled", trial_expr)
    JS_FILE.write_text(source)
    print("Synchronized data blocks in app/js/function-word-card.js (optimized JSON.parse)")


if __name__ == "__main__":
    main()
