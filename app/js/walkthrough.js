// The walkthrough — for VISITORS: an employer, or anyone being shown the app
// who is not going to use it.
//
// Not the tutorial (tutorial.js). The tutorial teaches a learner who is about
// to study: it starts from the setup screen, rings one element at a time and
// runs to a dozen steps. A visitor has none of that context and may look for
// five seconds, so this is built the other way round:
//
//   * A step is a whole face with every label on it at once, not one element.
//     The first screen alone — front and back side by side — is the point; a
//     visitor who closes after it has still seen what a card is.
//   * Two screens on anything wider than a phone: the card, then Lyrics mode.
//     A phone cannot fit two cards side by side, so it turns the one card
//     over instead, which is the only extra click.
//   * No setup, no language choice, no instructions for studying.
//   * It opens from About and closes back into About.
//
// The card is drawn by card-replica.js, which the tutorial shares, so the two
// never disagree about what a card looks like. The card stays live: tapping a
// meaning changes the example and the Spotify button plays the real line,
// because that is worth showing off. Nothing is written to progress.

import {
    REPLICA_CARDS, esc, renderBack, replicaCardHTML, wireReplicaBack,
    measureReplicaCard, fitReplicaCard,
} from './card-replica.js?v=20260921ac';

// ---------------------------------------------------------------------------
// Content
// ---------------------------------------------------------------------------
//
// Labels are short on purpose. A title a visitor can take in at a glance and,
// where there is room, one line under it. Anything needing a paragraph belongs
// in the tutorial. `face` scopes the anchor to the side of the card it sits
// on, since both faces are always in the DOM.

const FRONT_LABELS = [
    { face: 'front', anchor: '.card-word', title: 'The word, as it is said',
      text: 'Taken from real speech, not a dictionary headword.' },
    { face: 'front', anchor: '.front-lemma-pair', title: 'What kind of word',
      text: 'With the dictionary form it belongs to.' },
    // One label for the whole row. Rank and frequency as two labels drew two
    // leader lines across each other to reach the right-hand figure.
    { face: 'front', anchor: '.card-ranking', title: 'Ranked by use',
      text: 'Counted across film and TV dialogue. The most common words come first.' },
];

const BACK_LABELS = [
    { face: 'back', anchor: '.pos-section-head', title: 'Every meaning, separated',
      text: 'One word, two unrelated meanings: a bank and a bench.' },
    { face: 'back', anchor: '.meaning-row.is-current-sense .sense-prominence-badge', title: 'How often each is used',
      text: 'Estimated from the real sentences behind the deck.' },
    { face: 'back', anchor: '.example-word-highlight', title: 'A real sentence for it',
      text: 'Tap another meaning and the example changes with it.' },
];

const LYRICS_LABELS = [
    { face: 'back', side: 'left', anchor: '.meanings-scroll', title: 'How this artist uses it',
      text: 'Mostly heaven in these songs, sometimes the sky.' },
    // The whole line, not the highlighted word: a leader to the word ran
    // through the lyric to reach it.
    { face: 'back', side: 'right', anchor: '.breakdown-trigger', title: 'An actual lyric',
      text: 'From a Bad Bunny song, translated underneath.' },
    { face: 'back', side: 'right', anchor: '.spotify-btn', pin: 'below', title: 'Plays that exact line',
      text: 'Opens Spotify at the right second.' },
];

// Screens are chosen by layout, not by device name: whether two cards fit side
// by side is a measurement, and a narrow desktop window is treated like the
// phone it resembles.
function buildScreens(pair) {
    const lyrics = {
        id: 'lyrics',
        title: 'Lyrics mode',
        lead: 'Pick an artist and the whole deck is built from the words they sing. '
            + 'Every example is a real lyric you can play.',
        cards: [{ key: 'cielo', face: 'back', labels: LYRICS_LABELS }],
    };
    if (pair) {
        return [{
            id: 'card',
            title: 'This is a flashcard',
            lead: 'The front asks you to recall a word. The back shows everything it can mean, '
                + 'how often each meaning comes up, and a real sentence for it.',
            cards: [
                { key: 'bancoSpeech', face: 'front', labels: FRONT_LABELS.map(l => ({ ...l, side: 'left' })) },
                { key: 'bancoSpeech', face: 'back', labels: BACK_LABELS.map(l => ({ ...l, side: 'right' })) },
            ],
        }, lyrics];
    }
    return [{
        id: 'front',
        title: 'The front of a card',
        lead: 'A word to recall, ranked by how often it is actually said.',
        cards: [{ key: 'bancoSpeech', face: 'front', labels: FRONT_LABELS }],
    }, {
        id: 'back',
        title: 'The back of a card',
        lead: 'Every meaning, how often each is used, and a real sentence for the one you pick.',
        cards: [{ key: 'bancoSpeech', face: 'back', labels: BACK_LABELS }],
    }, lyrics];
}

