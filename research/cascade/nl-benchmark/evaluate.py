"""Accuracy and escalation curves for every scorer in results/.

Gate: if any menu sense matches the Stanza part of speech, only those compete
(a sentence keeps its whole menu when none match). Margin = top-1 minus top-2
score among competing senses, ranked within each scorer; a lower margin is
escalated first. Gap and unclear items are excluded from accuracy.
"""
import json, os, sys, pickle, glob
HERE = os.path.dirname(os.path.abspath(__file__))
menus, _, _ = pickle.load(open(os.environ["NL_CACHE"], "rb"))
POS = json.load(open(os.path.join(HERE, "results", "_pos.json")))
BRIDGE = {"NOUN": {"noun"}, "PROPN": {"noun", "name"}, "VERB": {"verb"}, "AUX": {"verb"}, "ADJ": {"adj"},
          "ADV": {"adv"}, "ADP": {"prep", "adv", "postp"}, "DET": {"det", "article", "pron"},
          "PRON": {"pron", "det"}, "SCONJ": {"conj"}, "CCONJ": {"conj"}, "INTJ": {"intj"}, "NUM": {"num"}}
labels = {}
for n in ("labels-random.jsonl", "labels-hard.jsonl"):
    for l in open(os.path.join(HERE, n)):
        r = json.loads(l); labels[(r["sentence_id"], r["span"][0])] = r

def correct(word, pick, lab):
    """Right if picked, or if the learner would see exactly the same gloss text."""
    gloss = {s[2]: (s[0], s[3]) for s in menus[word]}
    return pick in lab["gold_sense_ids"] or gloss[pick] in {gloss[g] for g in lab["gold_sense_ids"]}

def decide(row, gate):
    menu = menus[row["word"]]; idx = list(range(len(menu)))
    if gate:
        p = POS.get(f"{row['sentence_id']}:{row['span'][0]}")
        ok = [i for i in idx if p and menu[i][0] in BRIDGE.get(p["upos"], set())]
        if ok: idx = ok
    ranked = sorted(idx, key=lambda i: -row["scores"][i])
    margin = row["scores"][ranked[0]] - row["scores"][ranked[1]] if len(ranked) > 1 else float("inf")
    return row["sense_ids"][ranked[0]], margin, len(ranked)

def report(name, gate):
    rows = [json.loads(l) for l in open(os.path.join(HERE, "results", f"{name}.jsonl"))]
    res = {}
    for stratum in ("random", "hard"):
        items = []
        for row in rows:
            lab = labels[(row["sentence_id"], row["span"][0])]
            if lab["stratum"] != stratum or lab["verdict"] not in ("fits", "closest"): continue
            pick, margin, n = decide(row, gate)
            items.append((margin, correct(row["word"], pick, lab), n == 1))
        acc = sum(c for _, c, _ in items) / len(items)
        res[stratum] = (len(items), acc, items)
    return res

def curve(items, fracs=(0.05, 0.10, 0.20, 0.30)):
    # forced (one competing sense) items never escalate
    order = sorted(items, key=lambda t: t[0])
    out = []
    for f in fracs:
        k = round(f * len(order)); kept = order[k:]
        errs = sum(not c for _, c, _ in order); caught = sum(not c for _, c, _ in order[:k])
        out.append(f"{int(f*100)}%→{sum(c for _, c, _ in kept)/len(kept):.0%} (catches {caught}/{errs})")
    return "  ".join(out)

def auroc(items):
    pos = [m for m, c, _ in items if not c]; neg = [m for m, c, _ in items if c]
    if not pos or not neg: return float("nan")
    return sum((p < n) + 0.5 * (p == n) for p in pos for n in neg) / (len(pos) * len(neg))

if __name__ == "__main__":
    names = sys.argv[1:] or sorted(os.path.basename(p)[:-6] for p in glob.glob(os.path.join(HERE, "results", "*.jsonl")))
    for name in names:
        for gate in (False, True):
            r = report(name, gate)
            n, acc, items = r["random"]; nh, acch, ih = r["hard"]
            print(f"{name:20s} gate={'Y' if gate else 'N'}  random {acc:.0%} (n={n})  hard {acch:.0%} (n={nh})  "
                  f"margin-AUROC {auroc(items):.2f}")
            if gate: print(f"{'':22s}escalate lowest-margin random: {curve(items)}")
