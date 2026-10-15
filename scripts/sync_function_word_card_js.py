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
    object_pron: 'object',
    reflexive: 'reflexive (-self)',
    interrogative: 'question word',
    indefinite: 'pronoun',
    quantifier: 'amount word',
    conj: 'conjunction',
    conj_that: 'conjunction',
    conj_if: 'conjunction',
    conj_before: 'conjunction',
    infinitive_to: 'to + verb',
    degree_too: 'too + adjective',
    existential_er: 'there is / are',
    locative_er: 'there (place)',
    pronominal_adverb: 'with a preposition',
    partitive_er: 'of them',
    possessive: 'possessive',
    aux_perfect: 'helper verb',
    aux_passive: 'helper verb (passive)',
    copula: 'linking verb',
    be: 'verb',
    adverb: 'adverb',
    demonstrative: 'pointing word',
    relative: 'relative pronoun',
    personal_a: 'personal a',
    impersonal_se: 'impersonal se',
    than: 'comparison',
    conditional: 'conditional',
    negation: 'negation',
}};

function esc(value) {{
    return String(value ?? '')
        .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;');
}}

function shortGloss(gloss) {{
    return String(gloss || '').split(/\\s*[(;,]/)[0].trim();
}}

const NOT_A_MEANING = /^used other than|\\b(?:form|spelling) of\\b|^synonym of\\b/i;

function meaningOf(gloss) {{
    return NOT_A_MEANING.test(String(gloss || '')) ? '' : gloss;
}}

export function getGrammarWordDefinition(cardOrWord, lang) {{
    const langKey = String(lang || 'pt').toLowerCase();
    const dict = GRAMMAR_WORDS[langKey] || (langKey.startsWith('es') ? SPANISH_GRAMMAR_WORDS : PORTUGUESE_GRAMMAR_WORDS);
    if (!dict) return null;
    const wordKey = typeof cardOrWord === 'string'
        ? cardOrWord.trim().toLowerCase()
        : String(cardOrWord?.targetWord || cardOrWord?.word || cardOrWord?.lemma || '').trim().toLowerCase();
    return dict[wordKey] || null;
}}

export function isPortugueseGrammarWord(card, lang) {{
    if (!card) return false;
    const isPt = !lang || lang === 'portuguese' || lang === 'pt' || lang === 'portuguese_brazilian';
    if (!isPt) return false;
    const wordKey = String(card.targetWord || card.word || card.lemma || '').trim().toLowerCase();
    return Boolean(PORTUGUESE_GRAMMAR_WORDS[wordKey]);
}}

export function getPortugueseGrammarDefinition(card, lang) {{
    return getGrammarWordDefinition(card, lang || 'pt');
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

export function isFunctionWordCard(card, lang) {{
    return Boolean(card?.functionWord || getGrammarWordDefinition(card, lang));
}}

// Computes ambient glow CSS for any flashcard based on POS rules & FW signature glow
export function getCardAmbientGlow(card, lang, activePos, isSplitCard, getPosAccentRgbFn) {{
    const getRgb = getPosAccentRgbFn || (typeof window !== 'undefined' ? window.getPosAccentRgb : null) || (() => '148, 163, 184');

    // 1. Function words get the dedicated Periwinkle Moonstone Off-White halo
    if (isFunctionWordCard(card, lang)) {{
        return `radial-gradient(circle at 50% 20%, rgba(${{FW_SIGNATURE_GLOW_RGB}}, 0.18), transparent 70%)`;
    }}

    // 2. Non-function words
    // Companion card ("Card 1 of 2"): single POS color matching active companion card
    if (isSplitCard && card?.splitInfo) {{
        const splitPos = card.splitInfo.pos || card.partOfSpeech || activePos;
        const rgb = getRgb(splitPos);
        return `radial-gradient(circle at 50% 20%, rgba(${{rgb}}, 0.18), transparent 70%)`;
    }}

    // Collect distinct POS realized on this card (prioritize active/non-rare meanings)
    const nonRareMeanings = (card?.meanings || []).filter(m =>
        m && !m.isRareSense && m.prominenceLabel !== 'Rare' && !m.exampleOnly && !m.unassigned
    );
    const candidateMeanings = nonRareMeanings.length > 0 ? nonRareMeanings : (card?.meanings || []);

    const distinctPos = [...new Set(
        candidateMeanings
            .map(m => m?.pos)
            .filter(p => p && !['MWE', 'CLITIC', 'SENSE_CYCLE', 'EXAMPLE_ONLY'].includes(p))
    )];
    if (distinctPos.length === 0 && (card?.partOfSpeech || activePos)) {{
        distinctPos.push(card.partOfSpeech || activePos);
    }}

    // Single POS: single centered radial glow
    if (distinctPos.length <= 1) {{
        const rgb = getRgb(distinctPos[0] || activePos);
        return `radial-gradient(circle at 50% 20%, rgba(${{rgb}}, 0.18), transparent 70%)`;
    }}

    // Multi-POS Unified: multi-corner glow
    if (distinctPos.length === 2) {{
        const rgb1 = getRgb(distinctPos[0]);
        const rgb2 = getRgb(distinctPos[1]);
        return `radial-gradient(circle at 22% 16%, rgba(${{rgb1}}, 0.17), transparent 58%), radial-gradient(circle at 78% 16%, rgba(${{rgb2}}, 0.17), transparent 58%)`;
    }}

    // 3 or more POS
    const rgb1 = getRgb(distinctPos[0]);
    const rgb2 = getRgb(distinctPos[1]);
    const rgb3 = getRgb(distinctPos[2]);
    return `radial-gradient(circle at 18% 16%, rgba(${{rgb1}}, 0.15), transparent 50%), radial-gradient(circle at 50% 12%, rgba(${{rgb2}}, 0.15), transparent 50%), radial-gradient(circle at 82% 16%, rgba(${{rgb3}}, 0.15), transparent 50%)`;
}}

// Active state for deterministic card back navigation
let _activeWordKey = null;
let _activeRelIndex = 0;

export function selectFunctionWordRelation(relIdx) {{
    _activeRelIndex = Number(relIdx) || 0;
    refreshFunctionWordCardBack();
}}

// Backward compatibility alias:
export function selectFunctionWordUse(useIdx) {{
    selectFunctionWordRelation(useIdx);
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

    // Update sentence target and translation
    const sentenceEl = container.querySelector('.fw-sentence-target');
    if (sentenceEl && currentRel) {{
        sentenceEl.innerHTML = currentRel.targetHTML || currentRel.target || '';
    }}

    const transEl = container.querySelector('.fw-sentence-translation');
    if (transEl && currentRel) {{
        transEl.textContent = currentRel.translation || '';
    }}
}}

// Make functions available globally for onclick handlers
if (typeof window !== 'undefined') {{
    window.selectFunctionWordRelation = selectFunctionWordRelation;
    window.selectFunctionWordUse = selectFunctionWordUse;
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
                <button type="button" class="fw-relation-box${{isSelected ? ' is-selected' : ''}}" aria-pressed="${{isSelected}}" onclick="event.stopPropagation(); window.selectFunctionWordRelation(${{i}})">
                    <div class="fw-relation-formula">${{rel.formulaHTML || esc(rel.formula || '')}}</div>
                    <p class="fw-relation-rule">${{esc(rel.rule || rel.description || '')}}</p>
                </button>`;
        }}).join('');

        const targetHTML = currentRel?.targetHTML || esc(currentRel?.target || '');
        const plainTargetText = targetHTML.replace(/<[^>]+>/g, '');

        return `
            <div class="fw-deterministic-card" data-word="${{esc(wordKey)}}" data-lang="${{esc(lang || 'pt')}}">
                <div class="fw-header">
                    <h2 class="fw-heading">${{esc(wordKey)}}</h2>
                    <div class="fw-section-header">Function Word · Example Patterns</div>
                </div>
                ${{partsBoxHTML}}
                ${{dynamicPartsHTML}}
                <div class="fw-relations-list">
                    ${{relationsHTML}}
                </div>
                <div class="fw-sentence-panel" onclick="event.stopPropagation(); (window.speakTargetSentence?.() || window.speakText?.('${{esc(plainTargetText)}}'))">
                    <div class="fw-sentence-target">${{targetHTML}}</div>
                    <div class="fw-sentence-translation">${{esc(currentRel?.translation || '')}}</div>
                </div>
            </div>`;
    }}

    // 2. Fallback to existing prototype for other languages/words
    const summary = card?.functionWord;
    if (!summary) return '';
    const distinct = texts => [...new Set(texts.filter(Boolean))];
    const roleTexts = distinct((summary.roles || []).map(r => functionWordLabelText({{ kind: 'role', ...r }}))).slice(0, 3);
    const patternTexts = distinct((summary.patterns || []).filter(p => p.count >= 2 && meaningOf(p.gloss))
        .map(p => functionWordLabelText({{ kind: 'unit', ...p }}))).slice(0, 3);
    const roleChips = roleTexts.map(t => `<span class="fw-chip fw-chip-role">${{esc(t)}}</span>`).join('');
    const patternChips = patternTexts.map(t => `<span class="fw-chip fw-chip-pattern">${{esc(t)}}</span>`).join('');

    return `
        <div class="fw-block">
            <div class="fw-row"><span class="fw-badge">Grammar word</span>${{roleChips}}</div>
            ${{patternChips ? `<div class="fw-row"><span class="fw-row-label">Patterns</span>${{patternChips}}</div>` : ''}}
        </div>`;
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
