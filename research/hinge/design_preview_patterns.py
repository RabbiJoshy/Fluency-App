"""Format study: readable word overview and one useful phrase pattern at a time.

Illustrative phrase copy is handwritten for design review, not an assignment
pass or a replacement of dictionary data. Production remains unchanged.
"""
import json
import shutil
from pathlib import Path

from design_preview import CARDS, OUT
from design_preview_normal import RANKS

ROOT = Path(__file__).resolve().parents[2]
PATTERNS = {
    "que": [
        {"phrase": "o que", "english": "what", "purpose": "Ask what someone wants, says or does.", "pattern": "o que + a question", "target": "O que você quer?", "translation": "What do you want?"},
        {"phrase": "ter que", "english": "have to", "purpose": "Say someone has to do something.", "pattern": "ter que + an action", "target": "Tenho que ir.", "translation": "I have to go."},
        {"phrase": "assim que", "english": "as soon as", "purpose": "Say what happens as soon as something else happens.", "pattern": "assim que + what happens", "target": "Assim que chegar, eu te ligo.", "translation": "As soon as I arrive, I’ll call you."},
    ],
    "de": [
        {"phrase": "gostar de", "english": "like", "purpose": "Say what someone likes.", "pattern": "gostar de + what you like", "target": "Gosto de música.", "translation": "I like music."},
        {"phrase": "precisar de", "english": "need", "purpose": "Say what someone needs.", "pattern": "precisar de + what you need", "target": "Preciso de ajuda.", "translation": "I need help."},
        {"phrase": "ter de", "english": "have to", "purpose": "Say someone has to do something.", "pattern": "ter de + an action", "target": "Tenho de sair.", "translation": "I have to leave."},
    ],
    "se": [
        {"phrase": "lembrar-se de", "english": "remember", "purpose": "Say who or what someone remembers.", "pattern": "lembrar-se de + someone or something", "target": "Lembro-me de você.", "translation": "I remember you."},
        {"phrase": "preocupar-se com", "english": "worry about", "purpose": "Say who or what someone worries about.", "pattern": "preocupar-se com + someone or something", "target": "Ela se preocupa com você.", "translation": "She worries about you."},
    ],
    "o": [{"phrase": "o que", "english": "what", "purpose": "Ask what someone wants, says or does.", "pattern": "o que + a question", "target": "O que você quer?", "translation": "What do you want?"}],
}


# Handwritten illustrations for format review; these do not label corpus examples.
DEMONSTRATIONS = {
    "que": [
        ("Introduces what someone thinks, says or knows.", "Acho que vai chover.", "I think it’s going to rain.", "que", "that"),
        ("Adds information about a person or thing.", "Este é o livro que estou lendo.", "This is the book that I’m reading.", "que", "who / which / that"),
        ("Connects the two sides of a comparison.", "Ela é mais alta que eu.", "She is taller than me.", "que", "than"),
    ],
    "de": [("Shows a connection, possession or origin.", "Ela é de Lisboa.", "She is from Lisbon.", "de", "of / from")],
    "se": [
        ("Introduces a condition or an indirect question.", "Se chover, fico em casa.", "If it rains, I’ll stay home.", "Se", "if / whether"),
        ("Refers back to the person doing the action, or belongs with the verb.", "Ela se olhou no espelho.", "She looked at herself in the mirror.", "se", "-self / part of a verb"),
        ("Describes an action without naming who does it.", "Aqui se fala português.", "Portuguese is spoken here.", "se", "without naming who"),
    ],
    "o": [
        ("Introduces a masculine singular noun.", "O livro está na mesa.", "The book is on the table.", "O", "the"),
        ("Refers to the person or thing receiving the action.", "Eu o vi ontem.", "I saw him yesterday.", "o", "him / it"),
    ],
    "nos": [
        ("Refers to us as the people receiving the action.", "Ela nos chamou.", "She called us.", "nos", "us / to us"),
        ("Refers back to us as the people doing the action.", "Nós nos abraçamos.", "We hugged each other.", "nos", "ourselves / each other"),
        ("Combines em + os before a masculine plural noun.", "Está nos livros.", "It’s in the books.", "nos", "in / on / at the"),
    ],
    "naquele": [("Combines em + aquele to point to a particular place or time.", "Eu estava naquele lugar.", "I was in that place.", "naquele", "in / on / at that")],
}
for word, demonstrations in DEMONSTRATIONS.items():
    for use, (description, target, translation, highlight, english) in zip(CARDS[word]["uses"], demonstrations):
        use.update(description=description, target=target, translation=translation, highlight=highlight, english=english)