// ---------------------------------------------------------------------------
// Layout
// ---------------------------------------------------------------------------

const CARD_GAP = 32;
const PAIR_CARD_W = 380;
const SINGLE_CARD_W = 420;
// A callout needs this much width beside the card to be readable; below it the
// labels become tags pinned onto the card instead.
const CALLOUT_W = 200;
const CALLOUT_GAP = 44;

const state = {
    screens: [],
    index: 0,
    pair: false,
    // Per card slot on the current screen: which sense and example are up.
    slots: [],
};

let _resizeHandler = null;
let _layoutTimer = null;

function stageWidth() {
    const body = document.getElementById('walkthroughBody');
    if (!body) return window.innerWidth;
    const style = getComputedStyle(body);
    return body.clientWidth - parseFloat(style.paddingLeft) - parseFloat(style.paddingRight);
}

function fitsPair() {
    return stageWidth() >= PAIR_CARD_W * 2 + CARD_GAP;
}

function currentScreen() {
    return state.screens[state.index];
}

// Whether there is room for callouts either side of the cards on show.
function calloutMode(cardWidth, count) {
    const used = cardWidth * count + CARD_GAP * (count - 1);
    return (stageWidth() - used) / 2 >= CALLOUT_W + CALLOUT_GAP;
}

// As wide as the room allows with callouts beside it, up to the width of a
// real card on a laptop. Without room for callouts, the plain width.
const MAX_CARD_W = 440;
const MIN_CALLOUT_CARD_W = 340;

function cardWidthFor(count) {
    const available = stageWidth();
    const gaps = CARD_GAP * (count - 1);
    const withCallouts = Math.floor((available - gaps - 2 * (CALLOUT_W + CALLOUT_GAP)) / count);
    if (withCallouts >= MIN_CALLOUT_CARD_W) return Math.min(MAX_CARD_W, withCallouts);
    const wanted = count === 2 ? PAIR_CARD_W : SINGLE_CARD_W;
    return Math.min(wanted, Math.floor((available - gaps) / count));
}

// ---------------------------------------------------------------------------
// Rendering
// ---------------------------------------------------------------------------

function renderScreen({ turnFrom = null } = {}) {
    const screen = currentScreen();
    const stage = document.getElementById('walkthroughStage');
    if (!screen || !stage) return;

    document.getElementById('walkthroughTitle').textContent = screen.title;
    document.getElementById('walkthroughLead').textContent = screen.lead;
    renderProgress();

    state.slots = screen.cards.map(spec => ({
        spec,
        meaningIndex: REPLICA_CARDS[spec.key].defaultMeaningIndex || 0,
        exampleIndex: 0,
    }));

    const count = screen.cards.length;
    const width = cardWidthFor(count);
    stage.style.setProperty('--walkthrough-card-w', `${width}px`);
    stage.classList.toggle('is-callouts', calloutMode(width, count));
    stage.classList.toggle('is-pins', !calloutMode(width, count));

    stage.innerHTML = `
        <div class="walkthrough-cards">
            ${state.slots.map((slot, i) => `
                <div class="walkthrough-slot" data-slot="${i}">
                    ${replicaCardHTML(REPLICA_CARDS[slot.spec.key], {
                        // Turning the card over in place, rather than redrawing
                        // it already turned, is what makes "the back" read as
                        // the other side of the same card.
                        flipped: turnFrom ? false : slot.spec.face === 'back',
                        meaningIndex: slot.meaningIndex,
                        exampleIndex: slot.exampleIndex,
                    })}
                </div>`).join('')}
        </div>
        <svg class="walkthrough-leaders" aria-hidden="true"></svg>
        <div class="walkthrough-labels"></div>`;

    stage.querySelectorAll('.walkthrough-slot').forEach(slotEl => wireSlot(slotEl));
    fitCards();

    const reduced = window.matchMedia?.('(prefers-reduced-motion: reduce)').matches;
    if (turnFrom && !reduced) {
        // Commit the unturned card to layout, then turn it. A reflow rather
        // than requestAnimationFrame, which is throttled in background tabs
        // and low-power mode. placeLabels() waits out the turn itself.
        const cards = [...stage.querySelectorAll('.walkthrough-slot .card')];
        void stage.offsetWidth;
        cards.forEach((cardEl, i) => {
            cardEl.classList.toggle('flipped', state.slots[i].spec.face === 'back');
        });
        scheduleLabels(0);
    } else {
        if (turnFrom) {
            stage.querySelectorAll('.walkthrough-slot .card').forEach((cardEl, i) => {
                cardEl.classList.toggle('flipped', state.slots[i].spec.face === 'back');
            });
        }
        scheduleLabels(0);
    }
    document.getElementById('walkthroughBody')?.scrollTo?.({ top: 0 });
}

