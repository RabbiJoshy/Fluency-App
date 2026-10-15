"""Standalone card preview, rendered from the reviewed data (no copied examples)."""
import json


def render(originals, proposals, ledger):
    data = json.dumps({'before': {l: {w: originals[l][w] for w in words} for l,words in proposals.items()},
                       'after': proposals, 'ledger': ledger}, ensure_ascii=False).replace('<', '\\u003c')
    return '''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Function-word pilot · review</title><style>
*{box-sizing:border-box}body{margin:0;background:#10151e;color:#e7edf6;font:17px/1.6 system-ui,sans-serif}main{max-width:1200px;margin:auto;padding:32px}h1{font-size:32px;margin-bottom:6px}.muted,small{color:#afbdd0}nav{display:flex;flex-wrap:wrap;gap:14px;margin:24px 0}label{display:flex;align-items:center;gap:8px}select,button{font:inherit;color:inherit;background:#253043;border:1px solid #576980;border-radius:9px;padding:8px 14px}button{cursor:pointer}button:focus-visible,select:focus-visible{outline:3px solid #b1bfff;outline-offset:3px}.columns{display:grid;grid-template-columns:1fr 1fr;gap:20px}.card{min-width:0;background:#192231;border:1px solid #38485f;border-radius:18px;padding:25px}.formula{padding:18px;background:#101925;border-radius:10px;line-height:2}.sentence{font-size:23px;padding-top:15px}.fw-token-v{color:#9fd5b8;text-decoration:underline;text-decoration-style:dotted;text-underline-offset:5px}.fw-token-connector{color:#d8d9ff;font-weight:800;border-bottom:2px solid}.fw-token-c{color:#ffc799;text-decoration:underline;text-underline-offset:5px}.parts{display:inline-block;border:1px solid #71829b;border-radius:8px;padding:4px 10px}.notes{margin-top:24px;padding:20px;border-left:3px solid #a3b5ef;background:#192231}h2{margin-top:0}footer{margin-top:30px}#count{min-width:130px;text-align:center}@media(max-width:750px){main{padding:18px}.columns{grid-template-columns:1fr}.card{padding:18px}h1{font-size:27px}}
</style><main><p class="muted">EDITORIAL PILOT · PROPOSALS ONLY</p><h1>Small words, clearer patterns</h1><p>Compare the current cards with the proposed wording. Nothing here changes the live decks.</p>
<nav><label>Language <select id="language"><option value="pt">Portuguese</option><option value="es">Spanish</option></select></label><label>Word <select id="word"></select></label><label>Pattern <select id="pattern"></select></label></nav>
<div class="columns"><section class="card" id="before"></section><section class="card" id="after"></section></div>
<nav aria-label="Example navigation"><button id="previous">← Previous example</button><span id="count" aria-live="polite"></span><button id="next">Next example →</button></nav><div class="notes" id="notes"></div>
<footer class="muted">Underlined chunks match the formula; the bold connector is the word being taught. Examples are editorial judgments, not automated naturalness scores. Portuguese defaults to Brazilian usage; valid formal forms remain where needed for recognition.</footer></main><script>
const DATA = ''' + data + ''';
const $=id=>document.getElementById(id);let example=0;
const esc=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
function options(el,values){el.replaceChildren(...values.map(([value,label])=>{const o=document.createElement('option');o.value=value;o.textContent=label;return o}));}
function words(){options($('word'),Object.keys(DATA.after[$('language').value]).map(w=>[w,w]));patterns();}
function patterns(){const entry=DATA.after[$('language').value][$('word').value];options($('pattern'),entry.relations.map((r,i)=>[i,r.tag]));example=0;draw();}
function draw(){const l=$('language').value,w=$('word').value,p=Number($('pattern').value);for(const side of ['before','after']){const entry=DATA[side][l][w],r=entry.relations[p],e=r.examples[example],parts=r.parts||entry.parts;$(side).innerHTML=`<h2>${side==='before'?'Current':'Proposed'} · ${esc(w)}</h2><p>${esc(r.tag)}</p>${parts?`<p class="parts">${esc(parts.join(' + '))} = ${esc(w)}</p>`:''}<div class="formula">${r.formulaHTML}</div><p>${esc(r.rule)}</p><p class="sentence" lang="${l==='pt'?'pt-BR':'es'}">${e.targetHTML}</p><p>${esc(e.translation)}</p><small>${esc(e.source)}</small>`;}
const n=DATA.after[l][w].relations[p].examples.length;$('count').textContent=`Example ${example+1} of ${n}`;
const row=DATA.ledger.find(r=>r.language===l&&r.word===w&&r.pattern===p&&r.example===example);$('notes').textContent=row.reasons.join(' ')+' '+row.provenance;}
$('language').onchange=words;$('word').onchange=patterns;$('pattern').onchange=()=>{example=0;draw()};
function cycle(delta){const n=DATA.after[$('language').value][$('word').value].relations[Number($('pattern').value)].examples.length;example=(example+delta+n)%n;draw();}
$('previous').onclick=()=>cycle(-1);$('next').onclick=()=>cycle(1);words();
</script></html>'''
