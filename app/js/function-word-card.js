// Function-word presentation & ambient lighting for Fluency.
//
// Function words -- articles, prepositions, particles, clitics, contractions -- are
// taught by their structural role and deterministic content-word variation,
// rather than dictionary sense assignments.
//
// Portuguese closed-class focus set: que, de, se, o, nos, naquele.

export const FW_SIGNATURE_GLOW_RGB = '212, 218, 245'; // Periwinkle Moonstone Off-White

// Curated deterministic definitions for Portuguese closed-class focus words.
export const PORTUGUESE_GRAMMAR_WORDS = {
    que: {
        word: 'que',
        role: 'Connector',
        pos: 'CONJ',
        posLabel: 'Connector',
        rank: 1,
        frequency: 38240,
        uses: [
            {
                id: 'that',
                english: 'that',
                description: 'Introduces what someone thinks, says or knows.',
                examples: [
                    { target: 'Acho que vai chover.', translation: 'I think it’s going to rain.', highlight: 'que', content: 'achar' },
                    { target: 'Sei que você está certo.', translation: 'I know that you are right.', highlight: 'que', content: 'saber' },
                    { target: 'Ela disse que viria.', translation: 'She said that she would come.', highlight: 'que', content: 'dizer' }
                ]
            },
            {
                id: 'relative',
                english: 'who / which / that',
                description: 'Adds information about a person or thing.',
                examples: [
                    { target: 'Este é o livro que estou lendo.', translation: 'This is the book that I’m reading.', highlight: 'que', content: 'livro' },
                    { target: 'A pessoa que me ajudou foi embora.', translation: 'The person who helped me left.', highlight: 'que', content: 'pessoa' }
                ]
            },
            {
                id: 'than',
                english: 'than',
                description: 'Connects the two sides of a comparison.',
                examples: [
                    { target: 'Ela é mais alta que eu.', translation: 'She is taller than me.', highlight: 'que', content: 'mais alta' },
                    { target: 'Este café é melhor que o outro.', translation: 'This coffee is better than the other.', highlight: 'que', content: 'melhor' }
                ]
            }
        ]
    },
    de: {
        word: 'de',
        role: 'Preposition',
        pos: 'PREP',
        posLabel: 'Preposition',
        rank: 4,
        frequency: 25447,
        uses: [
            {
                id: 'of-from',
                english: 'of / from',
                description: 'Shows connection, possession or origin.',
                examples: [
                    { target: 'Ela é de Lisboa.', translation: 'She is from Lisbon.', highlight: 'de', content: 'origem' },
                    { target: 'A casa de Ana é bonita.', translation: 'Ana\'s house is beautiful.', highlight: 'de', content: 'posse' },
                    { target: 'Quero um copo de água.', translation: 'I want a glass of water.', highlight: 'de', content: 'conteúdo' }
                ]
            },
            {
                id: 'verb-object',
                english: 'connects a verb to its object',
                description: 'Required link after common verbs before a noun or action.',
                examples: [
                    { target: 'Gosto de música.', translation: 'I like music.', highlight: 'de', content: 'gostar' },
                    { target: 'Preciso de ajuda.', translation: 'I need help.', highlight: 'de', content: 'precisar' },
                    { target: 'Tudo depende de você.', translation: 'Everything depends on you.', highlight: 'de', content: 'depender' }
                ]
            }
        ]
    },
    se: {
        word: 'se',
        role: 'Conjunction & Clitic',
        pos: 'CONJ',
        posLabel: 'Conjunction & Clitic',
        rank: 11,
        frequency: 16900,
        uses: [
            {
                id: 'conditional',
                english: 'if / whether',
                description: 'Introduces a condition or an indirect question.',
                examples: [
                    { target: 'Se chover, fico em casa.', translation: 'If it rains, I’ll stay home.', highlight: 'Se', content: 'condição' },
                    { target: 'Não sei se ele vem.', translation: 'I don\'t know if he is coming.', highlight: 'se', content: 'dúvida' }
                ]
            },
            {
                id: 'reflexive',
                english: '-self / each other',
                description: 'Action reflects back on the person doing it.',
                examples: [
                    { target: 'Ela se olhou no espelho.', translation: 'She looked at herself in the mirror.', highlight: 'se', content: 'olhar' },
                    { target: 'Ele se levantou cedo.', translation: 'He got [himself] up early.', highlight: 'se', content: 'levantar' },
                    { target: 'Nós nos abraçamos com carinho.', translation: 'We hugged each other warmly.', highlight: 'nos', content: 'abraçar' }
                ]
            },
            {
                id: 'passive',
                english: 'action without naming who',
                description: 'Describes something done generally or passively.',
                examples: [
                    { target: 'Aqui se fala português.', translation: 'Portuguese is spoken here.', highlight: 'se', content: 'falar' },
                    { target: 'Vende-se esta casa.', translation: 'This house is for sale.', highlight: 'se', content: 'vender' }
                ]
            }
        ]
    },
    o: {
        word: 'o',
        role: 'Article & Pronoun',
        pos: 'DET',
        posLabel: 'Article & Pronoun',
        rank: 3,
        frequency: 31200,
        uses: [
            {
                id: 'article',
                english: 'the',
                description: 'Before a masculine singular noun.',
                examples: [
                    { target: 'O livro está na mesa.', translation: 'The book is on the table.', highlight: 'O', content: 'livro' },
                    { target: 'O dia está lindo.', translation: 'The day is beautiful.', highlight: 'O', content: 'dia' }
                ]
            },
            {
                id: 'pronoun',
                english: 'him / it',
                description: 'Object pronoun receiving the action of a verb.',
                examples: [
                    { target: 'Eu o vi ontem no parque.', translation: 'I saw him yesterday in the park.', highlight: 'o', content: 'ver' },
                    { target: 'Não consigo encontrá-lo.', translation: 'I cannot find it.', highlight: 'lo', content: 'encontrar' }
                ]
            }
        ]
    },
    nos: {
        word: 'nos',
        role: 'Pronoun & Contraction',
        pos: 'PRON',
        posLabel: 'Pronoun & Contraction',
        rank: 44,
        frequency: 7890,
        uses: [
            {
                id: 'pronoun-object',
                english: 'us / to us',
                description: 'Object pronoun receiving the action.',
                examples: [
                    { target: 'Ela nos chamou para jantar.', translation: 'She called us for dinner.', highlight: 'nos', content: 'chamar' },
                    { target: 'Eles nos disseram a verdade.', translation: 'They told us the truth.', highlight: 'nos', content: 'dizer' }
                ]
            },
            {
                id: 'pronoun-reflexive',
                english: 'ourselves / each other',
                description: 'Reflexive or reciprocal action done by nós.',
                examples: [
                    { target: 'Nós nos abraçamos.', translation: 'We hugged each other.', highlight: 'nos', content: 'abraçar' },
                    { target: 'Nós nos conhecemos bem.', translation: 'We know each other well.', highlight: 'nos', content: 'conhecer' }
                ]
            },
            {
                id: 'contraction',
                english: 'in / on / at the',
                description: 'Contraction of em + os before a masculine plural noun.',
                parts: ['em', 'os'],
                examples: [
                    { target: 'Está nos livros.', translation: 'It’s in the books.', highlight: 'nos', content: 'livros' },
                    { target: 'Eles moram nos Estados Unidos.', translation: 'They live in the United States.', highlight: 'nos', content: 'Estados Unidos' }
                ]
            }
        ]
    },
    naquele: {
        word: 'naquele',
        role: 'Contraction',
        pos: 'CONTRACTION',
        posLabel: 'Contraction',
        rank: 1104,
        frequency: 420,
        parts: ['em', 'aquele'],
        partsLabel: 'Contraction formula',
        uses: [
            {
                id: 'in-that',
                english: 'in that / on that',
                description: 'Points to a particular place or time.',
                examples: [
                    { target: 'Eu estava naquele lugar.', translation: 'I was in that place.', highlight: 'naquele', content: 'lugar' },
                    { target: 'Tudo começou naquele dia.', translation: 'Everything started on that day.', highlight: 'naquele', content: 'dia' },
                    { target: 'Naquele momento, tudo mudou.', translation: 'At that moment, everything changed.', highlight: 'Naquele', content: 'momento' }
                ]
            }
        ]
    }
};

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
let _activeUseIndex = 0;
let _activeExampleIndex = 0;

