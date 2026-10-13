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

// Measure the visible centre column in CSS layout units. Body zoom scales
// both the card and fixed sheets, so mixing offsetWidth with innerWidth lets
// an apparently fitting panel spill over the card.
const PANEL_MAX = 400;
const PANEL_MIN = 280;
const EDGE = 16;
const GAP = 16;
const SETUP_MIN_WINDOW = 900;
const SETUP_PANEL_MAX = 440;

function studyViewOpen() {
    const app = document.getElementById('appContent');
    return Boolean(app && !app.classList.contains('hidden'));
}

function layoutZoom() {
    return parseFloat(getComputedStyle(document.body).zoom) || 1;
}

function centreBounds() {
    // The container does not flip or shrink during card navigation.
    const centre = document.querySelector(studyViewOpen() ? '.card-container' : '#setupPanel');
    const rect = centre?.getBoundingClientRect();
    const zoom = layoutZoom();
    if (rect?.width) {
        const card = studyViewOpen() && document.getElementById('flashcard');
        if (card?.offsetWidth) {
            const midpoint = (rect.left + rect.right) / (2 * zoom);
            return { left: midpoint - card.offsetWidth / 2, right: midpoint + card.offsetWidth / 2 };
        }
        return { left: rect.left / zoom, right: rect.right / zoom };
    }
    const width = window.innerWidth / zoom;
    return { left: (width - 513) / 2, right: (width + 513) / 2 };
}

function gutterWidth() {
    const bounds = centreBounds();
    return Math.max(0, Math.min(bounds.left, window.innerWidth / layoutZoom() - bounds.right));
}

function panelWidth() {
    return Math.min(studyViewOpen() ? PANEL_MAX : SETUP_PANEL_MAX,
        Math.floor(gutterWidth() - EDGE - GAP));
}

function applyPanelWidth() {
    const width = Math.max(0, panelWidth());
    document.body.style.setProperty('--dock-w', `${width}px`);
    document.body.style.setProperty('--dock-inset', `${Math.max(EDGE, Math.floor((gutterWidth() - width) / 2))}px`);
    document.body.classList.toggle('can-dock-card', canDockCard());
    document.body.classList.toggle('can-dock-sheet', canDockSheet());
}

function canDockCard() {
    return studyViewOpen() && panelWidth() >= PANEL_MIN;
}
function canDockSheet() {
    return !document.body.classList.contains('desktop-workspace')
        && panelWidth() >= PANEL_MIN
        && (studyViewOpen() || window.innerWidth / layoutZoom() >= SETUP_MIN_WINDOW);
}

const isShown = el => !el.classList.contains('hidden') && !el.hidden;

function closeButtonFor(id) {
    return () => {
        const button = document.getElementById(`close${id[0].toUpperCase()}${id.slice(1)}`);
        if (button) button.click();
        else document.getElementById(id)?.classList.add('hidden');
    };
}

const PRIORITY_DEFAULT = 10;
const PRIORITY_KNOWLEDGE = 20;
const PRIORITY_STUDY = 30;

