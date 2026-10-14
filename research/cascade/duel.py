"""Head-to-head check: current sense vs DeepSeek's new sense, two options only.

A change from the 15-way pick survives only if DeepSeek, shown just the two
senses in random order, prefers its own pick. Batched by word.

    .venv/bin/python research/cascade/duel.py --workspace ../Fluency-Workspace --sample   # 60 judged items
    .venv/bin/python research/cascade/duel.py --workspace ../Fluency-Workspace --spend    # every change
"""

from __future__ import annotations

import argparse
import json
import random
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from compare import PRICE_IN, PRICE_OUT, api_key
from oneoff_pt import OUT

import urllib.request

MODEL = "deepseek-flash"
# Claude's verdicts on review.html's 60 (seeded) sample, by item number: B better, W worse.
SAMPLE_BETTER = {2, 5, 6, 7, 9, 13, 14, 15, 16, 17, 18, 24, 26, 27, 29, 31, 32, 37, 38, 39, 45, 46, 47,
                 48, 50, 51, 54, 55, 56, 57}
SAMPLE_WORSE = {3, 8, 30, 59, 60}


def ask(key: str, text: str) -> tuple[dict, dict]:
    body = json.dumps({"model": MODEL, "temperature": 0, "thinking": {"type": "disabled"},
                       "response_format": {"type": "json_object"},
                       "messages": [{"role": "system", "content": "You are a careful lexicographer."},
                                    {"role": "user", "content": text}]}).encode()
    req = urllib.request.Request("https://api.deepseek.com/chat/completions", data=body, headers={
        "Content-Type": "application/json", "Authorization": f"Bearer {key}"})
    with urllib.request.urlopen(req, timeout=120) as resp:
        out = json.loads(resp.read())
    return json.loads(out["choices"][0]["message"]["content"]), out.get("usage", {})


def gloss(leaf: dict) -> str:
    return f"({leaf['headword']}, {leaf['pos']}) {leaf['gloss']}"


def prompt(batch: list[dict]) -> str:
    parts = []
    for k, it in enumerate(batch, 1):
        parts.append(f"[{k}] Target word \"{it['surface']}\"\npt: {it['text']}\nEnglish: {it['translation']}\n"
                     f"  A: {it['_A']}\n  B: {it['_B']}")
    return ("For each sentence, which dictionary sense fits the target word better as it is used here? "
            "Prefer the sense a learner would recognise as the meaning in this sentence; do not prefer a "
            "sense just because it is more specific.\n\n" + "\n\n".join(parts) +
            "\n\nReply with JSON only: {\"answers\": [{\"sentence\": <n>, \"better\": \"A\" | \"B\" | \"same\"}, ...]}")


def load_changes(ws: Path, cut: int | None = None):
    """Meaning changes in results order. cut=80 reproduces the listing Claude judged by hand
    (it compared glosses truncated to 80 characters)."""
    items = []
    for line in (ws / OUT / "results.jsonl").open():
        call = json.loads(line)
        leaves = {l["sense_id"]: l for l in call["leaves"]}
        for it in call["items"]:
            new, old = it["deepseek_pick"], it["embedding_pick"]
            text = lambda sid: ((leaves.get(sid) or {}).get("gloss") or "")[:cut] if sid in leaves else None
            if new in (None, old) or text(new) == text(old):
                continue
            it["_old"] = gloss(leaves[old]) if old in leaves else str(old)
            it["_new"] = gloss(leaves[new])
            items.append(it)
    return items


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--workspace", type=Path, required=True)
    ap.add_argument("--sample", action="store_true")
    ap.add_argument("--spend", action="store_true")
    args = ap.parse_args()

    items = load_changes(args.workspace, cut=80 if args.sample else None)
    if args.sample:
        items = sorted(random.Random(1014).sample(items, 60), key=lambda it: it["rank"])
        for n, it in enumerate(items, 1):
            it["_n"] = n
    rng = random.Random(7)
    for it in items:
        it["_new_is"] = rng.choice("AB")
        it["_A"], it["_B"] = (it["_new"], it["_old"]) if it["_new_is"] == "A" else (it["_old"], it["_new"])
    groups = defaultdict(list)
    for it in items:
        groups[it["card_id"]].append(it)
    calls = [g[k:k + 15] for g in groups.values() for k in range(0, len(g), 15)]
    est = sum(len(prompt(b)) for b in calls) / 3.5
    print(f"{len(items):,} changes in {len(calls):,} calls; ~{est:,.0f} input tokens, "
          f"~${est / 1e6 * PRICE_IN + 12 * len(items) / 1e6 * PRICE_OUT:.3f} at peak")
    if not (args.spend or args.sample):
        return

    key = api_key()
    tin = tout = 0
    with ThreadPoolExecutor(max_workers=16) as pool:
        for batch, (ans, usage) in zip(calls, pool.map(lambda b: ask(key, prompt(b)), calls)):
            tin += usage.get("prompt_tokens", 0)
            tout += usage.get("completion_tokens", 0)
            by_n = {a.get("sentence"): a.get("better") for a in ans.get("answers", []) if isinstance(a, dict)}
            for k, it in enumerate(batch, 1):
                v = by_n.get(k)
                it["duel"] = "new" if v == it["_new_is"] else "same" if v == "same" else "old" if v in ("A", "B") else None
    print(f"actual ${tin / 1e6 * PRICE_IN + tout / 1e6 * PRICE_OUT:.3f}")
    keep = [it for it in items if it.get("duel") == "new"]
    print(f"duel: keep new {len(keep):,} | prefers old {sum(it.get('duel') == 'old' for it in items):,} | "
          f"same {sum(it.get('duel') == 'same' for it in items):,} | no answer {sum(it.get('duel') is None for it in items):,}")
    if args.sample:
        kb = sum(it["_n"] in SAMPLE_BETTER for it in keep)
        kw = sum(it["_n"] in SAMPLE_WORSE for it in keep)
        print(f"of Claude's 30 'better': kept {kb}; of the 5 'worse': kept {kw}; "
              f"of the 25 'too close': kept {len(keep) - kb - kw}")
        for it in items:
            tag = "B" if it["_n"] in SAMPLE_BETTER else "W" if it["_n"] in SAMPLE_WORSE else "T"
            if (tag == "B" and it.get("duel") != "new") or (tag == "W" and it.get("duel") == "new"):
                print(f"  #{it['_n']} [{tag}] {it['surface']}: duel says {it.get('duel')}")
        return
    with (args.workspace / OUT / "duel.jsonl").open("w") as fh:
        for it in items:
            fh.write(json.dumps({k: it[k] for k in ("card_id", "sentence_id", "embedding_pick", "deepseek_pick", "duel")},
                                ensure_ascii=False) + "\n")


if __name__ == "__main__":
    main()
