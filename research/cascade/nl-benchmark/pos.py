"""Stanza (pinned stanza-nl 1.14.0) UPOS/deprel of each benchmark target, by character offset."""
import json, os, stanza
HERE = os.path.dirname(os.path.abspath(__file__))
rows = [json.loads(l) for n in ("labels-random.jsonl", "labels-hard.jsonl") for l in open(os.path.join(HERE, n))]
nlp = stanza.Pipeline("nl", processors="tokenize,mwt,pos,lemma,depparse", download_method=None, use_gpu=False, verbose=False)
docs = nlp.bulk_process([stanza.Document([], text=r["text"]) for r in rows])
out = {}
for r, d in zip(rows, docs):
    a, b = r["span"]; hit = None
    for s in d.sentences:
        for tok in s.tokens:
            if tok.start_char <= a < tok.end_char or a <= tok.start_char < b:
                w = tok.words[0]; head = s.words[w.head - 1].lemma if w.head else "ROOT"
                hit = {"upos": w.upos, "deprel": w.deprel, "lemma": w.lemma, "head": head}
                break
        if hit: break
    out[f"{r['sentence_id']}:{a}"] = hit
json.dump(out, open(os.path.join(HERE, "results", "_pos.json"), "w"), ensure_ascii=False, indent=0)
print(len(out), sum(v is None for v in out.values()), "unmatched")
