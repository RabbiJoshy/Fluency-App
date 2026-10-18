"""Preview the real app renderer and CSS with isolated editorial proposal data."""
import json
import re
from check import ROOT
from pos_preview import payload, SCRIPT
from provenance_preview import script as provenance_script


def render(originals, proposals, ledger):
    data_sets = {'before': {l: {w: originals[l][w] for w in words} for l, words in proposals.items()},
                       'after': proposals}
    trial_path=ROOT/'docs/audits/function-word-labels/trial.json'
    if trial_path.exists(): data_sets['automatic']=json.loads(trial_path.read_text())
    syntax_path=ROOT/'docs/audits/function-word-labels/syntax-trial.json'
    if syntax_path.exists(): data_sets['syntax']=json.loads(syntax_path.read_text())
    syntax_option='<option value="syntax">Syntax trial</option>' if syntax_path.exists() else ''
    trial_option='<option value="automatic">Label trial</option>' if trial_path.exists() else ''
    data = json.dumps(data_sets, ensure_ascii=False).replace('<', '\\u003c')
    # Inline the actual renderer to support file:// without module/CORS restrictions.
    # No renderer logic or examples are maintained separately in the preview.
    renderer = (ROOT / 'app/js/function-word-card.js').read_text()
    renderer = re.sub(r'^export (?=(?:const|function)\b)', '', renderer, flags=re.M)
    renderer = renderer.replace('</script', '<\\/script')
    return '''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Fluency · Function-word cards</title>
<link rel="stylesheet" href="../../../app/css/style.css?v=20261016fw">
<style>
/* Preview-only shell and optional chunk colour experiment. */
.preview-card .fw-credit-start{overflow:visible;white-space:normal;min-width:0;max-width:75%;display:flex;align-items:center}
.preview-card .fw-credit-start .example-source-chip{max-width:100%}
.preview-card .fw-example-credit-row{min-height:42px}
.preview-license{margin-top:10px;font-size:10px;line-height:1.5;color:var(--text-muted)}
.preview-license a{color:inherit;text-decoration:underline}

body{height:auto;min-height:100vh;overflow:auto;padding:20px 14px;user-select:text}
.preview-shell{max-width:460px;margin:0 auto;font-family:var(--font-reading,system-ui)}
.preview-toolbar{display:flex;flex-wrap:wrap;gap:8px;margin-bottom:14px;align-items:center}
.preview-toolbar label{display:flex;gap:6px;align-items:center;font-size:12px;color:var(--text-muted)}
.preview-toolbar select{font:inherit;color:var(--text-primary);background:var(--bg-tertiary);border:1px solid var(--border-color);border-radius:8px;padding:8px;min-height:36px}
.preview-shell .preview-card.card-face.card-back{position:relative;transform:none;opacity:1;visibility:visible;pointer-events:auto;backface-visibility:visible;height:auto;min-height:560px;width:100%;overflow:visible}
.preview-card #backContent{width:100%;flex:1}
.preview-card .fw-deterministic-card{min-height:500px}
.preview-footer{display:flex;align-items:center;justify-content:space-between;gap:12px;margin-top:14px;font-size:12px;color:var(--text-muted)}
.preview-footer button{font:inherit;border:1px solid var(--border-color);background:var(--bg-tertiary);color:var(--text-primary);border-radius:8px;padding:9px 12px;cursor:pointer}
.preview-note{font-size:11px;color:var(--text-muted);line-height:1.5;margin:12px 0}
.preview-shell :focus-visible{outline:2px solid #a8baff;outline-offset:3px}
@media(max-width:380px){body{padding:12px 8px}.preview-shell .preview-card.card-face.card-back{padding:22px 16px!important}.preview-card .fw-deterministic-card{min-height:460px}}
.preview-pos .fw-token-v,.preview-pos .fw-token-c{color:#e0e4ea}
.preview-pos .fw-sentence-target{font-weight:400}
.preview-pos .fw-token-connector{color:#fff;font-weight:700;text-decoration-thickness:1px;text-underline-offset:4px}
.preview-pos .fw-sentence-target .fw-token-connector{font-weight:700;text-decoration-thickness:1px}
.preview-pos .fw-relation-box.is-selected{border-color:rgba(212,218,245,.4);background:rgba(212,218,245,.06);box-shadow:none}
/* Keep the construction beside its heading and examples beside their patterns. */
.preview-card .fw-parts-box{background:none;border:0;border-radius:0;padding:0;margin:2px 0 10px;gap:7px;font:500 22px/1.2 var(--font-emphasis,"Space Grotesk");}
.preview-card .fw-part-pill{font:inherit;color:var(--text-secondary);}
.preview-card .fw-part-plus{font:inherit;color:var(--text-muted);}
.preview-card .fw-sentence-panel{margin-top:4px;}
.preview-card .fw-relations-list{margin-bottom:14px;}
.preview-shell .preview-card.card-face.card-back{min-height:560px;}
.preview-card .fw-deterministic-card{min-height:500px;height:auto;}
@media(max-width:380px){.preview-card .fw-deterministic-card{min-height:460px;}}
.preview-flat .fw-relation-box{border-color:transparent;border-radius:8px;background:transparent;padding:9px 14px;}
.preview-flat .fw-relations-list{gap:4px;}
.preview-flat .fw-relation-box:hover{background:rgba(255,255,255,.035);border-color:transparent;}
.preview-flat .fw-relation-box.is-selected,.preview-flat .fw-relation-box[aria-pressed="true"]{background:rgba(212,218,245,.07);border-color:rgba(212,218,245,.18);box-shadow:none;}
.preview-flat .fw-relation-rule{color:var(--text-secondary);font-size:max(15px,calc(var(--card-fs,18px)*.83));line-height:1.45;}
/* Match the normal example's translation divider and reading colour. */
.preview-card .fw-sentence-translation{margin-top:8px;padding-top:8px;border-top:1px solid rgba(255,255,255,.13);color:#e6eaf0;font-size:16px;font-weight:500;font-style:normal;line-height:1.4;}
.preview-card .fw-example-credit-row{border-top:0;padding-top:0;}
.preview-card .fw-relation-formula{font-size:17px;line-height:1.3;}
.preview-card .fw-relation-rule{font-size:15px;line-height:1.45;}
@media(max-width:389px){.preview-card .fw-sentence-translation{font-size:15px;}}
</style></head><body><main class="preview-shell">
<nav class="preview-toolbar" aria-label="Preview controls">
<label for="language">Language <select id="language"><option value="pt">Portuguese</option><option value="es">Spanish</option></select></label>
<label for="word">Word <select id="word"></select></label>
<label for="version">Copy <select id="version"><option value="after">Revised</option><option value="before">Current</option>''' + trial_option + syntax_option + '''</select></label>
<label for="colours">Colours <select id="colours"><option value="pos">Clear chunks</option><option value="pattern">Original</option></select></label>
<label for="rows">Rows <select id="rows"><option value="flat">Flatter</option><option value="boxed">Current</option></select></label>
</nav>
<section class="preview-card card-face card-back" aria-label="Learner card"><div id="backContent"></div></section>
<div class="preview-footer"><span>Tap a pattern to explore it.</span><button id="next" type="button">Next example →</button></div>
<p id="review-status" class="preview-note" role="status"></p>
<p class="preview-note">Preview only · matching colours connect each formula slot to its sentence chunk. White underlining marks the word you’re learning.</p>
<p class="preview-license">Reviewed pilot sources: <a href="https://tatoeba.org/" target="_blank" rel="noopener noreferrer">Tatoeba</a> · <a href="https://creativecommons.org/licenses/by/2.0/fr/" target="_blank" rel="noopener noreferrer">CC BY 2.0 FR</a> and <a href="http://www.opensubtitles.org/" target="_blank" rel="noopener noreferrer">OpenSubtitles.org</a> via OPUS. Pilot attribution is retained in the source review. Other cards retain unverified examples.</p>
</main><script>''' + renderer + '\nconst PREVIEW_DATA = ' + data + ';\nconst POS_PREVIEW = ' + json.dumps(payload(), ensure_ascii=False) + ';\n' + SCRIPT + '\n' + provenance_script() + ''';
const previewElement=id=>document.getElementById(id);
function previewWords(){const select=previewElement('word');select.replaceChildren(...Object.keys(PREVIEW_DATA.after[previewElement('language').value]).map(w=>{const o=document.createElement('option');o.value=w;o.textContent=w;return o}));previewDraw();}
function previewDraw(){document.querySelector('.preview-card').classList.toggle('preview-flat',previewElement('rows').value==='flat');const lang=previewElement('language').value,word=previewElement('word').value,version=previewElement('version').value;
const suite=lang==='pt'?PORTUGUESE_GRAMMAR_WORDS:SPANISH_GRAMMAR_WORDS;
const entry=structuredClone(PREVIEW_DATA[version][lang][word]);
previewElement('review-status').textContent=version==='syntax'?'Syntax trial · 6 reviewed additions with automatically generated highlights.':version==='automatic'?'Automatic-label trial · 13 reviewed additions; existing examples retained.':version==='before'?'Original suite copy · source labels not verified.':entry.previewReviewStatus==='source-reviewed'?'Reviewed source examples · simplified copy.':'Simplified copy · existing examples await source review.';
entry.uses=entry.relations;suite[word]=entry;
_activeWordKey=null;_activeRelIndex=0;_activeExampleIndex=0;
previewElement('backContent').innerHTML=functionWordBlockHTML({word},lang);
const panel=document.querySelector('.fw-sentence-panel');panel.tabIndex=0;panel.setAttribute('role','button');panel.setAttribute('aria-label','Next example');paintPreviewPOS();paintPreviewProvenance();panel.onkeydown=e=>{if(e.target===panel&&(e.key==='Enter'||e.key===' ')){e.preventDefault();cycleFunctionWordExample();}};
}
previewElement('language').onchange=previewWords;previewElement('word').onchange=previewDraw;previewElement('version').onchange=previewDraw;
previewElement('rows').onchange=()=>document.querySelector('.preview-card').classList.toggle('preview-flat',previewElement('rows').value==='flat');
previewElement('next').onclick=()=>cycleFunctionWordExample();previewElement('colours').onchange=paintPreviewPOS;previewWords();
</script></body></html>'''
