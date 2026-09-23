// First: rewrites old ?artist=/?about= links to their #/ route before
// anything below reads the address.
import { conjugationDrillHref, goToRoute, languageKeyFor, replaceRoute, routeCodeFor } from './routes.js?v=20260923cj';
import { releaseUrl } from './release-host.js?v=20260921rh';
import './theme.js?v=20260922ui';
import './state.js?v=20260921x';
import './offline-db.js?v=20260825ak';
import './sync-queue.js?v=20260825ak';
import { initOfflineContent } from './offline-content.js?v=20260825ak';
import './speech.js?v=20260914b';
import './artist-ui.js?v=20260825ak';
import './auth.js?v=20260923sb';
import './tutorial.js?v=20260921ac';
import './walkthrough.js?v=20260921ac';
import './estimation.js?v=20260825ak';
import './config.js?v=20260921rh';
import './progress.js?v=20260920e';
import './knowledge.js?v=20260922mod';
import './ui.js?v=20260923rs';
import './vocab.js?v=20260923cj';
import './cognates.js?v=20260922ft2';
import './coverage.js?v=20260909a';
import './fast-mode.js?v=20260922ft2';
import './extras.js?v=20260922ft2';
import './review-home.js?v=20260922rw';
import './song-sets.js?v=20260823ae';
import './playlist-live.js?v=20260923cj';
import './spotify-playlist-import.js?v=20260923cj';
import './vocabulary-import.js?v=20260920a';
import './flashcards.js?v=20260923rs';
import { validateArtistCatalog } from './data-contracts.js?v=20260825ak';

function startCardTutorial() {
    const knownLanguage = window.getCardTutorialLanguageKey?.();
    if (knownLanguage) {
        window.setCardTutorialLanguage?.(knownLanguage);
        closeTutorialIntroduction();
        window.openCardTutorial?.();
        return;
    }
    document.getElementById('tutorialWelcomeStep')?.classList.add('hidden');
    document.getElementById('tutorialLanguageStep')?.classList.remove('hidden');
}

function openTutorialIntroduction() {
    document.getElementById('tutorialWelcomeStep')?.classList.remove('hidden');
    document.getElementById('tutorialLanguageStep')?.classList.add('hidden');
    renderTutorialLanguageChoices();
    document.getElementById('tutorialIntroModal')?.classList.remove('hidden');
}

function renderTutorialLanguageChoices() {
    const container = document.getElementById('tutorialLanguageChoices');
    if (!container || container.childElementCount) return;
    const flags = { spanish: '🇪🇸', portuguese: '🇵🇹', czech: '🇨🇿', french: '🇫🇷' };
    const inheritedLanguage = window.getCardTutorialLanguageKey?.();
    (window.getCardTutorialLanguages?.() || []).forEach(({ key, language }) => {
        const profile = window.getCardTutorialProfile?.(key);
        const button = document.createElement('button');
        button.type = 'button';
        button.className = 'tutorial-language-choice';
        if (key === inheritedLanguage) button.classList.add('is-current');
        button.innerHTML = `<span class="tutorial-language-flag" aria-hidden="true">${flags[key] || '🌐'}</span>` +
            `<span><strong>${language}</strong><small>${profile?.lyrics ? 'Speech and lyrics' : 'Speech tutorial'}</small></span>` +
            '<span class="tutorial-language-arrow" aria-hidden="true">→</span>';
        button.addEventListener('click', () => {
            window.setCardTutorialLanguage?.(key);
            closeTutorialIntroduction();
            window.openCardTutorial?.();
        });
        container.appendChild(button);
    });
}

function closeTutorialIntroduction() {
    document.getElementById('tutorialIntroModal')?.classList.add('hidden');
}

window.openTutorialIntroduction = openTutorialIntroduction;

// Spotify is lyrics-only and its module is sizeable. Start the dynamic import
// immediately for an artist URL so it races setup/data loading, but keep it
// entirely out of normal Speech startup. Card/modal code already has its own
// lazy module stubs in flashcards.js.
const _spotifyModulePromise = ['artist', 'songs'].includes(window.fluencyRoute?.kind)
    ? import('./spotify.js?v=20260923sp').catch(error => {
        console.warn('Spotify controls deferred:', error);
        return null;
    })
    : null;

// Boot profiling — opt-in via ?perf=1 URL param so normal users don't see
// console noise. After boot, call window.perfSummary() in DevTools (or it
// auto-runs at the end of boot) to see a table of phase timings: cumulative
// time since navigation start + delta from the previous mark. Useful for
// validating whether a given perf change actually moved the needle.
const _perfEnabled = new URLSearchParams(window.location.search).has('perf');
const _perfMarks = [];
function perfMark(name) {
    if (!_perfEnabled) return;
    _perfMarks.push({ name, t: performance.now() });
}
function perfSummary() {
    if (!_perfEnabled || _perfMarks.length === 0) return;
    console.table(_perfMarks.map((m, i) => ({
        phase: m.name,
        cumulative_ms: m.t.toFixed(1),
        delta_ms: (i === 0 ? m.t : m.t - _perfMarks[i - 1].t).toFixed(1),
    })));
}
window.perfMark = perfMark;
window.perfSummary = perfSummary;
perfMark('main.js top — module imports done');

const APP_LOADING_MESSAGE_KEY = 'fluency_loading_message_v1';

// How long the deck-progress ring stays up before the screen behind it is
// revealed. A tap always ends it early; the number is the ceiling, not the
// target. The ring finishes animating at roughly 750ms (450ms to expand, 700ms
// of arc fill after a double rAF), so anything at or below that is over before
// the figures have settled enough to read.
const MIN_DECK_LOADING_BEAT_MS = 900;
const DECK_RING_CIRCUMFERENCE = 339.292;   // 2 * PI * r, r = 54 in the SVG
// Once the arcs have settled, invite the tap. Earlier than this and the hint
// would offer a way out of a screen that has not finished saying anything.
const DECK_LOADING_HINT_DELAY_MS = 750;
let deckLoadingBeat = null;
let resolveDeckLoadingBeat = null;
let deckLoadingBeatTimer = null;
let deckLoadingHintTimer = null;

function prefersReducedMotion() {
    try { return window.matchMedia('(prefers-reduced-motion: reduce)').matches; }
    catch (_) { return false; }
}

// Returns the overlay to its plain-spinner state. Called by showAppLoading so the
// boot path and the sessionStorage replay can never resurrect a ring they have no
// numbers for.
function resetDeckLoadingVisual() {
    const visual = document.getElementById('appLoadingVisual');
    if (visual) visual.dataset.mode = 'spinner';
    const legend = document.getElementById('appLoadingRingLegend');
    if (legend) legend.hidden = true;
    for (const id of ['appLoadingRingSeen', 'appLoadingRingKnown']) {
        const arc = document.getElementById(id);
        if (!arc) continue;
        arc.style.transition = 'none';
        arc.style.strokeDashoffset = String(DECK_RING_CIRCUMFERENCE);
    }
    const hint = document.getElementById('appLoadingTapHint');
    if (hint) hint.hidden = true;
    if (deckLoadingHintTimer) {
        clearTimeout(deckLoadingHintTimer);
        deckLoadingHintTimer = null;
    }
    if (deckLoadingBeatTimer) {
        clearTimeout(deckLoadingBeatTimer);
        deckLoadingBeatTimer = null;
    }
    resolveDeckLoadingBeat?.();
    resolveDeckLoadingBeat = null;
    deckLoadingBeat = null;
}

function showAppLoading(title = 'Getting things ready', detail = 'Loading your language and progress…', persist = false) {
    const screen = document.getElementById('appLoadingScreen');
    if (!screen) return;
    document.getElementById('appLoadingTitle').textContent = title;
    document.getElementById('appLoadingDetail').textContent = detail;
    resetDeckLoadingVisual();
    screen.classList.remove('is-hidden');
    screen.setAttribute('aria-busy', 'true');
    if (persist) {
        try { sessionStorage.setItem(APP_LOADING_MESSAGE_KEY, JSON.stringify({ title, detail })); } catch (_) {}
    }
}

// Paints the deck's own progress onto the loading overlay, using numbers the setup
// screen already holds (ui.js builds them from the local progress cache, so this
// runs before any release fetch is issued). Returns the minimum-beat promise, and
// resolves immediately whenever there is nothing worth showing - so a caller that
// has no stats needs no special case and keeps today's plain spinner.
function showDeckLoading(stats, { title, detail, holdMs = MIN_DECK_LOADING_BEAT_MS } = {}) {
    showAppLoading(
        title || 'Getting things ready',
        detail || 'Preparing your next cards…'
    );
    const cardCount = Number(stats?.cardCount) || 0;
    const seenCount = Math.max(0, Math.min(cardCount, Number(stats?.seenCount) || 0));
    const visual = document.getElementById('appLoadingVisual');
    // "Not when you're at 0%": an untouched deck has nothing to demonstrate.
    if (!visual || cardCount <= 0 || seenCount <= 0) return Promise.resolve();

    const reviewCount = Math.max(0, Math.min(seenCount, Number(stats?.reviewCount) || 0));
    const knownCount = Math.max(0, seenCount - reviewCount);
    const unseenCount = Math.max(0, cardCount - seenCount);
    const pctOf = count => 100 * count / cardCount;
    const offsetFor = pct => DECK_RING_CIRCUMFERENCE * (1 - Math.min(100, Math.max(0, pct)) / 100);

    const value = document.getElementById('appLoadingRingValue');
    if (value) value.textContent = `${knownCount}/${cardCount}`;
    const legend = document.getElementById('appLoadingRingLegend');
    if (legend) {
        document.getElementById('appLoadingLegendKnown').textContent = String(knownCount);
        document.getElementById('appLoadingLegendReview').textContent = String(reviewCount);
        document.getElementById('appLoadingLegendUnseen').textContent = String(unseenCount);
        legend.hidden = false;
    }

    const seenArc = document.getElementById('appLoadingRingSeen');
    const knownArc = document.getElementById('appLoadingRingKnown');
    const paint = () => {
        if (seenArc) seenArc.style.strokeDashoffset = String(offsetFor(pctOf(seenCount)));
        if (knownArc) knownArc.style.strokeDashoffset = String(offsetFor(pctOf(knownCount)));
    };

    visual.dataset.mode = 'progress';
    const hint = document.getElementById('appLoadingTapHint');
    const reduced = prefersReducedMotion();
    if (reduced) {
        // The hold stays: waiting to read is not motion. Only the animation goes.
        paint();
        if (hint) hint.hidden = false;
    } else {
        // Double rAF before restoring the transition, the same idiom the coverage bar
        // (progress.js) and the deck score ring (flashcards-modals.js) use: the browser
        // must commit the empty arc before the filled one becomes a transition.
        requestAnimationFrame(() => requestAnimationFrame(() => {
            for (const arc of [seenArc, knownArc]) {
                if (arc) arc.style.transition = '';
            }
            paint();
        }));
        if (hint) {
            deckLoadingHintTimer = setTimeout(() => {
                hint.hidden = false;
                deckLoadingHintTimer = null;
            }, DECK_LOADING_HINT_DELAY_MS);
        }
    }

    deckLoadingBeat = new Promise(resolve => {
        resolveDeckLoadingBeat = resolve;
        deckLoadingBeatTimer = setTimeout(resolve, holdMs);
    });
    return deckLoadingBeat;
}

