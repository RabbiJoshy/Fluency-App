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

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from fluency.surfaces.ledger import ledger_path  # noqa: E402

SENTENCES_PER_CARD = 6


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--workspace", type=Path, required=True)
    ap.add_argument("--language", required=True)
    ap.add_argument("--out", type=Path)
    ap.add_argument("--sentences", type=int, default=SENTENCES_PER_CARD)
    args = ap.parse_args()
    ws, lang = args.workspace, args.language

    view = json.loads(ledger_path(ws, lang).read_text())
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
:root{{--bg:#fbfbfa;--fg:#1a1a18;--mut:#6f6f69;--line:#e4e4df;--card:#fff;--hov:#f3f3ef;
--keep:#2f7d4f;--review:#9a6b00;--exclude:#b3261e}}
@media(prefers-color-scheme:dark){{:root{{--bg:#141412;--fg:#ecebe5;--mut:#96938a;
--line:#2d2b26;--card:#1c1a17;--hov:#232019;--keep:#6fbf8b;--review:#d9a640;--exclude:#e8776d}}}}
*{{box-sizing:border-box}}
body{{margin:0;background:var(--bg);color:var(--fg);
font:13px/1.45 -apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif}}
header{{position:sticky;top:0;z-index:9;background:var(--bg);
border-bottom:1px solid var(--line);padding:12px 16px}}
h1{{margin:0 0 6px;font-size:15px;font-weight:600}}
.sum{{color:var(--mut);font-size:12px;margin-bottom:9px}}
input,select{{font:inherit;padding:5px 8px;border:1px solid var(--line);border-radius:6px;
background:var(--card);color:var(--fg);margin-right:7px}}
input[type=search]{{width:230px}}
table{{width:100%;border-collapse:collapse}}
thead th{{position:sticky;top:96px;background:var(--bg);text-align:left;font-size:11px;
text-transform:uppercase;letter-spacing:.05em;color:var(--mut);font-weight:600;
padding:7px 9px;border-bottom:1px solid var(--line);z-index:8;white-space:nowrap}}
tbody tr.r{{border-bottom:1px solid var(--line);cursor:pointer}}
tbody tr.r:hover{{background:var(--hov)}}
td{{padding:5px 9px;vertical-align:top}}
td.n{{font-variant-numeric:tabular-nums;text-align:right;color:var(--mut);white-space:nowrap}}
td.w{{font-weight:620}}
.v{{font-size:10.5px;font-weight:650;text-transform:uppercase;letter-spacing:.04em}}
.keep{{color:var(--keep)}}.review{{color:var(--review)}}.exclude{{color:var(--exclude)}}
.tag{{display:inline-block;font-size:10.5px;color:var(--mut);border:1px solid var(--line);
padding:0 5px;border-radius:4px;margin:1px 3px 1px 0;white-space:nowrap}}
.thin{{color:var(--exclude);font-weight:650}}
tr.d>td{{background:var(--card);padding:2px 9px 11px 30px}}
tr.d table{{margin-top:4px}}
tr.d td{{padding:3px 9px 3px 0;border-top:1px solid var(--line)}}
tr.d td.s{{color:var(--mut);font-size:10.5px;width:24px}}
.en{{color:var(--mut)}}
.none{{color:var(--mut);font-style:italic}}
.caret{{color:var(--mut);display:inline-block;width:11px}}
#more{{margin:16px;padding:8px 15px;font:inherit;border:1px solid var(--line);
border-radius:7px;background:var(--card);color:var(--fg);cursor:pointer}}
</style>
<header>
<h1>{lang} &middot; pre-WSD audit</h1>
<div class="sum">{view['derived_from']['surfaces']:,} surfaces &middot; {html.escape(json.dumps(summary))} &middot; click a row for the sentences the WSD cap would take first</div>
<input type="search" id="q" placeholder="surface, lemma or tag">
<select id="v"><option value="">any verdict</option><option>keep</option><option>review</option><option>exclude</option></select>
<select id="f"><option value="">all cards</option><option value="thin">under 10 eligible</option>
<option value="tagged">has a tag</option><option value="lemma">has a lemma</option>
<option value="rej">something rejected</option><option value="nosent">no sentences</option></select>
<select id="sort"><option value="r">by rank</option><option value="e">by eligible</option>
<option value="t">by tag count</option></select>
</header>
<table><thead><tr>
<th style="width:26px"></th><th style="width:62px">rank</th><th>surface</th>
<th style="width:74px">verdict</th><th>tags</th><th>lemma</th>
<th style="width:58px">harv</th><th style="width:58px">elig</th><th>sources / cut</th>
</tr></thead><tbody id="body"></tbody></table>
<button id="more">show more</button>
<script>
const ROWS={json.dumps(rows, ensure_ascii=False)};
const esc=s=>String(s??"").replace(/[&<>]/g,c=>({{"&":"&amp;","<":"&lt;",">":"&gt;"}})[c]);
let shown=0,view=ROWS;
function apply(){{
  const q=document.getElementById("q").value.toLowerCase().trim();
  const v=document.getElementById("v").value,f=document.getElementById("f").value;
  const k=document.getElementById("sort").value;
  view=ROWS.filter(r=>{{
    if(v&&r.v!==v)return false;
    if(f==="thin"&&!(r.e!=null&&r.e<10))return false;
    if(f==="tagged"&&!r.t.length)return false;
    if(f==="lemma"&&!r.l.length)return false;
    if(f==="rej"&&!Object.keys(r.rej).length)return false;
    if(f==="nosent"&&r.s.length)return false;
    if(q&&!(r.w.toLowerCase().includes(q)||r.l.join(" ").toLowerCase().includes(q)
        ||r.t.join(" ").toLowerCase().includes(q)))return false;
    return true;
  }});
  if(k==="e")view=[...view].sort((a,b)=>(a.e??1e9)-(b.e??1e9));
  else if(k==="t")view=[...view].sort((a,b)=>b.t.length-a.t.length);
  else view=[...view].sort((a,b)=>(a.r??1e9)-(b.r??1e9));
  shown=0;document.getElementById("body").innerHTML="";draw();
}}
function draw(){{
  const body=document.getElementById("body"),n=Math.min(shown+120,view.length);
  let out="";
  for(let i=shown;i<n;i++){{
    const r=view[i];
    const src=Object.entries(r.src).map(([a,b])=>a.slice(0,3)+" "+b).join(" / ");
    const rej=Object.entries(r.rej).map(([a,b])=>a.replace("below_alignment_floor","align")+" "+b).join(", ");
    out+=`<tr class="r" data-i="${{i}}"><td class="caret">&#9656;</td>`
      +`<td class="n">${{r.r??"&ndash;"}}</td><td class="w">${{esc(r.w)}}</td>`
      +`<td><span class="v ${{r.v}}">${{r.v}}</span></td>`
      +`<td>${{r.t.map(t=>`<span class="tag">${{esc(t)}}</span>`).join("")}}</td>`
      +`<td>${{esc(r.l.join(", "))}}${{r.p.length?` <span class="en">${{esc(r.p[0])}}</span>`:""}}</td>`
      +`<td class="n">${{r.h??"&ndash;"}}</td>`
      +`<td class="n ${{r.e!=null&&r.e<10?"thin":""}}">${{r.e??"&ndash;"}}</td>`
      +`<td class="en">${{esc(src)}}${{rej?` &middot; cut ${{esc(rej)}}`:""}}</td></tr>`;
  }}
  body.insertAdjacentHTML("beforeend",out);shown=n;
  const m=document.getElementById("more");
  m.style.display=shown<view.length?"block":"none";
  m.textContent=`show more (${{view.length-shown}} left)`;
}}
document.getElementById("body").onclick=e=>{{
  const tr=e.target.closest("tr.r");if(!tr)return;
  const nxt=tr.nextElementSibling;
  if(nxt&&nxt.classList.contains("d")){{nxt.remove();tr.firstChild.innerHTML="&#9656;";return;}}
  const r=view[+tr.dataset.i];
  const inner=r.s.length
    ? `<table>`+r.s.map(s=>`<tr><td class="s">${{esc(s[2])}}</td><td>${{esc(s[0])}}<br><span class="en">${{esc(s[1])}}</span></td></tr>`).join("")+`</table>`
    : `<div class="none">no eligible sentences</div>`;
  tr.insertAdjacentHTML("afterend",`<tr class="d"><td colspan="9">${{inner}}</td></tr>`);
  tr.firstChild.innerHTML="&#9662;";
}};
document.getElementById("more").onclick=draw;
for(const id of ["q","v","f","sort"])document.getElementById(id).oninput=apply;
apply();
</script>"""
    out = args.out or (ws / f"raw/surfaces/{lang}/audit.html")
    out.write_text(doc, encoding="utf-8")
    size = out.stat().st_size / 1e6
    print(f"{lang}: {len(rows):,} cards, {args.sentences} sentences each -> {out} ({size:.1f} MB)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
