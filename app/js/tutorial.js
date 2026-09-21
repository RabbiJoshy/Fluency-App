// The card tutorial — for LEARNERS, people actually using the app.
//
// Not the walkthrough (walkthrough.js), which is a two-screen demo for
// visitors and opens from About. This one is opened by the "?" button, by the
// first-run prompt and by Settings → How to Study, and it teaches someone who
// is about to study: it starts from the setup screen they just used, steps
// through a card one element at a time, owns the flip, and explains Lyrics
// mode on its own slide before showing one. Desktop and phone are equal
// targets; the phone gets a coach sheet instead of note columns.
//
// The card itself is drawn by card-replica.js, which both features share.

import {
    REPLICA_CARDS, esc, renderBack, replicaCardHTML, wireReplicaBack, fitReplicaCard,
} from './card-replica.js?v=20260921ac';


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

const TUTORIAL_DECKS = [
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
// Tutorial controller
// ---------------------------------------------------------------------------

// What the tutorial is showing right now. `flipped` is derived from the
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

const MOBILE_TUTORIAL_QUERY = '(max-width: 700px)';

function isMobileTutorial() {
    return window.matchMedia?.(MOBILE_TUTORIAL_QUERY).matches === true;
}

// The speech deck carries no card of its own: which one it shows depends on
// the language being taught, so it is filled in here.
function deckById(id) {
    const deck = TUTORIAL_DECKS.find(d => d.id === id);
    return deck.id === 'speech' ? { ...deck, card: tutorialAdapter().speechCard } : deck;
}

function currentDeck() {
    const step = currentStep();
    return step && step.kind === 'card' ? deckById(step.deck) : null;
}

function currentCard() {
    return REPLICA_CARDS[currentDeck().card];
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
    const stage = document.getElementById('cardTutorialStage');
    if (!stage) return;
    const card = currentCard();

    stage.innerHTML = replicaCardHTML(card, {
        flipped: state.flipped,
        meaningIndex: state.meaningIndex,
        exampleIndex: state.exampleIndex,
    });

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
    const stage = document.getElementById('cardTutorialStage');
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
    const stage = document.getElementById('cardTutorialStage');
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
        if (isMobileTutorial()) {
            const finalIndex = Math.max(0, orderedNotes().length - 1);
            setActiveNote(Math.min(mobileNote, finalIndex));
        }
    }, 640);
}

// Handlers for everything inside the back face. Called again after every
// back-face rebuild, since those nodes are replaced wholesale.
function wireBack(stage) {
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

// One button, one job: go to the next step. Its label says what that step is,
// so the reader always knows what pressing it will do.
function syncContinueButton() {
    const btn = document.getElementById('cardTutorialContinue');
    if (!btn) return;
    const steps = tutorialSteps();
    const step = steps[state.stepIndex];
    // A break slide carries its own controls; the card's button would sit in a
    // column that is hidden behind it.
    const ready = !isMobileTutorial() && step && step.kind === 'card';
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
    fitReplicaCard(document.querySelector('#cardTutorialStage .card-replica'));
}


function markAnchors() {
    const stage = document.getElementById('cardTutorialStage');
    if (!stage) return;
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
    if (active) active.scrollIntoView({ block: 'nearest', inline: 'nearest' });
    renderMobileCoach();
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
    // No deck name here. Which deck you are on is the story the tutorial is
    // telling — the Lyrics slide announces it — not a label to carry around.
    document.getElementById('cardTutorialMobileProgress').textContent =
        `Step ${progress.current} of ${progress.total} · ${state.flipped ? 'back of card' : 'front of card'}`;
    document.getElementById('cardTutorialMobileTitle').innerHTML =
        `${esc(note.title)}${note.interactive ? '<span class="card-tutorial-try">tap it</span>' : ''}`;
    document.getElementById('cardTutorialMobileText').innerHTML = tutorialText(note.text);
    const back = document.getElementById('cardTutorialMobileBack');
    const next = document.getElementById('cardTutorialMobileNext');
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
    if (!isMobileTutorial()) return;
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
                <strong>${note.title}${note.interactive ? '<span class="card-tutorial-try">try it</span>' : ''}</strong>
                <span>${tutorialText(note.text)}</span>
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
            el.addEventListener('mouseenter', () => setActiveNote(i));
            el.addEventListener('mouseleave', () => setActiveNote(-1));
        });
}

