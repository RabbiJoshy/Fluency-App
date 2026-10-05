// The replica card: real demo entries and the markup that draws them.
//
// Two features show a flashcard without the app having loaded a deck, and they
// are for different people:
//
//   * tutorial.js     — for LEARNERS. Guided, one element at a time, starts
//                       on the selected mode’s card. Opened by "?" and first run.
//   * walkthrough.js  — for VISITORS (employers, anyone being shown the app).
//                       Two screens, whole faces labelled at once. Opened from
//                       About, which links it and never embeds the tutorial.
//
// Neither owns the card. This module does, so both show the same card, and it
// knows nothing about steps, notes or audiences.
//
// "Exact replica": the card is built from the same class names and inline
// styles that updateCard() in flashcards.js emits, so it inherits the real
// card's CSS rather than a lookalike stylesheet. Only SIZE is overridden (see
// .card-replica in style.css). The Spotify button is not a picture of a button:
// it calls the real window.spotifyPlayTrack() with a real track id and lyric
// timestamp. Nothing here writes progress or touches deck state.

// ---------------------------------------------------------------------------
// Demo cards — real entries, real lyrics, real track ids.
// ---------------------------------------------------------------------------
//
// `cielo` is a genuine Bad Bunny deck entry — rank, line count, meanings,
// percentages, lyrics and timestamps all read out of the built deck rather
// than written for the demo. `tem` is curated from the live Portuguese
// speech release because its Wiktionary senses demonstrate the compact
// metadata and cross-card-reference treatment.