function wireSlot(slotEl) {
    const i = Number(slotEl.dataset.slot);
    wireReplicaBack(slotEl, {
        onSelectMeaning: idx => {
            state.slots[i].meaningIndex = idx;
            state.slots[i].exampleIndex = 0;
            refreshSlotBack(i);
        },
        onCycleExample: () => {
            state.slots[i].exampleIndex += 1;
            refreshSlotBack(i);
        },
        onLayoutChange: () => scheduleLabels(0),
    });
}

// Sense and example changes replace only the back face, so the card keeps its
// flip state, the same as updateCard() rewriting #backContent on a live card.
function refreshSlotBack(i) {
    const slotEl = document.querySelector(`#walkthroughStage .walkthrough-slot[data-slot="${i}"]`);
    const back = slotEl?.querySelector('.card-back');
    if (!back) return;
    const slot = state.slots[i];
    back.outerHTML = renderBack(REPLICA_CARDS[slot.spec.key], slot.meaningIndex, slot.exampleIndex);
    wireSlot(slotEl);
    fitCards();
    scheduleLabels(0);
}

// Cards shown together share one height, so a front and back read as a pair
// rather than two unrelated boxes. The height comes from the taller back.
function fitCards() {
    const inners = [...document.querySelectorAll('#walkthroughStage .card-replica')];
    if (!inners.length) return;
    const tallest = Math.max(...inners.map(measureReplicaCard));
    // Leave the header and the footer on screen with the card.
    const chrome = (document.querySelector('.walkthrough-head')?.offsetHeight || 90)
        + (document.querySelector('.walkthrough-foot')?.offsetHeight || 70) + 48;
    const ceiling = Math.max(0.5, (window.innerHeight - chrome) / window.innerHeight);
    inners.forEach(inner => fitReplicaCard(inner, { height: tallest, ceiling, floor: 380 }));
}

function renderProgress() {
    const dots = document.getElementById('walkthroughDots');
    if (dots) {
        dots.innerHTML = state.screens.map((_, i) =>
            `<span class="walkthrough-dot${i === state.index ? ' is-current' : ''}${i < state.index ? ' is-done' : ''}"></span>`,
        ).join('');
    }
    const count = document.getElementById('walkthroughCount');
    if (count) count.textContent = `${state.index + 1} of ${state.screens.length}`;

    const back = document.getElementById('walkthroughBack');
    if (back) back.hidden = state.index === 0;
    const next = document.getElementById('walkthroughNext');
    if (next) {
        const after = state.screens[state.index + 1];
        next.textContent = !after ? 'Back to About'
            : after.id === 'back' ? 'Turn it over →'
            : after.id === 'lyrics' ? 'Lyrics mode →'
            : 'Next →';
        next.classList.toggle('is-final', !after);
    }
}

// ---------------------------------------------------------------------------
// Labels
// ---------------------------------------------------------------------------

function scheduleLabels(delay) {
    clearTimeout(_layoutTimer);
    _layoutTimer = setTimeout(placeLabels, delay);
}

