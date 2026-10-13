"""Score the rule labeller against teach-as gold. Usage: score_rules.py <lang> <labels.jsonl>"""
import json, sys, collections, importlib, stanza
lang, path = sys.argv[1], sys.argv[2]
L = importlib.import_module(f"labeller_{lang}")
rows = [json.loads(l) for l in open(path)]
nlp = stanza.Pipeline(lang, processors="tokenize,mwt,pos,lemma,depparse", download_method=None, use_gpu=False, verbose=False)
docs = nlp.bulk_process([stanza.Document([], text=r["text"]) for r in rows])
per = collections.defaultdict(collections.Counter); out = []
for r, d in zip(rows, docs):
    a = r["span"][0]; lab = {"kind": "none", "value": None, "rule": "not_found"}
    for s in d.sentences:
        for k, w in enumerate(s.words):
            tok = w.parent
            if tok.start_char <= a < tok.end_char and w.text.lower() == r["word"]:
                lab = L.label(s.words, k); break
        else: continue
        break
    got = f"{lab['kind']}:{lab['value']}" if lab["kind"] != "none" else "none"
    norm = lambda x: x.replace("…", "").replace(" ", "").lower()
    ok = any(norm(got) == norm(t) for t in r["teach"])
    c = per[r["word"]]; c["n"] += 1; c["right"] += ok; c["labelled"] += lab["kind"] != "none"
    out.append((ok, r["word"], got, r["teach"], r["text"][:70], lab.get("gloss")))
tot = collections.Counter()
for w, c in per.items():
    print(f"{w:6s} right {c['right']}/{c['n']}  labelled {c['labelled']}/{c['n']}"); tot.update(c)
print(f"ALL    right {tot['right']}/{tot['n']} ({tot['right']/tot['n']:.0%})  labelled {tot['labelled']}/{tot['n']}")
print("\nwrong:")
for ok, w, got, teach, text, gl in out:
    if not ok: print(f"  {w:5s} got {got:30s} gold {'|'.join(teach):38s} {text}")
