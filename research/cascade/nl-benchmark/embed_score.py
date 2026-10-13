"""Embedding scorers on the Dutch benchmark: one recipe, many models.

Score = cosine(query vector, gloss vector), the production recipe
(wsd_execute.GlossScorer: sentence vs leaf.translation). Three query variants:
  nl   the Dutch sentence
  en   the English subtitle
  inst the Dutch sentence with the target marked <<like this>> plus the English,
       behind the model's own instruction/prefix format where it has one
Glosses are the menu translations, with the model's document prefix.

Backends: local (sentence-transformers), deepinfra (OpenAI-compatible), gemini.
Paid backends print projected tokens and cost before calling. Vectors are cached
per model in $NL_SCRATCH/vec/<model>.npz so a variant is never paid for twice.
Usage: embed_score.py <model-key> [--yes]
"""
import json, os, sys, time, pickle, hashlib
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
SCRATCH = os.environ["NL_SCRATCH"]
menus, _, _ = pickle.load(open(os.path.join(SCRATCH, "cache.pkl"), "rb"))
TASK = ("Given a Dutch sentence with one word marked between << and >>, retrieve the English "
        "dictionary sense of the marked word as it is used in that sentence")

def qwen_q(t): return f"Instruct: {TASK}\nQuery: {t}"
MODELS = {
    # key: (backend, model id, query format for inst, query prefix for nl/en, doc prefix, $ per 1M tokens)
    "gemini-001":        ("gemini", "gemini-embedding-001", None, "", "", 0.15),
    "qwen3-0.6b-di":     ("deepinfra", "Qwen/Qwen3-Embedding-0.6B", qwen_q, "", "", 0.01),
    "qwen3-4b-di":       ("deepinfra", "Qwen/Qwen3-Embedding-4B", qwen_q, "", "", 0.02),
    "qwen3-8b-di":       ("deepinfra", "Qwen/Qwen3-Embedding-8B", qwen_q, "", "", 0.01),
    "gemma-300m-di":     ("deepinfra", "google/embeddinggemma-300m", lambda t: f"task: search result | query: {TASK}: {t}",
                          "task: sentence similarity | query: ", "title: none | text: ", 0.002),
    "e5-large-instruct-di": ("deepinfra", "intfloat/multilingual-e5-large-instruct", lambda t: f"Instruct: {TASK}\nQuery: {t}", "", "", 0.01),
    "bge-m3-di":         ("deepinfra", "BAAI/bge-m3", None, "", "", 0.01),
    "e5-small":          ("local", "intfloat/multilingual-e5-small", lambda t: "query: " + t, "query: ", "passage: ", 0),
    "e5-large-instruct": ("local", "intfloat/multilingual-e5-large-instruct", lambda t: f"Instruct: {TASK}\nQuery: {t}", "", "", 0),
    "gte-ml-base":       ("local", "Alibaba-NLP/gte-multilingual-base", None, "", "", 0),
    "qwen3-0.6b-local":  ("local", "Qwen/Qwen3-Embedding-0.6B", qwen_q, "", "", 0),
    "bge-m3":            ("local", "BAAI/bge-m3", None, "", "", 0),
    "labse":             ("local", "sentence-transformers/LaBSE", None, "", "", 0),
}

def rows():
    for n in ("labels-random.jsonl", "labels-hard.jsonl"):
        for l in open(os.path.join(HERE, n)):
            yield json.loads(l)

def queries(r, spec):
    _, _, inst, qp, _, _ = spec
    a, b = r["span"]
    marked = r["text"][:a] + "<<" + r["text"][a:b] + ">>" + r["text"][b:] + "\nEnglish: " + r["translation"]
    return {"nl": qp + r["text"], "en": qp + r["translation"], "inst": inst(marked) if inst else qp + marked}

def _repair_gte_buffers(model):
    """gte-multilingual's remote code builds its position and rotary buffers at
    init; under transformers 5 the model is initialised on the meta device and
    those non-persistent buffers come back as garbage. Rebuild them."""
    import torch
    emb = model.embeddings
    emb.position_ids = torch.arange(emb.position_ids.shape[0])
    rope = emb.rotary_emb
    rope.inv_freq = 1.0 / (rope.base ** (torch.arange(0, rope.dim, 2).float() / rope.dim))
    rope._set_cos_sin_cache(rope.max_position_embeddings, rope.inv_freq.device, torch.float32)

