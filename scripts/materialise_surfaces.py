#!/usr/bin/env python3
"""Fold the observation log into one file per language: the current view.

The log is the record and this is the answer -- surface, verdict, why, and
whatever morphology is known. It is derived, so it is safe to delete and
regenerate, and it records which events produced it. Nothing reads the raw log
in anger; stages read this.

    python scripts/materialise_surfaces.py --workspace <ws> --language cs
"""

from __future__ import annotations

import argparse, collections, json, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from fluency.surfaces.events import by_surface, read, scope, store_path  # noqa: E402
from fluency.surfaces.policy import load_policy, verdict  # noqa: E402

VIEW_VERSION = "surface-view/v1"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--workspace", type=Path, required=True)
    ap.add_argument("--language", required=True)
    ap.add_argument("--out", type=Path)
    args = ap.parse_args()
    ws, lang = args.workspace, args.language

    events = read(store_path(ws, lang))
    if not events:
        print(f"{lang}: no observations"); return 1
    grouped = by_surface(events)
    policy = load_policy(Path(__file__).resolve().parents[1] / f"config/surfaces/{lang}.json")

    ranks: dict[str, int] = {}
    supply: dict[str, dict] = {}
    marker = ws / f"runs/{lang}/speech/LATEST_V11"
    if marker.exists():
        run = ws / f"runs/{lang}/speech/{marker.read_text().strip()}"
        inv = json.loads((run / "stages/01_inventory/output/inventory.json").read_text())
        ranks = {c["display_form"]: c["rank"] for c in inv["cards"]}
        # What the harvest found, and what survived cleaning. Carrying both on
        # the surface is what lets one file answer "is this word worth a card"
        # -- the tags say whether it is a word, the counts say whether there is
        # anything to teach it with.
        pools = run / "stages/04_pools/output/pools.json"
        if pools.exists():
            for card in json.loads(pools.read_text())["cards"]:
                form = card.get("display_form")
                if not form:
                    continue
                items = card["candidates"]
                rejected = collections.Counter(
                    i["rejected_for"] for i in items if not i["eligible"]
                )
                sources = collections.Counter(
                    i["tags"]["source"] for i in items if i["eligible"]
                )
                # The ids, not the sentences. WSD joins them against the
                # sentence bank; duplicating 375,000 sentences into a per-surface
                # file would make this unreadable and immediately stale.
                # Eligible ids are ordered as the WSD cap will take them --
                # easiest first -- so the head of the list is what gets scored.
                order = sorted(
                    (i for i in items if i["eligible"]),
                    key=lambda i: (i["metrics"].get("score", float("inf")), i["sentence_id"]),
                )
                dropped: dict[str, list[str]] = {}
                for i in items:
                    if not i["eligible"]:
                        dropped.setdefault(i["rejected_for"] or "unknown", []).append(
                            i["sentence_id"])
                supply[form] = {
                    "harvested": len(items),
                    "eligible": len(order),
                    "rejected": {k: v for k, v in rejected.items() if k},
                    "eligible_by_source": dict(sources),
                    "eligible_sentence_ids": [i["sentence_id"] for i in order],
                    "rejected_sentence_ids": dropped,
                }
        else:
            cand = run / "stages/03_sentence_harvest/output/candidates.json"
            if cand.exists():
                by_card = {c["card_id"]: len(c.get("candidates", []))
                           for c in json.loads(cand.read_text())["cards"]}
                for c in inv["cards"]:
                    if c["card_id"] in by_card:
                        supply[c["display_form"]] = {
                            "harvested": by_card[c["card_id"]],
                            "eligible": None,
                            "rejected": {},
                            "eligible_by_source": {},
                        }

    # A surface with nothing recorded against it still belongs in the view:
    # a stage joining on this file should find every card, not have to treat a
    # miss as "keep". Silence is a verdict, and the commonest one.
    for surface in ranks:
        grouped.setdefault(surface, [])

    surfaces = {}
    for surface, items in sorted(grouped.items()):
        found = verdict(items, policy)
        lemmas, pos, evidence = [], [], {}
        candidates: list[str] = []
        for event in items:
            code, data = event["reason_code"], event.get("evidence") or {}
            if code in ("lemma_resolved", "lemma_is_headword"):
                rank_of = data.get("priority", 1)
                for lemma in data.get("lemmas") or []:
                    candidates.append((rank_of, lemma))
                pos = pos or data.get("pos") or []
            if data:
                evidence[code] = data
        # Several sources answer and they disagree, so the list is ordered
        # rather than reduced to one: the best answer leads and the rest stay
        # available, because the menu builder can follow every path while a
        # reader wants the likeliest first.
        # Closed-class self-lemma leads, except where the word also resolves to
        # a lemma that is itself core vocabulary. "é" carries an interjection
        # sense alongside being the third person of ser, and "je" is a pronoun
        # as well as a form of být -- so the closed-class test alone answered
        # "é" and "je", when at ranks 6 and 3 they are overwhelmingly the verb.
        # A resolved lemma inside the top of the list is the better answer; a
        # rare one, like unir behind the article "una", is not.
        # Promoting a frequent resolution above the closed-class self-lemma was
        # tried and is worse: it answers "é" with ser but also "no" with número,
        # "me" with yo and "la" with ella. Four orderings were tried and each
        # fixed one class while breaking another, which is the evidence that a
        # single correct lemma is not derivable here. So the list is ordered and
        # kept whole, and the residual cost is named: "é" and "je" lead with
        # their interjection and pronoun senses, with ser and být behind them.
        seen_lemma: set[str] = set()
        lemmas = []
        for _, lemma in sorted(candidates, key=lambda c: (c[0], ranks.get(c[1], 10**9), c[1])):
            if lemma not in seen_lemma:
                seen_lemma.add(lemma)
                lemmas.append(lemma)
        surfaces[surface] = {
            "surface": surface,
            "rank": ranks.get(surface),
            "verdict": found["verdict"],
            "reason_codes": found["reason_codes"],
            "tags": sorted({e["reason_code"] for e in items}),
            "lemmas": lemmas,
            "part_of_speech": pos,
            "evidence": evidence,
            "observations": len(items),
            # Split so a rerun can be reasoned about: the durable tags are
            # facts about the word and survive any harvest, while these two
            # depend on the corpus that was read.
            "durable_tags": sorted({e["reason_code"] for e in items
                                    if scope(e["reason_code"]) == "durable"}),
            "run_scoped_tags": sorted({e["reason_code"] for e in items
                                       if scope(e["reason_code"]) == "run_scoped"}),
            "supply": supply.get(surface),
        }
        # An excluded surface keeps its row -- the verdict and the reasons are
        # the point of it -- but not its sentences. Nothing downstream should
        # teach a word the list says is not a word, and carrying the ids invites
        # exactly that. The harvest counts stay, so the row still explains
        # itself.
        entry = surfaces[surface]
        if entry["verdict"] == "exclude" and entry["supply"]:
            entry["supply"] = {
                **entry["supply"],
                "eligible_sentence_ids": [],
                "rejected_sentence_ids": {},
                "sentences_withheld": "surface excluded",
            }

    out = args.out or (ws / f"raw/surfaces/{lang}/surfaces.json")
    out.parent.mkdir(parents=True, exist_ok=True)
    counts = collections.Counter(s["verdict"] for s in surfaces.values())
    out.write_text(json.dumps({
        "view_version": VIEW_VERSION,
        "language": lang,
        "derived_from": {"events": len(events), "surfaces": len(surfaces)},
        "summary": dict(counts),
        "surfaces": surfaces,
    }, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"{lang}: {len(surfaces):,} surfaces from {len(events):,} events -> {dict(counts)}")
    print(f"  with a lemma: {sum(1 for s in surfaces.values() if s['lemmas']):,}")
    have = [s["supply"] for s in surfaces.values() if s.get("supply")]
    if have:
        eligible = [s["eligible"] for s in have if s["eligible"] is not None]
        print(f"  with supply:  {len(have):,}  mean harvested "
              f"{sum(s['harvested'] for s in have)/len(have):.1f}"
              + (f", mean eligible {sum(eligible)/len(eligible):.1f}" if eligible else ""))
        thin = [s for s in eligible if s < 10]
        if eligible:
            print(f"  under 10 eligible: {len(thin):,}")
    print(f"  wrote {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