// ---------------------------------------------------------------------------
// Linear tutorial chapters
// ---------------------------------------------------------------------------

function renderSequenceProgress() {
    const host = document.getElementById('cardTutorialSequence');
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
    const onStage = document.querySelector('#cardTutorialStage .card');
    const turnsInPlace = index !== state.stepIndex && onStage
        && from && from.kind === 'card' && to.kind === 'card'
        && from.deck === to.deck && from.face !== to.face;

    state.stepIndex = index;
    state.flipped = to.kind === 'card' && to.face === 'back';

    renderSequenceProgress();
    const body = document.getElementById('cardTutorialBody');

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
    state.activeNote = isMobileTutorial()
        ? Math.min(mobileNote, Math.max(0, stepNotes(to).length - 1))
        : 0;
    renderCard();
    syncFlipButton();
    renderMobileCoach();
    if (body) body.scrollTop = 0;
}

function advanceStep() {
    if (state.stepIndex < tutorialSteps().length - 1) goToStep(state.stepIndex + 1);
    else closeCardTutorial();
}

// ---------------------------------------------------------------------------
// Break slides
// ---------------------------------------------------------------------------

// A step with no card. The tutorial used to change deck silently and hope
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
    const host = document.getElementById('cardTutorialBreak');
    if (!host) return;
    const slide = TUTORIAL_BREAKS[currentStep().id];
    if (!slide) return;

    const first = state.stepIndex === 0;
    host.innerHTML = `
        <div class="card-tutorial-break-card">
            <span class="card-tutorial-break-eyebrow">${esc(slide.eyebrow)}</span>
            <h3 class="card-tutorial-break-title">${esc(slide.title)}</h3>
            <p class="card-tutorial-break-lead">${tutorialText(slide.lead)}</p>
            <ul class="card-tutorial-break-points">
                ${slide.points.map(point => `
                    <li>
                        <strong>${esc(point.title)}</strong>
                        <span>${tutorialText(point.text)}</span>
                    </li>`).join('')}
            </ul>
            <div class="card-tutorial-break-actions">
                ${first ? '' : '<button type="button" class="card-tutorial-break-back" id="cardTutorialBreakBack">Back</button>'}
                <button type="button" class="card-tutorial-break-cta" id="cardTutorialBreakNext">${esc(slide.cta)}</button>
            </div>
        </div>`;

    // The slide carries its own title, so the card's one-line header would be
    // the previous step's copy left standing over it.
    const intro = document.getElementById('cardTutorialIntro');
    if (intro) intro.innerHTML = '';

    showBreakChrome();
    document.getElementById('cardTutorialBreakNext')?.addEventListener('click', advanceStep);
    document.getElementById('cardTutorialBreakBack')
        ?.addEventListener('click', () => goToStep(state.stepIndex - 1, Number.MAX_SAFE_INTEGER));
}

// The card and its note columns, or the slide — never both. The mobile coach
// belongs to the card, so it goes with it.
function showBreakChrome() {
    document.getElementById('cardTutorialBody')?.classList.add('is-break-step');
    const host = document.getElementById('cardTutorialBreak');
    if (host) host.hidden = false;
    const coach = document.getElementById('cardTutorialMobileCoach');
    if (coach) coach.hidden = true;
    const cont = document.getElementById('cardTutorialContinue');
    if (cont) cont.hidden = true;
}

function showCardChrome() {
    document.getElementById('cardTutorialBody')?.classList.remove('is-break-step');
    const host = document.getElementById('cardTutorialBreak');
    if (host) { host.hidden = true; host.innerHTML = ''; }
}

