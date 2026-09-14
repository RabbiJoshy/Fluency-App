#!/usr/bin/env python3
"""A page for reading the pre-WSD state of a language by eye.

Counts say a card has 40 eligible sentences; they do not say whether those
sentences are any good. This inlines the first few for every card so the
judgement can actually be made, and puts the tags, the lemma and the supply
next to them so a bad card explains itself.

Self-contained: one HTML file, no server, no network.

    python scripts/audit_surfaces_html.py --workspace <ws> --language pt
"""

from __future__ import annotations

import argparse, html, json, sys
from pathlib import Path

SENTENCES_PER_CARD = 6


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--workspace", type=Path, required=True)
    ap.add_argument("--language", required=True)
    ap.add_argument("--out", type=Path)
    ap.add_argument("--sentences", type=int, default=SENTENCES_PER_CARD)
    args = ap.parse_args()
    ws, lang = args.workspace, args.language

    view = json.loads((ws / f"raw/surfaces/{lang}/surfaces.json").read_text())
    marker = ws / f"runs/{lang}/speech/LATEST_V11"
    run = ws / f"runs/{lang}/speech/{marker.read_text().strip()}"
    bank = {}
    with (run / "stages/03_sentence_harvest/output/sentence-bank.jsonl").open(encoding="utf-8") as fh:
        for line in fh:
            if not line.strip():
                continue
            row = json.loads(line)
            bank[row["sentence_id"]] = (
                (row.get("target") or {}).get("text") or "",
                (row.get("translation") or {}).get("text") or "",
                ((row.get("source") or {}).get("name") or "")[:3],
            )

    rows = []
    for s in view["surfaces"].values():
        supply = s.get("supply") or {}
        ids = (supply.get("eligible_sentence_ids") or [])[: args.sentences]
        rows.append({
            "w": s["surface"], "r": s.get("rank"), "v": s["verdict"],
            "t": s["tags"], "l": s.get("lemmas") or [], "p": s.get("part_of_speech") or [],
            "h": supply.get("harvested"), "e": supply.get("eligible"),
            "src": supply.get("eligible_by_source") or {},
            "rej": supply.get("rejected") or {},
            "s": [[*bank.get(i, ("", "", ""))] for i in ids],
        })
    rows.sort(key=lambda r: (r["r"] is None, r["r"] or 0))

    summary = view.get("summary", {})
    doc = f"""<!doctype html><meta charset="utf-8"><title>{lang} pre-WSD audit</title>
<style>
:root{{--bg:#fbfbfa;--fg:#1a1a18;--mut:#6b6b66;--line:#e2e2dd;--card:#fff;
--keep:#2f7d4f;--review:#9a6b00;--exclude:#b3261e}}
@media(prefers-color-scheme:dark){{:root{{--bg:#161614;--fg:#eceae4;--mut:#9b978d;
--line:#2f2d28;--card:#1e1c19;--keep:#6fbf8b;--review:#d9a640;--exclude:#e8776d}}}}
*{{box-sizing:border-box}}body{{margin:0;background:var(--bg);color:var(--fg);
font:14px/1.5 -apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif}}
header{{position:sticky;top:0;background:var(--bg);border-bottom:1px solid var(--line);
padding:14px 18px;z-index:5}}
h1{{margin:0 0 8px;font-size:16px;font-weight:600}}
.sum{{color:var(--mut);font-size:12.5px;margin-bottom:10px}}
input,select{{font:inherit;padding:6px 9px;border:1px solid var(--line);border-radius:6px;
background:var(--card);color:var(--fg);margin-right:8px}}
input[type=search]{{width:260px}}
main{{padding:12px 18px 60px;max-width:1180px}}
.card{{background:var(--card);border:1px solid var(--line);border-radius:9px;
padding:11px 13px;margin-bottom:9px}}
.hd{{display:flex;flex-wrap:wrap;gap:9px;align-items:baseline}}
.w{{font-weight:650;font-size:15px}}
.rank{{color:var(--mut);font-variant-numeric:tabular-nums;font-size:12.5px}}
.v{{font-size:11px;font-weight:650;text-transform:uppercase;letter-spacing:.04em;
padding:1px 7px;border-radius:99px;border:1px solid currentColor}}
.keep{{color:var(--keep)}}.review{{color:var(--review)}}.exclude{{color:var(--exclude)}}
.tag{{font-size:11px;color:var(--mut);background:var(--bg);border:1px solid var(--line);
padding:1px 6px;border-radius:4px}}
.sup{{color:var(--mut);font-size:12.5px;font-variant-numeric:tabular-nums;margin-left:auto}}
.lem{{font-size:12.5px;color:var(--mut);margin-top:3px}}
table{{width:100%;border-collapse:collapse;margin-top:8px;font-size:13px}}
td{{padding:3px 8px 3px 0;vertical-align:top;border-top:1px solid var(--line)}}
td.s{{color:var(--mut);font-size:11px;width:26px;white-space:nowrap}}
td.en{{color:var(--mut)}}
.thin{{color:var(--exclude);font-weight:650}}
.none{{color:var(--mut);font-style:italic;font-size:12.5px;margin-top:6px}}
#more{{margin:18px 0;padding:9px 16px;font:inherit;border:1px solid var(--line);
border-radius:7px;background:var(--card);color:var(--fg);cursor:pointer}}
</style>
<header>
<h1>{lang} &middot; pre-WSD audit</h1>
<div class="sum">{view['derived_from']['surfaces']:,} surfaces &middot; {html.escape(json.dumps(summary))} &middot; sentences shown are the eligible ones the WSD cap would take first</div>
<input type="search" id="q" placeholder="surface, lemma or tag">
<select id="v"><option value="">any verdict</option><option>keep</option><option>review</option><option>exclude</option></select>
<select id="f"><option value="">all cards</option><option value="thin">under 10 eligible</option>
<option value="tagged">has a tag</option><option value="lemma">has a lemma</option>
<option value="rej">something rejected</option></select>
</header>
<main><div id="list"></div><button id="more">show more</button></main>
<script>
const ROWS={json.dumps(rows, ensure_ascii=False)};
const esc=s=>String(s??"").replace(/[&<>]/g,c=>({{"&":"&amp;","<":"&lt;",">":"&gt;"}})[c]);
let shown=0,view=ROWS;
function match(){{
  const q=document.getElementById("q").value.toLowerCase().trim();
  const v=document.getElementById("v").value, f=document.getElementById("f").value;
  view=ROWS.filter(r=>{{
    if(v&&r.v!==v)return false;
    if(f==="thin"&&!(r.e!=null&&r.e<10))return false;
    if(f==="tagged"&&!r.t.length)return false;
    if(f==="lemma"&&!r.l.length)return false;
    if(f==="rej"&&!Object.keys(r.rej).length)return false;
    if(q&&!(r.w.toLowerCase().includes(q)||r.l.join(" ").toLowerCase().includes(q)
        ||r.t.join(" ").toLowerCase().includes(q)))return false;
    return true;
  }});
  shown=0;document.getElementById("list").innerHTML="";draw();
}}
function draw(){{
  const el=document.getElementById("list"),n=Math.min(shown+60,view.length);
  let out="";
  for(let i=shown;i<n;i++){{
    const r=view[i];
    const src=Object.entries(r.src).map(([k,v])=>k.slice(0,3)+" "+v).join(" / ");
    const rej=Object.entries(r.rej).map(([k,v])=>k+" "+v).join(", ");
    out+=`<div class="card"><div class="hd"><span class="w">${{esc(r.w)}}</span>`
      +`<span class="rank">#${{r.r??"-"}}</span>`
      +`<span class="v ${{r.v}}">${{r.v}}</span>`
      +r.t.map(t=>`<span class="tag">${{esc(t)}}</span>`).join("")
      +`<span class="sup">${{r.h??"-"}} harvested &rarr; <b class="${{r.e!=null&&r.e<10?"thin":""}}">${{r.e??"-"}}</b> eligible`
      +(src?` &middot; ${{esc(src)}}`:"")+(rej?` &middot; cut: ${{esc(rej)}}`:"")+`</span></div>`
      +(r.l.length?`<div class="lem">lemma ${{esc(r.l.join(", "))}}${{r.p.length?" &middot; "+esc(r.p.join(", ")):""}}</div>`:"")
      +(r.s.length?`<table>`+r.s.map(s=>`<tr><td class="s">${{esc(s[2])}}</td><td>${{esc(s[0])}}<br><span class="en">${{esc(s[1])}}</span></td></tr>`).join("")+`</table>`
                  :`<div class="none">no eligible sentences</div>`)
      +`</div>`;
  }}
  el.insertAdjacentHTML("beforeend",out);shown=n;
  document.getElementById("more").style.display=shown<view.length?"block":"none";
  document.getElementById("more").textContent=`show more (${{view.length-shown}} left)`;
}}
document.getElementById("more").onclick=draw;
for(const id of ["q","v","f"])document.getElementById(id).oninput=match;
match();
</script>"""
    out = args.out or (ws / f"raw/surfaces/{lang}/audit.html")
    out.write_text(doc, encoding="utf-8")
    size = out.stat().st_size / 1e6
    print(f"{lang}: {len(rows):,} cards, {args.sentences} sentences each -> {out} ({size:.1f} MB)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
