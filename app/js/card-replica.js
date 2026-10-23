import { songCreditHTML } from './song-credit.js?v=b624e66b';
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
        lookup: ['spanishDict', 'reverso'],
        rareUses: [],
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
    // Portuguese learner tutorial: `devia` (rank 332), a form of `dever`, with
    // two short senses. Read out of pt-speech-v24-headway-r2-10000x30-slim:
    // 28 and 2 assigned examples, plus two rare senses; IMDb titles come from
    // the shipped source_titles.json mapping.
    ptDeviaSpeech: {
        mode: 'speech', word: 'devia', pos: 'VERB', lemma: 'dever', rank: 332, vocabSize: 10000, corpusCount: 412,
        defaultMeaningIndex: 0,
        lookup: ['reverso'],
        rareUses: [
            { pos: 'VERB', translation: 'owe', context: 'to be in debt', example: null },
            { pos: 'VERB', translation: 'will likely', context: null,
              example: { target: 'Deve chover.', english: "(It looks like) it's going to rain." } },
        ],
        meanings: [
            {
                pos: 'VERB', translation: 'should', context: null, pct: 93,
                examples: [
                    { target: 'Isto é um filme que toda a gente devia ver.', english: 'This is a film that everybody should see.', sourceLabel: 'Tatoeba example' },
                    { target: 'Você devia ter feito isso na semana passada.', english: "You should've done that last week.", sourceLabel: 'Tatoeba example' },
                    { target: 'Sei que isto parece loucura, mas o que eu devia fazer?', english: "I know this all sounds loco, but what am I supposed to do?", sourceLabel: 'IMDb', titleId: '6385978', sourceTitle: 'Criminal Minds: Beyond Borders · S2 E3' },
                ],
            },
            {
                pos: 'VERB', translation: 'ought', context: null, pct: 7,
                examples: [
                    { target: 'Desculpa, eu sei que não devia estar aqui.', english: "I'm sorry. I know I'm not supposed to be here.", sourceLabel: 'IMDb', titleId: '4168598', sourceTitle: 'Rectify · S3 E3' },
                    { target: 'Você ainda não fez tudo o que devia ter feito.', english: "You haven't yet done everything that you were supposed to do.", sourceLabel: 'Tatoeba example' },
                ],
            },
        ],
    },
    // Spanish learner tutorial: `quiero` (rank 64), a form of `querer`, three
    // short senses. Read out of es-speech-v24-headway-r4-10000x30-slim: 27, 2
    // and 1 assigned examples.
    quieroSpeech: {
        mode: 'speech', word: 'quiero', pos: 'VERB', lemma: 'querer', rank: 64, vocabSize: 10000, corpusCount: 1925,
        defaultMeaningIndex: 0,
        lookup: ['spanishDict', 'reverso'],
        // The word's unused menu senses in the live deck: what Rare uses lists.
        rareUses: [
            { pos: 'NOUN', translation: 'beloved', context: "object of one's affection",
              example: { target: 'Llora por el hombre que fue su querer.', english: 'She cries for the man that was her beloved.' } },
            { pos: 'NOUN', translation: 'love', context: "object of one's affection",
              example: { target: 'El primer querer siempre es el más fuerte.', english: 'First love is always the deepest.' } },
            { pos: 'NOUN', translation: 'love affair', context: 'romance',
              example: { target: 'Cuando salió a relucir su querer, el gobernador renunció.', english: 'When his love affair was exposed, the governor resigned.' } },
            { pos: 'VERB', translation: 'to like', context: 'to feel affection for',
              example: { target: 'El perro te quiere mucho.', english: 'The dog likes you a lot.' } },
            { pos: 'VERB', translation: 'to be fond of', context: 'to feel affection for',
              example: { target: 'Quiero mucho a mis estudiantes.', english: 'I am very fond of my students.' } },
            { pos: 'VERB', translation: 'to try', context: 'to have as intention',
              example: { target: 'Hace años que quiero ir a París, pero es demasiado caro.', english: "I've been trying to go to Paris for years, but it's too expensive." } },
            { pos: 'VERB', translation: 'to love each other', context: 'to feel affection for',
              example: { target: 'Dejaron de quererse.', english: 'They no longer love each other.' } },
            { pos: 'VERB', translation: 'to love oneself', context: 'to appreciate oneself',
              example: { target: 'Necesitas empezar a quererte más.', english: 'You need to learn to love yourself more.' } },
        ],
        meanings: [
            {
                pos: 'VERB', translation: 'to want', context: 'to wish', pct: 90,
                examples: [
                    { target: 'Eso es lo que quiero.', english: "That's what I want.", sourceLabel: 'Tatoeba example' },
                    { target: 'Quiero hablar de una cosa con vuestra madre.', english: 'I want to talk about something with your mother.', sourceLabel: 'Tatoeba example' },
                    { target: 'Y cuando lo haga, quiero estar aquí.', english: 'And when he does, I wanna be here.', sourceLabel: 'IMDb', titleId: '4950318', sourceTitle: 'Daredevil · S2 E10' },
                ],
            },
            {
                pos: 'VERB', translation: 'to love', context: 'to feel affection for', pct: 7,
                examples: [
                    { target: 'Y... aún te quiero.', english: 'And... I love you still.', sourceLabel: 'IMDb', titleId: '5767452', sourceTitle: 'Scandal · S6 E3' },
                    { target: '“Os quiero a todos... pero ya es suficiente”.', english: '“I love you all... but enough’s enough.”', sourceLabel: 'IMDb', titleId: '5218470', sourceTitle: 'Fear the Walking Dead · S2 E13' },
                ],
            },
            {
                pos: 'VERB', translation: 'to mean', context: 'to have as intention', pct: 3,
                examples: [
                    { target: 'Bueno, eso no es lo que quiero decir.', english: "Well, that's not what I mean.", sourceLabel: 'IMDb', titleId: '5350058', sourceTitle: 'Jane the Virgin · S2 E11' },
                ],
            },
        ],
    },
    jeSpeech: {
        mode: 'speech', word: 'je', pos: 'VERB', lemma: 'být', rank: 3, vocabSize: 4000, corpusCount: 12890,
        lookup: ['reverso'],
        rareUses: [
            { pos: 'VERB', translation: 'used to form passive voice forms of verbs with passive participles', context: 'auxiliary',
              example: { target: 'Jsem překvapen.', english: 'I am surprised.' } },
            { pos: 'VERB', translation: 'used to form past tense forms of verbs with past participles', context: 'auxiliary',
              example: { target: 'Jel jsem do Prahy.', english: 'I went to Prague.' } },
            { pos: 'VERB', translation: 'used to form future tense forms of verbs with infinitives', context: 'auxiliary',
              example: { target: 'Budu ti pomáhat.', english: 'I will be helping you.' } },
        ],
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
        lookup: ['reverso'],
        rareUses: [],
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
    INTJ: 'pos-int', NUM: 'pos-num', MWE: 'pos-mwe', PROPN: 'pos-propn',
    AUX: 'pos-aux', NAME: 'pos-propn', ARTICLE: 'pos-det', ABBREVIATION: 'pos-abbr',
    ABBR: 'pos-abbr', CONTRACTION: 'pos-contraction',
};

