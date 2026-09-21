// The replica card: real demo entries and the markup that draws them.
//
// Two features show a flashcard without the app having loaded a deck, and they
// are for different people:
//
//   * tutorial.js     — for LEARNERS. Guided, one element at a time, starts
//                       from the setup screen. Opened by "?" and first run.
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
// stylesheet reads it for the sense-group tint, the selected row, the check,
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
    // The live card prints the rank against the size of the deck it came from,
    // which is what makes "rank 1" mean something.
    const denominator = card.vocabSize ? ` / ${card.vocabSize.toLocaleString()}` : '';
    const rankLabel = `<span class="card-rank-label">Vocabulary rank: `
        + `<strong class="card-stat-value">${card.rank.toLocaleString()}</strong>${denominator}</span>`;
    const count = `<strong class="card-stat-value">${card.corpusCount.toLocaleString()}</strong>`;
    // Same two figures the live card puts here, in the same words. An earlier
    // draft hedged with "Frequency from the Spanish release", which told a
    // visitor nothing: the number is the point, and a count per million is
    // what the real front says.
    const freqLabel = card.mode === 'lyrics'
        ? `<span class="card-freq-label">Lyric lines: ${count}</span>`
        : `<span class="card-freq-label">Frequency: ${count}/million</span>`;

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
            <div class="card-ranking" style="display: flex; justify-content: space-between; align-items: baseline; width: 100%; gap: 12px;">${rankLabel}${freqLabel}</div>
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
    const primary = meaning.metadata.filter(item => item.family !== 'grammar' && !isSupporting(item));
    const grammar = meaning.metadata.filter(item => item.family === 'grammar');
    const supporting = meaning.metadata.filter(isSupporting);
    const primaryHTML = primary.length
        ? `<span class="sense-metadata-tier sense-metadata-tier--primary">${renderItems(primary, true)}</span>` : '';
    const grammarHTML = grammar.length
        ? `<span class="sense-metadata-tier sense-metadata-tier--grammar">${renderItems(grammar, false)}</span>` : '';
    const supportingHTML = supporting.length
        ? `<span class="sense-metadata-tier sense-metadata-tier--details${supporting.length === 1 ? ' is-single' : ''}"${supporting.length > 1 ? ' hidden' : ''}>${renderItems(supporting, false)}</span>` : '';
    const more = supporting.length > 1
        ? `<button type="button" class="sense-metadata-more" aria-expanded="false" data-count="${supporting.length}" aria-label="Show ${supporting.length} supporting details"><span class="sense-metadata-more-label">More details</span><span class="sense-metadata-more-count">${supporting.length}</span></button>` : '';
    return `<span class="sense-metadata-list" aria-label="Sense details">${primaryHTML}${grammarHTML}${more}${supportingHTML}</span>`;
}

// Share → the live card's four-bar meter. Exported so About's animated demo
// cards use the same thresholds as the walkthrough rather than a third copy.
export function replicaProminence(pct) {
    if (!(Number(pct) < 100)) return null;
    if (pct <= 0) return { label: 'Rare', key: 'rare' };
    if (pct >= 60) return { label: 'Dominant', key: 'dominant' };
    if (pct >= 20) return { label: 'Common', key: 'common' };
    return { label: 'Uncommon', key: 'uncommon' };
}

