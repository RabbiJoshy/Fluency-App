"""Per-word easiness, measured: does a cheap model agree with the reference on a word's
other sentences, and does that predict the cheap model on the word's held-out sentence?

Offline, every card is built with the expensive method anyway, so the agreement rate
between a cheap model and that answer is free to compute per card. Here the reference
is DeepSeek V4.1 Flash; 10 further eligible sentences per benchmark word (never the
benchmark sentence), seed 20261014.

Steps (each resumable):
  sample    pick the extra sentences            -> $NL_SCRATCH/agree_sample.json
  pos       Stanza POS for them (POS gate)       -> $NL_SCRATCH/agree_pos.json
  llm       DeepSeek, one call per word          -> results/agree_llm.jsonl     (paid)
  embed     cheap models' picks                  -> results/agree_<model>.jsonl (paid only for DeepInfra)
  report    predictive power
Usage: word_agreement.py <step> [--spend]
"""
import json, os, sys, re, random, pickle
from concurrent.futures import ThreadPoolExecutor
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
SCRATCH = os.environ["NL_SCRATCH"]
menus, pools, bank = pickle.load(open(os.path.join(SCRATCH, "cache.pkl"), "rb"))
from evaluate import labels, decide, correct, BRIDGE
from pairs import load, CFG
N_EXTRA = 10
WORDS = sorted({l["word"] for l in labels.values() if l["stratum"] == "random"})
BENCH = {l["sentence_id"] for l in labels.values()}

def span_of(word, text):
    m = re.search(r"(?<![\w'])" + re.escape(word) + r"(?![\w'])", text, re.I)
    return [m.start(), m.end()] if m else None

def sample():
    rnd = random.Random(20261014); out = {}
    for w in WORDS:
        cand = [s for s in pools[w] if s not in BENCH and span_of(w, bank[s][0])]
        out[w] = [{"sid": s, "text": bank[s][0], "translation": bank[s][1], "span": span_of(w, bank[s][0])}
                  for s in rnd.sample(cand, min(N_EXTRA, len(cand)))]
    json.dump(out, open(os.path.join(SCRATCH, "agree_sample.json"), "w"), ensure_ascii=False)
    print(len(out), "words,", sum(len(v) for v in out.values()), "sentences")

def S(): return json.load(open(os.path.join(SCRATCH, "agree_sample.json")))

def pos():
    import stanza
    smp = S(); flat = [(w, it) for w, v in smp.items() for it in v]
    nlp = stanza.Pipeline("nl", processors="tokenize,mwt,pos,lemma,depparse", download_method=None, use_gpu=False, verbose=False)
    docs = nlp.bulk_process([stanza.Document([], text=it["text"]) for _, it in flat])
    out = {}
    for (w, it), d in zip(flat, docs):
        a, b = it["span"]
        for s in d.sentences:
            for tok in s.tokens:
                if tok.start_char <= a < tok.end_char:
                    out[f"{it['sid']}:{a}"] = tok.words[0].upos
    json.dump(out, open(os.path.join(SCRATCH, "agree_pos.json"), "w"))
    print(len(out), "tagged of", len(flat))

def llm(spend):
    sys.path.insert(0, os.path.join(HERE, ".."))
    from compare import ask, api_key, PRICE_IN, PRICE_OUT
    smp = S(); path = os.path.join(HERE, "results", "agree_llm.jsonl")
    done = {json.loads(l)["word"] for l in open(path)} if os.path.exists(path) else set()
    calls = []
    for w, items in smp.items():
        if w in done or not items: continue
        senses = "\n".join(f"{i + 1}. ({s[1]}, {s[0]}) {s[3]}" for i, s in enumerate(menus[w]))
        sents = "\n\n".join(f"[{k + 1}] Dutch: {it['text'][:it['span'][0]]}<<{it['text'][it['span'][0]:it['span'][1]]}>>"
                            f"{it['text'][it['span'][1]:]}\nEnglish: {it['translation']}" for k, it in enumerate(items))
        calls.append((w, f"Dictionary senses of the Dutch word \"{w}\":\n{senses}\n\nFor each numbered sentence, which "
                         f"sense does the word marked <<like this>> have?\n\n{sents}\n\nReply with JSON only: "
                         "{\"answers\": [{\"sentence\": <n>, \"choice\": <sense number>}, ...]} with one answer per sentence."))
    est_in = sum(len(p) for _, p in calls) / 3.5 + 40 * len(calls); est_out = 14 * sum(len(smp[w]) for w, _ in calls)
    print(f"{len(calls)} calls, {sum(len(smp[w]) for w, _ in calls)} sentences; projected ~{est_in:,.0f} in + ~{est_out:,.0f} out "
          f"tokens, ~${est_in / 1e6 * PRICE_IN + est_out / 1e6 * PRICE_OUT:.3f}")
    if not spend: print("dry run"); return
    key = api_key()
    with ThreadPoolExecutor(8) as pool, open(path, "a") as f:
        tin = tout = 0
        for (w, _), (ans, u) in zip(calls, pool.map(lambda c: ask(key, c[1]), calls)):
            tin += u.get("prompt_tokens", 0); tout += u.get("completion_tokens", 0)
            by = {a.get("sentence"): a.get("choice") for a in ans.get("answers", []) if isinstance(a, dict)}
            picks = []
            for k, it in enumerate(smp[w], 1):
                c = by.get(k); picks.append(menus[w][c - 1][2] if isinstance(c, int) and 1 <= c <= len(menus[w]) else None)
            f.write(json.dumps({"word": w, "picks": picks}) + "\n")
    print(f"actual {tin:,} in / {tout:,} out, ${tin / 1e6 * PRICE_IN + tout / 1e6 * PRICE_OUT:.4f}")

