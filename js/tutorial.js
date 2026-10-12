// The card tutorial — for LEARNERS, people actually using the app.
//
// Not the walkthrough (walkthrough.js), which is a two-screen demo for
// visitors and opens from About. This one is opened by the "?" button, by the
// first-run prompt and by Settings → How to Study, and it teaches someone who
// is about to study. Three chapters, most needed first: the card in their
// chosen mode, one element at a time (the tutorial owns the flip), then Smart
// Skip, then switching between speech and music. Each chapter ends with the
// choice to start studying. Desktop and phone are equal targets; the phone
// gets a coach sheet instead of note columns.
//
// The card itself is drawn by card-replica.js, which both features share.

import {
    REPLICA_CARDS, esc, posAccentRgb, posName, renderBack, replicaCardHTML, wireReplicaBack,
} from './card-replica.js?v=db6ceea7';


// Each language selects its own representative card and dictionary wording.
// The controller below remains shared, so another language needs only a card
// and one adapter entry instead of a forked tutorial.
// The Smart Skip examples are the ones its own page uses (fast-mode.js), so
// the tutorial and the setting never show a learner different words.
const TUTORIAL_LANGUAGE_ADAPTERS = {
    spanish: { language: 'Spanish', flag: '🇪🇸', speechCard: 'quieroSpeech', provider: 'SpanishDict', lyrics: true, usageShares: true,
        smartSkip: { forms: ['hablo', 'habló', 'hablar'], plurals: ['vida', 'vidas'], lookalike: 'chocolate' } },
    portuguese: { language: 'Portuguese', flag: '🇵🇹', speechCard: 'ptDeviaSpeech', provider: 'Wiktionary', lyrics: false, usageShares: true,
        smartSkip: { forms: ['falo', 'falou', 'falar'], plurals: ['noite', 'noites'], lookalike: 'hotel' } },
    czech: { language: 'Czech', flag: '🇨🇿', speechCard: 'jeSpeech', provider: 'Wiktionary', lyrics: false, usageShares: true,
        smartSkip: { forms: ['dělám', 'dělal', 'dělat'], lookalike: 'film' } },
    french: { language: 'French', flag: '🇫🇷', speechCard: 'deSpeech', provider: 'Wiktionary', lyrics: false,
        smartSkip: { forms: ['parle', 'parla', 'parler'], lookalike: 'important' } },
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
        .replaceAll('{provider}', adapter.provider)
        .replaceAll('{posExample}', tutorialLanguageKey() === 'portuguese' ? 'For example, Portuguese “como” can be a verb (“I eat”) or a conjunction (“as”).' : '')
        .replaceAll('{demoLemma}', currentCard()?.lemma || currentCard()?.word || '')
        .replaceAll('{lemmaSentence}', (() => {
            const card = currentCard();
            if (!card) return '';
            return card.lemma && card.lemma !== card.word
                ? `Here the word is “${card.word}” but its dictionary form is “${card.lemma}”, the form you would find in a dictionary.`
                : `Here the word and dictionary form are both “${card.lemma || card.word}”. Inflected words can differ: {lemmaExample}.`;
        })())
        .replaceAll('{altMeaning}', esc(orderedMeanings(currentCard())[1]?.translation || ''))
        .replaceAll('{demoWord}', currentCard()?.word || '')
        .replaceAll('{rank}', (currentCard()?.rank || '').toLocaleString())
        .replaceAll('{vocabSize}', (currentCard()?.vocabSize || '').toLocaleString())
        .replaceAll('{perMillion}', Math.round(currentCard()?.corpusCount || 0).toLocaleString())
        .replaceAll('{pluralForms}', listPhrase((adapter.smartSkip.plurals || []).map(form => `“${form}”`)))
        .replaceAll('{lemmaExample}', ({ portuguese: '“tenho” (I have) comes from “ter” (to have)', spanish: '“tengo” (I have) comes from “tener” (to have)', czech: '“jsem” (I am) comes from “být” (to be)', french: '“ai” (I have) comes from “avoir” (to have)' })[tutorialLanguageKey()] || '')
        .replaceAll('{smartSkipForms}', listPhrase(adapter.smartSkip.forms.map(form => `“${form}”`)))
        .replaceAll('{smartSkipLookalike}', `“${adapter.smartSkip.lookalike}”`)
        .replace(/\bTap\b/g, isMobileTutorial() ? 'Tap' : 'Click');
}

function listPhrase(items) {
    return items.length > 1 ? `${items.slice(0, -1).join(', ')} and ${items[items.length - 1]}` : items.join('');
}

// The stored key names predate the tutorial/walkthrough split. Renaming them
// would re-show the tutorial to everyone who has already seen it.
const TUTORIAL_SEEN_KEY = 'fluencyCardWalkthroughSeenV1';
const LEGACY_TUTORIAL_PROMPT_KEY = 'fluencyCardWalkthroughPromptV1';

function hasSeenCardTutorial() {
    try {
        return localStorage.getItem(TUTORIAL_SEEN_KEY) === '1'
            || localStorage.getItem(LEGACY_TUTORIAL_PROMPT_KEY) === '1';
    } catch (_) {
        return false;
    }
}

function rememberCardTutorial() {
    try {
        localStorage.setItem(TUTORIAL_SEEN_KEY, '1');
        // The older first-flip prompt reads this key. Marking both makes every
        // route into the same tour converge on one durable onboarding state.
        localStorage.setItem(LEGACY_TUTORIAL_PROMPT_KEY, '1');
    } catch (_) {}
}

// ---------------------------------------------------------------------------
// Decks and their annotations
// ---------------------------------------------------------------------------
//
// Shared annotations explain the card; Lyrics adds only song-specific details
// and swaps in `lyricsText` where a note's wording is about speech.
// `anchor` resolves inside the replica and `side` chooses the note column. A
// `closing` note comes last on its face whichever column it sits in.
//
// Notes explain; they do not set tasks. The card stays live, so a reader can
// tap a meaning or an example, but nothing waits for them to.

