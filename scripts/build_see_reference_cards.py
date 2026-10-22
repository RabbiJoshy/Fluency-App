#!/usr/bin/env python3
"""Build dictionary reference content only for explicit multiword See targets.

Does not modify releases, MWE admission, WSD assignments, or learner card IDs.
Dictionary examples are distinguished from corpus observations; quotations and
unresolved redirects are not turned into examples or definitions.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
from urllib.parse import quote

ROOT = Path(__file__).resolve().parents[1]


def see_targets(rows: list[dict]) -> set[str]:
    targets: set[str] = set()
    for row in rows:
        meanings = [*row.get("meanings", []), *row.get("unused_menu_senses", [])]
        meanings.extend(s for m in list(meanings) for s in m.get("allSenses", []))
        for meaning in meanings:
            metadata = meaning.get("metadata") or {}
            references = [metadata.get("cross_references", []),
                metadata.get("sense_provider_metadata", {}).get("cross_references", []),
                metadata.get("sense_metadata", {}).get("source_metadata", {}).get("cross_references", [])]
            for values in references:
                for ref in values:
                    target = str(ref.get("target") or "").strip()
                    if ref.get("relation") == "see" and re.search(r"\s", target):
                        targets.add(target)
            match = re.fullmatch(r"See ([^.]+)\.", str(meaning.get("translation") or "").strip())
            if match:
                targets.update(t.strip() for t in match[1].split(",") if re.search(r"\s", t.strip()))
    return targets


def dictionary_senses(entry: dict) -> list[dict]:
    result = []
    for sense in entry.get("senses", []):
        glosses = [str(g).strip() for g in sense.get("glosses", []) if str(g).strip()]
        if not glosses or sense.get("form_of") or sense.get("alt_of"):
            continue
        # Some extracts misparse an example as an additional definition.
        if any("―" in g or "\n" in g or re.match(r"^(?:see|alternative form|inflection of)\b", g, re.I) for g in glosses):
            continue
        record = {"translation": glosses[0], "context": "; ".join(glosses[1:]),
                  "pos": entry.get("pos", "phrase"), "source": "wiktionary"}
        if any("with infinitive" in g for g in sense.get("raw_glosses", [])):
            record["context"] = "; ".join(filter(None, [record["context"], "with infinitive"]))
        example = next((e for e in sense.get("examples", [])
                        if e.get("type") == "example" and e.get("text")
                        and (e.get("translation") or e.get("english"))), None)
        if example:
            record["canonical_example"] = {"text": example["text"],
                "translation": example.get("translation") or example["english"],
                "evidence": "dictionary"}
        result.append(record)
    return result


def build(rows: list[dict], dictionary: Path, language_name: str) -> dict:
    targets = see_targets(rows)
    needles = [json.dumps(t, ensure_ascii=False).encode() for t in targets]
    entries: dict[str, dict] = {}
    digest = hashlib.sha256()
    with dictionary.open("rb") as handle:
        for line in handle:
            digest.update(line)
            if not any(needle in line for needle in needles):
                continue
            record = json.loads(line)
            word = record.get("word")
            if word not in targets:
                continue
            senses = dictionary_senses(record)
            if not senses:
                continue
            entry = entries.setdefault(word.casefold(), {"expression": word, "senses": [],
                "reference_only": True,
                "source_url": f"https://en.wiktionary.org/wiki/{quote(word.replace(' ', '_'))}#{quote(language_name)}"})
            entry["senses"].extend(senses)
    return {"schema": "see-expression-references/v1", "scope": "see_links_only",
        "source": {"provider": "wiktionary", "snapshot": dictionary.parent.name,
                   "filename": dictionary.name, "sha256": digest.hexdigest()},
        "entries": entries, "unresolved": sorted(t for t in targets if t.casefold() not in entries)}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--language", required=True, help="app config language key")
    parser.add_argument("--dictionary", type=Path, required=True, help="pinned Kaikki JSONL extract")
    args = parser.parse_args()
    config_path = ROOT / "app/config/config.json"
    config_text = config_path.read_text()
    cfg = json.loads(config_text)["languages"][args.language]
    index = ROOT.parent / "Fluency-Workspace" / cfg["indexPath"]
    rows = json.loads(index.read_text())
    payload = build(rows, args.dictionary, cfg["name"])
    payload["language"] = cfg["routeCode"]
    payload["built_from_index"] = cfg["indexPath"]
    payload["index_sha256"] = hashlib.sha256(index.read_bytes()).hexdigest()
    path = f'data/see-references/{cfg["routeCode"]}-see-v1.json'
    out = ROOT / "app" / path
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n")
    previous = cfg.get("seeReferencesPath")
    if previous:
        config_text = config_text.replace(json.dumps(previous), json.dumps(path))
    else:
        index_line = f'"indexPath": {json.dumps(cfg["indexPath"])}'
        config_text = config_text.replace(index_line, index_line + f',\n      "seeReferencesPath": {json.dumps(path)}')
    config_path.write_text(config_text)
    print(f'{len(payload["entries"])} reference expressions; unresolved: {payload["unresolved"]}')


if __name__ == "__main__":
    main()
