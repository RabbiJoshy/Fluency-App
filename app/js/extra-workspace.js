window._conjugationDecks = window._conjugationDecks || {};
if (!window.registerConjugationDeck) {
    window.registerConjugationDeck = function (payload) {
        window._conjugationDecks[payload.language] = payload;
    };
}
if (!window.registerConjugationNotVerbs) {
    window._conjugationNotVerbs = window._conjugationNotVerbs || {};
    window.registerConjugationNotVerbs = function (payload) {
        const words = {};
        (payload.words || []).forEach(w => { words[w] = true; });
        window._conjugationNotVerbs[payload.language] = words;
    };
}

const scriptPromises = new Map();

// The app's own folder (this file is app/js/). Production lives under
// /Fluency-App/, so scripts resolve from here, not from the site root or the
// /conjugation address the drill puts in the bar.
const APP_ROOT = new URL('../', import.meta.url);

function loadScript(src) {
    const cleanSrc = src.replace(/^\/+/, '');
    const fullUrl = new URL(cleanSrc, APP_ROOT).href;

    if (scriptPromises.has(fullUrl)) {
        return scriptPromises.get(fullUrl);
    }

    const p = new Promise((resolve, reject) => {
        const existing = document.querySelector(`script[src="${src}"], script[src="${fullUrl}"]`);
        if (existing && existing.dataset.loaded === 'true') {
            resolve();
            return;
        }
        if (existing) {
            existing.addEventListener('load', () => resolve(), { once: true });
            existing.addEventListener('error', () => reject(new Error(`Failed to load script: ${src}`)), { once: true });
            return;
        }
        const script = document.createElement('script');
        script.src = fullUrl;
        script.onload = () => {
            script.dataset.loaded = 'true';
            resolve();
        };
        script.onerror = () => {
            scriptPromises.delete(fullUrl);
            reject(new Error(`Failed to load script: ${src}`));
        };
        document.head.appendChild(script);
    });

    scriptPromises.set(fullUrl, p);
    return p;
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

    const lyricsCard = document.getElementById('extraLyricsCard');
    const lyricsDesc = document.getElementById('extraLyricsDesc');
    if (lyricsCard) {
        const lyricsSupported = window.config?.languages?.[langKey]?.capabilities?.lyrics !== false
            && window.musicOpenFor?.(langKey) !== false;
        lyricsCard.hidden = !inMusic || !lyricsSupported;
        if (lyricsDesc) {
            lyricsDesc.textContent = 'Read and listen to the lyrics of any song line by line with synchronized translation and word lookups.';
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

export async function openConjugationsScreen(targetVerb = null, targetView = null) {
    const drillCode = conjugationDrillCode() || 'es';
    const menuView = document.getElementById('extraMenuView');
    const conjView = document.getElementById('extraConjugationsView');

    if (menuView) menuView.hidden = true;
    if (conjView) conjView.hidden = false;

    window._embeddedConjugation = true;
    window._conjugationBasePath = 'conjugation/data/';
    window.onLeaveConjugationMode = backToExtraMenu;

    try {
        const url = new URL(window.location.href);
        const base = url.pathname.replace(/\/conjugation\/?$/, '').replace(/\/+$/, '');
        const drillPath = `${base}/conjugation`;
        const search = targetVerb ? `?verb=${encodeURIComponent(targetVerb)}` : '';
        history.replaceState({ screen: 'conjugation' }, '', drillPath + search);
    } catch (_) {}

    try {
        if (!window.ConjugationProgress) {
            await loadScript('conjugation/progress.js?v=42d6f5c2');
        }
        if (!window.conjugationBoot) {
            await loadScript('conjugation/app.js?v=42d6f5c2');
        }
        if (!window._conjugationDecks || !window._conjugationDecks[drillCode]) {
            await loadScript(`conjugation/data/${drillCode}.js?v=42d6f5c2`);
            try {
                await loadScript(`conjugation/data/${drillCode}-not-verbs.js?v=42d6f5c2`);
            } catch (_) {
                // not-verbs is optional
            }
        }

        if (typeof window.conjugationBoot === 'function') {
            window.conjugationBoot(drillCode, targetVerb, targetView);
        }
    } catch (err) {
        console.error('Failed to boot conjugations screen:', err);
    }
}

export function openLyricsViewScreen() {
    openSongPickerScreen();
}

function escapeHtml(str) {
    if (!str) return '';
    return String(str)
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#39;');
}

const songsCache = new Map();
let currentLoadedSongs = [];

function getSongsFileName(langKey) {
    const code = window.fluencyRoutes?.routeCodeFor?.(langKey, window.config?.languages) || (langKey === 'spanish' ? 'es' : langKey);
    return code === 'es' ? 'probe_songs.json' : `${code}_probe_songs.json`;
}

async function fetchSongsForLanguage(langKey) {
    if (songsCache.has(langKey)) {
        return songsCache.get(langKey);
    }
    const fileName = getSongsFileName(langKey);
    const code = window.fluencyRoutes?.routeCodeFor?.(langKey, window.config?.languages) || (langKey === 'spanish' ? 'es' : langKey);
    let songs = [];
    try {
        const resp = await fetch(`turbo/${fileName}?v=20261017`);
        if (resp.ok) {
            const probe = await resp.json();
            probe.forEach((s, idx) => {
                s.id = s.spotifyId || `offline_${idx}`;
            });
            songs = [...probe];
        }
    } catch (err) {
        console.warn('Failed to fetch probe songs:', err);
    }

    if (code === 'es') {
        try {
            const catResp = await fetch('turbo/catalogue/index.json?v=20261017');
            if (catResp.ok) {
                const cat = await catResp.json();
                cat.forEach(entry => {
                    songs.push({
                        id: entry.id,
                        spotifyId: entry.id,
                        title: entry.title,
                        artist: entry.artist,
                        isCatalogue: true
                    });
                });
            }
        } catch (_) {}
    }

    songsCache.set(langKey, songs);
    return songs;
}

export function launchLyricsView(songParam) {
    const langKey = currentLanguageKey();
    const langCode = window.fluencyRoutes?.routeCodeFor?.(langKey, window.config?.languages) || (langKey === 'spanish' ? 'es' : langKey);
    let href = window.fluencyRoutes?.lyricsViewHref?.(null, langKey) || `lyrics-view/?lang=${langCode}`;
    const url = new URL(href, window.location.href);
    if (songParam) {
        url.searchParams.set('song', songParam);
    }
    window.location.href = url.toString();
}

function renderSongsList(songs) {
    const container = document.getElementById('extraSongsList');
    const emptyEl = document.getElementById('extraSongsEmpty');
    if (!container) return;
    container.innerHTML = '';

    if (!songs || songs.length === 0) {
        if (emptyEl) emptyEl.style.display = 'block';
        return;
    }
    if (emptyEl) emptyEl.style.display = 'none';

    songs.forEach(song => {
        const item = document.createElement('div');
        item.className = 'extra-song-item';
        item.setAttribute('role', 'listitem');
        item.innerHTML = `
            <div class="extra-song-item-left">
                <span class="extra-song-item-icon" aria-hidden="true">
                    <svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                        <path d="M9 18V5l12-2v13"></path>
                        <circle cx="6" cy="18" r="3"></circle>
                        <circle cx="18" cy="16" r="3"></circle>
                    </svg>
                </span>
                <div>
                    <div class="extra-song-item-title">${escapeHtml(song.title || 'Unknown title')}</div>
                    <div class="extra-song-item-artist">${escapeHtml(song.artist || 'Unknown artist')}</div>
                </div>
            </div>
            <span class="extra-song-item-arrow" aria-hidden="true">›</span>
        `;
        item.addEventListener('click', () => {
            launchLyricsView(song.id || song.spotifyId || song.title);
        });
        container.appendChild(item);
    });
}

function filterSongs(query) {
    const q = (query || '').trim().toLowerCase();
    if (!q) {
        renderSongsList(currentLoadedSongs);
        return;
    }
    const filtered = currentLoadedSongs.filter(s =>
        (s.title || '').toLowerCase().includes(q) ||
        (s.artist || '').toLowerCase().includes(q)
    );
    renderSongsList(filtered);
}

export async function openSongPickerScreen() {
    const menuView = document.getElementById('extraMenuView');
    const conjView = document.getElementById('extraConjugationsView');
    const songPickerView = document.getElementById('extraSongPickerView');

    if (menuView) menuView.hidden = true;
    if (conjView) conjView.hidden = true;
    if (songPickerView) songPickerView.hidden = false;

    const langKey = currentLanguageKey();
    const songs = await fetchSongsForLanguage(langKey);
    currentLoadedSongs = songs;

    const searchInput = document.getElementById('extraSongSearchInput');
    const clearBtn = document.getElementById('extraSongSearchClearBtn');
    const spotifyTray = document.getElementById('extraSpotifyTray');
    const spotifyInput = document.getElementById('extraSpotifyInput');

    if (searchInput) {
        searchInput.value = '';
        if (clearBtn) clearBtn.style.display = 'none';
        setTimeout(() => searchInput.focus(), 60);
    }
    if (spotifyTray) spotifyTray.style.display = 'none';
    if (spotifyInput) spotifyInput.value = '';

    renderSongsList(songs);
}

export function backToExtraMenu() {
    const menuView = document.getElementById('extraMenuView');
    const conjView = document.getElementById('extraConjugationsView');
    const songPickerView = document.getElementById('extraSongPickerView');
    if (conjView) conjView.hidden = true;
    if (songPickerView) songPickerView.hidden = true;
    if (menuView) menuView.hidden = false;
    try {
        if (window.location.pathname.includes('/conjugation')) {
            const basePath = window.location.pathname.replace(/\/conjugation\/?$/, '') || '/';
            history.replaceState({ screen: 'extra' }, '', basePath);
        }
    } catch (_) {}
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
    const conjView = document.getElementById('extraConjugationsView');
    const songPickerView = document.getElementById('extraSongPickerView');
    const menuView = document.getElementById('extraMenuView');
    if (conjView) conjView.hidden = true;
    if (songPickerView) songPickerView.hidden = true;
    if (menuView) menuView.hidden = false;
    if (typeof window.showConjugationScreen === 'function') {
        try { window.showConjugationScreen('setup'); } catch (_) {}
    }
    try {
        if (window.location.pathname.includes('/conjugation')) {
            const basePath = window.location.pathname.replace(/\/conjugation\/?$/, '') || '/';
            history.replaceState({ screen: 'home' }, '', basePath);
        }
    } catch (_) {}
}

export function initExtraWorkspace() {
    updateExtraUI();

    const exploreBtn = document.getElementById('desktopExploreBtn');
    exploreBtn?.addEventListener('click', () => {
        openExtraModal();
    });

    const lyricsCard = document.getElementById('extraLyricsCard');
    lyricsCard?.addEventListener('click', () => {
        openSongPickerScreen();
    });

    const conjCard = document.getElementById('extraConjugationsCard');
    conjCard?.addEventListener('click', () => {
        if (!conjCard.disabled) {
            openConjugationsScreen();
        }
    });

    const conjBackBtn = document.getElementById('extraConjugationsBackBtn');
    conjBackBtn?.addEventListener('click', backToExtraMenu);

    // Close steps back one level: in a drill → the conjugation menu; in the
    // conjugation menu → the Extra menu (not out of Extra altogether).
    const conjCloseBtn = document.getElementById('extraConjugationsCloseBtn');
    conjCloseBtn?.addEventListener('click', () => {
        if (window.conjugationCloseStep?.()) return;
        backToExtraMenu();
    });

    const songPickerBackBtn = document.getElementById('extraSongPickerBackBtn');
    songPickerBackBtn?.addEventListener('click', backToExtraMenu);

    const searchInput = document.getElementById('extraSongSearchInput');
    const clearBtn = document.getElementById('extraSongSearchClearBtn');
    if (searchInput) {
        searchInput.addEventListener('input', () => {
            const val = searchInput.value;
            if (clearBtn) clearBtn.style.display = val ? 'flex' : 'none';
            filterSongs(val);
        });
        searchInput.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') {
                searchInput.value = '';
                if (clearBtn) clearBtn.style.display = 'none';
                filterSongs('');
            }
        });
    }
    if (clearBtn) {
        clearBtn.addEventListener('click', () => {
            if (searchInput) {
                searchInput.value = '';
                clearBtn.style.display = 'none';
                searchInput.focus();
            }
            filterSongs('');
        });
    }

    const openSpotifyBtn = document.getElementById('extraOpenSpotifyBtn');
    const spotifyTray = document.getElementById('extraSpotifyTray');
    const spotifyInput = document.getElementById('extraSpotifyInput');
    const spotifySubmitBtn = document.getElementById('extraSpotifySubmitBtn');

    if (openSpotifyBtn && spotifyTray) {
        openSpotifyBtn.addEventListener('click', () => {
            const isHidden = spotifyTray.style.display === 'none';
            spotifyTray.style.display = isHidden ? 'block' : 'none';
            if (isHidden && spotifyInput) {
                spotifyInput.focus();
            }
        });
    }

    const submitSpotify = () => {
        const val = spotifyInput ? spotifyInput.value.trim() : '';
        if (val) {
            launchLyricsView(val);
        }
    };

    if (spotifySubmitBtn) {
        spotifySubmitBtn.addEventListener('click', submitSpotify);
    }
    if (spotifyInput) {
        spotifyInput.addEventListener('keydown', (e) => {
            if (e.key === 'Enter') {
                submitSpotify();
            }
        });
    }

    window.openExtraModal = openExtraModal;
    window.openConjugationsScreen = (targetVerb = null, targetView = null) => {
        openExtraModal();
        openConjugationsScreen(targetVerb, targetView);
    };
    window.addEventListener('popstate', () => {
        const isConj = window.location.pathname.includes('/conjugation');
        const conjView = document.getElementById('extraConjugationsView');
        if (!isConj && conjView && !conjView.hidden) {
            backToExtraMenu();
        } else if (isConj && (!conjView || conjView.hidden)) {
            const urlParams = new URLSearchParams(window.location.search);
            window.openConjugationsScreen(urlParams.get('verb'));
        }
    });
    window.openSongPickerScreen = () => {
        openExtraModal();
        openSongPickerScreen();
    };
    window.openLyricsViewScreen = () => {
        openSongPickerScreen();
    };
    window.updateExtraUI = updateExtraUI;
}

if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initExtraWorkspace, { once: true });
} else {
    initExtraWorkspace();
}
