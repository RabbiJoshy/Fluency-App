"""Batched DeepSeek accuracy on the benchmark: one call per word, the benchmark sentence
hidden at a random position among 9 of the word's other sentences (from agree_sample),
same prompt as word_agreement.llm. Answers for the benchmark sentence are scored
against the hand labels and compared with the single-sentence answers.
Usage: batched_bench.py [--spend]
"""
import json, os, sys, random, pickle
from concurrent.futures import ThreadPoolExecutor
HERE = os.path.dirname(os.path.abspath(__file__))
SCRATCH = os.environ["NL_SCRATCH"]
sys.path.insert(0, os.path.join(HERE, ".."))
from compare import ask, api_key, PRICE_IN, PRICE_OUT
from evaluate import labels, correct, menus
OUT = os.path.join(HERE, "results", "llm_deepseek-flash_batched.jsonl")

def build():
    smp = json.load(open(os.path.join(SCRATCH, "agree_sample.json")))
    rnd = random.Random(20261015); calls = []
    for k, l in labels.items():
        if l["stratum"] != "random" or l["verdict"] == "unclear": continue
        w = l["word"]; items = smp[w][:9]
        pos = rnd.randrange(len(items) + 1)
        items = items[:pos] + [{"text": l["text"], "translation": l["translation"], "span": l["span"]}] + items[pos:]
        senses = "\n".join(f"{i + 1}. ({s[1]}, {s[0]}) {s[3]}" for i, s in enumerate(menus[w]))
        sents = "\n\n".join(f"[{n + 1}] Dutch: {it['text'][:it['span'][0]]}<<{it['text'][it['span'][0]:it['span'][1]]}>>"
                            f"{it['text'][it['span'][1]:]}\nEnglish: {it['translation']}" for n, it in enumerate(items))
        calls.append((k, pos + 1, f"Dictionary senses of the Dutch word \"{w}\":\n{senses}\n\nFor each numbered sentence, which "
                      f"sense does the word marked <<like this>> have?\n\n{sents}\n\nReply with JSON only: "
                      "{\"answers\": [{\"sentence\": <n>, \"choice\": <sense number>}, ...]} with one answer per sentence."))
    return calls

if __name__ == "__main__":
    calls = build()
    est_in = sum(len(p) for _, _, p in calls) / 3.5 + 40 * len(calls); est_out = 140 * len(calls)
    print(f"{len(calls)} calls; projected ~{est_in:,.0f} in + ~{est_out:,.0f} out tokens, "
          f"~${est_in / 1e6 * PRICE_IN + est_out / 1e6 * PRICE_OUT:.3f}")
    if "--spend" not in sys.argv: sys.exit()
    key = api_key(); tin = tout = 0
    with ThreadPoolExecutor(8) as pool, open(OUT, "w") as f:
        for (k, n, _), (ans, u) in zip(calls, pool.map(lambda c: ask(key, c[2]), calls)):
            tin += u.get("prompt_tokens", 0); tout += u.get("completion_tokens", 0)
            by = {a.get("sentence"): a.get("choice") for a in ans.get("answers", []) if isinstance(a, dict)}
            c = by.get(n); menu = menus[labels[k]["word"]]
            pick = menu[c - 1][2] if isinstance(c, int) and 1 <= c <= len(menu) else None
            f.write(json.dumps({"sentence_id": k[0], "span0": k[1], "pick": pick}) + "\n")
    print(f"actual {tin:,} in / {tout:,} out, ${tin / 1e6 * PRICE_IN + tout / 1e6 * PRICE_OUT:.4f}")