export const REPLICA_CARDS = {
    // Chosen for the quality of its sense assignment, not at random. `fuego`
    // was here first and read badly: its "light (for smoking)" row was
    // illustrated by "Fuego, desde que te vi me puse roja" and its "passion"
    // row by "me voy a fuego" — an idiom meaning "I go all out". Both are
    // real output of the current classifier, and a visitor who reads the
    // English can see they don't demonstrate the meaning claimed. A showcase
    // has to be a case the system gets right; `cielo` splits cleanly into two
    // concrete meanings a non-Spanish-speaker can check from the translation
    // alone. Revisit when sense assignment improves.
    cielo: {
        mode: 'lyrics',
        word: 'cielo',
        lemma: 'cielo',
        pos: 'NOUN',
        rank: 344,
        vocabSize: 2000,
        corpusCount: 33,
        meanings: [
            {
                pos: 'NOUN',
                translation: 'heaven',
                context: 'religious',
                pct: 70,
                examples: [
                    {
                        target: 'El cielo en el infierno, nadie va a entender',
                        english: 'Heaven in hell, no one will understand',
                        song: 'Volando (Remix)',
                        trackId: '0G2zPzWqVjR68iNPmx2TBe',
                        positionMs: 220310,
                        vocalists: 'Bad Bunny',
                    },
                    {
                        target: 'Lo subo al cielo, yo soy su Messiah',
                        english: 'I take him to heaven, I am his Messiah',
                        song: 'LA NOCHE DE ANOCHE',
                        trackId: '2XIc1pqjXV3Cr2BQUGNBck',
                        positionMs: 137190,
                        vocalists: 'ROSALÍA',
                    },
                    {
                        target: 'Ya estoy acostumbra’o a estar siempre en el cielo',
                        english: 'I’m already used to always being in heaven',
                        song: 'Estamos Bien',
                        trackId: '2OWVCFTolecLiGZPquvWvT',
                        positionMs: 68170,
                        vocalists: null,
                    },
                ],
            },
            {
                pos: 'NOUN',
                translation: 'sky',
                context: 'firmament',
                pct: 30,
                examples: [
                    {
                        target: 'Y ver pa’l cielo a ver si te veo caer',
                        english: 'And I look to the sky to see if I see you fall',
                        song: 'BAILE INoLVIDABLE',
                        trackId: '2lTm559tuIvatlT1u0JYG2',
                        positionMs: 118690,
                        vocalists: null,
                    },
                ],
            },
        ],
    },

    tem: {
        mode: 'speech',
        word: 'tem',
        lemma: 'ter',
        pos: 'VERB',
        rank: 47,
        vocabSize: 6000,
        corpusCount: 1326,
        defaultMeaningIndex: 2,
        meanings: [
            {
                pos: 'VERB',
                translation: 'he/she has (possesses or holds something)',
                context: 'to be in possession of something',
                pct: 50,
                metadata: [
                    { short: 'tr.', full: 'transitive', family: 'construction' },
                ],
                examples: [
                    {
                        target: 'E isso tem muito mais do que isso!',
                        english: 'And this has much more than that!',
                        sourceLabel: 'Speech example',
                    },
                ],
            },
            {
                pos: 'VERB',
                translation: 'he/she has to; must',
                context: null,
                pct: 30,
                metadata: [
                    { short: 'aux.', full: 'auxiliary', family: 'construction' },
                    { short: '+ de/que + infinitive', full: 'with de or que + infinitive', family: 'construction' },
                ],
                examples: [
                    {
                        target: 'Mas não tem de o ser.',
                        english: "But it doesn't have to be.",
                        sourceLabel: 'Speech example',
                    },
                ],
            },
            {
                pos: 'VERB',
                translation: 'there is (to exist physically or abstractly)',
                context: null,
                pct: 15,
                metadata: [
                    { short: 'impers.', full: 'impersonal', family: 'construction' },
                    { short: 'tr.', full: 'transitive', family: 'construction' },
                    { short: 'Brazil', full: 'Brazil', family: 'register' },
                    { short: 'informal', full: 'informal', family: 'register' },
                ],
                examples: [
                    {
                        target: 'Aqui tem tudo o que precisamos.',
                        english: 'Everything we need is here.',
                        sourceLabel: 'Wiktionary example',
                    },
                ],
            },
            {
                pos: 'VERB',
                translation: 'See ter de, ter que.',
                references: ['ter de', 'ter que'],
                context: null,
                pct: 5,
                metadata: [
                    { short: 'aux.', full: 'auxiliary', family: 'construction' },
                    { short: '+ de/que + infinitive', full: 'with de or que + infinitive', family: 'construction' },
                ],
                examples: [
                    {
                        target: 'Não, ele tem de fazer isto.',
                        english: "No, he's got to do this.",
                        sourceLabel: 'Speech example',
                    },
                ],
            },
        ],
    },
    // The visitor-facing Speech card (About and the walkthrough). Chosen so a
    // glance shows what disambiguation is for: two meanings nobody could
    // confuse, and every example visibly right. Read out of the live v15 deck
    // (es-speech-v15-10000x10): rank 1,057, 84 per million, 26 of 30 assigned
    // sentences are the bank and 4 the bench. `que` stays for the tutorial,
    // but its WSD is too tangled to show off at a glance.
    bancoSpeech: {
        mode: 'speech', word: 'banco', pos: 'NOUN', lemma: 'banco', rank: 1057, vocabSize: 10000, corpusCount: 84,
        defaultMeaningIndex: 1,
        meanings: [
            {
                pos: 'NOUN', translation: 'bench', context: 'seat', pct: 13,
                examples: [{ target: 'Él y su amigo se sentaron en el banco.', english: 'He and his friend sat on the bench.', sourceLabel: 'Tatoeba example' }],
            },
            {
                pos: 'NOUN', translation: 'bank', context: 'finance', pct: 87,
                examples: [
                    { target: '¿En serio quieres poner tu dinero en ese banco?', english: 'Do you really want to put your money in that bank?', sourceLabel: 'Tatoeba example' },
                    { target: 'Es decir, un banco como este debería ser más seguro.', english: 'That is, a bank like this should be safer.', sourceLabel: 'Speech example' },
                    { target: 'Mi hermana trabaja en un banco como secretaria.', english: 'My sister works in a bank as a secretary.', sourceLabel: 'Tatoeba example' },
                ],
            },
        ],
    },
    // Portuguese learner tutorial: three distinct uses of provar and fourteen
    // curated examples from pt-speech-v23-10000x30-slim, unchanged. The live
    // release assigns 22 examples to prove, four to taste and two to try on;
    // shares are relative to those three displayed senses. The general "try
    // out" sense is omitted because its examples overlap the clothing sense.
    // IMDb titles are resolved from the shipped source_titles.json mapping.
    ptProvarSpeech: {
        "mode": "speech",
        "word": "provar",
        "pos": "VERB",
        "lemma": "provar",
        "rank": 1165,
        "vocabSize": 10000,
        "corpusCount": 74.556751,
        "defaultMeaningIndex": 0,
        "meanings": [
            {
                "pos": "VERB",
                "translation": "to prove",
                "context": "show that something is true",
                "pct": 78.57142857142857,
                "metadata": [
                    {
                        "short": "tr.",
                        "full": "transitive: used with an object",
                        "family": "construction"
                    }
                ],
                "examples": [
                    {
                        "target": "Tens de me ajudar a provar que estou inocente.",
                        "english": "I need you to help me prove that I'm innocent.",
                        "sourceLabel": "IMDb",
                        "titleId": "5273862",
                        "sourceTitle": "Power · S3 E7"
                    },
                    {
                        "target": "Você não precisa provar nada para mim.",
                        "english": "You don't need to prove anything to me.",
                        "sourceLabel": "Tatoeba example"
                    },
                    {
                        "target": "Eu posso provar que tenho razão.",
                        "english": "I can prove that I am right.",
                        "sourceLabel": "Tatoeba example"
                    },
                    {
                        "target": "Pode provar que estou errado?",
                        "english": "Can you prove I'm wrong?",
                        "sourceLabel": "Tatoeba example"
                    },
                    {
                        "target": "Eu posso provar isso.",
                        "english": "I can prove it.",
                        "sourceLabel": "Tatoeba example"
                    },
                    {
                        "target": "Você pode provar isso?",
                        "english": "Can you prove that?",
                        "sourceLabel": "Tatoeba example"
                    },
                    {
                        "target": "Não o vou deixar em paz até o conseguir provar.",
                        "english": "I'm not letting you alone until I prove it.",
                        "sourceLabel": "IMDb",
                        "titleId": "4172404",
                        "sourceTitle": "The Mentalist · S7 E6"
                    },
                    {
                        "target": "Sempre tive de provar que sou bom.",
                        "english": "I've always had to prove I'm good enough.",
                        "sourceLabel": "IMDb",
                        "titleId": "5521456",
                        "sourceTitle": "Avengers Assemble · S3 E2"
                    }
                ]
            },
            {
                "pos": "VERB",
                "translation": "to taste; to try",
                "context": "food",
                "pct": 14.285714285714285,
                "metadata": [
                    {
                        "short": "tr.",
                        "full": "transitive: used with an object",
                        "family": "construction"
                    }
                ],
                "examples": [
                    {
                        "target": "Que tal provar um pouco de sushi?",
                        "english": "How about trying some sushi?",
                        "sourceLabel": "Tatoeba example"
                    },
                    {
                        "target": "Parece delicioso. Acho que vou provar algum.",
                        "english": "Looks delicious. Think I'll try some.",
                        "sourceLabel": "Tatoeba example"
                    },
                    {
                        "target": "Isso parece delicioso. Gostaria de provar.",
                        "english": "That looks delicious. I'd like to try it.",
                        "sourceLabel": "Tatoeba example"
                    },
                    {
                        "target": "Quando você provar, vai achar toda esta comida excelente e muito nutritiva.",
                        "english": "When you taste it, you will find all this food excellent and very nourishing.",
                        "sourceLabel": "Tatoeba example"
                    }
                ]
            },
            {
                "pos": "VERB",
                "translation": "to try on",
                "context": "clothes",
                "pct": 7.142857142857142,
                "metadata": [
                    {
                        "short": "tr.",
                        "full": "transitive: used with an object",
                        "family": "construction"
                    }
                ],
                "examples": [
                    {
                        "target": "Eu gostaria de provar este vestido.",
                        "english": "I'd like to try on this dress.",
                        "sourceLabel": "Tatoeba example"
                    },
                    {
                        "target": "Gostaria de provar um tamanho menor que este.",
                        "english": "I'd like to try on one size smaller than this.",
                        "sourceLabel": "Tatoeba example"
                    }
                ]
            }
        ]
    },
    queSpeech: {
        mode: 'speech', word: 'que', pos: 'CCONJ', lemma: 'que', rank: 1, vocabSize: 6000, corpusCount: 33170,
        meanings: [
            {
                pos: 'CCONJ', translation: 'that', context: 'introduces a subordinate clause', pct: 34,
                metadata: [{ short: 'subordinate clause', full: 'used to introduce a subordinate clause', family: 'functional' }],
                examples: [{ target: 'Es sólo que no es sutil.', english: "It’s just that it isn’t subtle.", sourceLabel: 'Speech example' }],
            },
            {
                pos: 'CCONJ', translation: 'than; to', context: 'used in comparisons', pct: 33,
                metadata: [{ short: 'comparison', full: 'used in comparisons', family: 'construction' }],
                examples: [{ target: 'Prefiero las tiendas pequeñas que los grandes supermercados.', english: 'I prefer small stores to big supermarkets.', sourceLabel: 'SpanishDict example' }],
            },
            {
                pos: 'PRON', translation: 'that; which', context: 'defines the object', pct: 33,
                examples: [{ target: 'Ese es el teléfono que yo quiero.', english: 'That is the phone that I want.', sourceLabel: 'SpanishDict example' }],
            },
        ],
    },
    jeSpeech: {
        mode: 'speech', word: 'je', pos: 'VERB', lemma: 'být', rank: 3, vocabSize: 4000, corpusCount: 12890,
        meanings: [
            {
                pos: 'VERB', translation: 'he/she is (exists)', pct: 40,
                metadata: [{ short: 'impf.', full: 'imperfective', family: 'grammar' }],
                examples: [{ target: 'A co myslíš, že to je?', english: 'And what do you think it is?', sourceLabel: 'Speech example' }],
            },
            {
                pos: 'VERB', translation: 'he/she is', pct: 60,
                metadata: [{ short: '3rd sg. present', full: 'third-person singular present', family: 'grammar' }],
                examples: [{ target: 'Ten kabát je vlhký.', english: 'The coat is wet.', sourceLabel: 'Wiktionary example' }],
            },
        ],
    },
    deSpeech: {
        mode: 'speech', word: 'de', pos: 'PREP', lemma: 'de', rank: 1, vocabSize: 6000, corpusCount: 26810,
        meanings: [
            {
                pos: 'PREP', translation: 'of', context: 'possession, association or relationship',
                metadata: [{ short: 'relationship', full: 'indicates possession, association or relationship', family: 'functional' }],
                examples: [{ target: 'Paris est la capitale de la France.', english: 'Paris is the capital of France.', sourceLabel: 'Wiktionary example' }],
            },
            {
                pos: 'PREP', translation: 'from; of', context: 'after a negation',
                metadata: [{ short: 'after negation', full: 'used with an object in a negated sentence', family: 'construction' }],
                examples: [{ target: 'Elle n’a pas de mère.', english: 'She does not have a mother.', sourceLabel: 'Wiktionary example' }],
            },
        ],
    },
};