export function selectFunctionWordUse(useIdx) {
    _activeUseIndex = Number(useIdx) || 0;
    _activeExampleIndex = 0;
    refreshFunctionWordCardBack();
}

export function selectFunctionWordExample(exIdx) {
    _activeExampleIndex = Number(exIdx) || 0;
    refreshFunctionWordCardBack();
}

function refreshFunctionWordCardBack() {
    const container = document.querySelector('.fw-deterministic-card');
    if (!container) return;
    const cardWord = container.dataset.word;
    const data = PORTUGUESE_GRAMMAR_WORDS[cardWord];
    if (!data) return;

    const uses = data.uses || [];
    if (_activeUseIndex >= uses.length) _activeUseIndex = 0;
    const currentUse = uses[_activeUseIndex];
    const examples = currentUse?.examples || [];
    if (_activeExampleIndex >= examples.length) _activeExampleIndex = 0;
    const currentEx = examples[_activeExampleIndex];

    // Update uses selection
    container.querySelectorAll('.fw-use-btn').forEach((btn, i) => {
        const isSelected = i === _activeUseIndex;
        btn.setAttribute('aria-pressed', String(isSelected));
        btn.classList.toggle('is-selected', isSelected);
    });

    // Update contextual parts box (e.g. for hybrid nos)
    const dynamicPartsBox = container.querySelector('.fw-dynamic-parts-box');
    if (dynamicPartsBox) {
        if (currentUse?.parts && currentUse.parts.length === 2) {
            dynamicPartsBox.innerHTML = `<span class="fw-part-pill">${esc(currentUse.parts[0])}</span> <span class="fw-part-plus">+</span> <span class="fw-part-pill">${esc(currentUse.parts[1])}</span>`;
            dynamicPartsBox.style.display = 'inline-flex';
        } else {
            dynamicPartsBox.style.display = 'none';
        }
    }

    // Update content variation chips
    const variationBar = container.querySelector('.fw-variation-bar');
    if (variationBar) {
        if (examples.length > 1) {
            const chipsHtml = examples.map((ex, idx) => {
                const isSelected = idx === _activeExampleIndex;
                const label = ex.content || ex.highlight || `Example ${idx + 1}`;
                return `<button type="button" class="fw-chip-step${isSelected ? ' is-selected' : ''}" aria-pressed="${isSelected}" onclick="window.selectFunctionWordExample(${idx})">${esc(label)}</button>`;
            }).join('');
            variationBar.innerHTML = `<span class="fw-variation-label">Content variation (${examples.length})</span><div class="fw-chips">${chipsHtml}</div>`;
            variationBar.style.display = 'flex';
        } else {
            variationBar.style.display = 'none';
        }
    }

    // Update example target sentence with highlight and translation
    const sentenceEl = container.querySelector('.fw-example-sentence');
    if (sentenceEl && currentEx) {
        const hl = currentEx.highlight || data.word;
        const re = new RegExp(`(\\b${hl}\\b)`, 'i');
        const highlightedTarget = esc(currentEx.target).replace(re, '<strong class="fw-highlight">$1</strong>');
        sentenceEl.innerHTML = highlightedTarget;
    }

    const transEl = container.querySelector('.fw-example-translation');
    if (transEl && currentEx) {
        transEl.textContent = currentEx.translation;
    }
}

