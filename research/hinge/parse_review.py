"""Cache parser observations separately from blind gold and rule predictions."""
import json
import sys
from pathlib import Path

from record_gold import AUDIT

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "research/cascade/trouble-words"))


def serialize(doc):
    return [[{"text": w.text, "lemma": w.lemma, "upos": w.upos, "feats": w.feats,
              "deprel": w.deprel, "id": w.id, "head": w.head,
              "token": {"text": w.parent.text, "start_char": w.parent.start_char,
                        "end_char": w.parent.end_char}}
             for w in sentence.words] for sentence in doc.sentences]


def main():
    split = sys.argv[1] if len(sys.argv) > 1 else "development"
    rows = [json.loads(line) for line in (AUDIT / f"blind-{split}.jsonl").read_text().splitlines()]
    for lang in ("es", "pt"):
        path = AUDIT / f"parsed-{split}-{lang}.json"
        if path.exists():
            continue
        selected = [r for r in rows if r["language"] == lang]
        if lang == "es":
            from spacy_adapter import Pipeline
            parser = Pipeline()
            parse = parser.bulk
            revision = parser.version
        else:
            import stanza
            parser = stanza.Pipeline("pt", processors="tokenize,mwt,pos,lemma,depparse", download_method=None, use_gpu=False, verbose=False)
            parse = lambda texts: parser.bulk_process([stanza.Document([], text=t) for t in texts])
            revision = f"stanza-pt-default@{stanza.__version__}"
        observations = {}
        for offset in range(0, len(selected), 32):
            batch = selected[offset:offset + 32]
            for row, doc in zip(batch, parse([r["text"] for r in batch])):
                observations[str(row["review_id"])] = serialize(doc)
            print(lang, offset + len(batch), "/", len(selected), flush=True)
        path.write_text(json.dumps({"parser": revision, "rows": observations}, ensure_ascii=False) + "\n")


if __name__ == "__main__":
    main()