function awaitDeckLoadingBeat() {
    return deckLoadingBeat || Promise.resolve();
}

// Tap anywhere on the overlay to end the hold. The work behind it may still be
// in flight; this only gives up the reading time, never the load.
document.getElementById('appLoadingScreen')?.addEventListener('click', () => {
    if (deckLoadingBeatTimer) {
        clearTimeout(deckLoadingBeatTimer);
        deckLoadingBeatTimer = null;
    }
    resolveDeckLoadingBeat?.();
});

function hideAppLoading() {
    const screen = document.getElementById('appLoadingScreen');
    document.documentElement.classList.remove('app-booting');
    screen?.classList.add('is-hidden');
    screen?.setAttribute('aria-busy', 'false');
    try { sessionStorage.removeItem(APP_LOADING_MESSAGE_KEY); } catch (_) {}
}

try {
    const pendingLoadingMessage = JSON.parse(sessionStorage.getItem(APP_LOADING_MESSAGE_KEY) || 'null');
    if (pendingLoadingMessage?.title) {
        showAppLoading(pendingLoadingMessage.title, pendingLoadingMessage.detail || 'Preparing the next screen…');
    }
} catch (_) {}

window.showAppLoading = showAppLoading;
window.hideAppLoading = hideAppLoading;
window.showDeckLoading = showDeckLoading;
window.awaitDeckLoadingBeat = awaitDeckLoadingBeat;

// Wire the static authentication surface before any configuration fetch or
// artist resolution. The HTML intentionally contains this modal as a boot
// fallback; its buttons must never depend on loadConfig() having completed.
setupAuthEventListeners();
checkAuthentication();
perfMark('after early authentication');

// Register service worker for PWA functionality
if ('serviceWorker' in navigator) {
    window.addEventListener('load', () => {
        navigator.serviceWorker.register('service-worker.js')
            .then(registration => {
                console.log('SW registered');
                const announceUpdate = () => {
                    if (!registration.waiting) return;
                    const indicator = document.getElementById('syncStatusIndicator');
                    if (indicator) {
                        indicator.className = 'sync-status is-update';
                        indicator.textContent = 'Update ready';
                        indicator.onclick = () => registration.waiting.postMessage({ type: 'SKIP_WAITING' });
                    }
                };
                announceUpdate();
                registration.addEventListener('updatefound', () => {
                    registration.installing?.addEventListener('statechange', announceUpdate);
                });
                let reloading = false;
                navigator.serviceWorker.addEventListener('controllerchange', () => {
                    if (!reloading) { reloading = true; location.reload(); }
                });
            })
            .catch(err => console.log('SW registration failed'));
    });
}

// All available artist configs, keyed by slug. Loaded once from artists.json.
let allArtistsConfig = null;
// The query key crosses the one-time migration boundary from the old worker,
// which cached the unversioned empty catalog. The current worker routes this
// pathname network-only, so later release activations remain immediately live.
const ACTIVE_ARTIST_CATALOG_URL = 'config/artists.json?contract=lyrics-v1';


function requestedLyricsRelease() {
    const value = new URLSearchParams(window.location.search).get('lyricsRelease') || '';
    return /^[A-Za-z0-9][A-Za-z0-9._-]*$/.test(value) ? value : '';
}

function artistCatalogUrl() {
    const releaseId = requestedLyricsRelease();
    return releaseId
        ? releaseUrl(`releases/lyrics/${encodeURIComponent(releaseId)}/app/config/artists.json`)
        : ACTIVE_ARTIST_CATALOG_URL;
}

function bindArtistCatalogToRelease(catalog, requestedReleaseId = '') {
    for (const artist of Object.values(catalog)) {
        const releaseId = requestedReleaseId || artist.releaseId;
        if (!releaseId) continue;
        const appBase = releaseUrl(`releases/lyrics/${encodeURIComponent(releaseId)}/app/`);
        for (const field of ['indexPath', 'examplesPath', 'masterPath', 'songsPath', 'spotifyPath', 'albumsDictionary', 'defaultAlbumArt', 'pickerImage']) {
            if (typeof artist[field] === 'string' && artist[field]) artist[field] = appBase + artist[field];
        }
        if (artist.albumImageMap) {
            artist.albumImageMap = Object.fromEntries(
                Object.entries(artist.albumImageMap).map(([album, path]) => [album, appBase + path])
            );
        }
        artist.releaseManifestPath = releaseUrl(`releases/lyrics/${encodeURIComponent(releaseId)}/manifest.json`);
        artist.releaseCompositionPath = releaseUrl(`releases/lyrics/${encodeURIComponent(releaseId)}/composition.json`);
    }
    return catalog;
}
// Slugs of artists currently selected for multi-artist merge
let selectedArtistSlugs = [];
const CUSTOM_ARTIST_SLUG = 'custom';
const ARTIST_EXTRA_UNLOCK_KEY = 'fluency_artist_extra_unlocked_v1';
const ARTIST_EXTRA_UNLOCK_PCT = 60;

function readArtistExtraUnlocks() {
    try {
        const saved = JSON.parse(localStorage.getItem(ARTIST_EXTRA_UNLOCK_KEY) || '[]');
        return new Set(Array.isArray(saved) ? saved : []);
    } catch (_) {
        return new Set();
    }
}

function isArtistExtraUnlocked(slug = window._urlArtistSlug) {
    return !!slug && readArtistExtraUnlocks().has(slug);
}

function updateArtistExtraUnlock(coveragePct) {
    if (!activeArtist || artistVocabularyScope !== 'main') return;
    const pct = Math.max(0, Number(coveragePct) || 0);
    window._artistMainCoveragePct = pct;
    const slug = window._urlArtistSlug;
    if (slug && pct >= ARTIST_EXTRA_UNLOCK_PCT && !isArtistExtraUnlocked(slug)) {
        const unlocks = readArtistExtraUnlocks();
        unlocks.add(slug);
        try { localStorage.setItem(ARTIST_EXTRA_UNLOCK_KEY, JSON.stringify(Array.from(unlocks))); } catch (_) {}
    }
    renderArtistSourceSummary();
}

window.isArtistExtraUnlocked = isArtistExtraUnlocked;
window.updateArtistExtraUnlock = updateArtistExtraUnlock;

// A route names a language by routeCode (`es`) or config key (`spanish`).
// Artist resolution runs before loadConfig(), so read the language table on
// its own here; only #/es/songs needs it.
let _routeLanguagesPromise = null;
async function routeLanguageKey(token) {
    if (!token) return null;
    _routeLanguagesPromise ||= fetch('config/config.json?v=20260827a', { cache: 'no-store' })
        .then(response => response.ok ? response.json() : {})
        .then(json => json.languages || {})
        .catch(() => ({}));
    return languageKeyFor(token, await _routeLanguagesPromise);
}

// Resolve artist from the route: #/artist/bad-bunny, or #/es/songs for the
// learner's own songs. Old ?artist= and ?mode=badbunny links (home-screen
// installs) were rewritten to these by routes.js.
async function resolveArtist() {
    const route = window.fluencyRoute || { kind: 'home' };
    const artistSlug = route.kind === 'artist' ? route.artist
        : route.kind === 'songs' ? CUSTOM_ARTIST_SLUG
        : null;

    if (!artistSlug) return; // normal mode

    try {
        const previewRelease = requestedLyricsRelease();
        let catalog = null;
        try {
            const response = await fetch(artistCatalogUrl(), { cache: 'no-store' });
            if (response.ok) catalog = await response.json();
        } catch (_) {}
        if (!catalog || Object.keys(catalog).length === 0) {
            try {
                const fallbackResp = await fetch(releaseUrl('releases/lyrics/lyrics-all-artists-v7-native-20260825b/app/config/artists.json'), { cache: 'no-store' });
                if (fallbackResp.ok) catalog = await fallbackResp.json();
            } catch (_) {}
        }
        allArtistsConfig = bindArtistCatalogToRelease(validateArtistCatalog(catalog || {}, {
            source: 'config/artists.json'
        }), previewRelease);

        // Tag each config with its slug
        for (const [slug, cfg] of Object.entries(allArtistsConfig)) {
            cfg.slug = slug;
        }

        let artistConfig = allArtistsConfig[artistSlug];
        if (artistSlug === CUSTOM_ARTIST_SLUG) {
            const customLanguage = await routeLanguageKey(route.language) || 'spanish';
            const customSources = Object.entries(allArtistsConfig)
                .filter(([, cfg]) => (cfg.language || 'spanish') === customLanguage
                    && cfg.songsPath && (cfg.indexPath || cfg.dataPath))
                .map(([slug]) => slug);
            const primary = allArtistsConfig[customSources[0]];
            if (primary && customSources.length) {
                artistConfig = {
                    ...primary,
                    slug: CUSTOM_ARTIST_SLUG,
                    name: 'Choose your own',
                    customSongSource: true,
                    customSourceSlugs: customSources,
                    songsPath: null,
                    albumsDictionary: null,
                    albumImageMap: null,
                    defaultAlbumArt: '',
                    pickerImage: '',
                    colorTheme: { primary: '#10B981', secondary: '#6EE7B7' },
                    maxLevel: Object.entries(allArtistsConfig)
                        .filter(([slug]) => customSources.includes(slug))
                        .reduce((total, [, cfg]) => total + (Number(cfg.maxLevel) || 0), 0)
                };
            }
        }
        if (artistConfig) {
            activeArtist = artistConfig;
            window.activeArtist = artistConfig;
            // Store the URL artist slug — this is the immutable primary artist
            window._urlArtistSlug = artistSlug;
            const requestedExtra = route.scope === 'extra';
            artistVocabularyScope = requestedExtra && isArtistExtraUnlocked(artistSlug)
                ? 'extra'
                : 'main';
            if (requestedExtra && artistVocabularyScope === 'main') {
                replaceRoute({ ...route, scope: 'main' });
            }

            // Custom Lyrics loads every real source, then the song selector
            // narrows that union. Ordinary sources retain their single slug.
            selectedArtistSlugs = artistConfig.customSongSource
                ? artistConfig.customSourceSlugs.slice()
                : [artistSlug];
        } else {
            console.warn(`Unknown artist slug: ${artistSlug}`);
        }
    } catch (error) {
        console.error('Failed to load artists.json:', error);
    }
}

await resolveArtist();
perfMark('after resolveArtist');

// Expose for use by ui.js artist selection
window._allArtistsConfig = allArtistsConfig;
window._selectedArtistSlugs = selectedArtistSlugs;
window.resetActiveArtist = () => {
    activeArtist = null;
    window._urlArtistSlug = null;
    selectedArtistSlugs = [];
    window._selectedArtistSlugs = [];
};