// Make functions available globally for onclick handlers
if (typeof window !== 'undefined') {
    window.selectFunctionWordUse = selectFunctionWordUse;
    window.selectFunctionWordExample = selectFunctionWordExample;
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
    if (ptData && ptData.uses) {
        const wordKey = ptData.word || card.targetWord || card.word;
        if (_activeWordKey !== wordKey) {
            _activeWordKey = wordKey;
            _activeUseIndex = 0;
            _activeExampleIndex = 0;
        }

        const uses = ptData.uses || [];
        if (_activeUseIndex >= uses.length) _activeUseIndex = 0;
        const currentUse = uses[_activeUseIndex];
        const examples = currentUse?.examples || [];
        if (_activeExampleIndex >= examples.length) _activeExampleIndex = 0;
        const currentEx = examples[_activeExampleIndex];

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

        // Contextual formula box for hybrid words (e.g. nos = em + os when contraction use is active)
        let dynamicPartsHTML = '';
        if (!ptData.parts) {
            const hasParts = currentUse?.parts && currentUse.parts.length === 2;
            dynamicPartsHTML = `
                <div class="fw-parts-box fw-dynamic-parts-box" style="${hasParts ? 'display: inline-flex;' : 'display: none;'}">
                    ${hasParts ? `<span class="fw-part-pill">${esc(currentUse.parts[0])}</span> <span class="fw-part-plus">+</span> <span class="fw-part-pill">${esc(currentUse.parts[1])}</span>` : ''}
                </div>`;
        }

        // Uses list
        const usesHTML = uses.map((u, i) => {
            const isSelected = i === _activeUseIndex;
            return `
                <button type="button" class="fw-use-btn${isSelected ? ' is-selected' : ''}" aria-pressed="${isSelected}" onclick="window.selectFunctionWordUse(${i})">
                    <strong>${esc(u.english)}</strong>
                    <p>${esc(u.description)}</p>
                </button>`;
        }).join('');

        // Content variation stepper chips
        let variationChipsHTML = '';
        if (examples.length > 1) {
            const chips = examples.map((ex, idx) => {
                const isSelected = idx === _activeExampleIndex;
                const label = ex.content || ex.highlight || `Example ${idx + 1}`;
                return `<button type="button" class="fw-chip-step${isSelected ? ' is-selected' : ''}" aria-pressed="${isSelected}" onclick="window.selectFunctionWordExample(${idx})">${esc(label)}</button>`;
            }).join('');
            variationChipsHTML = `
                <div class="fw-variation-bar">
                    <span class="fw-variation-label">Content variation (${examples.length})</span>
                    <div class="fw-chips">${chips}</div>
                </div>`;
        } else {
            variationChipsHTML = `<div class="fw-variation-bar" style="display: none;"></div>`;
        }

        // Example sentence highlight
        let exampleTargetHTML = '';
        if (currentEx) {
            const hl = currentEx.highlight || ptData.word;
            const re = new RegExp(`(\\b${hl}\\b)`, 'i');
            exampleTargetHTML = esc(currentEx.target).replace(re, '<strong class="fw-highlight">$1</strong>');
        }

        return `
            <div class="fw-deterministic-card" data-word="${esc(wordKey)}">
                <div class="fw-header">
                    <div class="fw-heading">${esc(wordKey)}</div>
                    <span class="fw-badge">${esc(ptData.posLabel || ptData.role)}</span>
                </div>
                ${partsBoxHTML}
                ${dynamicPartsHTML}
                <div class="fw-uses-grid">
                    ${usesHTML}
                </div>
                <div class="fw-example-section">
                    ${variationChipsHTML}
                    <div class="fw-example-box" onclick="window.speakTargetSentence?.() || window.speakText?.('${esc(currentEx?.target || '')}')">
                        <div class="fw-example-sentence">${exampleTargetHTML}</div>
                        <div class="fw-example-translation">${esc(currentEx?.translation || '')}</div>
                        <div class="fw-example-hint">Tap a chip above to see how <strong>${esc(wordKey)}</strong> connects different content words</div>
                    </div>
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
