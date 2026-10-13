"""Score every benchmark item against its full menu with one local scorer.

Writes results/<scorer>.jsonl: one row per item with a score per menu sense, so
accuracy and escalation signals can be computed afterwards without re-running.
Local models only (HF_HUB_OFFLINE); nothing is downloaded or paid for.
"""
import json, os, sys, pickle
os.environ.setdefault("HF_HUB_OFFLINE", "1")
HERE = os.path.dirname(os.path.abspath(__file__))
CACHE = sys.argv[2] if len(sys.argv) > 2 else os.environ["NL_CACHE"]
menus, pools, bank = pickle.load(open(CACHE, "rb"))

def items():
    for name in ("labels-random.jsonl", "labels-hard.jsonl"):
        for line in open(os.path.join(HERE, name)):
            yield json.loads(line)

def marked(r):
    a, b = r["span"]
    return r["text"][:a] + "<<" + r["text"][a:b] + ">>" + r["text"][b:]

def run_labse(rows, use_en=False):
    from sentence_transformers import SentenceTransformer
    m = SentenceTransformer("sentence-transformers/LaBSE", device="cpu")
    texts = sorted({(r["translation"] if use_en else r["text"]) for r in rows} |
                   {s[3] for r in rows for s in menus[r["word"]]})
    vec = dict(zip(texts, m.encode(texts, normalize_embeddings=True, batch_size=64)))
    out = []
    for r in rows:
        q = vec[r["translation"] if use_en else r["text"]]
        out.append([float(q @ vec[s[3]]) for s in menus[r["word"]]])
    return out

def run_gte(rows):
    import torch
    from transformers import AutoTokenizer, AutoModelForSequenceClassification
    name = "Alibaba-NLP/gte-multilingual-reranker-base"
    tok = AutoTokenizer.from_pretrained(name)
    m = AutoModelForSequenceClassification.from_pretrained(name, trust_remote_code=True, torch_dtype=torch.float32).eval()
    out = []
    for r in rows:
        q = f"Meaning of '{r['word']}' in: {marked(r)}"
        pairs = [[q, f"{s[1]} ({s[0]}): {s[3]}"] for s in menus[r["word"]]]
        with torch.no_grad():
            enc = tok(pairs, padding=True, truncation=True, max_length=512, return_tensors="pt")
            out.append(m(**enc).logits.view(-1).float().tolist())
    return out

def run_qwen(rows, size="0.6B", use_en=True):
    import torch
    from transformers import AutoTokenizer, AutoModelForCausalLM
    name = f"Qwen/Qwen3-Reranker-{size}"
    dev = "mps"
    tok = AutoTokenizer.from_pretrained(name, padding_side="left")
    m = AutoModelForCausalLM.from_pretrained(name, torch_dtype=torch.float16).to(dev).eval()
    yes, no = tok.convert_tokens_to_ids("yes"), tok.convert_tokens_to_ids("no")
    pre = ("<|im_start|>system\nJudge whether the Document meets the requirements based on the Query and the "
           "Instruct provided. Note that the answer can only be \"yes\" or \"no\".<|im_end|>\n<|im_start|>user\n")
    suf = "<|im_end|>\n<|im_start|>assistant\n<think>\n\n</think>\n\n"
    inst = ("Given a Dutch sentence with one word marked <<like this>>, judge whether the Document "
            "is the dictionary sense the marked word has in this sentence")
    out = []
    for r in rows:
        q = marked(r) + (f"\n(English: {r['translation']})" if use_en else "")
        texts = [pre + f"<Instruct>: {inst}\n<Query>: {q}\n<Document>: {s[1]} ({s[0]}): {s[3]}" + suf
                 for s in menus[r["word"]]]
        with torch.no_grad():
            enc = tok(texts, padding=True, return_tensors="pt").to(dev)
            last = m(**enc).logits[:, -1, :]
            lp = torch.log_softmax(torch.stack([last[:, no], last[:, yes]], 1).float(), 1)[:, 1]
        out.append(lp.exp().tolist())
    return out

SCORERS = {
    "first_sense": lambda rows: [[-i for i in range(len(menus[r["word"]]))] for r in rows],
    "labse_nl": lambda rows: run_labse(rows),
    "labse_en": lambda rows: run_labse(rows, use_en=True),
    "gte_rerank": run_gte,
    "qwen06_rerank": lambda rows: run_qwen(rows, "0.6B"),
    "qwen06_rerank_noen": lambda rows: run_qwen(rows, "0.6B", use_en=False),
    "qwen4b_rerank": lambda rows: run_qwen(rows, "4B"),
}

if __name__ == "__main__":
    import time
    name = sys.argv[1]
    rows = list(items())
    t = time.time()
    scores = SCORERS[name](rows)
    dt = time.time() - t
    os.makedirs(os.path.join(HERE, "results"), exist_ok=True)
    with open(os.path.join(HERE, "results", f"{name}.jsonl"), "w") as f:
        for r, s in zip(rows, scores):
            f.write(json.dumps({"sentence_id": r["sentence_id"], "word": r["word"], "span": r["span"],
                                "sense_ids": [x[2] for x in menus[r["word"]]], "scores": s}) + "\n")
    print(f"{name}: {len(rows)} items, {sum(len(menus[r['word']]) for r in rows)} pairs, {dt:.1f}s")
