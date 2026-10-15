"""Portuguese design review using the app's real replica markup and stylesheet."""
import json
import shutil
from pathlib import Path

from design_preview import CARDS, OUT

ROOT = Path(__file__).resolve().parents[2]
RANKS = {"que": 1, "o": 3, "de": 4, "se": 11, "nos": 44, "naquele": 1104}
POSITIONS = {
    "que": ["CONJ", "PRON", "CONJ"], "de": ["PREP"],
    "se": ["CONJ", "PRON", "PRON"], "o": ["ARTICLE", "PRON"],
    "nos": ["PRON", "PRON", "CONTRACTION"], "naquele": ["CONTRACTION"],
}

HTML = r'''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Portuguese grammar cards — normal UI draft</title>
<link href="https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;600;700&family=Space+Grotesk:wght@600;700&display=swap" rel="stylesheet">
<link rel="stylesheet" href="assets/css/style.css">
<style>
:root{--accent-primary:#67bf85;--accent-secondary:#dbeadf;--ui-zoom:1}
body{height:auto;min-height:100vh;overflow:auto;padding:24px 12px;user-select:auto}
.draft-shell{max-width:900px;margin:auto}.draft-heading{font:600 17px var(--font-emphasis);margin-bottom:8px}.draft-note{font-size:13px;color:var(--text-muted);margin-bottom:16px}.draft-nav{display:flex;gap:7px;flex-wrap:wrap;align-items:center;margin-bottom:24px}.draft-nav button{font:600 14px var(--font-reading);border:1px solid var(--border-light);background:var(--bg-tertiary);color:var(--text-primary);padding:7px 14px;border-radius:20px;cursor:pointer}.draft-nav button[aria-pressed=true]{border-color:var(--accent-primary);color:var(--accent-primary)}.draft-nav .flip-toggle{margin-left:auto;color:var(--text-muted)}
.draft-layout{display:flex;justify-content:center;align-items:flex-start;gap:26px}.draft-stage{width:568px;max-width:100%;flex-shrink:0}.draft-stage .card-replica{width:100%;--replica-card-h:650px}.draft-stage .card-details{min-height:0}.draft-stage .card-face.card-back{overflow:visible}.draft-stage .meaning-context{font-size:13px!important;line-height:1.35}.draft-stage .meaning-row-translation{font-size:21px!important}.draft-stage .meaning-row{padding:3px 2px!important}.draft-stage .meaning-row-body{padding-block:3px!important}.draft-stage .meaning-pos-section .pos-section-head{min-height:34px;padding-top:5px;padding-bottom:5px}.draft-stage .back-headword-row{position:relative}.draft-stage .draft-grammar-badge{position:absolute;right:0;top:7px;font-size:10px;line-height:1.3;font-weight:500;padding:3px 6px;border:1px solid var(--border-light);border-radius:8px;color:var(--text-muted)}.draft-stage .grammar-pair-chips{font-size:13px}.draft-stage .grammar-pair-chip{cursor:default}.draft-stage .draft-phrases .pos-section-label{font-size:14px}.draft-stage .draft-phrases .meaning-row-translation{font-size:16px!important}.draft-stage .draft-phrases .meaning-context{display:none}.draft-stage .draft-phrases .meaning-pos-rows{display:none}.draft-stage .draft-phrases.is-open .meaning-pos-rows{display:block}.draft-stage .draft-phrases .pos-section-summary{display:flex!important;opacity:1;overflow:visible}.draft-stage .draft-phrases.is-open .pos-section-summary{display:none!important}.draft-stage .draft-phrases .pos-summary-sense{font-size:13px}.draft-stage .sentence{--sense-match-rgb:103,191,133!important}.draft-stage .example-word-highlight{color:var(--accent-primary)!important}.draft-stage .sentence .breakdown-trigger{font-size:21px!important;cursor:default}.draft-stage .sentence .translation{font-size:16px!important}.draft-stage .links-section{justify-content:center!important}.draft-annotation{width:190px;font-size:13px;color:var(--text-muted);line-height:1.5;padding-top:16px}.draft-annotation p{margin-bottom:16px}.draft-annotation b{color:var(--text-primary)}
@media(max-width:760px){body{padding:16px 8px}.draft-layout{display:block}.draft-stage{width:100%;max-width:568px;margin:auto}.draft-stage .card-replica{--replica-card-h:620px}.draft-stage .card-face.card-back{padding-top:16px}.draft-stage .card-details{padding-inline:12px!important}.draft-stage .back-headword{font-size:38px!important}.draft-stage .draft-grammar-badge{font-size:9px;top:4px}.draft-stage .meaning-row-translation{font-size:19px!important}.draft-stage .meaning-context{font-size:12px!important}.draft-stage .sentence .breakdown-trigger{font-size:19px!important}.draft-stage .sentence .translation{font-size:14px!important}.draft-nav{gap:5px;margin-bottom:15px}.draft-nav button{padding:6px 10px;font-size:13px}.draft-nav .flip-toggle{margin-left:0}.draft-annotation{width:auto;margin:20px 8px 0;padding:0}.draft-note{font-size:12px;line-height:1.4}.draft-heading{font-size:16px}}
</style></head><body><main class="draft-shell"><h1 class="draft-heading">Portuguese cards · revised draft</h1><p class="draft-note">Normal card layout. Grammar uses and phrases are drafts; existing examples are unchanged.</p><nav class="draft-nav" id="picker" aria-label="Choose a draft card"></nav><div class="draft-layout"><div class="draft-stage" id="stage"></div><aside class="draft-annotation"><p><b>Same card.</b> Normal word heading, part-of-speech groups, meaning rows and example block.</p><p><b>Small additions.</b> A grammar-word badge, short use notes and contraction parts.</p><p><b>Same phrase group.</b> Common phrases use the normal expandable Expression section.</p><p>Rows explain the word’s uses. This draft does not assign the example to a selected use.</p></aside></div></main>
<script type="module">
import {renderBack,renderFront,posAccentRgb,esc} from './assets/js/card-replica.js';
const cards=__CARDS__,examples=__EXAMPLES__,positions=__POSITIONS__,ranks=__RANKS__;let word='que',front=false;
const stage=document.getElementById('stage');
function model(d,pos,meanings){return{mode:'speech',word,lemma:word,pos,rank:ranks[word],vocabSize:10000,corpusCount:0,lookup:[],rareUses:[],meanings:meanings.map(m=>({...m,pct:100,examples:[{target:examples[word].text,english:examples[word].english}]}))}}
function section(pos,rows){const temp=document.createElement('template');temp.innerHTML=renderBack(model(cards[word],pos,rows),0,0);const group=temp.content.querySelector('.meaning-pos-section');group.querySelectorAll('.meaning-row').forEach(row=>row.removeAttribute('data-meaning-index'));return group}
function render(){document.querySelectorAll('[data-word]').forEach(b=>b.setAttribute('aria-pressed',b.dataset.word===word?'true':'false'));const d=cards[word];const primary=d.uses.map((u,i)=>({pos:positions[word][i],translation:u.english,context:u.description}));const cardModel=model(d,primary[0].pos,primary);stage.innerHTML=`<div class="card-replica"><div class="card${front?'':' flipped'}">${renderFront(cardModel)}${renderBack(cardModel,0,0)}</div></div>`;const back=stage.querySelector('.card-back');back.querySelector('.meanings-scroll').replaceChildren();const groups=new Map();primary.forEach(m=>{if(!groups.has(m.pos))groups.set(m.pos,[]);groups.get(m.pos).push(m)});for(const[pos,rows]of groups){back.querySelector('.meanings-scroll').append(section(pos,rows))}
back.querySelectorAll('.meaning-pos-section').forEach((s,i)=>{if(i){s.classList.remove('is-open');s.querySelector('.pos-section-head').setAttribute('aria-expanded','false')}});
if(d.phrases.length){const phrases=section('MWE',d.phrases.map(p=>({translation:`${p.text} · ${p.english}`})));phrases.classList.add('draft-phrases');phrases.classList.remove('is-open');phrases.querySelector('.pos-section-head').setAttribute('aria-expanded','false');back.querySelector('.meanings-scroll').append(phrases)}
back.querySelector('.back-headword-row').insertAdjacentHTML('beforeend','<span class="draft-grammar-badge">Grammar word</span>');if(d.parts){const target=word==='nos'?back.querySelector('[data-pos="CONTRACTION"] .meaning-pos-rows'):back.querySelector('.back-headword-row');target.insertAdjacentHTML('beforeend',`<div class="surface-relation-cue back-surface-relation grammar-pair-chips" aria-label="Parts of this contraction">${d.parts.map(p=>`<span class="grammar-pair-chip">${esc(p)}</span>`).join('<span class="grammar-pair-plus" aria-hidden="true">+</span>')}</div>`)}
back.querySelectorAll('.meaning-row').forEach(r=>r.classList.remove('selected','is-current-sense'));back.querySelectorAll('.sense-note-trigger').forEach(b=>b.remove());back.querySelector('.sentence').classList.remove('example-is-matched');back.querySelector('.knowledge-overview-trigger').remove();stage.querySelector('.card-freq-label')?.remove();back.querySelectorAll('.pos-section-head').forEach(h=>h.addEventListener('click',()=>{const s=h.closest('.meaning-pos-section'),opening=!s.classList.contains('is-open');back.querySelectorAll('.meaning-pos-section').forEach(other=>{other.classList.remove('is-open');other.querySelector('.pos-section-head').setAttribute('aria-expanded','false')});if(opening){s.classList.add('is-open');h.setAttribute('aria-expanded','true')}}));back.querySelector('.ref-lookup-btn').addEventListener('click',()=>window.open(`https://en.wiktionary.org/wiki/${encodeURIComponent(word)}#Portuguese`,'_blank','noopener'));stage.querySelector('.card-front').addEventListener('click',()=>{front=false;render()});back.querySelector('.flip-back-area').addEventListener('click',()=>{front=true;render()});}
document.getElementById('picker').innerHTML=Object.keys(cards).map(w=>`<button type="button" data-word="${w}" aria-pressed="false">${w}</button>`).join('')+'<button type="button" class="flip-toggle" id="flip">Flip card</button>';document.getElementById('picker').addEventListener('click',e=>{const b=e.target.closest('[data-word]');if(b){word=b.dataset.word;front=false;render()}});document.getElementById('flip').addEventListener('click',()=>{front=!front;render()});render();
</script></body></html>'''


def main():
    for kind, names in (("css", ("style.css", "appearance.css")), ("js", ("card-replica.js", "song-credit.js"))):
        target = OUT / "assets" / kind
        target.mkdir(parents=True, exist_ok=True)
        for name in names:
            shutil.copy2(ROOT / "app" / kind / name, target / name)
    if not (OUT / "index-v1.html").exists():
        shutil.copy2(OUT / "index.html", OUT / "index-v1.html")
    examples = json.loads((OUT / "examples.json").read_text())
    payload = HTML
    for name, value in (("CARDS", CARDS), ("EXAMPLES", examples), ("POSITIONS", POSITIONS), ("RANKS", RANKS)):
        payload = payload.replace("__" + name + "__", json.dumps(value, ensure_ascii=False))
    (OUT / "index.html").write_text(payload)
    print(OUT / "index.html")


if __name__ == "__main__":
    main()
