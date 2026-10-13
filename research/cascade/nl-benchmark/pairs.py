"""Escalation by disagreement: primary model answers; escalate when the second disagrees.

For each pair on the random stratum: share escalated, accuracy on what stays,
errors of the primary that escalation catches. Upper bound for the cascade
assumes the LLM is right on everything escalated (measured separately).
"""
import json, sys
from evaluate import labels, decide, correct
CFG = {  # scorer -> POS gate on/off (the better setting for that scorer on random)
    "emb_gemini-001_inst": False, "emb_gemini-001_nl": False, "emb_qwen3-8b-di_inst": False,
    "emb_qwen3-4b-di_inst": False, "emb_gemma-300m-di_en": True, "emb_labse_en": True,
    "emb_gte-ml-base_en": True, "emb_e5-small_inst": True, "emb_qwen3-0.6b-di_en": True,
    "qwen06_rerank": True, "emb_e5-large-instruct-di_inst": False, "emb_bge-m3-di_en": True,
}
def load(n): return {(r['sentence_id'], r['span'][0]): r for r in map(json.loads, open(f'results/{n}.jsonl'))}
def run(primaries, seconds, stratum="random"):
    keys = [k for k, l in labels.items() if l['stratum'] == stratum and l['verdict'] in ('fits', 'closest')]
    S = {n: load(n) for n in set(primaries) | set(seconds)}
    pick = {n: {k: decide(S[n][k], CFG[n])[0] for k in keys} for n in S}
    for a in primaries:
        ra = {k: correct(labels[k]['word'], pick[a][k], labels[k]) for k in keys}
        print(f"{a} alone: {sum(ra.values())}/{len(keys)} ({sum(ra.values())/len(keys):.0%})")
        for b in seconds:
            if a == b: continue
            esc = [k for k in keys if pick[a][k] != pick[b][k]]; stay = [k for k in keys if k not in esc]
            err = [k for k in keys if not ra[k]]
            caught = sum(k in esc for k in err)
            print(f"   + {b:30s} escalate {len(esc)/len(keys):4.0%}  stays right {sum(ra[k] for k in stay)/len(stay):4.0%}  "
                  f"catches {caught}/{len(err)} errors  ceiling {(sum(ra[k] for k in stay)+len(esc))/len(keys):.0%}")
if __name__ == "__main__":
    online = ["emb_gemini-001_inst", "emb_qwen3-8b-di_inst", "emb_qwen3-4b-di_inst"]
    offline = ["emb_labse_en", "emb_gemma-300m-di_en", "emb_gte-ml-base_en", "emb_e5-small_inst", "qwen06_rerank"]
    run(online, offline + online, sys.argv[1] if len(sys.argv) > 1 else "random")
