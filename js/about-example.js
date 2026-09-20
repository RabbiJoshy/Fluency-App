// About → "See Example": an annotated walkthrough of real flashcards.
//
// The About copy already carries two small auto-playing demo cards
// (`demo://normal` / `demo://artist`, built in auth.js). Those show the card
// moving; they deliberately say nothing about what any part of it means.
// This module is the other half: a stepped tour where the card sits still and
// the element being explained is ringed while its note is on screen.
//
// Two constraints shape the implementation:
//
//   1. "Exact replica". The card is built from the same class names and the
//      same inline styles that updateCard() in flashcards.js emits, so it
//      inherits the real card's CSS rather than a lookalike stylesheet. Only
//      SIZE is overridden (see .about-example-card-inner in style.css), the
//      same trick the inline demo cards use.
//   2. "Spotify needs to work". The Spotify button is not a picture of a
//      button — it calls the real window.spotifyPlayTrack() with a real track
//      id and a real lyric timestamp, and the Spotify module handles the
//      login hand-off itself when the visitor isn't connected yet. Track ids
//      and timestamps below are lifted from Artists/spotify_tracks.json and
//      the Bad Bunny deck, so they play the actual line on the actual song.
//
// Everything else about the card is inert on purpose: no progress is written,
// no deck state is touched, nothing here needs the app to have loaded a
// vocabulary. The walkthrough works for a logged-out visitor landing on
// `?about=1`, which is the main audience for it.

// ---------------------------------------------------------------------------
// Demo cards — real entries, real lyrics, real track ids.
// ---------------------------------------------------------------------------
//
// `cielo` is a genuine Bad Bunny deck entry — rank, line count, meanings,
// percentages, lyrics and timestamps all read out of the built deck rather
// than written for the walkthrough. `tem` is curated from the live Portuguese
// speech release because its Wiktionary senses demonstrate the compact
// metadata and cross-card-reference treatment.

