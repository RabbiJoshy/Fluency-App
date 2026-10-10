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
    REPLICA_CARDS, esc, renderBack, replicaCardHTML, wireReplicaBack,
} from './card-replica.js?v=5e2c6e6b';


// Each language selects its own representative card and dictionary wording.
// The controller below remains shared, so another language needs only a card
// and one adapter entry instead of a forked tutorial.
// The Smart Skip examples are the ones its own page uses (fast-mode.js), so
// the tutorial and the setting never show a learner different words.
const TUTORIAL_LANGUAGE_ADAPTERS = {
    spanish: { language: 'Spanish', flag: '🇪🇸', speechCard: 'queSpeech', provider: 'SpanishDict', lyrics: true, usageShares: true,
        smartSkip: { forms: ['hablo', 'habló', 'hablar'], lookalike: 'chocolate' } },
    portuguese: { language: 'Portuguese', flag: '🇵🇹', speechCard: 'ptProvarSpeech', provider: 'Wiktionary', lyrics: false, usageShares: true,
        smartSkip: { forms: ['falo', 'falou', 'falar'], lookalike: 'hotel' } },
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
                        title: 'The meanings at a glance',
                        text: 'Meanings are grouped by kind of word, with the most common first.',
                    },
                    {
                        side: 'left',
                        anchor: '.meaning-row.is-current-sense',
                        title: 'The selected meaning',
                        text: 'Tap any meaning to change the example below. The shaded cue explains when that meaning is used.',
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
                        anchor: '.meaning-row.is-current-sense .sense-prominence-badge',
                        requires: 'usageShares',
                        title: 'How common this meaning is',
                        text: 'The bars show how often this meaning shows up in real speech. Tap them to read Dominant, Common, Uncommon, or Rare.',
                        lyricsText: 'The bars show how often this meaning shows up in your chosen songs. Tap them to read Dominant, Common, Uncommon, or Rare.',
                    },
                    {
                        side: 'right',
                        anchor: '.sentence',
                        title: 'A real example',
                        text: 'Each sentence matches the selected meaning; where there are several, tap it for the next. Beneath it is where it comes from: film or TV dialogue (IMDb), Tatoeba for contributed sentences, or {provider} for dictionary examples.',
                        lyricsText: 'Each lyric matches the selected meaning; where there are several, tap it for the next.',
                    },
                    {
                        side: 'right',
                        anchor: '.card-back',
                        closing: true,
                        title: 'Grade your answer',
                        text: 'Swipe right if you knew it, or left if you need practice: ← Needs practice · Got it →. The next card follows. On a computer, press Enter for Got it or X for Needs practice.',
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
                        anchor: '.card-ranking',
                        title: 'How common the word is',
                        text: 'Its place in the {language} deck, and how often it is said per million words. The most common words come first.',
                        lyricsText: 'Its place in your deck, and how many lines in your chosen songs contain it. The most common words come first.',
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
                        text: 'Here the word and dictionary form are both “{demoLemma}”. Inflected words can differ: {lemmaExample}. The small label tells you which dictionary entry to look up.',
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
                side: 'right',
                anchor: '.tutorial-page-forms',
                title: 'Word forms share a card',
                text: '{smartSkipForms} share one flashcard, so you learn the word once.',
            },
            {
                side: 'right',
                anchor: '.tutorial-page-lookalike',
                title: 'Look-alikes are skipped',
                text: 'Words that look and mean the same as in a language you know, like {smartSkipLookalike} in English. Tap Smart Skip to see every word it set aside; you can still study them.',
            },
        ],
        html: smartSkipPageHTML,
    },
    modes: {
        title: 'Speech or music',
        blurb: 'Choose where your words come from, and switch whenever you like.',
        notes: [
            {
                side: 'left',
                anchor: '.tutorial-page-topbar',
                title: 'Switch at any time',
                text: 'Tap the language name at the top, then Vocabulary, and choose Everyday speech or Your music.',
            },
            {
                side: 'right',
                anchor: '.tutorial-page-sources',
                title: 'Your progress comes with you',
                text: 'A word you learn in one counts in the other.',
            },
        ],
        html: modesPageHTML,
    },
};

