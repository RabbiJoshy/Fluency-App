"""Batched DeepSeek calls: one sense list, up to 10 sentences per call.

Same contenders as compare.py, topped up with more close-call sentences of the
same words so batches reach a realistic size. The sense list goes first so
repeats can bill as cached input. Scored against compare.py's single-sentence
answers on the 78 examples in spotcheck.jsonl.

    .venv/bin/python research/cascade/batched.py --workspace ../Fluency-Workspace [--spend]
"""

from __future__ import annotations

import argparse
import json
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from compare import HERE, MODEL, PRICE_IN, PRICE_OUT, RUNS, api_key, ask, pick_examples, same

BATCH = 10
PRICE_CACHED = 0.006  # USD per million cache-hit input tokens, peak


def prompt(lang: str, leaves: list[dict], batch: list[dict]) -> str:
    menu = [f"{i + 1}. ({l['headword']}, {l['pos']}) {l['gloss']}" for i, l in enumerate(leaves)]
    sents = [
        f"[{k + 1}] Target word \"{it['surface']}\"\n{lang}: {it['text']}\nEnglish: {it['translation']}"
        for k, it in enumerate(batch)
    ]
    return (
        "Dictionary senses:\n" + "\n".join(menu)
        + "\n\nFor each numbered sentence, which sense does the target word have?\n\n"
        + "\n\n".join(sents)
        + "\n\nReply with JSON only: {\"answers\": [{\"sentence\": <n>, \"choice\": <sense number>, "
        "\"none_fit\": <true if no sense really fits>}, ...]} with one answer per sentence."
    )


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--workspace", type=Path, required=True)
    ap.add_argument("--spend", action="store_true")
    args = ap.parse_args()

    single = {(i["language"], i["sentence_id"], i["surface"]): i
              for i in map(json.loads, (HERE / "spotcheck.jsonl").open())}
    items = []
    for lang in RUNS:
        items += pick_examples(args.workspace, lang, families=8, per_family=10, per_word=4)
    # Make sure every judged example is in, whatever the top-up picked.
    have = {(i["language"], i["sentence_id"], i["surface"]) for i in items}
    items += [i for k, i in single.items() if k not in have]

    groups = defaultdict(list)
    for i in items:
        groups[(i["language"], tuple(l["sense_id"] for l in i["leaves"]))].append(i)
    calls = []
    for (lang, _), its in groups.items():
        for s in range(0, len(its), BATCH):
            batch = its[s:s + BATCH]
            calls.append((batch, prompt(lang, batch[0]["leaves"], batch)))

    est_in = sum(len(p) for _, p in calls) / 3.5 + 30 * len(calls)
    est_out = 25 * len(items)
    print(f"{len(items)} sentences ({sum(k in single for k in have) + len(single) - len(have & single.keys())} judged) "
          f"in {len(calls)} calls; mean batch {len(items) / len(calls):.1f}")
    print(f"projected: ~{est_in:,.0f} input + ~{est_out:,.0f} output tokens, "
          f"~${est_in / 1e6 * PRICE_IN + est_out / 1e6 * PRICE_OUT:.4f} with no cache hits")
    if not args.spend:
        print("dry run; pass --spend\n\nexample prompt:\n" + calls[0][1][:1500])
        return

    key = api_key()
    tin = tcached = tout = 0
    with ThreadPoolExecutor(max_workers=8) as pool:
        for (batch, _), (ans, usage) in zip(calls, pool.map(lambda c: ask(key, c[1]), calls)):
            tin += usage.get("prompt_cache_miss_tokens", usage.get("prompt_tokens", 0))
            tcached += usage.get("prompt_cache_hit_tokens", 0)
            tout += usage.get("completion_tokens", 0)
            by_n = {a.get("sentence"): a for a in ans.get("answers", []) if isinstance(a, dict)}
            for k, it in enumerate(batch, 1):
                c = (by_n.get(k) or {}).get("choice")
                ok = isinstance(c, int) and 1 <= c <= len(it["leaves"])
                it["batched_pick"] = it["leaves"][c - 1]["sense_id"] if ok else None
    cost = tin / 1e6 * PRICE_IN + tcached / 1e6 * PRICE_CACHED + tout / 1e6 * PRICE_OUT
    print(f"actual: {tin:,} uncached + {tcached:,} cached input, {tout:,} output; ${cost:.4f} "
          f"= ${cost / len(items) * 1000:.3f} per 1,000 sentences")

    judged = [(single[k], i) for i in items
              if (k := (i["language"], i["sentence_id"], i["surface"])) in single]
    missing = sum(i.get("batched_pick") is None for _, i in judged)
    agree = sum(same(s, s["deepseek_pick"], i["batched_pick"]) for s, i in judged)
    print(f"on the {len(judged)} judged: batched agrees with single-sentence DeepSeek on {agree}, "
          f"no answer on {missing}")
    with (HERE / "batched.jsonl").open("w") as fh:
        for s, i in judged:
            s = dict(s, batched_pick=i["batched_pick"])
            fh.write(json.dumps(s, ensure_ascii=False) + "\n")


if __name__ == "__main__":
    main()
