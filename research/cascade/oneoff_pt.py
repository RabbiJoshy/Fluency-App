"""ONE-OFF (2026-10-14): DeepSeek Flash re-picks the riskiest Portuguese sense picks.

Not a method. Josh asked for a single quality pass on the live Portuguese deck
before sharing it. Reads the live run read-only and writes only to a side
folder; no run, stage, profile or release is touched.

Selection, by example: shown sentences of words ranked 1-4,000 that the
embeddings decided (one-sense words, phrases and grammar-word cards never reach
WSD), in the narrowest 40% of margins over all WSD sentences, minus rows a rule
decided (negative margin, closed-class ground, or shipped pick != embedding
pick). Why 40%: research/cascade/README.md, calibration 2026-10-14.

Batching, by word: one call per (card, POS-supported analyses), the sense list
once, up to 15 numbered sentences. Results append per call, so a rerun resumes.

    .venv/bin/python research/cascade/oneoff_pt.py --workspace ../Fluency-Workspace            # plan
    .venv/bin/python research/cascade/oneoff_pt.py --workspace ../Fluency-Workspace --limit 200 --spend
    .venv/bin/python research/cascade/oneoff_pt.py --workspace ../Fluency-Workspace --spend
"""

from __future__ import annotations

import argparse
import json
import time
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import numpy as np

from batched import PRICE_CACHED, prompt
from compare import MODEL, PRICE_IN, PRICE_OUT, api_key, ask, leaf_text

RUN = "runs/pt/speech/20261013T133630Z-12746d8c"
FW_LABELS = "raw/wsd/pt/fw1-function-word-labels.json"
OUT = "raw/wsd/pt/oneoff-deepseek-2026-10-14"
MAX_RANK, BAND, BATCH = 4000, 40, 15


