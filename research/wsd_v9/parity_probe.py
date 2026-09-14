"""Build the same relation-profile artifact for SpanishDict and Wiktionary."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from .profiles import build_profiles, load_menu, summarize_profiles, write_jsonl


def _run_provider(menu_path: Path, model: str, output: Path) -> dict[str, Any]:
    import spacy

    cards = load_menu(menu_path)
    nlp = spacy.load(model)
    records = build_profiles(cards, nlp=nlp)
    write_jsonl(output, (record.to_json() for record in records))
    summary = summarize_profiles(records)
    summary.update({"menu": str(menu_path), "model": model, "cards": len(cards)})
    return summary


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--spanish-menu", type=Path, required=True)
    parser.add_argument("--portuguese-menu", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--spanish-model", default="es_core_news_lg")
    parser.add_argument("--portuguese-model", default="pt_core_news_lg")
    args = parser.parse_args()

    args.output_dir.mkdir(parents=True, exist_ok=True)
    report = {
        "schema": "wsd-v9-provider-parity/v1",
        "contract": {
            "provider_specific": "source-example decoding and Wiktionary target offsets",
            "provider_neutral": "presence/frame/relation/slot extraction and record schema",
            "unsupported_policy": "explicit source_example_missing or target_not_located status",
        },
        "spanishdict": _run_provider(
            args.spanish_menu,
            args.spanish_model,
            args.output_dir / "spanishdict-profiles.jsonl",
        ),
        "wiktionary": _run_provider(
            args.portuguese_menu,
            args.portuguese_model,
            args.output_dir / "wiktionary-profiles.jsonl",
        ),
    }
    (args.output_dir / "report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    )
    print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
