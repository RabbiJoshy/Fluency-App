"""Generate the small Portuguese card-design draft without changing the app.

Uses are editorial card-level facts. Existing sentences/translations are copied
unchanged; this draft neither labels examples nor edits learner progress.
"""
import json
from pathlib import Path

OUT = Path(__file__).resolve().parents[3] / "Fluency-Workspace/audits/hinge-20261014/portuguese-card-preview"

CARDS = {
    "que": {
        "uses": [
            {"english": "that", "description": "Introduces a statement: Acho que vai chover."},
            {"english": "who / which / that", "description": "Adds a description: Este é o livro que estou lendo."},
            {"english": "than", "description": "Makes a comparison: Ela é mais alta que eu."},
        ],
        "phrases": [{"text": "o que", "english": "what"}, {"text": "ter que", "english": "have to"}, {"text": "assim que", "english": "as soon as"}],
    },
    "de": {
        "uses": [{"english": "of / from", "description": "Connects words: a casa de Ana · de Lisboa"}],
        "phrases": [{"text": "gostar de", "english": "like"}, {"text": "precisar de", "english": "need"}, {"text": "ter de", "english": "have to"}],
    },
    "se": {
        "uses": [
            {"english": "if / whether", "description": "Introduces a condition or an indirect question."},
            {"english": "-self / part of a verb", "description": "Can refer back to the subject, or be part of a verb such as lembrar-se."},
            {"english": "without naming who", "description": "Leaves the person doing the action unnamed: Aqui se fala português."},
        ],
        "phrases": [],
    },
    "o": {
        "uses": [
            {"english": "the", "description": "Before a masculine singular noun: o livro."},
            {"english": "him / it", "description": "An object pronoun, before or attached to a verb."},
        ],
        "phrases": [{"text": "o que", "english": "what"}],
    },
    "nos": {
        "uses": [
            {"english": "us / to us", "description": "An object pronoun used with a verb."},
            {"english": "ourselves / each other", "description": "With a verb, it can refer back to nós."},
            {"english": "in / on / at the", "description": "A contraction of em + os, before a masculine plural noun."},
        ],
        "parts": ["em", "os"],
        "partsLabel": "When used as a contraction",
        "phrases": [],
    },
    "naquele": {
        "uses": [{"english": "in / on / at that", "description": "A contraction of em + aquele: naquele dia · on that day."}],
        "parts": ["em", "aquele"],
        "phrases": [],
    },
}