const TUTORIAL_DECKS = [
    {
        id: 'lyrics',
        card: 'cielo',
        tab: 'Lyrics',
        faces: {
            back: {
                notes: [
                    {
                        side: 'right',
                        anchor: '.spotify-btn',
                        title: 'Play the line',
                        text: 'Plays that moment in your own Spotify. Spotify Premium required.',
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
                blurb: 'The back shows the meanings, how common each one is, and a real '
                     + 'example in {language}.',
                notes: [
                    {
                        side: 'left',
                        anchor: '.pos-section-head',
                        title: 'The kind of word',
                        text: 'Meanings are grouped by kind of word. This heading names the group, gives its dictionary form and sums up the meanings beneath.',
                    },
                    // One note per meaning row, filled in from the card on show.
                    { side: 'left', rows: true },
                    {
                        side: 'left',
                        anchor: '.sense-note-trigger',
                        when: card => Boolean(selectedMeaning(card)?.context || selectedMeaning(card)?.metadata?.length),
                        title: 'More about a meaning',
                        text: 'Tap the “i” on the highlighted meaning for when it is used and any grammar that goes with it.',
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
                        anchor: '.meaning-row .sense-prominence-badge',
                        all: true,
                        requires: 'usageShares',
                        title: 'How common each meaning is',
                        text: 'The bars show how often each meaning turns up in real speech. Tap them to read Dominant, Common, Uncommon, or Rare.',
                        lyricsText: 'The bars show how often each meaning turns up in your chosen songs. Tap them to read Dominant, Common, Uncommon, or Rare.',
                    },
                    {
                        side: 'right',
                        anchor: '.sentence',
                        title: 'A real example',
                        lyricsTitle: 'A real lyric',
                        text: 'A sentence that uses the highlighted meaning. Tap a meaning to see its example; where a meaning has several, tap the sentence for the next.',
                        lyricsText: 'A line that uses the highlighted meaning. Tap a meaning to see its line; where it has several, tap the line for the next.',
                    },
                    {
                        side: 'right',
                        anchor: '.sentence .translation',
                        title: 'The sentence in English',
                        lyricsTitle: 'The line in English',
                        text: 'So you can check the meaning without looking anything up.',
                        lyricsText: 'So the whole lyric makes sense without looking anything up.',
                    },
                    {
                        side: 'right',
                        anchor: '.example-song-credit',
                        title: 'Where it comes from',
                        lyricsTitle: 'Which song it is from',
                        text: 'Film or TV dialogue (IMDb), Tatoeba for contributed sentences, or {provider} for dictionary examples.',
                        lyricsText: 'The song, plus any guest artist singing that line.',
                    },
                    // The next two do something: the tour performs the tap.
                    {
                        side: 'right',
                        demo: 'selectMeaning',
                        when: card => (card?.meanings?.length || 0) > 1,
                        find: stage => [stage.querySelector(`.meaning-row[data-meaning-index="${altMeaningIndex()}"]`),
                            stage.querySelector('.sentence')],
                        title: 'Change the meaning',
                        text: 'Tap another meaning, here “{altMeaning}”, and the example below changes to a sentence that uses that meaning. The highlighted row is always the one being illustrated.',
                    },
                    {
                        side: 'right',
                        demo: 'cycleExample',
                        when: card => (card?.meanings || []).some(m => m.examples.length > 1),
                        anchor: '.sentence',
                        title: 'Cycle through the examples',
                        text: 'Tap the sentence and the next example of the same meaning takes its place; the little dots beneath mark which one you are on. After the last it goes back to the first.',
                    },
                    {
                        side: 'right',
                        demo: 'openRare',
                        when: card => Boolean(card?.rareUses?.length),
                        anchor: '.ref-rare-uses-btn',
                        title: 'Rare uses',
                        text: 'Opens a sheet over the card listing the word’s less common meanings, each with an example folded under it (tap “Examples”). They are for browsing and are not tested in daily reviews. Tap × to close.',
                    },
                    {
                        side: 'right',
                        demo: 'openReview',
                        anchor: '.knowledge-overview-trigger',
                        title: 'Flag a meaning',
                        text: 'Know the word, but not every meaning? The badge shows how many meanings you have flagged for review. Tap it to tick the ones you want future reviews to bring back; those move to the top of the card’s back, and the meanings you know fade to the bottom.',
                    },
                    {
                        side: 'right',
                        demo: 'openLookup',
                        when: card => Boolean(card?.lookup?.length),
                        find: stage => [stage.querySelector('.ref-lookup-btn'), stage.querySelector('.lookup-sheet')],
                        title: 'Look up',
                        text: 'Opens a short column of dictionary sites above the button, for when you want more than the card gives.',
                    },
                    {
                        side: 'right',
                        demo: 'armLookup',
                        when: card => Boolean(card?.lookup?.length),
                        find: stage => [stage.querySelector('.lookup-sheet-icon'), stage.querySelector('.lookup-sheet')],
                        title: 'Open a dictionary',
                        text: 'Tap a site and a Visit button appears; tap that and the word’s dictionary form (“{demoLemma}”) opens there in a new tab. Nothing leaves the app until you confirm.',
                    },
                    {
                        side: 'right',
                        anchor: '.card-back',
                        closing: true,
                        title: 'Grade your answer',
                        text: 'Swipe right if you knew it, left if you need more practice. On a computer, press Enter for Got it or X for Needs practice.',
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
                        text: 'Try to recall what it means, then tap the card to flip it. On a computer, press Space.',
                    },
                    {
                        side: 'left',
                        anchor: '.card-rank-label',
                        title: 'Vocabulary rank',
                        text: 'Where the word sits in the {language} deck: number {rank} of {vocabSize}. The most common words come first.',
                        lyricsText: 'Where the word sits in your deck: number {rank} of {vocabSize}. The most common words come first.',
                    },
                    {
                        side: 'right',
                        anchor: '.card-freq-label',
                        title: 'How often it is said',
                        lyricsTitle: 'Song lines',
                        text: 'About {perMillion} times in every million words of {language} dialogue.',
                        lyricsText: 'How many lines in your chosen songs contain it: {perMillion}.',
                    },
                    {
                        side: 'right',
                        anchor: '.front-pos-unit .card-pos',
                        title: 'Kind of word',
                        text: 'The label names the kind of word, such as a noun or verb. Different kinds of use get separate groups on the back. {posExample}',
                    },
                    {
                        side: 'right',
                        anchor: '.front-lemma-name',
                        title: 'The dictionary form',
                        text: '{lemmaSentence} The small label tells you which dictionary entry to look up.',
                    },
                ],
            },
        },
    },
];

// Smart Skip and the vocabulary source are not on the card, so each gets a
// page of its own: a copy of the real control, annotated the way the card is.
const TUTORIAL_PAGES = {
    smartSkip: {
        title: 'Smart Skip',
        blurb: 'Study fewer cards for the same coverage.',
        notes: [
            {
                side: 'left',
                anchor: '.tutorial-page-switch-row',
                title: 'Turn it on',
                text: 'Smart Skip is the switch under Choose level. It is recommended, and you can turn it off at any time.',
            },
            {
                side: 'left',
                anchor: '.tutorial-page-lookalike',
                title: 'Look-alikes are skipped',
                text: 'Words that look and mean the same as in a language you know, like {smartSkipLookalike} in English. Tap Smart Skip to see every word it set aside; you can still study them.',
            },
            {
                side: 'right',
                anchor: '.tutorial-page-forms',
                title: 'Word forms share a card',
                text: '{smartSkipForms} share one flashcard, so you learn the word once.',
            },
            {
                side: 'right',
                anchor: '.tutorial-page-plurals',
                when: () => Boolean(tutorialAdapter().smartSkip.plurals),
                title: 'Singular and plural share a card',
                text: '{pluralForms} are one noun, so they share one flashcard. This happens only when the singular and the plural mean exactly the same things; if either has an extra meaning they stay separate.',
            },
        ],
        html: smartSkipPageHTML,
    },
    modes: {
        title: 'Speech or music',
        blurb: 'Both teach the same words in the same way. What differs is where the words, and the example sentences on the back of each card, come from.',
        notes: [
            {
                side: 'left',
                anchor: '.tutorial-page-source:nth-of-type(1)',
                title: 'Speech',
                text: 'Words are ranked by how often people actually say them, counted across thousands of films and TV series. It is the fastest route to the words you need for ordinary conversation, and the examples are lines of real dialogue.',
            },
            {
                side: 'left',
                anchor: '.tutorial-page-source:nth-of-type(2)',
                title: 'Music',
                text: 'You choose the songs, and the words are ranked by how often they appear in those lyrics. Song lyrics use different vocabulary from speech, so the deck changes with your taste, and every example is a real line from one of your songs, with the artist and a button to play it in Spotify.',
            },
            {
                side: 'right',
                anchor: '.tutorial-page-sources',
                requires: 'lyrics',
                title: 'Two ways to choose your music',
                text: 'Pick artists from the app’s library, taking all of their songs or just the ones you choose. Or connect Spotify and build a deck from one of your own playlists, either from songs the app already has or from a new import.',
            },
            {
                side: 'right',
                anchor: '.tutorial-page-topbar',
                title: 'Switch at any time',
                text: 'You can change between them whenever you like, from the language header at the top of the screen. Your progress comes with you: a word you learn in one is already marked known when it appears in the other.',
            },
        ],
        html: modesPageHTML,
    },
};

function smartSkipPageHTML(adapter) {
    const { forms, lookalike, plurals } = adapter.smartSkip;
    const word = value => `<span class="tutorial-page-word">${esc(value)}</span>`;
    return `
        <div class="tutorial-page" aria-label="Example of Smart Skip">
            <div class="tutorial-page-switch-row">
                <svg class="tutorial-page-skip-icon" viewBox="0 0 24 24" aria-hidden="true"><path d="M3 5.5v13l8-6.5-8-6.5Z"></path><path d="M12 5.5v13l8-6.5-8-6.5Z"></path></svg>
                <span class="tutorial-page-switch-copy">
                    <strong>Smart Skip <span class="streamline-rec-badge">Recommended</span></strong>
                    <small>Fewer cards, same coverage</small>
                </span>
                <span class="tutorial-page-switch" aria-hidden="true"><i></i></span>
            </div>
            <div class="tutorial-page-example tutorial-page-lookalike">
                <span class="tutorial-page-label">Skip look-alikes</span>
                <div class="tutorial-page-flow">
                    <span class="tutorial-page-words">${word(lookalike)}<span class="tutorial-page-gloss">English: ${esc(lookalike)}</span></span>
                    <span class="tutorial-page-arrow" aria-hidden="true">→</span>
                    <span class="tutorial-page-result is-skipped">Skipped</span>
                </div>
            </div>
            <div class="tutorial-page-example tutorial-page-forms">
                <span class="tutorial-page-label">Combine word forms</span>
                <div class="tutorial-page-flow">
                    <span class="tutorial-page-words">${forms.map(word).join('')}</span>
                    <span class="tutorial-page-arrow" aria-hidden="true">→</span>
                    <span class="tutorial-page-result">1 card</span>
                </div>
            </div>
            ${plurals ? `<div class="tutorial-page-example tutorial-page-plurals">
                <span class="tutorial-page-label">Combine singular and plural</span>
                <div class="tutorial-page-flow">
                    <span class="tutorial-page-words">${plurals.map(word).join('')}</span>
                    <span class="tutorial-page-arrow" aria-hidden="true">→</span>
                    <span class="tutorial-page-result">1 card</span>
                </div>
            </div>` : ''}
        </div>`;
}

// The two sources in the app's own words (ui.js learningModeCopy), so the
// copy cannot drift from the picker it shows. The fallback is for tests.
function modesPageHTML(adapter) {
    const copy = window.learningModeCopy?.(tutorialLanguageKey()) || {
        speech: { label: 'Speech', description: 'From films and TV shows.' },
        lyrics: { label: 'Music', description: 'The words in the songs you choose.' },
    };
    const current = state.mode === 'lyrics' ? 'lyrics' : 'speech';
    const source = id => `
        <div class="tutorial-page-source${id === current ? ' is-current' : ''}">
            <span class="tutorial-page-source-icon" aria-hidden="true">${copy[id].iconHTML || ''}</span>
            <span class="tutorial-page-source-copy"><strong>${esc(copy[id].label)}</strong><small>${esc(copy[id].description)}</small></span>
            <span class="tutorial-page-source-tail" aria-hidden="true">${id === current ? '✓' : '›'}</span>
        </div>`;
    return `
        <div class="tutorial-page" aria-label="Example of switching vocabulary">
            <div class="tutorial-page-topbar">
                <span class="tutorial-page-flag" aria-hidden="true">${adapter.flag}</span>
                <strong>${esc(adapter.language)}</strong>
                <span class="tutorial-page-chevron" aria-hidden="true">›</span>
            </div>
            <div class="tutorial-page-sources">
                <span class="tutorial-page-label">Vocabulary</span>
                ${source('speech')}
                ${source('lyrics')}
            </div>
        </div>`;
}

// ---------------------------------------------------------------------------
// Tutorial controller
// ---------------------------------------------------------------------------

// What the tutorial is showing right now. `flipped` is derived from the
// current step rather than owned: the step list decides which face is up, and
// renderCard()/flipCardFace() read this to drive the real card CSS.
const state = {
    mode: 'speech',
    cardHeight: null,
    stepIndex: 0,
    flipped: false,
    meaningIndex: 0,
    exampleIndex: 0,
    activeNote: -1,
    flipping: false,
    demoKey: '',
};

// Source selection precedes automatic onboarding. Explicit replays without
// a chosen source use Speech; Lyrics extends the same card explanations.
function selectedTutorialMode() {
    if (window.activeArtist || window.playlistLiveActive?.()) return 'lyrics';
    if (document.getElementById('step1')?.classList.contains('source-speech-active')) return 'speech';
    return null;
}

// Most needed first. Each chapter ends with the choice to start studying, so
// stopping after the card is a normal way through, not a skip.
const TUTORIAL_CHAPTERS = [
    { id: 'card', label: 'Studying a card' },
    { id: 'smartSkip', label: 'Smart Skip' },
    { id: 'modes', label: 'Speech or music' },
];

function tutorialSteps() {
    return [
        { kind: 'card', deck: state.mode, face: 'front', chapter: 'card' },
        { kind: 'card', deck: state.mode, face: 'back', chapter: 'card' },
        { kind: 'page', page: 'smartSkip', chapter: 'smartSkip' },
        { kind: 'page', page: 'modes', chapter: 'modes' },
    ];
}

function currentStep() {
    return tutorialSteps()[state.stepIndex] || null;
}

function chapterById(id) {
    return TUTORIAL_CHAPTERS.find(chapter => chapter.id === id) || null;
}

// The chapter the next step opens, or null while this one continues.
function nextChapter() {
    const steps = tutorialSteps();
    const step = steps[state.stepIndex];
    const next = steps[state.stepIndex + 1];
    return step && next && next.chapter !== step.chapter ? chapterById(next.chapter) : null;
}

const MOBILE_TUTORIAL_QUERY = '(max-width: 1180px)';

function isMobileTutorial() {
    return window.matchMedia?.(MOBILE_TUTORIAL_QUERY).matches === true;
}

// The speech deck carries no card of its own: which one it shows depends on
// the language being taught, so it is filled in here.
function deckById(id) {
    const speech = TUTORIAL_DECKS.find(d => d.id === 'speech');
    if (id === 'speech') return { ...speech, card: tutorialAdapter().speechCard };
    const lyrics = TUTORIAL_DECKS.find(d => d.id === 'lyrics');
    const forLyrics = note => ({ ...note,
        ...(note.lyricsText ? { text: note.lyricsText } : {}),
        ...(note.lyricsTitle ? { title: note.lyricsTitle } : {}) });
    // Shared meanings and examples first; the song-specific button follows the
    // line it belongs to.
    const shared = speech.faces.back.notes.map(forLyrics);
    const credit = shared.findIndex(note => note.anchor === '.example-song-credit');
    const back = [...shared.slice(0, credit + 1), ...lyrics.faces.back.notes, ...shared.slice(credit + 1)];
    return { ...lyrics, faces: {
        front: { ...speech.faces.front, title: 'The front of a Music card', notes: speech.faces.front.notes.map(forLyrics) },
        back: { ...speech.faces.back, title: 'The back of a Music card',
            blurb: 'The meanings and examples come from the songs you chose.', notes: back },
    } };
}

function currentDeck() {
    const step = currentStep();
    return step && step.kind === 'card' ? deckById(step.deck) : null;
}

function currentCard() {
    const deck = currentDeck();
    return deck ? REPLICA_CARDS[deck.card] : null;
}

// A card face or a page: whichever is on stage owns the title, the summary
// and the notes. This is the whole reason flipping re-renders the notes.
function stepFace(step) {
    if (!step) return null;
    return step.kind === 'page' ? TUTORIAL_PAGES[step.page] : deckById(step.deck).faces[step.face];
}

function currentFace() {
    return stepFace(currentStep());
}

// Meanings in the order the card draws them: most common first.
function orderedMeanings(card) {
    return [...(card?.meanings || [])].sort((a, b) => (Number(b.pct) || 0) - (Number(a.pct) || 0));
}

// The row the tour taps to show a change of meaning: the second most common.
function altMeaningIndex() {
    const card = currentCard();
    const alt = orderedMeanings(card)[1];
    return card ? card.meanings.indexOf(alt) : -1;
}

// The meaning the card opens on, as the card data says.
function selectedMeaning(card) {
    return card?.meanings?.[card.defaultMeaningIndex || 0] || null;
}

// Rows are drawn most common first (card-replica.js renderMeaningRows), so one
// note per row, in that order, names each meaning the way the card shows it.
function meaningRowNotes(card, side) {
    const ordered = [...(card?.meanings || [])]
        .sort((a, b) => (Number(b.pct) || 0) - (Number(a.pct) || 0));
    return ordered.map((meaning, i) => {
        const gloss = `“${esc(meaning.translation)}”`;
        const last = i === ordered.length - 1 && ordered.length > 2;
        return {
            side,
            find: stage => stage.querySelectorAll('.meanings-scroll .meaning-row')[i],
            title: i === 0 ? 'The most common meaning'
                : last ? 'The least common meaning' : 'The next meaning',
            text: i === 0
                ? `${gloss} is the meaning you will meet most often. The shaded line, when there is one, says when it is used.`
                : `${gloss} is ${last ? 'the rarest meaning of this word' : 'a less common meaning of the same word'}. Tap its row to see an example of it.`,
        };
    });
}

// Left column first, then right, so each note sits on the same side as the
// element it explains; a closing note ends the face.
function stepNotes(step) {
    const face = stepFace(step);
    if (!face) return [];
    const card = step.kind === 'card' ? REPLICA_CARDS[deckById(step.deck).card] : null;
    const notes = face.notes
        .flatMap(note => (note.rows ? meaningRowNotes(card, note.side) : [note]))
        .filter(note => !note.requires || tutorialAdapter()[note.requires])
        .filter(note => !note.when || note.when(card));
    const body = notes.filter(n => !n.closing);
    return [...body.filter(n => n.side !== 'right'), ...body.filter(n => n.side === 'right'),
        ...notes.filter(n => n.closing)];
}

function orderedNotes() {
    return stepNotes(currentStep());
}

// Progress counts the annotations in the current chapter only, so each
// chapter reads as its own short sequence.
function tutorialStepPosition(noteIndex = state.activeNote) {
    const steps = tutorialSteps();
    const chapter = steps[state.stepIndex]?.chapter;
    let before = 0;
    let total = 0;
    steps.forEach((step, i) => {
        if (step.chapter !== chapter) return;
        const weight = stepNotes(step).length;
        total += weight;
        if (i < state.stepIndex) before += weight;
    });
    const within = Math.max(0, Math.min(noteIndex, Math.max(0, orderedNotes().length - 1)));
    return { current: before + within + 1, total };
}

// Full rebuild — used when the deck changes or a page comes on stage. A page
// sits in the card's own box, so moving between them never shifts the layout.
function renderCard() {
    const stage = document.getElementById('cardTutorialStage');
    if (!stage) return;
    const step = currentStep();
    state.flipping = false;
    state.demoKey = '';
    clearDemoTimers();

    if (step.kind === 'page') {
        stage.innerHTML = `<div class="card-replica tutorial-page-replica">${TUTORIAL_PAGES[step.page].html(tutorialAdapter())}</div>`;
    } else {
        stage.innerHTML = replicaCardHTML(currentCard(), {
            flipped: state.flipped,
            meaningIndex: state.meaningIndex,
            exampleIndex: state.exampleIndex,
        });
        wireBack(stage);
    }
    // On a phone the full-size card scrolls above the lesson controls.
    renderFaceCopy();
    renderNotes();
    syncContinueButton();
    fitCardToContent();
    markAnchors();
    // A face starts blank; its first element fades in a beat later so the
    // card visibly builds rather than appearing complete.
    if (step.kind === 'card') {
        stage.querySelectorAll('.card-tutorial-anchored:not(.card-back)').forEach(el =>
            el.classList.add('card-tutorial-unrevealed'));
        setTimeout(syncReveal, 60);
    }
}

// Sense and example changes replace only the back face, leaving the .card
// element (and therefore its flip transform) untouched — the same division of
// labour as the live app, where updateCard() rewrites #backContent rather than
// the card around it.
function refreshBack() {
    const stage = document.getElementById('cardTutorialStage');
    const back = stage?.querySelector('.card-back');
    if (!stage || !back) return;
    const meaningsScrollTop = back.querySelector('.meanings-scroll')?.scrollTop || 0;
    back.outerHTML = renderBack(currentCard(), state.meaningIndex, state.exampleIndex);
    wireBack(stage);
    fitCardToContent();
    stage.querySelector('.meanings-scroll').scrollTop = meaningsScrollTop;
    markAnchors();
}

// Flipping is a face change, so the annotations change with it: new copy, new
// numbered set, badges re-placed on the side now showing.
// Turn the card that is already on stage, rather than rebuilding it. Toggling
// the class is what lets the real 0.6s flip transition play.
function flipCardFace(mobileNote = 0) {
    const stage = document.getElementById('cardTutorialStage');
    const cardEl = stage?.querySelector('.card');
    if (!cardEl) return;

    state.activeNote = Math.min(mobileNote, Math.max(0, orderedNotes().length - 1));
    state.demoKey = '';
    state.flipping = true;
    cardEl.classList.toggle('flipped', state.flipped);

    renderFaceCopy();
    renderNotes();
    syncFlipButton();
    syncContinueButton();
    markAnchors();
    // Re-place once the transform has settled, so boxes are measured flat.
    setTimeout(() => {
        state.flipping = false;
        fitCardToContent();
        markAnchors();
    }, 640);
}

// Handlers for everything inside the back face. Called again after every
// back-face rebuild, since those nodes are replaced wholesale.
function wireBack(stage) {
    stage.querySelectorAll('.meaning-row, .sentence[data-replica-cycle="1"]').forEach(control => {
        control.tabIndex = 0;
        control.setAttribute('role', 'button');
        control.setAttribute('aria-label', control.classList.contains('meaning-row')
            ? `Choose meaning: ${control.querySelector('.meaning-row-translation')?.textContent.trim()}` : 'Show another example');
        control.addEventListener('keydown', event => {
            if (event.target !== control || !['Enter', ' '].includes(event.key)) return;
            event.preventDefault(); control.click();
        });
    });
    wireReplicaBack(stage, {
        onSelectMeaning: idx => {
            state.meaningIndex = idx;
            state.exampleIndex = 0;
            refreshBack();
        },
        onCycleExample: () => {
            state.exampleIndex += 1;
            refreshBack();
        },
        onLayoutChange: markAnchors,
    });
}

function syncFlipButton() {
    const btn = document.getElementById('cardTutorialFlip');
    if (!btn) return;
    btn.textContent = state.flipped ? 'Flip to the front' : 'Flip to the back';
}

// Where the tour stands: the note showing, whether it ends its chapter, and
// what pressing Next will do. Both layouts label their buttons from this.
function tourPosition() {
    const steps = tutorialSteps();
    const step = steps[state.stepIndex];
    const notes = orderedNotes();
    const index = Math.max(0, Math.min(state.activeNote, notes.length - 1));
    const next = steps[state.stepIndex + 1];
    const lastNote = index >= notes.length - 1;
    return {
        step, index, lastNote,
        finished: lastNote && !next,
        chapterEnd: lastNote && Boolean(next) && next.chapter !== step.chapter,
        turningSameCard: Boolean(next) && next.kind === 'card' && step.kind === 'card' && next.deck === step.deck,
    };
}

// One button, one job: go to the next step. Its label says what that step is,
// so the reader always knows what pressing it will do.
// On desktop it walks the notes first, one at a time, and only once the last
// note on this face is showing does it flip the card or move on. At the end
// of a chapter a second button offers to stop there and study.
function syncContinueButton() {
    const btn = document.getElementById('cardTutorialContinue');
    const actions = document.getElementById('cardTutorialDesktopActions');
    if (!btn) return;
    const ready = !isMobileTutorial() && Boolean(currentStep());
    btn.hidden = !ready;
    if (actions) actions.hidden = !ready;
    if (!ready) return;

    const at = tourPosition();
    btn.textContent = !at.lastNote ? 'Next →'
        : at.finished ? 'Start studying'
        : at.chapterEnd ? `Next: ${nextChapter().label} →`
        : at.turningSameCard ? 'Flip the card over →'
        : 'Next →';
    btn.classList.remove('is-secondary');
    const finish = document.getElementById('cardTutorialFinish');
    if (finish) finish.hidden = !at.chapterEnd;

    const prev = document.getElementById('cardTutorialPrev');
    if (prev) prev.hidden = state.stepIndex === 0 && at.index === 0;
    const progress = document.getElementById('cardTutorialDesktopProgress');
    if (progress) {
        const position = tutorialStepPosition(at.index);
        progress.textContent = `${position.current} of ${position.total}`;
    }
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
// Both faces share the available card box. Opening meanings and changing
// examples cannot grow it; compact layouts also reserve room for the coach.
function tutorialCardHeight() {
    if (!isMobileTutorial() || window.innerWidth > 700) {
        const pane = document.querySelector('#cardTutorialBody .card-tutorial-columns');
        const actions = document.getElementById('cardTutorialDesktopActions');
        const column = document.querySelector('#cardTutorialBody .card-tutorial-stage-col');
        const compact = isMobileTutorial();
        if (pane && column) {
            if (state.cardHeight !== null) return state.cardHeight;
            const styles = getComputedStyle(pane);
            const padding = parseFloat(styles.paddingTop) + parseFloat(styles.paddingBottom);
            const actionStyle = actions ? getComputedStyle(actions) : null;
            const footer = compact ? 0 : actions.offsetHeight + parseFloat(actionStyle.marginTop || 0)
                + parseFloat(actionStyle.marginBottom || 0) + parseFloat(getComputedStyle(column).gap);
            state.cardHeight = Math.max(80, Math.min(860, Math.floor(pane.clientHeight - padding - footer - 8)));
            return state.cardHeight;
        }
        return Math.max(80, Math.min(860, window.innerHeight - 160));
    }
    const pane = document.querySelector('#cardTutorialBody .card-tutorial-columns');
    const coach = document.getElementById('cardTutorialMobileCoach');
    if (!pane || !coach?.cloneNode) return pane ? Math.min(760, Math.max(160, pane.clientHeight - 18)) : 440;
    if (state.cardHeight !== null) return state.cardHeight;
    // Reserve the tallest explanation once, so changing steps cannot move
    // the card's bottom or the navigation on a phone. The coach is measured
    // at the width it really has (the body less its padding, not the pane's),
    // and the last note of a chapter is measured in its two-button layout.
    const body = document.getElementById('cardTutorialBody');
    const bodyStyle = getComputedStyle(body);
    const coachWidth = body.clientWidth - parseFloat(bodyStyle.paddingLeft) - parseFloat(bodyStyle.paddingRight);
    const probe = coach.cloneNode(true);
    probe.hidden = false;
    Object.assign(probe.style, {position: 'fixed', visibility: 'hidden', left: '-10000px',
        top: '0', bottom: 'auto', right: 'auto', width: `${coachWidth}px`, height: 'auto', minHeight: '0'});
    probe.querySelector('#cardTutorialMobileBack').hidden = false;
    coach.parentElement.appendChild(probe);
    let tallest = 0;
    const steps = tutorialSteps();
    steps.forEach((step, i) => {
        const notes = stepNotes(step);
        const endsChapter = steps[i + 1]?.chapter !== step.chapter;
        notes.forEach((note, n) => {
            probe.dataset.end = endsChapter && n === notes.length - 1 ? '1' : '';
            probe.querySelector('#cardTutorialMobileProgress').textContent = 'Step 13 of 13 · back of card';
            probe.querySelector('#cardTutorialMobileTitle').textContent = note.title;
            probe.querySelector('#cardTutorialMobileText').innerHTML = tutorialText(note.text);
            tallest = Math.max(tallest, probe.offsetHeight);
        });
    });
    probe.remove();
    body.style.setProperty('--tutorial-coach-h', `${Math.ceil(tallest)}px`);
    const paneStyle = getComputedStyle(pane);
    const panePadding = parseFloat(paneStyle.paddingTop) + parseFloat(paneStyle.paddingBottom);
    const coachNow = coach.hidden ? 0 : coach.offsetHeight;
    state.cardHeight = Math.min(760, Math.max(160, pane.clientHeight + coachNow - Math.max(tallest, coachNow) - panePadding));
    return state.cardHeight;
}

function fitCardToContent() {
    const inner = document.querySelector('#cardTutorialStage .card-replica');
    if (!inner) return;
    inner.style.removeProperty('--replica-card-scale');
    // Measure every step's summary so the header never changes the card's budget.
    const intro = document.getElementById('cardTutorialIntro');
    if (!isMobileTutorial() && intro?.cloneNode) {
        const probe = intro.cloneNode(true);
        Object.assign(probe.style, {position: 'fixed', visibility: 'hidden', left: '-10000px',
            top: '0', bottom: 'auto', right: 'auto', width: `${intro.clientWidth}px`, minHeight: '0'});
        intro.parentElement.appendChild(probe);
        let tallest = 0;
        tutorialSteps().forEach(step => {
            probe.innerHTML = bannerHTML(step);
            tallest = Math.max(tallest, probe.offsetHeight);
        });
        probe.remove();
        intro.style.minHeight = `${tallest}px`;
    }
    let height = tutorialCardHeight();
    // Everything on a face must be on screen. If a face's content is taller
    // than the box it has (a narrow phone wraps rows), shrink the whole card
    // to fit rather than cut a row off; below 70% the page scrolls instead.
    const measureNeed = () => {
        let need = 0;
        inner.querySelectorAll('.card-face, .tutorial-page').forEach(face => {
            // The back's details box scrolls on its own, so its overflow does not
            // reach the face: add what is hidden in it to the face's own height.
            const details = face.querySelector('.card-details');
            const hidden = details ? Math.max(0, details.scrollHeight - details.clientHeight) : 0;
            need = Math.max(need, face.scrollHeight + hidden);
            face.scrollTop = 0;
            if (details) details.scrollTop = 0;
        });
        return need;
    };
    // A card that must shrink is laid out at stage width ÷ scale, so after the
    // transform it still spans the stage rather than sitting in a narrow
    // strip with empty margins. A wider card wraps fewer rows and so needs
    // less height, which can raise the scale: settle the two together.
    const phoneStage = window.innerWidth <= 700 ? document.getElementById('cardTutorialStage') : null;
    const stageWidth = phoneStage?.clientWidth || 0;
    let need = 0;
    let scale = 1;
    inner.style.setProperty('--replica-card-scale', '1');
    for (let pass = 0; pass < (stageWidth ? 4 : 1); pass++) {
        if (stageWidth) inner.style.setProperty('--replica-layout-w', `${Math.round(stageWidth / scale)}px`);
        inner.style.setProperty('--replica-card-h', `${height}px`);
        need = measureNeed();
        const next = need > height + 1 ? Math.max(0.7, height / need) : 1;
        if (Math.abs(next - scale) < 0.01) break;
        scale = next;
    }
    inner.style.setProperty('--replica-card-scale', '1');
    if (need > height + 1) {
        // Give the card the room its content needs, then shrink the whole
        // card back down to the room there is (never below 70%).
        const finalScale = Math.max(0.7, height / need);
        inner.style.setProperty('--replica-card-h', `${Math.ceil(need)}px`);
        inner.style.setProperty('--replica-card-scale', String(finalScale));
        if (stageWidth) inner.style.setProperty('--replica-layout-w', `${Math.round(stageWidth / finalScale)}px`);
    } else if (stageWidth) {
        inner.style.setProperty('--replica-layout-w', `${stageWidth}px`);
    }
    const compactDesktop = window.innerWidth > 700 && window.innerWidth <= 1180;
    const pane = document.querySelector('#cardTutorialBody .card-tutorial-columns');
    const width = Math.min(640, (compactDesktop ? height * .85 : Math.max(440, height * .78)), (pane?.clientWidth || window.innerWidth) * (compactDesktop ? .95 : .4));
    document.getElementById('cardTutorialBody')?.style.setProperty('--tutorial-card-width', `${Math.round(width)}px`);
}

function markAnchors() {
    const stage = document.getElementById('cardTutorialStage');
    if (!stage) return;
    stage.querySelectorAll('.card-tutorial-anchored').forEach(el => {
        el.classList.remove('card-tutorial-anchored', 'is-annotation-active');
        delete el.dataset.cardTutorialNote;
    });
    orderedNotes().forEach((note, i) => {
        const found = note.find ? [].concat(note.find(stage))
            : note.all ? [...stage.querySelectorAll(note.anchor)]
            : [stage.querySelector(note.anchor)];
        found.filter(Boolean).forEach(target => {
            target.classList.add('card-tutorial-anchored');
            // One element can be the subject of several notes.
            const seen = target.dataset.cardTutorialNote ? target.dataset.cardTutorialNote.split(',') : [];
            target.dataset.cardTutorialNote = [...seen, String(i)].join(',');
        });
    });
    if (state.activeNote >= 0) setActiveNote(state.activeNote);
    else syncReveal();
}

// Both faces start blank and each element appears as its note comes up.
// Elements keep their space (opacity, not display) so the card does not
// reflow as they arrive. Going back keeps everything already seen. The whole
// back face is itself annotated (the closing note), so it is never hidden.
function syncReveal() {
    const stage = document.getElementById('cardTutorialStage');
    if (!stage) return;
    const step = currentStep();
    const building = step?.kind === 'card';
    stage.querySelectorAll('.card-tutorial-anchored').forEach(el => {
        const index = Math.min(...el.dataset.cardTutorialNote.split(',').map(Number));
        if (el.classList.contains('card-back')) return;
        el.classList.toggle('card-tutorial-unrevealed', building && index > state.activeNote);
    });
    // The capsule that holds the kind-of-word pill and the dictionary form
    // belongs to the pill: it should not sit there empty before the pill does.
    const pair = stage.querySelector('.front-lemma-pair');
    const pill = pair?.querySelector('.card-tutorial-anchored.card-pos');
    if (pair) pair.classList.toggle('card-tutorial-unrevealed', building && Boolean(pill?.classList.contains('card-tutorial-unrevealed')));
    positionRing();
}

// The spotlight is a ring drawn over the card rather than an outline on the
// element. An outline is clipped by every overflow:hidden ancestor (the card
// faces, the sense box) and by the card edge, which is how it used to go
// missing on one side or run off the screen. The ring is measured from the
// element's box and clamped inside the card, so it is always whole.
function positionRing() {
    const stage = document.getElementById('cardTutorialStage');
    if (!stage) return;
    let ring = stage.querySelector('.card-tutorial-ring');
    const targets = [...stage.querySelectorAll('.card-tutorial-anchored.is-annotation-active')]
        .filter(el => el.getBoundingClientRect().width > 0);
    const target = targets[0];
    const card = stage.querySelector('.card-replica');
    // While a demo sheet covers the card, the sheet is the thing on show.
    if (!target || !card || state.flipping || stage.querySelector('.tutorial-demo-sheet')
        || target.classList.contains('card-tutorial-unrevealed')) {
        if (ring) ring.hidden = true;
        return;
    }
    if (!ring) {
        ring = document.createElement('div');
        ring.className = 'card-tutorial-ring';
        ring.setAttribute('aria-hidden', 'true');
        stage.appendChild(ring);
    }
    const frame = stage.getBoundingClientRect();
    const bounds = card.getBoundingClientRect();
    // A headword's box is the full card width; ring the word, not the row.
    let box = target.getBoundingClientRect();
    if (targets.length > 1) {
        const rects = targets.map(el => el.getBoundingClientRect());
        const left = Math.min(...rects.map(r => r.left));
        const top = Math.min(...rects.map(r => r.top));
        const right = Math.max(...rects.map(r => r.right));
        const bottom = Math.max(...rects.map(r => r.bottom));
        box = { left, top, right, bottom, width: right - left, height: bottom - top };
    } else if (target.matches('.card-word')) {
        const range = document.createRange();
        range.selectNodeContents(target);
        const text = range.getBoundingClientRect();
        if (text.width) box = { left: text.left - 8, right: text.right + 8, top: box.top, bottom: box.bottom, width: text.width, height: box.height };
    }
    if (!box.width || !box.height) { ring.hidden = true; return; }
    const pad = 5;
    const edge = 3;
    const left = Math.max(box.left - pad, bounds.left + edge);
    const top = Math.max(box.top - pad, bounds.top + edge);
    const right = Math.min(box.right + pad, bounds.right - edge);
    const bottom = Math.min(box.bottom + pad, bounds.bottom - edge);
    // Page zoom ("Bigger" text) and the phone's scale transform change the
    // viewport size of a CSS pixel; ring coordinates are in the stage's own.
    const scale = (stage.offsetWidth && frame.width) ? frame.width / stage.offsetWidth : 1;
    ring.hidden = false;
    ring.style.left = `${(left - frame.left) / scale}px`;
    ring.style.top = `${(top - frame.top) / scale}px`;
    ring.style.width = `${Math.max(0, right - left) / scale}px`;
    ring.style.height = `${Math.max(0, bottom - top) / scale}px`;
    const radius = parseFloat(getComputedStyle(target).borderTopLeftRadius) || 0;
    ring.style.borderRadius = `${Math.max(8, radius + pad)}px`;
}

// Hovering either a badge or its note lights up both, plus the element itself.
function setActiveNote(index) {
    state.activeNote = index;
    enterNoteDemo(index);
    renderNotes();
    renderSequenceProgress();
    const root = document.getElementById('cardTutorialModal');
    if (!root) return;
    root.querySelectorAll('.card-tutorial-note').forEach((n) => {
        n.classList.toggle('is-active', Number(n.dataset.note) === index);
    });
    let active = null;
    root.querySelectorAll('.card-tutorial-anchored').forEach((el) => {
        const on = el.dataset.cardTutorialNote.split(',').map(Number).includes(index);
        el.classList.toggle('is-annotation-active', on);
        if (on) active = el;
    });
    // A phone cannot show a dense card whole — `tem` wants more height than the
    // screen has once its rows wrap. Rather than clip it, bring whatever is
    // being explained into view inside its own scroll region. `nearest` keeps
    // this to the smallest scroll that works and never moves the page.
    if (active) {
        const rows = active.closest('.meaning-pos-rows');
        const group = rows?.closest('.meaning-pos-section');
        if (group && !group.classList.contains('is-open')) {
            group.classList.add('is-open');
            group.querySelector('.pos-section-head')?.setAttribute('aria-expanded', 'true');
        }
        keepInView(active);
    }
    syncReveal();
    renderMobileCoach();
    if (isMobileTutorial()) fitCardToContent();
    positionRing();
    settleRing();
    syncContinueButton();
    scheduleNextHint();
}

// Rows and groups animate open and the card re-fits after fonts and flips, so
// the first measurement can be taken mid-move. Measure again as things settle.
let _ringSettle = [];
function settleRing() {
    _ringSettle.forEach(clearTimeout);
    _ringSettle = [120, 300, 700].map(ms => setTimeout(positionRing, ms));
}

// Whatever moves the target (a row opening, a font arriving, a flip, the page
// zooming) the ring follows: while the tutorial is open it is re-measured
// every 100ms, which costs one box read.
let _ringWatch = null;
function watchRing() {
    clearInterval(_ringWatch);
    _ringWatch = setInterval(positionRing, 100);
}

// Bring the element being explained into view by scrolling the tutorial's own
// body only. scrollIntoView() would also scroll the card faces, which clip
// their overflow, and push the headword out of the card.
function keepInView(el) {
    // On a phone the columns scroll; on a desktop the body does.
    const columns = document.querySelector('#cardTutorialBody .card-tutorial-columns');
    const body = document.getElementById('cardTutorialBody');
    const scroller = [columns, body].find(node => node && node.scrollHeight > node.clientHeight + 1);
    if (!scroller || !el.getBoundingClientRect) return;
    const view = scroller.getBoundingClientRect();
    const box = el.getBoundingClientRect();
    if (box.top < view.top + 8) scroller.scrollTop -= view.top + 8 - box.top;
    else if (box.bottom > view.bottom - 8) scroller.scrollTop += box.bottom - view.bottom + 8;
}

// ---------------------------------------------------------------------------
// Demonstrations
// ---------------------------------------------------------------------------
//
// A few notes describe something the card *does* rather than something it
// shows. Those notes carry `demo`, and on arriving at one the tour performs
// the action itself: it changes the meaning, cycles the example, opens the
// sheets. The same controls stay live, so the reader can do it again. Arriving
// at any other note puts the card back as it was.

let _demoTimers = [];

function clearDemoTimers() {
    _demoTimers.forEach(clearTimeout);
    _demoTimers = [];
}

function later(ms, fn) {
    _demoTimers.push(setTimeout(fn, ms));
}

function closeDemoSheet() {
    document.querySelectorAll('#cardTutorialStage .tutorial-demo-sheet').forEach(el => el.remove());
}

function closeLookupDemo() {
    const stage = document.getElementById('cardTutorialStage');
    stage?.querySelectorAll('.lookup-sheet').forEach(sheet => { sheet.hidden = true; });
    stage?.querySelectorAll('.lookup-sheet-icon').forEach(icon => {
        icon.classList.remove('is-armed-outbound');
        icon.setAttribute('aria-expanded', 'false');
        icon.querySelector('.outbound-leave-btn')?.setAttribute('hidden', '');
    });
}

function closeDemo() {
    clearDemoTimers();
    closeDemoSheet();
    closeLookupDemo();
}

const RARE_POS_ORDER = ['NOUN', 'VERB', 'ADJ', 'ADV'];

// Markup follows the live sheets (flashcards.js ensureRareUsesModal and
// renderRareSenseGroups, knowledge.js renderKnowledgeOverview) class for
// class, so the real stylesheet draws them.
function rareSheetHTML(card) {
    const byPos = new Map();
    (card.rareUses || []).forEach(item => {
        const pos = String(item.pos || 'OTHER').toUpperCase();
        if (!byPos.has(pos)) byPos.set(pos, []);
        byPos.get(pos).push(item);
    });
    const order = [...byPos.keys()].sort((a, b) => {
        const ia = RARE_POS_ORDER.indexOf(a);
        const ib = RARE_POS_ORDER.indexOf(b);
        return (ia < 0 ? 99 : ia) - (ib < 0 ? 99 : ib);
    });
    const body = order.map(pos => {
        const accent = posAccentRgb(pos);
        const leaves = byPos.get(pos).map(item => {
            const example = item.example
                ? `<button type="button" class="rare-ex-btn" aria-expanded="false" aria-label="Show 1 example" data-count="1" onclick="toggleRareExamples(event, this)"><svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M21 12a8 8 0 0 1-11.6 7.1L4 20.5l1.5-4.6A8 8 0 1 1 21 12z"/></svg><span class="rare-ex-count">1</span></button>` : '';
            const panel = item.example
                ? `<div class="rare-ex-panel" hidden>
                    <div class="phrase-example phrase-example--compact" style="--sense-match-rgb: ${accent};">
                        <div class="phrase-example-target">${esc(item.example.target)}</div>
                        <div class="phrase-example-translation">${esc(item.example.english)}</div>
                    </div></div>` : '';
            return `<div class="other-uses-gloss-group"><div class="other-uses-leaf">
                <div class="rare-row"><div class="rare-row-text"><div class="other-uses-gloss">${esc(item.translation)}</div>
                ${item.context ? `<div class="phrase-context">${esc(item.context)}</div>` : ''}</div>${example}</div>${panel}
            </div></div>`;
        }).join('');
        const label = esc(posName(pos).replace(/^./, c => c.toUpperCase()));
        const collapsed = order.length > 1;
        return `<section class="other-uses-pos uses-section${collapsed ? ' is-collapsed' : ''}" style="--sense-match-rgb: ${accent};"><h4 class="other-uses-pos-heading"><button type="button" class="uses-section-toggle" aria-expanded="${!collapsed}" aria-controls="tutUses-${pos}" data-section-key="tut-${pos}" onclick="toggleUsesSection(event, this)"><span class="uses-section-label">${label}</span><span class="uses-section-count">· ${byPos.get(pos).length}</span><svg class="uses-section-chevron" viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M6 9l6 6 6-6"/></svg></button></h4><div class="uses-section-rows" id="tutUses-${pos}"${collapsed ? ' hidden' : ''}>${leaves}</div></section>`;
    }).join('');
    return `<div class="knowledge-overview-modal rare-uses-modal tutorial-demo-sheet" role="dialog" aria-label="Rare uses">
        <div class="knowledge-overview-sheet rare-uses-sheet">
            <header class="knowledge-overview-header">
                <div>
                    <h2>Less common uses of <span class="rare-uses-word">${esc(card.word)}</span></h2>
                </div>
                <button type="button" class="knowledge-overview-close" aria-label="Close rare uses" data-demo-close>×</button>
            </header>
            <div class="phrase-summary-scroll rare-uses-body uses-list">${body}</div>
        </div>
    </div>`;
}

function reviewSheetHTML(card) {
    const rows = orderedMeanings(card);
    const accent = posAccentRgb(card.pos);
    const list = rows.map((meaning, i) => `<label class="knowledge-overview-row" data-demo-row="${i}">
            <span class="knowledge-overview-focus is-static">
                <span class="knowledge-overview-status" aria-label="Unmarked"></span>
                <span class="knowledge-overview-copy"><strong>${esc(meaning.translation)}</strong>${meaning.context ? `<small>${esc(meaning.context)}</small>` : ''}</span>
            </span>
            <input type="checkbox" class="knowledge-overview-checkbox" aria-label="Review ${esc(meaning.translation)} later">
        </label>`).join('');
    return `<div class="knowledge-overview-modal tutorial-demo-sheet" role="dialog" aria-label="Flag a meaning">
        <div class="knowledge-overview-sheet">
            <header class="knowledge-overview-header">
                <p class="knowledge-overview-hint">Know the word, but not every meaning? Select the meaning(s) you’d like to revisit, and future reviews will focus on those.</p>
                <button type="button" class="knowledge-overview-close" aria-label="Close" data-demo-close>×</button>
            </header>
            <div class="knowledge-overview-list"><section class="knowledge-overview-section">
                <div class="knowledge-overview-group" style="--sense-match-rgb: ${accent};">
                    <div class="knowledge-overview-group-head">
                        <span class="knowledge-overview-group-pos">${esc(posName(card.pos).replace(/^./, c => c.toUpperCase()))}</span>
                        ${card.lemma && String(card.lemma).toLowerCase() !== String(card.word || '').toLowerCase() ? `<span class="knowledge-overview-group-from">from</span><span class="knowledge-overview-group-lemma">${esc(card.lemma)}</span>` : ''}
                        <span class="knowledge-overview-group-count">0/${rows.length}</span>
                    </div>
                    <div class="knowledge-overview-rows">${list}</div>
                </div>
            </section></div>
        </div>
    </div>`;
}

function openDemoSheet(kind) {
    const replica = document.querySelector('#cardTutorialStage .card-replica');
    const card = currentCard();
    if (!replica || !card) return;
    closeLookupDemo();
    closeDemoSheet();
    replica.insertAdjacentHTML('beforeend', kind === 'rare' ? rareSheetHTML(card) : reviewSheetHTML(card));
    if (kind === 'review') updateDemoFlagCount();
    // The sheet covers the card from its top edge: on a short phone the pane
    // may be scrolled down to the links row, which would cut the sheet's head.
    keepInView(replica);
    positionRing();
}

// Tick the second meaning, the way a learner marks one to revisit.
function updateDemoFlagCount() {
    const stage = document.getElementById('cardTutorialStage');
    const rows = stage?.querySelectorAll('.tutorial-demo-sheet [data-demo-row]');
    if (!rows?.length) return;
    const flagged = [...rows].filter(row => row.classList.contains('is-selected')).length;
    const fraction = stage.querySelector('.knowledge-overview-trigger .ref-tile-fraction');
    if (fraction) fraction.textContent = `${flagged}/${rows.length}`;
}

function tickReviewRow() {
    const row = document.querySelector('#cardTutorialStage .tutorial-demo-sheet [data-demo-row="1"]')
        || document.querySelector('#cardTutorialStage .tutorial-demo-sheet [data-demo-row="0"]');
    if (!row) return;
    row.classList.add('is-selected');
    const box = row.querySelector('input');
    if (box) box.checked = true;
    const status = row.querySelector('.knowledge-overview-status');
    if (status) status.setAttribute('aria-label', 'Practice');
    updateDemoFlagCount();
}

function openLookupDemo({ arm = false } = {}) {
    closeDemoSheet();
    const stage = document.getElementById('cardTutorialStage');
    const sheet = stage?.querySelector('.lookup-sheet');
    if (!sheet) return;
    sheet.hidden = false;
    if (arm) armLookupIcon(sheet.querySelector('.lookup-sheet-icon'));
    positionRing();
}

function armLookupIcon(icon) {
    if (!icon) return;
    const leave = icon.querySelector('.outbound-leave-btn');
    const opening = !icon.classList.contains('is-armed-outbound');
    icon.parentElement.querySelectorAll('.lookup-sheet-icon').forEach(other => {
        if (other === icon) return;
        other.classList.remove('is-armed-outbound');
        other.querySelector('.outbound-leave-btn')?.setAttribute('hidden', '');
    });
    icon.classList.toggle('is-armed-outbound', opening);
    icon.setAttribute('aria-expanded', String(opening));
    if (leave) leave.hidden = !opening;
}

// Put the card back to the meaning and example it opened on.
function resetDemoSelection() {
    const card = currentCard();
    if (!card) return;
    const home = card.defaultMeaningIndex || 0;
    if (state.meaningIndex === home && state.exampleIndex === 0) return;
    state.meaningIndex = home;
    state.exampleIndex = 0;
    refreshBack();
}

function goToMeaning(index) {
    if (state.meaningIndex === index && state.exampleIndex === 0) return;
    state.meaningIndex = index;
    state.exampleIndex = 0;
    refreshBack();
}

// Called as a note becomes the active one. Re-entry for the same note (every
// re-render calls setActiveNote) must not start the demo again.
function enterNoteDemo(index) {
    const step = currentStep();
    const key = `${state.stepIndex}:${index}:${state.flipped ? 'b' : 'f'}`;
    if (state.demoKey === key) return;
    state.demoKey = key;
    closeDemo();
    if (!step || step.kind !== 'card' || !state.flipped) return;
    const note = orderedNotes()[index];
    const card = currentCard();
    if (!note || !card) return;

    const keepsSelection = note.demo === 'selectMeaning' || note.demo === 'cycleExample';
    if (!keepsSelection) resetDemoSelection();

    switch (note.demo) {
        case 'selectMeaning':
            resetDemoSelection();
            later(750, () => goToMeaning(altMeaningIndex()));
            break;
        case 'cycleExample': {
            const current = card.meanings[state.meaningIndex];
            if (!current || current.examples.length < 2) {
                const richest = card.meanings.reduce((best, m, i) =>
                    (m.examples.length > (card.meanings[best]?.examples.length || 0) ? i : best), 0);
                goToMeaning(richest);
            }
            const next = () => { state.exampleIndex += 1; refreshBack(); };
            later(800, next);
            later(2100, next);
            break;
        }
        case 'openRare':
            later(700, () => openDemoSheet('rare'));
            later(2100, () => {
                const details = document.querySelector('#cardTutorialStage .tutorial-demo-sheet details');
                if (details) details.open = true;
            });
            break;
        case 'openReview':
            later(700, () => openDemoSheet('review'));
            later(1900, tickReviewRow);
            break;
        case 'openLookup':
            later(600, () => openLookupDemo());
            break;
        case 'armLookup':
            later(100, () => openLookupDemo());
            later(900, () => armLookupIcon(document.querySelector('#cardTutorialStage .lookup-sheet-icon')));
            break;
        default:
    }
}

// The card's own controls work during the tour too.
function onStageClick(event) {
    const stage = document.getElementById('cardTutorialStage');
    if (!stage) return;
    const target = event.target;
    if (target.closest('[data-demo-close]')) {
        event.stopPropagation();
        closeDemoSheet();
        positionRing();
        return;
    }
    const row = target.closest('.tutorial-demo-sheet [data-demo-row]');
    if (row) {
        event.preventDefault();
        const on = !row.classList.contains('is-selected');
        row.classList.toggle('is-selected', on);
        const box = row.querySelector('input');
        if (box) box.checked = on;
        updateDemoFlagCount();
        return;
    }
    if (target.closest('.tutorial-demo-sheet')) return;
    if (target.closest('.ref-rare-uses-btn')) { openDemoSheet('rare'); return; }
    if (target.closest('.knowledge-overview-trigger')) { openDemoSheet('review'); return; }
    if (target.closest('.ref-lookup-btn')) {
        const sheet = stage.querySelector('.lookup-sheet');
        if (sheet) { closeDemoSheet(); sheet.hidden = !sheet.hidden; positionRing(); }
        return;
    }
    const icon = target.closest('.lookup-sheet-icon');
    if (icon && !target.closest('.outbound-leave-btn')) armLookupIcon(icon);
}

// A first-time reader can stall on a step not knowing the tour moves on with
// Next. After a few seconds on the same note, the Next button starts a clear,
// pulsing ring; any step restarts the wait.
const NEXT_HINT_DELAY_MS = 1800;
let _nextHintTimer = null;

function scheduleNextHint() {
    clearTimeout(_nextHintTimer);
    const buttons = ['cardTutorialContinue', 'cardTutorialMobileNext']
        .map(id => document.getElementById(id)).filter(btn => btn && !btn.disabled);
    buttons.forEach(btn => btn.classList.remove('is-hinting'));
    _nextHintTimer = setTimeout(() => {
        buttons.forEach(btn => btn.classList.add('is-hinting'));
    }, NEXT_HINT_DELAY_MS);
}

function clearNextHint() {
    clearTimeout(_nextHintTimer);
    document.querySelectorAll('.is-hinting').forEach(btn => btn.classList.remove('is-hinting'));
}

function renderMobileCoach() {
    const coach = document.getElementById('cardTutorialMobileCoach');
    if (!coach) return;
    const mobile = isMobileTutorial();
    const notes = orderedNotes();
    const index = Math.max(0, Math.min(state.activeNote, notes.length - 1));
    const note = notes[index];
    coach.hidden = !mobile || !note;
    if (coach.hidden) return;

    const progress = tutorialStepPosition(index);
    const at = tourPosition();
    // Progress stays with the current face, or the page, and annotation.
    const where = at.step.kind === 'page' ? chapterById(at.step.chapter).label
        : state.flipped ? 'back of card' : 'front of card';
    document.getElementById('cardTutorialMobileProgress').textContent =
        `Step ${progress.current} of ${progress.total} · ${where}`;
    document.getElementById('cardTutorialMobileTitle').innerHTML =
        esc(note.title);
    document.getElementById('cardTutorialMobileText').innerHTML = tutorialText(note.text);
    const back = document.getElementById('cardTutorialMobileBack');
    const next = document.getElementById('cardTutorialMobileNext');
    const finish = document.getElementById('cardTutorialMobileFinish');
    // A phone has room for two buttons. At a chapter's end they are the two
    // ways on — study now, or the next chapter — and Back steps aside.
    back.hidden = at.chapterEnd || (state.stepIndex === 0 && index === 0);
    back.disabled = false;
    if (finish) finish.hidden = !at.chapterEnd;
    coach.dataset.end = at.chapterEnd ? '1' : '';
    next.textContent = !at.lastNote ? 'Next'
        : at.finished ? 'Start studying'
        : at.chapterEnd ? `${nextChapter().label} →`
        : at.turningSameCard ? 'Flip over'
        : 'Continue';
}

// One note forwards or back, on either layout; past either end of a face it
// moves to the neighbouring step.
function moveTour(direction) {
    const step = currentStep();
    if (!step) return;
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

// The banner reads Section · Title — Text on one line: the section chip is
// beside it (renderSequenceProgress), this is the title and text. A page's
// title is its section, so it is not said twice.
function bannerHTML(step) {
    const face = stepFace(step);
    const lede = step.kind === 'page' ? ''
        : `<strong class="card-tutorial-lede">${tutorialText(face.title)}</strong> `;
    return `<p class="card-tutorial-blurb">${lede}${tutorialText(face.blurb)}</p>`;
}

function renderFaceCopy() {
    const host = document.getElementById('cardTutorialIntro');
    if (!host || !currentStep()) return;
    host.innerHTML = bannerHTML(currentStep());
}

function noteHTML(note, index) {
    return `
        <li class="card-tutorial-note" data-note="${index}">
            <div>
                <strong>${note.title}</strong>
                <span class="card-tutorial-note-copy">${tutorialText(note.text)}</span>
            </div>
        </li>`;
}

function renderNotes() {
    const left = document.getElementById('cardTutorialNotesLeft');
    const right = document.getElementById('cardTutorialNotesRight');
    if (!left || !right) return;

    const notes = orderedNotes();
    const leftHTML = [];
    const rightHTML = [];
    notes.forEach((note, i) => {
        (note.side === 'right' ? rightHTML : leftHTML).push(noteHTML(note, i));
    });

    left.innerHTML = `<ol class="card-tutorial-note-list">${leftHTML.join('')}</ol>`;
    right.innerHTML = `<ol class="card-tutorial-note-list">${rightHTML.join('')}</ol>`;

    document.getElementById('cardTutorialModal')
        ?.querySelectorAll('.card-tutorial-note')
        .forEach((el) => {
            const i = Number(el.dataset.note);
            // Every explanation is part of the tutorial and can be revisited directly.
            el.addEventListener('click', () => setActiveNote(i));
            {
                el.tabIndex = 0;
                el.setAttribute('role', 'button');
                el.addEventListener('keydown', event => {
                    if (event.key === 'Enter' || event.key === ' ') { event.preventDefault(); setActiveNote(i); }
                });
            }
        });
}

// ---------------------------------------------------------------------------
// Linear tutorial chapters
// ---------------------------------------------------------------------------

// The chapters double as the table of contents: any one can be opened
// directly, which is how a replay skips to the part it came for.
function renderChapters() {
    renderSequenceProgress();
}

function renderSequenceProgress() {
    const host = document.getElementById('cardTutorialSequence');
    if (!host) return;
    const step = currentStep();
    if (!step) return;
    const chapter = chapterById(step.chapter);
    // Phones show the count here, beside the chapter, instead of in the coach.
    const pos = tutorialStepPosition();
    host.innerHTML = `<div class="card-tutorial-chapters" aria-label="Tutorial section"><span class="card-tutorial-chapter is-current">${esc(chapter.label)}</span></div>`
        + `<span class="card-tutorial-phone-count" aria-label="Step ${pos.current} of ${pos.total}">${pos.current}/${pos.total}</span>`;
}

function goToChapter(id) {
    const index = tutorialSteps().findIndex(step => step.chapter === id);
    if (index >= 0) goToStep(index);
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
    const onStage = document.querySelector('#cardTutorialStage .card');
    // Only two faces of one card turn; a page, or a card after a page, is built.
    const turnsInPlace = index !== state.stepIndex && onStage
        && from && from.kind === 'card' && to.kind === 'card'
        && from.deck === to.deck && from.face !== to.face;

    state.stepIndex = index;
    state.flipped = to.kind === 'card' && to.face === 'back';

    renderSequenceProgress();
    const body = document.getElementById('cardTutorialBody');

    if (turnsInPlace) {
        flipCardFace(mobileNote);
        return;
    }

    state.meaningIndex = currentCard()?.defaultMeaningIndex || 0;
    state.exampleIndex = 0;
    state.activeNote = Math.min(mobileNote, Math.max(0, stepNotes(to).length - 1));
    renderCard();
    syncFlipButton();
    renderMobileCoach();
    if (body) body.scrollTop = 0;
}

function advanceStep() {
    if (state.stepIndex < tutorialSteps().length - 1) goToStep(state.stepIndex + 1);
    else finishTutorialLesson();
}

// ---------------------------------------------------------------------------
// Open / close
// ---------------------------------------------------------------------------

function finishTutorialLesson() {
    closeCardTutorial();
    const studying = !document.getElementById('appContent')?.classList.contains('hidden');
    const target = studying ? document.getElementById('flipBtn')
        : document.querySelector('#studySetStartBtn:not(:disabled)')
            || document.getElementById('standardSourceSpeechBtn');
    target?.scrollIntoView({ block: 'center' });
    target?.focus();
}

let _resizeHandler = null;

function openCardTutorial({ chapter = 'card' } = {}) {
    const modal = document.getElementById('cardTutorialModal');
    if (!modal) return;
    document.getElementById('resumeLastSetCard')?.remove();
    rememberCardTutorial();
    state.cardHeight = null;
    modal.classList.remove('hidden');
    // Replays start directly on the chosen mode's card.
    state.mode = tutorialAdapter().lyrics && selectedTutorialMode() === 'lyrics' ? 'lyrics' : 'speech';
    state.stepIndex = 0;
    watchRing();
    renderChapters();
    goToStep(Math.max(0, tutorialSteps().findIndex(step => step.chapter === chapter)));

    if (!_resizeHandler) {
        _resizeHandler = () => {
            state.cardHeight = null;
            if (isMobileTutorial() && state.activeNote < 0) state.activeNote = 0;
            fitCardToContent();
            markAnchors();
            syncContinueButton();
            renderMobileCoach();
        };
        window.addEventListener('resize', _resizeHandler);
    }
}

function openFirstRunCardTutorial() {
    if (['word', 'about', 'walkthrough'].includes(window.fluencyRoute?.kind)) return false;
    if (hasSeenCardTutorial()) return false;
    // The setup screen has a technical default before the learner chooses a
    // language. Do not mistake that for interest and launch the wrong tour.
    if (!explicitTutorialLanguageKey()) return false;
    if (!selectedTutorialMode()) return false;
    // Never stack the automatic tour over authentication, About, settings, or
    // another onboarding sheet. Permanent replay links remain available.
    if (document.querySelector('.modal:not(.hidden), .knowledge-overview-modal:not([hidden])')) {
        return false;
    }
    openCardTutorial();
    return true;
}

// The modal is layered over its opener: the study screen, the setup screen,
// or the help sheet. About never opens it — About links the walkthrough.
function closeCardTutorial() {
    const modal = document.getElementById('cardTutorialModal');
    if (!modal) return;
    modal.classList.add('hidden');
    clearNextHint();
    closeDemo();
    state.demoKey = '';
    clearInterval(_ringWatch);
    _ringSettle.forEach(clearTimeout);
    // Leave any Spotify playback the visitor started running — they pressed
    // play deliberately, and closing the tutorial shouldn't stop their music.
    if (_resizeHandler) {
        window.removeEventListener('resize', _resizeHandler);
        _resizeHandler = null;
    }
}

function setupCardTutorial() {
    const modal = document.getElementById('cardTutorialModal');
    if (!modal || modal.dataset.ready === '1') return;
    modal.dataset.ready = '1';

    document.getElementById('closeCardTutorialModal')?.addEventListener('click', closeCardTutorial);
    document.getElementById('cardTutorialStage')?.addEventListener('click', onStageClick);
    document.getElementById('cardTutorialFlip')?.addEventListener('click', () => flipCardFace(0));
    document.getElementById('cardTutorialContinue')?.addEventListener('click', () => moveTour(1));
    document.getElementById('cardTutorialPrev')?.addEventListener('click', () => moveTour(-1));
    document.getElementById('cardTutorialMobileBack')?.addEventListener('click', () => moveTour(-1));
    document.getElementById('cardTutorialMobileNext')?.addEventListener('click', () => moveTour(1));
    ['cardTutorialFinish', 'cardTutorialMobileFinish'].forEach(id =>
        document.getElementById(id)?.addEventListener('click', finishTutorialLesson));

    // Escape closes; left/right step through the tour like Back and Next.
    // Space deliberately does nothing: the tutorial owns the flip, so the card
    // only turns when the tour says so.
    document.addEventListener('keydown', (e) => {
        if (modal.classList.contains('hidden')) return;
        if (e.key === 'Escape') closeCardTutorial();
        else if (e.key === 'ArrowRight') moveTour(1);
        else if (e.key === 'ArrowLeft') moveTour(-1);
    });
}

document.addEventListener('DOMContentLoaded', setupCardTutorial);
if (document.readyState !== 'loading') setupCardTutorial();

window.openCardTutorial = openCardTutorial;
window.openFirstRunCardTutorial = openFirstRunCardTutorial;
window.closeCardTutorial = closeCardTutorial;
window.getCardTutorialProfile = tutorialAdapter;
window.getCardTutorialLanguageKey = explicitTutorialLanguageKey;
window.getCardTutorialMode = selectedTutorialMode;
window.getCardTutorialLanguages = () => Object.entries(TUTORIAL_LANGUAGE_ADAPTERS)
    .map(([key, adapter]) => ({ key, language: adapter.language }));
window.setCardTutorialLanguage = key => {
    tutorialLanguageOverride = TUTORIAL_LANGUAGE_ADAPTERS[key] ? key : null;
};
