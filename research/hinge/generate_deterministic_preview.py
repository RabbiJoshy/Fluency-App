"""Interactive draft with deterministic example cycling across content words.

Shows the six focus words (que, de, se, o, nos, naquele) with taxonomy badges,
independent grammatical uses, and deterministic examples cycling content verbs/words.
"""
import json
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parents[3] / "Fluency-Workspace/audits/hinge-20261014/portuguese-card-preview"
DESIGN_DIR = Path(__file__).resolve().parents[3] / "Fluency-Workspace/handoffs/hinge-20261014/design"

RANKS = {"que": 1, "o": 3, "de": 4, "se": 11, "nos": 44, "naquele": 1104}

CARDS = {
    "que": {
        "role": "Connector",
        "posColors": ["34, 197, 94", "108, 92, 246"],  # Conjunction (green) + Relative pronoun (violet)
        "uses": [
            {
                "english": "that",
                "description": "Introduces what someone thinks, says or knows.",
                "examples": [
                    {"target": "Acho que vai chover.", "translation": "I think it’s going to rain.", "highlight": "que", "content": "achar"},
                    {"target": "Sei que você está certo.", "translation": "I know that you are right.", "highlight": "que", "content": "saber"},
                    {"target": "Ela disse que viria.", "translation": "She said that she would come.", "highlight": "que", "content": "dizer"},
                ]
            },
            {
                "english": "who / which / that",
                "description": "Adds information about a person or thing.",
                "examples": [
                    {"target": "Este é o livro que estou lendo.", "translation": "This is the book that I’m reading.", "highlight": "que", "content": "livro"},
                    {"target": "A pessoa que me ajudou foi embora.", "translation": "The person who helped me left.", "highlight": "que", "content": "pessoa"},
                ]
            },
            {
                "english": "than",
                "description": "Connects the two sides of a comparison.",
                "examples": [
                    {"target": "Ela é mais alta que eu.", "translation": "She is taller than me.", "highlight": "que", "content": "mais alta"},
                    {"target": "Este café é melhor que o outro.", "translation": "This coffee is better than the other.", "highlight": "que", "content": "melhor"},
                ]
            },
        ]
    },
    "de": {
        "role": "Preposition",
        "posColors": ["236, 72, 153"],  # Preposition (pink)
        "uses": [
            {
                "english": "of / from",
                "description": "Shows connection, possession or origin.",
                "examples": [
                    {"target": "Ela é de Lisboa.", "translation": "She is from Lisbon.", "highlight": "de", "content": "origem"},
                    {"target": "A casa de Ana é bonita.", "translation": "Ana's house is beautiful.", "highlight": "de", "content": "posse"},
                    {"target": "Quero um copo de água.", "translation": "I want a glass of water.", "highlight": "de", "content": "conteúdo"},
                ]
            },
            {
                "english": "connects a verb to its object",
                "description": "Required link after common verbs before a noun or action.",
                "examples": [
                    {"target": "Gosto de música.", "translation": "I like music.", "highlight": "de", "content": "gostar"},
                    {"target": "Preciso de ajuda.", "translation": "I need help.", "highlight": "de", "content": "precisar"},
                    {"target": "Tudo depende de você.", "translation": "Everything depends on you.", "highlight": "de", "content": "depender"},
                ]
            },
        ]
    },
    "se": {
        "role": "Conjunction & Clitic",
        "posColors": ["34, 197, 94", "108, 92, 246"],  # Conjunction (green) + Clitic pronoun (violet)
        "uses": [
            {
                "english": "if / whether",
                "description": "Introduces a condition or an indirect question.",
                "examples": [
                    {"target": "Se chover, fico em casa.", "translation": "If it rains, I’ll stay home.", "highlight": "Se", "content": "condição"},
                    {"target": "Não sei se ele vem.", "translation": "I don't know if he is coming.", "highlight": "se", "content": "dúvida"},
                ]
            },
            {
                "english": "-self / each other",
                "description": "Action reflects back on the person doing it.",
                "examples": [
                    {"target": "Ela se olhou no espelho.", "translation": "She looked at herself in the mirror.", "highlight": "se", "content": "olhar"},
                    {"target": "Ele se levantou cedo.", "translation": "He got [himself] up early.", "highlight": "se", "content": "levantar"},
                    {"target": "Nós nos abraçamos com carinho.", "translation": "We hugged each other warmly.", "highlight": "nos", "content": "abraçar"},
                ]
            },
            {
                "english": "action without naming who",
                "description": "Describes something done generally or passively.",
                "examples": [
                    {"target": "Aqui se fala português.", "translation": "Portuguese is spoken here.", "highlight": "se", "content": "falar"},
                    {"target": "Vende-se esta casa.", "translation": "This house is for sale.", "highlight": "se", "content": "vender"},
                ]
            },
        ]
    },
    "o": {
        "role": "Article & Pronoun",
        "posColors": ["239, 68, 68", "108, 92, 246"],  # Article (coral red) + Pronoun (violet)
        "uses": [
            {
                "english": "the",
                "description": "Before a masculine singular noun.",
                "examples": [
                    {"target": "O livro está na mesa.", "translation": "The book is on the table.", "highlight": "O", "content": "livro"},
                    {"target": "O dia está lindo.", "translation": "The day is beautiful.", "highlight": "O", "content": "dia"},
                ]
            },
            {
                "english": "him / it",
                "description": "Object pronoun receiving the action of a verb.",
                "examples": [
                    {"target": "Eu o vi ontem no parque.", "translation": "I saw him yesterday in the park.", "highlight": "o", "content": "ver"},
                    {"target": "Não consigo encontrá-lo.", "translation": "I cannot find it.", "highlight": "lo", "content": "encontrar"},
                ]
            },
        ]
    },
    "nos": {
        "role": "Pronoun & Contraction",
        "posColors": ["108, 92, 246", "251, 120, 50"],  # Pronoun (violet) + Contraction (amber)
        "uses": [
            {
                "english": "us / to us",
                "description": "Object pronoun receiving the action.",
                "examples": [
                    {"target": "Ela nos chamou para jantar.", "translation": "She called us for dinner.", "highlight": "nos", "content": "chamar"},
                    {"target": "Eles nos disseram a verdade.", "translation": "They told us the truth.", "highlight": "nos", "content": "dizer"},
                ]
            },
            {
                "english": "ourselves / each other",
                "description": "Reflexive or reciprocal action done by nós.",
                "examples": [
                    {"target": "Nós nos abraçamos.", "translation": "We hugged each other.", "highlight": "nos", "content": "abraçar"},
                    {"target": "Nós nos conhecemos bem.", "translation": "We know each other well.", "highlight": "nos", "content": "conhecer"},
                ]
            },
            {
                "english": "in / on / at the",
                "description": "Contraction of em + os before a masculine plural noun.",
                "parts": ["em", "os"],
                "examples": [
                    {"target": "Está nos livros.", "translation": "It’s in the books.", "highlight": "nos", "content": "livros"},
                    {"target": "Eles moram nos Estados Unidos.", "translation": "They live in the United States.", "highlight": "nos", "content": "Estados Unidos"},
                ]
            },
        ]
    },
    "naquele": {
        "role": "Contraction",
        "posColors": ["251, 120, 50"],  # Contraction (amber)
        "parts": ["em", "aquele"],
        "partsLabel": "Contraction formula",
        "uses": [
            {
                "english": "in that / on that",
                "description": "Points to a particular place or time.",
                "examples": [
                    {"target": "Eu estava naquele lugar.", "translation": "I was in that place.", "highlight": "naquele", "content": "lugar"},
                    {"target": "Tudo começou naquele dia.", "translation": "Everything started on that day.", "highlight": "naquele", "content": "dia"},
                    {"target": "Naquele momento, tudo mudou.", "translation": "At that moment, everything changed.", "highlight": "Naquele", "content": "momento"},
                ]
            }
        ]
    }
}