# cheap models: (embed_score model key, query variant, POS gate)
CHEAP = {"e5-small": ("e5-small", "inst", True), "labse": ("labse", "en", True),
         "gemma-300m-di": ("gemma-300m-di", "en", True), "bge-m3-di": ("bge-m3-di", "en", True),
         "gemini-001": ("gemini-001", "inst", False), "qwen3-8b-di": ("qwen3-8b-di", "inst", False)}

def embed(spend):
    import embed_score as E
    smp = S(); P = json.load(open(os.path.join(SCRATCH, "agree_pos.json")))
    for name, (key, var, gate) in CHEAP.items():
        spec = E.MODELS[key]; dp = spec[4]
        rows = [(w, it) for w, v in smp.items() for it in v]
        qs = [E.queries({"text": it["text"], "translation": it["translation"], "span": it["span"]}, spec)[var] for _, it in rows]
        docs = {dp + s[3] for w in smp for s in menus[w]}
        path = os.path.join(SCRATCH, "vec", key + ".npz")
        store = dict(np.load(path, allow_pickle=True)["store"].item()) if os.path.exists(path) else {}
        missing = sorted((set(qs) | docs) - set(store))
        if missing:
            if spec[0] != "local" and not spend:
                tok = sum(len(t) for t in missing) // 3
                print(f"{name}: would embed {len(missing)} texts, ~{tok:,} tokens, ~${tok * spec[5] / 1e6:.4f}"); continue
            for t, v in zip(missing, E.embed(spec, missing, True)): store[t] = np.asarray(v, dtype=np.float32)
            np.savez(path, store=np.array(store, dtype=object))
        out = {}
        for (w, it), q in zip(rows, qs):
            menu = menus[w]; idx = list(range(len(menu)))
            if gate:
                up = P.get(f"{it['sid']}:{it['span'][0]}")
                ok = [i for i in idx if menu[i][0] in BRIDGE.get(up, set())]
                if ok: idx = ok
            sc = {i: float(store[q] @ store[dp + menu[i][3]]) for i in idx}
            out.setdefault(w, []).append(menu[max(sc, key=sc.get)][2])
        with open(os.path.join(HERE, "results", f"agree_{name}.jsonl"), "w") as f:
            for w, picks in out.items(): f.write(json.dumps({"word": w, "picks": picks}) + "\n")
        print(f"{name}: picks for {len(out)} words")

def same(w, a, b):
    g = {s[2]: (s[0], s[3]) for s in menus[w]}
    return a is not None and b is not None and (a == b or g[a] == g[b])

def report():
    ref = {r["word"]: r["picks"] for r in map(json.loads, open(os.path.join(HERE, "results", "agree_llm.jsonl")))}
    keys = [k for k, l in labels.items() if l["stratum"] == "random" and l["verdict"] in ("fits", "closest")]
    bench = {"e5-small": "emb_e5-small_inst", "labse": "emb_labse_en", "gemma-300m-di": "emb_gemma-300m-di_en",
             "bge-m3-di": "emb_bge-m3-di_en", "gemini-001": "emb_gemini-001_inst", "qwen3-8b-di": "emb_qwen3-8b-di_inst"}
    for name in CHEAP:
        p = os.path.join(HERE, "results", f"agree_{name}.jsonl")
        if not os.path.exists(p): continue
        cheap = {r["word"]: r["picks"] for r in map(json.loads, open(p))}
        B = load(bench[name])
        rows = []
        for k in keys:
            w = labels[k]["word"]
            if w not in ref or w not in cheap: continue
            pairs = [(a, b) for a, b in zip(cheap[w], ref[w]) if b is not None]
            if not pairs: continue
            agree = sum(same(w, a, b) for a, b in pairs) / len(pairs)
            right = correct(w, decide(B[k], CFG[bench[name]])[0], labels[k])
            rows.append((agree, right))
        pos = [a for a, r in rows if r]; neg = [a for a, r in rows if not r]
        au = sum((p > n) + 0.5 * (p == n) for p in pos for n in neg) / (len(pos) * len(neg)) if neg else float("nan")
        line = f"{name:14s} n={len(rows)} right {sum(r for _, r in rows)/len(rows):.0%}  AUROC {au:.2f} |"
        for t in (1.0, 0.9, 0.8):
            sel = [r for a, r in rows if a >= t]
            line += f"  agree>={t:.0%}: {len(sel)/len(rows):3.0%} of words, {sum(sel)/max(1,len(sel)):.0%} right"
        print(line)

if __name__ == "__main__":
    step = sys.argv[1]; spend = "--spend" in sys.argv
    {"sample": sample, "pos": pos, "llm": lambda: llm(spend), "embed": lambda: embed(spend), "report": report}[step]()
