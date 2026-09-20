#!/usr/bin/env python3
"""One page for reading the pre-WSD state of every language by eye.

Counts say a card has 40 eligible sentences; they do not say whether those
sentences are any good. This inlines the first few for every card so the
judgement can actually be made, and puts the tags, the lemma and the supply
next to them so a bad card explains itself.

Every derived cell carries its provenance on hover: where a lemma came from and
what else was on offer, which observation produced a tag and what it said, and
how the supply was narrowed.

Self-contained: one HTML file, no server, no network. Each language's payload
is parsed only when that language is selected, so the page stays responsive
even though all of them are in the file.

    python scripts/audit_surfaces_html.py --workspace <ws>
    python scripts/audit_surfaces_html.py --workspace <ws> --language pt --language es
"""

from __future__ import annotations

import argparse, html, json, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from fluency.surfaces.ledger import ledger_path  # noqa: E402

SENTENCES_PER_CARD = 6
COMPACT = (",", ":")

# What each reason code means, so a hover explains the verdict rather than
# restating the code. Kept here rather than in policy.py because it is prose for
# a reader, not a rule the fold consults.
GLOSS = {
    "english_wordlist": "appears in the English web2 word list",
    "foreign_frequency_list": "appears in another language's frequency list",
    "accent_stripped_duplicate": "another surface differs from it only by accents",
    "abbreviation_form": "looks like an abbreviation",
    "capitalised_in_corpus": "almost always capitalised in the corpus, so likely a name",
    "low_harvest_yield": "the harvest found little or nothing for it",
    "dictionary_absent": "the dictionary has no entry",
    "dictionary_entry_language": "the dictionary answered in the wrong language",
    "dictionary_spelling_substitution": "the dictionary answered about a different spelling",
    "dictionary_pos_gloss_mismatch": "the dictionary's part of speech and gloss disagree",
    "lemma_resolved": "a lemma was resolved for it",
    "lemma_is_headword": "it is its own headword",
    "lemma_absent_from_dictionary": "no dictionary supplies a lemma",
    "human_review": "held for a human to decide",
    "adjudicated_keep": "kept by hand, settling the other evidence",
    "adjudicated_exclude": "excluded by hand",
}


class Intern:
    """A string table, because the payload repeats a handful of strings 10,000
    times. Provider ids and rationales are shared across rows; storing an index
    instead of the text is what keeps the file openable."""

    def __init__(self) -> None:
        self.table: list[str] = []
        self.index: dict[str, int] = {}

    def __call__(self, value: str | None) -> int:
        if not value:
            return -1
        key = str(value)
        if key not in self.index:
            self.index[key] = len(self.table)
            self.table.append(key)
        return self.index[key]


def build_rows(view: dict, bank: dict, limit: int, pool: Intern,
               pos: dict[tuple[str, str], str] | None = None) -> list[dict]:
    rows = []
    pos = pos or {}
    for s in view["surfaces"].values():
        supply = s.get("supply") or {}
        ids = (supply.get("eligible_sentence_ids") or [])[:limit]
        evidence = s.get("evidence") or {}
        durable = set(s.get("durable_tags") or ())
        rows.append({
            "w": s["surface"], "r": s.get("rank"), "v": s["verdict"],
            "t": s["tags"], "l": s.get("lemmas") or [],
            "p": s.get("part_of_speech") or [],
            "lp": s.get("lemma_provenance") or "",
            "la": [[a.get("lemma", ""), a.get("provenance", "")]
                   for a in (s.get("lemma_alternates") or [])],
            "rc": s.get("reason_codes") or [],
            "ob": s.get("observations"),
            # Evidence as indices into a shared string table, assembled into
            # prose in the browser. Storing the prose here made the file 40MB.
            "ev": {t: [pool((evidence.get(t) or {}).get("provider")),
                       pool((evidence.get(t) or {}).get("rationale"))]
                   for t in s["tags"] if evidence.get(t)},
            # Run-scoped tags are the rare case, so ship those rather than the
            # durable ones and let the reader infer the complement.
            "rs": [t for t in s["tags"] if t not in durable],
            "h": supply.get("harvested"), "e": supply.get("eligible"),
            "src": supply.get("eligible_by_source") or {},
            "rej": supply.get("rejected") or {},
            "wh": supply.get("sentences_withheld") or "",
            "s": [[*bank.get(i, ("", "", "")), pos.get((s["surface"], i), "")]
                  for i in ids],
        })
    rows.sort(key=lambda r: (r["r"] is None, r["r"] or 0))
    return rows


