#!/usr/bin/env python3
"""Bad Bunny cards and selected lyric lines per Sankey branch -> WSD-Planning/bad-bunny-counts.json.

Menu kind from the v20 menu before WSD (plan.json, cap lifted): no menu / only hand-written
(declared slang or gloss) senses / one sense / several. "Once" = one line in Bad Bunny's corpus
(index corpus_count). Frequency tier = the surface's rank in OpenSubtitles es_50k.txt:
top 10,000 (the speech deck's range), 10,001-50,000, or absent from the list.
Menu source = the dictionaries among the card's senses (SpanishDict, Wiktionary or both);
a hand-written slang sense competing beside them is ignored.
"""
import collections, json
from pathlib import Path
REPO = Path(__file__).resolve().parents[3]
WS = REPO.parent / "Fluency-Workspace"
rank = {}
for i, line in enumerate((WS / "raw/frequency/frequencywords-opensubtitles-2018-es/es_50k.txt").open(), 1):
    rank.setdefault(line.split()[0], i)
plan = json.loads((WS / "reviews/bb-jev-20261101/plan.json").read_text())
live = WS / "releases/lyrics/lyrics-all-artists-v20-1/app/Artists/es/bad-bunny"
corpus = {r["id"]: r.get("corpus_count") or 0 for r in json.loads((live / "index.json").read_text())}
strategy = {k: v["resolution"]["strategy"] for k, v in json.loads((live / "vocabulary_master.json").read_text()).items()}
out = collections.defaultdict(lambda: {"cards": 0, "examples": 0})
for cid, card in plan.items():
    r = rank.get(card["surface"].lower().rstrip("'’"))
    tier = "top10k" if r and r <= 10000 else "mid50k" if r else "out50k"
    senses = card["senses"]
    if not senses or strategy[cid] == "no_menu": kind = "nomenu"
    elif all(s["source"].startswith("declared") for s in senses): kind = "slang"
    elif len(senses) == 1: kind = "mono"
    else: kind = "poly"
    keys = ["all", kind]
    if kind == "poly":
        once = "once" if corpus[cid] <= 1 else "repeat"
        dicts = {x["source"] for x in senses} & {"spanishdict", "wiktionary"}
        source = "both" if len(dicts) == 2 else (dicts.pop() if dicts else "other")
        keys += [once, f"{once}_{tier}", f"{once}_src_{source}", "jev"]
    for k in keys:
        out[k]["cards"] += 1
        out[k]["examples"] += len(card["examples"])
path = REPO / "WSD-Planning/bad-bunny-counts.json"
path.write_text(json.dumps(out, indent=1) + "\n")
print(json.dumps(out))