// Every colour on the back of a card comes from one custom property. The live
// card sets it per part of speech (getPosAccentRgb in flashcards.js) and the
// stylesheet reads it for the sense-group tint, the selected row,
// the prominence bars and the underline under the word in the example. The
// replica used those same rules but never defined the variable, so all of it
// resolved to nothing and the card came out grey. These are the live values.
const POS_ACCENT_RGB = {
    'pos-noun': '74, 158, 255',
    'pos-propn': '34, 211, 238',
    'pos-verb': '0, 212, 170',
    'pos-aux': '0, 212, 170',
    'pos-adj': '245, 166, 35',
    'pos-adv': '192, 90, 245',
    'pos-prep': '236, 72, 153',
    'pos-conj': '34, 197, 94',
    'pos-cconj': '34, 197, 94',
    'pos-sconj': '34, 197, 94',
    'pos-pron': '108, 92, 246',
    'pos-det': '239, 68, 68',
    'pos-int': '250, 224, 50',
    'pos-num': '163, 230, 53',
    'pos-mwe': '245, 166, 35',
    'pos-clitic': '205, 130, 60',
    'pos-part': '217, 70, 239',
    'pos-prefix': '125, 211, 252',
    'pos-suffix': '252, 165, 165',
    'pos-contraction': '251, 120, 50',
    'pos-abbr': '176, 148, 120',
    'pos-other': '148, 163, 184',
};

