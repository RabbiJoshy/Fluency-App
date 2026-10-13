"""LLM tier: DeepSeek V4.1 Flash (thinking off) on the sentences a cascade escalates.

Escalation rule under test: primary = Gemini (marked + English, no POS gate);
escalate when the Qwen3 0.6B reranker (POS gate) picks a different sense.
One call per sentence (each word appears once in the random stratum, so there is
nothing to batch). Answers saved to results/llm_deepseek-flash.jsonl.
Usage: llm_tier.py [--all] [--spend]   (--all: every labelled sentence; appends, skips done)
"""
import json, os, sys, pickle
from concurrent.futures import ThreadPoolExecutor
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from compare import ask, api_key, PRICE_IN, PRICE_OUT, MODEL
from evaluate import labels, decide, menus
from pairs import load, CFG
HERE = os.path.dirname(os.path.abspath(__file__))
PRIMARY, SECOND = "emb_gemini-001_inst", "qwen06_rerank"

def prompt(lab):
    menu = menus[lab["word"]]
    a, b = lab["span"]
    senses = "\n".join(f"{i + 1}. ({s[1]}, {s[0]}) {s[3]}" for i, s in enumerate(menu))
    marked = lab["text"][:a] + "<<" + lab["text"][a:b] + ">>" + lab["text"][b:]
    return ("Dictionary senses of the Dutch word \"" + lab["word"] + "\":\n" + senses +
            "\n\nWhich sense does the word marked <<like this>> have in this sentence?\n"
            f"Dutch: {marked}\nEnglish: {lab['translation']}\n\n"
            "Reply with JSON only: {\"choice\": <sense number>, \"none_fit\": <true if no sense really fits>}")

def escalated():
    P, Q = load(PRIMARY), load(SECOND)
    return [k for k, l in labels.items() if l["verdict"] != "unclear"
            and decide(P[k], CFG[PRIMARY])[0] != decide(Q[k], CFG[SECOND])[0]]

if __name__ == "__main__":
    done = set()
    out_path = os.path.join(HERE, "results", "llm_deepseek-flash.jsonl")
    if os.path.exists(out_path):
        done = {(r["sentence_id"], r["span0"]) for r in map(json.loads, open(out_path))}
    keys = escalated() if "--all" not in sys.argv else [k for k, l in labels.items() if l["verdict"] != "unclear"]
    keys = [k for k in keys if k not in done]
    prompts = {k: prompt(labels[k]) for k in keys}
    est_in = sum(len(p) for p in prompts.values()) / 3.5 + 40 * len(keys); est_out = 20 * len(keys)
    print(f"{len(keys)} escalated sentences ({sum(labels[k]['stratum']=='random' for k in keys)} random, "
          f"{sum(labels[k]['stratum']=='hard' for k in keys)} hard), {len(keys)} calls to {MODEL}")
    print(f"projected ~{est_in:,.0f} input + ~{est_out:,.0f} output tokens, ~${est_in/1e6*PRICE_IN + est_out/1e6*PRICE_OUT:.4f}")
    if "--spend" not in sys.argv:
        print("dry run\n" + next(iter(prompts.values()))); sys.exit()
    key = api_key()
    with ThreadPoolExecutor(8) as pool:
        res = list(pool.map(lambda k: ask(key, prompts[k]), keys))
    tin = sum(u.get("prompt_tokens", 0) for _, u in res); tout = sum(u.get("completion_tokens", 0) for _, u in res)
    print(f"actual {tin:,} in / {tout:,} out, ${tin/1e6*PRICE_IN + tout/1e6*PRICE_OUT:.4f}")
    with open(out_path, "a") as f:
        for k, (ans, _) in zip(keys, res):
            c = ans.get("choice"); menu = menus[labels[k]["word"]]
            pick = menu[c - 1][2] if isinstance(c, int) and 1 <= c <= len(menu) else None
            f.write(json.dumps({"sentence_id": k[0], "span0": k[1], "pick": pick, "none_fit": ans.get("none_fit")}) + "\n")