def resolve_run(ws: Path, lang: str, overrides: list[str] | None) -> Path | None:
    """The run to read for ``lang``: an explicit --run-id, else LATEST_V11.

    LATEST_V11 tracks whatever ran last, and small probe runs share the marker
    with the full-deck run -- deliberately, since probes exist to find problems
    before the real run. That makes it the wrong thing for the ledger to follow:
    it will happily build a 10,000-surface ledger whose supply covers 3,000.
    Name the run instead wherever the caller knows which one it means.
    """

    for item in overrides or ():
        key, _, value = item.partition("=")
        if not value:
            key, value = lang, key
        if key == lang:
            return ws / f"runs/{lang}/speech/{value.strip()}"
    marker = ws / f"runs/{lang}/speech/LATEST_V11"
    if marker.exists():
        return ws / f"runs/{lang}/speech/{marker.read_text().strip()}"
    return None


V12_WSD_RUNS = {
    "es": "20260915T140557Z-3c7e70a9",
    "pt": "20260915T130807Z-4120e951",
}


def load_occurrence_pos(ws: Path, lang: str, overrides: list[str] | None) -> dict[tuple[str, str], str]:
    """UD tags for (surface, sentence_id). Pairs v2 freeze first, else v12 assignments."""

    from fluency.surfaces.prewsd import occurrence_pos_lookup

    found: dict[tuple[str, str], str] = {}
    run = resolve_run(ws, lang, overrides)
    prewsd_root = ws / "raw/surfaces" / lang / "prewsd"
    candidates = []
    if run is not None:
        candidates.append(prewsd_root / f"{run.name}-v2")
        candidates.append(prewsd_root / run.name)
    candidates.extend(sorted(prewsd_root.glob("*-v2"), reverse=True))
    for folder in candidates:
        pairs_path = folder / "pairs.json"
        examples_path = folder / "examples.json"
        if not (pairs_path.is_file() and examples_path.is_file()):
            continue
        pairs = json.loads(pairs_path.read_text(encoding="utf-8"))
        if not any((entry.get("occurrence_pos") or ())
                   for entry in (pairs.get("surfaces") or {}).values()):
            continue
        examples = json.loads(examples_path.read_text(encoding="utf-8"))
        found.update(occurrence_pos_lookup(examples, pairs))
        break
    assign_id = None
    for item in overrides or ():
        key, _, value = item.partition("=")
        if not value:
            key, value = lang, key
        if key == lang:
            assign_id = value.strip()
    assign_id = assign_id or (run.name if run else None) or V12_WSD_RUNS.get(lang)
    assign_path = (
        ws / "runs" / lang / "speech" / assign_id
        / "stages/04_wsd_assignments/output/assignments.jsonl"
        if assign_id else None
    )
    if assign_path and assign_path.is_file():
        with assign_path.open(encoding="utf-8") as fh:
            for line in fh:
                if not line.strip():
                    continue
                row = json.loads(line)
                tag = ((row.get("evidence") or {}).get("candidate_preparation")
                       or {}).get("observed_pos")
                form, sid = row.get("surface_form"), row.get("sentence_id")
                if tag and form and sid:
                    found.setdefault((form, sid), str(tag))
    return found


def load_bank(ws: Path, lang: str, overrides: list[str] | None = None) -> dict:
    run = resolve_run(ws, lang, overrides)
    bank = {}
    path = run / "stages/03_sentence_harvest/output/sentence-bank.jsonl"
    with path.open(encoding="utf-8") as fh:
        for line in fh:
            if not line.strip():
                continue
            row = json.loads(line)
            bank[row["sentence_id"]] = (
                (row.get("target") or {}).get("text") or "",
                (row.get("translation") or {}).get("text") or "",
                ((row.get("source") or {}).get("name") or "")[:3],
            )
    return bank