// home: the side it prefers. card: closes with the card. stacks: may open
// over settings. onlyOverSettings: centred unless settings is open.
// priority: when only one gutter is free, a higher number replaces a lower.
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
    { id: 'knowledgeOverviewModal', home: 'right', card: true, centred: () => true, priority: PRIORITY_KNOWLEDGE,
      open: el => !el.hidden && !el.classList.contains('is-closing'),
      close: () => window.closeKnowledgeOverview?.() },
    { id: 'rareUsesModal', home: 'right', card: true, priority: PRIORITY_KNOWLEDGE,
      open: el => !el.hidden,
      close: () => window.closeRareUsesModal?.() },
    { id: 'studyChoiceSheet', home: 'left', priority: PRIORITY_STUDY,
      open: el => el.isConnected && !el.classList.contains('is-closing'),
      close: () => window.closeChoiceSheet?.('studyChoiceSheet', true) },
    // Settings, and the sheets about you and the session. The full Settings
    // page is a wide sheet over the page; only Study settings, opened from a
    // set, docks beside the card.
    { id: 'settingsModal', home: 'left', settings: true,
      centred: el => !el.classList.contains('settings-study-only'),
      open: isShown, close: closeButtonFor('settingsModal') },
    ...['statsModal', 'totalStatsModal', 'reviewHomeModal', 'spacedRepetitionInfoModal', 'keyboardShortcutsModal', 'helpModal'].map(id => ({
        id, home: 'left', stacks: true,
        centred: id === 'totalStatsModal' ? () => true : undefined,
        stackOver: id === 'spacedRepetitionInfoModal' ? 'reviewHomeModal' : null,
        open: isShown, close: closeButtonFor(id) })),
    // Setup-page reference sheets: word lists and rules.
    ...['extrasModal', 'cognateRulesModal'].map(id => ({
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

function occupantPriority(occupant) {
    return occupant.priority || PRIORITY_DEFAULT;
}

function keyboardHoldsLeft() {
    if (!canDockCard()) return false;
    if (openOn('left').length) return false;
    const guide = document.getElementById('desktopKeyboardGuide');
    return Boolean(guide && !guide.classList.contains('collapsed') && studyViewOpen());
}

function usableSides(occupant) {
    const prio = occupantPriority(occupant);
    const order = occupant.home === 'left' ? ['left', 'right'] : ['right', 'left'];
    return order.filter(side => {
        if (side === 'left' && keyboardHoldsLeft() && prio < PRIORITY_STUDY) return false;
        return true;
    });
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

    if (occupant.centred?.(el)) {
        mark(el, null);
        return null;
    }
    if (occupant.settings) {
        // Settings is the base of the left: it clears what was there.
        closeAll(openOn('left', occupant.id));
        mark(el, 'left');
        return 'left';
    }

    // Over the centred Settings page a sheet centres too, on top of it.
    if (occupant.stacks && isOpen(byId.settingsModal) && !sideOf(byId.settingsModal)) {
        mark(el, null);
        return null;
    }

    const parent = occupant.stackOver ? byId[occupant.stackOver] : null;
    if (parent && isOpen(parent) && sideOf(parent)) {
        // A short explainer opened from a sheet belongs directly above that
        // sheet, on the same side, without replacing or moving its context.
        const side = sideOf(parent);
        mark(el, side, true);
        return side;
    }

    if (occupant.stacks && settingsOpen()) {
        // Over settings; one sheet at a time on top of it.
        closeAll(openOn('left', occupant.id).filter(o => !o.settings));
        mark(el, 'left', true);
        return 'left';
    }

    // Usable gutters first: empty preferred side, then the other empty side.
    // The keyboard hint occupies the left gutter, so card sheets only get
    // one slot until Study options (higher priority) takes the left.
    const sides = usableSides(occupant);
    const prio = occupantPriority(occupant);
    for (const side of sides) {
        if (!openOn(side, occupant.id).length) {
            mark(el, side);
            return side;
        }
    }

    // No empty usable gutter. Privileged sheets replace a weaker occupant;
    // ordinary card panels still replace whoever is on their home side.
    for (const side of sides) {
        const there = openOn(side, occupant.id);
        const weaker = there.filter(o => occupantPriority(o) < prio);
        const peers = there.filter(o => occupantPriority(o) <= prio);
        if (weaker.length) {
            closeAll(weaker);
            if (!openOn(side, occupant.id).length) {
                mark(el, side);
                return side;
            }
        }
        if (prio <= PRIORITY_DEFAULT || peers.length === there.length) {
            closeAll(there);
            mark(el, side);
            return side;
        }
    }
    mark(el, null);
    return null;
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
function placeById(id) {
    const occupant = byId[id];
    return occupant ? place(occupant) : null;
}

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
        // Settings switches between its centred page and docked Study
        // settings while open; place it again when that changes.
        const shapeChanged = nowOpen && wasOpen && occupant.centred
            && occupant.centred(el) === Boolean(sideOf(occupant));
        if ((nowOpen && !wasOpen) || shapeChanged) place(occupant);
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
    function refreshPlacement() {
        applyPanelWidth();
        const open = OCCUPANTS.filter(isOpen);
        // Clear invalid slots together before trying to dock again. Preserve
        // valid slots, especially sheets stacked over settings, on a resize.
        for (const occupant of open) {
            const el = elementOf(occupant);
            const fits = occupant.panel ? canDockCard() : canDockSheet();
            if (!fits || occupant.centred?.(el)) {
                if (occupant.panel) stowCardPanel(el);
                else mark(el, null);
            }
        }
        for (const occupant of open.filter(isOpen)) {
            const el = elementOf(occupant);
            const side = sideOf(occupant) || place(occupant);
            if (occupant.panel && side) hostCardPanel(el);
        }
    }
    function schedulePlacement() {
        cancelAnimationFrame(resizeFrame);
        resizeFrame = requestAnimationFrame(refreshPlacement);
    }
    window.addEventListener('resize', schedulePlacement);
    const centreObserver = new ResizeObserver(schedulePlacement);
    for (const el of document.querySelectorAll('.card-container, #flashcard, #setupPanel')) centreObserver.observe(el);
    // Text size can change without a window resize.
    new MutationObserver(schedulePlacement).observe(document.documentElement, {
        attributes: true, attributeFilter: ['data-text-size'],
    });
    // knowledgeOverviewModal and rareUsesModal are created on first use; catch
    // them when they land.
    new MutationObserver(watchModals).observe(document.body, { childList: true });
    // Leaving the study view closes what described its cards and its session.
    // Settings, and whatever is stacked over it, belongs to the app, not the
    // set, so it stays.
    const app = document.getElementById('appContent');
    if (app) {
        new MutationObserver(() => {
            if (!app.classList.contains('hidden')) {
                schedulePlacement();
                return;
            }
            closeAll(OCCUPANTS.filter(o => isOpen(o) && !o.settings
                && elementOf(o).dataset.dockStack === undefined
                && (o.card || sideOf(o) === 'left' || sideOf(o) === 'right')));
            schedulePlacement();
        }).observe(app, { attributes: true, attributeFilter: ['class'] });
    }
    applyPanelWidth();
}

if (!window.sideDock) {
    window.sideDock = {
        canDockCard, canDockSheet, openCardPanel, stowCardPanel, placeById,
        keepsSettingsOpen, closeForFront, beforeBackRender, closeTopmost,
    };
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init, { once: true });
    } else {
        init();
    }
}