// ---------------------------------------------------------------------------
// Card rendering — mirrors updateCard() in flashcards.js.
// ---------------------------------------------------------------------------

const POS_CLASS = {
    VERB: 'pos-verb', NOUN: 'pos-noun', ADJ: 'pos-adj', ADV: 'pos-adv',
    PREP: 'pos-prep', ADP: 'pos-prep', CONJ: 'pos-conj', CCONJ: 'pos-cconj',
    SCONJ: 'pos-sconj', PRON: 'pos-pron', DET: 'pos-det', INT: 'pos-int',
    INTJ: 'pos-int', NUM: 'pos-num', MWE: 'pos-mwe',
};

// Every colour on the back of a card comes from one custom property. The live
// card sets it per part of speech (getPosAccentRgb in flashcards.js) and the
// stylesheet reads it for the sense-group tint, the selected row,
// the prominence bars and the underline under the word in the example. The
// replica used those same rules but never defined the variable, so all of it
// resolved to nothing and the card came out grey. These are the live values.
const POS_ACCENT_RGB = {
    'pos-noun': '74, 158, 255',
    'pos-propn': '14, 165, 233',
    'pos-verb': '0, 212, 170',
    'pos-aux': '45, 212, 191',
    'pos-adj': '245, 166, 35',
    'pos-adv': '168, 85, 247',
    'pos-prep': '236, 72, 153',
    'pos-conj': '20, 184, 166',
    'pos-cconj': '34, 197, 94',
    'pos-sconj': '132, 204, 22',
    'pos-pron': '99, 102, 241',
    'pos-det': '244, 63, 94',
    'pos-int': '234, 179, 8',
    'pos-num': '6, 182, 212',
    'pos-mwe': '251, 191, 36',
};