// Every label is placed from the measured box of the element it describes, so
// labels stay right when a row wraps or the window narrows. Callouts sit in
// the gutter beside the card with a leader line to their element; when there
// is no gutter, a short tag is pinned onto the element itself instead.
function placeLabels() {
    const stage = document.getElementById('walkthroughStage');
    const layer = stage?.querySelector('.walkthrough-labels');
    const svg = stage?.querySelector('.walkthrough-leaders');
    if (!stage || !layer || !svg) return;

    // A card that is still turning reports mirrored boxes. Ask it rather than
    // guess a delay: wait for its own transition to finish, then measure.
    const turning = [...stage.querySelectorAll('.walkthrough-slot .card')]
        .flatMap(cardEl => cardEl.getAnimations?.() || [])
        .filter(anim => anim.playState === 'running' || anim.playState === 'pending');
    if (turning.length) {
        layer.innerHTML = '';
        svg.innerHTML = '';
        Promise.all(turning.map(anim => anim.finished)).then(() => scheduleLabels(0), () => {});
        return;
    }
    layer.innerHTML = '';
    svg.innerHTML = '';
    stage.querySelectorAll('.walkthrough-anchored').forEach(el => el.classList.remove('walkthrough-anchored'));

    const frame = stage.getBoundingClientRect();
    const callouts = stage.classList.contains('is-callouts');
    const placed = { left: [], right: [] };

    state.slots.forEach((slot, i) => {
        const slotEl = stage.querySelector(`.walkthrough-slot[data-slot="${i}"]`);
        const cardBox = slotEl?.querySelector('.card-replica')?.getBoundingClientRect();
        if (!cardBox) return;
        slot.spec.labels.forEach(label => {
            const target = slotEl.querySelector(`.card-${label.face} ${label.anchor}`);
            if (!target) return;
            const box = target.getBoundingClientRect();
            if (!box.width && !box.height) return;
            target.classList.add('walkthrough-anchored');
            const rel = {
                left: box.left - frame.left,
                right: box.right - frame.left,
                top: box.top - frame.top,
                bottom: box.bottom - frame.top,
                cy: box.top - frame.top + box.height / 2,
            };
            if (callouts) {
                // In a pair, a label goes on the outside of its own card; a
                // single card takes whichever side the label asks for.
                const side = label.side || 'right';
                placed[side].push({ label, rel, card: {
                    left: cardBox.left - frame.left, right: cardBox.right - frame.left,
                } });
            } else {
                pinLabel(layer, label, rel, cardBox.left - frame.left, cardBox.right - frame.left);
            }
        });
    });

    if (callouts) {
        ['left', 'right'].forEach(side => layoutCallouts(layer, svg, side, placed[side], frame.height));
    }
}

function layoutCallouts(layer, svg, side, items, stageHeight) {
    if (!items.length) return;
    items.sort((a, b) => a.rel.cy - b.rel.cy);
    const nodes = items.map(({ label }) => {
        const el = document.createElement('div');
        el.className = `walkthrough-callout is-${side}`;
        el.innerHTML = `<strong>${esc(label.title)}</strong>${label.text ? `<span>${esc(label.text)}</span>` : ''}`;
        layer.appendChild(el);
        return el;
    });
    // Aim each callout's middle at its element, then push down so none overlap,
    // then pull the whole column back up if it ran off the bottom.
    const GAP = 14;
    const heights = nodes.map(n => n.offsetHeight);
    const tops = [];
    items.forEach((item, i) => {
        const wanted = item.rel.cy - heights[i] / 2;
        tops[i] = i === 0 ? Math.max(0, wanted) : Math.max(wanted, tops[i - 1] + heights[i - 1] + GAP);
    });
    const overflow = tops.length ? tops[tops.length - 1] + heights[heights.length - 1] - stageHeight : 0;
    if (overflow > 0) {
        for (let i = tops.length - 1; i >= 0; i -= 1) {
            const limit = i === tops.length - 1 ? stageHeight - heights[i] : tops[i + 1] - GAP - heights[i];
            tops[i] = Math.max(0, Math.min(tops[i], limit));
        }
    }

    const ns = 'http://www.w3.org/2000/svg';
    items.forEach((item, i) => {
        const node = nodes[i];
        const cardEdge = side === 'left' ? item.card.left : item.card.right;
        const x = side === 'left' ? cardEdge - CALLOUT_GAP - CALLOUT_W : cardEdge + CALLOUT_GAP;
        node.style.left = `${x}px`;
        node.style.top = `${tops[i]}px`;

        // Leader: from the callout's inner edge, level with its title, to the
        // near edge of the element it names.
        const startX = side === 'left' ? x + CALLOUT_W + 6 : x - 6;
        const startY = tops[i] + 11;
        const endX = side === 'left' ? item.rel.left - 4 : item.rel.right + 4;
        const endY = item.rel.cy;
        const elbowX = side === 'left' ? cardEdge - 10 : cardEdge + 10;
        const path = document.createElementNS(ns, 'path');
        path.setAttribute('d', `M ${startX} ${startY} L ${elbowX} ${startY} L ${endX} ${endY}`);
        path.setAttribute('class', 'walkthrough-leader');
        svg.appendChild(path);
        const dot = document.createElementNS(ns, 'circle');
        dot.setAttribute('cx', endX);
        dot.setAttribute('cy', endY);
        dot.setAttribute('r', '3.5');
        dot.setAttribute('class', 'walkthrough-leader-dot');
        svg.appendChild(dot);
    });
}

