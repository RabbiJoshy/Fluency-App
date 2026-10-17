// Extra practice & tools workspace — manages the Extra menu, embedded conjugation drills,
// and embedded lyrics translation view.

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

export function isMusicMode() {
    const mode = window.currentLearningMode?.() || null;
    if (mode === 'lyrics' || mode === 'live') return true;
    if (window.activeArtist) return true;
    if (window.musicWorkspaceActive?.()) return true;
    return false;
}

export function conjugationDrillCode() {
    const key = currentLanguageKey();
    return window.config?.languages?.[key]?.conjugationDrill || null;
}

export function updateExtraUI() {
    const langKey = currentLanguageKey();
    const langName = currentLanguageName();
    const drillCode = conjugationDrillCode();
    const inMusic = isMusicMode();

    const contextEl = document.getElementById('extraLanguageContext');
    if (contextEl) {
        if (inMusic) {
            const artistName = window.activeArtist?.name || '';
            contextEl.textContent = artistName
                ? `${langName} · ${artistName} · Extra`
                : `${langName} · Music · Extra`;
        } else {
            contextEl.textContent = `${langName} · Extra`;
        }
    }

    const lyricsCard = document.getElementById('extraLyricsCard');
    const lyricsDesc = document.getElementById('extraLyricsDesc');
    if (lyricsCard) {
        const lyricsSupported = window.config?.languages?.[langKey]?.capabilities?.lyrics !== false;
        lyricsCard.hidden = !inMusic || !lyricsSupported;
        if (lyricsDesc && inMusic) {
            const artistName = window.activeArtist?.name;
            lyricsDesc.textContent = artistName
                ? `Read and listen to ${artistName}’s songs line by line with synchronized translation and word lookups.`
                : 'Read and listen to song lyrics line by line with synchronized translation and word lookups.';
        }
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

function pauseLyricsIframe() {
    try {
        const iframe = document.getElementById('extraLyricsIframe');
        iframe?.contentWindow?.postMessage({ type: 'fluency-pause' }, '*');
    } catch (_) {}
}

export async function openConjugationsScreen() {
    const drillCode = conjugationDrillCode() || 'es';
    const menuView = document.getElementById('extraMenuView');
    const conjView = document.getElementById('extraConjugationsView');
    const lyricsView = document.getElementById('extraLyricsView');

    pauseLyricsIframe();
    if (lyricsView) lyricsView.hidden = true;
    if (menuView) menuView.hidden = true;
    if (conjView) conjView.hidden = false;

    window._embeddedConjugation = true;
    window._conjugationBasePath = 'conjugation/data/';
    window.onLeaveConjugationMode = backToExtraMenu;

    try {
        if (!window.ConjugationProgress) {
            await loadScript('conjugation/progress.js?v=8a844388');
        }
        if (!window.conjugationBoot) {
            await loadScript('conjugation/app.js?v=8a844388');
        }
        if (!loadedDecks.has(drillCode)) {
            await loadScript(`conjugation/data/${drillCode}.js?v=8a844388`);
            try {
                await loadScript(`conjugation/data/${drillCode}-not-verbs.js?v=8a844388`);
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

export function openLyricsViewScreen() {
    const langKey = currentLanguageKey();
    const menuView = document.getElementById('extraMenuView');
    const conjView = document.getElementById('extraConjugationsView');
    const lyricsView = document.getElementById('extraLyricsView');
    const iframe = document.getElementById('extraLyricsIframe');

    if (menuView) menuView.hidden = true;
    if (conjView) conjView.hidden = true;
    if (lyricsView) lyricsView.hidden = false;

    if (iframe) {
        const langCode = window.fluencyRoutes?.routeCodeFor?.(langKey, window.config?.languages) || langKey;
        const baseHref = window.fluencyRoutes?.lyricsViewHref?.(null, langKey) || `lyrics-view/?lang=${langCode}`;
        const sep = baseHref.includes('?') ? '&' : '?';
        const targetSrc = `${baseHref}${sep}embedded=1`;
        if (iframe.getAttribute('src') !== targetSrc) {
            iframe.src = targetSrc;
        }
    }
}

export function backToExtraMenu() {
    pauseLyricsIframe();
    const menuView = document.getElementById('extraMenuView');
    const conjView = document.getElementById('extraConjugationsView');
    const lyricsView = document.getElementById('extraLyricsView');
    if (conjView) conjView.hidden = true;
    if (lyricsView) lyricsView.hidden = true;
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
    pauseLyricsIframe();
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

    const lyricsCard = document.getElementById('extraLyricsCard');
    lyricsCard?.addEventListener('click', () => {
        openLyricsViewScreen();
    });

    const conjCard = document.getElementById('extraConjugationsCard');
    conjCard?.addEventListener('click', () => {
        if (!conjCard.disabled) {
            openConjugationsScreen();
        }
    });

    const backBtn = document.getElementById('extraConjugationsBackBtn');
    backBtn?.addEventListener('click', backToExtraMenu);

    const lyricsBackBtn = document.getElementById('extraLyricsBackBtn');
    lyricsBackBtn?.addEventListener('click', backToExtraMenu);

    window.addEventListener('message', event => {
        if (event.data?.type === 'fluency-back-to-extra') {
            backToExtraMenu();
        }
    });

    window.openExtraModal = openExtraModal;
    window.openConjugationsScreen = () => {
        openExtraModal();
        openConjugationsScreen();
    };
    window.openLyricsViewScreen = () => {
        openExtraModal();
        openLyricsViewScreen();
    };
    window.updateExtraUI = updateExtraUI;
}

if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initExtraWorkspace, { once: true });
} else {
    initExtraWorkspace();
}