export const posAccentRgb = pos => POS_ACCENT_RGB[posClass(pos)] || '148, 163, 184';

const POS_NAME = {
    VERB: 'verb', NOUN: 'noun', ADJ: 'adjective', ADV: 'adverb',
    PREP: 'preposition', ADP: 'preposition', CONJ: 'conjunction',
    CCONJ: 'conjunction', SCONJ: 'conjunction', PRON: 'pronoun',
    DET: 'determiner', INT: 'interjection', INTJ: 'interjection',
    NUM: 'number', MWE: 'expression',
};

const posClass = (pos) => POS_CLASS[String(pos || '').toUpperCase()] || '';
const posName = (pos) => POS_NAME[String(pos || '').toUpperCase()] || String(pos || '').toLowerCase();

export function esc(s) {
    return String(s ?? '')
        .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;');
}

// Same word-boundary highlight the real card applies to its example sentence:
// unicode property escapes so Spanish letters are handled, case-insensitive so
// a sentence-initial "Fuego" still matches. The sentence is escaped first, so
// data can never inject markup.
export function highlightWord(sentence, word) {
    const escaped = esc(sentence);
    if (!word) return escaped;
    const wordEsc = word.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
    try {
        const re = new RegExp(`(?<![\\p{L}\\p{N}])(${wordEsc})(?![\\p{L}\\p{N}])`, 'giu');
        return escaped.replace(re, '<span class="example-word-highlight">$1</span>');
    } catch (_) {
        return escaped;  // engines without \p{...} support
    }
}

// Verbatim copy of the real card's Spotify mark so the button is visually and
// behaviourally identical — see the `spotifySvg` const in flashcards.js.
const SPOTIFY_SVG = '<svg width="44" height="44" viewBox="0 0 24 24" fill="#1DB954">'
    + '<path d="M12 0C5.4 0 0 5.4 0 12s5.4 12 12 12 12-5.4 12-12S18.66 0 12 0zm5.521 17.34'
    + 'c-.24.359-.66.48-1.021.24-2.82-1.74-6.36-2.101-10.561-1.141-.418.122-.779-.179-.899-.539'
    + '-.12-.421.18-.78.54-.9 4.56-1.021 8.52-.6 11.64 1.32.42.18.479.659.301 1.02zm1.44-3.3'
    + 'c-.301.42-.841.6-1.262.3-3.239-1.98-8.159-2.58-11.939-1.38-.479.12-1.02-.12-1.14-.6'
    + '-.12-.48.12-1.021.6-1.141C9.6 9.9 15 10.561 18.72 12.84c.361.181.54.78.241 1.2zm.12-3.36'
    + 'C15.24 8.4 8.82 8.16 5.16 9.301c-.6.179-1.2-.181-1.38-.721-.18-.601.18-1.2.72-1.381'
    + ' 4.26-1.26 11.28-1.02 15.721 1.621.539.3.719 1.02.419 1.56-.299.421-1.02.599-1.559.3z"/>'
    + '</svg>';

