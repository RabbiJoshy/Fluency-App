"""Can a per-word score, computed offline from the menu alone, predict where a cheap model is right?

Features per word (no labels used):
  senses      menu size
  pos_max     largest number of senses sharing one part of speech
  sep_any     smallest cosine distance between any two distinct glosses (model's own vectors)
  sep_pos     same, only between senses of the same part of speech (inf if none)
Each is scored by AUROC for predicting 'cheap model right' on the random stratum, then
as a routing curve: keep the easiest X% of words on the cheap model, what accuracy there.
"""
import json, os, sys, pickle, itertools
import numpy as np
from evaluate import labels, decide, correct, menus
from pairs import load, CFG
SCRATCH = os.environ["NL_SCRATCH"]
MODEL = {"emb_e5-small_inst": ("e5-small", "passage: "), "emb_labse_en": ("labse", ""),
         "emb_gemma-300m-di_en": ("gemma-300m-di", "title: none | text: "), "emb_gemini-001_inst": ("gemini-001", "")}

def features(word, store, dp):
    menu = menus[word]
    glosses = {}
    for s in menu: glosses.setdefault((s[0], s[3]), store[dp + s[3]])
    items = list(glosses.items())
    def mind(pairs):
        d = [1 - float(va @ vb) for (ka, va), (kb, vb) in pairs if ka[1] != kb[1]]
        return min(d) if d else 2.0
    pos_counts = {}
    for s in menu: pos_counts[s[0]] = pos_counts.get(s[0], 0) + 1
    return {"senses": -len(menu), "pos_max": -max(pos_counts.values()),
            "sep_any": mind(itertools.combinations(items, 2)),
            "sep_pos": mind([p for p in itertools.combinations(items, 2) if p[0][0][0] == p[1][0][0]])}

def auroc(score, good):
    pos = [s for s, g in zip(score, good) if g]; neg = [s for s, g in zip(score, good) if not g]
    return sum((p > n) + 0.5 * (p == n) for p in pos for n in neg) / (len(pos) * len(neg))

if __name__ == "__main__":
    keys = [k for k, l in labels.items() if l["stratum"] == "random" and l["verdict"] in ("fits", "closest")]
    for scorer, (vkey, dp) in MODEL.items():
        store = dict(np.load(os.path.join(SCRATCH, "vec", vkey + ".npz"), allow_pickle=True)["store"].item())
        S = load(scorer)
        good = [correct(labels[k]["word"], decide(S[k], CFG[scorer])[0], labels[k]) for k in keys]
        F = [features(labels[k]["word"], store, dp) for k in keys]
        print(f"\n{scorer}: right {sum(good)}/{len(keys)}")
        for f in ("senses", "pos_max", "sep_any", "sep_pos"):
            sc = [x[f] for x in F]
            order = sorted(range(len(keys)), key=lambda i: -sc[i])
            curve = "  ".join(f"easiest {p}%: {sum(good[i] for i in order[:round(p/100*len(keys))])/round(p/100*len(keys)):.0%}"
                              for p in (25, 50, 75))
            print(f"  {f:8s} AUROC {auroc(sc, good):.2f}   {curve}")
