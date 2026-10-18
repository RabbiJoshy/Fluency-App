#!/usr/bin/env python3
"""Sync JSON suites into app/js/function-word-card.js so the app works seamlessly offline."""
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PT_FILE = ROOT / "app/data/grammar-words/pt.json"
ES_FILE = ROOT / "app/data/grammar-words/es.json"
JS_FILE = ROOT / "app/js/function-word-card.js"

with open(PT_FILE) as f:
    pt_data = json.load(f)

with open(ES_FILE) as f:
    es_data = json.load(f)

# Ensure .uses alias
for d in (pt_data, es_data):
    for entry in d.values():
        entry["uses"] = entry.get("relations", [])

pt_json_str = json.dumps(pt_data, ensure_ascii=False, indent=4)
es_json_str = json.dumps(es_data, ensure_ascii=False, indent=4)

trial_json_str = (ROOT / "app/data/grammar-words/syntax-trial.json").read_text().strip()

js_code = f"""// Function-word presentation & ambient lighting for Fluency.
//
// Function words -- articles, prepositions, particles, clitics, contractions -- are
// taught by their structural role and deterministic content-word variation,
// rather than dictionary sense assignments.
//
// Supported deterministic closed-class focus suites: Portuguese (pt), Spanish (es).

export const FW_SIGNATURE_GLOW_RGB = '212, 218, 245'; // Periwinkle Moonstone Off-White

// Curated deterministic relational definitions for Portuguese closed-class focus words.
export const PORTUGUESE_GRAMMAR_WORDS = {pt_json_str};

// Curated deterministic relational definitions for Spanish closed-class focus words.
export const SPANISH_GRAMMAR_WORDS = {es_json_str};

export const GRAMMAR_WORDS = {{
    pt: PORTUGUESE_GRAMMAR_WORDS,
    portuguese: PORTUGUESE_GRAMMAR_WORDS,
    portuguese_brazilian: PORTUGUESE_GRAMMAR_WORDS,
    es: SPANISH_GRAMMAR_WORDS,
    spanish: SPANISH_GRAMMAR_WORDS,
}};

// Explicitly reviewed additions only; never enabled in production.
const FW_SYNTAX_TRIAL = {trial_json_str};
function syntaxTrialEnabled() {{
    return typeof window !== 'undefined' && window.__FLUENCY_ENV__ === 'staging'
        && new URLSearchParams(window.location?.search || '').get('fwSyntaxTrial') === '1';
}}

// Backward-compatibility: ensure .uses aliases
for (const dict of [PORTUGUESE_GRAMMAR_WORDS, SPANISH_GRAMMAR_WORDS]) {{
    for (const entry of Object.values(dict)) {{
        if (!entry.uses) entry.uses = entry.relations;
    }}
}}

const ROLE_NAMES = {{
    prep: 'preposition',
    article: 'article',
    subject_pron: 'subject',
    direct_obj: 'direct object',
    indirect_obj: 'indirect object',
    reflexive: 'reflexive',
    rel_pron: 'relative',
    coord_conj: 'coordination',
    subord_conj: 'subordination',
    adverbial: 'adverbial',
    adv_connector: 'connector',
    possessive: 'possessive',
    demonstrative: 'demonstrative',
    indefinite: 'indefinite',
    quantifier: 'quantifier',
    negation: 'negation',
    focus_particle: 'focus particle',
    interrogative: 'question',
    comparative: 'comparison',
    contraction: 'contraction',
    clitic: 'clitic'
}};


// Reuse the app palette and provenance component without a circular import.
let fwPresentation = {{}};
export function configureFunctionWordPresentation(options) {{
    fwPresentation = options || {{}};
}}
function fwSlotHTML(html, relation) {{
    // A slot the pattern no longer names (e.g. the clause after "think + que")
    // stays plain text in the example rather than taking a colour.
    const formula = relation?.formulaHTML;
    let out = String(html || '').replace(/<span class=['"]fw-token-([vc])['"]>/g, (tag, side) => {{
        if (formula && !new RegExp(`fw-token-${{side}}['"]`).test(formula)) return '<span>';
        const type = relation?.slotTypes?.[side];
        const isPOS = ['noun', 'verb', 'adj', 'pron', 'prep', 'adv', 'det', 'conj', 'clitic', 'part'].includes(type);
        const rgb = isPOS ? fwPresentation.posRgb?.(type) : null;
        const colour = rgb ? `rgb(${{rgb}})` : (side === 'v' ? '#8fb8d8' : '#c3a6df');
        return `<span class="fw-token-${{side}}" data-pos="${{type || ''}}" style="color:${{colour}}">`;
    }});
    if (relation?.pos) {{
        const pos = relation.pos;
        const rgb = fwPresentation.posRgb?.(pos);
        const connectorStyle = rgb ? ` style="--sense-match-rgb: ${{rgb}}; --fw-pos-rgb: ${{rgb}};"` : '';
        out = out.replace(/<span class=['"]fw-token-connector['"]>/g, `<span class="fw-token-connector" data-pos="${{esc(pos)}}"${{connectorStyle}}>`);
    }}
    return out;
}}
function fwCreditHTML(example) {{
    if (example?.metadata?.source?.source_record_id) {{
        return fwPresentation.provenanceHTML?.(example) || '';
    }}
    return String(example?.source || '').startsWith('Original teaching example') ? 'Teaching example' : 'Source not verified';
}}

function esc(str) {{
    return String(str || '')
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#39;');
}}

function shortGloss(raw) {{
    const s = String(raw || '').trim();
    if (!s) return '';
    return s.split(/[,;/]/)[0].trim().toLowerCase();
}}

function meaningOf(obj) {{
    if (!obj) return '';
    if (typeof obj === 'string') return obj;
    return obj.gloss || obj.meaning || obj.translation || obj.definition || '';
}}

/** Lookup a deterministic grammar-word definition for a card in the given language. */
export function getGrammarWordDefinition(cardOrWord, lang) {{
    if (!cardOrWord) return null;
    const wordKey = typeof cardOrWord === 'string'
        ? cardOrWord.trim().toLowerCase()
        : (cardOrWord.targetWord || cardOrWord.word || '').trim().toLowerCase();
    if (!wordKey) return null;

    const langKey = String(lang || 'pt').toLowerCase();
    const suite = GRAMMAR_WORDS[langKey] || PORTUGUESE_GRAMMAR_WORDS;
    const base = suite[wordKey] || null;
    if (!base || !syntaxTrialEnabled()) return base;
    const language = suite === SPANISH_GRAMMAR_WORDS ? 'es' : 'pt';
    const additions = FW_SYNTAX_TRIAL[language]?.[wordKey];
    if (!additions) return base;
    const relations = base.relations.map((relation, index) => {{
        const extra = additions[index];
        if (!extra?.length) return relation;
        const existing = relation.examples || [];
        const ids = new Set(existing.map(example => example.example_id).filter(Boolean));
        const examples = [...extra.filter(example => !ids.has(example.example_id)), ...existing];
        return {{...relation, examples, targetHTML: examples[0].targetHTML, translation: examples[0].translation}};
    }});
    return {{...base, relations, uses: relations, syntaxTrial: true}};
}}

// Backward-compatibility alias:
export function getPortugueseGrammarDefinition(cardOrWord, lang) {{
    return getGrammarWordDefinition(cardOrWord, lang || 'pt');
}}

/** Determine if a card is a function word. */
export function isFunctionWordCard(card, lang) {{
    if (!card) return false;
    if (card.partOfSpeech === 'FW' || card.pos === 'FW' || card.functionWord) return true;
    return Boolean(getGrammarWordDefinition(card, lang));
}}

export function isPortugueseGrammarWord(card, lang) {{
    if (!card) return false;
    const isPt = !lang || lang === 'portuguese' || lang === 'pt' || lang === 'portuguese_brazilian';
    if (!isPt) return false;
    const wordKey = String(card.targetWord || card.word || card.lemma || '').trim().toLowerCase();
    return Boolean(PORTUGUESE_GRAMMAR_WORDS[wordKey]);
}}

export function isSpanishGrammarWord(card, lang) {{
    if (!card) return false;
    const isEs = lang === 'spanish' || lang === 'es';
    if (!isEs) return false;
    const wordKey = String(card.targetWord || card.word || card.lemma || '').trim().toLowerCase();
    return Boolean(SPANISH_GRAMMAR_WORDS[wordKey]);
}}

export function getSpanishGrammarDefinition(card, lang) {{
    return getGrammarWordDefinition(card, lang || 'es');
}}

// Computes ambient glow CSS for any flashcard based on POS rules & FW signature glow
export function getCardAmbientGlow(card, lang, activePos, isSplitCard, getPosAccentRgbFn) {{
    const getRgb = getPosAccentRgbFn || (typeof window !== 'undefined' ? window.getPosAccentRgb : null) || (() => '148, 163, 184');

    // 1. Companion card ("Card 1 of 2"): single POS color matching active companion card
    if (isSplitCard && card?.splitInfo) {{
        const splitPos = card.splitInfo.pos || card.partOfSpeech || activePos;
        const rgb = getRgb(splitPos);
        return `radial-gradient(circle at 50% 20%, rgba(${{rgb}}, 0.18), transparent 70%)`;
    }}

    // 2. Merged lemmas: merged cards represent a single unified lexeme (verb).
    // Always emits a single centered radial glow in the verb color (green).
    if (card?.mergedLemma) {{
        const mergedPos = (card.partOfSpeech && !/verb|aux/i.test(card.partOfSpeech))
            ? card.partOfSpeech
            : (activePos || card.partOfSpeech || 'VERB');
        const rgb = getRgb(mergedPos);
        return `radial-gradient(circle at 50% 20%, rgba(${{rgb}}, 0.18), transparent 70%)`;
    }}

    const NON_LEXICAL_POS = new Set(['MWE', 'CLITIC', 'SENSE_CYCLE', 'EXAMPLE_ONLY', 'PHRASE']);

    const isRareMeaning = m => {{
        if (!m) return true;
        if (m.isRareSense || m.lowShare || m.rare || m.unassigned || m.exampleOnly) return true;
        if (m.assignment_method === 'unassigned') return true;
        const prom = String(m.prominenceLabel || '').trim().toLowerCase();
        if (prom === 'rare') return true;
        if (typeof window !== 'undefined' && typeof window.getSenseProminenceInfo === 'function') {{
            try {{
                if (window.getSenseProminenceInfo(m)?.key === 'rare') return true;
            }} catch (_) {{}}
        }}
        const share = Number(m.shownShare ?? m.percentage);
        const hasExplicitShare = (m.shownShare != null || m.percentage != null) && !isNaN(share);
        const hasExamples = Boolean(
            m.targetSentence ||
            (Array.isArray(m.allExamples) && m.allExamples.length > 0) ||
            (Array.isArray(m.examples) && m.examples.length > 0)
        );
        if (hasExplicitShare && share <= 0) return true;
        if (!hasExamples && hasExplicitShare && share < 0.10) return true;
        return false;
    }};

    const cardMeanings = (card?.meanings || []).filter(m => {{
        if (!m) return false;
        const pos = m.pos === 'SENSE_CYCLE' ? (m.cycle_pos || '') : (m.pos || '');
        if (!pos || NON_LEXICAL_POS.has(String(pos).toUpperCase())) return false;
        if (typeof window !== 'undefined' && typeof window.isHiddenExpressionOnParent === 'function' && window.isHiddenExpressionOnParent(card, m)) return false;
        return true;
    }});

    const nonRareMeanings = cardMeanings.filter(m => !isRareMeaning(m));
    const candidateMeanings = nonRareMeanings.length > 0 ? nonRareMeanings : cardMeanings;

    const totalWeight = candidateMeanings.reduce(
        (sum, m) => sum + (Number(m.shownShare ?? m.percentage) || 0),
        0
    );

    const rgbWeights = new Map();
    const rgbOrder = [];

    for (const m of candidateMeanings) {{
        const pos = m.pos === 'SENSE_CYCLE' ? (m.cycle_pos || '') : (m.pos || '');
        const rgb = getRgb(pos);
        if (!rgb) continue;
        const weight = Number(m.shownShare ?? m.percentage) || 0;
        if (!rgbWeights.has(rgb)) {{
            rgbWeights.set(rgb, 0);
            rgbOrder.push(rgb);
        }}
        rgbWeights.set(rgb, rgbWeights.get(rgb) + weight);
    }}

    let distinctRgb = rgbOrder;
    if (totalWeight > 0 && rgbOrder.length > 1) {{
        const significant = rgbOrder.filter(rgb => (rgbWeights.get(rgb) / totalWeight) >= 0.10);
        if (significant.length > 0) {{
            distinctRgb = significant;
        }}
    }}

    if (distinctRgb.length === 0) {{
        let fallbackPos = card?.partOfSpeech;
        if (!fallbackPos || String(fallbackPos).toUpperCase() === 'FW') {{
            const gw = typeof getGrammarWordDefinition === 'function' ? getGrammarWordDefinition(card, lang) : null;
            fallbackPos = gw?.role || gw?.pos || card?.pos || activePos;
        }}
        distinctRgb = [getRgb(fallbackPos || activePos)];
    }}

    const activeRgb = activePos ? getRgb(activePos) : null;
    if (activeRgb && distinctRgb.includes(activeRgb) && distinctRgb[0] !== activeRgb) {{
        distinctRgb = [activeRgb, ...distinctRgb.filter(c => c !== activeRgb)];
    }}

    // Single POS color: single centered radial glow
    if (distinctRgb.length <= 1) {{
        return `radial-gradient(circle at 50% 20%, rgba(${{distinctRgb[0]}}, 0.18), transparent 70%)`;
    }}

    // 2 POS colors: multi-corner glow
    if (distinctRgb.length === 2) {{
        return `radial-gradient(circle at 22% 16%, rgba(${{distinctRgb[0]}}, 0.17), transparent 58%), radial-gradient(circle at 78% 16%, rgba(${{distinctRgb[1]}}, 0.17), transparent 58%)`;
    }}

    // 3 or more POS colors
    return `radial-gradient(circle at 18% 16%, rgba(${{distinctRgb[0]}}, 0.15), transparent 50%), radial-gradient(circle at 50% 12%, rgba(${{distinctRgb[1]}}, 0.15), transparent 50%), radial-gradient(circle at 82% 16%, rgba(${{distinctRgb[2]}}, 0.15), transparent 50%)`;
}}

// Active state for deterministic card back navigation
let _activeWordKey = null;
let _activeRelIndex = 0;
let _activeExampleIndex = 0;

export function selectFunctionWordRelation(relIdx) {{
    _activeRelIndex = Number(relIdx) || 0;
    _activeExampleIndex = 0;
    refreshFunctionWordCardBack();
}}

// Backward compatibility alias:
export function selectFunctionWordUse(useIdx) {{
    selectFunctionWordRelation(useIdx);
}}

export function cycleFunctionWordExample() {{
    const container = document.querySelector('.fw-deterministic-card');
    if (!container) return;
    const cardWord = container.dataset.word;
    const lang = container.dataset.lang || 'pt';
    const data = getGrammarWordDefinition(cardWord, lang);
    if (!data) return;

    const relations = data.relations || data.uses || [];
    if (_activeRelIndex >= relations.length) _activeRelIndex = 0;
    const currentRel = relations[_activeRelIndex];
    const examples = currentRel?.examples || (currentRel?.targetHTML ? [currentRel] : []);
    if (examples.length <= 1) {{
        const plain = (currentRel?.targetHTML || currentRel?.target || '').replace(/<[^>]+>/g, '');
        window.speakTargetSentence?.() || window.speakText?.(plain);
        return;
    }}

    _activeExampleIndex = (_activeExampleIndex + 1) % examples.length;
    refreshFunctionWordCardBack();

    const curEx = examples[_activeExampleIndex];
    if (curEx) {{
        const plain = (curEx.targetHTML || curEx.target || '').replace(/<[^>]+>/g, '');
        window.speakText?.(plain);
    }}
}}

function renderFwTicks(total, current) {{
    if (total < 2) return '';
    const ticks = Array.from({{ length: total }}, (_, i) =>
        `<span class="example-tick${{i === current ? ' is-current' : ''}}"></span>`
    ).join('');
    return `<div class="example-ticks" role="img" aria-label="Example ${{current + 1}} of ${{total}}">${{ticks}}</div>`;
}}

function refreshFunctionWordCardBack() {{
    const container = document.querySelector('.fw-deterministic-card');
    if (!container) return;
    const cardWord = container.dataset.word;
    const lang = container.dataset.lang || 'pt';
    const data = getGrammarWordDefinition(cardWord, lang);
    if (!data) return;

    const relations = data.relations || data.uses || [];
    if (_activeRelIndex >= relations.length) _activeRelIndex = 0;
    const currentRel = relations[_activeRelIndex];

    // Update container POS and ambient glow
    if (currentRel?.pos) {{
        if (container.dataset) container.dataset.pos = currentRel.pos;
        const rgb = fwPresentation.posRgb?.(currentRel.pos);
        if (rgb && container.style?.setProperty) container.style.setProperty('--sense-match-rgb', rgb);
    }}

    // Update relations selection
    container.querySelectorAll('.fw-relation-box').forEach((btn, i) => {{
        const isSelected = i === _activeRelIndex;
        btn.setAttribute('aria-pressed', String(isSelected));
        btn.classList.toggle('is-selected', isSelected);
    }});

    // Update contextual parts box (e.g. for hybrid nos)
    const dynamicPartsBox = container.querySelector('.fw-dynamic-parts-box');
    if (dynamicPartsBox) {{
        if (currentRel?.parts && currentRel.parts.length === 2) {{
            dynamicPartsBox.innerHTML = `<span class="fw-part-pill">${{esc(currentRel.parts[0])}}</span> <span class="fw-part-plus">+</span> <span class="fw-part-pill">${{esc(currentRel.parts[1])}}</span>`;
            dynamicPartsBox.style.display = 'inline-flex';
        }} else {{
            dynamicPartsBox.style.display = 'none';
        }}
    }}

    // Get current example from examples array
    const examples = currentRel?.examples || (currentRel?.targetHTML ? [currentRel] : []);
    if (_activeExampleIndex >= examples.length) _activeExampleIndex = 0;
    const currentEx = examples[_activeExampleIndex] || currentRel;

    // Update sentence target and translation
    const sentenceEl = container.querySelector('.fw-sentence-target');
    if (sentenceEl && currentEx) {{
        sentenceEl.innerHTML = fwSlotHTML(currentEx.targetHTML || currentEx.target || '', currentRel);
    }}

    const transEl = container.querySelector('.fw-sentence-translation');
    if (transEl && currentEx) {{
        transEl.textContent = currentEx.translation || '';
    }}

    const creditStartEl = container.querySelector('.fw-credit-start');
    if (creditStartEl) {{
        creditStartEl.innerHTML = fwCreditHTML(currentEx);
    }}

    const ticksContainer = container.querySelector('.fw-sentence-ticks-container');
    if (ticksContainer) {{
        ticksContainer.innerHTML = renderFwTicks(examples.length, _activeExampleIndex);
    }}
}}

// Make functions available globally for onclick handlers
if (typeof window !== 'undefined') {{
    window.selectFunctionWordRelation = selectFunctionWordRelation;
    window.selectFunctionWordUse = selectFunctionWordUse;
    window.cycleFunctionWordExample = cycleFunctionWordExample;
    window.getCardAmbientGlow = getCardAmbientGlow;
    window.FW_SIGNATURE_GLOW_RGB = FW_SIGNATURE_GLOW_RGB;
}}

export function functionWordLabelText(label) {{
    if (!label || !label.value) return '';
    if (label.kind === 'unit') {{
        const gloss = shortGloss(meaningOf(label.gloss));
        return gloss ? `${{label.value}} · ${{gloss}}` : label.value;
    }}
    const name = ROLE_NAMES[label.value] || label.value.replace(/_/g, ' ');
    const gloss = label.value === 'prep' ? String(label.gloss || '').replace(/\\s*\\(\\+ verb\\)$/, '') : label.gloss;
    return gloss && gloss !== name ? `${{name}} · ${{gloss}}` : name;
}}

/** Card-back block replacing the sense list: what the word does, and its constructions. */
export function functionWordBlockHTML(card, lang) {{
    const fwData = getGrammarWordDefinition(card, lang) || (card?.functionWord?.uses ? card.functionWord : null);

    // 1. Deterministic layout for Portuguese and Spanish focus grammar words
    if (fwData && (fwData.relations || fwData.uses)) {{
        const wordKey = fwData.word || card.targetWord || card.word;
        if (_activeWordKey !== wordKey) {{
            _activeWordKey = wordKey;
            _activeRelIndex = 0;
            _activeExampleIndex = 0;
        }}

        const relations = fwData.relations || fwData.uses || [];
        if (_activeRelIndex >= relations.length) _activeRelIndex = 0;
        const currentRel = relations[_activeRelIndex];

        // Permanent contraction formula box (e.g. naquele = em + aquele)
        let partsBoxHTML = '';
        if (fwData.parts && fwData.parts.length === 2) {{
            partsBoxHTML = `
                <div class="fw-parts-box">
                    <span class="fw-part-pill">${{esc(fwData.parts[0])}}</span>
                    <span class="fw-part-plus">+</span>
                    <span class="fw-part-pill">${{esc(fwData.parts[1])}}</span>
                </div>`;
        }}

        // Contextual formula box for hybrid words (e.g. nos = em + os when contraction relation is active)
        let dynamicPartsHTML = '';
        if (!fwData.parts) {{
            const hasParts = currentRel?.parts && currentRel.parts.length === 2;
            dynamicPartsHTML = `
                <div class="fw-parts-box fw-dynamic-parts-box" style="${{hasParts ? 'display: inline-flex;' : 'display: none;'}}">
                    ${{hasParts ? `<span class="fw-part-pill">${{esc(currentRel.parts[0])}}</span> <span class="fw-part-plus">+</span> <span class="fw-part-pill">${{esc(currentRel.parts[1])}}</span>` : ''}}
                </div>`;
        }}

        // Relations tiles (no square brackets, color alone establishes constituents)
        const relationsHTML = relations.map((rel, i) => {{
            const isSelected = i === _activeRelIndex;
            return `
                <button type="button" class="fw-relation-box${{isSelected ? ' is-selected' : ''}}" data-pos="${{esc(rel.pos || '')}}" aria-pressed="${{isSelected}}" onclick="event.stopPropagation(); window.selectFunctionWordRelation(${{i}})">
                    <div class="fw-relation-formula">${{fwSlotHTML(rel.formulaHTML || esc(rel.formula || ''), rel)}}</div>
                    <p class="fw-relation-rule">${{esc(rel.rule || rel.description || '')}}</p>
                </button>`;
        }}).join('');

        const examples = currentRel?.examples || (currentRel?.targetHTML ? [currentRel] : []);
        if (_activeExampleIndex >= examples.length) _activeExampleIndex = 0;
        const currentEx = examples[_activeExampleIndex] || currentRel;

        const targetHTML = currentEx?.targetHTML || currentRel?.targetHTML || esc(currentRel?.target || '');
        const plainTargetText = targetHTML.replace(/<[^>]+>/g, '');
        const sourceText = currentEx?.source || '';
        const ticksHTML = renderFwTicks(examples.length, _activeExampleIndex);

        return `
            <div class="fw-deterministic-card" data-word="${{esc(wordKey)}}" data-lang="${{esc(lang || 'pt')}}" data-pos="${{esc(currentRel?.pos || '')}}" style="--sense-match-rgb: ${{fwPresentation.posRgb?.(currentRel?.pos || card?.pos || card?.meanings?.[0]?.pos) || 'var(--accent-primary-rgb)'}};">
                <div class="fw-header">
                    <h2 class="fw-heading">${{esc(wordKey)}}</h2>
                    ${{partsBoxHTML}}
                    ${{dynamicPartsHTML}}
                    <div class="fw-section-header">Function Word · Example Patterns</div>
                    ${{fwData.syntaxTrial ? '<div class="fw-section-header">Reviewed example trial</div>' : ''}}
                </div>
                <div class="fw-relations-list">
                    ${{relationsHTML}}
                </div>
                <div class="fw-sentence-panel" onclick="event.stopPropagation(); window.cycleFunctionWordExample();">
                    <div class="fw-sentence-target">${{fwSlotHTML(targetHTML, currentRel)}}</div>
                    <div class="fw-sentence-translation">${{esc(currentEx?.translation || currentRel?.translation || '')}}</div>
                    <div class="fw-example-credit-row">
                        <span class="fw-credit-start">${{fwCreditHTML(currentEx)}}</span>
                        <div class="fw-sentence-ticks-container">${{ticksHTML}}</div>
                    </div>
                </div>
            </div>`;
    }}

    // Uncovered words keep the normal meaning rows; legacy summary chips are retired.
    return '';
}}

/** The label under one example's translation; empty when the rules gave none. */
export function functionWordExampleHTML(example) {{
    const label = example?.metadata?.function_word;
    const text = functionWordLabelText(label);
    if (!text) return '';
    const kind = label.kind === 'unit' ? 'fw-chip-pattern' : 'fw-chip-role';
    return `<div class="fw-example-label"><span class="fw-chip ${{kind}}">${{esc(text)}}</span></div>`;
}}
"""

with open(JS_FILE, "w") as f:
    f.write(js_code)

print("Synchronized app/js/function-word-card.js successfully!")
