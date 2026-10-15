"""Cache the existing reflexive tagger's actual decisions for an audit set."""
import importlib
import json
import sys
from pathlib import Path

from record_gold import AUDIT

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))


def main():
    import spacy
    from spacy.tokens import DocBin
    split = sys.argv[1] if len(sys.argv) > 1 else "development"
    rows = [json.loads(line) for line in (AUDIT / f"blind-{split}.jsonl").read_text().splitlines()]
    for lang, model in (("es", "es_dep_news_trf"), ("pt", "pt_core_news_lg")):
        path = AUDIT / f"reflexive-{split}-{lang}.json"
        if path.exists():
            continue
        nlp = spacy.load(model)
        tagger = importlib.import_module(f"fluency.reflexive.{'spanish' if lang == 'es' else 'portuguese'}")
        selected = [r for r in rows if r["language"] == lang]
        result = {}
        cache = DocBin(store_user_data=False)
        for row, doc in zip(selected, nlp.pipe([r["text"] for r in selected], batch_size=32)):
            cache.add(doc)
            result[str(row["review_id"])] = [{"text": t.text, "lemma": t.lemma_, "pos": t.pos_, "dep": t.dep_,
                    "start": t.idx, "end": t.idx + len(t.text), "head_start": t.head.idx,
                    "resolved_lemma": tagger.lemma_of(t) if lang == "pt" else tagger.tok_lemma(t),
                    "policy": list(tagger.policy(doc, (t.idx, t.idx + len(t.text))))}
                    for t in doc if t.pos_ in ("VERB", "AUX") or (lang == "pt" and "-" in t.text)]
        cache.to_disk(AUDIT / f"reflexive-{split}-{lang}.spacy")
        path.write_text(json.dumps({"parser": model + "@" + nlp.meta["version"], "rows": result}, ensure_ascii=False) + "\n")
        print(lang, len(result), "reflexive decisions cached", flush=True)


if __name__ == "__main__":
    main()