// Add artist mode class to body and load albums dictionary
if (activeArtist) {
    document.body.classList.add('artist-mode');
    const artistColor = (activeArtist.colorTheme && activeArtist.colorTheme.primary) || 'var(--accent-primary)';
    document.documentElement.style.setProperty('--artist-ambient-glow', artistColor);
    if (activeArtist.customSongSource) {
        loadMultiArtistAlbumsDictionaries(selectedArtistSlugs, allArtistsConfig);
    } else {
        loadArtistAlbumsDictionary();
    }
}

loadConfig().then(async () => {
    const isResumeNavigation = new URLSearchParams(window.location.search).get('resume') === '1';
    perfMark('after loadConfig');
    // #/es/conjugate[/verb] names the drill page, which is its own document.
    // A language with no drill deck opens that language instead.
    if (window.fluencyRoute?.kind === 'conjugate') {
        const route = window.fluencyRoute;
        const key = languageKeyFor(route.language, config.languages);
        const drillHref = conjugationDrillHref(key, route.verb, config.languages);
        if (drillHref) {
            window.location.replace(drillHref);
            return;
        }
        window.fluencyRoute = { kind: 'language', language: route.language };
        replaceRoute(window.fluencyRoute);
    }
    renderLanguageTabs();
    // A language is a durable learning context, not a choice learners should
    // have to repeat on every visit. First-time visitors still see the picker.
    const firstLang = Object.keys(config.languages).find(lang => config.languages[lang].hasData !== false) || Object.keys(config.languages)[0];
    let preferredLanguage = null;
    try { preferredLanguage = localStorage.getItem('fluencyPreferredLanguageV1'); } catch (_) {}
    // A language or word link names the language outright and becomes the
    // saved preference, as choosing it on the picker would.
    const bootRoute = window.fluencyRoute || { kind: 'home' };
    const routeLanguage = ['language', 'word', 'live'].includes(bootRoute.kind)
        ? languageKeyFor(bootRoute.language, config.languages)
        : null;
    if (routeLanguage && config.languages[routeLanguage].hasData !== false) {
        preferredLanguage = routeLanguage;
        try { localStorage.setItem('fluencyPreferredLanguageV1', routeLanguage); } catch (_) {}
    }
    // Canonical spelling in the address bar: #/spanish/songs becomes #/es/songs.
    const namedLanguage = bootRoute.language && languageKeyFor(bootRoute.language, config.languages);
    if (namedLanguage) {
        replaceRoute({ ...bootRoute, language: routeCodeFor(namedLanguage, config.languages) });
    }
    const wordRoute = bootRoute.kind === 'word' && routeLanguage ? bootRoute : null;
    const preferredIsReady = preferredLanguage
        && config.languages[preferredLanguage]
        && config.languages[preferredLanguage].hasData !== false;
    selectedLanguage = preferredIsReady ? preferredLanguage : firstLang;
    await loadSecrets();
    // #/es/live reopens this learner's live playlist deck. Someone with no deck
    // yet lands on the language with the music-source sheet open instead.
    let liveRouteNeedsImport = false;
    if (bootRoute.kind === 'live' && routeLanguage) {
        await window.preparePlaylistLiveSession?.(selectedLanguage);
        if (window.playlistLiveActive?.()) {
            document.body.classList.add('playlist-live-mode');
        } else {
            liveRouteNeedsImport = true;
        }
    }
    // Exact Speech resumes bypass the language/source chooser, so restore the
    // small Spanish-only helpers here for that route. Ordinary language choice
    // deliberately fetches neither: ui.js starts them only after Speech is
    // selected, allowing Lyrics learners to avoid the Speech loading phase.
    // Conjugation tables are needed for inflected English glosses on first
    // paint, so prefetch them for any resumed Speech language that has a path.
    if ((isResumeNavigation || wordRoute) && !activeArtist) {
        if (selectedLanguage === 'spanish') {
            if (window.loadSpanishRanks) window.loadSpanishRanks();
            if (window.loadConjugatedEnglishData) window.loadConjugatedEnglishData();
        }
        if (window.loadConjugationData) await window.loadConjugationData();
    }
    applyLanguageColorTheme();
    setupLemmaToggle();
    setupCognateToggle();
    setupGlobalStudyDefaults();
    setupPercentModeButton();
    setupEstimationModal();
    setupTooltipHandlers();
    setupSettingsSearch();

    const learningContextModal = document.getElementById('learningContextModal');
    const closeLearningContext = () => learningContextModal?.classList.add('hidden');
    document.getElementById('learningContextBtn')?.addEventListener('click', () => {
        window.updateLearningContextUI?.();
        learningContextModal?.classList.remove('hidden');
    });
    document.getElementById('closeLearningContextModal')?.addEventListener('click', closeLearningContext);
    learningContextModal?.addEventListener('click', event => {
        if (event.target === event.currentTarget) closeLearningContext();
    });
    document.getElementById('learningContextProgressBtn')?.addEventListener('click', () => {
        closeLearningContext();
        showTotalStatsModal();
    });
    document.getElementById('learningContextLanguageBtn')?.addEventListener('click', () => {
        closeLearningContext();
        if (activeArtist) {
            try { localStorage.removeItem('fluencyPreferredLanguageV1'); } catch (_) {}
            window.location.href = window.location.pathname;
        } else {
            window.reopenLanguagePicker?.();
        }
    });
    document.getElementById('learningContextSourceBtn')?.addEventListener('click', () => {
        closeLearningContext();
        window.openLearningSourcePicker?.();
    });

    document.getElementById('dailyReviewBtn')?.addEventListener('click', () => {
        const button = document.getElementById('dailyReviewBtn');
        const limit = Number(button?.dataset.limit || 100);
        closeLearningContext();
        window.startDailyReview?.({ limit, urgencyTier: 'all' });
    });

    // "?" is the learner tutorial. The portfolio About page links the
    // walkthrough instead and never opens this.
    document.getElementById('helpBtn').addEventListener('click', openTutorialIntroduction);
    document.getElementById('closeTutorialIntroModal')?.addEventListener('click', closeTutorialIntroduction);
    document.getElementById('startCardTutorialBtn')?.addEventListener('click', startCardTutorial);
    document.getElementById('tutorialLanguageBackBtn')?.addEventListener('click', () => {
        document.getElementById('tutorialLanguageStep')?.classList.add('hidden');
        document.getElementById('tutorialWelcomeStep')?.classList.remove('hidden');
    });
    document.getElementById('tutorialIntroModal')?.addEventListener('click', event => {
        if (event.target === event.currentTarget) closeTutorialIntroduction();
    });
    document.getElementById('topBarGearBtn').addEventListener('click', () => showSettingsModal());
    document.getElementById('levelEstimateCTABtn')?.addEventListener('click', () => openEstimationModal());
    document.getElementById('openEstimationFromLevelHelpBtn')?.addEventListener('click', () => {
        document.getElementById('step2Tooltip')?.classList.remove('visible');
        openEstimationModal();
    });
    document.getElementById('personalProgressInfoBtn')?.addEventListener('click', event => {
        event.stopPropagation();
        showTotalStatsModal();
    });
    setupFindWord();
    setupFrequencyIntro();
    if (currentUser && document.getElementById('authModal')?.classList.contains('hidden')) {
        window.maybeShowFrequencyIntro?.();
    }
    document.getElementById('topBarUserName').addEventListener('click', () => {
        if (currentUser && !currentUser.isGuest) showSettingsModalWithTab('account');
    });
    document.getElementById('closeHelpModal').addEventListener('click', () => {
        document.getElementById('helpModal').classList.add('hidden');
    });
    wireExtraScopeModal();
    setupTabSwitching(document.getElementById('helpModal'));
    // Welcome tab → "More about this project" link opens the standalone
    // project explainer modal (the same one the Account tab uses), so
    // there's a single canonical "what is this app" surface.
    const helpMoreInfoBtn = document.getElementById('helpMoreInfoBtn');
    if (helpMoreInfoBtn) {
        helpMoreInfoBtn.addEventListener('click', () => {
            document.getElementById('helpModal').classList.add('hidden');
            if (window.openAboutProjectModal) window.openAboutProjectModal();
        });
    }
    const helpStudyContent = document.querySelector('#helpStudyTabContent .help-content');
    if (helpStudyContent && !document.getElementById('helpCardTutorialBtn')) {
        const tutorialAction = document.createElement('p');
        tutorialAction.className = 'help-card-tutorial-action';
        tutorialAction.innerHTML = '<button class="help-more-info-btn" id="helpCardTutorialBtn" type="button">Open tutorial introduction →</button>';
        helpStudyContent.appendChild(tutorialAction);
        tutorialAction.querySelector('button').addEventListener('click', () => {
            document.getElementById('helpModal').classList.add('hidden');
            openTutorialIntroduction();
        });
    }
    // Hide floating gear — replaced by gear in the top bar
    document.getElementById('gearBtn').style.display = 'none';

    // Set user name in top bar immediately (don't wait for progress load).
    const userName = currentUser ? (currentUser.isGuest ? 'GUEST' : currentUser.initials) : '';
    document.getElementById('topBarUserName').textContent = userName;

    // Shareable page links open on top of whatever state the app lands in.
    const pageRoute = window.fluencyRoute?.kind;
    if (pageRoute === 'about') window.openAboutProjectModal?.();
    else if (pageRoute === 'tutorial') openTutorialIntroduction();
    else if (pageRoute === 'walkthrough') window.openWalkthrough?.();


    perfMark('after sync setup phase');
    await Promise.allSettled([migrateLocalStorageIds(), migrateLocalStorageIdsV2()]);
    perfMark('after migrations');
    await loadSecrets();
    perfMark('after loadSecrets');
    if ((activeArtist?.songsPath || activeArtist?.customSongSource) && window.initArtistSongSelection) {
        try {
            await window.initArtistSongSelection();
        } catch (error) {
            console.warn('Per-song Lyrics selection unavailable; using the full artist deck.', error);
            artistSongCatalog = null;
            selectedSongIds = [];
        }
    }
    // Retry Spotify player init now that client ID is available (handles race with SDK load)
    _spotifyModulePromise?.then(() => window._spotifyTryInit?.());
    // Offline sync: wire connectivity listeners, render the status indicator,
    // and drain any writes queued while previously offline. Runs after
    // loadSecrets() so GOOGLE_SCRIPT_URL is populated for the initial flush.
    // These enhance the already-interactive app. Neither is allowed to block
    // authentication or source rendering when Safari storage is unavailable.
    if (window.initSync) window.initSync().catch(error =>
        console.warn('Offline sync initialization deferred:', error));
    initOfflineContent().catch(error =>
        console.warn('Offline content initialization deferred:', error));

    // Start loading progress from Google Sheets (loads cache synchronously, then fetches)
    let progressPromise = Promise.resolve(false);
    if (currentUser && !currentUser.isGuest) {
        progressPromise = loadUserProgressFromSheet();
    }

    // Render UI immediately using cached progress data
    if (window.playlistLiveActive?.()) {
        applyLanguageColorTheme();
        document.getElementById('step1').style.display = 'none';
        const deck = window.playlistLiveDeck?.();
        const sourceName = document.getElementById('selectedSourceInline');
        if (sourceName && deck?.playlistName) {
            sourceName.textContent = `Live · ${deck.playlistName}`;
        }
        document.body.classList.add('has-learning-context');
        window.updateLearningContextUI?.();
        sessionStorage.setItem('fluencyPendingSpeechLanguage', selectedLanguage);
        sessionStorage.setItem('fluencyPendingLiveStudy', '1');
        const liveTab = document.querySelector(`.lang-tab[data-lang="${selectedLanguage}"]`);
        if (liveTab && !liveTab.disabled) {
            liveTab.click();
        } else if (!isResumeNavigation) {
            hideAppLoading();
        }
        perfMark('after playlist-live init');
    } else if (activeArtist) {
        const promptForCustomSongs = activeArtist.customSongSource && selectedSongIds.length === 0;
        let deckOverviewHold = null;
        try {
            selectedLanguage = activeArtist.language || 'spanish';
            await loadReleaseProvenance(selectedLanguage);
            applyLanguageColorTheme();
            // Hide step 1 entirely (language auto-selected)
            document.getElementById('step1').style.display = 'none';
            renderArtistSourceSummary();
            await loadPpmData(activeArtist.language || 'spanish');
            document.getElementById('step2').style.display = 'block';
            // Title is now static ("Choose level" in the HTML); the
            // CEFR/% toggle hides itself in artist mode via
            // setupPercentModeButton() — both are no-ops here.
            updateStep2Tooltip();
            updateStep5Tooltip();
            await updateLemmaToggleVisibility();
            await updateCognateToggleVisibility();
            // The coverage figure needs the index, which the toggle-visibility
            // calls above have already pulled -- but nothing the level selector
            // builds. So publish it first, raise the wheel, and let the selector
            // render underneath it rather than ahead of it.
            await updateExclusionBars();
            if (!isResumeNavigation) deckOverviewHold = window.showDeckOverviewLoading?.();
            await renderLevelSelector(activeArtist.language || 'spanish');
            document.body.classList.add('has-learning-context');
            window.updateLearningContextUI?.();
        } finally {
            if (!isResumeNavigation) {
                await deckOverviewHold;
                hideAppLoading();
            }
        }
        if (promptForCustomSongs) window.showSongSetPicker?.();
        perfMark('after artist init');
    } else {
        const pendingSpeechLanguage = sessionStorage.getItem('fluencyPendingSpeechLanguage');
        const pendingTab = pendingSpeechLanguage
            ? document.querySelector(`.lang-tab[data-lang="${pendingSpeechLanguage}"]`)
            : null;
        if (wordRoute) {
            // The linked card opens by itself; the language is chosen for real
            // when the learner leaves it (see openRouteWord).
            hideAppLoading();
        } else if (pendingTab && !pendingTab.disabled) pendingTab.click();
        else {
            if (preferredIsReady && !isResumeNavigation) {
                document.querySelector(`.lang-tab[data-lang="${preferredLanguage}"]`)?.click();
            }
            if (!isResumeNavigation) hideAppLoading();
        }
    }

    // Cached progress is already loaded synchronously by
    // loadUserProgressFromSheet(). Do not hold boot or exact-session resume
    // behind the remote Sheets round trip.
    window.renderResumeLastSetCard?.();
    if (isResumeNavigation) {
        await window.resumeLastStudySession?.();
    }
    if (wordRoute) openRouteWord(wordRoute, routeLanguage);
    if (liveRouteNeedsImport) {
        // The music-source sheet, not the import itself: the import goes
        // straight to Spotify sign-in, which a visitor should choose to do.
        await window.authReady;
        await frequencyIntroClosed();
        await showLyricsPicker(selectedLanguage);
    }

    // Reconcile the setup badges once the background Sheets refresh finishes.
    const dataChanged = await progressPromise;
    const setupIsVisible = !document.getElementById('setupPanel')?.classList.contains('hidden');
    if (dataChanged && selectedLanguage && selectedLevel && setupIsVisible) {
        try { await window.refreshSetupAfterProgress?.(); } catch (e) { /* setup may not be visible yet */ }
    }
    perfMark('boot complete');
    perfSummary();
}).catch(error => {
    console.error('App initialization failed:', error);
    hideAppLoading();
});

