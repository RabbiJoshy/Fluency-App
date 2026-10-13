"""Sample random (card, sentence) pairs from Dutch pronoun/determiner cards for a hand-checked spot test.
Writes $NL_PROTO/pd_sample.jsonl with the rule label and the English line."""
import json, os, random, re, sys
import stanza, labeller_nl as L
OUT = os.environ["NL_PROTO"]
RUN = "/Users/joshuathomasamar/PycharmProjects/Fluency-Workspace/runs/nl/speech/20261012T175838Z-76d34ee3"
plan = json.load(open(OUT + "/plan.json"))
cards = [c for c in plan["cards"] if c["form"].lower() in L.PRON_GLOSS and c["class"] == "function_word_candidate"]
rng = random.Random(int(os.environ.get("SEED", 7))); pairs = []
cards.sort(key=lambda c: c["rank"]); top = cards[:30]
for _ in range(int(sys.argv[1]) if len(sys.argv) > 1 else 100):
    c = rng.choice(top if rng.random() < 0.6 else cards); pairs.append((c["form"], rng.choice(c["selected"])))
need = {s for _, s in pairs}; bank = {}
for line in open(RUN + "/stages/03_sentence_harvest/output/sentence-bank.jsonl"):
    r = json.loads(line)
    if r["sentence_id"] in need: bank[r["sentence_id"]] = (r["target"]["text"], r["translation"]["text"])
nlp = stanza.Pipeline("nl", processors="tokenize,mwt,pos,lemma,depparse", download_method=None, use_gpu=False, verbose=False)
with open(OUT + "/pd_sample.jsonl", "w") as f:
    for n, (form, sid) in enumerate(pairs):
        nl, en = bank[sid]; d = nlp(nl); lab = None
        m = re.search(r"(?<![\w'’])" + re.escape(form).replace("'", "['’]") + r"(?![\w'])", nl, re.I)
        for s in d.sentences:
            hit = [k for k, w in enumerate(s.words) if m and w.parent.start_char <= m.start() < w.parent.end_char]
            if hit: lab = L.label(s.words, hit[0]); break
        f.write(json.dumps({"n": n, "form": form, "sid": sid, "nl": nl, "en": en, "label": lab}, ensure_ascii=False) + "\n")
