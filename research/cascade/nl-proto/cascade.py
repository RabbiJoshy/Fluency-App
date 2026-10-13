"""Stage D: the WSD cascade on every selected sentence of a cascade card.

  Qwen3-Embedding-4B (DeepInfra) answers; e5-small (local) checks with the POS gate;
  where they disagree, DeepSeek V4.1 Flash decides, batched per card.
Inputs and query formats are the benchmark's (nl-benchmark/embed_score.py, 'inst').
Steps: embed [--spend] -> picks -> llm [--spend]. Outputs under $NL_PROTO.
"""
import json, os, sys, re, pickle
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import numpy as np
BENCH = Path("/Users/joshuathomasamar/PycharmProjects/Fluency-Next/research/cascade/nl-benchmark")
sys.path.insert(0, str(BENCH)); sys.path.insert(0, str(BENCH.parent))
import embed_score as E
from evaluate import BRIDGE
OUT = Path(os.environ["NL_PROTO"])
RUN = Path("/Users/joshuathomasamar/PycharmProjects/Fluency-Workspace/runs/nl/speech/20261012T175838Z-76d34ee3")
plan = json.loads((OUT / "plan.json").read_text())
# Main model. Qwen3-Embedding-8B was the benchmark's best but DeepInfra stopped answering
# its batched requests (2026-10-13); 4B is 1.1 points behind in the cascade and responsive.
PRIMARY = "qwen3-4b-di"
_fw = json.loads((OUT / "fw.json").read_text())["cards"] if (OUT / "fw.json").exists() else {}
# Function-word candidates the rules cannot label (pronouns, determiners) go through the cascade.
cards = [c for c in plan["cards"] if c["class"] == "cascade"
         or (c["class"] == "function_word_candidate" and c["card_id"] in _fw and not _fw[c["card_id"]]["keep"])]
menu = {c["card_id"]: [(a["part_of_speech"], a["headword"], s["sense_id"], s["translation"], a["menu_analysis_id"])
                       for a in c["analyses"] for s in a["senses"]]
        for c in json.loads((RUN / "stages/02_sense_menu/output/sense-menu.json").read_text())["cards"]}
need = {s for c in cards for s in c["selected"]}
bank = {}
for line in open(RUN / "stages/03_sentence_harvest/output/sentence-bank.jsonl"):
    r = json.loads(line)
    if r["sentence_id"] in need: bank[r["sentence_id"]] = (r["target"]["text"], r["translation"]["text"])

def rows():
    for c in cards:
        for sid in c["selected"]:
            text, en = bank[sid]
            m = re.search(r"(?<![\w'])" + re.escape(c["form"]) + r"(?![\w'])", text, re.I)
            span = [m.start(), m.end()] if m else [0, 0]
            yield c, sid, {"text": text, "translation": en, "span": span}

def store_for(key):
    """Vectors from the base file plus append-only shards (vec_<key>.part*.npz)."""
    p = OUT / f"vec_{key}.npz"
    store = dict(np.load(p, allow_pickle=True)["store"].item()) if p.exists() else {}
    for part in sorted(OUT.glob(f"vec_{key}.part*.npz")):
        store.update(np.load(part, allow_pickle=True)["store"].item())
    return p, store

def _embed_parallel(spec, texts, key, workers=4, per_request=96, per_shard=3000):
    """DeepInfra in parallel requests; each finished shard is its own file, so an
    interruption loses at most one shard and nothing is ever rewritten."""
    from concurrent.futures import ThreadPoolExecutor
    n0 = len(list(OUT.glob(f"vec_{key}.part*.npz")))
    for s0 in range(0, len(texts), per_shard):
        shard = texts[s0:s0 + per_shard]
        batches = [shard[i:i + per_request] for i in range(0, len(shard), per_request)]
        import time as _t
        t0 = _t.time()
        def one(b):
            v = E.embed(spec, b, True)
            print(f"    batch of {len(b)} done at +{_t.time() - t0:.0f}s", flush=True)
            return v
        with ThreadPoolExecutor(workers) as pool:
            vecs = list(pool.map(one, batches))
        part = {t: np.asarray(v, dtype=np.float32) for b, vs in zip(batches, vecs) for t, v in zip(b, vs)}
        np.savez(OUT / f"vec_{key}.part{n0:04d}.npz", store=np.array(part, dtype=object)); n0 += 1
        print(f"  {key}: {min(s0 + per_shard, len(texts))}/{len(texts)}", flush=True)

def embed(spend):
    for key, var in (("e5-small", "inst"), (PRIMARY, "inst")):
        spec = E.MODELS[key]; dp = spec[4]
        texts = {E.queries(r, spec)[var] for _, _, r in rows()} | {dp + s[3] for c in cards for s in menu[c["card_id"]]}
        p, store = store_for(key); missing = sorted(texts - set(store))
        print(f"{key}: {len(texts)} texts, {len(missing)} to embed")
        if not missing: continue
        if spec[0] != "local" and not spend:
            tok = sum(len(t) for t in missing) // 3
            print(f"  PAID {spec[1]}: ~{tok:,} tokens, ~${tok * spec[5] / 1e6:.4f} -- pass --spend"); continue
        if spec[0] != "local":
            _embed_parallel(spec, missing, key); continue
        for i in range(0, len(missing), 2000):
            chunk = missing[i:i + 2000]
            for t, v in zip(chunk, E.embed(spec, chunk, True)): store[t] = np.asarray(v, dtype=np.float32)
            np.savez(p, store=np.array(store, dtype=object)); print(f"  {key}: {min(i + 2000, len(missing))}/{len(missing)}", flush=True)