// Build the initials shown on the color fallback (no image) — up to 2 letters.
function artistInitials(name) {
    const words = (name || '').trim().split(/\s+/).filter(Boolean);
    if (words.length === 0) return '?';
    if (words.length === 1) return words[0].slice(0, 2).toUpperCase();
    return (words[0][0] + words[1][0]).toUpperCase();
}

// Pick the image to represent an artist in the radial picker.
// Priority: explicit picker image → default album art → (none → color fallback).
function artistPickerImage(cfg) {
    return cfg.pickerImage || cfg.image || cfg.defaultAlbumArt || '';
}

function customSongsIcon() {
    return '<svg viewBox="0 0 24 24" aria-hidden="true" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"><path d="M4 6h10M4 12h10M4 18h7"/><path d="M18 11v8m-4-4h8"/></svg>';
}

function renderArtistSourceSummary() {
    const step = document.getElementById('artistSourceStep');
    const picker = document.getElementById('artistSourcePickerBtn');
    const artistBtn = document.getElementById('artistSourceArtistBtn');
    const speechBtn = document.getElementById('artistSourceSpeechBtn');
    const name = document.getElementById('artistSourceName');
    const selectionLabel = document.getElementById('artistSourceSelectionLabel');
    const image = document.getElementById('artistSourceImage');
    if (!step || !picker || !artistBtn || !speechBtn || !name || !image || !activeArtist) return;

    const lang = activeArtist.language || selectedLanguage || 'spanish';
    const langCfg = config?.languages?.[lang] || {};
    const langNameEl = document.getElementById('artistSourceLanguageName');
    const langIconEl = document.getElementById('artistSourceLanguageIcon');
    const langBtn = document.getElementById('artistSourceLanguageBtn');
    if (langNameEl) langNameEl.textContent = langCfg.name || lang;
    if (langIconEl) langIconEl.textContent = langCfg.flag || lang.slice(0, 2).toUpperCase();
    if (langBtn) {
        langBtn.onclick = () => window.showLanguagePicker?.(config.languages);
    }

    const artistName = activeArtist.name || 'Artist';
    const art = artistPickerImage(activeArtist);
    const isCustom = activeArtist.customSongSource === true;
    name.textContent = artistName;
    if (selectionLabel) selectionLabel.textContent = window.songSelectionSummary?.() || 'Choose songs';
    image.innerHTML = isCustom ? customSongsIcon() : '';
    if (!art && !isCustom) image.textContent = artistInitials(artistName);
    image.classList.toggle('artist-source-image--fallback', !art && !isCustom);
    image.classList.toggle('artist-source-image--custom', isCustom);
    image.style.backgroundImage = art ? `url('${art}')` : '';
    image.style.backgroundColor = art || isCustom ? '' : (activeArtist.colorTheme?.primary || 'var(--accent-primary)');
    artistBtn.textContent = isCustom ? 'Change songs' : 'Change artist';
    speechBtn.textContent = 'Speech ›';
    step.style.display = 'block';

    window.mergeArtistProgressIntoSourceStep?.();

    picker.onclick = () => {
        if (artistSongCatalog?.songs?.length && window.showSongSetPicker) {
            window.showSongSetPicker();
            return;
        }
        artistBtn.click();
    };
    artistBtn.onclick = () => {
        const language = activeArtist.language || 'spanish';
        const matchingArtists = Object.fromEntries(Object.entries(allArtistsConfig || {}).filter(([, cfg]) =>
            (cfg.language || 'spanish') === language));
        showArtistPicker(picker, matchingArtists, language);
    };
    speechBtn.onclick = () => {
        const targetLang = activeArtist?.language || selectedLanguage || 'spanish';
        window.showAppLoading?.('Switching to Speech', 'Preparing your language and progress…', true);
        sessionStorage.setItem('fluencyPendingSpeechLanguage', targetLang);
        window.location.href = window.location.pathname;
    };

    window.renderSetupExtrasSection?.();
}

window.renderArtistSourceSummary = renderArtistSourceSummary;

window.addEventListener('fluency-song-selection-changed', async () => {
    if (!activeArtist) return;
    cachedVocabularyData = null;
    ppmData = null;
    totalPpm = 0;
    selectedLevel = null;
    selectedRanges = [];
    _findWordIndex = null;
    _findWordIndexKey = null;
    document.getElementById('step4').style.display = 'none';
    renderArtistSourceSummary();
    const loading = document.getElementById('dataLoadingIndicator');
    loading?.classList.add('visible');
    try {
        window.invalidateLyricsSourceCaches?.(selectedLanguage);
        await loadPpmData(selectedLanguage);
        await renderLevelSelector(selectedLanguage, { preferActionable: true });
        await updateExclusionBars();
    } finally {
        loading?.classList.remove('visible');
    }
});

async function setArtistVocabularyScope(scope, { autoStart = false } = {}) {
    if (!activeArtist || !['main', 'extra'].includes(scope)) return;
    if (scope === 'extra' && !isArtistExtraUnlocked()) return;
    const changed = artistVocabularyScope !== scope;
    artistVocabularyScope = scope;
    if (window._urlArtistSlug && window._urlArtistSlug !== CUSTOM_ARTIST_SLUG) {
        replaceRoute({ kind: 'artist', artist: window._urlArtistSlug, scope });
    }
    renderArtistSourceSummary();
    if (!changed && !autoStart) return;

    selectedLevel = null;
    selectedRanges = [];
    _findWordIndex = null;
    _findWordIndexKey = null;
    document.getElementById('step4').style.display = 'none';
    document.getElementById('lemmaToggleContainer').style.display = 'none';
    document.getElementById('cognateToggleContainer').style.display = 'none';
    const loading = document.getElementById('dataLoadingIndicator');
    loading?.classList.add('visible');
    try {
        await renderLevelSelector(selectedLanguage, { preferActionable: true });
        await updateExclusionBars();
        if (autoStart) {
            const firstLevel = document.querySelector('.level-btn.selected')
                || document.querySelector('.level-selector-buttons .level-btn, #levelSelector > .level-btn');
            if (!firstLevel) return;
            const firstSet = Array.from(document.querySelectorAll('#rangeSelector .study-set-dot'))
                .find(dot => !dot.disabled && Number(dot.dataset.pct) < 100)
                || Array.from(document.querySelectorAll('#rangeSelector .study-set-dot'))
                    .find(dot => !dot.disabled);
            if (firstSet) {
                await loadVocabularyData(firstSet.dataset.range, {
                    rankBasis: firstSet.dataset.rankBasis || 'stable',
                    setNumber: Number(firstSet.dataset.index) + 1,
                    levelSetCount: document.querySelectorAll('#rangeSelector .study-set-dot').length,
                });
            }
        }
    } finally {
        loading?.classList.remove('visible');
    }
}