export function renderFront(card) {
    // Like the live card: the deck's size sits small under the rank.
    const rankOf = card.vocabSize ? `of ${card.vocabSize.toLocaleString()}` : '';
    // `below` puts the unit on its own line, as "per million" is on the live card.
    const stat = (kind, label, value, unit = '', below = false) =>
        `<span class="card-stat${kind === 'card-rank-label' ? '' : ' card-stat--end'} ${kind}">`
        + `<span class="card-stat-label">${label}</span>`
        + `<span class="card-stat-line"><strong class="card-stat-value">${value}</strong>`
        + `${unit && !below ? `<span class="card-stat-unit">${unit}</span>` : ''}</span>`
        + `${unit && below ? `<span class="card-stat-unit card-stat-unit--below">${unit}</span>` : ''}</span>`;
    const rankLabel = stat('card-rank-label', 'Vocabulary Rank', card.rank.toLocaleString(), rankOf, true);
    // Same two figures the live card puts here, in the same words. An earlier
    // draft hedged with "Frequency from the Spanish release", which told a
    // visitor nothing: the number is the point, and a count per million is
    // what the real front says.
    const freqLabel = card.mode === 'lyrics'
        ? stat('card-freq-label', 'Song Lines', card.corpusCount.toLocaleString())
        : stat('card-freq-label', 'Frequency', Math.round(card.corpusCount).toLocaleString(), 'per million', true);

    // updateCard() pairs each POS pill with the lemma it governs inside one
    // capsule (.front-lemma-pair), which is how a learner sees that `tem` is
    // a form of `ter`. The replica dropped the lemma and showed a bare pill.
    const lemma = card.lemma || card.word;
    const posUnit = `<span class="front-pos-unit"><span class="card-pos ${posClass(card.pos)}">${posName(card.pos)}</span></span>`;

    return `
        <div class="card-face card-front">
            <div class="card-word">${esc(card.word)}</div>
            <div class="card-pos-list is-lemma-map pos-count-1" style="display: flex;">
                <span class="front-lemma-pair">${posUnit}<span class="front-lemma-name">${esc(lemma)}</span></span>
            </div>
            <div class="card-ranking" style="display: flex; justify-content: space-between; align-items: flex-start; width: 100%; gap: 12px;">${rankLabel}${freqLabel}</div>
            <div class="card-tint" aria-hidden="true"></div>
        </div>`;
}

// Sense rows. The real card emits several row layouts depending on how the
// meanings group; the singleton `.meaning-row-regular` branch below is the one
// these demo cards hit, reproduced with its inline styles intact so it picks
// up the live rules rather than a copy of them.
function replicaSenseSummary(value) {
    let text = String(value || '').trim();
    let previous = '';
    while (text !== previous) {
        previous = text;
        text = text.replace(/\s*\([^()]*\)/gu, ' ');
    }
    return text.replace(/\s{2,}/gu, ' ').replace(/\s+([,;:.])/gu, '$1').trim();
}

function replicaSenseText(meaning, selected) {
    if (Array.isArray(meaning.references) && meaning.references.length) {
        const links = meaning.references.map(target => (
            `<button type="button" class="sense-cross-reference" title="Open ${esc(target)} card" `
            + `aria-label="Open ${esc(target)} card">${esc(target)}</button>`
        )).join('<span class="sense-cross-reference-separator">,</span> ');
        return `<span class="sense-cross-reference-prefix">See</span> ${links}`;
    }
    const value = selected ? meaning.translation : replicaSenseSummary(meaning.translation);
    return esc(value || meaning.translation);
}

function replicaMetadata(meaning, selected) {
    if (!selected || !Array.isArray(meaning.metadata) || !meaning.metadata.length) return '';
    const renderItems = (items, isPillTier = true) => items.map(item => {
        const family = esc(item.family);
        if (!isPillTier) {
            return `<span class="sense-metadata-detail" data-family="${family}" title="${esc(`${item.family}: ${item.full}`)}">${esc(item.short)}</span>`;
        }
        const isCompanion = item.family === 'companion' || (item.short && /^used with /i.test(item.short));
        const isSyntax = item.family === 'construction';
        const pillClass = `sense-metadata-detail sense-pill sense-pill--${family}${isSyntax ? ' sense-pill--syntax' : ''}${isCompanion ? ' sense-pill--companion sense-pill--privileged' : ''}`;
        const titleAttr = isCompanion
            ? `Used with &quot;${esc(item.value || item.full || item.short)}&quot;`
            : esc(`${item.family}: ${item.full}`);
        const label = isCompanion
            ? `<span class="sense-pill-label"><span class="sense-pill-prefix">used with</span> <span class="sense-pill-token">${esc(item.value || String(item.short || '').replace(/^used with /i, '').replace(/^\+\s*/, ''))}</span></span>`
            : `<span class="sense-pill-label">${esc(item.short)}</span>`;
        return `<span class="${pillClass}" data-family="${family}" title="${titleAttr}">${label}</span>`;
    }).join('');
    const softRegister = new Set(['broadly', 'especially', 'figuratively', 'literally', 'metonymically', 'mildly', 'often', 'possibly', 'sometimes', 'specifically', 'standard', 'usually']);
    const isSupporting = item => item.family === 'functional'
        || (item.family === 'register' && softRegister.has(item.short.toLocaleLowerCase('en')));
    const primary = meaning.metadata.filter(item => item.family !== 'grammar' && item.short !== 'tr.' && !isSupporting(item));
    const grammar = meaning.metadata.filter(item => item.family === 'grammar');
    const primaryHTML = primary.length
        ? `<span class="sense-metadata-tier sense-metadata-tier--primary">${renderItems(primary, true)}</span>` : '';
    const grammarHTML = grammar.length
        ? `<span class="sense-metadata-tier sense-metadata-tier--grammar">${renderItems(grammar, false)}</span>` : '';
    if (!primaryHTML && !grammarHTML) return '';
    return `<span class="sense-metadata-list" aria-label="Sense information">${primaryHTML}${grammarHTML}</span>`;
}

