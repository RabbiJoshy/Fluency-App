// Naive live-playlist deck: tokenise lyrics in the browser, join them to the
// speech inventory, and study those cards with unassigned song-line examples.
const LIVE_DB_NAME = 'fluency-playlist-lyrics';
const LIVE_DB_VERSION = 2;
const DECK_STORE = 'decks';
const LIVE_DECK_ID = 'live';
const MAX_LINES_PER_SURFACE = 5;

let _liveDeck = null;

function normalizeSurface(value) {
    return String(value || '').normalize('NFC').toLowerCase().trim();
}

function naiveLyricTokens(text) {
    const cleaned = String(text || '').replace(/\[[^\]]*\]/g, ' ');
    const matches = cleaned.match(/[\p{L}\p{N}]+(?:['’-][\p{L}\p{N}]+)*/gu) || [];
    return matches.map(token => normalizeSurface(token.replace(/’/g, "'")));
}

function lyricLines(text) {
    return String(text || '')
        .split(/\r?\n/)
        .map(line => line.replace(/\[[^\]]*\]/g, '').trim())
        .filter(line => line && !/^\d+:\d{2}/.test(line));
}

function openLiveDb() {
    return new Promise((resolve, reject) => {
        if (!('indexedDB' in window)) {
            reject(new Error('IndexedDB unavailable'));
            return;
        }
        const request = indexedDB.open(LIVE_DB_NAME, LIVE_DB_VERSION);
        request.onupgradeneeded = () => {
            const db = request.result;
            if (!db.objectStoreNames.contains('tracks')) {
                db.createObjectStore('tracks', { keyPath: 'spotifyId' });
            }
            if (!db.objectStoreNames.contains('imports')) {
                db.createObjectStore('imports', { keyPath: 'id' });
            }
            if (!db.objectStoreNames.contains(DECK_STORE)) {
                db.createObjectStore(DECK_STORE, { keyPath: 'id' });
            }
        };
        request.onsuccess = () => resolve(request.result);
        request.onerror = () => reject(request.error);
    });
}

function idbRequest(request) {
    return new Promise((resolve, reject) => {
        request.onsuccess = () => resolve(request.result);
        request.onerror = () => reject(request.error);
    });
}

async function loadSpeechSurfaces(language) {
    const cfg = window._normalModeLangConfigs?.[language];
    if (!cfg) throw new Error(`No speech vocabulary is configured for ${language}.`);
    const indexPath = cfg.indexPath || cfg.dataPath;
    if (!indexPath) throw new Error(`No speech index for ${language}.`);
    const directory = indexPath.slice(0, indexPath.lastIndexOf('/') + 1);
    const words = new Set();
    try {
        const manifestResp = await fetch(`${directory}vocabulary.index.manifest.json`);
        if (manifestResp.ok) {
            const manifest = await manifestResp.json();
            if (manifest?.columns) {
                const columnsResp = await fetch(`${directory}${manifest.columns}`);
                if (!columnsResp.ok) throw new Error(`Speech columns HTTP ${columnsResp.status}`);
                const columns = await columnsResp.json();
                for (const word of columns.word || []) {
                    const key = normalizeSurface(word);
                    if (key) words.add(key);
                }
                if (words.size) return words;
            }
        }
    } catch (error) {
        console.warn('Columnar speech index unavailable, using monolith:', error);
    }
    const response = await fetch(indexPath);
    if (!response.ok) throw new Error(`Speech index HTTP ${response.status}`);
    const data = await response.json();
    for (const item of data) {
        const key = normalizeSurface(item.word);
        if (key) words.add(key);
    }
    return words;
}

async function buildPlaylistLiveDeck({ playlist, language, records }) {
    const speechSurfaces = await loadSpeechSurfaces(language);
    const surfaces = new Map();
    let tokenCount = 0;
    let lyricsTrackCount = 0;

    for (const record of records || []) {
        const lyrics = (record.plainLyrics || record.syncedLyrics || '').trim();
        if (!lyrics || record.status === 'instrumental' || record.status === 'miss' || record.status === 'error') {
            continue;
        }
        lyricsTrackCount += 1;
        const title = record.title || 'Unknown track';
        const artist = record.artist || '';
        for (const line of lyricLines(lyrics)) {
            const tokens = naiveLyricTokens(line);
            tokenCount += tokens.length;
            for (const token of tokens) {
                if (!speechSurfaces.has(token)) continue;
                let entry = surfaces.get(token);
                if (!entry) {
                    entry = { count: 0, lines: [] };
                    surfaces.set(token, entry);
                }
                entry.count += 1;
                if (entry.lines.length < MAX_LINES_PER_SURFACE
                    && !entry.lines.some(existing => existing.text === line)) {
                    entry.lines.push({ text: line, song: title, artist });
                }
            }
        }
    }

    const deck = {
        id: LIVE_DECK_ID,
        playlistId: playlist.id,
        playlistName: playlist.name,
        language,
        builtAt: new Date().toISOString(),
        trackCount: (records || []).length,
        lyricsTrackCount,
        tokenCount,
        matchedCount: surfaces.size,
        surfaces: Object.fromEntries(surfaces)
    };
    const db = await openLiveDb();
    try {
        await idbRequest(db.transaction(DECK_STORE, 'readwrite').objectStore(DECK_STORE).put(deck));
    } finally {
        db.close();
    }
    _liveDeck = deck;
    return deck;
}

async function savePlaylistLiveDeckToServer(deck) {
    if (!deck) return { ok: false, skipped: true };
    if (typeof window.postPlaylistLive === 'function') {
        return window.postPlaylistLive('savePlaylistLiveDeck', {
            language: deck.language,
            playlistId: deck.playlistId,
            playlistName: deck.playlistName,
            deck
        });
    }
    return { ok: false, skipped: true };
}

async function loadPlaylistLiveDeckFromServer(language) {
    const user = window.currentUser;
    if (!window.GOOGLE_SCRIPT_URL || !user || user.isGuest || !language) return null;
    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), 20000);
    try {
        const response = await fetch(window.GOOGLE_SCRIPT_URL, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                action: 'loadPlaylistLiveDeck',
                user: user.initials,
                language
            }),
            signal: controller.signal
        });
        const json = await response.json().catch(() => null);
        if (!response.ok || json?.success !== true) return null;
        return json.data?.deck || null;
    } catch (_) {
        return null;
    } finally {
        clearTimeout(timeout);
    }
}

