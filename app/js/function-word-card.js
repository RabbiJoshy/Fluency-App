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
    },
    em: {
        word: 'em',
        role: 'Preposition',
        rank: 21,
        frequency: 6025,
        relations: [
            {
                formulaHTML: '<span class="fw-token-v">Verb</span> + <span class="fw-token-connector">em</span> + <span class="fw-token-c">Place</span>',
                rule: 'Spatial location: anchors an action or state to an enclosed place, city, or space.',
                targetHTML: "<span class='fw-token-v'>Moro</span> <span class='fw-token-connector'>em</span> <span class='fw-token-c'>Lisboa</span>.",
                translation: 'I live in Lisbon.'
            },
            {
                formulaHTML: '<span class="fw-token-v">Action</span> + <span class="fw-token-connector">em</span> + <span class="fw-token-c">Time Period</span>',
                rule: 'Temporal framing: situates an event within a month, year, or duration.',
                targetHTML: "<span class='fw-token-v'>Viajo</span> <span class='fw-token-connector'>em</span> <span class='fw-token-c'>maio</span>.",
                translation: 'I travel in May.'
            }
        ]
    },
    para: {
        word: 'para',
        role: 'Preposition',
        rank: 9,
        frequency: 11850,
        relations: [
            {
                formulaHTML: '<span class="fw-token-v">Verb</span> + <span class="fw-token-connector">para</span> + <span class="fw-token-c">Destination</span>',
                rule: 'Direction and destination: points toward a final physical goal or place of arrival.',
                targetHTML: "<span class='fw-token-v'>Vou</span> <span class='fw-token-connector'>para</span> <span class='fw-token-c'>casa</span>.",
                translation: 'I am going home.'
            },
            {
                formulaHTML: '<span class="fw-token-v">Action</span> + <span class="fw-token-connector">para</span> + <span class="fw-token-c">Infinitive Goal</span>',
                rule: 'Purpose and objective: links an intentional action to what it aims to achieve.',
                targetHTML: "<span class='fw-token-v'>Estudo</span> <span class='fw-token-connector'>para</span> <span class='fw-token-c'>aprender</span>.",
                translation: 'I study in order to learn.'
            },
            {
                formulaHTML: '<span class="fw-token-v">Object</span> + <span class="fw-token-connector">para</span> + <span class="fw-token-c">Recipient</span>',
                rule: 'Beneficiary: marks who receives or benefits from something.',
                targetHTML: "Isto é <span class='fw-token-v'>um presente</span> <span class='fw-token-connector'>para</span> <span class='fw-token-c'>você</span>.",
                translation: 'This is a gift for you.'
            }
        ]
    },
    com: {
        word: 'com',
        role: 'Preposition',
        rank: 17,
        frequency: 7842,
        relations: [
            {
                formulaHTML: '<span class="fw-token-v">Verb</span> + <span class="fw-token-connector">com</span> + <span class="fw-token-c">Companion</span>',
                rule: 'Accompaniment: joins an action to the person or entity sharing it.',
                targetHTML: "<span class='fw-token-v'>Falo</span> <span class='fw-token-connector'>com</span> <span class='fw-token-c'>você</span> amanhã.",
                translation: 'I speak with you tomorrow.'
            },
            {
                formulaHTML: '<span class="fw-token-v">Action</span> + <span class="fw-token-connector">com</span> + <span class="fw-token-c">Tool / Manner</span>',
                rule: 'Instrument and manner: describes the means used or attitude applied.',
                targetHTML: "<span class='fw-token-v'>Escrevo</span> <span class='fw-token-connector'>com</span> <span class='fw-token-c'>cuidado</span>.",
                translation: 'I write with care.'
            }
        ]
    },
    por: {
        word: 'por',
        role: 'Preposition',
        rank: 16,
        frequency: 6938,
        relations: [
            {
                formulaHTML: '<span class="fw-token-v">Verb / State</span> + <span class="fw-token-connector">por</span> + <span class="fw-token-c">Motive / Cause</span>',
                rule: 'Causal ground: links an emotion, gratitude, or outcome back to its reason.',
                targetHTML: "<span class='fw-token-v'>Obrigado</span> <span class='fw-token-connector'>por</span> <span class='fw-token-c'>ajudar</span>.",
                translation: 'Thank you for helping.'
            },
            {
                formulaHTML: '<span class="fw-token-v">Movement</span> + <span class="fw-token-connector">por</span> + <span class="fw-token-c">Transit Space</span>',
                rule: 'Trajectory: marks the path, medium, or space through which motion occurs.',
                targetHTML: "<span class='fw-token-v'>Caminho</span> <span class='fw-token-connector'>por</span> <span class='fw-token-c'>aqui</span>.",
                translation: 'I walk around here.'
            }
        ]
    },
    no: {
        word: 'no',
        role: 'Contraction',
        rank: 13,
        frequency: 4450,
        parts: ['em', 'o'],
        relations: [
            {
                formulaHTML: '<span class="fw-token-connector">em + o</span> + <span class="fw-token-c">Masculine Noun / Place</span>',
                rule: "Contraction of 'em + o' (in the / at the) before a specific masculine noun.",
                targetHTML: "O livro está <span class='fw-token-connector'>no</span> <span class='fw-token-c'>quarto</span>.",
                translation: 'The book is in the room.'
            }
        ]
    },
    na: {
        word: 'na',
        role: 'Contraction',
        rank: 31,
        frequency: 4170,
        parts: ['em', 'a'],
        relations: [
            {
                formulaHTML: '<span class="fw-token-connector">em + a</span> + <span class="fw-token-c">Feminine Noun / Place</span>',
                rule: "Contraction of 'em + a' (in the / at the) before a specific feminine noun.",
                targetHTML: "Ela está <span class='fw-token-connector'>na</span> <span class='fw-token-c'>praia</span>.",
                translation: 'She is at the beach.'
            }
        ]
    },
    do: {
        word: 'do',
        role: 'Contraction',
        rank: 19,
        frequency: 7403,
        parts: ['de', 'o'],
        relations: [
            {
                formulaHTML: '<span class="fw-token-connector">de + o</span> + <span class="fw-token-c">Masculine Noun / Origin</span>',
                rule: "Contraction of 'de + o' (of the / from the) denoting possession, origin, or attribute.",
                targetHTML: "Este é o carro <span class='fw-token-connector'>do</span> <span class='fw-token-c'>meu pai</span>.",
                translation: "This is my father's car."
            }
        ]
    },
    da: {
        word: 'da',
        role: 'Contraction',
        rank: 27,
        frequency: 5714,
        parts: ['de', 'a'],
        relations: [
            {
                formulaHTML: '<span class="fw-token-connector">de + a</span> + <span class="fw-token-c">Feminine Noun / Origin</span>',
                rule: "Contraction of 'de + a' (of the / from the) denoting possession, origin, or attribute.",
                targetHTML: "Esta é a chave <span class='fw-token-connector'>da</span> <span class='fw-token-c'>casa</span>.",
                translation: 'This is the key to the house.'
            }
        ]
    },
    como: {
        word: 'como',
        role: 'Connector',
        rank: 23,
        frequency: 5447,
        relations: [
            {
                formulaHTML: '<span class="fw-token-v">Action</span> + <span class="fw-token-connector">como</span> + <span class="fw-token-c">Model / Standard</span>',
                rule: 'Simile and manner: compares the style or way an action is performed to an archetype.',
                targetHTML: "Ela <span class='fw-token-v'>canta</span> <span class='fw-token-connector'>como</span> <span class='fw-token-c'>um pássaro</span>.",
                translation: 'She sings like a bird.'
            },
            {
                formulaHTML: '<span class="fw-token-connector">como</span> + <span class="fw-token-c">Role / Capacity</span>',
                rule: 'Capacity and function: specifies the role, profession, or capacity someone acts in.',
                targetHTML: "Trabalho <span class='fw-token-connector'>como</span> <span class='fw-token-c'>engenheiro</span>.",
                translation: 'I work as an engineer.'
            }
        ]
    },
    mas: {
        word: 'mas',
        role: 'Connector',
        rank: 26,
        frequency: 6058,
        relations: [
            {
                formulaHTML: '<span class="fw-token-v">Statement</span> + <span class="fw-token-connector">mas</span> + <span class="fw-token-c">Counterpoint</span>',
                rule: 'Adversative bridge: introduces a contrast, restriction, or unexpected limitation.',
                targetHTML: "<span class='fw-token-v'>Tentei</span>, <span class='fw-token-connector'>mas</span> <span class='fw-token-c'>não consegui</span>.",
                translation: 'I tried, but I could not.'
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
    const getRgb = getPosAccentRgbFn || (typeof window !== 'undefined' ? window.getPosAccentRgb : null) || (() => '148, 163, 184');

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
                    <div class="fw-relation-formula">${rel.formulaHTML || esc(rel.formula || '')}</div>
                    <p class="fw-relation-rule">${esc(rel.rule || rel.description || '')}</p>
                </button>`;
        }).join('');

        const targetHTML = currentRel?.targetHTML || esc(currentRel?.target || '');
        const plainTargetText = targetHTML.replace(/<[^>]+>/g, '');

        return `
            <div class="fw-deterministic-card" data-word="${esc(wordKey)}">
                <div class="fw-header">
                    <h2 class="fw-heading">${esc(wordKey)}</h2>
                    <div class="fw-section-header">Function Word · Example Patterns</div>
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