function replicaSenseNote(meaning, selected) {
    if (!selected) return '';
    const context = meaning.context ? `<section class="sense-note-section sense-note-section--usage"><h3>Usage</h3><p>${esc(meaning.context)}</p></section>` : '';
    const metadata = (meaning.metadata || []).map(item => `<p>${esc(item.full || item.short)}</p>`).join('');
    if (!context && !metadata) return '';
    return `<button type="button" class="sense-note-trigger" aria-haspopup="dialog" aria-label="Information about this meaning" title="Information about this meaning"><span aria-hidden="true">i</span></button><template class="sense-note-template"><div class="sense-note-copy" data-sense-note-title="${esc(meaning.translation)}">${context}${metadata ? `<section class="sense-note-section sense-note-section--grammar"><h3>Grammar</h3>${metadata}</section>` : ''}</div></template>`;
}

// Share → the live card's three-bar meter. Exported so About's animated demo
// cards use the same thresholds as the walkthrough rather than a third copy.
export function replicaProminence(pct) {
    if (!(Number(pct) < 100)) return null;
    if (pct <= 0) return { label: 'Rare', key: 'rare' };
    if (pct >= 60) return { label: 'Dominant', key: 'dominant' };
    if (pct >= 20) return { label: 'Common', key: 'common' };
    return { label: 'Uncommon', key: 'uncommon' };
}

function renderMeaningRows(card, selectedIdx) {
    // Sort the display without changing the indices used by sense selection.
    const ordered = card.meanings.map((meaning, index) => ({ meaning, index }))
        .sort((a, b) => (Number(b.meaning.pct) || 0) - (Number(a.meaning.pct) || 0));
    const rows = ordered.map(({ meaning: m, index: idx }) => {
        const isSelected = idx === selectedIdx;
        const bg = 'rgba(var(--sense-match-rgb), 0.10)';
        const textColor = 'var(--text-primary)';
        const ctx = m.context
            ? `<span class="meaning-row-sub sense-cue-area" style="text-align: center; width: 100%;"><span class="meaning-context">${esc(m.context)}</span></span>`
            : '';
        const prominence = replicaProminence(m.pct);
        const pct = prominence
            ? (typeof window.prominenceBadgeHTML === 'function'
                ? window.prominenceBadgeHTML(prominence, 'position: absolute; right: 8px; top: 50%; transform: translateY(-50%);')
                : `<button type="button" class="replica-pct sense-prominence-badge prominence-${esc(prominence.key)}" style="position: absolute; right: 8px; top: 50%; transform: translateY(-50%);">${esc(prominence.label)}</button>`)
            : '';
        return `
            <div class="meaning-row meaning-row-regular${isSelected ? ' selected is-current-sense' : ''}" data-meaning-index="${idx}" style="position: relative; display: grid; grid-template-columns: 1fr; align-items: center; padding: 1px 2px; margin-bottom: 4px; background: ${bg}; border-radius: 8px; cursor: pointer; min-height: 44px;">
                ${replicaSenseNote(m, isSelected)}
                <div class="meaning-row-body" style="display: flex; flex-direction: column; align-items: stretch; justify-content: center; min-width: 0; padding: 0 ${prominence ? '32px' : '8px'} 0 8px;">
                    <span class="meaning-row-translation row-adaptive-text" style="font-weight: ${isSelected ? 700 : 500}; color: ${textColor}; text-align: center; width: 100%;">${replicaSenseText(m, isSelected)}</span>
                    ${ctx}
                    ${replicaMetadata(m, isSelected)}
                </div>
                ${pct}
            </div>`;
    }).join('');
    const summaryLimit = Math.min(2, card.meanings.length);
    const summaries = ordered.slice(0, summaryLimit).map(({ meaning }) => (
        `<span class="pos-summary-sense">${esc(replicaSenseSummary(meaning.translation))}</span>`
    )).join('');
    const hiddenCount = card.meanings.length - summaryLimit;
    const more = hiddenCount > 0
        ? `<span class="pos-pill-more" aria-label="${hiddenCount} more senses">+${hiddenCount}</span>`
        : '';
    return `
        <section class="meaning-pos-section pos-collapsible is-open" data-pos="${esc(card.pos)}"
                 style="--sense-match-rgb: ${posAccentRgb(card.pos)};">
            <button type="button" class="pos-section-head" aria-expanded="true" aria-label="${esc(`${posName(card.pos)}: ${ordered.map(({ meaning }) => replicaSenseSummary(meaning.translation)).join('; ')}`)}">
                <span class="pos-section-label">${esc(posName(card.pos))}</span>
                <span class="pos-pill-lemma">${esc(card.lemma || card.word)}</span>
                <span class="pos-section-summary">${summaries}${more}</span>
                <span class="pos-section-chevron">▾</span>
            </button>
            <div class="meaning-pos-rows">${rows}</div>
        </section>`;
}

