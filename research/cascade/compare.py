"""CASCADE spot check: DeepSeek against the embedding pick on the router's top contenders.

Reads research/cascade/contenders.jsonl (router.py), takes the top families per
language (words sharing a first menu headword: nessa/neste/naquele -> em), and
from each the closest-call examples. DeepSeek chooses from exactly the leaves the
embedding stage chose from (the POS-supported analyses). Writes a side-by-side
page; it judges nothing itself.

    .venv/bin/python research/cascade/compare.py --workspace ../Fluency-Workspace          # plan + cost
    .venv/bin/python research/cascade/compare.py --workspace ../Fluency-Workspace --spend  # call DeepSeek
"""

from __future__ import annotations

import argparse
import html
import json
import math
import os
import re
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from collections import defaultdict
from pathlib import Path

from router import RUNS

HERE = Path(__file__).parent
MODEL = "deepseek-flash"  # DeepSeek-V4.1-Flash, the cheap tier (API model list, 2026-10-12)
# USD per million tokens (cache-miss input, output), peak rate; off-peak is half.
PRICE_IN, PRICE_OUT = 0.30, 1.20


def api_key() -> str:
    if os.environ.get("DEEPSEEK_API_KEY"):
        return os.environ["DEEPSEEK_API_KEY"]
    for line in (HERE.parents[1] / ".env").read_text().splitlines():
        k, _, v = line.partition("=")
        if k.strip() == "DEEPSEEK_API_KEY":
            return v.strip().strip('"').strip("'")
    raise SystemExit("DEEPSEEK_API_KEY not set")


def leaf_text(sense: dict) -> str:
    text = sense.get("translation") or sense.get("definition") or ""
    note = sense.get("definition") or ""
    if note and note != text:
        text += f" [{note}]"
    return text


def pick_examples(workspace: Path, lang: str, families: int, per_family: int, per_word: int):
    rows = [json.loads(l) for l in (HERE / "contenders.jsonl").open()]
    rows = [r for r in rows if r["language"] == lang]
    run = workspace / RUNS[lang]
    menu = json.loads((run / "stages/02_sense_menu/output/sense-menu.json").read_text())
    menus = {c["card_id"]: c for c in menu["cards"]}

    fams: dict[str, list] = defaultdict(list)
    for r in rows:
        analyses = menus[r["card_id"]]["analyses"]
        if not analyses:
            continue
        r["score"] = r["predicted_unsure_share"] * math.log1p(r["examples"])
        fams[analyses[0]["headword"]].append(r)
    chosen = sorted(fams.items(), key=lambda kv: -max(r["score"] for r in kv[1]))[:families]
    want = {r["card_id"]: fam for fam, rs in chosen for r in rs}

    # Lowest-margin embedding-decided examples for the chosen cards.
    cand = defaultdict(list)
    with (run / "stages/04_wsd_assignments/output/assignments.jsonl").open() as fh:
        for line in fh:
            if '"disambiguated"' not in line:
                continue
            r = json.loads(line)
            if r["card_id"] not in want or r.get("decision_kind") != "disambiguated":
                continue
            proj = (r.get("selection_projections") or {}).get("provider_only") or {}
            if proj.get("raw_margin") is None:
                continue
            cand[r["card_id"]].append(r)

    picked = []
    for fam, rs in chosen:
        got = 0
        for w in sorted(rs, key=lambda r: -r["score"]):
            exs = sorted(cand[w["card_id"]],
                         key=lambda r: r["selection_projections"]["provider_only"]["raw_margin"])
            for r in exs[:per_word]:
                if got >= per_family:
                    break
                picked.append((fam, r))
                got += 1
    sentences = {r["sentence_id"] for _, r in picked}
    bank = {}
    with (run / "stages/03_sentence_harvest/output/sentence-bank.jsonl").open() as fh:
        for line in fh:
            sid = line[line.find('"sentence_id":"') + 15:].split('"', 1)[0]
            if sid in sentences:
                s = json.loads(line)
                bank[sid] = (s["target"]["text"], (s.get("english") or s.get("translation") or {}).get("text", ""))

    items = []
    for fam, r in picked:
        card = menus[r["card_id"]]
        supported = set(r["evidence"]["candidate_preparation"]["constraint_supported_analysis_ids"])
        leaves = [(a, s) for a in card["analyses"] if a["menu_analysis_id"] in supported for s in a["senses"]]
        proj = r["selection_projections"]["provider_only"]
        text, eng = bank.get(r["sentence_id"], ("", ""))
        items.append({
            "language": lang, "family": fam, "surface": r["surface_form"],
            "sentence_id": r["sentence_id"], "text": text, "translation": eng,
            "margin": proj["raw_margin"],
            "leaves": [{"sense_id": s["sense_id"], "headword": a["headword"],
                        "pos": a["part_of_speech"], "gloss": leaf_text(s)} for a, s in leaves],
            "embedding_pick": proj["selected_sense_id"],
            "shipped_pick": r.get("selected_sense_id"),
        })
    return items