window.setArtistVocabularyScope = setArtistVocabularyScope;

// Extra explainer/confirm modal. Extra is supplementary and reorganises the
// study interface, so entering it requires an explicit confirmation rather than
// a one-tap toggle.
function openExtraScopeModal() {
    const modal = document.getElementById('extraScopeModal');
    if (!modal) { setArtistVocabularyScope('extra'); return; }
    const nameEl = document.getElementById('extraScopeArtistName');
    if (nameEl) {
        nameEl.textContent = activeArtist?.name
            ? `${activeArtist.name} Extra`
            : 'Extra';
    }
    modal.classList.remove('hidden');
}

function closeExtraScopeModal() {
    document.getElementById('extraScopeModal')?.classList.add('hidden');
}

function wireExtraScopeModal() {
    const modal = document.getElementById('extraScopeModal');
    if (!modal) return;
    document.getElementById('closeExtraScopeModal')?.addEventListener('click', closeExtraScopeModal);
    document.getElementById('cancelExtraScopeBtn')?.addEventListener('click', closeExtraScopeModal);
    document.getElementById('confirmExtraScopeBtn')?.addEventListener('click', () => {
        closeExtraScopeModal();
        setArtistVocabularyScope('extra');
    });
    // Dismiss when tapping the backdrop.
    modal.addEventListener('click', event => {
        if (event.target === modal) closeExtraScopeModal();
    });
}

window.openExtraScopeModal = openExtraScopeModal;

// Shared radial "clock of pictures" picker used by artists and languages.
function showRadialPicker({ id, ariaLabel, hubHTML, entries, className = '', closeLabel = '' }) {
    const existing = document.getElementById(id);
    if (existing) { closeRadialPicker(id); return; }

    const n = entries.length;
    if (n === 0) return;
    const maxSeats = 6;
    const overlay = document.createElement('div');
    overlay.id = id;
    overlay.className = 'artist-radial-overlay';
    if (className) overlay.classList.add(...className.split(/\s+/).filter(Boolean));
    overlay.setAttribute('role', 'dialog');
    overlay.setAttribute('aria-modal', 'true');
    overlay.setAttribute('aria-label', ariaLabel);

    const stage = document.createElement('div');
    stage.className = 'artist-radial-stage';

    // Center hub: label + close affordance. The secondary line doubles as the
    // scrub position so a long picker still communicates its full size.
    const hub = document.createElement('div');
    hub.className = 'artist-radial-hub';
    hub.setAttribute('role', 'button');
    hub.setAttribute('tabindex', '0');
    hub.setAttribute('aria-label', `Close ${ariaLabel}`);
    const hubHint = closeLabel || (n > maxSeats ? `Drag ring · 1/${n}` : '');
    hub.innerHTML = `<span class="artist-radial-hub-title">${hubHTML}</span>${hubHint ? `<span class="artist-radial-close-label">${hubHint}</span>` : ''}`;
    stage.appendChild(hub);

    // A radial menu has a fixed visual capacity. Keep one readable ring and
    // rotate the collection through its seats instead of shrinking entries or
    // piling additional translucent rings on top of it.
    const startAngle = -90; // top of the circle (12 o'clock), going clockwise
    const seatCount = Math.min(n, maxSeats);
    const seatStep = 360 / seatCount;
    const radius = 39;
    let scrubIndex = 0;
    let scrubPointer = null;
    let scrubMoved = false;
    let suppressClickUntil = 0;
    const thumbs = [];

    const wrappedDistance = (index, centre) => {
        let distance = index - centre;
        while (distance > n / 2) distance -= n;
        while (distance < -n / 2) distance += n;
        return distance;
    };

    const renderRing = (animate = false) => {
        stage.classList.toggle('is-snapping', animate);
        thumbs.forEach((thumb, index) => {
            const distance = wrappedDistance(index, scrubIndex);
            const snappedDistance = wrappedDistance(index, Math.round(scrubIndex));
            const firstSeat = -Math.floor((seatCount - 1) / 2);
            const lastSeat = firstSeat + seatCount - 1;
            const visible = n <= seatCount
                || (snappedDistance >= firstSeat && snappedDistance <= lastSeat);
            const angle = (startAngle + seatStep * distance) * (Math.PI / 180);
            thumb.style.left = `${50 + radius * Math.cos(angle)}%`;
            thumb.style.top = `${50 + radius * Math.sin(angle)}%`;
            thumb.classList.toggle('is-off-ring', !visible);
            thumb.setAttribute('aria-hidden', visible ? 'false' : 'true');
            thumb.tabIndex = visible && !thumb.disabled ? 0 : -1;
        });
        const hint = hub.querySelector('.artist-radial-close-label');
        if (hint && n > seatCount) {
            const selected = ((Math.round(scrubIndex) % n) + n) % n;
            hint.textContent = `Drag ring · ${selected + 1}/${n}`;
        }
    };

    entries.forEach((entry, i) => {
        const thumb = document.createElement('button');
        thumb.className = 'artist-radial-thumb';
        thumb.setAttribute('aria-label', entry.disabled ? `${entry.label} — coming soon` : entry.label);
        thumb.title = entry.disabled ? `${entry.label} — Data coming soon` : entry.label;
        thumb.disabled = !!entry.disabled;
        if (entry.disabled) thumb.classList.add('artist-radial-thumb--disabled');

        const accent = entry.accent || 'var(--accent-primary)';
        thumb.style.setProperty('--artist-accent', accent);

        const disc = document.createElement('span');
        disc.className = 'artist-radial-disc';
        if (entry.iconHTML) {
            disc.classList.add('artist-radial-disc--icon');
            disc.innerHTML = entry.iconHTML;
        } else if (entry.image) {
            disc.style.backgroundImage = `url('${entry.image}')`;
        } else {
            disc.classList.add('artist-radial-disc--fallback');
            disc.style.background = accent;
            disc.textContent = entry.fallbackText || '?';
        }
        if (entry.discClass) disc.classList.add(entry.discClass);
        thumb.appendChild(disc);

        const label = document.createElement('span');
        label.className = 'artist-radial-label';
        label.textContent = entry.disabled ? `${entry.label} · soon` : entry.label;
        thumb.appendChild(label);

        thumb.addEventListener('click', (e) => {
            e.stopPropagation();
            if (Date.now() < suppressClickUntil) return;
            if (entry.disabled) return;
            closeRadialPicker(id);
            entry.onSelect();
        });

        thumbs.push(thumb);
        stage.appendChild(thumb);
    });

    renderRing();

    const pointerAngle = event => {
        const bounds = stage.getBoundingClientRect();
        return Math.atan2(event.clientY - (bounds.top + bounds.height / 2), event.clientX - (bounds.left + bounds.width / 2)) * 180 / Math.PI;
    };
    const angleDelta = (current, start) => {
        let delta = current - start;
        while (delta > 180) delta -= 360;
        while (delta < -180) delta += 360;
        return delta;
    };
    stage.addEventListener('pointerdown', event => {
        if (event.target === hub || hub.contains(event.target)) return;
        if (event.button !== undefined && event.button !== 0) return;
        scrubPointer = {
            id: event.pointerId,
            angle: pointerAngle(event),
            index: scrubIndex
        };
        scrubMoved = false;
        stage.classList.add('is-scrubbing');
    });
    stage.addEventListener('pointermove', event => {
        if (!scrubPointer || event.pointerId !== scrubPointer.id) return;
        const delta = angleDelta(pointerAngle(event), scrubPointer.angle);
        if (Math.abs(delta) > 4 && !scrubMoved) {
            scrubMoved = true;
            // Capturing on pointerdown retargets an ordinary tap away from the
            // option button. Capture only once this gesture is truly a scrub.
            stage.setPointerCapture?.(event.pointerId);
        }
        scrubIndex = scrubPointer.index + delta / seatStep;
        renderRing();
        if (scrubMoved) event.preventDefault();
    });
    const finishScrub = event => {
        if (!scrubPointer || event.pointerId !== scrubPointer.id) return;
        if (scrubMoved) suppressClickUntil = Date.now() + 400;
        scrubIndex = ((Math.round(scrubIndex) % n) + n) % n;
        scrubPointer = null;
        stage.classList.remove('is-scrubbing');
        renderRing(true);
        setTimeout(() => stage.classList.remove('is-snapping'), 180);
    };
    stage.addEventListener('pointerup', finishScrub);
    stage.addEventListener('pointercancel', finishScrub);

    overlay.appendChild(stage);
    document.body.appendChild(overlay);
    // Trigger enter transition on next frame.
    requestAnimationFrame(() => overlay.classList.add('is-open'));

    // Close on backdrop click, Escape, or hub tap.
    overlay.addEventListener('click', (e) => {
        if (e.target === overlay) closeRadialPicker(id);
    });
    hub.addEventListener('click', () => closeRadialPicker(id));
    hub.addEventListener('keydown', event => {
        if (event.key === 'Enter' || event.key === ' ') {
            event.preventDefault();
            closeRadialPicker(id);
        }
    });
    overlay._radialKeyHandler = e => {
        if (e.key === 'Escape') closeRadialPicker(id);
        if (e.key === 'ArrowRight' || e.key === 'ArrowDown') {
            e.preventDefault();
            scrubIndex = (Math.round(scrubIndex) + 1) % n;
            renderRing(true);
        }
        if (e.key === 'ArrowLeft' || e.key === 'ArrowUp') {
            e.preventDefault();
            scrubIndex = (Math.round(scrubIndex) - 1 + n) % n;
            renderRing(true);
        }
    };
    document.addEventListener('keydown', overlay._radialKeyHandler);
}

function closeRadialPicker(id) {
    const overlay = document.getElementById(id);
    if (!overlay) return;
    if (overlay._radialKeyHandler) {
        document.removeEventListener('keydown', overlay._radialKeyHandler);
    }
    overlay.classList.remove('is-open');
    setTimeout(() => overlay.remove(), 200);
}

window.showRadialPicker = showRadialPicker;
window.closeRadialPicker = closeRadialPicker;