export const posAccentRgb = pos => POS_ACCENT_RGB[posClass(pos)] || '148, 163, 184';

const POS_NAME = {
    VERB: 'verb', NOUN: 'noun', ADJ: 'adjective', ADV: 'adverb',
    PREP: 'preposition', ADP: 'preposition', CONJ: 'conjunction',
    CCONJ: 'conjunction', SCONJ: 'conjunction', PRON: 'pronoun',
    DET: 'determiner', INT: 'interjection', INTJ: 'interjection',
    NUM: 'number', MWE: 'expression', PROPN: 'proper noun', AUX: 'auxiliary verb',
    NAME: 'proper noun', ARTICLE: 'article', ABBREVIATION: 'abbreviation',
    ABBR: 'abbreviation', CONTRACTION: 'contraction',
};

const posClass = (pos) => POS_CLASS[String(pos || '').toUpperCase()] || '';
export const posLabel = (pos) => { const n = posName(pos); return n.charAt(0).toUpperCase() + n.slice(1); };
export const posName = (pos) => POS_NAME[String(pos || '').toUpperCase()] || String(pos || '').toLowerCase();

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

// The word is not its own dictionary form (quiero → querer).
export function hasDistinctLemma(card) {
    return Boolean(card?.lemma) && String(card.lemma).toLowerCase() !== String(card.word || '').toLowerCase();
}

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
    // As on the live card: a capitalised pill, and the dictionary form only
    // when it differs from the word ("from querer"); banco shows the pill alone.
    const lemma = card.lemma || card.word;
    const accent = posAccentRgb(card.pos);
    const posUnit = `<span class="front-pos-unit" style="--front-pos-rgb: ${accent};"><span class="card-pos ${posClass(card.pos)}">${posLabel(card.pos)}</span></span>`;
    const lemmaPair = hasDistinctLemma(card)
        ? `<span class="front-lemma-pair">${posUnit}<span class="front-lemma-name"><span class="front-lemma-from">from </span>${esc(lemma)}</span></span>`
        : `<span class="front-lemma-pair is-pos-only">${posUnit}</span>`;

    return `
        <div class="card-face card-front">
            <div class="card-word">${esc(card.word)}</div>
            <div class="card-pos-list is-lemma-map pos-count-1" style="display: flex;">
                ${lemmaPair}
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
                : `<span class="replica-pct sense-prominence-badge prominence-${esc(prominence.key)}" style="position: absolute; right: 8px; top: 50%; transform: translateY(-50%);">${esc(prominence.label)}</span>`)
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
    const replicaLemma = card.lemma && card.lemma.toLowerCase() !== String(card.word || '').toLowerCase()
        ? `<span class="pos-lemma-from">from</span><span class="pos-pill-lemma">${esc(card.lemma)}</span>` : '';
    return `
        <section class="meaning-pos-section pos-collapsible is-open" data-pos="${esc(card.pos)}"
                 style="--sense-match-rgb: ${posAccentRgb(card.pos)};">
            <button type="button" class="pos-section-head" aria-expanded="true" aria-label="${esc(`${posLabel(card.pos)}${replicaLemma ? ' from ' + card.lemma : ''}: ${ordered.map(({ meaning }) => replicaSenseSummary(meaning.translation)).join('; ')}`)}">
                <span class="pos-section-label">${esc(posLabel(card.pos))}</span>
                ${replicaLemma}
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
    // As on the live card: the IMDb icon alone, the show named only on hover.
    if (titleId) label = `IMDb · ${sourceTitle || `tt${String(titleId).padStart(7, '0')}`} · OpenSubtitles`;
    if (!domain) {
        return `<span class="example-song-credit" style="margin-right:auto;">${esc(raw)}</span>`;
    }
    const icon = { 'tatoeba.org': 'icons/tatoeba.svg', 'wiktionary.org': 'icons/wikipedia-w.svg' }[domain]
        || `https://www.google.com/s2/favicons?domain=${encodeURIComponent(domain)}&sz=64`;
    return `<span class="example-song-credit" style="margin-right:auto;"><span class="example-source-chip example-source-chip--icon dictionary-provenance-badge" title="${esc(label)}" aria-label="${esc(label)}"><img class="example-source-favicon dict-provenance-icon${domain === 'wiktionary.org' ? ' example-source-favicon--wikipedia' : ''}" src="${icon}" width="34" height="34" alt="" aria-hidden="true"></span></span>`;
}

