"""Compare frozen labels with independently reviewed grammar-word gold.

Role/phrase identity is a reproducible first check. Gloss correctness must also
be reviewed: the same phrase name can carry a wrong dictionary reading.
"""
import collections
import json
from pathlib import Path

from record_gold import AUDIT


def compare(tag, split="development", print_errors=True):
    frozen = AUDIT / "inputs/Fluency-Workspace/raw/wsd"
    labels = {lang: json.loads((frozen / lang / f"{tag}-function-word-labels.json").read_text())["cards"] for lang in ("es", "pt")}
    counts = collections.defaultdict(collections.Counter)
    errors = []
    for row in map(json.loads, (AUDIT / f"gold-{split}.jsonl").read_text().splitlines()):
        label = labels[row["language"]].get(row["card_id"], {}).get("labels", {}).get(row["sentence_id"])
        got = f"{label['kind']}:{label['value']}" if label else "none"
        count = counts[(row["language"], row["word"])]
        count["reviewed"] += 1
        count["labelled"] += bool(label)
        if got not in row["accepted"]:
            count["wrong_label" if label else "missing_label"] += 1
            errors.append({**row, "predicted": label})
    print(tag, "label identity only; not a gloss accuracy claim")
    for (lang, word), count in counts.items():
        print(lang, word, dict(count))
    if print_errors:
        for r in errors:
            print(r["review_id"], r["word"], r["predicted"], "GOLD", r["accepted"], r["meaning"], "|", r["text"])
    (AUDIT / f"{tag}-{split}-identity-comparison.json").write_text(json.dumps({"counts": [{"language": l, "word": w, **dict(c)} for (l, w), c in counts.items()], "errors": errors}, ensure_ascii=False, indent=2) + "\n")


if __name__ == "__main__":
    import sys
    compare(sys.argv[1])