// Stable choice surfaces for lists that can grow. Options keep a fixed place,
// remain discoverable, and can briefly explain the consequence of a choice.
function showChoiceSheet({ id, ariaLabel, title, intro = '', stepLabel = '', entries, variant = 'list', onBack = null, dock = false }) {
    const existing = document.getElementById(id);
    if (existing) { closeChoiceSheet(id); return; }
    if (!entries.length) return;

    const overlay = document.createElement('div');
    overlay.id = id;
    overlay.className = `choice-sheet-overlay choice-sheet-${variant}`;
    overlay.setAttribute('role', 'dialog');
    overlay.setAttribute('aria-modal', 'true');
    overlay.setAttribute('aria-label', ariaLabel);

    const panel = document.createElement('div');
    panel.className = 'choice-sheet-panel';
    const header = document.createElement('div');
    header.className = 'choice-sheet-header';
    if (typeof onBack === 'function') {
        const backBtn = document.createElement('button');
        backBtn.type = 'button';
        backBtn.className = 'choice-sheet-back';
        backBtn.setAttribute('aria-label', 'Back');
        backBtn.textContent = '‹';
        backBtn.addEventListener('click', () => {
            closeChoiceSheet(id, true);
            onBack();
        });
        header.appendChild(backBtn);
    }
    const headingGroup = document.createElement('div');
    headingGroup.className = 'choice-sheet-heading';
    if (stepLabel) {
        const step = document.createElement('span');
        step.className = 'choice-sheet-step';
        step.textContent = stepLabel;
        headingGroup.appendChild(step);
    }
    const heading = document.createElement('h2');
    heading.textContent = title;
    headingGroup.appendChild(heading);
    if (intro) {
        const introduction = document.createElement('p');
        introduction.textContent = intro;
        headingGroup.appendChild(introduction);
    }
    const close = document.createElement('button');
    close.type = 'button';
    close.className = 'choice-sheet-close';
    close.setAttribute('aria-label', `Close ${ariaLabel}`);
    close.textContent = '×';
    header.append(headingGroup, close);

    const body = document.createElement('div');
    body.className = 'choice-sheet-body';
    entries.forEach(entry => {
        const item = document.createElement('button');
        item.type = 'button';
        item.className = 'choice-sheet-item';
        item.disabled = !!entry.disabled;
        item.setAttribute('aria-label', [entry.label, entry.description || (entry.disabled ? 'Coming soon' : ''), entry.selected ? 'Current choice' : ''].filter(Boolean).join('. '));
        if (entry.selected) {
            item.classList.add('is-selected');
            item.setAttribute('aria-current', 'true');
        }

        const icon = document.createElement('span');
        icon.className = 'choice-sheet-icon';
        icon.style.setProperty('--choice-accent', entry.accent || 'var(--accent-primary)');
        if (entry.iconHTML) icon.innerHTML = entry.iconHTML;
        else if (entry.image) {
            icon.classList.add('choice-sheet-icon--image');
            icon.style.backgroundImage = `url('${entry.image}')`;
        }
        else icon.textContent = entry.fallbackText || '•';

        const copy = document.createElement('span');
        copy.className = 'choice-sheet-copy';
        const label = document.createElement('strong');
        label.textContent = entry.label;
        copy.appendChild(label);
        if (entry.disabled || entry.description) {
            const detail = document.createElement('small');
            detail.textContent = entry.description || (entry.disabled ? 'Coming soon' : '');
            copy.appendChild(detail);
        }

        const tail = document.createElement('span');
        tail.className = 'choice-sheet-tail';
        tail.setAttribute('aria-hidden', 'true');
        tail.textContent = entry.tail ?? (entry.selected ? '✓' : (entry.disabled ? '' : '›'));
        item.append(icon, copy, tail);
        item.addEventListener('click', event => {
            event.stopPropagation();
            if (entry.disabled) return;
            // A toggle stays open and redraws itself from refresh(), so the
            // row always states the current setting.
            if (entry.keepOpen) {
                entry.onSelect();
                const next = entry.refresh?.() || {};
                if (next.label) {
                    label.textContent = next.label;
                    item.setAttribute('aria-label', next.label);
                }
                if (next.iconHTML) icon.innerHTML = next.iconHTML;
                return;
            }
            closeChoiceSheet(id, true);
            entry.onSelect();
        });
        body.appendChild(item);
    });

    panel.append(header, body);
    overlay.appendChild(panel);
    document.body.appendChild(overlay);
    if (dock) window.sideDock?.placeById?.(id);
    requestAnimationFrame(() => overlay.classList.add('is-open'));

    close.addEventListener('click', () => closeChoiceSheet(id));
    overlay.addEventListener('click', event => {
        if (event.target === overlay) closeChoiceSheet(id);
    });
    overlay._choiceSheetKeyHandler = event => {
        if (event.key === 'Escape') closeChoiceSheet(id);
    };
    document.addEventListener('keydown', overlay._choiceSheetKeyHandler);
    requestAnimationFrame(() => body.querySelector('button:not(:disabled)')?.focus());
}

function closeChoiceSheet(id, immediate = false) {
    const overlay = document.getElementById(id);
    if (!overlay) return;
    if (overlay._choiceSheetKeyHandler) {
        document.removeEventListener('keydown', overlay._choiceSheetKeyHandler);
    }
    overlay.style.pointerEvents = 'none';
    overlay.classList.remove('is-open');
    if (immediate) overlay.remove();
    else setTimeout(() => overlay.remove(), 180);
}

window.showChoiceSheet = showChoiceSheet;
window.closeChoiceSheet = closeChoiceSheet;

function showAvailableMusicPicker(artists) {
    const pickerLanguage = Object.values(artists || {})[0]?.language || 'spanish';
    const entries = Object.entries(artists || {}).map(([slug, cfg]) => ({
        label: cfg.name,
        description: 'Build a set from this artist’s available songs.',
        image: artistPickerImage(cfg),
        fallbackText: artistInitials(cfg.name),
        accent: (cfg.colorTheme && cfg.colorTheme.primary) || 'var(--accent-primary)',
        onSelect: () => {
            window.clearPlaylistLiveSession?.();
            showAppLoading(`Loading ${cfg.name}`, 'Preparing lyrics, levels and progress…', true);
            goToRoute({ kind: 'artist', artist: slug });
        }
    }));
    if (Object.values(artists || {}).some(cfg => cfg.songsPath)) {
        entries.push({
            label: 'Choose individual songs',
            description: 'Build a mix from the songs currently available in Fluency.',
            iconHTML: customSongsIcon(),
            accent: '#10B981',
            onSelect: () => {
                window.clearPlaylistLiveSession?.();
                showAppLoading('Opening your songs', 'Combining the available Lyrics catalogues…', true);
                goToRoute({ kind: 'songs', language: routeCodeFor(pickerLanguage, config?.languages) });
            }
        });
    }
    showChoiceSheet({
        id: 'artistChoiceSheet',
        ariaLabel: 'Choose artists or songs',
        title: 'Choose your music',
        intro: 'Pick an artist, or combine individual songs into one vocabulary list.',
        stepLabel: 'Lyrics · Choose songs',
        onBack: () => showArtistPicker(null, artists, pickerLanguage),
        variant: 'list',
        entries
    });
}

async function ensureArtistCatalog() {
    if (allArtistsConfig && Object.keys(allArtistsConfig).length > 0) {
        return allArtistsConfig;
    }
    try {
        let value = null;
        try {
            const response = await fetch(artistCatalogUrl(), { cache: 'no-store' });
            if (response.ok) value = await response.json();
        } catch (_) {}
        if (!value || Object.keys(value).length === 0) {
            try {
                const fallbackResp = await fetch(releaseUrl('releases/lyrics/lyrics-all-artists-v7-native-20260825b/app/config/artists.json'), { cache: 'no-store' });
                if (fallbackResp.ok) value = await fallbackResp.json();
            } catch (_) {}
        }
        allArtistsConfig = bindArtistCatalogToRelease(
            validateArtistCatalog(value || {}, { source: 'config/artists.json' }),
            requestedLyricsRelease()
        );
        for (const [slug, cfg] of Object.entries(allArtistsConfig)) {
            cfg.slug = slug;
        }
        window._allArtistsConfig = allArtistsConfig;
    } catch (error) {
        console.warn('Could not load lyric artists:', error);
        allArtistsConfig = {};
    }
    return allArtistsConfig;
}

// Music setup begins with the source method, then opens the growing catalogue.
async function showArtistPicker(anchorBtn, artists, targetLanguage = null) {
    let resolvedArtists = artists;
    const language = targetLanguage || Object.values(artists || {})[0]?.language || selectedLanguage || 'spanish';
    if (!resolvedArtists || Object.keys(resolvedArtists).length === 0) {
        const catalog = await ensureArtistCatalog();
        resolvedArtists = Object.fromEntries(Object.entries(catalog || {}).filter(([, cfg]) =>
            (cfg.language || 'spanish') === language));
    }
    const hasAvailableMusic = Object.keys(resolvedArtists || {}).length > 0;
    showChoiceSheet({
        id: 'lyricsSourceSheet',
        ariaLabel: 'Choose how to add music',
        title: 'How would you like to choose music?',
        intro: 'Your choice determines where the song words and example lines come from.',
        stepLabel: 'Lyrics · Choose source',
        onBack: openLearningSourcePicker,
        variant: 'list',
        entries: [
            {
                label: 'Choose artists or songs',
                description: hasAvailableMusic
                    ? 'Pick an artist or individual songs from the Fluency lyrics library.'
                    : 'No music collection has been published for this language yet.',
                fallbackText: '♫',
                accent: 'var(--accent-primary)',
                disabled: !hasAvailableMusic,
                onSelect: () => {
                    window.clearPlaylistLiveSession?.();
                    showAvailableMusicPicker(resolvedArtists);
                }
            },
            {
                label: 'Match a Spotify playlist',
                description: hasAvailableMusic
                    ? 'Import a playlist and use songs already in the Fluency lyrics library.'
                    : 'No music collection has been published for this language yet.',
                fallbackText: '∩',
                accent: '#10B981',
                disabled: !hasAvailableMusic,
                onSelect: () => {
                    window.clearPlaylistLiveSession?.();
                    window.openSpotifyPlaylistImport?.(resolvedArtists, language, { live: false });
                }
            },
            {
                label: 'Live playlist',
                description: 'Look up your playlist now. Cards use speech meanings with your song lines; meaning matching is limited.',
                fallbackText: '＋',
                accent: '#F59E0B',
                onSelect: () => window.openSpotifyPlaylistImport?.(resolvedArtists, language, { live: true })
            }
        ]
    });
}

function openLearningSourcePicker() {
    const language = activeArtist?.language || selectedLanguage || 'spanish';
    const languageConfig = config.languages?.[language] || {};
    const lyricsCatalog = languageConfig.capabilities?.lyrics !== false;
    const speechAvailable = languageConfig.capabilities?.speech !== false;
    const lyricsAvailable = lyricsCatalog || speechAvailable;
    showChoiceSheet({
        id: 'learningSourceChoiceSheet',
        ariaLabel: 'Choose vocabulary',
        title: 'What do you want to understand?',
        intro: 'Choose a source for your words. You can switch later and keep your card progress.',
        stepLabel: `${languageConfig.name || language} · Choose mode`,
        variant: 'list',
        entries: [
            {
                label: 'Everyday Speech',
                description: 'Common words from films and TV, ordered by how often people say them.',
                fallbackText: '1',
                selected: !activeArtist && !window.playlistLiveActive?.(),
                onSelect: () => {
                    if (window.playlistLiveActive?.()) {
                        window.clearPlaylistLiveSession?.();
                        sessionStorage.setItem('fluencyPendingSpeechLanguage', language);
                        goToRoute({ kind: 'language', language: routeCodeFor(language, config?.languages) });
                        return;
                    }
                    if (activeArtist) {
                        showAppLoading('Switching to speech vocabulary', 'Preparing your language and progress…', true);
                        sessionStorage.setItem('fluencyPendingSpeechLanguage', language);
                        window.location.href = window.location.pathname;
                    } else {
                        document.getElementById('standardSourceSpeechBtn')?.click();
                    }
                }
            },
            {
                label: 'Music & lyrics',
                description: lyricsCatalog
                    ? 'Learn words from artists and songs you choose, with their lyric lines as examples.'
                    : 'Look up a playlist and study speech meanings with its lyric lines.',
                fallbackText: '2',
                selected: Boolean(activeArtist || window.playlistLiveActive?.()),
                disabled: !lyricsAvailable,
                onSelect: () => {
                    showArtistPicker(null, null, language);
                }
            }
        ]
    });
}