def build(ws: Path):
    run = ws / RUN
    sel = json.loads((run / "stages/05_example_selection/output/selection.json").read_text())
    shown = {(c["card_id"], s["sentence_id"]) for c in sel["cards"] for s in c["selected"]}
    fw = json.loads((ws / FW_LABELS).read_text())["cards"]
    fwkeep = {cid for cid, c in fw.items() if c.get("keep")}
    rank = {c["card_id"]: c["rank"] for c in
            json.loads((run / "stages/01_inventory/output/inventory.json").read_text())["cards"]}
    rows = []
    with (run / "stages/04_wsd_assignments/output/assignments.jsonl").open() as fh:
        for line in fh:
            a = json.loads(line)
            if (a["card_id"], a["sentence_id"]) not in shown or a["card_id"] in fwkeep:
                continue
            if a["status"] != "assigned" or a.get("decision_kind") != "disambiguated":
                continue
            p = (a.get("selection_projections") or {}).get("provider_only") or {}
            if p.get("raw_margin") is None:
                continue
            rows.append(a)
    margins = np.array([a["selection_projections"]["provider_only"]["raw_margin"] for a in rows])
    cut = float(np.percentile(margins, BAND))

    picked, ruled = [], 0
    for a in rows:
        p = a["selection_projections"]["provider_only"]
        if p["raw_margin"] >= cut or rank[a["card_id"]] > MAX_RANK:
            continue
        if p["raw_margin"] < 0 or (a.get("evidence") or {}).get("ground") or a.get("selected_sense_id") != p["selected_sense_id"]:
            ruled += 1
            continue
        picked.append(a)

    menu = {c["card_id"]: c for c in json.loads((run / "stages/02_sense_menu/output/sense-menu.json").read_text())["cards"]}
    need = {a["sentence_id"] for a in picked}
    bank = {}
    with (run / "stages/03_sentence_harvest/output/sentence-bank.jsonl").open() as fh:
        for line in fh:
            sid = line[line.find('"sentence_id":"') + 15:].split('"', 1)[0]
            if sid in need:
                s = json.loads(line)
                bank[sid] = (s["target"]["text"], (s.get("english") or s.get("translation") or {}).get("text", ""))

    groups = defaultdict(list)
    for a in picked:
        sup = tuple(sorted(a["evidence"]["candidate_preparation"]["constraint_supported_analysis_ids"]))
        groups[(a["card_id"], sup)].append(a)
    calls = []
    for (cid, sup), items in sorted(groups.items(), key=lambda kv: rank[kv[0][0]]):
        leaves = [{"sense_id": s["sense_id"], "headword": an["headword"], "pos": an["part_of_speech"],
                   "gloss": leaf_text(s)} for an in menu[cid]["analyses"] if an["menu_analysis_id"] in sup
                  for s in an["senses"]]
        for k in range(0, len(items), BATCH):
            batch = []
            for a in items[k:k + BATCH]:
                t, e = bank[a["sentence_id"]]
                p = a["selection_projections"]["provider_only"]
                batch.append({"card_id": cid, "rank": rank[cid], "surface": a["surface_form"],
                              "sentence_id": a["sentence_id"], "text": t, "translation": e,
                              "margin": p["raw_margin"], "embedding_pick": p["selected_sense_id"],
                              "shipped_pick": a.get("selected_sense_id")})
            calls.append({"call_id": f"{cid}:{len(calls)}", "leaves": leaves, "items": batch})
    return calls, {"wsd_sentences": len(rows), "margin_cut": cut, "rule_decided_excluded": ruled,
                   "sentences": len(picked), "words": len({a["card_id"] for a in picked}), "calls": len(calls)}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--workspace", type=Path, required=True)
    ap.add_argument("--spend", action="store_true")
    ap.add_argument("--limit", type=int, help="only the first N calls (trial)")
    ap.add_argument("--workers", type=int, default=16)
    args = ap.parse_args()

    out = args.workspace / OUT
    calls, stats = build(args.workspace)
    est_in = sum(len(prompt("pt", c["leaves"], c["items"])) for c in calls) / 3.5 + 30 * len(calls)
    est_out = 22 * stats["sentences"]
    print(json.dumps(stats))
    print(f"projected: {len(calls):,} {MODEL} calls, ~{est_in:,.0f} input + ~{est_out:,.0f} output tokens, "
          f"~${est_in / 1e6 * PRICE_IN + est_out / 1e6 * PRICE_OUT:.2f} at peak (off-peak about half)")
    if not args.spend:
        return

    out.mkdir(parents=True, exist_ok=True)
    (out / "README.md").write_text(
        "# One-off DeepSeek re-pick of risky Portuguese sense picks (2026-10-14)\n\n"
        "Not a method and not read by the pipeline. Josh asked for a single quality pass before\n"
        "sharing the Portuguese deck. Script: `research/cascade/oneoff_pt.py` (Fluency-Next).\n"
        f"Source run (read-only): `{RUN}`. Model: {MODEL}, thinking off, temperature 0.\n\n"
        "`plan.json` is the selection; `results.jsonl` holds one line per call, appended as\n"
        "calls finish (`items[].deepseek_pick`, `usage`).\n")
    (out / "plan.json").write_text(json.dumps({**stats, "run": RUN, "model": MODEL, "max_rank": MAX_RANK,
                                               "band_percent": BAND, "batch": BATCH}, indent=1))
    res_path = out / "results.jsonl"
    done = set()
    if res_path.exists():
        done = {json.loads(l)["call_id"] for l in res_path.open()}
    todo = [c for c in calls if c["call_id"] not in done]
    if args.limit:
        todo = todo[: args.limit]
    print(f"{len(done):,} calls already done; running {len(todo):,}")

    key = api_key()

    def run_one(c):
        p = prompt("pt", c["leaves"], c["items"])
        for attempt in range(3):
            try:
                ans, usage = ask(key, p)
                break
            except Exception as e:  # network / rate limit: back off and retry
                if attempt == 2:
                    return c, None, {"error": repr(e)}
                time.sleep(5 * (attempt + 1))
        by_n = {x.get("sentence"): x for x in ans.get("answers", []) if isinstance(x, dict)}
        missing = []
        for k, it in enumerate(c["items"], 1):
            ch = (by_n.get(k) or {}).get("choice")
            ok = isinstance(ch, int) and 1 <= ch <= len(c["leaves"])
            it["deepseek_pick"] = c["leaves"][ch - 1]["sense_id"] if ok else None
            it["deepseek_none_fit"] = bool((by_n.get(k) or {}).get("none_fit"))
            if not ok:
                missing.append(it)
        for it in missing:  # one retry, alone
            try:
                a1, u1 = ask(key, prompt("pt", c["leaves"], [it]))
                ch = ((a1.get("answers") or [{}])[0]).get("choice")
                if isinstance(ch, int) and 1 <= ch <= len(c["leaves"]):
                    it["deepseek_pick"] = c["leaves"][ch - 1]["sense_id"]
                    it["retried"] = True
                for k in ("prompt_cache_hit_tokens", "prompt_cache_miss_tokens", "completion_tokens"):
                    usage[k] = usage.get(k, 0) + u1.get(k, 0)
            except Exception:
                pass
        return c, usage, None

    tin = tcache = tout = errors = n = 0
    t0 = time.time()
    with res_path.open("a") as fh, ThreadPoolExecutor(max_workers=args.workers) as pool:
        for c, usage, err in pool.map(run_one, todo):
            n += 1
            if err:
                errors += 1
                continue
            tin += usage.get("prompt_cache_miss_tokens", usage.get("prompt_tokens", 0))
            tcache += usage.get("prompt_cache_hit_tokens", 0)
            tout += usage.get("completion_tokens", 0)
            fh.write(json.dumps({"call_id": c["call_id"], "leaves": c["leaves"], "items": c["items"],
                                 "usage": usage}, ensure_ascii=False) + "\n")
            fh.flush()
            if n % 250 == 0:
                print(f"  {n:,}/{len(todo):,} calls, {time.time() - t0:.0f}s", flush=True)
    cost = tin / 1e6 * PRICE_IN + tcache / 1e6 * PRICE_CACHED + tout / 1e6 * PRICE_OUT
    print(f"done {n - errors:,} calls ({errors} failed, rerun to retry) in {time.time() - t0:.0f}s; "
          f"{tin:,} uncached + {tcache:,} cached in, {tout:,} out; ${cost:.3f} at peak rates")


if __name__ == "__main__":
    main()