const ABOUT_EXAMPLE_CARDS = {
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

// Each language selects its own representative card and dictionary wording.
// The controller below remains shared, so another language needs only a card
// and one adapter entry instead of a forked tutorial.
const TUTORIAL_LANGUAGE_ADAPTERS = {
    spanish: { language: 'Spanish', flag: '🇪🇸', speechCard: 'queSpeech', provider: 'SpanishDict', lyrics: true, usageShares: true },
    portuguese: { language: 'Portuguese', flag: '🇵🇹', speechCard: 'tem', provider: 'Wiktionary', lyrics: false, usageShares: true, crossReferences: true },
    czech: { language: 'Czech', flag: '🇨🇿', speechCard: 'jeSpeech', provider: 'Wiktionary', lyrics: false, usageShares: true },
    french: { language: 'French', flag: '🇫🇷', speechCard: 'deSpeech', provider: 'Wiktionary', lyrics: false },
};

let tutorialLanguageOverride = null;

function explicitTutorialLanguageKey() {
    const activeTab = document.querySelector('.lang-tab.active')?.dataset.lang;
    const hasLanguageSummary = document.getElementById('step1')?.classList.contains('language-summary-active');
    const candidate = window.activeArtist?.language
        || activeTab
        || (hasLanguageSummary ? window.selectedLanguage : null);
    return TUTORIAL_LANGUAGE_ADAPTERS[candidate] ? candidate : null;
}

function tutorialLanguageKey() {
    return tutorialLanguageOverride || explicitTutorialLanguageKey() || 'spanish';
}

function tutorialAdapter(requestedKey = tutorialLanguageKey()) {
    const key = TUTORIAL_LANGUAGE_ADAPTERS[requestedKey] ? requestedKey : 'spanish';
    const adapter = TUTORIAL_LANGUAGE_ADAPTERS[key];
    const configuredLyrics = window.config?.languages?.[key]?.capabilities?.lyrics;
    return { ...adapter, lyrics: adapter.lyrics && configuredLyrics !== false };
}

function tutorialText(value) {
    const adapter = tutorialAdapter();
    return String(value || '')
        .replaceAll('{language}', adapter.language)
        .replaceAll('{provider}', adapter.provider);
}

const CARD_WALKTHROUGH_SEEN_KEY = 'fluencyCardWalkthroughSeenV1';
const LEGACY_CARD_WALKTHROUGH_PROMPT_KEY = 'fluencyCardWalkthroughPromptV1';

function hasSeenCardWalkthrough() {
    try {
        return localStorage.getItem(CARD_WALKTHROUGH_SEEN_KEY) === '1'
            || localStorage.getItem(LEGACY_CARD_WALKTHROUGH_PROMPT_KEY) === '1';
    } catch (_) {
        return false;
    }
}

function rememberCardWalkthrough() {
    try {
        localStorage.setItem(CARD_WALKTHROUGH_SEEN_KEY, '1');
        // The older first-flip prompt reads this key. Marking both makes every
        // route into the same tour converge on one durable onboarding state.
        localStorage.setItem(LEGACY_CARD_WALKTHROUGH_PROMPT_KEY, '1');
    } catch (_) {}
}

// ---------------------------------------------------------------------------
// Decks and their annotations
// ---------------------------------------------------------------------------
//
// Two things are being selected independently, and conflating them was the
// first version's mistake:
//
//   * The DECK (Lyrics / Speech) — chosen by the tab. This is the only thing
//     the tab does.
//   * The FACE (back / front) — chosen by flipping the card, like anywhere
//     else in the app.
//
// Annotations belong to a FACE, not to a tab step. Flip the card and the whole
// numbered set is replaced by the one describing the side now showing;
// otherwise the labels stay behind pointing at elements that turned away.
//
// The back opens by default. It carries the senses, the shares and the
// evidence — everything the app is actually for. The front is a prompt.
//
// `anchor` is a CSS selector resolved inside the rendered card; `side` puts
// the note in the left or right column and pins its badge to the matching edge
// of the element, so a badge never has to cross the card to reach its note.

const ABOUT_EXAMPLE_DECKS = [
    {
        id: 'lyrics',
        card: 'cielo',
        tab: 'Lyrics',
        faces: {
            back: {
                title: 'The back of a Lyrics card',
                blurb: 'The meanings work exactly as they did on the Speech card. '
                     + 'These four things are new.',
                notes: [
                    {
                        side: 'left',
                        anchor: '.meanings-scroll .meaning-row:nth-child(2)',
                        title: 'Tap a meaning to change the lyric',
                        text: 'On a Speech card the example changes too — but here it switches to a completely different song line.',
                        interactive: true,
                    },
                    {
                        side: 'left',
                        anchor: '.translation',
                        title: 'The line in English',
                        text: 'So the whole lyric makes sense without looking anything up.',
                    },
                    {
                        side: 'left',
                        anchor: '.example-song-credit',
                        title: 'Which song it is from',
                        text: 'Plus any guest artist singing that line.',
                    },
                    {
                        side: 'right',
                        anchor: '.spotify-btn',
                        title: 'Play the line',
                        text: 'Plays that moment in your own Spotify. Spotify Premium required.',
                        interactive: true,
                    },
                    {
                        side: 'right',
                        anchor: '.example-ticks',
                        title: 'More examples',
                        text: 'If this meaning has more than one example, tap the lyric to see the next one.',
                        interactive: true,
                    },
                ],
            },
            front: {
                title: 'The front of a Lyrics card',
                blurb: 'Identical to the Speech card you just saw, with one number '
                     + 'measuring something different.',
                notes: [
                    {
                        side: 'right',
                        anchor: '.card-freq-label',
                        title: 'Song line count',
                        text: 'On a Speech card this says how often the word is spoken. Here it counts lyric lines instead.',
                    },
                ],
            },
        },
    },

    {
        id: 'speech',
        card: null,
        tab: 'Speech',
        faces: {
            back: {
                title: 'The back of the card',
                blurb: 'The back shows every meaning, how common each one is, and a real '
                     + 'example from spoken {language}.',
                notes: [
                    {
                        side: 'left',
                        anchor: '.back-headword',
                        title: 'The word',
                        text: 'Exactly as it appears in {language} speech — not always the dictionary’s base form.',
                    },
                    {
                        side: 'left',
                        anchor: '.pos-section-head',
                        title: 'The meanings at a glance',
                        text: 'A short list of the senses. Tap the heading if you want to open or close the group.',
                        interactive: true,
                    },
                    {
                        side: 'left',
                        anchor: '.meaning-row.is-current-sense',
                        title: 'The meaning you tapped',
                        text: 'The selected row shows the full wording. The others stay short so the card stays readable.',
                        interactive: true,
                    },
                    {
                        side: 'left',
                        anchor: '.sense-cross-reference',
                        requires: 'crossReferences',
                        title: 'A link to another card',
                        text: 'If the dictionary says “see this other word”, that is a real link here.',
                    },
                    {
                        side: 'right',
                        anchor: '.sense-metadata-list',
                        title: 'Useful extras',
                        text: 'Small notes such as grammar, what the word pairs with, or how formal it is. Extra ones hide behind More details.',
                        interactive: true,
                    },
                    {
                        side: 'right',
                        anchor: '.sense-prominence-badge',
                        requires: 'usageShares',
                        title: 'How common this meaning is',
                        text: 'The bars show how often this meaning shows up in real speech. Tap them to read Common, Uncommon, or Rare.',
                    },
                    {
                        side: 'right',
                        anchor: '.example-word-highlight',
                        title: 'A real example',
                        text: 'Tap a different meaning and this sentence changes to match it.',
                    },
                    {
                        side: 'right',
                        anchor: '.example-song-credit',
                        title: 'Where the example is from',
                        text: 'Usually spoken {language}. A dictionary example is used only when speech does not have a good one.',
                    },
                ],
            },
            front: {
                title: 'The front of the card',
                blurb: 'This is what you see when studying — the word and a few hints. '
                     + 'Try to remember the meaning before flipping.',
                notes: [
                    {
                        side: 'left',
                        anchor: '.card-word',
                        title: 'The word',
                        text: 'Try to recall it before you flip.',
                    },
                    {
                        side: 'left',
                        anchor: '.card-rank-label',
                        title: 'How common the word is',
                        text: 'Where this word sits in the {language} deck. More common words come first.',
                    },
                    {
                        side: 'right',
                        anchor: '.card-pos-list',
                        title: 'Kind of word',
                        text: 'A small hint. On the back it becomes the heading for the meanings.',
                    },
                    {
                        side: 'right',
                        anchor: '.card-freq-label',
                        title: 'How often it is said',
                        text: 'How often it appears in spoken {language}. On a song card this counts lyric lines instead.',
                    },
                ],
            },
        },
    },
];

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

const posAccentRgb = pos => POS_ACCENT_RGB[posClass(pos)] || '148, 163, 184';

const POS_NAME = {
    VERB: 'verb', NOUN: 'noun', ADJ: 'adjective', ADV: 'adverb',
    PREP: 'preposition', ADP: 'preposition', CONJ: 'conjunction',
    CCONJ: 'conjunction', SCONJ: 'conjunction', PRON: 'pronoun',
    DET: 'determiner', INT: 'interjection', INTJ: 'interjection',
    NUM: 'number', MWE: 'expression',
};

const posClass = (pos) => POS_CLASS[String(pos || '').toUpperCase()] || '';
const posName = (pos) => POS_NAME[String(pos || '').toUpperCase()] || String(pos || '').toLowerCase();

function esc(s) {
    return String(s ?? '')
        .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;');
}

// Same word-boundary highlight the real card applies to its example sentence:
// unicode property escapes so Spanish letters are handled, case-insensitive so
// a sentence-initial "Fuego" still matches. The sentence is escaped first, so
// data can never inject markup.
function highlightWord(sentence, word) {
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

function renderFront(card) {
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
function walkthroughSenseSummary(value) {
    let text = String(value || '').trim();
    let previous = '';
    while (text !== previous) {
        previous = text;
        text = text.replace(/\s*\([^()]*\)/gu, ' ');
    }
    return text.replace(/\s{2,}/gu, ' ').replace(/\s+([,;:.])/gu, '$1').trim();
}

function walkthroughSenseText(meaning, selected) {
    if (Array.isArray(meaning.references) && meaning.references.length) {
        const links = meaning.references.map(target => (
            `<button type="button" class="sense-cross-reference" title="Open ${esc(target)} card" `
            + `aria-label="Open ${esc(target)} card">${esc(target)}</button>`
        )).join('<span class="sense-cross-reference-separator">,</span> ');
        return `<span class="sense-cross-reference-prefix">See</span> ${links}`;
    }
    const value = selected ? meaning.translation : walkthroughSenseSummary(meaning.translation);
    return esc(value || meaning.translation);
}

function walkthroughMetadata(meaning, selected) {
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

function walkthroughProminence(pct) {
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
        const prominence = walkthroughProminence(m.pct);
        const pct = prominence
            ? (typeof window.prominenceBadgeHTML === 'function'
                ? window.prominenceBadgeHTML(prominence, 'position: absolute; right: 8px; top: 50%; transform: translateY(-50%);')
                : `<button type="button" class="about-example-pct sense-prominence-badge prominence-${esc(prominence.key)}" style="position: absolute; right: 8px; top: 50%; transform: translateY(-50%);">${esc(prominence.label)}</button>`)
            : '';
        const check = isSelected
            ? '<svg class="meaning-row-check" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="rgb(var(--sense-match-rgb))" stroke-width="3" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><polyline points="20 6 9 17 4 12"></polyline></svg>'
            : '';
        return `
            <div class="meaning-row meaning-row-regular${isSelected ? ' selected is-current-sense' : ''}" data-meaning-index="${idx}" style="position: relative; display: grid; grid-template-columns: 1fr; align-items: center; padding: 1px 2px; margin-bottom: 4px; background: ${bg}; border-radius: 8px; cursor: pointer; min-height: 39px;">
                ${check}
                <div class="meaning-row-body" style="display: flex; flex-direction: column; align-items: stretch; justify-content: center; min-width: 0; padding: 0 ${prominence ? '32px' : '8px'} 0 8px;">
                    <span class="meaning-row-translation row-adaptive-text" style="font-weight: ${isSelected ? 700 : 500}; color: ${textColor}; text-align: center; width: 100%;">${walkthroughSenseText(m, isSelected)}${ctx}</span>
                    ${walkthroughMetadata(m, isSelected)}
                </div>
                ${pct}
            </div>`;
    }).join('');
    const summaryLimit = Math.min(2, card.meanings.length);
    const summaries = card.meanings.slice(0, summaryLimit).map(meaning => (
        `<span class="pos-summary-sense">${esc(walkthroughSenseSummary(meaning.translation))}</span>`
    )).join('');
    const hiddenCount = card.meanings.length - summaryLimit;
    const more = hiddenCount > 0
        ? `<span class="pos-pill-more" aria-label="${hiddenCount} more senses">+${hiddenCount}</span>`
        : '';
    return `
        <section class="meaning-pos-section pos-collapsible is-open" data-pos="${esc(card.pos)}"
                 style="--sense-match-rgb: ${posAccentRgb(card.pos)};">
            <button type="button" class="pos-section-head" aria-label="${esc(`${posName(card.pos)}: ${card.meanings.map(m => walkthroughSenseSummary(m.translation)).join('; ')}`)}">
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
function walkthroughExampleTicks(current, total) {
    if (total < 2) return '';
    const ticks = Array.from({ length: total }, (_, i) =>
        `<span class="example-tick${i === current ? ' is-current' : ''}"></span>`
    ).join('');
    return `<div class="example-ticks" role="img" aria-label="example ${current + 1} of ${total}">${ticks}</div>`;
}

function tutorialSourceChip(sourceLabel) {
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
                data-about-example-spotify="1">${SPOTIFY_SVG}</button>`;
        const vocalists = example.vocalists
            ? `<span class="example-vocalist-credit"> · ${esc(example.vocalists)}</span>`
            : '';
        return `
            <div class="example-credit-row is-lyric">
                <span class="example-credit-start">
                    <span class="example-song-credit">— ${esc(example.song)}${vocalists}</span>
                </span>
                <span class="example-credit-end">${walkthroughExampleTicks(exampleIdx, meaning.examples.length)}${btn}</span>
            </div>`;
    }

    const credit = example.sourceLabel
        ? tutorialSourceChip(example.sourceLabel)
        : '';
    const ticks = walkthroughExampleTicks(exampleIdx, meaning.examples.length);
    if (!credit && !ticks) return '';
    return `
        <div class="example-credit-row">
            <span class="example-credit-start">${credit}</span>
            <span class="example-credit-end">${ticks}</span>
        </div>`;
}

function renderBack(card, selectedIdx, exampleIdx) {
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
                <div class="sentence example-is-matched" style="text-align: center; ${cursor} --sense-match-rgb: ${posAccentRgb(card.pos)}; border-color: transparent;" data-about-example-cycle="${meaning.examples.length > 1 ? '1' : '0'}">
                    <div class="breakdown-trigger" style="margin-bottom: 8px;">${highlightWord(example.target, card.word)}</div>
                    <div class="translation">${esc(example.english)}</div>
                    ${renderCredit(card, meaning, example, exampleIdx % meaning.examples.length)}
                </div>
            </div>
            <div class="card-tint" aria-hidden="true"></div>
        </div>`;
}


// ---------------------------------------------------------------------------
// Walkthrough controller
// ---------------------------------------------------------------------------

// What the walkthrough is showing right now. `flipped` is derived from the
// current step rather than owned: the step list decides which face is up, and
// renderCard()/flipCardFace() read this to drive the real card CSS.
const state = {
    stepIndex: 0,
    flipped: false,
    meaningIndex: 0,
    exampleIndex: 0,
    activeNote: -1,
};

// The tutorial is a flat list of steps, not a pair of decks with two faces
// each. Read top to bottom it is the story a first-time visitor gets: learn
// the card itself on an everyday Speech card, front then back; then a slide
// that says what Lyrics mode is, in its own words, before a Lyrics card
// appears. Reordering the story, or adding a slide to it, is a change to this
// list and to nothing else.
function tutorialSteps() {
    const steps = [
        { kind: 'card', deck: 'speech', face: 'front' },
        { kind: 'card', deck: 'speech', face: 'back' },
    ];
    // Only Spanish has a lyrics deck today. The others simply end after the
    // Speech card rather than promising a mode they cannot show.
    if (tutorialAdapter().lyrics) {
        steps.push({ kind: 'break', id: 'lyrics' });
        steps.push({ kind: 'card', deck: 'lyrics', face: 'front' });
        steps.push({ kind: 'card', deck: 'lyrics', face: 'back' });
    }
    return steps;
}

function currentStep() {
    return tutorialSteps()[state.stepIndex] || null;
}

const MOBILE_WALKTHROUGH_QUERY = '(max-width: 700px)';

function isMobileWalkthrough() {
    return window.matchMedia?.(MOBILE_WALKTHROUGH_QUERY).matches === true;
}

// The speech deck carries no card of its own: which one it shows depends on
// the language being taught, so it is filled in here.
function deckById(id) {
    const deck = ABOUT_EXAMPLE_DECKS.find(d => d.id === id);
    return deck.id === 'speech' ? { ...deck, card: tutorialAdapter().speechCard } : deck;
}

function currentDeck() {
    const step = currentStep();
    return step && step.kind === 'card' ? deckById(step.deck) : null;
}

function currentCard() {
    return ABOUT_EXAMPLE_CARDS[currentDeck().card];
}

// The annotation set is a property of the face on show. This is the whole
// reason flipping re-renders the notes.
function currentFace() {
    const step = currentStep();
    return step && step.kind === 'card' ? deckById(step.deck).faces[step.face] : null;
}

// Left column first, then right, so each note sits on the same side as the
// element it explains.
function stepNotes(step) {
    if (!step || step.kind !== 'card') return [];
    const notes = deckById(step.deck).faces[step.face].notes
        .filter(note => !note.requires || tutorialAdapter()[note.requires]);
    return [
        ...notes.filter(n => n.side !== 'right'),
        ...notes.filter(n => n.side === 'right'),
    ];
}

function orderedNotes() {
    return stepNotes(currentStep());
}

// A card step is worth one position per annotation; a break slide is worth
// one. Counting off the step list means the running total cannot drift out of
// step with the story the way a hand-folded count did.
function tutorialStepPosition(noteIndex = state.activeNote) {
    const steps = tutorialSteps();
    let before = 0;
    let total = 0;
    steps.forEach((step, i) => {
        const weight = step.kind === 'card' ? stepNotes(step).length : 1;
        total += weight;
        if (i < state.stepIndex) before += weight;
    });
    const within = Math.max(0, Math.min(noteIndex, Math.max(0, orderedNotes().length - 1)));
    return { current: before + within + 1, total };
}

// Full rebuild — used when the deck changes.
function renderCard() {
    const stage = document.getElementById('aboutExampleStage');
    if (!stage) return;
    const card = currentCard();

    stage.innerHTML = `
        <div class="about-example-card-inner">
            <div class="card${state.flipped ? ' flipped' : ''}" data-rank="${card.rank}">
                ${renderFront(card)}
                ${renderBack(card, state.meaningIndex, state.exampleIndex)}
            </div>
        </div>`;

    wireBack(stage);
    fitCardToContent();
    renderFaceCopy();
    renderNotes();
    markAnchors();
    syncContinueButton();
}

// Sense and example changes replace only the back face, leaving the .card
// element (and therefore its flip transform) untouched — the same division of
// labour as the live app, where updateCard() rewrites #backContent rather than
// the card around it.
function refreshBack() {
    const stage = document.getElementById('aboutExampleStage');
    const back = stage?.querySelector('.card-back');
    if (!stage || !back) return;
    back.outerHTML = renderBack(currentCard(), state.meaningIndex, state.exampleIndex);
    wireBack(stage);
    fitCardToContent();
    markAnchors();
}

// Flipping is a face change, so the annotations change with it: new copy, new
// numbered set, badges re-placed on the side now showing.
// Turn the card that is already on stage, rather than rebuilding it. Toggling
// the class is what lets the real 0.6s flip transition play.
function flipCardFace(mobileNote = 0) {
    const stage = document.getElementById('aboutExampleStage');
    const cardEl = stage?.querySelector('.card');
    if (!cardEl) return;

    state.activeNote = -1;
    cardEl.classList.toggle('flipped', state.flipped);

    renderFaceCopy();
    renderNotes();
    syncFlipButton();
    syncContinueButton();
    // Re-place once the transform has settled, so boxes are measured flat.
    setTimeout(() => {
        markAnchors();
        if (isMobileWalkthrough()) {
            const finalIndex = Math.max(0, orderedNotes().length - 1);
            setActiveNote(Math.min(mobileNote, finalIndex));
        }
    }, 640);
}

// Handlers for everything inside the back face. Called again after every
// back-face rebuild, since those nodes are replaced wholesale.
function wireBack(stage) {
    stage.querySelector('.pos-section-head')?.addEventListener('click', (e) => {
        // The walkthrough shows one already-open group. Keep taps on its
        // heading from being mistaken for a request to flip the whole card.
        e.stopPropagation();
    });

    // Sense selection — switching sense resets to that sense's first example,
    // the same as selectMeaning() does on a live card.
    stage.querySelectorAll('.meaning-row').forEach((row) => {
        row.addEventListener('click', (e) => {
            if (e.target.closest('.sense-metadata-more, .sense-cross-reference')) return;
            e.stopPropagation();
            const idx = Number(row.dataset.meaningIndex);
            if (Number.isNaN(idx)) return;
            state.meaningIndex = idx;
            state.exampleIndex = 0;
            refreshBack();
        });
    });

    stage.querySelector('.sense-metadata-more')?.addEventListener('click', (e) => {
        e.stopPropagation();
        const control = e.currentTarget;
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
        markAnchors();
    });

    // The real card opens the referenced vocabulary card. The walkthrough is
    // data-independent, so its copy of the control is intentionally inert.
    stage.querySelectorAll('.sense-cross-reference').forEach(reference => {
        reference.addEventListener('click', e => {
            e.preventDefault();
            e.stopPropagation();
        });
    });

    // Tap the lyric to cycle this sense's other examples.
    const sentence = stage.querySelector('.sentence[data-about-example-cycle="1"]');
    if (sentence) {
        sentence.addEventListener('click', (e) => {
            if (e.target.closest('.spotify-btn')) return;
            e.stopPropagation();
            state.exampleIndex += 1;
            refreshBack();
        });
    }

    // The live Spotify hand-off. spotifyPlayTrack() is published on window by
    // spotify.js; it resolves the token, runs the PKCE login when there isn't
    // one, and picks the Web Playback SDK or Connect by device — all of which
    // we want unchanged, which is why this defers rather than reimplementing.
    // If the module somehow isn't loaded, fall back to the web player.
    const spotifyBtn = stage.querySelector('[data-about-example-spotify]');
    if (spotifyBtn) {
        spotifyBtn.addEventListener('click', (e) => {
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
    }
}

function syncFlipButton() {
    const btn = document.getElementById('aboutExampleFlip');
    if (!btn) return;
    btn.textContent = state.flipped ? 'Flip to the front' : 'Flip to the back';
}

// One button, one job: go to the next step. Its label says what that step is,
// so the reader always knows what pressing it will do.
function syncContinueButton() {
    const btn = document.getElementById('aboutExampleContinue');
    if (!btn) return;
    const steps = tutorialSteps();
    const step = steps[state.stepIndex];
    // A break slide carries its own controls; the card's button would sit in a
    // column that is hidden behind it.
    const ready = !isMobileWalkthrough() && step && step.kind === 'card';
    btn.hidden = !ready;
    if (!ready) return;

    const next = steps[state.stepIndex + 1];
    const turningSameCard = next && next.kind === 'card' && next.deck === step.deck;
    btn.textContent = !next ? 'Finish tutorial'
        : turningSameCard ? 'Flip the card over →'
        : 'Next →';
    btn.classList.toggle('is-secondary', Boolean(turningSameCard));
}

// ---------------------------------------------------------------------------
// Annotations
// ---------------------------------------------------------------------------

// Badges are positioned from each target's measured box rather than hard-coded
// offsets, so they stay correct when a sense row wraps, the lyric runs to two
// lines, or the viewport narrows. A left-column note pins its badge to the
// element's left edge and a right-column note to its right edge, so no badge
// has to cross the card to reach the note it belongs to.
// Tag every annotated element so setActiveNote() can ring the one being
// explained. This used to also pin a numbered badge outside the card edge for
// each note; the numbers indexed nothing a reader needed once the tour walked
// them through one note at a time, so the amber outline is the only link now.
// Both faces live in the same fixed-height box, so the box has to be tall
// enough for whichever is taller — in practice always the back. Measuring the
// back's own content beats guessing a height that suits one card: `que` has
// three senses and `tem` has four with grammar pills under the selected one.
function fitCardToContent() {
    const inner = document.querySelector('.about-example-card-inner');
    const details = inner?.querySelector('.card-back .card-details');
    if (!inner || !details) return;
    const face = inner.querySelector('.card-back');
    const pad = face
        ? parseFloat(getComputedStyle(face).paddingTop) + parseFloat(getComputedStyle(face).paddingBottom)
        : 40;
    // Sum the three blocks rather than reading the container. .meanings-scroll
    // is the flex child that gives, so inside a fixed-height card it has
    // already been squeezed and the container's own scrollHeight reports the
    // squeezed figure — the overflow it is hiding never shows up.
    const rowGap = parseFloat(getComputedStyle(details).rowGap || getComputedStyle(details).gap) || 14;
    const heightOf = sel => {
        const el = face?.querySelector(sel);
        return el ? Math.max(el.getBoundingClientRect().height, el.scrollHeight) : 0;
    };
    // A floor so a one-sense card still reads as a card rather than a strip,
    // and a ceiling so a dense one cannot outgrow a short window.
    const wanted = Math.ceil(
        pad + rowGap * 2
        + heightOf('.back-header') + heightOf('.meanings-scroll') + heightOf('.sentence'),
    );
    const height = Math.max(430, Math.min(wanted, Math.round(window.innerHeight * 0.78)));
    inner.style.setProperty('--about-card-h', `${height}px`);
}

function markAnchors() {
    const stage = document.getElementById('aboutExampleStage');
    if (!stage) return;
    orderedNotes().forEach((note, i) => {
        const target = stage.querySelector(note.anchor);
        if (!target) return;
        target.classList.add('about-example-anchored');
        target.dataset.aboutExampleNote = String(i);
    });
    if (state.activeNote >= 0) setActiveNote(state.activeNote);
}

// Hovering either a badge or its note lights up both, plus the element itself.
function setActiveNote(index) {
    state.activeNote = index;
    renderSequenceProgress();
    const root = document.getElementById('aboutExampleModal');
    if (!root) return;
    root.querySelectorAll('.about-example-note').forEach((n) => {
        n.classList.toggle('is-active', Number(n.dataset.note) === index);
    });
    let active = null;
    root.querySelectorAll('.about-example-anchored').forEach((el) => {
        const on = Number(el.dataset.aboutExampleNote) === index;
        el.classList.toggle('is-annotation-active', on);
        if (on) active = el;
    });
    // A phone cannot show a dense card whole — `tem` wants more height than the
    // screen has once its rows wrap. Rather than clip it, bring whatever is
    // being explained into view inside its own scroll region. `nearest` keeps
    // this to the smallest scroll that works and never moves the page.
    if (active) active.scrollIntoView({ block: 'nearest', inline: 'nearest' });
    renderMobileCoach();
}

function renderMobileCoach() {
    const coach = document.getElementById('aboutExampleMobileCoach');
    if (!coach) return;
    const mobile = isMobileWalkthrough();
    const notes = orderedNotes();
    const index = Math.max(0, Math.min(state.activeNote, notes.length - 1));
    const note = notes[index];
    coach.hidden = !mobile || !note;
    if (coach.hidden) return;

    const progress = tutorialStepPosition(index);
    // No deck name here. Which deck you are on is the story the walkthrough is
    // telling — the Lyrics slide announces it — not a label to carry around.
    document.getElementById('aboutExampleMobileProgress').textContent =
        `Step ${progress.current} of ${progress.total} · ${state.flipped ? 'back of card' : 'front of card'}`;
    document.getElementById('aboutExampleMobileTitle').innerHTML =
        `${esc(note.title)}${note.interactive ? '<span class="about-example-try">tap it</span>' : ''}`;
    document.getElementById('aboutExampleMobileText').innerHTML = tutorialText(note.text);
    const back = document.getElementById('aboutExampleMobileBack');
    const next = document.getElementById('aboutExampleMobileNext');
    back.hidden = state.stepIndex === 0 && index === 0;
    back.disabled = false;
    const steps = tutorialSteps();
    const after = steps[state.stepIndex + 1];
    const turningSameCard = after && after.kind === 'card' && after.deck === steps[state.stepIndex].deck;
    next.textContent = index < notes.length - 1 ? 'Next'
        : !after ? 'Finish'
        : turningSameCard ? 'Flip over'
        : 'Continue';
}

function moveMobileTour(direction) {
    if (!isMobileWalkthrough()) return;
    const notes = orderedNotes();
    const index = Math.max(0, Math.min(state.activeNote, notes.length - 1));
    const candidate = index + direction;
    if (candidate >= 0 && candidate < notes.length) {
        setActiveNote(candidate);
        return;
    }
    // Past either end of this step's notes, move to the neighbouring step.
    // Stepping backwards lands on that step's last note, so the tour reverses
    // exactly as it ran forwards.
    if (direction > 0) advanceStep();
    else goToStep(state.stepIndex - 1, Number.MAX_SAFE_INTEGER);
}

function renderFaceCopy() {
    const face = currentFace();
    const host = document.getElementById('aboutExampleIntro');
    if (!host) return;
    // The title is a lead-in to the summary, not a heading over it — one
    // line instead of two, because the card and its annotations have to share
    // the screen. No "Lyrics · Bad Bunny · back of card" line either: the tab
    // already says which deck, and the card in front of you already says
    // which side you are looking at.
    host.innerHTML = `
        <p class="about-example-blurb">
            <strong class="about-example-lede">${tutorialText(face.title)}</strong>
            ${tutorialText(face.blurb)}
        </p>`;
}

function noteHTML(note, index) {
    return `
        <li class="about-example-note" data-note="${index}">
            <div>
                <strong>${note.title}${note.interactive ? '<span class="about-example-try">try it</span>' : ''}</strong>
                <span>${tutorialText(note.text)}</span>
            </div>
        </li>`;
}

function renderNotes() {
    const left = document.getElementById('aboutExampleNotesLeft');
    const right = document.getElementById('aboutExampleNotesRight');
    if (!left || !right) return;

    const notes = orderedNotes();
    const leftHTML = [];
    const rightHTML = [];
    notes.forEach((note, i) => {
        (note.side === 'right' ? rightHTML : leftHTML).push(noteHTML(note, i));
    });

    left.innerHTML = `<ol class="about-example-note-list">${leftHTML.join('')}</ol>`;
    right.innerHTML = `<ol class="about-example-note-list">${rightHTML.join('')}</ol>`;

    document.getElementById('aboutExampleModal')
        ?.querySelectorAll('.about-example-note')
        .forEach((el) => {
            const i = Number(el.dataset.note);
            el.addEventListener('mouseenter', () => setActiveNote(i));
            el.addEventListener('mouseleave', () => setActiveNote(-1));
        });
}

// ---------------------------------------------------------------------------
// Linear tutorial chapters
// ---------------------------------------------------------------------------

function renderSequenceProgress() {
    const host = document.getElementById('aboutExampleSequence');
    if (!host) return;
    // Just the language. "Speech → Lyrics" named two modes before the reader
    // had met either, which is a label for someone who already knows the app.
    host.innerHTML = `<strong>${esc(tutorialAdapter().language)} tutorial</strong>`;
}

// Moving between the two faces of one card turns it; anything else is a new
// thing on stage and gets built from scratch. `mobileNote` may be
// Number.MAX_SAFE_INTEGER, meaning "land on this step's last note", which is
// how stepping backwards reverses the tour.
function goToStep(index, mobileNote = 0) {
    const steps = tutorialSteps();
    if (index < 0 || index >= steps.length) return;

    const from = steps[state.stepIndex];
    const to = steps[index];
    const onStage = document.querySelector('#aboutExampleStage .card');
    const turnsInPlace = index !== state.stepIndex && onStage
        && from && from.kind === 'card' && to.kind === 'card'
        && from.deck === to.deck && from.face !== to.face;

    state.stepIndex = index;
    state.flipped = to.kind === 'card' && to.face === 'back';

    renderSequenceProgress();
    const body = document.getElementById('aboutExampleBody');

    if (to.kind === 'break') {
        renderBreakStep();
        if (body) body.scrollTop = 0;
        return;
    }

    showCardChrome();
    if (turnsInPlace) {
        flipCardFace(mobileNote);
        return;
    }

    state.meaningIndex = currentCard().defaultMeaningIndex || 0;
    state.exampleIndex = 0;
    state.activeNote = isMobileWalkthrough()
        ? Math.min(mobileNote, Math.max(0, stepNotes(to).length - 1))
        : 0;
    renderCard();
    syncFlipButton();
    renderMobileCoach();
    if (body) body.scrollTop = 0;
}

function advanceStep() {
    if (state.stepIndex < tutorialSteps().length - 1) goToStep(state.stepIndex + 1);
    else closeAboutExample();
}

// ---------------------------------------------------------------------------
// Break slides
// ---------------------------------------------------------------------------

// A step with no card. The walkthrough used to change deck silently and hope
// the reader noticed the tab, which meant the Lyrics chapter opened by
// explaining itself in an annotation. A mode deserves its own moment: this
// says what Lyrics mode is before showing one.
const TUTORIAL_BREAKS = {
    lyrics: {
        eyebrow: 'The other way to study',
        title: 'Lyrics mode',
        lead: 'Everything you have just seen works the same way with music. '
            + 'You pick an artist, and Fluency builds a deck from the words they '
            + 'actually sing.',
        points: [
            {
                title: 'The example is a real lyric',
                text: 'Instead of a line from film or television, each meaning is '
                    + 'shown with a line from one of their songs, English underneath.',
            },
            {
                title: 'You can hear it',
                text: 'A play button starts that exact line in Spotify, at the right '
                    + 'second, so you learn the word as it is actually sung.',
            },
            {
                title: 'Counted against the artist',
                text: 'The number on the front is how many of their lines use the '
                    + 'word, rather than how common it is in the language at large.',
            },
        ],
        cta: 'Show me a Lyrics card →',
    },
};

// Break slides borrow the info-sheet treatment the setup screens use for their
// help panels, so a visitor who later opens one recognises the shape.
function renderBreakStep() {
    const host = document.getElementById('aboutExampleBreak');
    if (!host) return;
    const slide = TUTORIAL_BREAKS[currentStep().id];
    if (!slide) return;

    const first = state.stepIndex === 0;
    host.innerHTML = `
        <div class="about-example-break-card">
            <span class="about-example-break-eyebrow">${esc(slide.eyebrow)}</span>
            <h3 class="about-example-break-title">${esc(slide.title)}</h3>
            <p class="about-example-break-lead">${tutorialText(slide.lead)}</p>
            <ul class="about-example-break-points">
                ${slide.points.map(point => `
                    <li>
                        <strong>${esc(point.title)}</strong>
                        <span>${tutorialText(point.text)}</span>
                    </li>`).join('')}
            </ul>
            <div class="about-example-break-actions">
                ${first ? '' : '<button type="button" class="about-example-break-back" id="aboutExampleBreakBack">Back</button>'}
                <button type="button" class="about-example-break-cta" id="aboutExampleBreakNext">${esc(slide.cta)}</button>
            </div>
        </div>`;

    // The slide carries its own title, so the card's one-line header would be
    // the previous step's copy left standing over it.
    const intro = document.getElementById('aboutExampleIntro');
    if (intro) intro.innerHTML = '';

    showBreakChrome();
    document.getElementById('aboutExampleBreakNext')?.addEventListener('click', advanceStep);
    document.getElementById('aboutExampleBreakBack')
        ?.addEventListener('click', () => goToStep(state.stepIndex - 1, Number.MAX_SAFE_INTEGER));
}

// The card and its note columns, or the slide — never both. The mobile coach
// belongs to the card, so it goes with it.
function showBreakChrome() {
    document.getElementById('aboutExampleBody')?.classList.add('is-break-step');
    const host = document.getElementById('aboutExampleBreak');
    if (host) host.hidden = false;
    const coach = document.getElementById('aboutExampleMobileCoach');
    if (coach) coach.hidden = true;
    const cont = document.getElementById('aboutExampleContinue');
    if (cont) cont.hidden = true;
}

function showCardChrome() {
    document.getElementById('aboutExampleBody')?.classList.remove('is-break-step');
    const host = document.getElementById('aboutExampleBreak');
    if (host) { host.hidden = true; host.innerHTML = ''; }
}

// ---------------------------------------------------------------------------
// Setup-flow intro
// ---------------------------------------------------------------------------

// Three beats miming the real setup flow — language, level, study set — played
// once before the first card, so the walkthrough starts where a learner would
// actually start rather than dropping them straight onto a flashcard. It is
// purely presentational: the markup is static, nothing here reads or writes
// real config, and only the language line follows the chosen tutorial.

// Held so the skip button or a close can cut the sequence short. Null whenever
// no intro is running.
let _setupIntroFinish = null;
let _setupIntroTimers = [];

function resetSetupIntro() {
    _setupIntroTimers.forEach(clearTimeout);
    _setupIntroTimers = [];
    _setupIntroFinish = null;
    const host = document.getElementById('aboutExampleSetupAnim');
    if (host) {
        host.hidden = true;
        host.querySelector('.setup-anim-screen')?.classList.remove('is-leaving');
        host.querySelectorAll('.setup-anim-panel').forEach((el, i) => { el.hidden = i > 0; });
        host.querySelectorAll('.setup-anim-target').forEach((el) => {
            el.classList.remove('is-pressed', 'is-chosen', 'is-ready');
        });
        const pointer = document.getElementById('setupAnimPointer');
        if (pointer) { pointer.classList.remove('is-visible', 'is-pressing'); pointer.removeAttribute('style'); }
        const statusText = document.getElementById('setupAnimStatusText');
        if (statusText) statusText.textContent = 'Choosing where you begin…';
    }
    document.getElementById('aboutExampleBody')?.classList.remove('is-setup-intro');
}

// Cutting in early lands on the card, not on a half-played animation.
function skipSetupIntro() {
    _setupIntroFinish?.();
}

// Park the pointer over an element's centre, in the coordinate space of the
// replica screen. Measuring rather than hard-coding keeps the pointer on
// target when the panel reflows at narrow widths.
function moveSetupPointer(target) {
    const pointer = document.getElementById('setupAnimPointer');
    const screen = document.querySelector('.setup-anim-screen');
    if (!pointer || !screen || !target) return;
    const box = target.getBoundingClientRect();
    const frame = screen.getBoundingClientRect();
    if (!box.width && !box.height) return;
    pointer.style.left = `${box.left - frame.left + box.width / 2}px`;
    pointer.style.top = `${box.top - frame.top + box.height / 2}px`;
    pointer.classList.add('is-visible');
}

// The intro is a scripted pass through the real setup screen: pick a language,
// pick what kind of language, pick a level, pick a set, press the button. An
// earlier version showed three rows ticking themselves off, which told a
// first-time visitor what the app had decided but not where any of it happens.
function playSetupIntro(onDone) {
    const host = document.getElementById('aboutExampleSetupAnim');
    const body = document.getElementById('aboutExampleBody');
    const reduced = window.matchMedia?.('(prefers-reduced-motion: reduce)').matches;
    if (!host || !body || reduced) {
        onDone();
        return;
    }

    resetSetupIntro();

    const adapter = tutorialAdapter();
    const flag = document.getElementById('setupAnimLangFlag');
    const name = document.getElementById('setupAnimLangName');
    if (flag) flag.textContent = adapter.flag || '';
    if (name) name.textContent = adapter.language;

    host.hidden = false;
    body.classList.add('is-setup-intro');

    const el = id => document.getElementById(id);
    const at = (ms, fn) => _setupIntroTimers.push(setTimeout(fn, ms));
    const caption = el('setupAnimCaption');
    const status = el('setupAnimStatusText');
    const pointer = el('setupAnimPointer');

    const finish = () => { resetSetupIntro(); onDone(); };
    _setupIntroFinish = finish;

    // Reach for a control, press it, and leave it looking chosen.
    const press = (target, after) => {
        moveSetupPointer(target);
        _setupIntroTimers.push(setTimeout(() => {
            pointer?.classList.add('is-pressing');
            target?.classList.add('is-pressed');
        }, 520));
        _setupIntroTimers.push(setTimeout(() => {
            pointer?.classList.remove('is-pressing');
            target?.classList.remove('is-pressed');
            target?.classList.add('is-chosen');
            after?.();
        }, 760));
    };

    // Each beat is one decision, held long enough to read the thing being
    // pressed before the next panel appears.
    const BEAT = 1500;
    let t = 400;

    at(t, () => {
        if (caption) caption.textContent = `First you pick a language.`;
        press(el('setupAnimLangChip'));
    });

    t += BEAT;
    at(t, () => {
        if (caption) caption.textContent = 'Then what kind of language you want to understand.';
        press(el('setupAnimModeSpeech'));
    });

    t += BEAT;
    at(t, () => {
        if (caption) caption.textContent = 'Then how far in to start. Level 1 is the most common words.';
        el('setupAnimLevelPanel').hidden = false;
        el('setupAnimModePanel').hidden = true;
        press(el('setupAnimLevel1'));
    });

    t += BEAT;
    at(t, () => {
        if (caption) caption.textContent = 'Levels are split into small sets, so a session is finishable.';
        el('setupAnimSetPanel').hidden = false;
        el('setupAnimLevelPanel').hidden = true;
        press(el('setupAnimSet1'));
    });

    // The sequence stops here rather than pressing its own last button. The
    // visitor opens their first card, which is both the real gesture and what
    // gives the whole thing a moment to land.
    t += BEAT;
    at(t, () => {
        if (caption) caption.textContent = 'That is the whole setup. Here is what a card looks like.';
        if (status) status.textContent = 'Press Learn 20 new cards to see your first card';
        el('setupAnimActionBtn')?.classList.add('is-ready');
        moveSetupPointer(el('setupAnimActionBtn'));
    });
}

// The explicit advance out of the intro: press the button the pointer has just
// arrived at, watch it depress, then let the card come up behind it.
function startSetupIntroCard() {
    const host = document.getElementById('aboutExampleSetupAnim');
    const btn = document.getElementById('setupAnimActionBtn');
    if (!host || !_setupIntroFinish || !btn?.classList.contains('is-ready')) return;
    const done = _setupIntroFinish;
    _setupIntroTimers.forEach(clearTimeout);
    _setupIntroTimers = [];
    btn.classList.add('is-pressed');
    _setupIntroTimers.push(setTimeout(() => {
        host.querySelector('.setup-anim-screen')?.classList.add('is-leaving');
    }, 220));
    _setupIntroTimers.push(setTimeout(done, 620));
}

// ---------------------------------------------------------------------------
// Open / close
// ---------------------------------------------------------------------------

let _resizeHandler = null;

function openAboutExample() {
    const modal = document.getElementById('aboutExampleModal');
    if (!modal) return;
    rememberCardWalkthrough();
    modal.classList.remove('hidden');
    // Start from the top every time. Without this a replay opens with whatever
    // the last run finished on still on screen — a break slide, most visibly,
    // sitting under the intro.
    state.stepIndex = 0;
    showCardChrome();
    // The card is rendered only once the intro is out of the way: marker
    // placement measures real boxes, and those read zero while the columns
    // are hidden behind the animation.
    playSetupIntro(() => goToStep(0));

    if (!_resizeHandler) {
        _resizeHandler = () => {
            if (isMobileWalkthrough() && state.activeNote < 0) state.activeNote = 0;
            fitCardToContent();
            markAnchors();
            syncContinueButton();
            renderMobileCoach();
        };
        window.addEventListener('resize', _resizeHandler);
    }
}

function openFirstRunAboutExample() {
    if (hasSeenCardWalkthrough()) return false;
    // The setup screen has a technical default before the learner chooses a
    // language. Do not mistake that for interest and launch the wrong tour.
    if (!explicitTutorialLanguageKey()) return false;
    // Never stack the automatic tour over authentication, About, settings, or
    // another onboarding sheet. Permanent replay links remain available.
    if (document.querySelector('.modal:not(.hidden), .knowledge-overview-modal:not([hidden])')) {
        return false;
    }
    openAboutExample();
    return true;
}

// The modal is layered over its opener. Closing therefore reveals About when
// launched there, or the main app when launched by onboarding/help.
function closeAboutExample() {
    const modal = document.getElementById('aboutExampleModal');
    if (!modal) return;
    modal.classList.add('hidden');
    resetSetupIntro();
    showCardChrome();
    // Leave any Spotify playback the visitor started running — they pressed
    // play deliberately, and closing a walkthrough shouldn't stop their music.
    if (_resizeHandler) {
        window.removeEventListener('resize', _resizeHandler);
        _resizeHandler = null;
    }
}

function setupAboutExample() {
    const modal = document.getElementById('aboutExampleModal');
    if (!modal || modal.dataset.ready === '1') return;
    modal.dataset.ready = '1';

    document.getElementById('closeAboutExampleModal')?.addEventListener('click', closeAboutExample);
    // Start set is the deliberate way out of the intro and only works once the
    // three steps have filled in; Skip intro leaves at any point. A stray click
    // on the card does nothing, or "deliberate" would mean very little.
    document.getElementById('setupAnimActionBtn')?.addEventListener('click', startSetupIntroCard);
    document.getElementById('setupAnimSkipBtn')?.addEventListener('click', skipSetupIntro);
    document.getElementById('aboutExampleFlip')?.addEventListener('click', () => flipCardFace(0));
    document.getElementById('aboutExampleContinue')?.addEventListener('click', () => {
        advanceStep();
    });
    document.getElementById('aboutExampleMobileBack')?.addEventListener('click', () => moveMobileTour(-1));
    document.getElementById('aboutExampleMobileNext')?.addEventListener('click', () => moveMobileTour(1));

    // Escape closes; left/right jump chapters, kept as an escape hatch for
    // anyone who wants to skip ahead. Space deliberately does nothing: the
    // walkthrough owns the flip, so the card only turns when the tour says so.
    document.addEventListener('keydown', (e) => {
        if (modal.classList.contains('hidden')) return;
        if (e.key === 'Escape') closeAboutExample();
        else if (e.key === 'ArrowRight') goToStep(state.stepIndex + 1);
        else if (e.key === 'ArrowLeft') goToStep(state.stepIndex - 1);
    });
}

document.addEventListener('DOMContentLoaded', setupAboutExample);
if (document.readyState !== 'loading') setupAboutExample();

window.openAboutExample = openAboutExample;
window.openFirstRunAboutExample = openFirstRunAboutExample;
window.closeAboutExample = closeAboutExample;
window.getCardTutorialProfile = tutorialAdapter;
window.getCardTutorialLanguageKey = explicitTutorialLanguageKey;
window.getCardTutorialLanguages = () => Object.entries(TUTORIAL_LANGUAGE_ADAPTERS)
    .map(([key, adapter]) => ({ key, language: adapter.language }));
window.setCardTutorialLanguage = key => {
    tutorialLanguageOverride = TUTORIAL_LANGUAGE_ADAPTERS[key] ? key : null;
};