window.openLearningSourcePicker = openLearningSourcePicker;

// Language is chosen first; this lightweight picker is the Lyrics branch of
// the subsequent source choice. It loads only catalogue metadata until the
// learner selects an exact artist or custom collection.
async function showLyricsPicker(language, anchorBtn = null) {
    const catalog = await ensureArtistCatalog();
    const matchingArtists = Object.fromEntries(Object.entries(catalog || {}).filter(([, cfg]) =>
        (cfg.language || 'spanish') === language));
    showArtistPicker(anchorBtn, matchingArtists, language);
}

window.showLyricsPicker = showLyricsPicker;
window.showArtistPicker = showArtistPicker;

function showPortugueseVarietyPicker() {
    showChoiceSheet({
        id: 'portugueseVarietyChoiceSheet',
        ariaLabel: 'Choose Portuguese variety',
        title: 'Portuguese',
        intro: 'Choose variety',
        variant: 'list',
        onBack: () => showLanguagePicker(config.languages),
        entries: [
            {
                label: 'European Portuguese',
                fallbackText: '🇵🇹',
                description: 'Available now',
                accent: (config.languages?.portuguese?.colorTheme?.primary) || '#046A38',
                selected: selectedLanguage === 'portuguese',
                onSelect: () => {
                    document.querySelector('.lang-tab[data-lang="portuguese"]')?.click();
                }
            },
            {
                label: 'Brazilian Portuguese',
                fallbackText: '🇧🇷',
                disabled: true,
                description: 'Coming soon',
                accent: '#009c3b'
            }
        ]
    });
}

window.showPortugueseVarietyPicker = showPortugueseVarietyPicker;

// Standard-mode language adapter: flag pictures + existing hidden language
// buttons, so all loading/theme/progress behavior stays in ui.js.
function showLanguagePicker(languages) {
    const languageOrder = config.languageDisplayOrder || Object.keys(config.languages);
    // Flags live on each language's own config entry.
    const flags = Object.fromEntries(
        Object.entries(languages).map(([key, cfg]) => [key, cfg.flag || ''])
    );
    // Languages with no data yet go last, whatever order config declares. It was
    // declared order alone before, which meant every new language had to be
    // hand-placed ahead of the "soon" ones or it landed among them. Ready
    // languages keep their declared order relative to each other.
    // Brazilian Portuguese is chosen via the Portuguese variety picker rather
    // than having a duplicate orphaned tile.
    const ready = key => languages[key].hasData !== false;
    const ordered = languageOrder.filter(key => languages[key] && key !== 'portuguese_brazilian');
    const entries = [...ordered.filter(ready), ...ordered.filter(key => !ready(key))].map(key => {
        const cfg = languages[key];
        const isPortuguese = key === 'portuguese';
        return {
            label: cfg.name,
            fallbackText: flags[key] || '🌐',
            accent: (cfg.colorTheme && cfg.colorTheme.primary) || 'var(--accent-primary)',
            disabled: cfg.hasData === false,
            selected: key === selectedLanguage,
            onSelect: () => {
                if (isPortuguese) {
                    showPortugueseVarietyPicker();
                } else {
                    document.querySelector(`.lang-tab[data-lang="${key}"]`)?.click();
                }
            }
        };
    });
    showChoiceSheet({
        id: 'languageChoiceSheet',
        ariaLabel: 'Choose a language',
        title: 'Choose a language',
        intro: 'Pick the language you want to understand. You will choose Speech or Lyrics next.',
        stepLabel: 'Learning setup · Language',
        variant: 'grid',
        entries
    });
}

window.showLanguagePicker = showLanguagePicker;

// ===== Find-word: simple lookup of a word across the current language's vocab =====
let _findWordIndex = null; // [{ targetWord, lemma, rank, displayRank, id, firstMeaning }]
let _findWordIndexKey = null;

function normalizeForSearch(s) {
    return (s || '')
        .toString()
        .toLowerCase()
        .normalize('NFD')
        .replace(/[\u0300-\u036f]/g, '');
}

function findWordCacheKey() {
    const slugs = (window._selectedArtistSlugs || []).slice().sort().join(',');
    // Filter toggles change displayRank; include them so the cache invalidates.
    return [
        selectedLanguage || '',
        slugs,
        useLemmaMode ? '1' : '0',
        excludeCognates ? '1' : '0',
        activeArtist ? artistVocabularyScope : (hideSingleOccurrence ? '1' : '0'),
        excludeProperNouns ? '1' : '0',
        excludeNoise ? '1' : '0',
        excludeEnglishLoanwords ? '1' : '0'
    ].join('|');
}

async function buildFindWordIndex() {
    if (!selectedLanguage) return [];
    const key = findWordCacheKey();
    if (_findWordIndex && _findWordIndexKey === key) return _findWordIndex;
    const langConfig = config.languages[selectedLanguage];
    if (!langConfig) return [];
    let vocabularyData;
    // Reuse the cached merged index in multi-artist mode when present
    if (activeArtist && window._cachedMergedIndex) {
        vocabularyData = window._cachedMergedIndex;
    } else {
        vocabularyData = await window.fetchAndJoinIndex(langConfig);
    }
    vocabularyData.forEach((item, idx) => { if (!item.rank) item.rank = idx + 1; });
    // Build displayRank via the normal filter pipeline so ranks line up with
    // the set buttons. Clone each entry because the deck filter intentionally
    // strips empty meanings; search must not mutate its full source index.
    const filterInput = vocabularyData.map(item => ({
        ...item,
        meanings: Array.isArray(item.meanings) ? [...item.meanings] : []
    }));
    const { vocab: filtered } = window.buildFilteredVocab(filterInput);
    const byRank = new Map();
    filtered.forEach(it => byRank.set(it.rank, it.displayRank));
    const idx = vocabularyData.map(item => {
        const meanings = item.meanings || [];
        const matchedMeanings = meanings.filter(meaning =>
            meaning
            && String(meaning.translation || '').trim()
            && (!activeArtist || Number(meaning.frequency || 0) > 0));
        const firstMeaning = matchedMeanings.find(m =>
            m.pos !== 'MWE' && m.pos !== 'CLITIC' && m.pos !== 'SENSE_CYCLE');
        // Headwords, not lemma: a surface-keyed card can group several
        // (casa -> casa + casar), and the single `lemma` field is the old
        // one-lemma-per-card model.
        const headwords = [...new Set(
            meanings.map(meaning => meaning && meaning.headword).filter(Boolean)
        )];
        return {
            targetWord: item.word || item.targetWord || '',
            lemma: item.lemma || '',
            headwords,
            fullId: window.getWordId(item),
            rank: item.rank,
            displayRank: byRank.get(item.rank) || null,
            id: item.id || window.getWordId(item),
            firstMeaning: firstMeaning ? firstMeaning.translation : '',
            firstMeaningObj: firstMeaning || null,
            exclusionReason: window.getVocabularyExclusionReason?.(item) || null,
            examplesOnly: matchedMeanings.length === 0,
            sourceEntry: item
        };
    });
    _findWordIndex = idx;
    _findWordIndexKey = key;
    return idx;
}

let _findWordFilter = 'all';

function renderFindResults(query) {
    const resultsEl = document.getElementById('findWordResults');
    const statusEl = document.getElementById('findWordStatus');
    resultsEl.innerHTML = '';
    const q = normalizeForSearch(query).trim();
    if (!q) {
        statusEl.textContent = _findWordIndex ? `${_findWordIndex.length.toLocaleString()} words loaded` : '';
        return;
    }
    if (!_findWordIndex) { statusEl.textContent = 'Loading…'; return; }
    const matches = [];
    for (const entry of _findWordIndex) {
        const w = normalizeForSearch(entry.targetWord);
        // Searching a headword should still find the card that carries it —
        // `casar` lands on the `casa` card, because that is where the meaning
        // now lives.
        const heads = (entry.headwords || []).map(normalizeForSearch);
        const exact = w === q || heads.includes(q);
        const starts = w.startsWith(q) || heads.some(h => h.startsWith(q));
        const contains = w.includes(q) || heads.some(h => h.includes(q));
        if (exact || starts || contains) {
            matches.push({ entry, score: exact ? 0 : (starts ? 1 : 2) });
        }
        if (matches.length > 300) break;
    }
    matches.sort((a, b) => a.score - b.score || (a.entry.rank || 1e9) - (b.entry.rank || 1e9));
    const filteredMatches = [];
    for (const match of matches) {
        if (_findWordFilter !== 'all') {
            const progress = window.getMergedWordProgress?.(match.entry.fullId, match.entry.targetWord);
            const state = window.getProgressState?.(progress) || { status: 'unseen' };
            if (state.status !== _findWordFilter) continue;
        }
        filteredMatches.push(match);
    }
    const top = filteredMatches.slice(0, 30);
    if (top.length === 0) {
        statusEl.textContent = 'No matches';
        return;
    }
    statusEl.textContent = `${filteredMatches.length} match${filteredMatches.length === 1 ? '' : 'es'}${filteredMatches.length > top.length ? ` — showing top ${top.length}` : ''}`;
    for (const { entry } of top) {
        const btn = document.createElement('button');
        btn.type = 'button';
        btn.className = 'find-word-result';
        // Headwords only when the card groups more than one, or when the single
        // headword differs from the surface. One headword equal to the surface
        // is the common case and says nothing worth a chip.
        const heads = (entry.headwords || []).filter(Boolean);
        const showHeads = heads.length > 1
            || (heads.length === 1 && heads[0] !== entry.targetWord);
        const lemmaHTML = showHeads
            ? `<span class="fw-lemma">${heads.join(' · ')}</span>` : '';

        // Whether this card is done. Without it there is no way to check a card
        // from search — the whole reason for looking one up. Falls back to the
        // other mode's record, so a word studied only in lyrics reads as known
        // in speech, which is exactly what surface identity restored.
        const progress = window.getMergedWordProgress?.(entry.fullId, entry.targetWord);
        const state = window.getProgressState?.(progress) || { status: 'unseen' };
        let doneHTML = '<span class="fw-done fw-done--unseen">Not seen</span>';
        if (state.status === 'learned') {
            doneHTML = `<span class="fw-done fw-done--known">Known${
                state.lastCorrect ? ` · ${new Date(state.lastCorrect).toLocaleDateString()}` : ''}</span>`;
        } else if (state.status === 'review') {
            doneHTML = state.reviewReason === 'due'
                ? '<span class="fw-done fw-done--due">Due</span>'
                : '<span class="fw-done fw-done--review">Review</span>';
        }

        let promBadgeHTML = '';
        if (entry.firstMeaningObj && typeof window.getSenseProminenceInfo === 'function') {
            const prom = window.getSenseProminenceInfo(entry.firstMeaningObj);
            if (prom && prom.label) {
                promBadgeHTML = typeof window.prominenceBadgeHTML === 'function'
                    ? window.prominenceBadgeHTML(prom)
                    : `<button type="button" class="sense-prominence-badge prominence-${prom.key}">${prom.label}</button>`;
            }
        }

        const statusHTML = entry.exclusionReason
            ? `<span class="fw-status fw-status--excluded">Excluded · ${entry.exclusionReason}</span>`
            : (entry.examplesOnly
                ? '<span class="fw-status">Examples only</span>'
                : (entry.displayRank ? `<span class="fw-rank">#${entry.displayRank}</span>` : ''));
        btn.innerHTML = `
            <span class="fw-word">${entry.targetWord}</span>
            ${lemmaHTML}
            <span class="fw-meaning-group">
                <span class="fw-meaning">${(entry.firstMeaning || '').replace(/</g, '&lt;')}</span>
                ${promBadgeHTML}
            </span>
            ${doneHTML}
            ${statusHTML}`;
        btn.addEventListener('click', () => jumpToFoundWord(entry));
        resultsEl.appendChild(btn);
    }
    const first = resultsEl.querySelector('.find-word-result');
    if (first) first.classList.add('is-active');
}

