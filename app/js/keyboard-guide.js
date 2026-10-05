// Both shortcut references share this catalogue. Key handling stays in the
// study/search modules; these rows are deliberately not action buttons.
export const SHORTCUTS = [
    { id: 'flip', group: 'Study', label: 'Flip card', keys: [['Space']], compact: true },
    { id: 'correct', group: 'Study', label: 'Got it', keys: [['Enter'], ['C']], compact: true },
    { id: 'incorrect', group: 'Study', label: 'Needs practice', keys: [['X'], ['1']], compact: true },
    { id: 'speak', group: 'Study', label: 'Pronounce word', keys: [['A']], compact: true },
    { id: 'cards', group: 'Navigation', label: 'Previous / next card', keys: [['←', '→']], compact: true },
    { id: 'meanings', group: 'Navigation', label: 'Previous / next meaning', keys: [['↑', '↓']], compact: true, note: 'For cards with multiple meanings.', condition: 'meanings' },
    { id: 'examples', group: 'Navigation', label: 'Next example / expression', keys: [['Tab']], note: 'Cycles when the selected meaning has multiple examples or expressions.' },
    { id: 'next', group: 'Navigation', label: 'Next card (alternative)', keys: [['Shift', 'Tab']], chord: true },
    { id: 'back', group: 'Navigation', label: 'Close panel / go back', keys: [['Esc']], note: 'Closes the open panel first; otherwise goes back.' },
    { id: 'find', group: 'App tools', label: 'Find a word', keys: [['Mod', 'F']], chord: true },
    { id: 'progress', group: 'App tools', label: 'Study progress', keys: [['Mod', 'S']], chord: true },
    { id: 'preferences', group: 'App tools', label: 'Study preferences', keys: [['Mod', 'P']], chord: true },
    { id: 'shortcuts', group: 'App tools', label: 'All shortcuts', keys: [['?']] },
    { id: 'flag', group: 'Audit tools', label: 'Report a card issue', keys: [['F'], ['Mod', 'Shift', 'F']], chord: true, eligibility: 'audit' },
    { id: 'model', group: 'Audit tools', label: 'Data and model info', keys: [['Mod', 'I']], chord: true, eligibility: 'owner' },
];

export function availableShortcuts({ canFlag = false, isOwner = false } = {}) {
    return SHORTCUTS.filter(item => !item.eligibility ||
        (item.eligibility === 'audit' ? canFlag : isOwner));
}

export function shortcutKeys(item, isMac = false, compact = false) {
    const alternatives = compact ? item.keys.slice(0, 1) : item.keys;
    return alternatives.map(keys => `<span class="shortcut-key-combination">${keys.map(key =>
        `<kbd class="shortcut-kbd">${key === 'Mod' ? (isMac ? '⌘' : 'Ctrl') : key}</kbd>`
    ).join(item.chord ? '<span class="shortcut-plus" aria-hidden="true">+</span>' : '')}</span>`
    ).join('<span class="shortcut-or">or</span>');
}

export function renderShortcutRows(items, { isMac = false, compact = false, meaningCount = 0 } = {}) {
    return items.map(item => {
        const unavailable = item.condition === 'meanings' && meaningCount < 2;
        const note = compact ? '' : item.note;
        return `<div class="shortcut-row${unavailable ? ' is-unavailable' : ''}" data-shortcut="${item.id}">
            <span class="shortcut-copy"><span class="shortcut-desc">${item.label}</span>${note ? `<span class="shortcut-note">${note}</span>` : ''}</span>
            <span class="shortcut-kbd-group">${shortcutKeys(item, isMac, compact)}</span>
        </div>`;
    }).join('');
}