function renderCredit(card, meaning, example, exampleIdx) {
    if (example.trackId) {
        const btn = `<button type="button" class="spotify-btn link-btn"
                data-track-id="${esc(example.trackId)}" data-position-ms="${example.positionMs}"
                title="Play in Spotify" style="cursor:pointer; margin:0; position:relative; z-index:999;"
                data-replica-spotify="1">${SPOTIFY_SVG}</button>`;
        return `
            <div class="example-credit-row is-lyric">
                <span class="example-credit-start">
                    ${songCreditHTML(example.song, example.vocalists || card.artist || '')}
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
        <div class="example-credit-row has-centred-ticks">
            <span class="example-credit-start">${credit}</span>
            <span class="example-credit-end">${ticks}</span>
        </div>`;
}

// A card with no `rareUses` list keeps the tile (the walkthrough's cards
// predate the list); an explicit empty list means the word has none, and the
// live card then draws no tile at all.
// Verb cards carry Conjugate, as in the live card (flashcards.js), which
// shows it whenever the language has a conjugation table. Every replica verb
// is in such a language.
export function hasConjugateTile(card) {
    return String(card?.pos || '').toUpperCase() === 'VERB';
}

function hasRareUses(card) {
    return !Array.isArray(card.rareUses) || card.rareUses.length > 0;
}

// The sites the live card's Dictionary sheet offers, as it builds them
// (flashcards.js: every reference link but WordReference and conjugation).
const LOOKUP_SITES = {
    spanishDict: { label: 'SpanishDict', domain: 'spanishdict.com' },
    reverso: { label: 'Reverso Context', domain: 'reverso.net' },
};

function lookupSheetHTML(card) {
    const sites = (card.lookup || []).map(key => LOOKUP_SITES[key]).filter(Boolean);
    if (!sites.length) return '';
    const leaveIcon = '<svg class="outbound-leave-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"></path><polyline points="15 3 21 3 21 9"></polyline><line x1="10" y1="14" x2="21" y2="3"></line></svg>';
    return `<div class="lookup-sheet" hidden>${sites.map(site => `
        <span role="button" tabindex="0" class="lookup-sheet-icon" title="${esc(site.label)}" aria-label="${esc(site.label)}" aria-expanded="false" data-replica-lookup>
            <img src="https://www.google.com/s2/favicons?domain=${site.domain}&sz=64" width="40" height="40" alt="${esc(site.label)}" style="border-radius:4px">
            <button type="button" class="outbound-leave-btn outbound-leave-btn--label" hidden aria-label="Visit ${esc(site.label)}"><span class="outbound-visit-label">Visit ${esc(site.label)}</span>${leaveIcon}</button>
        </span>`).join('')}</div>`;
}

export function renderBack(card, selectedIdx, exampleIdx) {
    const meaning = card.meanings[selectedIdx];
    const example = meaning.examples[exampleIdx % meaning.examples.length];
    const cursor = meaning.examples.length > 1 ? 'cursor: pointer;' : '';

    return `
        <div class="card-face card-back has-action-tray">
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
                <div class="links-section" id="replicaLinksSection">
                    ${hasRareUses(card) ? `<button type="button" class="ref-tile ref-rare-uses-btn" aria-label="Rare uses" title="Rare uses">
                        <div class="ref-tile-icon-wrap">
                            <span class="ref-tile-icon ref-tile-meter" aria-hidden="true"><i class="is-on"></i><i></i><i></i></span>
                            <span class="ref-tile-count-badge">${Array.isArray(card.rareUses) ? card.rareUses.length : 2}</span>
                        </div>
                        <span class="ref-tile-label">Rare uses</span>
                    </button>` : ''}
                    <button type="button" class="ref-tile knowledge-overview-trigger" aria-label="Pin meaning" aria-pressed="false">
                        <div class="ref-tile-icon-wrap">
                            <svg class="ref-tile-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M12 17v5"></path><path d="M9 10.76a2 2 0 0 1-1.11 1.79l-1.78.9A2 2 0 0 0 5 15.24V16a1 1 0 0 0 1 1h12a1 1 0 0 0 1-1v-.76a2 2 0 0 0-1.11-1.79l-1.78-.9A2 2 0 0 1 15 10.76V7a1 1 0 0 1 1-1 1 1 0 0 0 1-1V4a1 1 0 0 0-1-1H8a1 1 0 0 0-1 1v1a1 1 0 0 0 1 1 1 1 0 0 1 1 1z"></path></svg>
                        </div>
                        <span class="ref-tile-label">Pin meaning</span>
                    </button>
                    ${hasConjugateTile(card) ? `<button type="button" class="ref-tile ref-conj-btn" aria-label="Conjugate">
                        <span class="ref-tile-icon ref-tile-endings" aria-hidden="true"><span>-ar</span><span>-er</span><span>-ir</span></span>
                        <span class="ref-tile-label">Conjugate</span>
                    </button>` : ''}
                    <div class="ref-lookup-wrap"><button type="button" class="ref-tile ref-lookup-btn" aria-label="Dictionary" title="Dictionary">
                        <svg class="ref-tile-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
                <circle cx="12" cy="12" r="9"></circle>
                <path d="M3 12h18"></path>
                <path d="M12 3a14 14 0 0 1 0 18M12 3a14 14 0 0 0 0 18"></path>
            </svg>
                        <span class="ref-tile-label">Dictionary</span>
                    </button>
                    ${lookupSheetHTML(card)}</div>
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
            if (e.target.closest('.sense-note-trigger, .sense-cross-reference, .sense-pin-btn')) return;
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
    // Sum the study blocks and action tray rather than reading the container. .meanings-scroll
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
        + (parseFloat(detailStyle.paddingTop) || 0) + (parseFloat(detailStyle.paddingBottom) || 0)
        + heightOf('.links-section') + (parseFloat(faceStyle.rowGap) || 0)
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
    const accent = posAccentRgb(card.pos);
    const glow = `radial-gradient(circle at 50% 20%, rgba(${accent}, 0.18), transparent 70%)`;
    return `
        <div class="card-replica${extraClass ? ` ${extraClass}` : ''}">
            <div class="card${flipped ? ' flipped' : ''}" data-rank="${card.rank}" style="--card-pos-rgb: ${accent}; --card-ambient-glow: ${glow};">
                ${renderFront(card)}
                ${renderBack(card, meaningIndex, exampleIndex)}
            </div>
        </div>`;
}
