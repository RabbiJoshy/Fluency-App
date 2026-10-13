// Setup uses a persistent desktop navigation; studying gives the gutters
// back to side-dock.js. Reuse the real header buttons and their handlers.
const PAGE_IDS = [
    'settingsModal', 'totalStatsModal', 'reviewHomeModal', 'helpModal',
    'learningContextModal', 'extrasModal', 'cognateRulesModal',
    'fastModeModal', 'vocabularyImportModal', 'aboutProjectModal',
];
const NAV_IDS = ['desktopStudyBtn', 'desktopWordsBtn', 'topBarProgressBtn',
    'topBarGearBtn', 'topBarUserName', 'helpBtn', 'learningContextBtn'];

function initDesktopShell() {
    const setup = document.getElementById('setupPanel');
    const app = document.getElementById('appContent');
    const header = document.getElementById('topBar');
    if (!setup || !app || !header) return;
    const pages = PAGE_IDS.map(id => document.getElementById(id)).filter(Boolean);
    const modalAttributes = new Map(pages.map(el => [el, el.getAttribute('aria-modal')]));
    let activeNav = 'desktopStudyBtn';

    function closePages() {
        for (const page of pages.filter(el => !el.hidden && !el.classList.contains('hidden'))) {
            // Run the existing close handler so its cleanup/back behavior is kept.
            document.getElementById(`close${page.id[0].toUpperCase()}${page.id.slice(1)}`)?.click();
            page.classList.add('hidden');
        }
    }
    function refresh() {
        const zoom = parseFloat(getComputedStyle(document.body).zoom) || 1;
        const desktop = window.innerWidth >= 1024 && window.innerWidth / zoom >= 1024;
        const studying = !app.classList.contains('hidden');
        const workspace = desktop && !studying && !setup.classList.contains('hidden');
        document.body.classList.toggle('desktop-workspace', workspace);
        document.body.classList.toggle('desktop-studying', desktop && studying);
        header.setAttribute('role', workspace ? 'navigation' : 'region');
        header.setAttribute('aria-label', workspace ? 'Main navigation' : 'App controls');
        let anyPage = false;
        for (const page of pages) {
            page.classList.toggle('desktop-workspace-page', workspace);
            const original = modalAttributes.get(page);
            if (workspace) page.setAttribute('aria-modal', 'false');
            else if (original !== null) page.setAttribute('aria-modal', original);
            else page.removeAttribute('aria-modal');
            if (!page.hidden && !page.classList.contains('hidden')) anyPage = true;
        }
        if (!anyPage) activeNav = 'desktopStudyBtn';
        for (const id of NAV_IDS) {
            const button = document.getElementById(id);
            if (workspace && id === activeNav) button?.setAttribute('aria-current', 'page');
            else button?.removeAttribute('aria-current');
        }
        // The setup underneath a workspace page must not receive keyboard focus.
        for (const child of setup.children) {
            if (child !== header) child.inert = workspace && anyPage;
        }
    }
    for (const id of NAV_IDS) {
        document.getElementById(id)?.addEventListener('click', () => {
            if (!document.body.classList.contains('desktop-workspace')) return;
            closePages();
            activeNav = id;
        }, { capture: true });
    }
    document.getElementById('desktopStudyBtn')?.addEventListener('click', () => {
        refresh();
    });
    document.getElementById('desktopWordsBtn')?.addEventListener('click', () => {
        window.showSettingsModalWithTab?.('vocabulary');
    });
    const observer = new MutationObserver(refresh);
    observer.observe(setup, { attributes: true, attributeFilter: ['class'] });
    observer.observe(app, { attributes: true, attributeFilter: ['class'] });
    // Observe visibility only; writing navigation attributes cannot retrigger it.
    for (const page of pages) observer.observe(page, { attributes: true, attributeFilter: ['class', 'hidden'] });
    window.addEventListener('resize', refresh);
    new MutationObserver(refresh).observe(document.documentElement, {
        attributes: true, attributeFilter: ['data-text-size'],
    });
    refresh();
}

if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initDesktopShell, { once: true });
} else {
    initDesktopShell();
}
