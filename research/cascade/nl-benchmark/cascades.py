"""Measured cascades: primary answers, escalate to DeepSeek when the second model disagrees.

DeepSeek has answered every labelled sentence (results/llm_deepseek-flash.jsonl),
so any primary/second pairing is measured, not bounded.
"""
import json, itertools
from evaluate import labels, decide, correct
from pairs import load, CFG
L = {(r["sentence_id"], r["span0"]): r["pick"] for r in map(json.loads, open("results/llm_deepseek-flash.jsonl"))}
def ok(k, pick): return pick is not None and correct(labels[k]["word"], pick, labels[k])
def table(stratum):
    keys = [k for k, l in labels.items() if l["stratum"] == stratum and l["verdict"] in ("fits", "closest")]
    pick = {n: {k: decide(load(n)[k], CFG[n])[0] for k in keys} for n in CFG}
    print(f"\n{stratum} (n={len(keys)}): DeepSeek alone {sum(ok(k, L[k]) for k in keys)}")
    rows = []
    for a, b in itertools.permutations(CFG, 2):
        esc = [k for k in keys if pick[a][k] != pick[b][k]]
        acc = sum(ok(k, pick[a][k]) for k in keys if k not in esc) + sum(ok(k, L[k]) for k in esc)
        rows.append((acc, -len(esc), a, b, sum(ok(k, pick[a][k]) for k in keys)))
    for acc, ne, a, b, alone in sorted(rows, reverse=True)[:12]:
        print(f"  {a.replace('emb_',''):24s} alone {alone:3d}  + {b.replace('emb_',''):24s} escalate {-ne:3d}  cascade {acc} ({acc/len(keys):.0%})")
    return rows
if __name__ == "__main__":
    import sys
    for s in ("random", "hard"):
        rows = table(s)
        if s == "random":
            n = len([k for k, l in labels.items() if l["stratum"] == "random" and l["verdict"] in ("fits", "closest")])
            free = {"emb_labse_en", "emb_e5-small_inst", "emb_gemma-300m-di_en", "emb_gte-ml-base_en", "qwen06_rerank", "emb_bge-m3-di_en"}
            print("  best all-free-local pairs:")
            for acc, ne, a, b, alone in sorted([r for r in rows if r[2] in free and r[3] in free], reverse=True)[:5]:
                print(f"    {a.replace('emb_',''):24s} + {b.replace('emb_',''):24s} escalate {-ne:3d}  cascade {acc} ({acc/n:.0%})")