def embed(spec, texts, yes):
    backend, mid, _, _, _, price = spec
    if backend == "local":
        from sentence_transformers import SentenceTransformer
        m = SentenceTransformer(mid, device="cpu", trust_remote_code=True)
        if "gte-multilingual" in mid:
            _repair_gte_buffers(m[0].auto_model)
        return m.encode(texts, normalize_embeddings=True, batch_size=32, show_progress_bar=False)
    tokens = sum(len(t) for t in texts) // 3  # generous: Dutch/English ~3-4 chars per token
    print(f"  PAID {backend} {mid}: {len(texts)} texts, ~{tokens:,} tokens, ~${tokens * price / 1e6:.5f}")
    if not yes:
        raise SystemExit("  not run: pass --yes after approval")
    env = dict((k.strip(), v) for k, v in (l.strip().split("=", 1) for l in open(os.path.join(HERE, "../../../.env")) if "=" in l and not l.startswith("#")))
    out = []
    if backend == "deepinfra":
        import requests
        key = env["DEEPINFRA_API_KEY"].strip().strip('"')
        for i in range(0, len(texts), 96):
            for attempt in range(8):  # DeepInfra answers 429 under load; back off and retry
                try:
                    resp = requests.post("https://api.deepinfra.com/v1/openai/embeddings",
                                         headers={"Authorization": f"Bearer {key}"},
                                         json={"model": mid, "input": texts[i:i + 96], "encoding_format": "float"}, timeout=120)
                except requests.exceptions.RequestException:
                    if attempt == 7: raise
                    time.sleep(2 ** attempt); continue
                if resp.status_code not in (429, 500, 502, 503, 504): break
                time.sleep(2 ** attempt)
            resp.raise_for_status()
            out += [d["embedding"] for d in sorted(resp.json()["data"], key=lambda d: d["index"])]
    else:
        from google import genai
        from google.genai import types
        client = genai.Client(api_key=env["GEMINI_API_KEY"].strip().strip('"'))
        for i in range(0, len(texts), 100):
            for attempt in range(10):  # per-minute quota: wait it out
                try:
                    resp = client.models.embed_content(model=mid, contents=texts[i:i + 100],
                                                       config=types.EmbedContentConfig(task_type="SEMANTIC_SIMILARITY"))
                    break
                except Exception as e:
                    if "429" not in str(e) or attempt == 9: raise
                    time.sleep(45)
            out += [e.values for e in resp.embeddings]
    v = np.asarray(out, dtype=np.float32)
    return v / np.linalg.norm(v, axis=1, keepdims=True)

def main():
    key = sys.argv[1]; yes = "--yes" in sys.argv
    spec = MODELS[key]; _, _, _, _, dp, _ = spec
    rs = list(rows())
    qs = [queries(r, spec) for r in rs]
    docs = sorted({dp + s[3] for r in rs for s in menus[r["word"]]})
    want = sorted({q for d in qs for q in d.values()} | set(docs))
    os.makedirs(os.path.join(SCRATCH, "vec"), exist_ok=True)
    path = os.path.join(SCRATCH, "vec", key + ".npz")
    store = dict(np.load(path, allow_pickle=True)["store"].item()) if os.path.exists(path) else {}
    missing = [t for t in want if t not in store]
    t0 = time.time()
    if missing:
        for t, v in zip(missing, embed(spec, missing, yes)):
            store[t] = np.asarray(v, dtype=np.float32)
        np.savez(path, store=np.array(store, dtype=object))
    dt = time.time() - t0
    os.makedirs(os.path.join(HERE, "results"), exist_ok=True)
    for var in ("nl", "en", "inst"):
        with open(os.path.join(HERE, "results", f"emb_{key}_{var}.jsonl"), "w") as f:
            for r, q in zip(rs, qs):
                qv = store[q[var]]
                f.write(json.dumps({"sentence_id": r["sentence_id"], "word": r["word"], "span": r["span"],
                                    "sense_ids": [s[2] for s in menus[r["word"]]],
                                    "scores": [float(qv @ store[dp + s[3]]) for s in menus[r["word"]]]}) + "\n")
    print(f"{key}: {len(missing)} new texts embedded in {dt:.1f}s ({len(want)} total)")

if __name__ == "__main__":
    main()