def prompt(item: dict) -> str:
    lines = [f"{i + 1}. ({l['headword']}, {l['pos']}) {l['gloss']}" for i, l in enumerate(item["leaves"])]
    return (
        f"Sentence ({item['language']}): {item['text']}\n"
        f"English: {item['translation']}\n"
        f"Target word: \"{item['surface']}\"\n\n"
        "Which dictionary sense does the target word have in this sentence?\n"
        + "\n".join(lines)
        + "\n\nReply with JSON only: {\"choice\": <number>, \"none_fit\": <true if no sense really fits>}"
    )


def ask(key: str, text: str) -> tuple[dict, dict]:
    body = json.dumps({
        "model": MODEL, "temperature": 0,
        "thinking": {"type": "disabled"},  # the cascade's LLM tier is the fast, cheap pass
        "response_format": {"type": "json_object"},
        "messages": [
            {"role": "system", "content": "You are a careful lexicographer doing word sense disambiguation."},
            {"role": "user", "content": text},
        ],
    }).encode()
    req = urllib.request.Request("https://api.deepseek.com/chat/completions", data=body, headers={
        "Content-Type": "application/json", "Authorization": f"Bearer {key}"})
    with urllib.request.urlopen(req, timeout=120) as resp:
        out = json.loads(resp.read())
    return json.loads(out["choices"][0]["message"]["content"]), out.get("usage", {})


def same(item: dict, a, b) -> bool:
    """Same sense, or the same gloss under a duplicated analysis (es VERB vs transitive verb)."""
    g = {l["sense_id"]: l["gloss"] for l in item["leaves"]}
    return a == b or (a in g and b in g and g[a] == g[b])