function smartSkipPageHTML(adapter) {
    const { forms, lookalike } = adapter.smartSkip;
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
            <div class="tutorial-page-example tutorial-page-forms">
                <span class="tutorial-page-label">Combine word forms</span>
                <div class="tutorial-page-flow">
                    <span class="tutorial-page-words">${forms.map(word).join('')}</span>
                    <span class="tutorial-page-arrow" aria-hidden="true">→</span>
                    <span class="tutorial-page-result">1 card</span>
                </div>
            </div>
            <div class="tutorial-page-example tutorial-page-lookalike">
                <span class="tutorial-page-label">Skip look-alikes</span>
                <div class="tutorial-page-flow">
                    <span class="tutorial-page-words">${word(lookalike)}<span class="tutorial-page-gloss">English: ${esc(lookalike)}</span></span>
                    <span class="tutorial-page-arrow" aria-hidden="true">→</span>
                    <span class="tutorial-page-result is-skipped">Skipped</span>
                </div>
            </div>
        </div>`;
}

// The two sources in the app's own words (ui.js learningModeCopy), so the
// copy cannot drift from the picker it shows. The fallback is for tests.
function modesPageHTML(adapter) {
    const copy = window.learningModeCopy?.(tutorialLanguageKey()) || {
        speech: { label: 'Everyday speech', description: 'From films and TV shows.' },
        lyrics: { label: 'Your music', description: 'The words in the songs you choose.' },
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
    const forLyrics = note => (note.lyricsText ? { ...note, text: note.lyricsText } : note);
    // Shared meanings and examples first; only song-specific details are added.
    const back = [...speech.faces.back.notes.map(forLyrics), ...lyrics.faces.back.notes];
    return { ...lyrics, faces: {
        front: { ...speech.faces.front, title: 'The front of a Lyrics card', notes: speech.faces.front.notes.map(forLyrics) },
        back: { ...speech.faces.back, title: 'The back of a Lyrics card',
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

// Left column first, then right, so each note sits on the same side as the
// element it explains; a closing note ends the face.
function stepNotes(step) {
    const face = stepFace(step);
    if (!face) return [];
    const notes = face.notes.filter(note => !note.requires || tutorialAdapter()[note.requires]);
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
    cardEl.classList.toggle('flipped', state.flipped);

    renderFaceCopy();
    renderNotes();
    syncFlipButton();
    syncContinueButton();
    markAnchors();
    // Re-place once the transform has settled, so boxes are measured flat.
    setTimeout(() => {
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
    if (!pane || !coach?.cloneNode) return pane ? Math.min(440, Math.max(160, pane.clientHeight - 18)) : 440;
    if (state.cardHeight !== null) return state.cardHeight;
    // Reserve the tallest explanation once, so changing steps cannot move
    // the card's bottom or the navigation on a phone.
    const probe = coach.cloneNode(true);
    probe.hidden = false;
    Object.assign(probe.style, {position: 'fixed', visibility: 'hidden', left: '-10000px',
        top: '0', bottom: 'auto', right: 'auto', width: `${pane.clientWidth}px`, height: 'auto'});
    probe.querySelector('#cardTutorialMobileBack').hidden = false;
    coach.parentElement.appendChild(probe);
    let tallest = 0;
    tutorialSteps().forEach(step => stepNotes(step).forEach(note => {
        probe.querySelector('#cardTutorialMobileProgress').textContent = 'Step 13 of 13 · back of card';
        probe.querySelector('#cardTutorialMobileTitle').textContent = note.title;
        probe.querySelector('#cardTutorialMobileText').innerHTML = tutorialText(note.text);
        tallest = Math.max(tallest, probe.offsetHeight);
    }));
    probe.remove();
    state.cardHeight = Math.min(440, Math.max(160, pane.clientHeight + coach.offsetHeight - tallest - 18));
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
            const face = stepFace(step);
            probe.innerHTML = `<p class="card-tutorial-blurb"><strong class="card-tutorial-lede">${tutorialText(face.title)}</strong> ${tutorialText(face.blurb)}</p>`;
            tallest = Math.max(tallest, probe.offsetHeight);
        });
        probe.remove();
        intro.style.minHeight = `${tallest}px`;
    }
    const height = tutorialCardHeight();
    inner.style.setProperty('--replica-card-h', `${height}px`);
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
        const target = stage.querySelector(note.anchor);
        if (!target) return;
        target.classList.add('card-tutorial-anchored');
        target.dataset.cardTutorialNote = String(i);
    });
    if (state.activeNote >= 0) setActiveNote(state.activeNote);
}

// Hovering either a badge or its note lights up both, plus the element itself.
function setActiveNote(index) {
    state.activeNote = index;
    renderNotes();
    renderSequenceProgress();
    const root = document.getElementById('cardTutorialModal');
    if (!root) return;
    root.querySelectorAll('.card-tutorial-note').forEach((n) => {
        n.classList.toggle('is-active', Number(n.dataset.note) === index);
    });
    let active = null;
    root.querySelectorAll('.card-tutorial-anchored').forEach((el) => {
        const on = Number(el.dataset.cardTutorialNote) === index;
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
        active.scrollIntoView({ block: 'nearest', inline: 'nearest' });
    }
    renderMobileCoach();
    if (isMobileTutorial()) fitCardToContent();
    syncContinueButton();
    scheduleNextHint();
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

function renderFaceCopy() {
    const face = currentFace();
    const host = document.getElementById('cardTutorialIntro');
    if (!host) return;
    // The title is a lead-in to the summary, not a heading over it — one
    // line instead of two, because the card and its annotations have to share
    // the screen. No "Lyrics · Bad Bunny · back of card" line either: the tab
    // already says which deck, and the card in front of you already says
    // which side you are looking at.
    host.innerHTML = `
        <p class="card-tutorial-blurb">
            <strong class="card-tutorial-lede">${tutorialText(face.title)}</strong>
            ${tutorialText(face.blurb)}
        </p>`;
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
    const host = document.getElementById('cardTutorialSequence');
    if (!host) return;
    host.innerHTML = `<nav class="card-tutorial-chapters" aria-label="Tutorial chapters">${TUTORIAL_CHAPTERS.map(chapter =>
        `<button type="button" class="card-tutorial-chapter" data-chapter="${chapter.id}">${esc(chapter.label)}</button>`).join('')}</nav>`;
    renderSequenceProgress();
}

function renderSequenceProgress() {
    const current = currentStep()?.chapter;
    document.querySelectorAll('#cardTutorialSequence [data-chapter]').forEach(button => {
        const on = button.dataset.chapter === current;
        button.classList.toggle('is-current', on);
        if (on) button.setAttribute('aria-current', 'step');
        else button.removeAttribute('aria-current');
    });
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
        : document.querySelector('#rangeSelector .study-set-dot:not(:disabled)')
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
    document.getElementById('cardTutorialFlip')?.addEventListener('click', () => flipCardFace(0));
    document.getElementById('cardTutorialContinue')?.addEventListener('click', () => moveTour(1));
    document.getElementById('cardTutorialPrev')?.addEventListener('click', () => moveTour(-1));
    document.getElementById('cardTutorialMobileBack')?.addEventListener('click', () => moveTour(-1));
    document.getElementById('cardTutorialMobileNext')?.addEventListener('click', () => moveTour(1));
    ['cardTutorialFinish', 'cardTutorialMobileFinish'].forEach(id =>
        document.getElementById(id)?.addEventListener('click', finishTutorialLesson));
    document.getElementById('cardTutorialSequence')?.addEventListener('click', event => {
        const chapter = event.target.closest('[data-chapter]')?.dataset.chapter;
        if (chapter) goToChapter(chapter);
    });

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
