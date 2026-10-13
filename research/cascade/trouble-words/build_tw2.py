"""Build random trouble-word labels (menu gold + teach-as gold). Usage: build_tw2.py <lang> <spec> <out>"""
import json, pickle, re, sys, collections
S = '/private/tmp/claude-501/-Users-joshuathomasamar-PycharmProjects-Fluency-Next/51f9645a-56c4-4730-af54-262353fc48ff/scratchpad'
lang, spec, out = sys.argv[1:4]
if lang == "nl":
    menus, pools, bank = pickle.load(open(S + "/cache.pkl", "rb")); prod = {}
    ids = {w: pools[w] for w in pools}
else:
    menus, assign, bank = pickle.load(open(f"{S}/es/cache_{lang}.pkl", "rb")); prod = assign
    ids = {w: list(assign[w]) for w in assign}
recs = []
for line in open(spec):
    if not line.strip() or line.startswith("#"): continue
    head, _, note = line.partition(" | ")
    sid8, word, occ, gold, verdict, teach = head.split(None, 5)
    sid = [s for s in ids[word] if s[9:17] == sid8]; assert len(sid) == 1, (sid8, word)
    sid = sid[0]; text, tr, src = bank[sid]
    m = list(re.finditer(r"(?<![\w'])" + re.escape(word) + r"(?![\w'])", text, re.I))[int(occ)]
    menu = menus[word]; gi = [] if gold == "-" else [int(g) for g in gold.split(",")]
    recs.append(dict(benchmark="trouble-words/v1", language=lang, word=word, sentence_id=sid, source=src, text=text,
                     translation=tr, span=[m.start(), m.end()], gold_sense_ids=[menu[i][2] for i in gi],
                     gold_glosses=[f"{menu[i][0]}: {menu[i][3]}" for i in gi], verdict=verdict,
                     teach=[t.strip() for t in teach.strip().split("|")], note=note.strip(),
                     production_pick=prod.get(word, {}).get(sid), labelled_by="Claude", blind=True))
open(out, "w").write("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in recs))
print(lang, len(recs), collections.Counter(r["verdict"] for r in recs), "unit-taught:", sum(any(t.startswith("unit:") for t in r["teach"]) for r in recs))
