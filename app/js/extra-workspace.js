// Extra practice & tools workspace — manages the Extra menu and embedded conjugation drills.

let scriptsLoaded = false;
const loadedDecks = new Set();

function loadScript(src) {
    return new Promise((resolve, reject) => {
        const existing = document.querySelector(`script[src="${src}"]`);
        if (existing) {
            resolve();
            return;
        }
        const script = document.createElement('script');
        script.src = src;
        script.onload = () => resolve();
        script.onerror = () => reject(new Error(`Failed to load script: ${src}`));
        document.head.appendChild(script);
    });
}

export function currentLanguageKey() {
    if (window.activeArtist && window.activeArtist.language && window.activeArtist.language === window.selectedLanguage) {
        return window.activeArtist.language;
    }
    return window.selectedLanguage || 'spanish';
}

export function currentLanguageName() {
    const key = currentLanguageKey();
    return window._normalModeLangConfigs?.[key]?.name
        || window.config?.languages?.[key]?.name
        || (key.charAt(0).toUpperCase() + key.slice(1));
}

export function conjugationDrillCode() {
    const key = currentLanguageKey();
    return window.config?.languages?.[key]?.conjugationDrill || null;
}

export function updateExtraUI() {
    const langKey = currentLanguageKey();
    const langName = currentLanguageName();
    const drillCode = conjugationDrillCode();

    const contextEl = document.getElementById('extraLanguageContext');
    if (contextEl) {
        contextEl.textContent = `${langName} · Extra`;
    }

    const card = document.getElementById('extraConjugationsCard');
    const desc = document.getElementById('extraConjugationsDesc');
    if (card && desc) {
        if (drillCode) {
            card.disabled = false;
            desc.textContent = `Master ${langName} verb conjugations, tenses, and irregular forms across all persons.`;
        } else {
            card.disabled = true;
            desc.textContent = `Verb conjugations are not yet available for ${langName}.`;
        }
    }
}

export async function openConjugationsScreen() {
    const drillCode = conjugationDrillCode() || 'es';
    const menuView = document.getElementById('extraMenuView');
    const conjView = document.getElementById('extraConjugationsView');

    if (menuView) menuView.hidden = true;
    if (conjView) conjView.hidden = false;

    window._embeddedConjugation = true;
    window._conjugationBasePath = 'conjugation/data/';
    window.onLeaveConjugationMode = backToExtraMenu;

    try {
        if (!window.ConjugationProgress) {
            await loadScript('conjugation/progress.js?v=20261016');
        }
        if (!window.conjugationBoot) {
            await loadScript('conjugation/app.js?v=20261016');
        }
        if (!loadedDecks.has(drillCode)) {
            await loadScript(`conjugation/data/${drillCode}.js?v=20261016`);
            try {
                await loadScript(`conjugation/data/${drillCode}-not-verbs.js?v=20261016`);
            } catch (_) {
                // not-verbs is optional
            }
            loadedDecks.add(drillCode);
        }

        if (typeof window.conjugationBoot === 'function') {
            window.conjugationBoot(drillCode);
        }
    } catch (err) {
        console.error('Failed to boot conjugations screen:', err);
    }
}

export function backToExtraMenu() {
    const menuView = document.getElementById('extraMenuView');
    const conjView = document.getElementById('extraConjugationsView');
    if (conjView) conjView.hidden = true;
    if (menuView) menuView.hidden = false;
}

export function openExtraModal() {
    updateExtraUI();
    backToExtraMenu();
    const modal = document.getElementById('extraModal');
    if (modal) {
        modal.classList.remove('hidden');
    }
}

export function closeExtraModal() {
    const modal = document.getElementById('extraModal');
    if (modal) {
        modal.classList.add('hidden');
    }
}

export function initExtraWorkspace() {
    updateExtraUI();

    const exploreBtn = document.getElementById('desktopExploreBtn');
    exploreBtn?.addEventListener('click', () => {
        openExtraModal();
    });

    const closeBtn = document.getElementById('closeExtraModal');
    closeBtn?.addEventListener('click', closeExtraModal);

    const conjCard = document.getElementById('extraConjugationsCard');
    conjCard?.addEventListener('click', () => {
        if (!conjCard.disabled) {
            openConjugationsScreen();
        }
    });

    const backBtn = document.getElementById('extraConjugationsBackBtn');
    backBtn?.addEventListener('click', backToExtraMenu);

    window.openExtraModal = openExtraModal;
    window.openConjugationsScreen = () => {
        openExtraModal();
        openConjugationsScreen();
    };
    window.updateExtraUI = updateExtraUI;
}

if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initExtraWorkspace, { once: true });
} else {
    initExtraWorkspace();
}