def picks():
    upos = {}
    for line in open(OUT / "parsed.jsonl"):
        r = json.loads(line)
        for x in r["rows"]: upos[(r["card_id"], x["sentence_id"])] = x["upos"]
    out = {}
    for key, var, gate in ((PRIMARY, "inst", False), ("e5-small", "inst", True)):
        spec = E.MODELS[key]; dp = spec[4]; _, store = store_for(key)
        for c, sid, r in rows():
            m = menu[c["card_id"]]; idx = list(range(len(m)))
            if gate:
                ok = [i for i in idx if m[i][0] in BRIDGE.get(upos.get((c["card_id"], sid)), set())]
                if ok: idx = ok
            q = store[E.queries(r, spec)[var]]
            sc = {i: float(q @ store[dp + m[i][3]]) for i in idx}
            best = sorted(sc, key=sc.get, reverse=True)
            out.setdefault((c["card_id"], sid), {})[key] = {"pick": m[best[0]][2], "margin": sc[best[0]] - (sc[best[1]] if len(best) > 1 else 0.0)}
    same = lambda cid, a, b: a == b or {s[2]: (s[0], s[3]) for s in menu[cid]}[a] == {s[2]: (s[0], s[3]) for s in menu[cid]}[b]
    with open(OUT / "picks.jsonl", "w") as f:
        for (cid, sid), v in out.items():
            v["primary"] = PRIMARY
            v["agree"] = same(cid, v[PRIMARY]["pick"], v["e5-small"]["pick"])
            f.write(json.dumps({"card_id": cid, "sentence_id": sid, **v}) + "\n")
    n = len(out); d = sum(not v["agree"] for v in out.values())
    print(f"{n} sentences; models disagree on {d} ({d / n:.0%}) -> DeepSeek")

def llm(spend):
    from compare import ask, api_key, PRICE_IN, PRICE_OUT
    P = [json.loads(l) for l in open(OUT / "picks.jsonl")]
    byc = {}
    for p in P:
        if not p["agree"]: byc.setdefault(p["card_id"], []).append(p["sentence_id"])
    path = OUT / "llm.jsonl"
    done = {json.loads(l)["card_id"] for l in open(path)} if path.exists() else set()
    form = {c["card_id"]: c["form"] for c in cards}
    calls = []
    for cid, sids in byc.items():
        if cid in done: continue
        for i in range(0, len(sids), 10):
            chunk = sids[i:i + 10]; m = menu[cid]
            senses = "\n".join(f"{k + 1}. ({s[1]}, {s[0]}) {s[3]}" for k, s in enumerate(m))
            parts = []
            for n, sid in enumerate(chunk):
                text, en = bank[sid]; mm = re.search(r"(?<![\w'])" + re.escape(form[cid]) + r"(?![\w'])", text, re.I)
                marked = text[:mm.start()] + "<<" + text[mm.start():mm.end()] + ">>" + text[mm.end():] if mm else text
                parts.append(f"[{n + 1}] Dutch: {marked}\nEnglish: {en}")
            calls.append((cid, chunk, f"Dictionary senses of the Dutch word \"{form[cid]}\":\n{senses}\n\nFor each numbered sentence, which "
                          "sense does the word marked <<like this>> have?\n\n" + "\n\n".join(parts) + "\n\nReply with JSON only: "
                          "{\"answers\": [{\"sentence\": <n>, \"choice\": <sense number>}, ...]} with one answer per sentence."))
    est_in = sum(len(p) for _, _, p in calls) / 3.5 + 40 * len(calls); est_out = 14 * sum(len(c) for _, c, _ in calls)
    print(f"{len(calls)} calls, {sum(len(c) for _, c, _ in calls)} sentences; projected ~{est_in:,.0f} in + ~{est_out:,.0f} out, ~${est_in / 1e6 * PRICE_IN + est_out / 1e6 * PRICE_OUT:.3f}")
    if not spend: return
    key = api_key(); tin = tout = 0
    def go(c):
        try: return ask(key, c[2])
        except Exception as e: return ({"error": str(e)}, {})
    with ThreadPoolExecutor(8) as pool, open(path, "a") as f:
        for (cid, chunk, _), (ans, u) in zip(calls, pool.map(go, calls)):
            tin += u.get("prompt_tokens", 0); tout += u.get("completion_tokens", 0)
            by = {a.get("sentence"): a.get("choice") for a in ans.get("answers", []) if isinstance(a, dict)}
            m = menu[cid]
            f.write(json.dumps({"card_id": cid, "picks": {sid: (m[by[n + 1] - 1][2] if isinstance(by.get(n + 1), int) and 1 <= by[n + 1] <= len(m) else None)
                                                          for n, sid in enumerate(chunk)}}) + "\n")
    print(f"actual {tin:,} in / {tout:,} out, ${tin / 1e6 * PRICE_IN + tout / 1e6 * PRICE_OUT:.4f}")

if __name__ == "__main__":
    step, spend = sys.argv[1], "--spend" in sys.argv
    {"embed": lambda: embed(spend), "picks": picks, "llm": lambda: llm(spend)}[step]()