// ---------------------------------------------------------------------------
// Setup-flow intro
// ---------------------------------------------------------------------------

// Three beats miming the real setup flow — language, level, study set — played
// once before the first card, so the tutorial starts where a learner would
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
    const host = document.getElementById('cardTutorialSetupAnim');
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
    document.getElementById('cardTutorialBody')?.classList.remove('is-setup-intro');
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
    const host = document.getElementById('cardTutorialSetupAnim');
    const body = document.getElementById('cardTutorialBody');
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
    const host = document.getElementById('cardTutorialSetupAnim');
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

function openCardTutorial() {
    const modal = document.getElementById('cardTutorialModal');
    if (!modal) return;
    rememberCardTutorial();
    modal.classList.remove('hidden');
    // Start from the top every time. Without this a replay opens with whatever
    // the last run finished on still on screen — a break slide, most visibly,
    // sitting under the intro.
    state.stepIndex = 0;
    showCardChrome();
    // Same for the top bar: it still held the last face's copy ("The back of
    // the card") over an intro that is about the setup screen.
    const intro = document.getElementById('cardTutorialIntro');
    if (intro) intro.innerHTML = '';
    // The card is rendered only once the intro is out of the way: marker
    // placement measures real boxes, and those read zero while the columns
    // are hidden behind the animation.
    playSetupIntro(() => goToStep(0));

    if (!_resizeHandler) {
        _resizeHandler = () => {
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
    if (hasSeenCardTutorial()) return false;
    // The setup screen has a technical default before the learner chooses a
    // language. Do not mistake that for interest and launch the wrong tour.
    if (!explicitTutorialLanguageKey()) return false;
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
    resetSetupIntro();
    showCardChrome();
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
    // Start set is the deliberate way out of the intro and only works once the
    // three steps have filled in; Skip intro leaves at any point. A stray click
    // on the card does nothing, or "deliberate" would mean very little.
    document.getElementById('setupAnimActionBtn')?.addEventListener('click', startSetupIntroCard);
    document.getElementById('setupAnimSkipBtn')?.addEventListener('click', skipSetupIntro);
    document.getElementById('cardTutorialFlip')?.addEventListener('click', () => flipCardFace(0));
    document.getElementById('cardTutorialContinue')?.addEventListener('click', () => {
        advanceStep();
    });
    document.getElementById('cardTutorialMobileBack')?.addEventListener('click', () => moveMobileTour(-1));
    document.getElementById('cardTutorialMobileNext')?.addEventListener('click', () => moveMobileTour(1));

    // Escape closes; left/right jump chapters, kept as an escape hatch for
    // anyone who wants to skip ahead. Space deliberately does nothing: the
    // tutorial owns the flip, so the card only turns when the tour says so.
    document.addEventListener('keydown', (e) => {
        if (modal.classList.contains('hidden')) return;
        if (e.key === 'Escape') closeCardTutorial();
        else if (e.key === 'ArrowRight') goToStep(state.stepIndex + 1);
        else if (e.key === 'ArrowLeft') goToStep(state.stepIndex - 1);
    });
}

document.addEventListener('DOMContentLoaded', setupCardTutorial);
if (document.readyState !== 'loading') setupCardTutorial();

window.openCardTutorial = openCardTutorial;
window.openFirstRunCardTutorial = openFirstRunCardTutorial;
window.closeCardTutorial = closeCardTutorial;
window.getCardTutorialProfile = tutorialAdapter;
window.getCardTutorialLanguageKey = explicitTutorialLanguageKey;
window.getCardTutorialLanguages = () => Object.entries(TUTORIAL_LANGUAGE_ADAPTERS)
    .map(([key, adapter]) => ({ key, language: adapter.language }));
window.setCardTutorialLanguage = key => {
    tutorialLanguageOverride = TUTORIAL_LANGUAGE_ADAPTERS[key] ? key : null;
};
