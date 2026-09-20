"""Export source-list frequencies for the surfaces in one published Speech index.

The app's legacy ``corpus_count`` field is absent from current Speech releases.
Keep these values in a small companion file, separate from harvested examples.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from fluency.inventory.frequency_list import read_frequency_list
from fluency.inventory.lexique import read_lexique4
from fluency.languages.surfaces import normalizer_for_language


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--language", required=True)
    parser.add_argument("--index", type=Path, required=True)
    parser.add_argument("--index-path", required=True, help="Path used by app/config/config.json")
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--source-name", required=True)
    parser.add_argument("--format", choices=("published-list", "lexique4"), required=True)
    parser.add_argument("--unit", choices=("per_million", "occurrences", "lexique_freqortho"), required=True)
    parser.add_argument("--scale", type=float, default=1.0)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    if args.format == "lexique4":
        frequencies = read_lexique4(args.source).frequencies
    else:
        frequencies = read_frequency_list(args.source, language=args.language).frequencies
    normalise = normalizer_for_language(args.language)
    rows = json.loads(args.index.read_text())
    if not isinstance(rows, list):
        raise ValueError("Speech index must be a list")
    values: dict[str, float | int] = {}
    missing: list[str] = []
    for row in rows:
        surface = str(row.get("word") or "")
        key = normalise(surface)
        raw = frequencies.get(key)
        if raw is None:
            missing.append(surface)
            continue
        value = raw * args.scale
        values[key] = int(value) if value.is_integer() else round(value, 6)
    if len(values) < len(rows) * 0.95:
        raise ValueError(f"Source covers only {len(values)} of {len(rows)} released surfaces")

    payload = {
        "schema": "speech-source-frequency/v1",
        "language": args.language,
        "indexPath": args.index_path,
        "source": args.source_name,
        "unit": args.unit,
        "sourceSha256": sha256(args.source),
        "indexSha256": sha256(args.index),
        "covered": len(values),
        "total": len(rows),
        "values": values,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, ensure_ascii=False, separators=(",", ":")) + "\n")
    print(f"{args.language}: {len(values)}/{len(rows)} source frequencies -> {args.output}")
    if missing:
        print(f"  Missing examples: {', '.join(missing[:8])}")


if __name__ == "__main__":
    main()
