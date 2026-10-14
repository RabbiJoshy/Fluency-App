"""Review page for the 2026-10-14 one-off: a random sample of what DeepSeek would change.

    .venv/bin/python research/cascade/oneoff_review.py --workspace ../Fluency-Workspace [--n 60]
"""

from __future__ import annotations

import argparse
import html
import json
import random
import re
from pathlib import Path

from oneoff_pt import OUT


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--workspace", type=Path, required=True)
    ap.add_argument("--n", type=int, default=60)
    args = ap.parse_args()
    out = args.workspace / OUT

    items = []
    for line in (out / "results.jsonl").open():
        call = json.loads(line)
        gloss = {l["sense_id"]: l for l in call["leaves"]}
        for it in call["items"]:
            it["_g"] = gloss
            items.append(it)
    total = len(items)
    none = sum(it["deepseek_pick"] is None for it in items)
    same_id = sum(it["deepseek_pick"] == it["embedding_pick"] for it in items)

    def text(it, sid):
        l = it["_g"].get(sid)
        return l["gloss"] if l else None

    same_text = [it for it in items if it["deepseek_pick"] not in (None, it["embedding_pick"])
                 and text(it, it["deepseek_pick"]) == text(it, it["embedding_pick"])]
    changed = [it for it in items if it["deepseek_pick"] not in (None, it["embedding_pick"])
               and text(it, it["deepseek_pick"]) != text(it, it["embedding_pick"])]
    rng = random.Random(1014)
    sample = sorted(rng.sample(changed, min(args.n, len(changed))), key=lambda it: it["rank"])

    def g(it, sid):
        l = it["_g"].get(sid)
        if not l:
            return html.escape(str(sid))
        return f"{html.escape(l['gloss'])} <small>({html.escape(l['headword'])}, {html.escape(l['pos'])})</small>"

    def mark(t, w):
        e = html.escape(t)
        return re.sub(rf"(?i)(?<!\w)({re.escape(html.escape(w))})(?!\w)", r"<mark>\1</mark>", e, count=1)

    rows = "\n".join(
        f"<div class=it><div class=h>#{n} <b>{html.escape(it['surface'])}</b> · word {it['rank']}"
        f" · margin {it['margin']:.4f}</div><div class=s>{mark(it['text'], it['surface'])}</div>"
        f"<div class=en>{html.escape(it['translation'])}</div>"
        f"<table><tr><td class=k>Now</td><td>{g(it, it['embedding_pick'])}</td></tr>"
        f"<tr><td class=k>DeepSeek</td><td>{g(it, it['deepseek_pick'])}"
        f"{' <b>(says none fit)</b>' if it.get('deepseek_none_fit') else ''}</td></tr></table></div>"
        for n, it in enumerate(sample, 1))
    page = f"""<!doctype html><meta charset=utf-8><meta name=viewport content="width=device-width,initial-scale=1">
<title>Portuguese one-off review</title>
<style>
:root{{--bg:#fff;--fg:#1d1d1f;--mute:#6e6e73;--line:#e3e3e8;--mark:#ffe08a}}
@media (prefers-color-scheme:dark){{:root{{--bg:#151517;--fg:#ececf0;--mute:#9a9aa2;--line:#2c2c31;--mark:#6b5a1e}}}}
body{{background:var(--bg);color:var(--fg);font:15px/1.45 system-ui;max-width:860px;margin:24px auto;padding:0 16px}}
.it{{border-top:1px solid var(--line);padding:12px 0}}.h{{color:var(--mute);font-size:13px}}
.s{{font-size:17px;margin:4px 0}}.en{{color:var(--mute)}}td{{vertical-align:top;padding:3px 10px 0 0}}
.k{{color:var(--mute);white-space:nowrap}}mark{{background:var(--mark);color:inherit}}
</style>
<h1>Portuguese one-off: what DeepSeek would change</h1>
<p>{total:,} risky sentences from words 1–4,000 re-picked by DeepSeek V4.1 Flash.
Kept the same sense: {same_id:,}. Switched to an identically worded duplicate sense: {len(same_text):,}
(no visible change). <b>Changed meaning: {len(changed):,}</b> ({len(changed) / total:.0%}).
No answer: {none:,} (keep their current pick).</p>
<p>Below: {len(sample)} of the meaning changes, picked at random, sorted by word rank.
Nothing in the deck has changed yet.</p>
{rows}
"""
    (out / "review.html").write_text(page)
    print(f"{total:,} sentences; same {same_id:,}; duplicate-text switch {len(same_text):,}; "
          f"meaning changed {len(changed):,}; none {none}; page {out / 'review.html'}")


if __name__ == "__main__":
    main()