CSS = """
:root{--bg:#fbfbfa;--fg:#1a1a18;--mut:#6f6f69;--line:#e4e4df;--card:#fff;--hov:#f3f3ef;
--keep:#2f7d4f;--review:#9a6b00;--exclude:#b3261e;--tipbg:#26241f;--tipfg:#f4f2ec}
@media(prefers-color-scheme:dark){:root{--bg:#141412;--fg:#ecebe5;--mut:#96938a;
--line:#2d2b26;--card:#1c1a17;--hov:#232019;--keep:#6fbf8b;--review:#d9a640;--exclude:#e8776d;
--tipbg:#33302a;--tipfg:#f4f2ec}}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--fg);
font:13px/1.45 -apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif}
header{position:sticky;top:0;z-index:9;background:var(--bg);
border-bottom:1px solid var(--line);padding:12px 16px}
h1{margin:0 0 6px;font-size:15px;font-weight:600}
.sum{color:var(--mut);font-size:12px;margin-bottom:9px}
input,select{font:inherit;padding:5px 8px;border:1px solid var(--line);border-radius:6px;
background:var(--card);color:var(--fg);margin-right:7px}
input[type=search]{width:230px}
select#lang{font-weight:650}
table{width:100%;border-collapse:collapse}
thead th{position:sticky;top:100px;background:var(--bg);text-align:left;font-size:11px;
text-transform:uppercase;letter-spacing:.05em;color:var(--mut);font-weight:600;
padding:7px 9px;border-bottom:1px solid var(--line);z-index:8;white-space:nowrap}
tbody tr.r{border-bottom:1px solid var(--line);cursor:pointer}
tbody tr.r:hover{background:var(--hov)}
td{padding:5px 9px;vertical-align:top}
td.n{font-variant-numeric:tabular-nums;text-align:right;color:var(--mut);white-space:nowrap}
td.w{font-weight:620}
.v{font-size:10.5px;font-weight:650;text-transform:uppercase;letter-spacing:.04em}
.keep{color:var(--keep)}.review{color:var(--review)}.exclude{color:var(--exclude)}
.tag{display:inline-block;font-size:10.5px;color:var(--mut);border:1px solid var(--line);
padding:0 5px;border-radius:4px;margin:1px 3px 1px 0;white-space:nowrap}
.thin{color:var(--exclude);font-weight:650}
tr.d>td{background:var(--card);padding:2px 9px 11px 30px}
tr.d table{margin-top:4px}
tr.d td{padding:3px 9px 3px 0;border-top:1px solid var(--line)}
tr.d td.s{color:var(--mut);font-size:10.5px;width:24px}
.en{color:var(--mut)}
.pos{display:inline-block;font-size:10.5px;font-weight:650;letter-spacing:.04em;
color:var(--mut);border:1px solid var(--line);padding:0 5px;border-radius:4px;
margin-right:6px;vertical-align:1px}
.none{color:var(--mut);font-style:italic}
.caret{color:var(--mut);display:inline-block;width:11px}
#more{margin:16px;padding:8px 15px;font:inherit;border:1px solid var(--line);
border-radius:7px;background:var(--card);color:var(--fg);cursor:pointer}
[data-tip]{cursor:help;border-bottom:1px dotted var(--line)}
#tip{position:fixed;z-index:99;max-width:430px;background:var(--tipbg);color:var(--tipfg);
padding:8px 11px;border-radius:7px;font-size:12px;line-height:1.5;white-space:pre-wrap;
box-shadow:0 6px 24px rgba(0,0,0,.28);pointer-events:none;display:none}
#tip b{font-weight:650}
#loading{padding:40px 16px;color:var(--mut)}
"""

