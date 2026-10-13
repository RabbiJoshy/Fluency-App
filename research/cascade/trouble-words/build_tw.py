"""Build trouble-word labels from a spec. Usage: build_tw.py <lang> <cache.pkl> <spec> <out.jsonl>"""
import json, pickle, re, sys, collections
lang, cache, spec, out = sys.argv[1:5]
menus, assign, bank = pickle.load(open(cache, "rb"))
recs = []
for line in open(spec):
    if not line.strip() or line.startswith("#"): continue
    head, _, note = line.partition("|")
    sid8, word, occ, gold, verdict, unit = head.split()
    sid = [s for s in assign[word] if s[9:17] == sid8]; assert len(sid) == 1, (sid8, word)
    sid = sid[0]; text, tr, src = bank[sid]
    m = list(re.finditer(r"(?<![\w'])" + re.escape(word) + r"(?![\w'])", text, re.I))[int(occ)]
    menu = menus[word]; gi = [] if gold == "-" else [int(g) for g in gold.split(",")]
    recs.append(dict(benchmark="trouble-words/v0", language=lang, word=word, sentence_id=sid, source=src, text=text,
                     translation=tr, span=[m.start(), m.end()], gold_sense_ids=[menu[i][2] for i in gi],
                     gold_glosses=[f"{menu[i][0]}: {menu[i][3]}" for i in gi], verdict=verdict,
                     unit=None if unit == "-" else unit.replace("_", " "), note=note.strip(),
                     production_pick=assign[word][sid], labelled_by="Claude", blind=False))
open(out, "w").write("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in recs))
print(len(recs), collections.Counter(r["verdict"] for r in recs), sum(r["unit"] is not None for r in recs), "in a larger unit")
