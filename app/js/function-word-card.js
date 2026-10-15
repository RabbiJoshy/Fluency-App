// Function-word presentation & ambient lighting for Fluency.
//
// Function words -- articles, prepositions, particles, clitics, contractions -- are
// taught by their structural role and deterministic content-word variation,
// rather than dictionary sense assignments.
//
// Portuguese closed-class focus set: que, de, se, o, nos, naquele.

export const FW_SIGNATURE_GLOW_RGB = '212, 218, 245'; // Periwinkle Moonstone Off-White

// Curated deterministic relational definitions for Portuguese closed-class focus words.
export const PORTUGUESE_GRAMMAR_WORDS = {
    de: {
        word: 'de',
        role: 'Preposition',
        rank: 4,
        frequency: 25447,
        relations: [
            {
                tag: 'Verbal Valency',
                formulaHTML: '<span class="fw-token-v">Verb</span> + <span class="fw-token-connector">de</span> + <span class="fw-token-c">Complement</span>',
                rule: "Required link: the preceding verb governs 'de' before its object or action.",
                targetHTML: "<span class='fw-token-v'>Gosto</span> <span class='fw-token-connector'>de</span> <span class='fw-token-c'>música</span>.",
                translation: 'I like music.'
            },
            {
                tag: 'Noun Attribution',
                formulaHTML: '<span class="fw-token-v">Noun</span> + <span class="fw-token-connector">de</span> + <span class="fw-token-c">Noun / Origin</span>',
                rule: 'Nominal binding: connects a head noun to its owner, origin, or content.',
                targetHTML: "Quero um <span class='fw-token-v'>copo</span> <span class='fw-token-connector'>de</span> <span class='fw-token-c'>água</span>.",
                translation: 'I want a glass of water.'
            }
        ]
    },
    que: {
        word: 'que',
        role: 'Connector',
        rank: 1,
        frequency: 38240,
        relations: [
            {
                tag: 'Clausal Link',
                formulaHTML: '<span class="fw-token-v">Thought / Speech</span> + <span class="fw-token-connector">que</span> + <span class="fw-token-c">Clause</span>',
                rule: 'Subordination: bridges what someone thinks, says, or knows to the statement.',
                targetHTML: "<span class='fw-token-v'>Acho</span> <span class='fw-token-connector'>que</span> <span class='fw-token-c'>vai chover</span>.",
                translation: 'I think it’s going to rain.'
            },
            {
                tag: 'Relative Pronoun',
                formulaHTML: '<span class="fw-token-v">Noun</span> + <span class="fw-token-connector">que</span> + <span class="fw-token-c">Description</span>',
                rule: 'Relativization: refers back to a noun while connecting more information.',
                targetHTML: "Este é o <span class='fw-token-v'>livro</span> <span class='fw-token-connector'>que</span> <span class='fw-token-c'>estou lendo</span>.",
                translation: 'This is the book that I’m reading.'
            },
            {
                tag: 'Comparison',
                formulaHTML: '<span class="fw-token-v">Degree</span> + <span class="fw-token-connector">que</span> + <span class="fw-token-c">Standard</span>',
                rule: 'Comparison: connects the two sides of a degree or quality difference.',
                targetHTML: "Ela é <span class='fw-token-v'>mais alta</span> <span class='fw-token-connector'>que</span> <span class='fw-token-c'>eu</span>.",
                translation: 'She is taller than me.'
            }
        ]
    },
    naquele: {
        word: 'naquele',
        role: 'Contraction',
        rank: 1104,
        frequency: 88,
        parts: ['em', 'aquele'],
        relations: [
            {
                tag: 'Deictic Location',
                formulaHTML: '<span class="fw-token-connector">em + aquele</span> + <span class="fw-token-c">Place / Time</span>',
                rule: 'Contraction formula pointing to a distant place or past moment.',
                targetHTML: "Eu estava <span class='fw-token-connector'>naquele</span> <span class='fw-token-c'>lugar</span>.",
                translation: 'I was in that place.'
            }
        ]
    },
    nos: {
        word: 'nos',
        role: 'Pronoun & Contraction',
        rank: 44,
        frequency: 1581,
        relations: [
            {
                tag: 'Object Pronoun',
                formulaHTML: '<span class="fw-token-connector">nos</span> + <span class="fw-token-v">Verb</span>',
                rule: "Pronominal argument: represents 'us / to us' receiving the action of a verb.",
                targetHTML: "Ela <span class='fw-token-connector'>nos</span> <span class='fw-token-v'>chamou</span> para jantar.",
                translation: 'She called us for dinner.'
            },
            {
                tag: 'Contraction',
                formulaHTML: '<span class="fw-token-connector">em + os</span> + <span class="fw-token-c">Plural Noun</span>',
                parts: ['em', 'os'],
                rule: "Contraction of 'em + os' (in / on / at the) before a masculine plural noun.",
                targetHTML: "Está <span class='fw-token-connector'>nos</span> <span class='fw-token-c'>livros</span>.",
                translation: 'It’s in the books.'
            }
        ]
    },
    se: {
        word: 'se',
        role: 'Conjunction & Clitic',
        rank: 11,
        frequency: 7806,
        relations: [
            {
                tag: 'Condition',
                formulaHTML: '<span class="fw-token-connector">Se</span> + <span class="fw-token-v">Condition</span> , <span class="fw-token-c">Result</span>',
                rule: 'Conditional marker: introduces a hypothetical situation before its consequence.',
                targetHTML: "<span class='fw-token-connector'>Se</span> <span class='fw-token-v'>chover</span>, <span class='fw-token-c'>fico em casa</span>.",
                translation: 'If it rains, I’ll stay home.'
            },
            {
                tag: 'Reflexive Clitic',
                formulaHTML: '<span class="fw-token-connector">se</span> + <span class="fw-token-v">Verb of self-action</span>',
                rule: 'Reflexive clitic: action reflects back onto the person doing it.',
                targetHTML: "Ela <span class='fw-token-connector'>se</span> <span class='fw-token-v'>olhou</span> no espelho.",
                translation: 'She looked at herself in the mirror.'
            }
        ]
    },
    o: {
        word: 'o',
        role: 'Article & Clitic',
        rank: 3,
        frequency: 34538,
        relations: [
            {
                tag: 'Definite Article',
                formulaHTML: '<span class="fw-token-connector">o</span> + <span class="fw-token-c">Masculine Noun</span>',
                rule: 'Definite determiner: points to a specific masculine singular noun.',
                targetHTML: "<span class='fw-token-connector'>O</span> <span class='fw-token-c'>livro</span> está na mesa.",
                translation: 'The book is on the table.'
            },
            {
                tag: 'Object Clitic',
                formulaHTML: '<span class="fw-token-v">Verb</span> + <span class="fw-token-connector">o</span>',
                rule: 'Direct object pronoun: replaces a 3rd-person masculine singular object.',
                targetHTML: "Eu <span class='fw-token-connector'>o</span> <span class='fw-token-v'>vi</span> ontem no parque.",
                translation: 'I saw him yesterday in the park.'
            }
        ]
    }
};