HTML = r'''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Portuguese · phrase patterns</title><link href="https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;600;700&family=Space+Grotesk:wght@600;700&display=swap" rel="stylesheet"><link rel="stylesheet" href="assets/css/appearance.css"><style>
*{box-sizing:border-box}body{margin:0;padding:25px 16px;min-height:100vh;background:var(--bg-primary);background-image:radial-gradient(ellipse at top,var(--bg-secondary),transparent 70%);color:var(--text-primary);font:19px/1.45 var(--font-reading)}button{font:inherit;cursor:pointer}button:focus-visible{outline:2px solid #67bf85;outline-offset:4px}.shell{max-width:1120px;margin:auto}.design-title{font:600 21px var(--font-emphasis);margin:0 0 7px}.design-note{font-size:18px;color:var(--text-muted);margin:0 0 18px}.words{display:flex;gap:8px;flex-wrap:wrap;margin-bottom:24px}.words button,.view-switch button{border:1px solid var(--border-light);border-radius:20px;background:var(--bg-tertiary);color:var(--text-primary);padding:7px 17px;font-size:19px}.words button[aria-pressed=true],.view-switch button[aria-pressed=true]{border-color:#67bf85;color:#91d4a8}.layout{display:grid;grid-template-columns:minmax(0,640px) 240px;gap:34px;justify-content:center;align-items:start}.surface{background:var(--bg-card);border:1px solid var(--border-color);border-radius:20px;box-shadow:0 18px 55px #0003;padding:27px 28px;min-width:0}.layout.word-view{grid-template-columns:minmax(0,640px)}[data-flip]{cursor:pointer}[data-flip]:focus-visible{outline:2px solid #91d4a8;outline-offset:4px}.word-heading{font:700 46px/1.1 var(--font-emphasis);text-align:center;margin:0 0 27px}.overview{display:grid;gap:18px}.use{border:1px solid #35463d;border-radius:11px;padding:15px 18px;background:#1b302608}.use{width:100%;text-align:left;color:var(--text-primary);font:inherit;cursor:pointer}.use[aria-pressed=true]{border-color:#91d4a8;background:#22382d}.use strong{display:block;font:700 27px var(--font-reading)}.use p{font-size:20px;line-height:1.4;color:var(--text-muted);margin:5px 0 0}.existing-example{margin-top:23px;background:#0d151c;border-radius:12px;padding:20px;text-align:center}.existing-example .target{font-size:24px}.existing-example .translation{border-top:1px solid var(--border-light);padding-top:13px;margin-top:13px;font-size:20px;color:var(--text-secondary)}.existing-example mark{background:none;color:#91d4a8;font-weight:700;text-decoration:underline;text-underline-offset:4px}.next{display:block;width:100%;margin-top:24px;text-align:center;border:1px solid #50735e;border-radius:10px;padding:13px 16px;background:#22382d;color:#e4f5eb;font-size:21px;font-weight:600}.parts{display:flex;justify-content:center;gap:10px;font-size:24px;margin:0 0 20px}.parent{display:flex;justify-content:space-between;gap:12px;color:var(--text-muted);font-size:20px;margin-bottom:23px}.parent button{border:0;background:none;color:var(--text-muted);padding:0;font-size:19px;text-align:left}.phrase-title{font:700 44px/1.15 var(--font-emphasis);margin:0 0 7px;letter-spacing:-.7px;color:#91d4a8}.phrase-english{font-size:29px;font-weight:600;margin:0 0 18px}.purpose{font-size:22px;line-height:1.4;margin:0 0 24px;color:var(--text-secondary)}.pattern{background:#172d22;border:1px solid #46634f;border-radius:12px;padding:19px 20px;font-size:25px;line-height:1.45;text-align:center}.pattern .slot{display:inline;border-bottom:2px dashed #a3beab;color:#c7e7d3;padding-bottom:2px}.illustration{margin-top:24px;background:#0d151c;border-radius:12px;padding:23px;text-align:center}.illustration .pt{font-size:28px;line-height:1.4;margin:0 0 15px}.illustration .en{font-size:22px;line-height:1.4;color:var(--text-secondary);border-top:1px solid var(--border-light);padding-top:15px}.phrase-nav{display:flex;gap:12px;justify-content:space-between;align-items:center;margin-top:25px}.phrase-nav button{padding:10px 0;color:var(--text-secondary);background:none;border:0;font-size:20px}.phrase-nav button.next-phrase{color:#91d4a8;font-weight:600}.view-switch{display:grid;gap:10px}.aside{font-size:20px;color:var(--text-muted);padding-top:6px}.aside p{margin:0 0 22px}.aside strong{color:var(--text-primary)}.aside .phrase-choices{display:grid;gap:9px;margin-top:24px}.phrase-choice{font:600 20px var(--font-reading);padding:12px 15px;border:1px solid var(--border-light);border-radius:10px;text-align:left;background:var(--bg-tertiary);color:var(--text-primary)}.phrase-choice[aria-pressed=true]{border-color:#67bf85;color:#91d4a8}.front{min-height:525px;display:flex;flex-direction:column}.front .front-word{font:700 56px var(--font-emphasis);margin:auto;text-align:center}.stats{display:flex;justify-content:space-between;gap:22px}.stat{font-size:20px;color:var(--text-muted)}.stat:last-child{text-align:right}.stat b{display:block;color:var(--text-primary);font:700 33px var(--font-emphasis);margin-top:2px}.stat .unit{font-size:18px}.front-reveal{margin-top:24px}.back-front{font-size:19px;color:var(--text-muted);padding:12px 0 0;border:0;background:none;display:block;margin:auto}
@media(max-width:800px){body{padding:18px 10px}.layout{display:block}.surface{padding:24px 20px;border-radius:18px}.aside{margin:22px 5px 0}.aside p{display:none}.view-switch{display:flex;flex-wrap:wrap}.view-switch button{padding:7px 12px}.aside .phrase-choices{display:flex;flex-wrap:wrap;margin-top:15px}.phrase-choice{padding:8px 13px}.words{gap:6px;margin-bottom:18px}.words button{padding:6px 12px;font-size:18px}.design-note{font-size:18px;line-height:1.4}.word-heading{font-size:42px;margin-bottom:22px}.use{padding:14px 15px}.use{width:100%;text-align:left;color:var(--text-primary);font:inherit;cursor:pointer}.use[aria-pressed=true]{border-color:#91d4a8;background:#22382d}.use strong{font-size:25px}.use p{font-size:19px}.phrase-title{font-size:39px}.phrase-english{font-size:27px}.purpose{font-size:21px}.pattern{font-size:23px;padding:17px 15px}.illustration{padding:20px 16px}.illustration .pt{font-size:25px}.illustration .en{font-size:21px}.parent{font-size:19px;margin-bottom:22px}.phrase-nav{align-items:flex-start}.phrase-nav button{font-size:19px;max-width:55%;text-align:left}.phrase-nav button.next-phrase{text-align:right}.front{min-height:470px}.stat{font-size:18px}.stat .unit{font-size:18px}.existing-example .target{font-size:23px}.existing-example .translation{font-size:20px}}
</style></head><body><main class="shell"><h1 class="design-title">Portuguese · format draft</h1><p class="design-note">A simple word overview, followed by useful phrase patterns. Illustrative wording; no deck changes.</p><nav class="words" id="words" aria-label="Choose a word"></nav><div class="layout"><div id="stage"></div><aside class="aside"><p><strong>Learn the useful combination.</strong><br>One pattern at a time, with room for a clear illustration.</p><div class="phrase-choices" id="choices"></div></aside></div></main><script>
const cards=__CARDS__,examples=__EXAMPLES__,patterns=__PATTERNS__,ranks=__RANKS__,frequencies=__FREQUENCY__;let word='que',view='back',phraseIndex=0,useIndex=0;const esc=s=>String(s).replaceAll('&','&amp;').replaceAll('<','&lt;').replaceAll('>','&gt;').replaceAll('"','&quot;');
function render(){const d=cards[word],e=examples[word],list=patterns[word]||[];document.querySelectorAll('[data-word]').forEach(b=>b.setAttribute('aria-pressed',String(b.dataset.word===word)));document.querySelectorAll('[data-view]').forEach(b=>b.setAttribute('aria-pressed',String(b.dataset.view===view)));document.querySelector('.aside').hidden=view!=='phrases';document.querySelector('.layout').classList.toggle('word-view',view!=='phrases');document.getElementById('choices').innerHTML=view==='phrases'?list.map((p,i)=>`<button class="phrase-choice" data-phrase="${i}" aria-pressed="${i===phraseIndex}">${esc(p.phrase)}</button>`).join(''):'';let html='';if(view==='front'){html=`<section class="surface front" data-flip tabindex="0" aria-label="Word front. Tap to see its uses."><div class="front-word">${esc(word)}</div><div class="stats"><div class="stat">Vocabulary rank<b>${ranks[word].toLocaleString()}</b><span class="unit">of 10,000</span></div><div class="stat">Frequency<b>${Math.round(frequencies[word]).toLocaleString()}</b><span class="unit">per million</span></div></div></section>` }else if(view==='back'){const u=d.uses[useIndex];const highlight=esc(u.highlight);html=`<section class="surface" data-flip tabindex="0" aria-label="Word back. Tap the card background to see the front."><h2 class="word-heading">${esc(word)}</h2>${d.parts&&word!=='nos'?`<div class="parts">${d.parts.map(p=>esc(p)).join(' + ')}</div>`:''}<div class="overview" aria-label="Choose a use">${d.uses.map((u,i)=>`<button class="use" data-use="${i}" aria-pressed="${i===useIndex}"><strong>${esc(u.english)}</strong><p>${esc(u.description)}</p></button>`).join('')}</div><div class="existing-example" aria-live="polite"><div class="target">${esc(u.target).replace(highlight,`<mark>${highlight}</mark>`)}</div><div class="translation">${esc(u.translation)}</div></div>${list.length?`<button class="next" data-view="phrases">Learn combinations with ${esc(word)} →</button>`:''}</section>`}else{const p=list[phraseIndex];const bits=p.pattern.split(' + ');html=`<section class="surface"><div class="parent"><button data-view="back">← ${esc(word)}</button><span>${phraseIndex+1} of ${list.length}</span></div><h2 class="phrase-title">${esc(p.phrase)}</h2><p class="phrase-english">${esc(p.english)}</p><p class="purpose">${esc(p.purpose)}</p><div class="pattern">${esc(bits[0])}${bits[1]?` + <span class="slot">${esc(bits[1])}</span>`:''}</div><div class="illustration"><p class="pt">${esc(p.target)}</p><div class="en">${esc(p.translation)}</div></div><nav class="phrase-nav" aria-label="Move between phrase patterns">${phraseIndex?`<button data-phrase="${phraseIndex-1}">← ${esc(list[phraseIndex-1].phrase)}</button>`:'<span></span>'}${phraseIndex+1<list.length?`<button class="next-phrase" data-phrase="${phraseIndex+1}">${esc(list[phraseIndex+1].phrase)} →</button>`:`<button class="next-phrase" data-view="back">Back to ${esc(word)} →</button>`}</nav></section>`}document.getElementById('stage').innerHTML=html}
document.getElementById('words').innerHTML=Object.keys(cards).map(w=>`<button data-word="${w}" aria-pressed="false">${w}</button>`).join('');document.addEventListener('click',e=>{const w=e.target.closest('[data-word]'),v=e.target.closest('[data-view]'),p=e.target.closest('[data-phrase]'),u=e.target.closest('[data-use]');if(u){useIndex=Number(u.dataset.use);render()}else if(w){word=w.dataset.word;view='back';phraseIndex=0;useIndex=0;render()}else if(v){view=v.dataset.view;if(view==='phrases')phraseIndex=0;render()}else if(p){phraseIndex=Number(p.dataset.phrase);view='phrases';render()}else if(e.target.closest('[data-flip]')&&!e.target.closest('button')){view=view==='front'?'back':'front';render()}});document.addEventListener('keydown',e=>{if((e.key==='Enter'||e.key===' ')&&e.target.matches('[data-flip]')){e.preventDefault();view=view==='front'?'back':'front';render()}});render();
</script></body></html>'''


def main():
    config = json.loads((ROOT / "app/config/config.json").read_text())
    frequency = json.loads((ROOT / "app" / config["languages"]["portuguese"]["frequencyPath"]).read_text())["values"]
    examples = json.loads((OUT / "examples.json").read_text())
    shutil.copy2(OUT / "index.html", OUT / "index-sequence.html")
    payload = HTML
    for name, value in (("CARDS", CARDS), ("EXAMPLES", examples), ("PATTERNS", PATTERNS), ("RANKS", RANKS), ("FREQUENCY", {w: frequency[w] for w in CARDS})):
        payload = payload.replace("__" + name + "__", json.dumps(value, ensure_ascii=False))
    (OUT / "index.html").write_text(payload)
    print(OUT / "index.html")


if __name__ == "__main__":
    main()
