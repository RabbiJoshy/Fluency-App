// Shareable links. The URL fragment names one thing to open and nothing else:
//
//   #/es                     a language, picker skipped
//   #/es/w/unidos            one word, as a single card (card_id is the surface)
//   #/artist/bad-bunny       an artist deck; /extra for the extra deck
//   #/es/songs               your songs: chosen ones, or a playlist matched
//                            against the lyrics library
//   #/es/live                your live playlist deck, looked up from lyrics
//   #/about  #/tutorial  #/walkthrough
//
// The two playlist routes open a mode, not a deck: the songs behind them are
// the learner's own, so the link reopens that learner's deck, or starts the
// playlist picker for someone who has none yet.
//
// Hash routes because GitHub Pages serves no fallback for unknown paths.
// Developer switches (speechRelease, lyricsRelease, wsdPublication, perf,
// resume) stay in the query string, orthogonal to the route.
//
// Mode is decided once at boot, so moving to another route reloads the page.
// The reload is flagged in sessionStorage so auth.js keeps a guest session
// through it, exactly as it does for an ordinary same-tab navigation.

const PAGE_ROUTES = new Set(['about', 'tutorial', 'walkthrough']);
const ROUTE_NAV_FLAG = 'fluencyRouteNav';

function decodePart(part) {
    try { return decodeURIComponent(part); } catch (_) { return part; }
}

export function parseRoute(hash) {
    const raw = String(hash || '').replace(/^#\/?/, '');
    const parts = raw.split('/').filter(Boolean).map(decodePart);
    if (parts.length === 0) return { kind: 'home' };
    const [first, second, third] = parts;
    if (parts.length === 1 && PAGE_ROUTES.has(first)) return { kind: first };
    if (first === 'artist' && second && second !== 'custom') {
        return { kind: 'artist', artist: second, scope: third === 'extra' ? 'extra' : 'main' };
    }
    if (parts.length === 1) return { kind: 'language', language: first };
    if (parts.length === 2 && (second === 'songs' || second === 'live')) return { kind: second, language: first };
    if (parts.length === 3 && second === 'w' && third) return { kind: 'word', language: first, surface: third };
    return { kind: 'unknown' };
}

export function formatRoute(route) {
    const enc = value => encodeURIComponent(String(value));
    switch (route?.kind) {
        case 'about':
        case 'tutorial':
        case 'walkthrough':
            return `#/${route.kind}`;
        case 'language':
            return `#/${enc(route.language)}`;
        case 'word':
            return `#/${enc(route.language)}/w/${enc(route.surface)}`;
        case 'songs':
        case 'live':
            return `#/${enc(route.language)}/${route.kind}`;
        case 'artist':
            return `#/artist/${enc(route.artist)}${route.scope === 'extra' ? '/extra' : ''}`;
        default:
            return '';
    }
}

// Old query-string links, still in bookmarks, home-screen installs and
// messages already sent. Returns the route they meant and the query string
// with those keys removed; every other key is left exactly as it was.
export function legacyRoute(search) {
    const params = new URLSearchParams(search || '');
    let artist = params.get('artist');
    if (!artist && params.get('mode') === 'badbunny') artist = 'bad-bunny';
    let route = null;
    if (artist) {
        route = artist === 'custom'
            ? { kind: 'songs', language: params.get('language') || 'spanish' }
            : { kind: 'artist', artist, scope: params.get('scope') === 'extra' ? 'extra' : 'main' };
        params.delete('artist');
        params.delete('scope');
        if (params.get('mode') === 'badbunny') params.delete('mode');
        if (artist === 'custom') params.delete('language');
    } else if (params.get('mode') === 'badbunny') {
        params.delete('mode');
    }
    if (params.get('playlistLive') === '1') {
        if (!route) route = { kind: 'live', language: params.get('language') || 'spanish' };
        params.delete('playlistLive');
        params.delete('language');
    }
    if (params.has('about')) {
        if (!route) route = { kind: 'about' };
        params.delete('about');
    }
    // A bare ?language= was the speech-mode hand-off out of a live playlist.
    if (!route && params.has('language')) {
        route = { kind: 'language', language: params.get('language') };
        params.delete('language');
    }
    const rest = params.toString();
    return { route, search: rest ? `?${rest}` : '' };
}

// A route names a language by its config key (`spanish`) or by the entry's
// own routeCode (`es`). Unknown tokens resolve to null — declared, not guessed.
export function languageKeyFor(token, languages) {
    if (!token || !languages) return null;
    const wanted = String(token).toLowerCase();
    for (const [key, cfg] of Object.entries(languages)) {
        if (key.toLowerCase() === wanted) return key;
        if (cfg && String(cfg.routeCode || '').toLowerCase() === wanted) return key;
    }
    return null;
}

export function routeCodeFor(key, languages) {
    return (languages && languages[key] && languages[key].routeCode) || key;
}

// Rewrite the address bar from an old query link to its route, once, before
// anything else reads the URL. Returns the route now in force.
export function adoptLegacyUrl(loc = window.location) {
    const { route, search } = legacyRoute(loc.search);
    // A route already in the fragment wins over a stale query beside it.
    const hash = route && parseRoute(loc.hash).kind === 'home' ? formatRoute(route) : loc.hash;
    if (search !== loc.search || hash !== loc.hash) {
        history.replaceState(null, '', `${loc.pathname}${search}${hash}`);
    }
    return parseRoute(loc.hash);
}

export function routeHref(route, { keepSearch = true } = {}) {
    const loc = window.location;
    return `${loc.pathname}${keepSearch ? loc.search : ''}${formatRoute(route)}`;
}

// Change mode: push the new address and reload into it.
export function goToRoute(route, options) {
    const href = routeHref(route, options);
    try { sessionStorage.setItem(ROUTE_NAV_FLAG, '1'); } catch (_) {}
    history.pushState(null, '', href);
    window.location.reload();
}

// Replace the address without reloading, for state the page already shows.
export function replaceRoute(route) {
    history.replaceState(null, '', routeHref(route));
}

export function clearRoute() {
    const loc = window.location;
    history.replaceState(null, '', `${loc.pathname}${loc.search}`);
}

// auth.js asks this once: was the reload we are in one of ours?
export function consumeRouteNavigation() {
    try {
        const flagged = sessionStorage.getItem(ROUTE_NAV_FLAG) === '1';
        sessionStorage.removeItem(ROUTE_NAV_FLAG);
        return flagged;
    } catch (_) {
        return false;
    }
}

function installBrowserHooks() {
    if (typeof window === 'undefined' || window.fluencyRoutes) return;
    const route = adoptLegacyUrl();
    window.fluencyRoute = route;
    window.fluencyRoutes = {
        parseRoute, formatRoute, legacyRoute, languageKeyFor, routeCodeFor,
        routeHref, goToRoute, replaceRoute, clearRoute, consumeRouteNavigation
    };
    // Someone edited the fragment of an open tab, or pasted a link into it.
    window.addEventListener('hashchange', () => {
        try { sessionStorage.setItem(ROUTE_NAV_FLAG, '1'); } catch (_) {}
        window.location.reload();
    });
}

if (typeof window !== 'undefined' && typeof history !== 'undefined') installBrowserHooks();
