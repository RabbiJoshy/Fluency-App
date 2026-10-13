"""Stage E: write the complete wsd-assignment-bundle/v1 for the Dutch prototype run.

Every harvested (card, sentence) pair gets one row:
  not selected by the 10-per-card cap -> not_evaluated_example_cap
  card without a menu                 -> no_menu
  one-sense menu                      -> assigned, deterministic_default
  function-word card (rules >= 6/10)  -> abstained from a sense, rule label in evidence.function_word
  every other card                    -> assigned by the cascade (Qwen3-4B agreed with e5-small,
                                         or DeepSeek decided); abstained if DeepSeek gave no answer
Provenance names this research prototype and every model it used; nothing claims Gemini or
the production executor. Output: Fluency-Workspace/raw/wsd/nl-cascade-proto-2/bundle.json
v2 (2026-10-13): pronouns and determiners labelled by rule too (labeller_nl.pron_det).
"""
import json, os, sys
from pathlib import Path
sys.path.insert(0, "/Users/joshuathomasamar/PycharmProjects/Fluency-Next/src")
from fluency.core.hashing import file_content_id, canonical_content_id
from fluency.wsd.contracts import WSDAssignment
W = Path("/Users/joshuathomasamar/PycharmProjects/Fluency-Workspace")
RUN = W / "runs/nl/speech/20261012T175838Z-76d34ee3"
OUT = Path(os.environ["NL_PROTO"])
HERE = Path(__file__).resolve().parent
plan = json.loads((OUT / "plan.json").read_text())
fw = json.loads((OUT / "fw.json").read_text())["cards"]
picks = {(r["card_id"], r["sentence_id"]): r for r in map(json.loads, open(OUT / "picks.jsonl"))}
llm = {}
for line in open(OUT / "llm.jsonl"):
    r = json.loads(line)
    for sid, p in r["picks"].items(): llm[(r["card_id"], sid)] = p
inputs = {name: file_content_id(path) for name, path in {
    "inventory": RUN / "stages/01_inventory/output/inventory.json",
    "sense_menu": RUN / "stages/02_sense_menu/output/sense-menu.json",
    "candidates": RUN / "stages/03_sentence_harvest/output/candidates.json",
    "sentence_bank": RUN / "stages/03_sentence_harvest/output/sentence-bank.jsonl"}.items()}
menu_cid = inputs["sense_menu"]
leaf = {}
for c in json.loads((RUN / "stages/02_sense_menu/output/sense-menu.json").read_text())["cards"]:
    leaf[c["card_id"]] = {s["sense_id"]: (a["menu_analysis_id"], a["headword"], a["part_of_speech"]) for a in c["analyses"] for s in a["senses"]}
code = [HERE / f for f in ("plan.py", "parse_label.py", "relabel.py", "cascade.py", "write_bundle.py")] + [
    HERE.parent / "trouble-words/labeller_nl.py", HERE.parent / "nl-benchmark/embed_score.py"]
REVS = {"gloss": "Qwen/Qwen3-Embedding-4B (DeepInfra)", "check": "intfloat/multilingual-e5-small@614241f622f53c4eeff9890bdc4f31cfecc418b3",
        "llm": "deepseek-flash (DeepSeek V4.1 Flash, thinking off)", "occurrence_pos": "stanza-nl-default@1.14.0"}
method = {"profile_id": "nl-cascade-proto-2", "implementation_version": "research.cascade.nl-proto/v2",
          "implementation_content_id": canonical_content_id({p.name: file_content_id(p) for p in code}),
          "model_revisions": REVS, "random_seed": 0}
cls = {c["card_id"]: c for c in plan["cards"]}
cands = json.loads((RUN / "stages/03_sentence_harvest/output/candidates.json").read_text())
rows, considered, selected_n = [], 0, 0
def row(cid, form, sid, status, **kw):
    base = dict(assignment_version="wsd-assignment/v1", card_id=cid, surface_form=form, sentence_id=sid, status=status,
                sense_menu_content_id=menu_cid, menu_analysis_id=None, selected_sense_id=None, selected_tuple=None,
                decision_path=[], evidence={}, confidence=None, model_revisions=REVS)
    base.update(kw); WSDAssignment.from_dict(base); return base
counts = {}
for card in cands["cards"]:
    cid, form = card["card_id"], card["display_form"]; c = cls[cid]; sel = set(c["selected"])
    for cand in card["candidates"]:
        sid = cand["sentence_id"]; considered += 1
        if c["class"] == "no_menu":
            r = row(cid, form, sid, "no_menu", sense_menu_content_id=None, model_revisions={})
        elif sid not in sel:
            r = row(cid, form, sid, "not_evaluated_example_cap", evidence={"reason": "per_surface_wsd_execution_cap", "cap_per_surface": 10})
        elif c["class"] == "single_sense":
            sense = next(iter(leaf[cid])); aid, hw, pos = leaf[cid][sense]
            r = row(cid, form, sid, "assigned", menu_analysis_id=aid, selected_sense_id=sense, selected_tuple={"headword": hw, "part_of_speech": pos},
                    decision_path=["commit"], decision_kind="deterministic_default", emitted_level="leaf",
                    evidence={"reason": "single_sense_menu", "cascade_tier": "bypass"})
        elif c["class"] == "function_word_candidate" and fw[cid]["keep"]:
            lab = fw[cid]["labels"].get(sid)
            ev = {"reason": "function_word_presentation", "cascade_tier": "rules"}
            if lab: ev["function_word"] = lab
            else: ev["reason"] = "function_word_presentation_unlabelled"
            r = row(cid, form, sid, "abstained", decision_path=["constrain"], evidence=ev)
        else:
            p = picks[(cid, sid)]
            tier = "embeddings_agree" if p["agree"] else "llm"
            prim = p["primary"]
            sense = p[prim]["pick"] if p["agree"] else llm.get((cid, sid))
            ev = {"cascade_tier": tier, "primary_model": prim, "primary_pick": p[prim]["pick"], "e5_small_pick": p["e5-small"]["pick"]}
            if not p["agree"]: ev["llm_pick"] = sense
            if sense is None:
                r = row(cid, form, sid, "abstained", decision_path=["gloss", "commit"], evidence={**ev, "reason": "llm_no_answer"})
            else:
                aid, hw, pos = leaf[cid][sense]
                r = row(cid, form, sid, "assigned", menu_analysis_id=aid, selected_sense_id=sense, selected_tuple={"headword": hw, "part_of_speech": pos},
                        decision_path=["gloss", "commit"], decision_kind="disambiguated", emitted_level="leaf", evidence=ev)
        if r["status"] != "not_evaluated_example_cap": selected_n += 1
        counts[r["status"]] = counts.get(r["status"], 0) + 1
        rows.append(r)
not_eval = considered - selected_n
bundle = {"bundle_version": "wsd-assignment-bundle/v1", "run_id": "20261012T175838Z-76d34ee3", "language": "nl", "mode": "speech",
          "coverage": "complete_candidate_pool", "method": method, "inputs": inputs, "assignments": rows,
          "sampling": {**{k: plan["policy"][k] for k in ()}, "policy": plan["policy"], "surface_cards": len(cands["cards"]),
                       "occurrences_considered": considered, "occurrences_selected": selected_n, "occurrences_not_evaluated": not_eval}}
dest = W / "raw/wsd/nl-cascade-proto-2"; dest.mkdir(parents=True, exist_ok=True)
(dest / "bundle.json").write_text(json.dumps(bundle, ensure_ascii=False))
print(counts, "->", dest / "bundle.json")
