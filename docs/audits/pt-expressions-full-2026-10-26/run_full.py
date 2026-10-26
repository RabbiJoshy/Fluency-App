#!/usr/bin/env python3
"""Re-ask DECIDE-1 Portuguese sentences that contain a newly matchable expression.

For every card, the inflecting matcher (decision 0034) over the recounted
inventory finds expressions in the card's sentences. An expression is offered
when it is not already on the menu and the menu does not already carry its
meaning (`expression_already_on_menu`, from the 2026-10-26 pilot). Only the
sentences that contain an offered expression are re-asked, each with only its
own expressions added, by the model that answered the card in DECIDE-1
(mercury-decide for the top 1,077 cards, Jev for the rest).

    python run_full.py          # plan and projected cost
    python run_full.py --run    # paid
"""
from __future__ import annotations

import argparse
import concurrent.futures as cf
import copy
import json
import random
import sys
import threading
import time
import urllib.error
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
WORKSPACE = REPO.parent / "Fluency-Workspace"
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO / "docs/audits/pt-wsd-mercury-2026-10-25"))

from fluency.wsd.multiword import (  # noqa: E402
    expression_already_on_menu, index_multiword_senses, load_expression_inflector, multiword_matches)

SETS = {"decide": WORKSPACE / "reviews/pt-top10000-decide-20261025",
        "jev": WORKSPACE / "reviews/pt-top10000-jev-remaining-20261025"}
INVENTORY = WORKSPACE / "raw/mwe/mwe-pt-20261026-v15-inflected/mwe_merged.json"
PARADIGMS = WORKSPACE / "cache/reflexives/forms-pt.json"
OUT = WORKSPACE / "reviews/pt-expressions-inflected-20261026"
CHARS_PER_TOKEN = 3.5
CAP_USD = 1.00


def plan_card(req: dict, index, inflector, inventory) -> dict | None:
    body = copy.deepcopy(req["body"])
    state = body["state"]
    menu = state["menu"]
    on_menu = {m["headword"] for m in menu.values()}
    glosses = [m["translation"] for m in menu.values() if m.get("pos") != "PHRASE"]
    offers: dict[str, list[str]] = {}
    for sid, text in state["sentences"].items():
        for entry, _ in multiword_matches(surface_form=req["surface"], sentence=text, index=index,
                                          inflector=inflector):
            e = entry.expression
            if e in on_menu or expression_already_on_menu(inventory[e]["translations"], glosses):
                continue
            offers.setdefault(sid, []).append(e)
    if not offers:
        return None
    keys: dict[str, str] = {}
    for expression in sorted({e for es in offers.values() for e in es}):
        key = str(len(menu) + 1)
        gloss = "; ".join(inventory[expression]["translations"][:2])
        menu[key] = {"sense_id": f"mwe:{expression}", "headword": expression, "pos": "PHRASE",
                     "translation": gloss, "meaning": gloss, "context": "fixed expression",
                     "definition_path": [gloss], "construction_frame": None, "tags": [], "regions": [],
                     "domains": [], "synonyms": [], "equivalent_choices": []}
        keys[expression] = key
    state["sentences"] = {sid: state["sentences"][sid] for sid in offers}
    if state.get("sentence_translations"):
        state["sentence_translations"] = {sid: state["sentence_translations"].get(sid) for sid in offers}
    body["questions"] = {sid: q for sid, q in body["questions"].items() if sid in offers}
    for sid, expressions in offers.items():
        for e in expressions:
            body["questions"][sid]["criteria"][keys[e]] = f"Sense {keys[e]} in the shared menu."
    return {"card_id": req["card_id"], "surface": req["surface"], "rank": req["rank"],
            "ids": list(offers), "offers": offers, "body": body}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", action="store_true")
    ap.add_argument("--workers", type=int, default=6)
    args = ap.parse_args()
    from run_decide import PROVIDERS, api_key
    inventory = json.loads(INVENTORY.read_text(encoding="utf-8"))["mwes"]
    index = index_multiword_senses({"mwes": inventory})
    inflector = load_expression_inflector(PARADIGMS)
    plans: dict[str, list[dict]] = {}
    for provider, folder in SETS.items():
        reqs = json.loads((folder / "requests.json").read_text(encoding="utf-8"))
        plans[provider] = [p for p in (plan_card(r, index, inflector, inventory) for r in reqs) if p]
    total_cost = 0.0
    for provider, items in plans.items():
        tokens = sum(len(json.dumps(p["body"])) for p in items) / CHARS_PER_TOKEN
        cost = tokens * PROVIDERS[provider][3]
        total_cost += cost
        print(f"{provider}: {len(items)} cards, {sum(len(p['ids']) for p in items):,} sentences, "
              f"~{tokens:,.0f} input tokens, ${cost:.3f}")
    print(f"projected ${total_cost:.3f} (cap ${CAP_USD})")
    OUT.mkdir(exist_ok=True)
    for provider, items in plans.items():
        (OUT / f"requests-{provider}.json").write_text(json.dumps(items, ensure_ascii=False), encoding="utf-8")
    if not args.run:
        return
    if total_cost > CAP_USD:
        raise SystemExit("over cap")
    for provider, items in plans.items():
        model, url, key_name, price_in, prefix = PROVIDERS[provider]
        key = api_key(key_name)
        raw = OUT / f"responses-{prefix}"
        raw.mkdir(exist_ok=True)
        lock, spent = threading.Lock(), [0.0]

        def call(item):
            cache = raw / f"{item['card_id']}.json"
            if cache.exists():
                return
            body = {**item["body"], "model": model}
            for attempt in range(10):
                try:
                    r = urllib.request.Request(url, data=json.dumps(body).encode(), method="POST", headers={
                        "Authorization": f"Bearer {key}", "Content-Type": "application/json"})
                    with urllib.request.urlopen(r, timeout=180) as f:
                        data = json.loads(f.read())
                    break
                except urllib.error.HTTPError as exc:
                    print(f"  {item['surface']} {exc.code}", flush=True)
                    time.sleep(random.uniform(1, 4) * (attempt + 1))
                except Exception as exc:  # noqa: BLE001
                    print(f"  {item['surface']} {exc}", flush=True)
                    time.sleep(random.uniform(1, 4) * (attempt + 1))
            else:
                return
            cache.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
            with lock:
                spent[0] += (data.get("usage") or {}).get("input_tokens", 0) * price_in
                if spent[0] > CAP_USD:
                    raise SystemExit(f"cap reached ${spent[0]:.3f}")

        with cf.ThreadPoolExecutor(args.workers) as pool:
            list(pool.map(call, items))
        print(f"{provider}: spent ${spent[0]:.4f}")


if __name__ == "__main__":
    main()
