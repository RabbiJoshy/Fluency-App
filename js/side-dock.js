// Side docking on a wide desktop. docs/ui/UI_WORK_ORDERS.md #8 has the rule
// and the reasons. In one sentence: anything that does not move you within
// your set opens at the side when there is room.
//
//   right gutter  about THIS card: dictionary, synonyms, conjugation, card
//                 data, lyric breakdown, rare-sense knowledge, word search.
//                 One at a time. Closed when the card changes or turns to its
//                 front, because what they show gives the answer away.
//   left gutter   about the SESSION: saved words, progress, shortcuts, help.
//                 One at a time. They stay open while you study, so their
//                 transparent backdrop lets clicks through to the card.
//
// Card panels are rendered inside the card's back face, where .card-face
// clips them and the flip transform makes even position:fixed resolve
// against the card. So they are hosted on <body> while docked and stowed back
// into the back face on close — the pattern the conjugation panel started.
//
// Loaded once from flashcards.js and reached through window.sideDock, so that
// flashcards-conj.js can use it without importing it under a second ?v= tag
// (a module imported under two URLs executes twice).

const DOCK_QUERY = '(min-width: 1360px)';

function studyViewOpen() {
    const app = document.getElementById('appContent');
    return Boolean(app && !app.classList.contains('hidden'));
}

function canDock() {
    return Boolean(window.matchMedia?.(DOCK_QUERY).matches) && studyViewOpen();
}

const isShown = el => !el.classList.contains('hidden') && !el.hidden;

// Each occupant is closed through its owner's own code path so its cleanup
// runs. `cardPanel` ones live in the back face; `cardBound` ones are modals
// that still describe the card on screen.
const RIGHT = [
    { id: 'synonymsPanel', cardPanel: true,
      open: el => el.classList.contains('visible'),
      close: () => window.toggleSynonymsPanel?.() },
    { id: 'conjugationTable', cardPanel: true,
      open: el => el.classList.contains('visible'),
      close: () => window.toggleConjugationTable?.() },
    { id: 'spanishDictPanel', cardPanel: true,
      open: el => !el.hidden,
      close: () => window.toggleSpanishDictPanel?.(false) },
    { id: 'provenancePanel', cardPanel: true,
      open: el => el.style.display === 'block',
      close: () => window.toggleProvenancePanel?.(false) },
    { id: 'lyricBreakdownModal', cardBound: true,
      open: isShown,
      close: () => window.hideLyricBreakdown?.() },
    { id: 'knowledgeOverviewModal', cardBound: true,
      open: el => !el.hidden && !el.classList.contains('is-closing'),
      close: () => window.closeKnowledgeOverview?.() },
    { id: 'findWordModal',
      open: isShown,
      close: () => document.getElementById('closeFindWordModal')?.click() },
];

const LEFT = ['savedWordsModal', 'statsModal', 'keyboardShortcutsModal', 'helpModal'].map(id => ({
    id,
    open: isShown,
    // Every one of these has a #close<Id> button wired to its own cleanup.
    close: () => {
        const button = document.getElementById(`close${id[0].toUpperCase()}${id.slice(1)}`);
        if (button) button.click();
        else document.getElementById(id)?.classList.add('hidden');
    },
}));

function isOpen(occupant) {
    const el = document.getElementById(occupant.id);
    return Boolean(el && occupant.open(el));
}

function closeWhere(list, predicate) {
    let closed = false;
    for (const occupant of list) {
        if (predicate(occupant) && isOpen(occupant)) {
            occupant.close();
            closed = true;
        }
    }
    return closed;
}

// An occupant calls this as it opens, so two never overlap in one gutter.
function claim(ownerId) {
    if (!canDock()) return;
    const side = LEFT.some(o => o.id === ownerId) ? LEFT : RIGHT;
    closeWhere(side, o => o.id !== ownerId);
}

function hostCardPanel(panel) {
    if (!panel) return;
    if (panel.parentElement !== document.body) document.body.appendChild(panel);
    panel.classList.add('is-docked');
}

function stowCardPanel(panel) {
    if (!panel) return;
    panel.classList.remove('is-docked');
    const host = document.getElementById('backContent');
    if (host && panel.parentElement !== host) host.appendChild(panel);
}

// Open a card panel: docked beside the card when there is room, otherwise
// left where it was rendered, over the card as before. Returns whether it
// docked so the caller can skip its own in-card handling.
function openCardPanel(panel) {
    if (!panel || !canDock()) return false;
    claim(panel.id);
    hostCardPanel(panel);
    return true;
}

// The card turned to its front: what the right gutter shows would give the
// answer away. Narrow layouts keep their panels inside the card, which turn
// away with the back face on their own, so they are left alone.
function closeForFront() {
    if (!canDock()) return;
    closeWhere(RIGHT, o => o.cardPanel || o.cardBound);
}

// The back face is about to be re-rendered. Panels hosted on <body> belong to
// the markup being replaced, so drop them rather than leave a second node
// claiming the same id; and when the card itself changed, close the modals
// that described the old one.
let lastCard = null;
function beforeBackRender(card) {
    for (const occupant of RIGHT) {
        if (!occupant.cardPanel) continue;
        const el = document.getElementById(occupant.id);
        if (el?.parentElement === document.body) el.remove();
    }
    if (card !== lastCard) {
        if (lastCard && canDock()) closeWhere(RIGHT, o => o.cardBound);
        lastCard = card;
    }
}

// Escape closes the nearest open panel instead of leaving the set.
function closeTopmost() {
    for (const list of [RIGHT, LEFT]) {
        for (const occupant of list) {
            if (isOpen(occupant)) {
                occupant.close();
                return true;
            }
        }
    }
    return false;
}

// Modals open through their own modules, so watch them rather than edit every
// opener: when one appears in a gutter, it claims that gutter.
function watchModal(el, occupant) {
    if (!el || el._sideDockWatched) return;
    el._sideDockWatched = true;
    let wasOpen = occupant.open(el);
    new MutationObserver(() => {
        const nowOpen = occupant.open(el);
        if (nowOpen && !wasOpen) claim(occupant.id);
        wasOpen = nowOpen;
    }).observe(el, { attributes: true, attributeFilter: ['class', 'hidden'] });
}

function watchModals() {
    for (const occupant of [...RIGHT, ...LEFT]) {
        if (occupant.cardPanel) continue;
        watchModal(document.getElementById(occupant.id), occupant);
    }
}

function init() {
    watchModals();
    // knowledgeOverviewModal is created on first use; catch it when it lands.
    new MutationObserver(watchModals).observe(document.body, { childList: true });
    // Leaving the study view closes everything docked in it, so a session
    // sheet does not follow you back to the setup page.
    const app = document.getElementById('appContent');
    if (app) {
        new MutationObserver(() => {
            if (app.classList.contains('hidden')) {
                closeWhere(RIGHT, () => true);
                closeWhere(LEFT, () => true);
            }
        }).observe(app, { attributes: true, attributeFilter: ['class'] });
    }
}

if (!window.sideDock) {
    window.sideDock = {
        canDock, claim, openCardPanel, stowCardPanel,
        closeForFront, beforeBackRender, closeTopmost,
    };
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init, { once: true });
    } else {
        init();
    }
}
