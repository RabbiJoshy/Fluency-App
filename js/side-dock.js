// Side docking on a wide desktop. docs/ui/UI_WORK_ORDERS.md #8 has the rule
// and the reasons. In one sentence: anything that does not move you within
// your set opens at the side when there is room.
//
//   left   you and the app. Settings lives here, and anything opened while
//          settings is open stacks on top of it, so closing the top one
//          returns you to settings. Otherwise: progress, saved words,
//          shortcuts, help.
//   right  this card. Dictionary, synonyms, conjugation, card data, lyric
//          breakdown, rarer-sense knowledge. When the right is
//          taken and the left is free, the next one opens on the left, so two
//          can be read side by side.
//
// Anything about the card closes when the card changes or turns to its front,
// because what it shows gives the answer away. Everything else stays open
// while you study; its transparent backdrop lets clicks through to the card.
//
// This module decides the side and marks it with data-dock="left|right" (and
// data-dock-stack on a sheet over settings); CSS only draws the two
// positions. Card panels are rendered inside the card's back face, where
// .card-face clips them and the flip transform makes even position:fixed
// resolve against the card, so they are hosted on <body> while docked.
//
// Loaded once from flashcards.js and reached through window.sideDock, so that
// other modules can use it without importing it under a second ?v= tag (a
// module imported under two URLs executes twice).

// Panel width. In a study session a panel sits in the gutter beside the card,
// centred between the screen edge and the card, up to 400px. A narrower
// window shrinks the panels, down to 300px; below that they are too cramped
// to read, so nothing docks and sheets stay centred. The card's width is
// measured, not assumed, so resizing the card never breaks this.
const PANEL_MAX = 400;
const PANEL_MIN = 300;
const EDGE = 16;
const GAP = 16;
// The setup page has no card to keep in view: sheets sit over the page.
const SETUP_MIN_WINDOW = 900;
const SETUP_PANEL_MAX = 440;

function studyViewOpen() {
    const app = document.getElementById('appContent');
    return Boolean(app && !app.classList.contains('hidden'));
}

function cardWidth() {
    // offsetWidth ignores transforms, so a flip or a nav animation in
    // progress does not read as a narrower card.
    const measured = document.getElementById('flashcard')?.offsetWidth;
    if (measured) return measured;
    const container = document.querySelector('.card-container');
    const declared = container && parseFloat(getComputedStyle(container).getPropertyValue('--study-card-max-width'));
    return declared || 513;
}

function panelWidth() {
    if (!studyViewOpen()) return Math.min(SETUP_PANEL_MAX, Math.floor(window.innerWidth * 0.4));
    const margin = (window.innerWidth - cardWidth()) / 2;
    return Math.min(PANEL_MAX, Math.floor(margin - EDGE - GAP));
}

// Publish the width for the CSS. Never below the minimum: a panel already
// docked when the window narrows keeps a readable width rather than
// collapsing.
function applyPanelWidth() {
    const width = Math.max(PANEL_MIN, panelWidth());
    document.body.style.setProperty('--dock-w', `${width}px`);
    // Centre the sheet in the gutter. A tight window keeps the old 16px edge.
    let inset = EDGE;
    if (studyViewOpen()) {
        const margin = (window.innerWidth - cardWidth()) / 2;
        inset = Math.max(EDGE, Math.round((margin - width) / 2));
    }
    document.body.style.setProperty('--dock-inset', `${inset}px`);
}

// Card panels need room beside the card; sheets can also dock over the
// setup page.
function canDockCard() {
    return studyViewOpen() && panelWidth() >= PANEL_MIN;
}
function canDockSheet() {
    return studyViewOpen() ? panelWidth() >= PANEL_MIN : window.innerWidth >= SETUP_MIN_WINDOW;
}

const isShown = el => !el.classList.contains('hidden') && !el.hidden;

function closeButtonFor(id) {
    return () => {
        const button = document.getElementById(`close${id[0].toUpperCase()}${id.slice(1)}`);
        if (button) button.click();
        else document.getElementById(id)?.classList.add('hidden');
    };
}