function renderMeaningRows(card, selectedIdx) {
    const rows = card.meanings.map((m, idx) => {
        const isSelected = idx === selectedIdx;
        const bg = 'rgba(var(--sense-match-rgb), 0.10)';
        const textColor = 'var(--text-primary)';
        const ctx = m.context
            ? ` <span class="meaning-context">· ${esc(m.context)}</span>`
            : '';
        const prominence = replicaProminence(m.pct);
        const pct = prominence
            ? (typeof window.prominenceBadgeHTML === 'function'
                ? window.prominenceBadgeHTML(prominence, 'position: absolute; right: 8px; top: 50%; transform: translateY(-50%);')
                : `<button type="button" class="replica-pct sense-prominence-badge prominence-${esc(prominence.key)}" style="position: absolute; right: 8px; top: 50%; transform: translateY(-50%);">${esc(prominence.label)}</button>`)
            : '';
        const check = isSelected
            ? '<svg class="meaning-row-check" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="rgb(var(--sense-match-rgb))" stroke-width="3" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><polyline points="20 6 9 17 4 12"></polyline></svg>'
            : '';
        return `
            <div class="meaning-row meaning-row-regular${isSelected ? ' selected is-current-sense' : ''}" data-meaning-index="${idx}" style="position: relative; display: grid; grid-template-columns: 1fr; align-items: center; padding: 1px 2px; margin-bottom: 4px; background: ${bg}; border-radius: 8px; cursor: pointer; min-height: 39px;">
                ${check}
                <div class="meaning-row-body" style="display: flex; flex-direction: column; align-items: stretch; justify-content: center; min-width: 0; padding: 0 ${prominence ? '32px' : '8px'} 0 8px;">
                    <span class="meaning-row-translation row-adaptive-text" style="font-weight: ${isSelected ? 700 : 500}; color: ${textColor}; text-align: center; width: 100%;">${replicaSenseText(m, isSelected)}${ctx}</span>
                    ${replicaMetadata(m, isSelected)}
                </div>
                ${pct}
            </div>`;
    }).join('');
    const summaryLimit = Math.min(2, card.meanings.length);
    const summaries = card.meanings.slice(0, summaryLimit).map(meaning => (
        `<span class="pos-summary-sense">${esc(replicaSenseSummary(meaning.translation))}</span>`
    )).join('');
    const hiddenCount = card.meanings.length - summaryLimit;
    const more = hiddenCount > 0
        ? `<span class="pos-pill-more" aria-label="${hiddenCount} more senses">+${hiddenCount}</span>`
        : '';
    return `
        <section class="meaning-pos-section pos-collapsible is-open" data-pos="${esc(card.pos)}"
                 style="--sense-match-rgb: ${posAccentRgb(card.pos)};">
            <button type="button" class="pos-section-head" aria-label="${esc(`${posName(card.pos)}: ${card.meanings.map(m => replicaSenseSummary(m.translation)).join('; ')}`)}">
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

function replicaSourceChip(sourceLabel) {
    const raw = String(sourceLabel || '');
    const lower = raw.toLowerCase();
    let domain = '';
    let label = raw.replace(/\s+example$/i, '') || raw;
    if (lower.includes('spanishdict')) domain = 'spanishdict.com';
    else if (lower.includes('wiktionary')) domain = 'wiktionary.org';
    else if (lower.includes('tatoeba')) domain = 'tatoeba.org';
    else if (lower.includes('imdb') || lower.includes('opensubtitles')) domain = 'imdb.com';
    if (!domain) {
        return `<span class="example-song-credit" style="margin-right:auto;">${esc(raw)}</span>`;
    }
    return `<span class="example-song-credit" style="margin-right:auto;"><span class="example-source-chip example-source-chip--icon dictionary-provenance-badge" title="${esc(label)}" aria-label="${esc(label)}"><img class="example-source-favicon dict-provenance-icon" src="https://www.google.com/s2/favicons?domain=${encodeURIComponent(domain)}&sz=64" width="28" height="28" alt="" aria-hidden="true"></span></span>`;
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
        ? replicaSourceChip(example.sourceLabel)
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
        head.addEventListener('click', e => e.stopPropagation());
    });

    // Sense selection — the caller resets to that sense's first example, the
    // same as selectMeaning() does on a live card.
    root.querySelectorAll('.meaning-row').forEach(row => {
        row.addEventListener('click', e => {
            if (e.target.closest('.sense-metadata-more, .sense-cross-reference')) return;
            e.stopPropagation();
            const idx = Number(row.dataset.meaningIndex);
            if (!Number.isNaN(idx)) onSelectMeaning?.(idx, row);
        });
    });

    root.querySelectorAll('.sense-metadata-more').forEach(control => {
        control.addEventListener('click', e => {
            e.stopPropagation();
            const list = control.closest('.sense-metadata-list');
            const expanded = control.getAttribute('aria-expanded') === 'true';
            const details = list?.querySelector('.sense-metadata-tier--details');
            if (details) details.hidden = expanded;
            control.setAttribute('aria-expanded', String(!expanded));
            const label = control.querySelector('.sense-metadata-more-label');
            if (label) label.textContent = expanded ? 'More details' : 'Hide details';
            control.setAttribute('aria-label', expanded
                ? `Show ${control.dataset.count} supporting details`
                : 'Hide supporting details');
            onLayoutChange?.();
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
