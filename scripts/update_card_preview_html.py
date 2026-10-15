#!/usr/bin/env python3
"""Update card_preview.html with full Portuguese and Spanish datasets and language toggle."""
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
    padding: 28px 24px;
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
    margin-bottom: 14px;
  }}
  .back-word {{
    font-size: 38px;
    font-weight: 700;
    letter-spacing: -1.2px;
    margin: 0 0 5px 0;
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
    padding: 5px 12px;
    font-size: 14px;
    margin: 0 auto 12px auto;
    width: fit-content;
  }}
  .parts-pill {{
    font-weight: 700;
    color: #fff;
  }}
  .parts-plus {{
    color: var(--text-muted);
  }}

  /* Relationship duty boxes */
  .relations-list {{
    display: flex;
    flex-direction: column;
    gap: 8px;
    margin-bottom: 18px;
  }}
  .relation-box {{
    width: 100%;
    text-align: left;
    border: 1px solid var(--border-color);
    border-radius: 12px;
    padding: 10px 16px;
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
    padding: 13px 16px;
  }}
  .relation-formula {{
    font-size: 16px;
    font-weight: 700;
    color: #fff;
    letter-spacing: -0.2px;
    margin-bottom: 0;
    line-height: 1.25;
  }}
  .relation-box.selected .relation-formula {{
    margin-bottom: 6px;
  }}
  .relation-formula .token-v, .relation-formula .fw-token-v {{ color: var(--color-verb); }}
  .relation-formula .token-c, .relation-formula .fw-token-c {{ color: var(--color-noun); }}
  .relation-formula .token-fw, .relation-formula .fw-token-connector {{ color: var(--color-connector); text-decoration: underline; text-underline-offset: 4px; text-decoration-thickness: 2px; }}

  .relation-rule {{
    font-size: 13.5px;
    line-height: 1.45;
    color: #cbd5e1;
    margin: 0;
    display: none;
  }}
  .relation-box.selected .relation-rule {{
    display: block;
  }}

  /* Clean Example Panel */
  .sentence-panel {{
    margin-top: auto;
    background: #0d151c;
    border: 1px solid var(--border-subtle);
    border-radius: 16px;
    padding: 20px 18px;
    text-align: center;
  }}
  .sentence-target {{
    font-size: 24px;
    font-weight: 700;
    line-height: 1.35;
    color: #f4f5f6;
    margin: 0 0 6px;
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
    font-size: 15px;
    color: var(--text-muted);
    margin: 0;
  }}
  .tap-flip-hint {{
    text-align: center;
    font-size: 12px;
    color: var(--text-muted);
    opacity: 0.6;
    margin-top: 12px;
  }}
</style>
</head>
<body>

  <!-- Controls -->
  <div class="top-controls">
    <div class="toggle-group">
      <button class="toggle-btn active" id="btnPT" onclick="setLang('pt')">Portuguese ({len(pt_data)})</button>
      <button class="toggle-btn" id="btnES" onclick="setLang('es')">Spanish ({len(es_data)})</button>
    </div>
    <div class="toggle-group">
      <button class="toggle-btn" id="btnFront" onclick="setSide('front')">Front</button>
      <button class="toggle-btn active" id="btnBack" onclick="setSide('back')">Back</button>
    </div>
    <div class="toggle-group">
      <button class="toggle-btn active" id="btnMobile" onclick="setViewport('mobile')">Mobile (390px)</button>
      <button class="toggle-btn" id="btnDesktop" onclick="setViewport('desktop')">Desktop (520px)</button>
    </div>
  </div>

  <!-- Words Nav -->
  <div class="controls-bar" id="wordNav"></div>

  <!-- Real Card Viewport -->
  <div class="card-viewport" id="viewport">
    <div class="card-shell" onclick="handleCardClick(event)">
      <div class="card-tint"></div>
      <div id="cardContent"></div>
    </div>
    <div class="tap-flip-hint">Click card background to flip</div>
  </div>

<script>
const SUITES = {{
  pt: {json.dumps(pt_data, ensure_ascii=False)},
  es: {json.dumps(es_data, ensure_ascii=False)}
}};

let currentLang = "pt";
let activeWord = "de";
let currentSide = "back";
let activeRelIdx = 0;

function setLang(lang) {{
  currentLang = lang;
  document.getElementById("btnPT").classList.toggle("active", lang === "pt");
  document.getElementById("btnES").classList.toggle("active", lang === "es");
  const words = Object.keys(SUITES[lang]);
  activeWord = words[0];
  activeRelIdx = 0;
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
  renderNav();
  renderCard();
}}

function selectRelation(event, idx) {{
  event.stopPropagation();
  activeRelIdx = idx;
  renderCard();
}}

function handleCardClick(event) {{
  if (event.target.closest("button")) return;
  setSide(currentSide === "front" ? "back" : "front");
}}

function renderNav() {{
  const container = document.getElementById("wordNav");
  const words = Object.keys(SUITES[currentLang]);
  container.innerHTML = words.map(w => `
    <button class="pill-btn ${{w === activeWord ? 'active' : ''}}" onclick="selectWord('${{w}}')">${{w}}</button>
  `).join("");
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
      <div class="sentence-panel">
        <div class="sentence-target">${{currentRel?.targetHTML || currentRel?.target || ''}}</div>
        <div class="sentence-translation">${{currentRel?.translation || ''}}</div>
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

print(f"Updated {PREVIEW_FILE} with PT ({len(pt_data)}) and ES ({len(es_data)}) suites.")