JS = r"""
const TIP=document.getElementById("tip");
document.addEventListener("mouseover",e=>{
  const el=e.target.closest("[data-tip]");
  if(!el){TIP.style.display="none";return;}
  TIP.textContent=el.dataset.tip;TIP.style.display="block";
  const r=el.getBoundingClientRect();
  const w=TIP.offsetWidth,h=TIP.offsetHeight;
  let x=r.left,y=r.bottom+7;
  if(x+w>innerWidth-10)x=innerWidth-w-10;
  if(y+h>innerHeight-10)y=r.top-h-7;
  TIP.style.left=Math.max(8,x)+"px";TIP.style.top=Math.max(8,y)+"px";
});
document.addEventListener("mouseout",e=>{
  if(!e.relatedTarget||!e.relatedTarget.closest("[data-tip]"))TIP.style.display="none";
});

const esc=s=>String(s??"").replace(/[&<>"]/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;"})[c]);
let ROWS=[],view=[],shown=0,LANG=null,POOL=[],GLOSS={};

function tagTip(r,t){
  const parts=[GLOSS[t]||t];
  const e=r.ev&&r.ev[t];
  if(e){
    if(e[0]>=0)parts.push("observed by "+POOL[e[0]]);
    if(e[1]>=0)parts.push(POOL[e[1]]);
  }
  parts.push(r.rs.includes(t)
    ?"run-scoped — a fact about one corpus pass, not about the word"
    :"durable evidence — survives a re-harvest");
  return parts.join("\n");
}

// Each language is parsed on first use, not at load. The file holds every
// language, but only the selected one ever becomes objects.
const CACHE={};
function load(lang){
  if(!CACHE[lang]){
    CACHE[lang]=JSON.parse(document.getElementById("d-"+lang).textContent);
  }
  return CACHE[lang];
}
function pick(lang){
  LANG=lang;
  document.getElementById("loading").style.display="block";
  document.getElementById("body").innerHTML="";
  setTimeout(()=>{
    const d=load(lang);
    ROWS=d.rows;POOL=d.pool;GLOSS=d.gloss;
    document.getElementById("sum").innerHTML=d.summary;
    document.getElementById("loading").style.display="none";
    apply();
  },0);
}

function apply(){
  const q=document.getElementById("q").value.toLowerCase().trim();
  const v=document.getElementById("v").value,f=document.getElementById("f").value;
  const k=document.getElementById("sort").value;
  view=ROWS.filter(r=>{
    if(v&&r.v!==v)return false;
    if(f==="thin"&&!(r.e!=null&&r.e<10))return false;
    if(f==="tagged"&&!r.t.length)return false;
    if(f==="lemma"&&!r.l.length)return false;
    if(f==="nolemma"&&r.l.length)return false;
    if(f==="rej"&&!Object.keys(r.rej).length)return false;
    if(f==="nosent"&&r.s.length)return false;
    if(f==="manual"&&!/manual|clitic/.test(r.lp))return false;
    if(q&&!(r.w.toLowerCase().includes(q)||r.l.join(" ").toLowerCase().includes(q)
        ||r.t.join(" ").toLowerCase().includes(q)||r.lp.toLowerCase().includes(q)))return false;
    return true;
  });
  if(k==="e")view=[...view].sort((a,b)=>(a.e??1e9)-(b.e??1e9));
  else if(k==="t")view=[...view].sort((a,b)=>b.t.length-a.t.length);
  else view=[...view].sort((a,b)=>(a.r??1e9)-(b.r??1e9));
  shown=0;document.getElementById("body").innerHTML="";draw();
}

function lemmaTip(r){
  if(!r.l.length)return "no lemma"+(r.rc.length?"\n"+r.rc.join(", "):"");
  let t="primary: "+r.l[0]+"\nprovenance: "+(r.lp||"unlabelled");
  t+="\n\nThe primary lemma comes only from the provider that supplies this "
    +"language's sense menus, because a lemma's job is to find a menu.";
  if(r.la.length){
    t+="\n\nalso recorded (never leads):";
    for(const [lem,prov] of r.la)t+="\n  "+lem+"  —  "+prov;
  }
  return t;
}
function verdictTip(r){
  let t=r.v.toUpperCase();
  t+=r.v==="keep"?"\nreaches WSD":r.v==="exclude"
    ?"\nkeeps its row for audit but carries no sentence ids":"\nawaiting a decision";
  if(r.rc.length)t+="\n\ndecided by:\n  "+r.rc.join("\n  ");
  else t+="\n\nnothing observed against it";
  t+="\n\nfolded from "+(r.ob??0)+" observation(s) at read time; the events are "
   +"facts and this verdict is policy.";
  return t;
}
function supplyTip(r){
  let t="harvested "+(r.h??"–")+"\neligible "+(r.e??"–");
  const src=Object.entries(r.src);
  if(src.length){t+="\n\neligible by corpus:";for(const[a,b]of src)t+="\n  "+a+": "+b;}
  const rej=Object.entries(r.rej);
  if(rej.length){t+="\n\ncut in cleaning:";for(const[a,b]of rej)t+="\n  "+a+": "+b;}
  if(r.wh)t+="\n\n"+r.wh;
  if(r.e!=null&&r.e<10)t+="\n\nUnder ten eligible: the long tail, where selection has little to choose from.";
  return t;
}

function draw(){
  const body=document.getElementById("body"),n=Math.min(shown+120,view.length);
  let out="";
  for(let i=shown;i<n;i++){
    const r=view[i];
    const src=Object.entries(r.src).map(([a,b])=>a.slice(0,3)+" "+b).join(" / ");
    const rej=Object.entries(r.rej).map(([a,b])=>a.replace("below_alignment_floor","align")+" "+b).join(", ");
    out+=`<tr class="r" data-i="${i}"><td class="caret">&#9656;</td>`
      +`<td class="n">${r.r??"&ndash;"}</td>`
      +`<td class="w"><span data-tip="${esc("rank "+(r.r??"unranked")+"\n"+(r.ob??0)+" observation(s) recorded\n\nCard identity is the surface form itself — not the lemma, not a sense, not a rank.")}">${esc(r.w)}</span></td>`
      +`<td><span class="v ${r.v}" data-tip="${esc(verdictTip(r))}">${r.v}</span></td>`
      +`<td>${r.t.map(t=>`<span class="tag" data-tip="${esc(tagTip(r,t))}">${esc(t)}</span>`).join("")}</td>`
      +`<td><span data-tip="${esc(lemmaTip(r))}">${esc(r.l.join(", "))||"<span class=none>&ndash;</span>"}</span>`
      +`${r.p.length?` <span class="en">${esc(r.p[0])}</span>`:""}</td>`
      +`<td class="n"><span data-tip="${esc(supplyTip(r))}">${r.h??"&ndash;"}</span></td>`
      +`<td class="n ${r.e!=null&&r.e<10?"thin":""}"><span data-tip="${esc(supplyTip(r))}">${r.e??"&ndash;"}</span></td>`
      +`<td class="en">${esc(src)}${rej?` &middot; cut ${esc(rej)}`:""}</td></tr>`;
  }
  body.insertAdjacentHTML("beforeend",out);shown=n;
  const m=document.getElementById("more");
  m.style.display=shown<view.length?"block":"none";
  m.textContent=`show more (${view.length-shown} left)`;
}

document.getElementById("body").onclick=e=>{
  const tr=e.target.closest("tr.r");if(!tr)return;
  const nxt=tr.nextElementSibling;
  if(nxt&&nxt.classList.contains("d")){nxt.remove();tr.firstChild.innerHTML="&#9656;";return;}
  const r=view[+tr.dataset.i];
  const inner=r.s.length
    ? `<table>`+r.s.map(s=>`<tr><td class="s" data-tip="${esc("corpus: "+(s[2]==="tat"?"Tatoeba — human-aligned":"OpenSubtitles — machine-aligned"))}">${esc(s[2])}</td><td>${s[3]?`<span class="pos" data-tip="${esc("occurrence POS (UD) for this word in this sentence. Absent means this pair was not frozen.")}">${esc(s[3])}</span>`:""}${esc(s[0])}<br><span class="en">${esc(s[1])}</span></td></tr>`).join("")+`</table>`
    : `<div class="none">${esc(r.wh||"no eligible sentences")}</div>`;
  tr.insertAdjacentHTML("afterend",`<tr class="d"><td colspan="9">${inner}</td></tr>`);
  tr.firstChild.innerHTML="&#9662;";
};
document.getElementById("more").onclick=draw;
for(const id of ["q","v","f","sort"])document.getElementById(id).oninput=apply;
document.getElementById("lang").onchange=e=>pick(e.target.value);
pick(document.getElementById("lang").value);
"""


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--workspace", type=Path, required=True)
    ap.add_argument("--language", action="append",
                    help="repeatable; defaults to every language with a ledger")
    ap.add_argument("--out", type=Path)
    ap.add_argument("--run-id", action="append", default=None,
                    help="explicit run, as <lang>=<run-id>. Prefer this over LATEST_V11, which tracks whatever ran last -- small probe runs and the full-deck run share the marker, so following it can build a 10,000-surface ledger whose supply covers 3,000.")
    ap.add_argument("--sentences", type=int, default=SENTENCES_PER_CARD)
    args = ap.parse_args()
    ws = args.workspace

    languages = args.language or sorted(
        p.parent.name for p in (ws / "raw/surfaces").glob("*/ledger.json"))
    if not languages:
        print(f"no ledgers under {ws / 'raw/surfaces'}")
        return 1

    blocks, options, totals = [], [], []
    for lang in languages:
        view = json.loads(ledger_path(ws, lang).read_text())
        pool = Intern()
        rows = build_rows(view, load_bank(ws, lang, args.run_id), args.sentences, pool,
                          load_occurrence_pos(ws, lang, args.run_id))
        counts = view.get("summary", {})
        lemma = sum(1 for r in rows if r["v"] == "keep" and r["l"])
        keep = sum(1 for r in rows if r["v"] == "keep")
        thin = sum(1 for r in rows if r["e"] is not None and r["e"] < 10)
        summary = (f"{len(rows):,} surfaces &middot; "
                   f"{html.escape(json.dumps(counts))} &middot; "
                   f"lemma {lemma / keep:.2%} of keep &middot; "
                   f"{thin:,} under ten eligible &middot; "
                   f"hover any cell for its provenance")
        payload = json.dumps({"rows": rows, "summary": summary,
                              "pool": pool.table, "gloss": GLOSS},
                             ensure_ascii=False, separators=COMPACT)
        # Inside a <script type="application/json"> only "</" can end the block.
        blocks.append(f'<script type="application/json" id="d-{lang}">'
                      f'{payload.replace("</", "<\\/")}</script>')
        options.append(f'<option value="{lang}">{lang}</option>')
        totals.append((lang, len(rows), len(payload)))

    doc = ("<!doctype html><meta charset=\"utf-8\"><title>pre-WSD surface ledger audit</title>\n"
           f"<style>{CSS}</style>\n"
           "<header>\n<h1>surface ledger &middot; pre-WSD audit</h1>\n"
           '<div class="sum" id="sum"></div>\n'
           f'<select id="lang">{"".join(options)}</select>\n'
           '<input type="search" id="q" placeholder="surface, lemma, tag or provenance">\n'
           '<select id="v"><option value="">any verdict</option><option>keep</option>'
           '<option>review</option><option>exclude</option></select>\n'
           '<select id="f"><option value="">all cards</option>'
           '<option value="thin">under 10 eligible</option>'
           '<option value="tagged">has a tag</option>'
           '<option value="lemma">has a lemma</option>'
           '<option value="nolemma">no lemma</option>'
           '<option value="manual">lemma by hand or inference</option>'
           '<option value="rej">something rejected</option>'
           '<option value="nosent">no sentences</option></select>\n'
           '<select id="sort"><option value="r">by rank</option>'
           '<option value="e">by eligible</option>'
           '<option value="t">by tag count</option></select>\n</header>\n'
           '<div id="tip"></div>\n'
           "<table><thead><tr>"
           '<th style="width:26px"></th><th style="width:62px">rank</th><th>surface</th>'
           '<th style="width:74px">verdict</th><th>tags</th><th>lemma</th>'
           '<th style="width:58px">harv</th><th style="width:58px">elig</th>'
           "<th>sources / cut</th></tr></thead><tbody id=\"body\"></tbody></table>\n"
           '<div id="loading">loading&hellip;</div>\n'
           '<button id="more">show more</button>\n'
           + "\n".join(blocks) + f"\n<script>{JS}</script>\n")

    # One explicitly named language keeps the old per-language path, so asking
    # for a single language never silently overwrites the combined page.
    if args.out:
        out = args.out
    elif args.language and len(args.language) == 1:
        out = ws / f"raw/surfaces/{args.language[0]}/audit.html"
    else:
        out = ws / "raw/surfaces/audit.html"
    out.write_text(doc, encoding="utf-8")
    print(f"languages: {', '.join(languages)}")
    for lang, n, size in totals:
        print(f"  {lang}: {n:,} cards, {size / 1e6:.1f} MB payload")
    print(f"-> {out} ({out.stat().st_size / 1e6:.1f} MB total, "
          f"parsed one language at a time)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
