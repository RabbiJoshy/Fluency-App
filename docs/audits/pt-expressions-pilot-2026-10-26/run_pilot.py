#!/usr/bin/env python3
"""Pilot: does offering inflected expressions change Jev's answers? (decision 0034)

Takes DECIDE-1 requests for a few Portuguese inflected verb cards, finds the
expressions the inflecting matcher sees in each card's sentences, and asks
Jev twice per card: the original menu (baseline) and the same menu plus those
expressions (with). Same prompt, same sentences, same model, so a changed
answer comes from the expression being on the menu.

    python run_pilot.py            # print the projected cost and stop
    python run_pilot.py --run      # call Jev (paid)
"""
from __future__ import annotations

import argparse
import copy
import json
import sys
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
WORKSPACE = REPO.parent / "Fluency-Workspace"
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO / "docs/audits/pt-wsd-mercury-2026-10-25"))

from fluency.wsd.multiword import index_multiword_senses, load_expression_inflector, multiword_matches  # noqa: E402

CARDS = ["fico", "ficou", "fique", "tome", "toma", "tomou", "vale", "valeu", "presta", "acabou", "acabei",
         "acaba", "acabo", "tenho", "temos", "deixou"]
REVIEWS = WORKSPACE / "reviews"
INVENTORY = WORKSPACE / "raw/mwe/mwe-pt-20261003-v15/mwe_merged.json"
PARADIGMS = WORKSPACE / "cache/reflexives/forms-pt.json"
PRICE_PER_TOKEN = 0.042 / 1_000_000
CHARS_PER_TOKEN = 3.5
CAP_USD = 0.25


def load_requests() -> dict[str, dict]:
    found = {}
    for folder in ("pt-top10000-decide-20261025", "pt-top10000-jev-remaining-20261025"):
        for req in json.loads((REVIEWS / folder / "requests.json").read_text(encoding="utf-8")):
            if req["surface"] in CARDS:
                found[req["surface"]] = req
    return found


def with_expressions(req: dict, index, inflector, inventory) -> tuple[dict, dict[str, list[str]]]:
    body = copy.deepcopy(req["body"])
    state = body["state"]
    menu = state["menu"]
    present = {m["headword"] for m in menu.values()}
    matched: dict[str, list[str]] = {}
    for sid, text in state["sentences"].items():
        for entry, span in multiword_matches(surface_form=req["surface"], sentence=text, index=index,
                                             inflector=inflector):
            matched.setdefault(entry.expression, []).append(sid)
    for expression, sids in matched.items():
        if expression in present:
            continue
        key = str(len(menu) + 1)
        gloss = "; ".join(inventory["mwes"][expression]["translations"][:2])
        menu[key] = {"sense_id": f"mwe:{expression}", "headword": expression, "pos": "PHRASE",
                     "translation": gloss, "meaning": gloss, "context": "fixed expression",
                     "definition_path": [gloss], "construction_frame": None, "tags": [], "regions": [],
                     "domains": [], "synonyms": [], "equivalent_choices": []}
        # Offered only where the expression occurs, as the WSD runner does.
        for sid in sids:
            body["questions"][sid]["criteria"][key] = f"Sense {key} in the shared menu."
    return body, matched


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", action="store_true")
    args = ap.parse_args()
    inventory = json.loads(INVENTORY.read_text(encoding="utf-8"))
    index = index_multiword_senses(inventory)
    inflector = load_expression_inflector(PARADIGMS)
    reqs = load_requests()
    plans, chars = [], 0
    for surface in CARDS:
        req = reqs[surface]
        body, matched = with_expressions(req, index, inflector, inventory)
        if not matched:
            continue
        plans.append((req, body, matched))
        chars += len(json.dumps(req["body"])) + len(json.dumps(body))
    sentences = sum(len(r["ids"]) for r, _, _ in plans)
    cost = chars / CHARS_PER_TOKEN * PRICE_PER_TOKEN
    print(f"{len(plans)} cards, {sentences} sentences x 2 runs, ~{chars / CHARS_PER_TOKEN:,.0f} input tokens, "
          f"projected ${cost:.3f} (cap ${CAP_USD})")
    for req, _, matched in plans:
        print(f"  {req['surface']}: " + ", ".join(f"{e} ({len(s)})" for e, s in matched.items()))
    if not args.run:
        return
    if cost > CAP_USD:
        raise SystemExit("over cap")
    from run_decide import PROVIDERS, api_key
    model, url, key_name, price_in, _ = PROVIDERS["jev"]
    key = api_key(key_name)
    out = HERE / "responses"
    out.mkdir(exist_ok=True)

    def ask(body: dict) -> dict:
        body = {**body, "model": model}
        request = urllib.request.Request(url, data=json.dumps(body).encode(), method="POST",
                                         headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"})
        with urllib.request.urlopen(request, timeout=180) as handle:
            return json.loads(handle.read())

    spent = 0.0
    for req, body, matched in plans:
        for name, payload in (("baseline", req["body"]), ("with", body)):
            path = out / f"{req['surface']}-{name}.json"
            if not path.exists():
                data = ask(payload)
                path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
                spent += (data.get("usage") or {}).get("input_tokens", 0) * price_in
        (out / f"{req['surface']}-plan.json").write_text(json.dumps(
            {"menu": body["state"]["menu"], "sentences": body["state"]["sentences"],
             "translations": body["state"].get("sentence_translations"), "matched": matched},
            ensure_ascii=False), encoding="utf-8")
    print(f"spent ${spent:.4f}")


if __name__ == "__main__":
    main()
