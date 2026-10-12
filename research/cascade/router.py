"""CASCADE router, first cut: which words will the embeddings be least sure about?

Unlabelled. The target is the embedding stage's own uncertainty, read from the
stored stage 04 picks: for each word, the share of its examples whose cosine
margin (best sense minus runner-up) falls in the language's bottom quartile.
Examples settled without embeddings (one sense, invariant phrase) count as sure.

The features are known before any sentence is embedded (menu shape, frequency,
closed-class POS), so the same model can route a new language like Dutch.

    .venv/bin/python research/cascade/router.py --workspace ../Fluency-Workspace
"""

from __future__ import annotations

import argparse
import json
import math
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.model_selection import cross_val_score

RUNS = {
    "es": "runs/es/speech/20261011T200847Z-353c3a7b",
    "pt": "runs/pt/speech/20261011T200523Z-53c7e6e2",
}
# Menu and spaCy POS labels for closed-class words, across SpanishDict (UD-ish)
# and Wiktionary (kaikki) spellings.
CLOSED = {
    "ADP", "DET", "PRON", "CCONJ", "SCONJ", "AUX", "PART", "CONJ",
    "prep", "article", "pron", "conj", "det", "contraction", "particle",
    "prep_phrase", "postp", "aux",
}
FEATURES = [
    "log_rank", "n_analyses", "n_senses", "max_senses_one_pos",
    "menu_closed_share", "observed_closed_share", "mean_live_leaves",
    "deterministic_share", "surface_len",
]


def load(workspace: Path, lang: str):
    run = workspace / RUNS[lang]
    inv = json.loads((run / "stages/01_inventory/output/inventory.json").read_text())
    menu = json.loads((run / "stages/02_sense_menu/output/sense-menu.json").read_text())
    words = {c["card_id"]: {"surface": c["surface_key"], "rank": c["rank"]} for c in inv["cards"]}
    for card in menu["cards"]:
        w = words.get(card["card_id"])
        if w is None:
            continue
        analyses = card.get("analyses") or []
        sizes = [len(a.get("senses") or []) for a in analyses]
        w["n_analyses"] = len(analyses)
        w["n_senses"] = sum(sizes)
        w["max_senses_one_pos"] = max(sizes, default=0)
        w["menu_closed_share"] = (
            sum(a.get("part_of_speech") in CLOSED for a in analyses) / len(analyses) if analyses else 0.0
        )

    margins: list[float] = []
    per = defaultdict(lambda: {"n": 0, "det": 0, "closed": 0, "leaves": [], "margins": []})
    path = run / "stages/04_wsd_assignments/output/assignments.jsonl"
    with path.open() as fh:
        for line in fh:
            r = json.loads(line)
            if r["status"] != "assigned":
                continue
            p = per[r["card_id"]]
            p["n"] += 1
            ev = r.get("evidence") or {}
            pos = (ev.get("occurrence_pos") or {}).get("observed_pos")
            p["closed"] += pos in CLOSED
            if r.get("decision_kind") != "disambiguated":
                p["det"] += 1
                continue
            proj = (r.get("selection_projections") or {}).get("provider_only") or {}
            m = proj.get("raw_margin")
            leaves = (ev.get("commit") or {}).get("candidate_leaf_count")
            if leaves is not None:
                p["leaves"].append(leaves)
            if m is not None:
                p["margins"].append(m)
                margins.append(m)
    cut = float(np.percentile(margins, 25))

    rows = []
    for cid, p in per.items():
        w = words.get(cid)
        if w is None or "n_analyses" not in w or p["n"] < 5:
            continue
        low = sum(m < cut for m in p["margins"])
        rows.append({
            "language": lang, "card_id": cid, "surface": w["surface"], "rank": w["rank"],
            "examples": p["n"],
            "log_rank": math.log(w["rank"]),
            "n_analyses": w["n_analyses"], "n_senses": w["n_senses"],
            "max_senses_one_pos": w["max_senses_one_pos"],
            "menu_closed_share": w["menu_closed_share"],
            "observed_closed_share": p["closed"] / p["n"],
            "mean_live_leaves": float(np.mean(p["leaves"])) if p["leaves"] else 1.0,
            "deterministic_share": p["det"] / p["n"],
            "surface_len": len(w["surface"]),
            "median_margin": float(np.median(p["margins"])) if p["margins"] else None,
            "unsure_share": low / p["n"],
        })
    return rows, cut


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--workspace", type=Path, required=True)
    ap.add_argument("--out", type=Path, default=Path("research/cascade/contenders.jsonl"))
    ap.add_argument("--top", type=int, default=25)
    args = ap.parse_args()

    rows = []
    for lang in RUNS:
        lang_rows, cut = load(args.workspace, lang)
        print(f"{lang}: {len(lang_rows)} words, bottom-quartile margin cut {cut:.4f}")
        rows += lang_rows

    X = np.array([[r[f] for f in FEATURES] for r in rows])
    y = np.array([r["unsure_share"] for r in rows])
    wts = np.array([r["examples"] for r in rows], dtype=float)
    model = GradientBoostingRegressor(n_estimators=300, max_depth=3, learning_rate=0.05,
                                      subsample=0.8, random_state=0)
    cv = cross_val_score(model, X, y, cv=5, scoring="r2", params={"sample_weight": wts})
    model.fit(X, y, sample_weight=wts)
    print(f"cross-validated R^2: {cv.mean():.2f} (folds {', '.join(f'{v:.2f}' for v in cv)})")
    print("feature importance:")
    for f, imp in sorted(zip(FEATURES, model.feature_importances_), key=lambda t: -t[1]):
        print(f"  {f:24s} {imp:.2f}")

    pred = model.predict(X)
    for r, p in zip(rows, pred):
        r["predicted_unsure_share"] = round(float(p), 4)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open("w") as fh:
        for r in sorted(rows, key=lambda r: -r["predicted_unsure_share"]):
            fh.write(json.dumps(r, ensure_ascii=False) + "\n")

    for lang in RUNS:
        # Weight by examples: a frequent unsure word costs more learner-facing errors.
        ranked = sorted((r for r in rows if r["language"] == lang),
                        key=lambda r: -r["predicted_unsure_share"] * math.log1p(r["examples"]))
        print(f"\n{lang} top {args.top} contenders (predicted / observed unsure share, senses, rank)")
        for r in ranked[: args.top]:
            print(f"  {r['surface']:14s} {r['predicted_unsure_share']:.2f} / {r['unsure_share']:.2f}"
                  f"  senses={r['n_senses']:3d} pos={r['n_analyses']} closed={r['menu_closed_share']:.1f}"
                  f"  rank={r['rank']}")


if __name__ == "__main__":
    main()
