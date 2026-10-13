"""Stage C: Stanza (pinned nl 1.14.0) over every selected sentence of function-word and
cascade cards; records the target's UPOS and, for function-word candidates, the rule label.
Writes $NL_PROTO/parsed.jsonl (resumable by card)."""
import json, os, sys, re
from pathlib import Path
sys.path.insert(0, "/Users/joshuathomasamar/PycharmProjects/Fluency-Next/research/cascade/trouble-words")
import stanza, labeller_nl as L
OUT = Path(os.environ["NL_PROTO"])
RUN = Path("/Users/joshuathomasamar/PycharmProjects/Fluency-Workspace/runs/nl/speech/20261012T175838Z-76d34ee3")
plan = json.loads((OUT / "plan.json").read_text())
todo = [c for c in plan["cards"] if c["class"] in ("function_word_candidate", "cascade")]
need = {s for c in todo for s in c["selected"]}
bank = {}
for line in open(RUN / "stages/03_sentence_harvest/output/sentence-bank.jsonl"):
    r = json.loads(line)
    if r["sentence_id"] in need: bank[r["sentence_id"]] = r["target"]["text"]
path = OUT / "parsed.jsonl"
done = {json.loads(l)["card_id"] for l in open(path)} if path.exists() else set()
nlp = stanza.Pipeline("nl", processors="tokenize,mwt,pos,lemma,depparse", download_method=None, use_gpu=False, verbose=False)
with open(path, "a") as f:
    for n, c in enumerate(todo):
        if c["card_id"] in done: continue
        sids = c["selected"]; form = c["form"].lower()
        docs = nlp.bulk_process([stanza.Document([], text=bank[s]) for s in sids])
        rows = []
        for sid, d in zip(sids, docs):
            m = re.search(r"(?<![\w'])" + re.escape(form) + r"(?![\w'])", bank[sid], re.I)
            hit = None
            if m:
                for s in d.sentences:
                    for k, w in enumerate(s.words):
                        if w.parent.start_char <= m.start() < w.parent.end_char:
                            hit = (s.words, k); break
                    if hit: break
            upos = hit[0][hit[1]].upos if hit else None
            lab = L.label(*hit) if hit and c["class"] == "function_word_candidate" else None
            rows.append({"sentence_id": sid, "upos": upos, "span": [m.start(), m.end()] if m else None, "label": lab})
        f.write(json.dumps({"card_id": c["card_id"], "rows": rows}, ensure_ascii=False) + "\n"); f.flush()
        if n % 200 == 0: print(n, "/", len(todo), flush=True)
print("done")