// home: the side it prefers. card: closes with the card. stacks: may open
// over settings. onlyOverSettings: centred unless settings is open.
const OCCUPANTS = [
    // Card panels, hosted on <body> while docked.
    { id: 'synonymsPanel', home: 'right', card: true, panel: true,
      open: el => el.classList.contains('visible'),
      close: () => window.toggleSynonymsPanel?.() },
    { id: 'conjugationTable', home: 'right', card: true, panel: true,
      open: el => el.classList.contains('visible'),
      close: () => window.toggleConjugationTable?.() },
    { id: 'spanishDictPanel', home: 'right', card: true, panel: true,
      open: el => !el.hidden,
      close: () => window.toggleSpanishDictPanel?.(false) },
    { id: 'provenancePanel', home: 'right', card: true, panel: true,
      open: el => el.style.display === 'block',
      close: () => window.toggleProvenancePanel?.(false) },
    // Modals about the card.
    { id: 'lyricBreakdownModal', home: 'right', card: true,
      open: isShown, close: () => window.hideLyricBreakdown?.() },
    { id: 'knowledgeOverviewModal', home: 'right', card: true,
      open: el => !el.hidden && !el.classList.contains('is-closing'),
      close: () => window.closeKnowledgeOverview?.() },
    // Settings, and the sheets about you and the session.
    { id: 'settingsModal', home: 'left', settings: true,
      open: isShown, close: closeButtonFor('settingsModal') },
    ...['savedWordsModal', 'statsModal', 'totalStatsModal', 'reviewHomeModal', 'keyboardShortcutsModal', 'helpModal'].map(id => ({
        id, home: 'left', stacks: true, open: isShown, close: closeButtonFor(id) })),
    // Setup-page reference sheets: word lists and rules.
    ...['mergedFormsModal', 'skippedWordsModal', 'extrasModal', 'cognateRulesModal'].map(id => ({
        id, home: 'right', stacks: true, open: isShown, close: closeButtonFor(id) })),
    // Pages reached from settings: they stack over it, and stay centred
    // when opened any other way.
    ...['fastModeModal', 'vocabularyImportModal'].map(id => ({
        id, home: 'left', stacks: true, onlyOverSettings: true, open: isShown, close: closeButtonFor(id) })),
];
const byId = Object.fromEntries(OCCUPANTS.map(o => [o.id, o]));

function elementOf(occupant) {
    return document.getElementById(occupant.id);
}
function isOpen(occupant) {
    const el = elementOf(occupant);
    return Boolean(el && occupant.open(el));
}
function sideOf(occupant) {
    return elementOf(occupant)?.dataset.dock || null;
}
function openOn(side, exceptId) {
    return OCCUPANTS.filter(o => o.id !== exceptId && isOpen(o) && sideOf(o) === side);
}
function settingsOpen() {
    return isOpen(byId.settingsModal) && sideOf(byId.settingsModal) === 'left';
}

function mark(el, side, stacked = false) {
    if (side) el.dataset.dock = side;
    else delete el.dataset.dock;
    if (stacked) el.dataset.dockStack = '';
    else delete el.dataset.dockStack;
}

function closeAll(list) {
    for (const occupant of list) occupant.close();
}

// Decide where an occupant goes as it opens, clearing whatever it displaces.
// Returns the side, or null when it should not dock here.
function place(occupant) {
    const el = elementOf(occupant);
    if (!el) return null;
    const dockable = occupant.panel ? canDockCard() : canDockSheet();
    if (!dockable || (occupant.onlyOverSettings && !settingsOpen())) {
        mark(el, null);
        return null;
    }
    applyPanelWidth();

    if (occupant.settings) {
        // Settings is the base of the left: it clears what was there.
        closeAll(openOn('left', occupant.id));
        mark(el, 'left');
        return 'left';
    }

    if (occupant.stacks && settingsOpen()) {
        // Over settings; one sheet at a time on top of it.
        closeAll(openOn('left', occupant.id).filter(o => !o.settings));
        mark(el, 'left', true);
        return 'left';
    }

    if (occupant.home === 'left') {
        closeAll(openOn('left', occupant.id));
        mark(el, 'left');
        return 'left';
    }

    // Right-hand occupants: the right if free, else the left if free, else
    // replace what is on the right.
    const right = openOn('right', occupant.id);
    if (!right.length) {
        mark(el, 'right');
        return 'right';
    }
    if (!openOn('left', occupant.id).length) {
        mark(el, 'left');
        return 'left';
    }
    closeAll(right);
    mark(el, 'right');
    return 'right';
}

