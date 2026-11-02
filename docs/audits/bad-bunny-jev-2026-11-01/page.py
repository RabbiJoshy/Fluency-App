#!/usr/bin/env python3
"""compare.json -> review.html (Jev vs live sense per sentence, grouped by card)."""
import html, json, collections, sys
from pathlib import Path
HERE = Path(__file__).resolve().parent
RUN = HERE.parents[2].parent / "Fluency-Workspace/reviews/bb-jev-20261101" / (sys.argv[1] if len(sys.argv) > 1 else "pilot50")
rows = json.loads((RUN / "compare.json").read_text())
e = html.escape
def sense(s):
    if not s: return '<span class="muted">—</span>'
    ctx = f' <span class="muted">({e(s["context"])})</span>' if s.get("context") else ""
    return f'<b>{e(s["translation"])}</b>{ctx} <span class="tag">{e(s["headword"])} · {e(s["pos"].lower())}</span>'
def mark(t): return e(t).replace("&lt;&lt;", "<mark>").replace("&gt;&gt;", "</mark>")
LABEL = {"same": "agree", "differs": "differ", "none": "Jev: no sense fits", "no_live": "not in live deck"}
cards = collections.OrderedDict()
for r in rows: cards.setdefault(r["surface"], []).append(r)
tot = collections.Counter(r["verdict"] for r in rows)
parts = []
for w, rs in cards.items():
    c = collections.Counter(r["verdict"] for r in rs)
    body = []
    for r in rs:
        alt = f'<div class="muted small">runner-up: {e(r["runner_up"])}</div>' if r.get("runner_up") else ""
        body.append(f'<tr class="v-{r["verdict"]}"><td><div>{mark(r["sentence"])}</div><div class="muted small">{e(r["english"])}</div></td>'
                    f'<td>{sense(r["jev"]) if r["verdict"]!="none" else "<b>NONE</b>"} <span class="p">{r["jev_p"]}</span>{alt}</td>'
                    f'<td>{sense(r["live"])}</td><td class="small">{LABEL[r["verdict"]]}</td></tr>')
    summary = " · ".join(f'{n} {LABEL[k]}' for k, n in c.most_common())
    parts.append(f'<details><summary><b>{e(w)}</b> <span class="muted">{len(rs)} lines, menu {rs[0]["menu_size"]} senses — {summary}</span></summary>'
                 f'<table><tr><th>Lyric</th><th>Jev</th><th>Live deck</th><th></th></tr>{"".join(body)}</table></details>')
page = f'''<!doctype html><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Bad Bunny Jev pilot</title>
<style>
:root{{--bg:#fff;--fg:#1d1d1f;--mut:#6e6e73;--line:#e5e5ea;--mark:#ffe58a;--diff:#fff4f0;--none:#f3f0ff}}
@media (prefers-color-scheme:dark){{:root{{--bg:#1c1c1e;--fg:#f2f2f7;--mut:#a1a1a6;--line:#3a3a3c;--mark:#7a5d00;--diff:#3a2622;--none:#2c2640}}}}
body{{background:var(--bg);color:var(--fg);font:15px/1.45 -apple-system,system-ui,sans-serif;margin:0 auto;max-width:1100px;padding:16px}}
.muted{{color:var(--mut)}}.small{{font-size:13px}}.tag{{font-size:12px;color:var(--mut);border:1px solid var(--line);border-radius:6px;padding:0 5px}}
.p{{font-size:12px;color:var(--mut)}} mark{{background:var(--mark);color:inherit;border-radius:3px;padding:0 2px}}
table{{width:100%;border-collapse:collapse;margin:6px 0 14px}} td,th{{text-align:left;vertical-align:top;padding:6px;border-bottom:1px solid var(--line)}}
th{{font-size:12px;color:var(--mut);font-weight:600}} td:nth-child(1){{width:40%}}
tr.v-differs{{background:var(--diff)}} tr.v-none{{background:var(--none)}}
details{{border-bottom:1px solid var(--line);padding:8px 0}} summary{{cursor:pointer}}
.bar button{{font:inherit;margin:0 6px 6px 0;padding:4px 10px;border:1px solid var(--line);border-radius:8px;background:none;color:inherit}}
@media (max-width:700px){{td{{display:block;width:auto!important;border:0}}tr{{display:block;border-bottom:1px solid var(--line)}}th{{display:none}}}}
</style>
<h1>Bad Bunny — Jev pilot</h1>
<p>50 cards, {len(rows):,} lyric lines. Jev 1.14 picked from the full SpanishDict/Wiktionary menu; “Live deck” is what production shows now (embedding scorer, menu capped at 6 senses per word). Highlighted word = the occurrence Jev was asked about. The number after Jev's pick is its probability.</p>
<p><b>{tot["same"]}</b> agree · <b>{tot["differs"]}</b> differ · <b>{tot["none"]}</b> Jev found no fitting sense · <b>{tot["no_live"]}</b> lines the live deck doesn't show</p>
<div class="bar"><button data-f="all">All lines</button><button data-f="differs">Only differences</button><button data-f="none">Only “no sense fits”</button></div>
{"".join(parts)}
<script>
document.querySelectorAll('.bar button').forEach(b=>b.onclick=()=>{{const f=b.dataset.f;
document.querySelectorAll('tbody tr, table tr').forEach(tr=>{{if(!tr.className)return;tr.style.display=(f==='all'||tr.classList.contains('v-'+f))?'':'none'}});
document.querySelectorAll('details').forEach(d=>d.open=f!=='all')}});
</script>'''
out = HERE / "review.html"
out.write_text(page, encoding="utf-8")
print(out)