let readContext = () => ({});
let lastRender = '';
export function refreshKeyboardGuide() {
    const context = readContext();
    const isMac = /Mac|iPhone|iPad|iPod/i.test(navigator.platform || navigator.userAgent || '');
    const meaningCount = context.card?.meanings?.length || 0;
    const signature = JSON.stringify([isMac, meaningCount, context.canFlag, context.isOwner]);
    if (signature === lastRender) return;
    lastRender = signature;
    const items = availableShortcuts(context);
    const options = { isMac, meaningCount };
    const compact = document.getElementById('keyboardGuideRows');
    if (compact) {
        const order = ['flip', 'correct', 'incorrect', 'cards', 'meanings', 'speak'];
        compact.innerHTML = renderShortcutRows(order.map(id => items.find(item => item.id === id)), { ...options, compact: true });
    }
    const reference = document.getElementById('keyboardShortcutGroups');
    if (reference) reference.innerHTML = ['Study', 'Navigation', 'App tools', 'Audit tools'].map(group => {
        const rows = items.filter(item => item.group === group);
        return rows.length ? `<section class="shortcut-group"><h4 class="shortcut-group-title">${group}</h4>${renderShortcutRows(rows, options)}</section>` : '';
    }).join('');
    const report = document.getElementById('keyboardGuideReport');
    if (report) report.hidden = !context.canFlag;
}

export function initKeyboardGuide({ getContext, openReference }) {
    readContext = getContext;
    refreshKeyboardGuide();
    const guide = document.getElementById('desktopKeyboardGuide');
    const toggle = document.getElementById('kbGuideToggle');
    const hide = document.getElementById('keyboardGuideHide');
    if (!guide || !toggle || !hide) return;
    const storageKey = 'fluency.kbGuideCollapsedV2';
    let collapsed = false;
    try { collapsed = localStorage.getItem(storageKey) === '1'; } catch (_) { /* Private browsing. */ }
    const setOpen = open => {
        guide.classList.toggle('kb-guide-popover-open', open);
        document.body.classList.toggle('kb-guide-open', open);
        toggle.setAttribute('aria-expanded', String(open));
        toggle.title = open ? 'Hide keyboard shortcuts' : 'Show keyboard shortcuts';
        toggle.setAttribute('aria-label', toggle.title);
    };
    const setCollapsed = value => {
        collapsed = value;
        guide.classList.toggle('collapsed', value);
        try { localStorage.setItem(storageKey, value ? '1' : '0'); } catch (_) { /* Private browsing. */ }
        const sidebar = document.getElementById('kbToggleSidebar');
        if (sidebar) {
            sidebar.title = value ? 'Show keyboard shortcuts' : 'Hide keyboard shortcuts';
            sidebar.setAttribute('aria-label', sidebar.title);
        }
    };
    const buttonShown = () => getComputedStyle(toggle).display !== 'none';
    const hideGuide = () => {
        setOpen(false);
        setCollapsed(true);
        if (buttonShown()) toggle.focus();
    };
    setCollapsed(collapsed);
    hide.addEventListener('click', hideGuide);
    toggle.addEventListener('click', event => {
        event.stopPropagation();
        if (guide.classList.contains('kb-guide-popover-open')) {
            hideGuide();
            return;
        }
        setCollapsed(false);
        // A wide window reveals the persistent panel. Smaller windows need
        // the popover; do not leave it floating when there is room beside us.
        setOpen(buttonShown());
        hide.focus();
    });
    document.getElementById('kbToggleSidebar')?.addEventListener('click', () => {
        if (!collapsed || guide.classList.contains('kb-guide-popover-open')) hideGuide();
        else toggle.click();
    });
    document.getElementById('keyboardGuideAll')?.addEventListener('click', () => {
        setOpen(false);
        openReference();
    });
    window.closeKeyboardGuidePopover = () => {
        if (!guide.classList.contains('kb-guide-popover-open')) return false;
        setOpen(false);
        if (buttonShown()) toggle.focus();
        return true;
    };
    document.addEventListener('click', event => {
        if (!guide.contains(event.target) && !toggle.contains(event.target)) setOpen(false);
    });
    const closeIfHidden = () => {
        if (!buttonShown()) setOpen(false);
    };
    window.addEventListener('resize', closeIfHidden);
    // Docking and leaving study can hide the button without a resize.
    const observer = new MutationObserver(closeIfHidden);
    observer.observe(document.getElementById('appContent'), { attributes: true, attributeFilter: ['class'] });
    observer.observe(document.body, { attributes: true, subtree: true, attributeFilter: ['data-dock'] });
}