// Backward-compatibility: alias .uses to .relations
for (const entry of Object.values(PORTUGUESE_GRAMMAR_WORDS)) {
    entry.uses = entry.relations;
}

const ROLE_NAMES = {
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
};

function esc(value) {
    return String(value ?? '')
        .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;');
}

function shortGloss(gloss) {
    return String(gloss || '').split(/\s*[(;,]/)[0].trim();
}

const NOT_A_MEANING = /^used other than|\b(?:form|spelling) of\b|^synonym of\b/i;

function meaningOf(gloss) {
    return NOT_A_MEANING.test(String(gloss || '')) ? '' : gloss;
}

export function isPortugueseGrammarWord(card, lang) {
    if (!card) return false;
    const isPt = !lang || lang === 'portuguese' || lang === 'pt' || lang === 'portuguese_brazilian';
    if (!isPt) return false;
    const wordKey = String(card.targetWord || card.word || card.lemma || '').trim().toLowerCase();
    return Boolean(PORTUGUESE_GRAMMAR_WORDS[wordKey]);
}

export function getPortugueseGrammarDefinition(card, lang) {
    if (!isPortugueseGrammarWord(card, lang)) return null;
    const wordKey = String(card.targetWord || card.word || card.lemma || '').trim().toLowerCase();
    return PORTUGUESE_GRAMMAR_WORDS[wordKey] || null;
}

export function isFunctionWordCard(card, lang) {
    return Boolean(card?.functionWord || isPortugueseGrammarWord(card, lang));
}

// Computes ambient glow CSS for any flashcard based on POS rules & FW signature glow
export function getCardAmbientGlow(card, lang, activePos, isSplitCard, getPosAccentRgbFn) {
    const getRgb = getPosAccentRgbFn || window.getPosAccentRgb || (() => '148, 163, 184');

    // 1. Function words get the dedicated Periwinkle Moonstone Off-White halo
    if (isFunctionWordCard(card, lang)) {
        return `radial-gradient(circle at 50% 20%, rgba(${FW_SIGNATURE_GLOW_RGB}, 0.18), transparent 70%)`;
    }

    // 2. Non-function words
    // Companion card ("Card 1 of 2"): single POS color matching active companion card
    if (isSplitCard && card?.splitInfo) {
        const splitPos = card.splitInfo.pos || card.partOfSpeech || activePos;
        const rgb = getRgb(splitPos);
        return `radial-gradient(circle at 50% 20%, rgba(${rgb}, 0.18), transparent 70%)`;
    }

    // Collect all distinct POS on this card
    const distinctPos = [...new Set(
        (card?.meanings || [])
            .map(m => m?.pos)
            .filter(p => p && !['MWE', 'CLITIC', 'SENSE_CYCLE', 'EXAMPLE_ONLY'].includes(p))
    )];
    if (distinctPos.length === 0 && (card?.partOfSpeech || activePos)) {
        distinctPos.push(card.partOfSpeech || activePos);
    }

    // Single POS: single centered radial glow
    if (distinctPos.length <= 1) {
        const rgb = getRgb(distinctPos[0] || activePos);
        return `radial-gradient(circle at 50% 20%, rgba(${rgb}, 0.18), transparent 70%)`;
    }

    // Multi-POS Unified: multi-corner glow
    if (distinctPos.length === 2) {
        const rgb1 = getRgb(distinctPos[0]);
        const rgb2 = getRgb(distinctPos[1]);
        return `radial-gradient(circle at 22% 16%, rgba(${rgb1}, 0.17), transparent 58%), radial-gradient(circle at 78% 16%, rgba(${rgb2}, 0.17), transparent 58%)`;
    }

    // 3 or more POS
    const rgb1 = getRgb(distinctPos[0]);
    const rgb2 = getRgb(distinctPos[1]);
    const rgb3 = getRgb(distinctPos[2]);
    return `radial-gradient(circle at 18% 16%, rgba(${rgb1}, 0.15), transparent 50%), radial-gradient(circle at 50% 12%, rgba(${rgb2}, 0.15), transparent 50%), radial-gradient(circle at 82% 16%, rgba(${rgb3}, 0.15), transparent 50%)`;
}

// Active state for deterministic card back navigation
let _activeWordKey = null;
let _activeRelIndex = 0;

export function selectFunctionWordRelation(relIdx) {
    _activeRelIndex = Number(relIdx) || 0;
    refreshFunctionWordCardBack();
}

// Backward compatibility alias:
export function selectFunctionWordUse(useIdx) {
    selectFunctionWordRelation(useIdx);
}

function refreshFunctionWordCardBack() {
    const container = document.querySelector('.fw-deterministic-card');
    if (!container) return;
    const cardWord = container.dataset.word;
    const data = PORTUGUESE_GRAMMAR_WORDS[cardWord];
    if (!data) return;

    const relations = data.relations || data.uses || [];
    if (_activeRelIndex >= relations.length) _activeRelIndex = 0;
    const currentRel = relations[_activeRelIndex];

    // Update relations selection
    container.querySelectorAll('.fw-relation-box').forEach((btn, i) => {
        const isSelected = i === _activeRelIndex;
        btn.setAttribute('aria-pressed', String(isSelected));
        btn.classList.toggle('is-selected', isSelected);
    });

    // Update contextual parts box (e.g. for hybrid nos)
    const dynamicPartsBox = container.querySelector('.fw-dynamic-parts-box');
    if (dynamicPartsBox) {
        if (currentRel?.parts && currentRel.parts.length === 2) {
            dynamicPartsBox.innerHTML = `<span class="fw-part-pill">${esc(currentRel.parts[0])}</span> <span class="fw-part-plus">+</span> <span class="fw-part-pill">${esc(currentRel.parts[1])}</span>`;
            dynamicPartsBox.style.display = 'inline-flex';
        } else {
            dynamicPartsBox.style.display = 'none';
        }
    }

    // Update sentence target and translation
    const sentenceEl = container.querySelector('.fw-sentence-target');
    if (sentenceEl && currentRel) {
        sentenceEl.innerHTML = currentRel.targetHTML || currentRel.target || '';
    }

    const transEl = container.querySelector('.fw-sentence-translation');
    if (transEl && currentRel) {
        transEl.textContent = currentRel.translation || '';
    }
}

// Make functions available globally for onclick handlers
if (typeof window !== 'undefined') {
    window.selectFunctionWordRelation = selectFunctionWordRelation;
    window.selectFunctionWordUse = selectFunctionWordUse;
    window.getCardAmbientGlow = getCardAmbientGlow;
    window.FW_SIGNATURE_GLOW_RGB = FW_SIGNATURE_GLOW_RGB;
}

export function functionWordLabelText(label) {
    if (!label || !label.value) return '';
    if (label.kind === 'unit') {
        const gloss = shortGloss(meaningOf(label.gloss));
        return gloss ? `${label.value} · ${gloss}` : label.value;
    }
    const name = ROLE_NAMES[label.value] || label.value.replace(/_/g, ' ');
    const gloss = label.value === 'prep' ? String(label.gloss || '').replace(/\s*\(\+ verb\)$/, '') : label.gloss;
    return gloss && gloss !== name ? `${name} · ${gloss}` : name;
}

/** Card-back block replacing the sense list: what the word does, and its constructions. */
export function functionWordBlockHTML(card, lang) {
    const ptData = getPortugueseGrammarDefinition(card, lang) || (card?.functionWord?.uses ? card.functionWord : null);

    // 1. Deterministic layout for Portuguese focus grammar words
    if (ptData && (ptData.relations || ptData.uses)) {
        const wordKey = ptData.word || card.targetWord || card.word;
        if (_activeWordKey !== wordKey) {
            _activeWordKey = wordKey;
            _activeRelIndex = 0;
        }

        const relations = ptData.relations || ptData.uses || [];
        if (_activeRelIndex >= relations.length) _activeRelIndex = 0;
        const currentRel = relations[_activeRelIndex];

        // Permanent contraction formula box (e.g. naquele = em + aquele)
        let partsBoxHTML = '';
        if (ptData.parts && ptData.parts.length === 2) {
            partsBoxHTML = `
                <div class="fw-parts-box">
                    <span class="fw-part-pill">${esc(ptData.parts[0])}</span>
                    <span class="fw-part-plus">+</span>
                    <span class="fw-part-pill">${esc(ptData.parts[1])}</span>
                </div>`;
        }

        // Contextual formula box for hybrid words (e.g. nos = em + os when contraction relation is active)
        let dynamicPartsHTML = '';
        if (!ptData.parts) {
            const hasParts = currentRel?.parts && currentRel.parts.length === 2;
            dynamicPartsHTML = `
                <div class="fw-parts-box fw-dynamic-parts-box" style="${hasParts ? 'display: inline-flex;' : 'display: none;'}">
                    ${hasParts ? `<span class="fw-part-pill">${esc(currentRel.parts[0])}</span> <span class="fw-part-plus">+</span> <span class="fw-part-pill">${esc(currentRel.parts[1])}</span>` : ''}
                </div>`;
        }

        // Relations tiles (no square brackets, color alone establishes constituents)
        const relationsHTML = relations.map((rel, i) => {
            const isSelected = i === _activeRelIndex;
            return `
                <button type="button" class="fw-relation-box${isSelected ? ' is-selected' : ''}" aria-pressed="${isSelected}" onclick="event.stopPropagation(); window.selectFunctionWordRelation(${i})">
                    <div class="fw-relation-top">
                        <span class="fw-relation-formula">${rel.formulaHTML || esc(rel.formula || '')}</span>
                        <span class="fw-relation-tag">${esc(rel.tag || '')}</span>
                    </div>
                    <p class="fw-relation-rule">${esc(rel.rule || rel.description || '')}</p>
                </button>`;
        }).join('');

        const targetHTML = currentRel?.targetHTML || esc(currentRel?.target || '');
        const plainTargetText = targetHTML.replace(/<[^>]+>/g, '');

        return `
            <div class="fw-deterministic-card" data-word="${esc(wordKey)}">
                <div class="fw-header">
                    <h2 class="fw-heading">${esc(wordKey)}</h2>
                </div>
                ${partsBoxHTML}
                ${dynamicPartsHTML}
                <div class="fw-relations-list">
                    ${relationsHTML}
                </div>
                <div class="fw-sentence-panel" onclick="event.stopPropagation(); (window.speakTargetSentence?.() || window.speakText?.('${esc(plainTargetText)}'))">
                    <div class="fw-sentence-target">${targetHTML}</div>
                    <div class="fw-sentence-translation">${esc(currentRel?.translation || '')}</div>
                </div>
            </div>`;
    }

    // 2. Fallback to existing prototype for other languages/words
    const summary = card?.functionWord;
    if (!summary) return '';
    const distinct = texts => [...new Set(texts.filter(Boolean))];
    const roleTexts = distinct((summary.roles || []).map(r => functionWordLabelText({ kind: 'role', ...r }))).slice(0, 3);
    const patternTexts = distinct((summary.patterns || []).filter(p => p.count >= 2 && meaningOf(p.gloss))
        .map(p => functionWordLabelText({ kind: 'unit', ...p }))).slice(0, 3);
    const roleChips = roleTexts.map(t => `<span class="fw-chip fw-chip-role">${esc(t)}</span>`).join('');
    const patternChips = patternTexts.map(t => `<span class="fw-chip fw-chip-pattern">${esc(t)}</span>`).join('');

    return `
        <div class="fw-block">
            <div class="fw-row"><span class="fw-badge">Grammar word</span>${roleChips}</div>
            ${patternChips ? `<div class="fw-row"><span class="fw-row-label">Patterns</span>${patternChips}</div>` : ''}
        </div>`;
}

/** The label under one example's translation; empty when the rules gave none. */
export function functionWordExampleHTML(example) {
    const label = example?.metadata?.function_word;
    const text = functionWordLabelText(label);
    if (!text) return '';
    const kind = label.kind === 'unit' ? 'fw-chip-pattern' : 'fw-chip-role';
    return `<div class="fw-example-label"><span class="fw-chip ${kind}">${esc(text)}</span></div>`;
}