// Credit strip beneath the lyric: song + vocalists on the left, autoplay /
// Spotify / example counter on the right. Speech cards have no track, so the
// strip degrades to a right-aligned source label, exactly as on a live card.
function replicaExampleTicks(current, total) {
    if (total < 2) return '';
    const ticks = Array.from({ length: total }, (_, i) =>
        `<span class="example-tick${i === current ? ' is-current' : ''}"></span>`
    ).join('');
    return `<div class="example-ticks" role="img" aria-label="example ${current + 1} of ${total}">${ticks}</div>`;
}

function replicaSourceChip(sourceLabel, titleId = '', sourceTitle = '') {
    const raw = String(sourceLabel || '');
    const lower = raw.toLowerCase();
    let domain = '';
    let label = raw.replace(/\s+example$/i, '') || raw;
    if (lower.includes('spanishdict')) domain = 'spanishdict.com';
    else if (lower.includes('wiktionary')) domain = 'wiktionary.org';
    else if (lower.includes('tatoeba')) domain = 'tatoeba.org';
    else if (lower.includes('imdb')) domain = 'imdb.com';
    else if (lower.includes('opensubtitles')) domain = 'opensubtitles.org';
    if (titleId) label = `IMDb · ${sourceTitle || `tt${String(titleId).padStart(7, '0')}`} · OpenSubtitles`;
    if (!domain) {
        return `<span class="example-song-credit" style="margin-right:auto;">${esc(raw)}</span>`;
    }
    const icon = { 'tatoeba.org': 'icons/tatoeba.svg', 'wiktionary.org': 'icons/wikipedia-w.svg' }[domain]
        || `https://www.google.com/s2/favicons?domain=${encodeURIComponent(domain)}&sz=64`;
    return `<span class="example-song-credit" style="margin-right:auto;"><span class="example-source-chip example-source-chip--${sourceTitle ? 'named' : 'icon'} dictionary-provenance-badge" title="${esc(label)}" aria-label="${esc(label)}"><img class="example-source-favicon dict-provenance-icon${domain === 'wiktionary.org' ? ' example-source-favicon--wikipedia' : ''}" src="${icon}" width="34" height="34" alt="" aria-hidden="true">${sourceTitle ? `<span class="example-source-text">${esc(sourceTitle)}</span>` : ''}</span></span>`;
}

function renderCredit(card, meaning, example, exampleIdx) {
    if (example.trackId) {
        const btn = `<button type="button" class="spotify-btn link-btn"
                data-track-id="${esc(example.trackId)}" data-position-ms="${example.positionMs}"
                title="Play in Spotify" style="cursor:pointer; margin:0; position:relative; z-index:999;"
                data-replica-spotify="1">${SPOTIFY_SVG}</button>`;
        const vocalists = example.vocalists
            ? `<span class="example-vocalist-credit"> · ${esc(example.vocalists)}</span>`
            : '';
        return `
            <div class="example-credit-row is-lyric">
                <span class="example-credit-start">
                    <span class="example-song-credit">— ${esc(example.song)}${vocalists}</span>
                </span>
                <span class="example-credit-end">${replicaExampleTicks(exampleIdx, meaning.examples.length)}${btn}</span>
            </div>`;
    }

    const credit = example.sourceLabel
        ? replicaSourceChip(example.sourceLabel, example.titleId, example.sourceTitle)
        : '';
    const ticks = replicaExampleTicks(exampleIdx, meaning.examples.length);
    if (!credit && !ticks) return '';
    return `
        <div class="example-credit-row">
            <span class="example-credit-start">${credit}</span>
            <span class="example-credit-end">${ticks}</span>
        </div>`;
}

export function renderBack(card, selectedIdx, exampleIdx) {
    const meaning = card.meanings[selectedIdx];
    const example = meaning.examples[exampleIdx % meaning.examples.length];
    const cursor = meaning.examples.length > 1 ? 'cursor: pointer;' : '';

    return `
        <div class="card-face card-back">
            <div class="card-details">
                <div class="back-header">
                    <div class="flip-back-area">
                        <div class="back-headword-row">
                            <span class="back-headword" style="font-size: 42px; font-weight: bold; line-height: 1.1;">${esc(card.word)}</span>
                        </div>
                    </div>
                </div>
                <div class="meanings-scroll">${renderMeaningRows(card, selectedIdx)}</div>
                <div class="sentence example-is-matched" style="text-align: center; ${cursor} --sense-match-rgb: ${posAccentRgb(card.pos)}; border-color: transparent;" data-replica-cycle="${meaning.examples.length > 1 ? '1' : '0'}">
                    <div class="breakdown-trigger" style="margin-bottom: 8px;">${highlightWord(example.target, card.word)}</div>
                    <div class="translation">${esc(example.english)}</div>
                    ${renderCredit(card, meaning, example, exampleIdx % meaning.examples.length)}
                </div>
            </div>
            <div class="card-tint" aria-hidden="true"></div>
        </div>`;
}

