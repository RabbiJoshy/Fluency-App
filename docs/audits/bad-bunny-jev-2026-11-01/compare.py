#!/usr/bin/env python3
"""Jev pilot vs the live v20 (es-lyrics-v24-1) sense for each Bad Bunny sentence -> compare.json."""
import json, collections, sys
from pathlib import Path
HERE = Path(__file__).resolve().parent
WS = HERE.parents[2].parent / "Fluency-Workspace"
RUN = WS / "reviews/bb-jev-20261101" / (sys.argv[1] if len(sys.argv) > 1 else "pilot50")
LIVE = WS / "releases/lyrics/lyrics-all-artists-v20-1/app/Artists/es/bad-bunny"
master = json.loads((LIVE / "vocabulary_master.json").read_text())
examples = json.loads((LIVE / "examples.json").read_text())
live = {}
for cid, payload in examples.items():
    senses = master[cid]["senses"]
    for s, bucket in zip(senses, payload["m"]):
        for ex in bucket:
            live[(cid, ex["spanish"])] = s
reqs = json.loads((RUN / "requests.json").read_text())
rows, stats = [], collections.Counter()
for req in reqs:
    res = json.loads((RUN / "responses" / f"{req['request_id']}.json").read_text())
    st = req["body"]["state"]
    plan_ex = {}
    for sid, text in st["sentences"].items():
        a = res["answers"].get(sid) or {}
        choice = a.get("choice")
        jev = st["menu"].get(choice) if choice not in (None, "NONE") else None
        raw = text.replace("<<", "").replace(">>", "")
        old = live.get((req["card_id"], raw))
        probs = a.get("probabilities") or {}
        top = sorted(probs.items(), key=lambda kv: -kv[1])
        if choice == "NONE": verdict = "none"
        elif old is None: verdict = "no_live"
        elif old["sense_id"] == jev["sense_id"]: verdict = "same"
        elif old["headword"] == jev["headword"] and (old.get("gloss_base") or old["translation"]).casefold() == jev["translation"].casefold(): verdict = "same"
        else: verdict = "differs"
        stats[verdict] += 1
        rows.append({"card_id": req["card_id"], "surface": req["surface"], "sentence": text,
                     "english": st["sentence_translations"].get(sid, ""), "verdict": verdict,
                     "jev": jev and {k: jev[k] for k in ("headword", "pos", "translation", "context")},
                     "jev_p": round(top[0][1], 2) if top else None,
                     "runner_up": (st["menu"].get(top[1][0], {"translation": top[1][0]})["translation"]
                                   if len(top) > 1 and top[1][1] >= 0.15 else None),
                     "live": old and {"headword": old["headword"], "pos": old["pos"],
                                      "translation": old.get("gloss_base") or old["translation"],
                                      "context": old.get("context", "")},
                     "menu_size": len(st["menu"])})
(RUN / "compare.json").write_text(json.dumps(rows, ensure_ascii=False, indent=1))
print(dict(stats), len(rows))
by = collections.defaultdict(collections.Counter)
for r in rows: by[r["surface"]][r["verdict"]] += 1
for w, c in sorted(by.items(), key=lambda kv: -sum(kv[1].values())): print(f"  {w:12s} {dict(c)}")