def page(items: list[dict]) -> str:
    def word_mark(text: str, surface: str) -> str:
        esc = html.escape(text)
        return re.sub(rf"(?i)(?<!\w)({re.escape(html.escape(surface))})(?!\w)", r"<mark>\1</mark>", esc, count=1)

    def gloss(item, sid):
        for l in item["leaves"]:
            if l["sense_id"] == sid:
                return f"{html.escape(l['gloss'])} <small>({html.escape(l['headword'])}, {html.escape(l['pos'])})</small>"
        return f"<small>{html.escape(str(sid))}</small>"

    agree = sum(same(i, i["embedding_pick"], i.get("deepseek_pick")) for i in items)
    out = [
        "<!doctype html><meta charset=utf-8><title>CASCADE spot check</title>",
        "<style>body{font:15px system-ui;max-width:900px;margin:24px auto;padding:0 16px}"
        ".it{border-top:1px solid #ccc;padding:10px 0}.s{font-size:17px}.en{color:#666}"
        ".diff{background:#fff6e0}td{vertical-align:top;padding:2px 8px}mark{background:#ffe08a}</style>",
        f"<h1>CASCADE spot check</h1><p>{len(items)} examples; DeepSeek agrees with the embedding pick on "
        f"{agree}. Disagreements are shaded.</p>",
    ]
    vpath = HERE / "verdicts.json"
    verdict = {}
    if vpath.exists():
        v = json.loads(vpath.read_text())
        verdict = {n: k for k in ("D", "E", "T") for n in v[k]}
        counts = {k: len(v[k]) for k in ("D", "E", "T")}
        out.append(f"<p>Claude's first pass on the disagreements (not blind): DeepSeek better {counts['D']}, "
                   f"embeddings better {counts['E']}, can't separate {counts['T']}.</p>")
    names = {"D": "DeepSeek better", "E": "embeddings better", "T": "can't separate"}
    fam = None
    for n, i in enumerate(items, 1):
        if (i["language"], i["family"]) != fam:
            fam = (i["language"], i["family"])
            out.append(f"<h2>{i['language']} · {html.escape(i['family'])}</h2>")
        diff = not same(i, i["embedding_pick"], i.get("deepseek_pick"))
        shipped = ""
        if i["shipped_pick"] not in (i["embedding_pick"], None):
            shipped = f"<tr><td>Shipped (after guards)</td><td>{gloss(i, i['shipped_pick'])}</td></tr>"
        nf = " <b>(says none fit)</b>" if i.get("deepseek_none_fit") else ""
        out.append(
            f"<div class='it{' diff' if diff else ''}'><div>#{n} <b>{html.escape(i['surface'])}</b> "
            f"· margin {i['margin']:.4f} · {len(i['leaves'])} senses"
            + (f" · <b>Claude: {names[verdict[n]]}</b>" if n in verdict else "") + "</div>"
            f"<div class=s>{word_mark(i['text'], i['surface'])}</div><div class=en>{html.escape(i['translation'])}</div>"
            f"<table><tr><td>Embeddings</td><td>{gloss(i, i['embedding_pick'])}</td></tr>"
            f"<tr><td>DeepSeek</td><td>{gloss(i, i.get('deepseek_pick'))}{nf}</td></tr>{shipped}</table></div>"
        )
    return "\n".join(out)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--workspace", type=Path, required=True)
    ap.add_argument("--families", type=int, default=8)
    ap.add_argument("--per-family", type=int, default=5)
    ap.add_argument("--per-word", type=int, default=2)
    ap.add_argument("--spend", action="store_true")
    ap.add_argument("--render", action="store_true", help="rebuild the page from spotcheck.jsonl")
    args = ap.parse_args()

    if args.render:
        return rerender()
    items = []
    for lang in RUNS:
        items += pick_examples(args.workspace, lang, args.families, args.per_family, args.per_word)
    prompts = [prompt(i) for i in items]
    est_in = sum(len(p) for p in prompts) / 3.5 + 30 * len(prompts)
    est_out = 15 * len(prompts)
    cost = est_in / 1e6 * PRICE_IN + est_out / 1e6 * PRICE_OUT
    print(f"{len(items)} examples, {len({(i['language'], i['family']) for i in items})} families")
    print(f"projected: {len(prompts)} {MODEL} calls, ~{est_in:,.0f} input + ~{est_out:,.0f} output tokens, ~${cost:.3f}")
    if not args.spend:
        print("dry run; pass --spend to call DeepSeek")
        print("\nexample prompt:\n" + prompts[0])
        return

    key = api_key()
    used_in = used_out = 0
    with ThreadPoolExecutor(max_workers=8) as pool:
        for i, (ans, usage) in zip(items, pool.map(lambda p: ask(key, p), prompts)):
            used_in += usage.get("prompt_tokens", 0)
            used_out += usage.get("completion_tokens", 0)
            c = ans.get("choice")
            i["deepseek_pick"] = i["leaves"][c - 1]["sense_id"] if isinstance(c, int) and 1 <= c <= len(i["leaves"]) else None
            i["deepseek_none_fit"] = bool(ans.get("none_fit"))
    print(f"actual: {used_in:,} input + {used_out:,} output tokens, "
          f"~${used_in / 1e6 * PRICE_IN + used_out / 1e6 * PRICE_OUT:.3f}")
    with (HERE / "spotcheck.jsonl").open("w") as fh:
        for i in items:
            fh.write(json.dumps(i, ensure_ascii=False) + "\n")
    (HERE / "spotcheck.html").write_text(page(items))
    agree = sum(same(i, i["embedding_pick"], i["deepseek_pick"]) for i in items)
    print(f"agree {agree}/{len(items)}; page: research/cascade/spotcheck.html")


def rerender() -> None:
    items = [json.loads(l) for l in (HERE / "spotcheck.jsonl").open()]
    (HERE / "spotcheck.html").write_text(page(items))


if __name__ == "__main__":
    main()
