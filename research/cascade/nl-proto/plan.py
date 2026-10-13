"""Stage A/B of the Dutch prototype bundle: sample exactly as production, classify cards.

Writes $NL_PROTO/plan.json: per card its rank, class (no_menu | single_sense |
function_word_candidate | cascade | outside_rank_limit) and the selected sentence ids.
Function-word candidates are confirmed later by label coverage (>= 6 of 10).
"""
import json, os, sys
sys.path.insert(0, "/Users/joshuathomasamar/PycharmProjects/Fluency-Next/src")
from fluency.wsd.sampling import OccurrenceSamplingPolicy, select_occurrences
from fluency.surfaces.ledger import ledger_path
from pathlib import Path
W = Path("/Users/joshuathomasamar/PycharmProjects/Fluency-Workspace")
RUN = W / "runs/nl/speech/20261012T175838Z-76d34ee3"
OUT = Path(os.environ["NL_PROTO"]); OUT.mkdir(parents=True, exist_ok=True)
RANK_LIMIT = 6000  # all cards: an unprocessed card would show no examples once WSD has run
CLOSED = {"article", "det", "pron", "prep", "conj", "particle", "postp"}
EXTRA = {"er", "te", "op", "aan", "uit", "mee", "af", "toe", "om", "in", "door", "over", "terug", "weg", "bij", "na"}

cands = json.loads((RUN / "stages/03_sentence_harvest/output/candidates.json").read_text())
menu = {c["card_id"]: c for c in json.loads((RUN / "stages/02_sense_menu/output/sense-menu.json").read_text())["cards"]}
pools = json.loads((RUN / "stages/04_pools/output/pools.json").read_text())
ineligible = {str(e["sentence_id"]) for c in pools["cards"] for e in c["candidates"] if not e.get("eligible", True)}
rank = {c["card_id"]: c["rank"] for c in json.loads((RUN / "stages/01_inventory/output/inventory.json").read_text())["cards"]}
ledger = json.loads(ledger_path(W, "nl").read_text())["surfaces"]
policy = OccurrenceSamplingPolicy(cap_per_surface=10)
plan = {"policy": policy.to_dict(), "rank_limit": RANK_LIMIT, "cards": []}
counts = {}
for card in cands["cards"]:
    cid, form = card["card_id"], card["display_form"]
    entry = ledger.get(form); preferred = None
    if entry is not None:
        if entry.get("verdict") == "exclude": preferred = ()
        elif (entry.get("supply") or {}).get("eligible_sentence_ids") is not None: preferred = entry["supply"]["eligible_sentence_ids"]
    sel = select_occurrences(card["candidates"], policy, card_id=cid, ineligible=ineligible, preferred_order=preferred)
    m = menu.get(cid, {"analyses": []}); n_senses = sum(len(a["senses"]) for a in m["analyses"])
    pos = {a["part_of_speech"] for a in m["analyses"]}
    if rank[cid] > RANK_LIMIT: cls = "outside_rank_limit"
    elif not m["analyses"]: cls = "no_menu"
    elif n_senses == 1: cls = "single_sense"
    elif pos & CLOSED or form in EXTRA: cls = "function_word_candidate"
    else: cls = "cascade"
    counts[cls] = counts.get(cls, 0) + 1
    plan["cards"].append({"card_id": cid, "form": form, "rank": rank[cid], "class": cls,
                          "selected": list(sel.selected), "overflow": list(sel.overflow)})
(OUT / "plan.json").write_text(json.dumps(plan))
sel_n = {k: sum(len(c["selected"]) for c in plan["cards"] if c["class"] == k) for k in counts}
print(counts); print("selected sentences by class:", sel_n)