// Handlers for everything inside a back face. Call again after every back-face
// rebuild, since those nodes are replaced wholesale. What a sense tap or an
// example cycle *means* belongs to the caller — the replica only reports it.
export function wireReplicaBack(root, { onSelectMeaning, onCycleExample, onLayoutChange } = {}) {
    root.querySelectorAll('.pos-section-head').forEach(head => {
        // One already-open group. Keep taps on its heading from being mistaken
        // for a request to flip the whole card.
        head.addEventListener('click', e => {
            e.stopPropagation();
            const section = head.closest('.meaning-pos-section');
            const open = section.classList.toggle('is-open');
            head.setAttribute('aria-expanded', String(open));
            onLayoutChange?.();
        });
    });

    // Sense selection — the caller resets to that sense's first example, the
    // same as selectMeaning() does on a live card.
    root.querySelectorAll('.meaning-row').forEach(row => {
        row.addEventListener('click', e => {
            if (e.target.closest('.sense-note-trigger, .sense-cross-reference')) return;
            e.stopPropagation();
            const idx = Number(row.dataset.meaningIndex);
            if (!Number.isNaN(idx)) onSelectMeaning?.(idx, row);
        });
    });

    root.querySelectorAll('.sense-note-trigger').forEach(control => {
        control.addEventListener('click', e => {
            if (typeof window.openSenseNote === 'function') window.openSenseNote(e, control);
            else e.stopPropagation();
        });
    });

    // The real card opens the referenced vocabulary card. The replica has no
    // vocabulary loaded, so its copy of the control is intentionally inert.
    root.querySelectorAll('.sense-cross-reference').forEach(reference => {
        reference.addEventListener('click', e => {
            e.preventDefault();
            e.stopPropagation();
        });
    });

    // Tap the example to cycle this sense's other examples.
    root.querySelectorAll('.sentence[data-replica-cycle="1"]').forEach(sentence => {
        sentence.addEventListener('click', e => {
            if (e.target.closest('.spotify-btn')) return;
            e.stopPropagation();
            onCycleExample?.(sentence);
        });
    });

    // The live Spotify hand-off. spotifyPlayTrack() is published on window by
    // spotify.js; it resolves the token, runs the PKCE login when there isn't
    // one, and picks the Web Playback SDK or Connect by device — all of which
    // we want unchanged, which is why this defers rather than reimplementing.
    // If the module somehow isn't loaded, fall back to the web player.
    root.querySelectorAll('[data-replica-spotify]').forEach(spotifyBtn => {
        spotifyBtn.addEventListener('click', e => {
            e.stopPropagation();
            e.preventDefault();
            const trackId = spotifyBtn.dataset.trackId;
            const positionMs = Number(spotifyBtn.dataset.positionMs) || 0;
            if (typeof window.spotifyPlayTrack === 'function') {
                spotifyBtn.classList.add('autoplay-loading');
                Promise.resolve(window.spotifyPlayTrack(trackId, positionMs))
                    .catch(() => {})
                    .finally(() => spotifyBtn.classList.remove('autoplay-loading'));
            } else {
                window.open(`https://open.spotify.com/track/${trackId}`, '_blank', 'noopener');
            }
        });
    });
}

// Both faces live in the same fixed-height box, so the box has to be tall
// enough for whichever is taller — in practice always the back. Measuring the
// back's own content beats guessing a height that suits one card: `que` has
// three senses and `tem` has four with grammar pills under the selected one.
// Returns the height so a caller showing two cards can give both the same one.
export function measureReplicaCard(inner) {
    const face = inner?.querySelector('.card-back');
    const details = face?.querySelector('.card-details');
    if (!face || !details) return 0;
    const faceStyle = getComputedStyle(face);
    const pad = parseFloat(faceStyle.paddingTop) + parseFloat(faceStyle.paddingBottom);
    // Sum the three blocks rather than reading the container. .meanings-scroll
    // is the flex child that gives, so inside a fixed-height card it has
    // already been squeezed and the container's own scrollHeight reports the
    // squeezed figure — the overflow it is hiding never shows up.
    const detailStyle = getComputedStyle(details);
    const rowGap = parseFloat(detailStyle.rowGap || detailStyle.gap) || 14;
    const heightOf = sel => {
        const el = face.querySelector(sel);
        return el ? Math.max(el.getBoundingClientRect().height, el.scrollHeight) : 0;
    };
    return Math.ceil(
        pad + rowGap * 2
        + heightOf('.back-header') + heightOf('.meanings-scroll') + heightOf('.sentence'),
    );
}

// A floor so a one-sense card still reads as a card rather than a strip, and a
// ceiling so a dense one cannot outgrow a short window.
export function fitReplicaCard(inner, { floor = 430, ceiling = 0.78, height = null } = {}) {
    if (!inner) return 0;
    const wanted = height ?? measureReplicaCard(inner);
    if (!wanted) return 0;
    const fitted = Math.max(floor, Math.min(wanted, Math.round(window.innerHeight * ceiling)));
    inner.style.setProperty('--replica-card-h', `${fitted}px`);
    return fitted;
}

// One card, one face up. `flipped` picks the face; both faces are always built
// so the real 0.6s flip transition can play when a caller toggles the class.
export function replicaCardHTML(card, { flipped = false, meaningIndex = 0, exampleIndex = 0, extraClass = '' } = {}) {
    return `
        <div class="card-replica${extraClass ? ` ${extraClass}` : ''}">
            <div class="card${flipped ? ' flipped' : ''}" data-rank="${card.rank}">
                ${renderFront(card)}
                ${renderBack(card, meaningIndex, exampleIndex)}
            </div>
        </div>`;
}
