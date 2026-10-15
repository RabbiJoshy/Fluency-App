#!/usr/bin/env python3
"""Update card_preview.html with full Portuguese and Spanish datasets, allowed_lemmas, pips, and cycling."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PT_FILE = ROOT / "app/data/grammar-words/pt.json"
ES_FILE = ROOT / "app/data/grammar-words/es.json"
PREVIEW_FILE = Path("/Users/joshuathomasamar/.gemini/antigravity/brain/b64d8841-ae6f-4b11-b4fb-0d8ca433eebf/card_preview.html")

with open(PT_FILE) as f:
    pt_data = json.load(f)

with open(ES_FILE) as f:
    es_data = json.load(f)

html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Function Words Suite · Fluency</title>
<script src="https://www.gstatic.com/antigravity/web/dev/tailwindcss.min.js"></script>
<style>
  :root {{
    --bg-primary: #0c1116;
    --bg-card: #151f28;
    --bg-tertiary: #18232d;
    --border-color: #2b3947;
    --border-subtle: #23313f;
    --text-primary: #f4f5f6;
    --text-secondary: #c2cbd4;
    --text-muted: #8d9aa7;
    --fw-glow-rgb: 212, 218, 245; /* Periwinkle Moonstone Off-White */

    /* Clean semantic constituent colors */
    --color-verb: #38bdf8;       /* Sky blue for Governing Verb */
    --color-noun: #c084fc;       /* Soft purple for Noun / Complement */
    --color-connector: #ffffff;  /* Luminous white for Function Word */
  }}
  body {{
    background-color: var(--bg-primary);
    color: var(--text-primary);
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
    margin: 0;
    padding: 24px 16px;
    display: flex;
    flex-direction: column;
    align-items: center;
  }}
  .top-controls {{
    display: flex;
    gap: 12px;
    margin-bottom: 16px;
    flex-wrap: wrap;
    justify-content: center;
    align-items: center;
  }}
  .controls-bar {{
    display: flex;
    gap: 8px;
    margin-bottom: 20px;
    flex-wrap: wrap;
    justify-content: center;
    max-width: 900px;
  }}
  .pill-btn {{
    border: 1px solid var(--border-subtle);
    border-radius: 999px;
    background: var(--bg-tertiary);
    color: var(--text-secondary);
    padding: 5px 13px;
    font-size: 13.5px;
    font-weight: 600;
    cursor: pointer;
    transition: all 0.15s ease;
  }}
  .pill-btn:hover {{
    border-color: rgba(var(--fw-glow-rgb), 0.4);
    color: #fff;
  }}
  .pill-btn.active {{
    border-color: rgba(var(--fw-glow-rgb), 0.85);
    background: rgba(var(--fw-glow-rgb), 0.18);
    color: #fff;
  }}
  .toggle-group {{
    display: inline-flex;
    background: #101820;
    padding: 3px;
    border-radius: 999px;
    border: 1px solid var(--border-subtle);
  }}
  .toggle-btn {{
    border: none;
    background: transparent;
    color: var(--text-muted);
    padding: 5px 14px;
    border-radius: 999px;
    font-size: 13.5px;
    font-weight: 600;
    cursor: pointer;
    transition: all 0.15s ease;
  }}
  .toggle-btn.active {{
    background: rgba(var(--fw-glow-rgb), 0.16);
    color: #fff;
  }}

  /* Card Viewport */
  .card-viewport {{
    transition: width 0.25s ease;
    width: 100%;
    max-width: 420px; /* Mobile */
  }}
  .card-viewport.desktop {{
    max-width: 520px; /* Desktop */
  }}
  .card-shell {{
    position: relative;
    background: var(--bg-card);
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 24px;
    box-shadow: 0 20px 50px rgba(0, 0, 0, 0.5);
    padding: 26px 22px;
    min-height: 520px;
    display: flex;
    flex-direction: column;
    overflow: hidden;
    cursor: pointer;
  }}
  .card-tint {{
    position: absolute;
    inset: 0;
    pointer-events: none;
    background: transparent;
    z-index: 0;
  }}
  .card-shell.front-active .card-tint {{
    background: radial-gradient(circle at 50% 20%, rgba(var(--fw-glow-rgb), 0.18), transparent 70%);
  }}

  /* Front View */
  .front-view {{
    position: relative;
    z-index: 1;
    display: flex;
    flex-direction: column;
    justify-content: space-between;
    height: 100%;
    flex: 1;
    min-height: 460px;
  }}
  .front-center {{
    margin: auto 0;
    text-align: center;
  }}
  .front-word {{
    font-size: 72px;
    font-weight: 700;
    letter-spacing: -2px;
    color: #ffffff;
    line-height: 1;
    margin: 0;
    text-shadow: 0 4px 30px rgba(0, 0, 0, 0.5);
  }}
  .front-stats {{
    display: flex;
    justify-content: space-between;
    align-items: flex-end;
    border-top: 1px solid rgba(255, 255, 255, 0.08);
    padding-top: 18px;
  }}
  .stat-block {{
    display: flex;
    flex-direction: column;
  }}
  .stat-block.end {{
    align-items: flex-end;
    text-align: right;
  }}
  .stat-label {{
    font-size: 13px;
    font-weight: 600;
    letter-spacing: 0.03em;
    color: var(--text-muted);
    margin-bottom: 2px;
  }}
  .stat-val {{
    font-size: 28px;
    font-weight: 700;
    color: #f4f5f6;
    line-height: 1.1;
  }}
  .stat-unit {{
    font-size: 12px;
    color: var(--text-muted);
    margin-top: 2px;
  }}

  /* Back View */
  .back-view {{
    position: relative;
    z-index: 1;
    display: flex;
    flex-direction: column;
    height: 100%;
    flex: 1;
  }}
  .back-header {{
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    margin-bottom: 12px;
  }}
  .back-word {{
    font-size: 44px;
    font-weight: 700;
    letter-spacing: -1.2px;
    margin: 0 0 4px 0;
    line-height: 1.1;
    color: #ffffff;
    text-align: center;
  }}
  .section-micro-header {{
    font-size: 11px;
    font-weight: 700;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    color: #64748b;
    margin: 0;
    text-align: center;
  }}

  /* Contraction badge (e.g. naquele = em + aquele) */
  .parts-box {{
    display: inline-flex;
    align-items: center;
    align-self: center;
    gap: 8px;
    background: #111a22;
    border: 1px solid var(--border-color);
    border-radius: 10px;
    padding: 4px 12px;
    font-size: 13.5px;
    margin: 0 auto 10px auto;
    width: fit-content;
  }}
  .parts-pill {{
    font-weight: 700;
    color: #fff;
  }}
  .parts-plus {{
    color: var(--text-muted);
  }}

  /* Relationship duty boxes — open by default */
  .relations-list {{
    display: flex;
    flex-direction: column;
    gap: 7px;
    margin-bottom: 12px;
  }}
  .relation-box {{
    width: 100%;
    text-align: left;
    border: 1px solid var(--border-color);
    border-radius: 12px;
    padding: 10px 14px;
    background: rgba(255, 255, 255, 0.02);
    color: var(--text-primary);
    cursor: pointer;
    transition: all 0.15s ease;
  }}
  .relation-box:hover {{
    border-color: rgba(var(--fw-glow-rgb), 0.4);
    background: rgba(255, 255, 255, 0.04);
  }}
  .relation-box.selected {{
    border-color: rgba(var(--fw-glow-rgb), 0.85);
    background: rgba(var(--fw-glow-rgb), 0.10);
    box-shadow: 0 0 0 1px rgba(var(--fw-glow-rgb), 0.3);
  }}
  .relation-formula {{
    font-size: 15.5px;
    font-weight: 700;
    color: #fff;
    letter-spacing: -0.2px;
    margin-bottom: 4px;
    line-height: 1.25;
  }}
  .relation-formula .token-v, .relation-formula .fw-token-v {{ color: var(--color-verb); }}
  .relation-formula .token-c, .relation-formula .fw-token-c {{ color: var(--color-noun); }}
  .relation-formula .token-fw, .relation-formula .fw-token-connector {{ color: var(--color-connector); text-decoration: underline; text-underline-offset: 4px; text-decoration-thickness: 2px; }}

  .relation-rule {{
    font-size: 13.8px;
    line-height: 1.4;
    color: #cbd5e1;
    margin: 0;
    display: block;
  }}

  /* Clean Example Panel with Cycling & Pips */
  .sentence-panel {{
    margin-top: auto;
    background: #0d151c;
    border: 1px solid var(--border-subtle);
    border-radius: 15px;
    padding: 16px 18px;
    text-align: center;
    cursor: pointer;
    user-select: none;
    transition: background 0.15s ease;
  }}
  .sentence-panel:hover {{
    background: #111a24;
  }}
  .sentence-target {{
    font-size: 23px;
    font-weight: 700;
    line-height: 1.35;
    color: #f4f5f6;
    margin: 0 0 5px;
  }}
  .sentence-target .token-v, .sentence-target .fw-token-v {{ color: var(--color-verb); }}
  .sentence-target .token-fw, .sentence-target .fw-token-connector {{
    color: var(--color-connector);
    text-decoration: underline;
    text-underline-offset: 5px;
    text-decoration-thickness: 2.5px;
  }}
  .sentence-target .token-c, .sentence-target .fw-token-c {{ color: var(--color-noun); }}
  .sentence-translation {{
    font-size: 14.5px;
    color: var(--text-muted);
    margin: 0;
  }}

  /* Credit & Pips Row */
  .fw-example-credit-row {{
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-top: 10px;
    padding-top: 8px;
    border-top: 1px solid rgba(255, 255, 255, 0.07);
    min-height: 18px;
  }}
  .fw-credit-start {{
    font-size: 11.5px;
    color: var(--text-muted);
    font-weight: 500;
    text-overflow: ellipsis;
    overflow: hidden;
    white-space: nowrap;
  }}
  .fw-sentence-ticks-container {{
    display: flex;
    align-items: center;
    margin-left: auto;
  }}
  .example-ticks {{
    display: flex;
    align-items: center;
    gap: 5px;
  }}
  .example-tick {{
    width: 7.5px;
    height: 7.5px;
    border-radius: 999px;
    background: rgba(255, 255, 255, 0.22);
    transition: background 0.2s ease, transform 0.2s ease;
  }}
  .example-tick.is-current {{
    background: #ffffff;
    transform: scale(1.15);
  }}

  .tap-flip-hint {{
    text-align: center;
    font-size: 12px;
    color: var(--text-muted);
    margin-top: 12px;
  }}
</style>
</head>
<body>

  <!-- Language & Side Controls -->
  <div class="top-controls">
    <div class="toggle-group">
      <button id="btnPT" class="toggle-btn active" onclick="setLang('pt')">Portuguese (44)</button>
      <button id="btnES" class="toggle-btn" onclick="setLang('es')">Spanish (37)</button>
    </div>
    <div class="toggle-group">
      <button id="btnFront" class="toggle-btn" onclick="setSide('front')">Front</button>
      <button id="btnBack" class="toggle-btn active" onclick="setSide('back')">Back</button>
    </div>
    <div class="toggle-group">
      <button id="btnMobile" class="toggle-btn active" onclick="setViewport('mobile')">Mobile (390px)</button>
      <button id="btnDesktop" class="toggle-btn" onclick="setViewport('desktop')">Desktop (520px)</button>
    </div>
  </div>

  <!-- Word Selector Bar -->
  <div class="controls-bar" id="wordNav"></div>

  <!-- Card Frame -->
  <div class="card-viewport" id="viewport">
    <div class="card-shell" onclick="handleCardClick(event)">
      <div class="card-tint"></div>
      <div id="cardContent"></div>
    </div>
    <div class="tap-flip-hint">Click card background to flip · Click sentence panel to cycle examples</div>
  </div>

<script>
const SUITES = {{
  pt: {json.dumps(pt_data, ensure_ascii=False)},
  es: {json.dumps(es_data, ensure_ascii=False)}
}};

let currentLang = "pt";
let activeWord = "que";
let currentSide = "back";
let activeRelIdx = 0;
let activeExIdx = 0;

function setLang(lang) {{
  currentLang = lang;
  document.getElementById("btnPT").classList.toggle("active", lang === "pt");
  document.getElementById("btnES").classList.toggle("active", lang === "es");
  const words = Object.keys(SUITES[lang]);
  activeWord = words[0];
  activeRelIdx = 0;
  activeExIdx = 0;
  renderNav();
  renderCard();
}}

function setSide(side) {{
  currentSide = side;
  document.getElementById("btnFront").classList.toggle("active", side === "front");
  document.getElementById("btnBack").classList.toggle("active", side === "back");
  const shell = document.querySelector(".card-shell");
  shell.classList.toggle("front-active", side === "front");
  renderCard();
}}

function setViewport(mode) {{
  const vp = document.getElementById("viewport");
  document.getElementById("btnMobile").classList.toggle("active", mode === "mobile");
  document.getElementById("btnDesktop").classList.toggle("active", mode === "desktop");
  vp.classList.toggle("desktop", mode === "desktop");
}}

function selectWord(w) {{
  activeWord = w;
  activeRelIdx = 0;
  activeExIdx = 0;
  renderNav();
  renderCard();
}}

function selectRelation(event, idx) {{
  event.stopPropagation();
  activeRelIdx = idx;
  activeExIdx = 0;
  renderCard();
}}

function cycleExample(event) {{
  event.stopPropagation();
  const item = SUITES[currentLang][activeWord];
  if (!item) return;
  const relations = item.relations || item.uses || [];
  const currentRel = relations[activeRelIdx] || relations[0];
  const examples = currentRel?.examples || (currentRel?.targetHTML ? [currentRel] : []);
  if (examples.length <= 1) return;
  activeExIdx = (activeExIdx + 1) % examples.length;
  renderCard();
}}

function handleCardClick(event) {{
  if (event.target.closest("button") || event.target.closest(".sentence-panel")) return;
  setSide(currentSide === "front" ? "back" : "front");
}}

function renderNav() {{
  const container = document.getElementById("wordNav");
  const words = Object.keys(SUITES[currentLang]);
  container.innerHTML = words.map(w => `
    <button class="pill-btn ${{w === activeWord ? 'active' : ''}}" onclick="selectWord('${{w}}')">${{w}}</button>
  `).join("");
}}

function renderTicks(total, current) {{
  if (total < 2) return "";
  const ticks = Array.from({{ length: total }}, (_, i) =>
    `<span class="example-tick${{i === current ? ' is-current' : ''}}"></span>`
  ).join("");
  return `<div class="example-ticks" role="img" aria-label="Example ${{current + 1}} of ${{total}}">${{ticks}}</div>`;
}}

function renderCard() {{
  const item = SUITES[currentLang][activeWord];
  const container = document.getElementById("cardContent");
  if (!item) return;

  if (currentSide === "front") {{
    container.innerHTML = `
      <div class="front-view">
        <div></div>
        <div class="front-center">
          <h1 class="front-word">${{activeWord}}</h1>
        </div>
        <div class="front-stats">
          <div class="stat-block">
            <span class="stat-label">Vocabulary Rank</span>
            <span class="stat-val">#${{item.rank.toLocaleString()}}</span>
            <span class="stat-unit">of 10,000</span>
          </div>
          <div class="stat-block end">
            <span class="stat-label">Frequency</span>
            <span class="stat-val">${{Math.round(item.frequency).toLocaleString()}}</span>
            <span class="stat-unit">per million</span>
          </div>
        </div>
      </div>
    `;
    return;
  }}

  // Back View
  const relations = item.relations || item.uses || [];
  if (activeRelIdx >= relations.length) activeRelIdx = 0;
  const currentRel = relations[activeRelIdx];

  // Contraction formula badge (if applicable)
  let partsHTML = "";
  if (item.parts) {{
    partsHTML = `
      <div class="parts-box">
        <span class="parts-pill">${{item.parts[0]}}</span>
        <span class="parts-plus">+</span>
        <span class="parts-pill">${{item.parts[1]}}</span>
      </div>`;
  }} else if (currentRel?.parts) {{
    partsHTML = `
      <div class="parts-box">
        <span class="parts-pill">${{currentRel.parts[0]}}</span>
        <span class="parts-plus">+</span>
        <span class="parts-pill">${{currentRel.parts[1]}}</span>
      </div>`;
  }}

  // Relations list (syntactic formulas)
  const relationsHTML = relations.map((rel, i) => `
    <button class="relation-box ${{i === activeRelIdx ? 'selected' : ''}}" onclick="selectRelation(event, ${{i}})">
      <div class="relation-formula">${{rel.formulaHTML || rel.formula}}</div>
      <p class="relation-rule">${{rel.rule || rel.description}}</p>
    </button>
  `).join("");

  const examples = currentRel?.examples || (currentRel?.targetHTML ? [currentRel] : []);
  if (activeExIdx >= examples.length) activeExIdx = 0;
  const currentEx = examples[activeExIdx] || currentRel;
  const targetHTML = currentEx?.targetHTML || currentRel?.targetHTML || "";
  const transHTML = currentEx?.translation || currentRel?.translation || "";
  const sourceText = currentEx?.source || "";
  const ticksHTML = renderTicks(examples.length, activeExIdx);

  container.innerHTML = `
    <div class="back-view">
      <div class="back-header">
        <h2 class="back-word">${{activeWord}}</h2>
        <div class="section-micro-header">Function Word · Example Patterns</div>
      </div>
      ${{partsHTML}}
      <div class="relations-list">
        ${{relationsHTML}}
      </div>
      <div class="sentence-panel" onclick="cycleExample(event)">
        <div class="sentence-target">${{targetHTML}}</div>
        <div class="sentence-translation">${{transHTML}}</div>
        <div class="fw-example-credit-row">
          <span class="fw-credit-start">${{sourceText}}</span>
          <div class="fw-sentence-ticks-container">${{ticksHTML}}</div>
        </div>
      </div>
    </div>
  `;
}}

renderNav();
renderCard();
</script>
</body>
</html>
"""

with open(PREVIEW_FILE, "w") as f:
    f.write(html_content)

print(f"Updated {PREVIEW_FILE} with PT ({len(pt_data)}) and ES ({len(es_data)}) suites, pips, and cycling.")