// Narrow screens: a title-only tag sitting on the element's top edge. The
// screen's lead line carries the explanation the callout text would have.
function pinLabel(layer, label, rel, cardLeft, cardRight) {
    const tag = document.createElement('div');
    tag.className = 'walkthrough-pin';
    tag.textContent = label.title;
    layer.appendChild(tag);
    const w = tag.offsetWidth;
    const h = tag.offsetHeight;
    const alignRight = label.pin === 'below' || label.anchor.includes('prominence');
    let left = alignRight ? rel.right - w : rel.left;
    left = Math.max(cardLeft + 6, Math.min(left, cardRight - w - 6));
    // Above the element by default. `below` is for an element with text
    // directly over it that a tag would cover — the Spotify button sits under
    // the translation.
    let top = label.pin === 'below' ? rel.bottom + 3 : rel.top - h - 3;
    if (top < 4) top = rel.top + 3;
    tag.style.left = `${left}px`;
    tag.style.top = `${top}px`;
}

// ---------------------------------------------------------------------------
// Navigation
// ---------------------------------------------------------------------------

function goTo(index) {
    if (index < 0) return;
    if (index >= state.screens.length) {
        closeWalkthrough();
        return;
    }
    const from = currentScreen();
    state.index = index;
    const to = currentScreen();
    // The front-then-back pair on a narrow screen is one card turning over.
    const turns = from && from.id === 'front' && to.id === 'back';
    renderScreen({ turnFrom: turns ? from : null });
}

// A resize can change how many screens there are: two cards stop fitting side
// by side, or start to. Map the screen being read onto the new list so the
// visitor stays where they were.
function relayout() {
    const pair = fitsPair();
    if (pair !== state.pair) {
        const id = currentScreen()?.id;
        state.pair = pair;
        state.screens = buildScreens(pair);
        const mapped = id === 'lyrics' ? 'lyrics' : pair ? 'card' : (id === 'card' ? 'front' : id);
        state.index = Math.max(0, state.screens.findIndex(s => s.id === mapped));
        renderScreen();
        return;
    }
    const stage = document.getElementById('walkthroughStage');
    const count = currentScreen()?.cards.length || 1;
    const width = cardWidthFor(count);
    stage?.style.setProperty('--walkthrough-card-w', `${width}px`);
    stage?.classList.toggle('is-callouts', calloutMode(width, count));
    stage?.classList.toggle('is-pins', !calloutMode(width, count));
    fitCards();
    scheduleLabels(0);
}

// ---------------------------------------------------------------------------
// Open / close
// ---------------------------------------------------------------------------

// `start` names a screen ('lyrics'), so a tap on About's Lyrics demo card
// lands on the Lyrics card rather than making the reader step past Speech.
function openWalkthrough({ start = null } = {}) {
    const modal = document.getElementById('walkthroughModal');
    if (!modal) return;
    modal.classList.remove('hidden');
    state.pair = fitsPair();
    state.screens = buildScreens(state.pair);
    state.index = Math.max(0, state.screens.findIndex(screen => screen.id === start));
    renderScreen();
    document.getElementById('walkthroughNext')?.focus({ preventScroll: true });
    if (!_resizeHandler) {
        _resizeHandler = () => relayout();
        window.addEventListener('resize', _resizeHandler);
    }
}

// Layered over About, so closing reveals About again where the visitor left it.
// Spotify playback the visitor started is left running on purpose.
function closeWalkthrough() {
    const modal = document.getElementById('walkthroughModal');
    if (!modal) return;
    modal.classList.add('hidden');
    clearTimeout(_layoutTimer);
    const stage = document.getElementById('walkthroughStage');
    if (stage) stage.innerHTML = '';
    if (_resizeHandler) {
        window.removeEventListener('resize', _resizeHandler);
        _resizeHandler = null;
    }
}

function setupWalkthrough() {
    const modal = document.getElementById('walkthroughModal');
    if (!modal || modal.dataset.ready === '1') return;
    modal.dataset.ready = '1';
    document.getElementById('closeWalkthroughModal')?.addEventListener('click', closeWalkthrough);
    document.getElementById('walkthroughNext')?.addEventListener('click', () => goTo(state.index + 1));
    document.getElementById('walkthroughBack')?.addEventListener('click', () => goTo(state.index - 1));
    document.addEventListener('keydown', e => {
        if (modal.classList.contains('hidden')) return;
        if (e.key === 'Escape') {
            // About listens for Escape too; this one belongs to the walkthrough.
            e.stopImmediatePropagation();
            closeWalkthrough();
        } else if (e.key === 'ArrowRight') goTo(state.index + 1);
        else if (e.key === 'ArrowLeft') goTo(state.index - 1);
    }, true);
}

document.addEventListener('DOMContentLoaded', setupWalkthrough);
if (document.readyState !== 'loading') setupWalkthrough();

window.openWalkthrough = openWalkthrough;
window.closeWalkthrough = closeWalkthrough;
