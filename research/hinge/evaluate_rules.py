"""Evaluate current rules on pinned, cached parses without loading NLP models."""
import importlib
import json
import sys
from pathlib import Path
from types import SimpleNamespace

from record_gold import AUDIT

RULES = Path(__file__).resolve().parents[2] / "research/cascade/trouble-words"
sys.path.insert(0, str(RULES))
from occurrence import locate


def restore(sentences):
    output = []
    for sentence in sentences:
        parents = {}
        words = []
        for data in sentence:
            data = dict(data)
            token = data.pop("token")
            key = (token["start_char"], token["end_char"])
            parent = parents.setdefault(key, SimpleNamespace(**token, words=[]))
            word = SimpleNamespace(**data, parent=parent)
            parent.words.append(word)
            words.append(word)
        output.append(SimpleNamespace(words=words))
    return SimpleNamespace(sentences=output)


def evaluate(split="development"):
    cache_split = "census" if split in ("coverage", "census") else split
    parses = {lang: json.loads((AUDIT / f"parsed-{cache_split}-{lang}.json").read_text())["rows"] for lang in ("es", "pt")}
    reflexives = {lang: json.loads((AUDIT / f"reflexive-{cache_split}-{lang}.json").read_text())["rows"] for lang in ("es", "pt")}
    labellers = {lang: importlib.import_module("labeller_" + lang) for lang in ("es", "pt")}
    output = []
    errors = []
    source = AUDIT / ("blind-census.jsonl" if split == "census" else f"gold-{split}.jsonl")
    for row in map(json.loads, source.read_text().splitlines()):
        lang, identifier = row["language"], str(row["review_id"])
        doc = restore(parses[lang][identifier])
        span = row.get("target_span") or (row["spans"][0] if row["spans"] else None)
        hit = locate(doc, row["text"], row["word"], span)
        result = labellers[lang].label(hit[0], hit[1], surface=hit[2], reflexive_decisions=reflexives[lang][identifier]) if hit else None
        label = result if result and result["kind"] != "none" else None
        got = f"{label['kind']}:{label['value']}" if label else "none"
        output.append({**row, "target_span": span, "predicted": label, "identity_match": got in row["accepted"] if "accepted" in row else None})
        if "accepted" in row and got not in row["accepted"]:
            errors.append(output[-1])
    path = AUDIT / f"corrected-{split}.jsonl"
    path.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in output))
    print(len(output), "rows;", len(errors), "identity discrepancies (require semantic adjudication)")
    for r in errors:
        print(r["review_id"], r["word"], r["predicted"], "GOLD", r["accepted"], "|", r["text"])


if __name__ == "__main__":
    evaluate(sys.argv[1] if len(sys.argv) > 1 else "development")