async function jumpToFoundWord(entry) {
    // Open the word as a standalone popup card via the cardNavStack pattern.
    // navigateBack reopens the search modal afterwards.
    if (window.popupFoundWord) {
        try {
            await window.popupFoundWord(entry);
        } catch (e) {
            console.error('Find-word: popupFoundWord failed', e);
            document.getElementById('findWordModal')?.classList.remove('hidden');
            const statusEl = document.getElementById('findWordStatus');
            // Name the actual failure. A bare "Could not open card" is
            // indistinguishable between a missing entry, a lazy-module load
            // failure, and a render exception — and on a phone there is no
            // console to check, so the reason has to reach the sheet itself.
            if (statusEl) {
                const where = String(e?.stack || '').split('\n')[1]?.trim() || '';
                statusEl.textContent = `Could not open card — ${e?.message || e}`
                    + (where ? ` (${where.slice(0, 80)})` : '');
            }
        }
    }
}

// #/es/w/unidos: the word as a single card, like a search result, so it
// counts toward progress when marked. Waits for sign-in (the landing sits on
// top for a first visit) and for progress, so known/unknown reads correctly.
// Leaving the card clears the route and lands on that language's menu.
async function openRouteWord(route, languageKey) {
    await window.authReady;
    await window.whenProgressReady?.();
    const surface = normalizeForSearch(route.surface).trim();
    let entry = null;
    try {
        const index = await buildFindWordIndex();
        const matches = index.filter(item => normalizeForSearch(item.targetWord) === surface);
        entry = matches.find(item => item.targetWord === route.surface)
            || matches.find(item => item.targetWord.toLocaleLowerCase() === route.surface.toLocaleLowerCase())
            || matches[0]
            || null;
    } catch (error) {
        console.warn('Linked word: vocabulary unavailable', error);
    }
    const chooseLanguage = () => {
        const tab = document.querySelector(`.lang-tab[data-lang="${languageKey}"]`);
        if (tab && !tab.disabled) tab.click();
    };
    if (!entry) {
        // Not in this deck: say so where the learner can act on it — search,
        // with the word already typed and its near matches listed.
        chooseLanguage();
        await openFindWordFor(route.surface);
        return;
    }
    try {
        // The index flags "examples only" from rows that may not be loaded
        // yet; popupFoundWord loads them and judges from the real meanings.
        await window.popupFoundWord({ ...entry, examplesOnly: false }, {
            reopenSearchOnBack: false,
            onClose: () => {
                window.fluencyRoutes?.clearRoute();
                chooseLanguage();
            }
        });
    } catch (error) {
        console.error('Linked word: could not open card', error);
        chooseLanguage();
        await openFindWordFor(route.surface);
    }
}

async function openFindWordFor(word) {
    await window.openFindWord?.();
    const input = document.getElementById('findWordInput');
    if (!input) return;
    input.value = word;
    renderFindResults(word);
}

function isFindWordOpen() {
    const modal = document.getElementById('findWordModal');
    return Boolean(modal && !modal.classList.contains('hidden'));
}

function closeFindWord() {
    document.getElementById('findWordModal')?.classList.add('hidden');
}

function moveFindWordHighlight(delta) {
    const items = [...document.querySelectorAll('#findWordResults .find-word-result')];
    if (!items.length) return;
    const current = items.findIndex(el => el.classList.contains('is-active'));
    const next = current < 0
        ? (delta > 0 ? 0 : items.length - 1)
        : Math.max(0, Math.min(items.length - 1, current + delta));
    items.forEach((el, i) => el.classList.toggle('is-active', i === next));
    items[next].scrollIntoView({ block: 'nearest' });
}

function setupFindWord() {
    const modal = document.getElementById('findWordModal');
    const closeBtn = document.getElementById('closeFindWordModal');
    const input = document.getElementById('findWordInput');
    const filterContainer = document.getElementById('findWordFilters');
    const hotkey = document.getElementById('findWordHotkey');
    if (!modal || !input) return;

    if (hotkey) {
        const isMac = /Mac|iPhone|iPad|iPod/i.test(navigator.platform || navigator.userAgent || '');
        hotkey.textContent = isMac ? '⌘F' : 'Ctrl+F';
        hotkey.hidden = false;
    }

    if (filterContainer && !filterContainer._filterWired) {
        filterContainer._filterWired = true;
        filterContainer.addEventListener('click', (e) => {
            const chip = e.target.closest('.find-word-filter-btn');
            if (!chip) return;
            filterContainer.querySelectorAll('.find-word-filter-btn').forEach(b => b.classList.remove('is-active'));
            chip.classList.add('is-active');
            _findWordFilter = chip.dataset.filter || 'all';
            renderFindResults(input.value);
        });
    }

    async function openFindWord() {
        document.getElementById('settingsModal')?.classList.add('hidden');
        modal.classList.remove('hidden');
        input.value = '';
        _findWordFilter = 'all';
        if (filterContainer) {
            filterContainer.querySelectorAll('.find-word-filter-btn').forEach(b => {
                b.classList.toggle('is-active', b.dataset.filter === 'all');
            });
        }
        document.getElementById('findWordResults').innerHTML = '';
        document.getElementById('findWordStatus').textContent = selectedLanguage
            ? 'Loading vocabulary…'
            : 'Choose a language first.';
        setTimeout(() => input.focus(), 50);
        try {
            await buildFindWordIndex();
            renderFindResults(input.value);
        } catch (e) {
            console.error('Find-word: failed to build index', e);
            document.getElementById('findWordStatus').textContent = 'Could not load vocabulary.';
        }
    }
    window.openFindWord = openFindWord;
    window.closeFindWord = closeFindWord;

    document.querySelectorAll('[data-open-find-word]').forEach(btn => {
        if (btn.dataset.findWordWired) return;
        btn.dataset.findWordWired = 'true';
        btn.addEventListener('click', () => openFindWord());
    });

    closeBtn?.addEventListener('click', closeFindWord);
    modal.addEventListener('click', (e) => {
        if (e.target === modal) closeFindWord();
    });

    document.addEventListener('keydown', (e) => {
        const key = String(e.key || '').toLowerCase();
        const findShortcut = (e.metaKey || e.ctrlKey) && !e.altKey && !e.shiftKey && key === 'f';
        if (findShortcut) {
            e.preventDefault();
            e.stopImmediatePropagation();
            if (isFindWordOpen()) {
                input.focus();
                input.select();
                return;
            }
            openFindWord();
            return;
        }
        if (e.key === 'Escape' && isFindWordOpen()) {
            e.preventDefault();
            e.stopImmediatePropagation();
            closeFindWord();
        }
    }, true);

    let debounce = null;
    input.addEventListener('input', () => {
        clearTimeout(debounce);
        debounce = setTimeout(() => renderFindResults(input.value), 80);
    });
    input.addEventListener('keydown', (e) => {
        if (e.key === 'ArrowDown') {
            e.preventDefault();
            moveFindWordHighlight(1);
        } else if (e.key === 'ArrowUp') {
            e.preventDefault();
            moveFindWordHighlight(-1);
        } else if (e.key === 'Enter') {
            const active = document.querySelector('#findWordResults .find-word-result.is-active')
                || document.querySelector('#findWordResults .find-word-result');
            if (active) active.click();
        }
    });
}

const FREQUENCY_INTRO_KEY = 'fluencySeenFrequencyIntroV2';

function closeFrequencyIntro() {
    document.getElementById('frequencyIntroModal')?.classList.add('hidden');
}

function markFrequencyIntroSeen() {
    try { localStorage.setItem(FREQUENCY_INTRO_KEY, '1'); } catch (_) {}
}

// A first visit shows the frequency explainer on choosing a language; a sheet
// opened by a link waits for it rather than stacking on top.
function frequencyIntroClosed() {
    const modal = document.getElementById('frequencyIntroModal');
    if (!modal || modal.classList.contains('hidden')) return Promise.resolve();
    return new Promise(resolve => {
        const observer = new MutationObserver(() => {
            if (!modal.classList.contains('hidden')) return;
            observer.disconnect();
            resolve();
        });
        observer.observe(modal, { attributes: true, attributeFilter: ['class'] });
    });
}

function maybeShowFrequencyIntro() {
    try {
        if (localStorage.getItem(FREQUENCY_INTRO_KEY) === '1') return false;
    } catch (_) {
        return false;
    }
    const route = window.fluencyRoute?.kind;
    if (route === 'about' || route === 'tutorial' || route === 'walkthrough' || route === 'word') return false;
    const auth = document.getElementById('authModal');
    if (auth && !auth.classList.contains('hidden')) return false;
    const modal = document.getElementById('frequencyIntroModal');
    if (!modal || !modal.classList.contains('hidden')) return false;
    if (document.querySelector('.modal:not(.hidden)')) return false;
    window.closeChoiceSheet?.('languageChoiceSheet');
    modal.classList.remove('hidden');
    return true;
}

function setupFrequencyIntro() {
    document.getElementById('skipFrequencyIntroBtn')?.addEventListener('click', () => {
        markFrequencyIntroSeen();
        closeFrequencyIntro();
    });
    document.getElementById('frequencyIntroTutorialBtn')?.addEventListener('click', () => {
        markFrequencyIntroSeen();
        closeFrequencyIntro();
        openTutorialIntroduction();
    });
    document.getElementById('frequencyIntroModal')?.addEventListener('click', event => {
        if (event.target === event.currentTarget) {
            markFrequencyIntroSeen();
            closeFrequencyIntro();
        }
    });
    window.maybeShowFrequencyIntro = maybeShowFrequencyIntro;
}