function hostCardPanel(panel) {
    if (panel.parentElement !== document.body) document.body.appendChild(panel);
    panel.classList.add('is-docked');
}

function stowCardPanel(panel) {
    if (!panel) return;
    panel.classList.remove('is-docked');
    mark(panel, null);
    const host = document.getElementById('backContent');
    if (host && panel.parentElement !== host) host.appendChild(panel);
}

// Open a card panel beside the card when there is room; otherwise leave it
// where it was rendered, over the card as before. Returns whether it docked.
function openCardPanel(panel) {
    const occupant = panel && byId[panel.id];
    if (!occupant || !place(occupant)) return false;
    hostCardPanel(panel);
    return true;
}

// Settings-launched pages used to close settings first. When they will
// stack over it instead, settings stays open underneath.
function keepsSettingsOpen() {
    return canDockSheet() && settingsOpen();
}

// The card turned to its front: anything about it would give the answer
// away. Narrow layouts keep their panels inside the card, which turn away
// with the back face on their own, so they are left alone.
function closeForFront() {
    if (!canDockCard()) return;
    closeAll(OCCUPANTS.filter(o => o.card && isOpen(o)));
}

// The back face is about to be re-rendered. Panels hosted on <body> belong to
// the markup being replaced, so drop them rather than leave a second node
// claiming the same id; and when the card itself changed, close the modals
// that described the old one.
let lastCard = null;
function beforeBackRender(card) {
    for (const occupant of OCCUPANTS) {
        if (!occupant.panel) continue;
        const el = elementOf(occupant);
        if (el?.parentElement === document.body) el.remove();
    }
    if (card !== lastCard) {
        if (lastCard && canDockCard()) {
            closeAll(OCCUPANTS.filter(o => o.card && !o.panel && isOpen(o)));
        }
        lastCard = card;
    }
}

// Escape closes the nearest open panel instead of leaving the set: the right
// first, then whatever is stacked over settings, then settings itself.
function closeTopmost() {
    const open = OCCUPANTS.filter(isOpen);
    const next = open.find(o => sideOf(o) === 'right')
        || open.find(o => elementOf(o).dataset.dockStack !== undefined)
        || open.find(o => sideOf(o) === 'left' && !o.settings)
        || open.find(o => o.settings)
        || open[0];
    if (!next) return false;
    next.close();
    return true;
}

// Modals open through their own modules, so watch them rather than edit
// every opener: each is placed the moment it appears. MutationObserver
// callbacks run before the next paint, so a sheet never flashes centred.
function watch(occupant) {
    const el = elementOf(occupant);
    if (!el || el._sideDockWatched) return;
    el._sideDockWatched = true;
    let wasOpen = occupant.open(el);
    new MutationObserver(() => {
        const nowOpen = occupant.open(el);
        if (nowOpen && !wasOpen) place(occupant);
        wasOpen = nowOpen;
    }).observe(el, { attributes: true, attributeFilter: ['class', 'hidden'] });
}

function watchModals() {
    for (const occupant of OCCUPANTS) {
        if (!occupant.panel) watch(occupant);
    }
}

function init() {
    watchModals();
    let resizeFrame = 0;
    window.addEventListener('resize', () => {
        cancelAnimationFrame(resizeFrame);
        resizeFrame = requestAnimationFrame(applyPanelWidth);
    });
    // knowledgeOverviewModal is created on first use; catch it when it lands.
    new MutationObserver(watchModals).observe(document.body, { childList: true });
    // Leaving the study view closes what described its cards and its session.
    // Settings, and whatever is stacked over it, belongs to the app, not the
    // set, so it stays.
    const app = document.getElementById('appContent');
    if (app) {
        new MutationObserver(() => {
            if (!app.classList.contains('hidden')) return;
            closeAll(OCCUPANTS.filter(o => isOpen(o) && !o.settings
                && elementOf(o).dataset.dockStack === undefined
                && (o.card || sideOf(o) === 'left' || sideOf(o) === 'right')));
        }).observe(app, { attributes: true, attributeFilter: ['class'] });
    }
}

if (!window.sideDock) {
    window.sideDock = {
        canDockCard, canDockSheet, openCardPanel, stowCardPanel,
        keepsSettingsOpen, closeForFront, beforeBackRender, closeTopmost,
    };
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init, { once: true });
    } else {
        init();
    }
}