HTML = r'''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Portuguese grammar cards — design draft</title>
<style>
:root{color-scheme:dark;--bg:#0c1116;--panel:#1c242e;--ink:#f4f5f6;--muted:#b1bbc6;--accent:#67bf85;--line:#35414e}
*{box-sizing:border-box}body{margin:0;background:radial-gradient(ellipse at top,#1b2934,var(--bg) 68%);color:var(--ink);font:15px/1.45 system-ui,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;min-height:100vh}
main{max-width:1050px;margin:auto;padding:32px 20px}header{margin:0 auto 22px;max-width:680px}header p{margin:5px 0;color:var(--muted);font-size:13px}h1{font-size:22px;margin:0 0 7px;letter-spacing:-.4px}.eyebrow{color:var(--accent);font-size:11px;letter-spacing:.12em;text-transform:uppercase;margin-bottom:7px}
.word-picker{display:flex;flex-wrap:wrap;gap:7px;margin:19px 0 0}.word-picker button{font:inherit;font-weight:600;color:var(--muted);background:#17212b;border:1px solid var(--line);padding:7px 15px;border-radius:20px;cursor:pointer}.word-picker button[aria-pressed=true]{color:#08150e;background:var(--accent);border-color:var(--accent)}
.layout{display:grid;grid-template-columns:minmax(0,520px) 230px;gap:28px;justify-content:center;align-items:start}.card{background:var(--panel);border:1px solid #2b3540;border-radius:22px;box-shadow:0 20px 65px #0004;padding:23px 25px 25px;min-width:0}.head{display:flex;justify-content:space-between;gap:12px;align-items:center;margin-bottom:20px}.head h2{font-size:43px;line-height:1.1;margin:0;letter-spacing:-1.1px}.badge{font-size:11px;color:var(--accent);border:1px solid #4d805f;border-radius:20px;padding:4px 9px;white-space:nowrap}.section-title{font-size:11px;color:var(--muted);text-transform:uppercase;letter-spacing:.1em;font-weight:600;margin:17px 0 7px}.uses{display:grid;gap:0}.use{padding:10px 0;border-bottom:1px solid var(--line)}.use:last-child{border:0}.use strong{font-size:18px;letter-spacing:-.2px}.use p{font-size:13px;color:var(--muted);margin:3px 0 0;line-height:1.45}.phrases{display:flex;flex-wrap:wrap;gap:7px}.phrase{padding:7px 10px;background:#18241e;border:1px solid #385947;border-radius:9px;font-size:13px}.phrase b{font-weight:600;color:#e4f4e9}.phrase span{color:#bcd0c3}.parts{display:flex;flex-wrap:wrap;align-items:center;gap:8px;margin:7px 0 4px}.part{font:inherit;color:var(--ink);text-decoration:none;background:#273240;border:1px solid #4b596b;border-radius:8px;padding:5px 14px}.part-note{font-size:11px;color:var(--muted);margin-top:10px}.example{background:#101820;padding:17px;border-radius:12px;margin-top:20px;text-align:center}.target{font-size:19px;line-height:1.4;overflow-wrap:anywhere}.target mark{background:none;color:var(--accent);font-weight:700;text-decoration:underline;text-decoration-thickness:2px;text-underline-offset:3px}.english{font-size:14px;padding-top:12px;margin-top:12px;border-top:1px solid #303b45;color:#d0d8e0}.face-toggle{display:block;margin:17px auto 0;font:inherit;font-size:12px;color:var(--muted);background:none;border:0;text-decoration:underline;text-underline-offset:3px;cursor:pointer}.front{min-height:420px;display:flex;flex-direction:column;align-items:center;justify-content:center}.front h2{font-size:56px;margin:0 0 14px;letter-spacing:-1.5px}.front .parts{margin-top:17px}.notes{color:var(--muted);font-size:13px;padding-top:16px}.notes h3{font-size:14px;color:var(--ink);margin:0 0 12px}.notes p{margin:0 0 15px}.notes b{color:#dbe4ed}button:focus-visible,a:focus-visible{outline:2px solid #e5f9e6;outline-offset:4px}[hidden]{display:none!important}
@media(max-width:760px){main{padding:19px 12px}.layout{display:block;max-width:520px;margin:auto}header{max-width:520px;margin-bottom:17px}.notes{margin:20px 5px 0}.card{padding:20px 20px 22px;border-radius:19px}.head h2{font-size:39px}.head{margin-bottom:13px}.uses .use{padding:9px 0}.word-picker{gap:6px}.word-picker button{padding:6px 12px}.example{padding:14px;margin-top:16px}.target{font-size:18px}}
</style></head><body><main>
<header><div class="eyebrow">Portuguese · design draft</div><h1>A clear overview before the examples</h1><p>Six card designs. Existing sentences and translations are unchanged; example labels are deferred.</p><nav class="word-picker" aria-label="Choose a draft card" id="picker"></nav></header>
<div class="layout"><section class="card" aria-label="Grammar-word card preview" id="card"></section><aside class="notes"><h3>Proposed method</h3><p><b>Choose the word deliberately.</b> A card gets this overview because of its grammatical uses.</p><p><b>Give each use room.</b> Explain it in plain English, instead of compressing everything into chips.</p><p><b>Keep phrases separate.</b> They illustrate common combinations, rather than a ranking from the sampled examples.</p><p><b>Keep examples neutral for now.</b> No role chip or percentage claims which use a sentence demonstrates.</p><p><b>Keep both readings visible.</b> For nos, the contraction is one use alongside the pronoun uses.</p></aside></div>
</main><script>
const cards=__CARDS__,examples=__EXAMPLES__;let selected='que',front=false;
const esc=s=>String(s).replaceAll('&','&amp;').replaceAll('<','&lt;').replaceAll('>','&gt;').replaceAll('"','&quot;');
function parts(d){return d.parts?`${d.partsLabel?`<div class="part-note">${esc(d.partsLabel)}</div>`:''}<div class="parts" aria-label="Parts of the contraction">${d.parts.map(p=>`<span class="part">${esc(p)}</span>`).join('<span aria-hidden="true">+</span>')}</div>`:''}
function render(){const d=cards[selected],e=examples[selected];document.querySelectorAll('#picker button').forEach(b=>b.setAttribute('aria-pressed',b.dataset.word===selected?'true':'false'));const re=new RegExp('(?<![\\p{L}])'+selected+'(?![\\p{L}])','giu');const target=esc(e.text).replace(re,t=>`<mark>${t}</mark>`);document.getElementById('card').innerHTML=front?`<div class="front"><h2>${esc(selected)}</h2><span class="badge">Grammar word</span></div><button class="face-toggle" onclick="flip()">Show uses and example</button>`:`<div class="head"><h2>${esc(selected)}</h2><span class="badge">Grammar word</span></div><div class="section-title">Uses</div><div class="uses">${d.uses.map(u=>`<div class="use"><strong>${esc(u.english)}</strong><p>${esc(u.description)}</p></div>`).join('')}</div>${parts(d)}${d.phrases.length?`<div class="section-title">Common phrases</div><div class="phrases">${d.phrases.map(p=>`<div class="phrase"><b>${esc(p.text)}</b><span> · ${esc(p.english)}</span></div>`).join('')}</div>`:''}<div class="example"><div class="target">${target}</div><div class="english">${esc(e.english)}</div></div><button class="face-toggle" onclick="flip()">Show front</button>`}
function flip(){front=!front;render()};document.getElementById('picker').innerHTML=Object.keys(cards).map(w=>`<button type="button" data-word="${w}" aria-pressed="false">${w}</button>`).join('');document.getElementById('picker').addEventListener('click',e=>{const b=e.target.closest('button');if(b){selected=b.dataset.word;front=false;render()}});render();
</script></body></html>'''


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    examples = json.loads((OUT / "examples.json").read_text())
    payload = HTML.replace("__CARDS__", json.dumps(CARDS, ensure_ascii=False)).replace("__EXAMPLES__", json.dumps(examples, ensure_ascii=False))
    (OUT / "index.html").write_text(payload)
    (OUT / "card-copy.json").write_text(json.dumps(CARDS, ensure_ascii=False, indent=2) + "\n")
    print(OUT / "index.html")


if __name__ == "__main__":
    main()