HTML = r'''<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Portuguese Grammar Words · Deterministic Cycling</title>
<link href="https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Space+Grotesk:wght@600;700&display=swap" rel="stylesheet">
<link rel="stylesheet" href="assets/css/appearance.css">
<style>
:root{
  --bg-primary: #0c1116;
  --bg-secondary: #131c24;
  --bg-tertiary: #18232d;
  --bg-card: #151f28;
  --border-color: #2b3947;
  --border-light: #23313f;
  --text-primary: #f4f5f6;
  --text-secondary: #c2cbd4;
  --text-muted: #8d9aa7;
  --font-reading: "DM Sans", -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
  --font-emphasis: "Space Grotesk", -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
}
*{box-sizing:border-box}
body{
  margin:0;
  padding:28px 16px;
  min-height:100vh;
  background:var(--bg-primary);
  background-image:radial-gradient(ellipse at top,#162432,transparent 75%);
  color:var(--text-primary);
  font:19px/1.45 var(--font-reading);
}
button{font:inherit;cursor:pointer}
button:focus-visible{outline:2px solid #67bf85;outline-offset:4px}
.shell{max-width:1100px;margin:auto}
.header{margin-bottom:24px}
.title{font:700 24px var(--font-emphasis);margin:0 0 6px;letter-spacing:-.4px}
.subtitle{font-size:17px;color:var(--text-muted);margin:0}
.words-nav{display:flex;gap:8px;flex-wrap:wrap;margin:18px 0 28px}
.words-nav button{
  border:1px solid var(--border-light);
  border-radius:20px;
  background:var(--bg-tertiary);
  color:var(--text-primary);
  padding:8px 18px;
  font-size:18px;
  font-weight:600;
  transition:all .15s ease;
}
.words-nav button[aria-pressed=true]{
  border-color:#67bf85;
  background:#1e3529;
  color:#91d4a8;
}
.layout{
  display:grid;
  grid-template-columns:minmax(0,620px) 320px;
  gap:32px;
  justify-content:center;
  align-items:start;
}
.surface{
  position:relative;
  background:var(--bg-card);
  border:1px solid rgba(255,255,255,0.08);
  border-radius:24px;
  box-shadow:0 24px 65px rgba(0,0,0,0.45);
  padding:30px 32px;
  min-width:0;
  overflow:hidden;
}
[data-flip]{cursor:pointer}
[data-flip]:focus-visible{outline:2px solid #91d4a8;outline-offset:4px}
.card-tint{
  position:absolute;
  inset:0;
  pointer-events:none;
  background:radial-gradient(circle at 50% 20%, rgba(var(--accent-rgb, 103, 191, 133), 0.16), transparent 75%);
  z-index:0;
}
.card-header{
  position:relative;
  z-index:1;
  display:flex;
  justify-content:space-between;
  align-items:center;
  margin-bottom:22px;
}
.word-heading{
  font:700 48px/1.1 var(--font-emphasis);
  margin:0;
  letter-spacing:-1.2px;
}
.badge{
  font-size:12.5px;
  font-weight:700;
  letter-spacing:.05em;
  text-transform:uppercase;
  padding:5px 13px;
  border-radius:20px;
  background:rgba(var(--accent-rgb, 103, 191, 133), 0.15);
  color:rgb(var(--accent-rgb, 103, 191, 133));
  border:1px solid rgba(var(--accent-rgb, 103, 191, 133), 0.35);
}
.parts-box{
  display:inline-flex;
  align-items:center;
  gap:10px;
  background:#131c24;
  border:1px solid #2d3f50;
  border-radius:12px;
  padding:10px 18px;
  font-size:22px;
  margin-bottom:22px;
}
.part-pill{
  font-weight:700;
  color:#91d4a8;
  font-family:var(--font-emphasis);
}
.part-plus{color:var(--text-muted);font-size:18px}
.overview{display:grid;gap:14px;margin-bottom:22px}
.use{
  width:100%;
  text-align:left;
  border:1px solid #35463d;
  border-radius:13px;
  padding:14px 18px;
  background:#1b302608;
  color:var(--text-primary);
  transition:all .15s ease;
}
.use[aria-pressed=true]{
  border-color:rgb(var(--accent-rgb, 103, 191, 133));
  background:rgba(var(--accent-rgb, 103, 191, 133), 0.12);
  box-shadow:0 0 0 1px rgba(var(--accent-rgb, 103, 191, 133), 0.5);
}
.use strong{display:block;font:700 24px var(--font-reading);letter-spacing:-.3px}
.use p{font-size:18px;line-height:1.4;color:var(--text-muted);margin:4px 0 0}
.example-section{
  background:#0d151c;
  border:1px solid #23313f;
  border-radius:14px;
  padding:20px 22px;
  text-align:center;
  margin-top:20px;
}
.stepper-header{
  display:flex;
  justify-content:space-between;
  align-items:center;
  margin-bottom:14px;
  padding-bottom:12px;
  border-bottom:1px solid #222f3d;
}
.stepper-label{
  font-size:13px;
  font-weight:600;
  letter-spacing:.06em;
  text-transform:uppercase;
  color:var(--text-muted);
}
.content-chips{
  display:flex;
  gap:6px;
  flex-wrap:wrap;
  justify-content:center;
}
.content-chip{
  border:1px solid #36485b;
  border-radius:14px;
  background:#16222d;
  color:var(--text-secondary);
  padding:4px 12px;
  font-size:15px;
  font-weight:600;
  transition:all .15s ease;
}
.content-chip[aria-pressed=true]{
  border-color:rgb(var(--accent-rgb, 103, 191, 133));
  background:rgba(var(--accent-rgb, 103, 191, 133), 0.2);
  color:rgb(var(--accent-rgb, 103, 191, 133));
}
.target-sentence{
  font-size:26px;
  line-height:1.35;
  margin:10px 0;
  color:#f4f5f6;
}
.target-sentence mark{
  background:none;
  color:#91d4a8;
  font-weight:700;
  text-decoration:underline;
  text-underline-offset:4px;
  text-decoration-thickness:2px;
}
.target-sentence .content-word{
  color:#c7e7d3;
  border-bottom:1px dashed #67bf85;
  padding-bottom:1px;
}
.translation-sentence{
  font-size:19px;
  color:var(--text-secondary);
  margin-top:10px;
}
.example-tip{
  font-size:13px;
  color:var(--text-muted);
  margin-top:12px;
}
.front{
  min-height:500px;
  display:flex;
  flex-direction:column;
  justify-content:space-between;
}
.front-center{
  margin:auto 0;
  text-align:center;
  position:relative;
  z-index:1;
}
.front-word{
  font:700 74px/1 var(--font-emphasis);
  letter-spacing:-2px;
  margin:0;
  color:#ffffff;
  text-shadow:0 4px 30px rgba(0,0,0,0.5);
}
.card-ranking{
  display:flex;
  justify-content:space-between;
  align-items:flex-end;
  border-top:1px solid rgba(255,255,255,0.08);
  padding-top:18px;
  position:relative;
  z-index:1;
}
.card-stat{
  display:flex;
  flex-direction:column;
}
.card-stat--end{
  align-items:flex-end;
  text-align:right;
}
.card-stat-label{
  font-size:13.5px;
  font-weight:600;
  letter-spacing:0.03em;
  color:var(--text-muted);
  margin-bottom:2px;
}
.card-stat-value{
  font:700 32px/1.1 var(--font-emphasis);
  color:#f4f5f6;
}
.card-stat-unit{
  font-size:12.5px;
  color:var(--text-muted);
  margin-top:2px;
}
.flip-hint{
  text-align:center;
  font-size:14px;
  color:var(--text-muted);
  margin-top:16px;
}
.sidebar-panel{
  background:var(--bg-tertiary);
  border:1px solid var(--border-light);
  border-radius:18px;
  padding:22px;
  font-size:16px;
}
.sidebar-panel h3{
  font:700 17px var(--font-emphasis);
  margin:0 0 10px;
  color:var(--text-primary);
}
.sidebar-panel p{
  font-size:15px;
  color:var(--text-muted);
  line-height:1.45;
  margin:0 0 16px;
}
.sidebar-examples{display:grid;gap:10px}
.sidebar-example-row{
  background:#0d151c;
  border:1px solid #23313f;
  border-radius:10px;
  padding:10px 14px;
  font-size:15px;
  cursor:pointer;
  transition:all .15s ease;
}
.sidebar-example-row[aria-current=true]{
  border-color:#67bf85;
  background:#13231b;
}
.sidebar-example-row .pt{color:#e4f5eb;font-weight:600;margin-bottom:3px}
.sidebar-example-row .en{color:var(--text-muted);font-size:13px}
@media(max-width:850px){
  .layout{display:block}
  .sidebar-panel{margin-top:24px}
  .surface{padding:22px 20px}
  .word-heading{font-size:42px}
  .front-word{font-size:56px}
  .target-sentence{font-size:22px}
}
</style>
</head>
<body>
<main class="shell">
  <header class="header">
    <h1 class="title">Portuguese Grammar Words · Deterministic Cycling</h1>
    <p class="subtitle">Grammar words act as fixed connectors while the content words shift. Tap the card background to flip.</p>
  </header>
  <nav class="words-nav" id="wordsNav" aria-label="Choose a word"></nav>
  <div class="layout">
    <div id="cardStage"></div>
    <aside class="sidebar-panel" id="sidebarPanel"></aside>
  </div>
</main>

<script>
const CARDS = __CARDS__;
const RANKS = __RANKS__;
const FREQUENCIES = __FREQUENCIES__;

let activeWord = 'de';
let isFront = false;
let activeUseIndex = 1; // default to 'connects a verb to its object' for de
let activeExampleIndex = 0;

try {
  const params = new URLSearchParams(window.location.search);
  if (params.get('word') && CARDS[params.get('word')]) {
    activeWord = params.get('word');
    activeUseIndex = (activeWord === 'de' ? 1 : 0);
  }
  if (params.get('front') === 'true') isFront = true;
  if (params.get('use') !== null) activeUseIndex = Number(params.get('use'));
  if (window.location.hash) {
    const hashWord = window.location.hash.replace('#', '');
    if (CARDS[hashWord]) {
      activeWord = hashWord;
      activeUseIndex = (activeWord === 'de' ? 1 : 0);
    }
  }
} catch(e) {}

const POS_ACCENTS = {
  "Preposition": "236, 72, 153",         // pink
  "Connector": "34, 197, 94",            // emerald green
  "Conjunction & Clitic": "34, 197, 94", // green
  "Article & Pronoun": "108, 92, 246",   // violet purple
  "Pronoun & Contraction": "251, 120, 50", // warm amber
  "Contraction": "251, 120, 50",         // warm amber
};

const esc = s => String(s).replaceAll('&','&amp;').replaceAll('<','&lt;').replaceAll('>','&gt;').replaceAll('"','&quot;');
function render(){
  const d = CARDS[activeWord];
  // All Function Words get a pure luminous white glow ("privileged" structural status)
  const FW_GLOW_RGB = "255, 255, 255";
  const accentRgb = FW_GLOW_RGB;
  const tintBg = `radial-gradient(circle at 50% 20%, rgba(${FW_GLOW_RGB}, 0.18), transparent 70%)`;

  const uses = d.uses;
  if(activeUseIndex >= uses.length) activeUseIndex = 0;
  const currentUse = uses[activeUseIndex];
  const examples = currentUse.examples;
  if(activeExampleIndex >= examples.length) activeExampleIndex = 0;
  const currentEx = examples[activeExampleIndex];

  // Nav buttons
  document.querySelectorAll('#wordsNav button').forEach(b => {
    b.setAttribute('aria-pressed', String(b.dataset.word === activeWord));
  });

  let cardHtml = '';
  if(isFront){
    cardHtml = `
      <section class="surface front" data-flip tabindex="0" aria-label="Card front. Tap to flip." style="--accent-rgb:${accentRgb}">
        <div class="card-tint" style="background:${tintBg}" aria-hidden="true"></div>
        <div class="card-header">
          <span class="badge">${esc(d.role)}</span>
        </div>
        <div class="front-center">
          <h2 class="front-word">${esc(activeWord)}</h2>
        </div>
        <div>
          <div class="card-ranking">
            <div class="card-stat">
              <span class="card-stat-label">Vocabulary Rank</span>
              <strong class="card-stat-value">#${RANKS[activeWord].toLocaleString()}</strong>
              <span class="card-stat-unit">of 10,000</span>
            </div>
            <div class="card-stat card-stat--end">
              <span class="card-stat-label">Frequency</span>
              <strong class="card-stat-value">${Math.round(FREQUENCIES[activeWord]).toLocaleString()}</strong>
              <span class="card-stat-unit">per million</span>
            </div>
          </div>
        </div>
      </section>
    `;
  } else {
    const highlight = esc(currentEx.highlight);
    const re = new RegExp('(?<![\\p{L}])' + highlight + '(?![\\p{L}])', 'gu');
    const highlightedTarget = esc(currentEx.target).replace(re, `<mark style="color:rgb(${accentRgb})">${highlight}</mark>`);

    cardHtml = `
      <section class="surface" data-flip tabindex="0" aria-label="Card back. Tap background to flip." style="--accent-rgb:${accentRgb}">
        <div class="card-tint" style="background:${tintBg}" aria-hidden="true"></div>
        <div class="card-header">
          <h2 class="word-heading">${esc(activeWord)}</h2>
          <span class="badge">${esc(d.role)}</span>
        </div>
        ${d.parts ? `
          <div class="parts-box" aria-label="Decomposition formula">
            <span class="part-pill">${esc(d.parts[0])}</span>
            <span class="part-plus">+</span>
            <span class="part-pill">${esc(d.parts[1])}</span>
          </div>
        ` : ''}
        <div class="overview" aria-label="Grammatical uses">
          ${uses.map((u, i) => `
            <button class="use" data-use="${i}" aria-pressed="${i === activeUseIndex}">
              <strong>${esc(u.english)}</strong>
              <p>${esc(u.description)}</p>
            </button>
          `).join('')}
        </div>
        <div class="example-section" aria-live="polite">
          ${currentUse.parts ? `
            <div style="margin-bottom:14px;text-align:center">
              <span class="badge" style="background:#131c24;border-color:#3c5369;font-size:15px;padding:6px 16px;text-transform:none">
                Contraction formula: <strong style="color:#91d4a8">${esc(currentUse.parts[0])}</strong> + <strong style="color:#91d4a8">${esc(currentUse.parts[1])}</strong>
              </span>
            </div>
          ` : ''}
          <div class="stepper-header">
            <span class="stepper-label">Content variation (${examples.length})</span>
            <div class="content-chips">
              ${examples.map((ex, i) => `
                <button class="content-chip" data-ex="${i}" aria-pressed="${i === activeExampleIndex}">
                  ${esc(ex.content)}
                </button>
              `).join('')}
            </div>
          </div>
          <div class="target-sentence">${highlightedTarget}</div>
          <div class="translation-sentence">${esc(currentEx.translation)}</div>
          <div class="example-tip">Tap a chip above to see how <strong>${esc(activeWord)}</strong> connects different content words</div>
        </div>
      </section>
    `;
  }
  document.getElementById('cardStage').innerHTML = cardHtml;

  // Sidebar panel
  document.getElementById('sidebarPanel').innerHTML = `
    <h3>${esc(activeWord)} · ${esc(currentUse.english)}</h3>
    <p>The connector <strong>${esc(activeWord)}</strong> stays fixed while the content word shifts:</p>
    <div class="sidebar-examples">
      ${examples.map((ex, i) => `
        <div class="sidebar-example-row" data-ex="${i}" aria-current="${i === activeExampleIndex}">
          <div class="pt">${esc(ex.target)}</div>
          <div class="en">${esc(ex.translation)}</div>
        </div>
      `).join('')}
    </div>
  `;
}

// Initialise nav
document.getElementById('wordsNav').innerHTML = Object.keys(CARDS).map(w => `
  <button data-word="${w}" aria-pressed="false">${w}</button>
`).join('');

// Interactions
document.addEventListener('click', e => {
  const w = e.target.closest('[data-word]');
  const u = e.target.closest('[data-use]');
  const x = e.target.closest('[data-ex]');
  const flip = e.target.closest('[data-flip]');

  if (w) {
    activeWord = w.dataset.word;
    isFront = false;
    activeUseIndex = (activeWord === 'de' ? 1 : 0);
    activeExampleIndex = 0;
    render();
  } else if (u) {
    activeUseIndex = Number(u.dataset.use);
    activeExampleIndex = 0;
    render();
  } else if (x) {
    activeExampleIndex = Number(x.dataset.ex);
    render();
  } else if (flip && !e.target.closest('button')) {
    isFront = !isFront;
    render();
  }
});

document.addEventListener('keydown', e => {
  if ((e.key === 'Enter' || e.key === ' ') && e.target.matches('[data-flip]')) {
    e.preventDefault();
    isFront = !isFront;
    render();
  }
});

render();
</script>
</body>
</html>
'''

def main():
    config = json.loads((ROOT / "app/config/config.json").read_text())
    frequency = json.loads((ROOT / "app" / config["languages"]["portuguese"]["frequencyPath"]).read_text())["values"]
    
    payload = HTML
    payload = payload.replace("__CARDS__", json.dumps(CARDS, ensure_ascii=False))
    payload = payload.replace("__RANKS__", json.dumps(RANKS, ensure_ascii=False))
    payload = payload.replace("__FREQUENCIES__", json.dumps({w: frequency[w] for w in CARDS}, ensure_ascii=False))

    OUT.mkdir(parents=True, exist_ok=True)
    DESIGN_DIR.mkdir(parents=True, exist_ok=True)

    (OUT / "index.html").write_text(payload)
    (DESIGN_DIR / "index.html").write_text(payload)
    print("Wrote to:", OUT / "index.html")
    print("Wrote to:", DESIGN_DIR / "index.html")

if __name__ == "__main__":
    main()
