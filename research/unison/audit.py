"""Build and summarise the UNISON part 1 problem list.

The audit is written by hand into ``research/unison/labels/<lang>-audit.jsonl``
as it is read, one problem per line, with short (8-hex) sentence ids as they
appear in the card views. ``build`` checks every line, fills in the card's
word, rank and id from the card reader, expands the sentence ids, and writes
``docs/unison/audit-300.jsonl``. ``summary`` ranks causes by cards affected.

Raw line fields: language, rank, cause, layer, scope, shows, should, and
optionally ids (short sentence ids), gold (a menu label, a special gold such as
``phrase:tener que``, or {short id: label}), alt, note.

  python research/unison/audit.py build
  python research/unison/audit.py summary [--language es] [--chunk t01]
"""

from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_WORKSPACE = ROOT.parent / "Fluency-Workspace"
RELEASES = {"es": "es-speech-v23-10000x30-slim", "pt": "pt-speech-v23-10000x30-slim"}
LABELS = ROOT / "research" / "unison" / "labels"
OUTPUT = ROOT / "docs" / "unison" / "audit-300.jsonl"
# The brief's five layers, plus inventory and harvest (stated in the plan).
LAYERS = {"menu", "features", "wsd", "selection", "display", "inventory", "harvest"}
SCOPES = {"card", "row", "example"}
SPECIAL = ("phrase:", "none:", "not_target:")


def read_jsonl(path: Path) -> list[dict]:
    if not path.exists():
        return []
    with open(path, encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def load_cards(workspace: Path, language: str) -> dict[int, dict]:
    path = workspace / "reviews" / "unison" / RELEASES[language] / "cards.jsonl"
    cards = {}
    with open(path, encoding="utf-8") as handle:
        for line in handle:
            card = json.loads(line)
            cards[card["rank"]] = {"word": card["word"], "card_id": card["card_id"], "chunk": card["chunk"],
                                   "sentences": list(card["examples"]), "menu": {e["label"] for e in card["menu"]}}
    return cards


def check_label(label: str, menu: set[str], where: str) -> None:
    if label.startswith(SPECIAL):
        return
    if label not in menu:
        raise SystemExit(f"{where}: gold label {label!r} is not on this card's menu")


def build(workspace: Path) -> None:
    out = []
    for language in sorted(RELEASES):
        raw = read_jsonl(LABELS / f"{language}-audit.jsonl")
        if not raw:
            continue
        cards = load_cards(workspace, language)
        for n, rec in enumerate(raw, 1):
            where = f"{language}-audit.jsonl line {n}"
            for field in ("rank", "cause", "layer", "scope", "shows", "should"):
                if not rec.get(field) and rec.get(field) != 0:
                    raise SystemExit(f"{where}: missing {field}")
            if rec["layer"] not in LAYERS:
                raise SystemExit(f"{where}: unknown layer {rec['layer']!r}")
            if rec["scope"] not in SCOPES:
                raise SystemExit(f"{where}: unknown scope {rec['scope']!r}")
            card = cards.get(rec["rank"])
            if card is None:
                raise SystemExit(f"{where}: rank {rec['rank']} is not an audited card")
            full_ids = []
            for short in rec.get("ids", []):
                hits = [sid for sid in card["sentences"] if sid.startswith(short)]
                if len(hits) != 1:
                    raise SystemExit(f"{where}: sentence id {short!r} matches {len(hits)} sentences on #{rec['rank']} {card['word']}")
                full_ids.append(hits[0])
            gold = rec.get("gold")
            if isinstance(gold, dict):
                expanded = {}
                for short, label in gold.items():
                    hits = [sid for sid in full_ids if sid.startswith(short)]
                    if len(hits) != 1:
                        raise SystemExit(f"{where}: gold key {short!r} is not one of this line's ids")
                    check_label(label, card["menu"], where)
                    expanded[hits[0]] = label
                gold = expanded
            elif gold:
                check_label(gold, card["menu"], where)
            for label in rec.get("alt") or []:
                check_label(label, card["menu"], where)
            if rec["scope"] == "example" and not full_ids:
                raise SystemExit(f"{where}: an example-scope problem needs sentence ids")
            out.append({
                "language": language, "rank": rec["rank"], "word": card["word"], "card_id": card["card_id"],
                "chunk": card["chunk"], "shows": rec["shows"], "should": rec["should"], "cause": rec["cause"],
                "layer": rec["layer"], "scope": rec["scope"], "sentence_ids": full_ids,
                **({"gold": gold} if gold else {}), **({"alt": rec["alt"]} if rec.get("alt") else {}),
                **({"note": rec["note"]} if rec.get("note") else {}),
            })
    out.sort(key=lambda r: (r["language"], r["rank"]))
    with open(OUTPUT, "w", encoding="utf-8") as handle:
        for rec in out:
            handle.write(json.dumps(rec, ensure_ascii=False) + "\n")
    print(f"{len(out)} problems -> {OUTPUT.relative_to(ROOT)}")


def summary(language: str | None, chunks: list[str] | None) -> None:
    rows = [r for r in read_jsonl(OUTPUT)
            if (not language or r["language"] == language) and (not chunks or r["chunk"] in chunks)]
    by_cause: dict[str, dict] = defaultdict(lambda: {"cards": set(), "sentences": 0, "layers": set(), "lines": 0})
    for r in rows:
        entry = by_cause[r["cause"]]
        entry["cards"].add((r["language"], r["rank"]))
        entry["sentences"] += len(r["sentence_ids"])
        entry["layers"].add(r["layer"])
        entry["lines"] += 1
    ranked = sorted(by_cause.items(), key=lambda kv: (-len(kv[1]["cards"]), -kv[1]["sentences"]))
    print(f"{'cause':32} cards  sentences  layers")
    for cause, entry in ranked:
        langs = defaultdict(int)
        for lang, _ in entry["cards"]:
            langs[lang] += 1
        split = " ".join(f"{k}{v}" for k, v in sorted(langs.items()))
        print(f"{cause:32} {len(entry['cards']):5}  {entry['sentences']:9}  {','.join(sorted(entry['layers']))}  ({split})")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="command", required=True)
    b = sub.add_parser("build")
    b.add_argument("--workspace", type=Path, default=DEFAULT_WORKSPACE)
    s = sub.add_parser("summary")
    s.add_argument("--language", choices=sorted(RELEASES))
    s.add_argument("--chunk", action="append")
    args = parser.parse_args()
    if args.command == "build":
        build(args.workspace)
    else:
        summary(args.language, args.chunk)


if __name__ == "__main__":
    main()
