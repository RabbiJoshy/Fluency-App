"""Stage C2: label every function-word candidate's selected sentences with the current
rule labeller and decide which cards get the function-word presentation (>= 6 of 10
labelled). Writes $NL_PROTO/fw.json."""
import json, os, re, sys
from pathlib import Path
sys.path.insert(0, "/Users/joshuathomasamar/PycharmProjects/Fluency-Next/research/cascade/trouble-words")
import stanza, labeller_nl as L
OUT = Path(os.environ["NL_PROTO"])
RUN = Path("/Users/joshuathomasamar/PycharmProjects/Fluency-Workspace/runs/nl/speech/20261012T175838Z-76d34ee3")
MIN_LABELLED = 6
plan = json.loads((OUT / "plan.json").read_text())
cands = [c for c in plan["cards"] if c["class"] == "function_word_candidate"]
need = {s for c in cands for s in c["selected"]}
bank = {}
for line in open(RUN / "stages/03_sentence_harvest/output/sentence-bank.jsonl"):
    r = json.loads(line)
    if r["sentence_id"] in need: bank[r["sentence_id"]] = r["target"]["text"]
nlp = stanza.Pipeline("nl", processors="tokenize,mwt,pos,lemma,depparse", download_method=None, use_gpu=False, verbose=False)
out = {"min_labelled": MIN_LABELLED, "labeller": "research/cascade/trouble-words/labeller_nl.py", "cards": {}}
for c in cands:
    docs = nlp.bulk_process([stanza.Document([], text=bank[s]) for s in c["selected"]])
    labels = {}
    for sid, d in zip(c["selected"], docs):
        m = re.search(r"(?<![\w'])" + re.escape(c["form"]) + r"(?![\w'])", bank[sid], re.I)
        lab = None
        if m:
            for s in d.sentences:
                hit = [k for k, w in enumerate(s.words) if w.parent.start_char <= m.start() < w.parent.end_char]
                if hit: lab = L.label(s.words, hit[0]); break
        if lab and lab["kind"] != "none":
            labels[sid] = {k: lab[k] for k in ("kind", "value", "gloss", "rule")}
    out["cards"][c["card_id"]] = {"form": c["form"], "rank": c["rank"], "keep": len(labels) >= MIN_LABELLED, "labels": labels}
(OUT / "fw.json").write_text(json.dumps(out, ensure_ascii=False))
kept = [v for v in out["cards"].values() if v["keep"]]
print(f"{len(cands)} candidates, {len(kept)} get the function-word presentation")