async function cacheLiveDeck(deck) {
    if (!deck) return;
    const db = await openLiveDb();
    try {
        await idbRequest(db.transaction(DECK_STORE, 'readwrite').objectStore(DECK_STORE).put({
            ...deck,
            id: LIVE_DECK_ID
        }));
    } finally {
        db.close();
    }
    _liveDeck = { ...deck, id: LIVE_DECK_ID };
}

async function preparePlaylistLiveSession(language) {
    const db = await openLiveDb();
    try {
        const deck = await idbRequest(db.transaction(DECK_STORE, 'readonly').objectStore(DECK_STORE).get(LIVE_DECK_ID));
        if (deck && (!language || deck.language === language)) {
            _liveDeck = deck;
            return deck;
        }
    } finally {
        db.close();
    }
    const remote = await loadPlaylistLiveDeckFromServer(language);
    if (remote && (!language || remote.language === language) && remote.matchedCount) {
        await cacheLiveDeck(remote);
        return _liveDeck;
    }
    _liveDeck = null;
    return null;
}

function playlistLiveDeck() {
    return _liveDeck;
}

function playlistLiveActive() {
    return Boolean(_liveDeck?.matchedCount);
}

function senseShare(meaning) {
    const raw = Number(meaning?.display_frequency ?? meaning?.frequency ?? meaning?.percentage);
    if (!Number.isFinite(raw)) return 0;
    return raw > 1 ? raw / 100 : raw;
}

function keepCommonOrUncommon(meaning) {
    if (!meaning || meaning.unassigned || meaning.isRareSense) return false;
    if (String(meaning.prominenceLabel || '').toLowerCase() === 'rare') return false;
    const share = senseShare(meaning);
    if (share > 0) return share >= 0.05;
    return true;
}

function lyricExample(line) {
    return {
        target: line.text,
        spanish: line.text,
        english: '',
        song: line.song || '',
        song_name: line.artist ? `${line.song} — ${line.artist}` : (line.song || ''),
        artist: line.artist || '',
        unassigned: true
    };
}

function applyPlaylistLiveVocabulary(items) {
    if (!playlistLiveActive() || !Array.isArray(items)) return items;
    const ranked = [];
    for (const item of items) {
        const entry = _liveDeck.surfaces[normalizeSurface(item.word)];
        if (!entry) continue;
        const lyricExamples = entry.lines.map(lyricExample);
        const next = { ...item, meanings: [...(item.meanings || [])], playlist_count: entry.count };
        const kept = next.meanings.filter(keepCommonOrUncommon);
        const meanings = kept.length ? kept : next.meanings.slice(0, 4);
        if (meanings.length) {
            next.meanings = meanings.map((m, idx) => ({
                ...m,
                examples: idx === 0
                    ? [...lyricExamples, ...(m.examples || [])]
                    : (m.examples || [])
            }));
        } else {
            next.meanings = [{
                pos: '',
                translation: '',
                frequency: '0',
                unassigned: true,
                assignment_method: 'unassigned',
                examples: lyricExamples
            }];
        }
        ranked.push(next);
    }
    ranked.sort((a, b) => (b.playlist_count || 0) - (a.playlist_count || 0)
        || String(a.word || '').localeCompare(String(b.word || '')));
    ranked.forEach((item, index) => {
        const rank = index + 1;
        item.rank = rank;
        item.displayRank = rank;
        item.stableRank = rank;
        item.categoryRank = rank;
    });
    return ranked;
}

function clearPlaylistLiveSession() {
    _liveDeck = null;
    document.body.classList.remove('playlist-live-mode');
    window.invalidatePreparedSetupVocabulary?.();
}

window.normalizePlaylistSurface = normalizeSurface;
window.naiveLyricTokens = naiveLyricTokens;
window.buildPlaylistLiveDeck = buildPlaylistLiveDeck;
window.preparePlaylistLiveSession = preparePlaylistLiveSession;
window.savePlaylistLiveDeckToServer = savePlaylistLiveDeckToServer;
window.playlistLiveDeck = playlistLiveDeck;
window.playlistLiveActive = playlistLiveActive;
window.applyPlaylistLiveVocabulary = applyPlaylistLiveVocabulary;
window.clearPlaylistLiveSession = clearPlaylistLiveSession;
window.FLUENCY_PLAYLIST_LIVE_DECK_ID = LIVE_DECK_ID;
