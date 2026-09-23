// Live playlist: look up lyrics on LRCLIB (six at a time), land each song in
// the progress list, save tracks to Fluency, then build a study deck from
// speech-inventory tokens plus unassigned song-line examples.
import './state.js?v=20260825ak';
import { combineSongCatalogs } from './song-sets-core.js?v=20260825ak';
import { goToRoute, replaceRoute, routeCodeFor } from './routes.js?v=20260921a';

const CUSTOM_SONG_SET_KEY = 'fluency_song_set_v1:custom';
const LYRICS_DB_NAME = 'fluency-playlist-lyrics';
const LYRICS_DB_VERSION = 2;
const TRACK_STORE = 'tracks';
const IMPORT_STORE = 'imports';
const DECK_STORE = 'decks';
const LRCLIB_SEARCH = 'https://lrclib.net/api/search';
const LRCLIB_CLIENT = 'Fluency playlist-import/0.1 (https://github.com/RabbiJoshy/Fluency-App)';
const LOOKUP_CONCURRENCY = 6;
const SPOTIFY_MODULE = './spotify.js?v=20260923sp';
const DISMISS_LOCK_MS = 1500;

let _matchState = null;
let _liveState = null;
let _importAbort = null;
let _importMode = 'filter';
let _importBusy = false;
let _ignoreBackdropUntil = 0;

function element(id) {
    return document.getElementById(id);
}

function songLabel(track) {
    return track.artist ? `${track.title} — ${track.artist}` : track.title;
}

async function fetchSongCatalog(path) {
    const response = await fetch(path);
    if (!response.ok) throw new Error(`Song catalog HTTP ${response.status}`);
    return response.json();
}

function customSourceEligible(cfg) {
    return Boolean(cfg?.songsPath && (cfg?.indexPath || cfg?.dataPath));
}

async function buildLanguageCatalog(matchingArtists) {
    const sources = await Promise.all(
        Object.entries(matchingArtists || {})
            .filter(([, cfg]) => customSourceEligible(cfg))
            .map(async ([slug, cfg]) => ({
                slug,
                name: cfg.name,
                catalog: await fetchSongCatalog(cfg.songsPath)
            }))
    );
    return combineSongCatalogs(sources);
}

function artistSlugsForMatches(catalog, matchedIds) {
    const selected = new Set(matchedIds.map(String));
    const slugs = new Set();
    for (const song of catalog.songs) {
        if (!selected.has(String(song.id))) continue;
        for (const sourceKey of song.sourceKeys || []) {
            const separator = String(sourceKey).indexOf(':');
            if (separator > 0) slugs.add(String(sourceKey).slice(0, separator));
        }
    }
    return Array.from(slugs).sort();
}

function openLyricsDb() {
    return new Promise((resolve, reject) => {
        if (!('indexedDB' in window)) {
            reject(new Error('IndexedDB unavailable'));
            return;
        }
        const request = indexedDB.open(LYRICS_DB_NAME, LYRICS_DB_VERSION);
        request.onupgradeneeded = () => {
            const db = request.result;
            if (!db.objectStoreNames.contains(TRACK_STORE)) {
                db.createObjectStore(TRACK_STORE, { keyPath: 'spotifyId' });
            }
            if (!db.objectStoreNames.contains(IMPORT_STORE)) {
                db.createObjectStore(IMPORT_STORE, { keyPath: 'id' });
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

async function getCachedLyrics(db, spotifyId) {
    return idbRequest(db.transaction(TRACK_STORE, 'readonly').objectStore(TRACK_STORE).get(spotifyId));
}

async function putCachedLyrics(db, record) {
    return idbRequest(db.transaction(TRACK_STORE, 'readwrite').objectStore(TRACK_STORE).put(record));
}

async function putImportSummary(db, record) {
    return idbRequest(db.transaction(IMPORT_STORE, 'readwrite').objectStore(IMPORT_STORE).put(record));
}

function pickLyricsRecord(records, durationSec) {
    if (!Array.isArray(records) || !records.length) return null;
    const usable = records.filter(record => record && (record.instrumental
        || (record.plainLyrics || '').trim()
        || (record.syncedLyrics || '').trim()));
    if (!usable.length) return null;
    if (durationSec != null) {
        const close = usable.find(record => Math.abs(Number(record.duration) - durationSec) <= 2);
        if (close) return close;
    }
    return usable.find(record => (record.plainLyrics || '').trim() || (record.syncedLyrics || '').trim())
        || usable[0];
}

function classifyRecord(record) {
    if (!record) return 'miss';
    if (record.instrumental && !(record.plainLyrics || '').trim() && !(record.syncedLyrics || '').trim()) {
        return 'instrumental';
    }
    if ((record.plainLyrics || '').trim() || (record.syncedLyrics || '').trim()) return 'lyrics';
    return 'miss';
}

async function searchLrclib(track, signal) {
    const params = new URLSearchParams({
        track_name: track.title,
        artist_name: track.artist.split(',')[0].trim() || track.artist
    });
    const response = await fetch(`${LRCLIB_SEARCH}?${params}`, {
        signal,
        headers: { 'Lrclib-Client': LRCLIB_CLIENT }
    });
    if (!response.ok) throw new Error(`LRCLIB HTTP ${response.status}`);
    return response.json();
}

function resetProgressUi({ keepVisible = false } = {}) {
    const progress = element('spotifyPlaylistProgress');
    const log = element('spotifyPlaylistLog');
    progress?.classList.toggle('hidden', !keepVisible);
    progress?.classList.remove('is-complete');
    if (log) log.replaceChildren();
    renderProgress(0, 0, []);
}

function setDismissLock(ms = DISMISS_LOCK_MS) {
    _ignoreBackdropUntil = Date.now() + ms;
    const modal = element('spotifyPlaylistModal');
    modal?.classList.add('is-dismiss-locked');
    const cancel = element('cancelSpotifyPlaylistBtn');
    const close = element('closeSpotifyPlaylistModal');
    if (cancel) cancel.disabled = true;
    if (close) close.disabled = true;
    window.clearTimeout(setDismissLock._timer);
    setDismissLock._timer = window.setTimeout(() => {
        modal?.classList.remove('is-dismiss-locked');
        if (cancel) cancel.disabled = false;
        if (close) close.disabled = false;
    }, ms);
}

function setImportBusy(busy) {
    _importBusy = Boolean(busy);
    element('spotifyPlaylistModal')?.classList.toggle('is-importing', _importBusy);
}

function renderProgress(done, total, activeLabels) {
    const percent = total ? Math.round((100 * done) / total) : 0;
    const percentEl = element('spotifyPlaylistPercent');
    const countEl = element('spotifyPlaylistCount');
    const bar = element('spotifyPlaylistBar');
    const fill = element('spotifyPlaylistBarFill');
    const nowEl = element('spotifyPlaylistNow');
    const progress = element('spotifyPlaylistProgress');
    if (percentEl) percentEl.textContent = `${percent}%`;
    if (countEl) countEl.textContent = total ? `${done} of ${total} songs` : '0 of 0 songs';
    if (bar) {
        bar.setAttribute('aria-valuenow', String(percent));
        bar.setAttribute('aria-valuemax', '100');
    }
    if (fill) fill.style.width = `${percent}%`;
    progress?.classList.toggle('is-complete', Boolean(total) && done === total);
    if (nowEl) {
        nowEl.textContent = activeLabels.length
            ? `Looking up: ${activeLabels.join(' · ')}`
            : (done && done === total ? 'Lookup complete.' : 'Waiting…');
    }
}

function namedSyncUser() {
    const user = window.currentUser;
    return user && !user.isGuest ? user.initials : '';
}

async function postJson(url, payload, { ignoreHttpErrors = false } = {}) {
    if (!url) return { ok: false, skipped: true };
    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), 20000);
    try {
        const response = await fetch(url, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload),
            signal: controller.signal
        });
        if (ignoreHttpErrors && (response.status === 404 || response.status === 405)) {
            return { ok: false, skipped: true };
        }
        let json;
        try { json = await response.json(); } catch (_) {
            throw new Error(`Ambiguous response (HTTP ${response.status})`);
        }
        if (!response.ok || json?.success !== true) {
            throw new Error(json?.message || `Server save failed (HTTP ${response.status})`);
        }
        return { ok: true, data: json.data };
    } finally {
        clearTimeout(timeout);
    }
}

async function postPlaylistLive(action, body) {
    const payload = {
        action,
        user: namedSyncUser() || 'anonymous',
        ...body
    };
    let remote = { ok: false, skipped: true };
    if (namedSyncUser() && window.GOOGLE_SCRIPT_URL) {
        try {
            remote = await postJson(window.GOOGLE_SCRIPT_URL, payload);
        } catch (error) {
            remote = { ok: false, error };
        }
    }
    let local = { ok: false, skipped: true };
    try {
        local = await postJson('/api/playlist-live', payload, { ignoreHttpErrors: true });
    } catch (error) {
        console.warn('Local playlist dump failed:', error);
    }
    if (remote.ok || local.ok) return { ok: true, remote: remote.ok, local: local.ok };
    if (remote.error) throw remote.error;
    return { ok: false, skipped: true };
}

function logStatusLabel(status) {
    return ({
        lyrics: 'lyrics',
        instrumental: 'instrumental',
        miss: 'no lyrics',
        error: 'error',
        cached: 'cached',
        saving: 'saving',
        saved: 'saved'
    })[status] || status;
}

function appendLogRow(track, status) {
    const log = element('spotifyPlaylistLog');
    if (!log) return null;
    const existing = log.querySelector(`[data-spotify-id="${CSS.escape(track.id)}"]`);
    if (existing) {
        setLogStatus(track, status);
        return existing;
    }
    const row = document.createElement('li');
    row.className = `playlist-lyrics-log-row is-${status}`;
    row.dataset.spotifyId = track.id;
    const name = document.createElement('span');
    name.className = 'playlist-lyrics-log-name';
    name.textContent = songLabel(track);
    const mark = document.createElement('span');
    mark.className = 'playlist-lyrics-log-status';
    mark.textContent = logStatusLabel(status);
    row.append(name, mark);
    log.prepend(row);
    return row;
}

function setLogStatus(track, status) {
    const log = element('spotifyPlaylistLog');
    const row = log?.querySelector(`[data-spotify-id="${CSS.escape(track.id)}"]`);
    if (!row) return appendLogRow(track, status);
    row.className = `playlist-lyrics-log-row is-${status}`;
    const mark = row.querySelector('.playlist-lyrics-log-status');
    if (mark) mark.textContent = logStatusLabel(status);
    return row;
}

async function lookupTrack(db, track, playlist, signal) {
    const cached = await getCachedLyrics(db, track.id).catch(() => null);
    if (cached?.status && cached.status !== 'error') {
        return { ...cached, fromCache: true };
    }
    const durationSec = track.durationMs ? Math.round(track.durationMs / 1000) : null;
    const records = await searchLrclib(track, signal);
    const picked = pickLyricsRecord(records, durationSec);
    const status = classifyRecord(picked);
    const record = {
        spotifyId: track.id,
        title: track.title,
        artist: track.artist,
        album: track.album,
        durationMs: track.durationMs,
        playlistId: playlist.id,
        playlistName: playlist.name,
        status,
        plainLyrics: (picked?.plainLyrics || '').trim(),
        syncedLyrics: (picked?.syncedLyrics || '').trim(),
        lrclibId: picked?.id ?? null,
        source: 'lrclib',
        fetchedAt: new Date().toISOString()
    };
    await putCachedLyrics(db, record).catch(() => {});
    return record;
}

async function mapPool(items, limit, worker, signal) {
    const results = new Array(items.length);
    let next = 0;
    async function run() {
        while (next < items.length) {
            if (signal?.aborted) throw new DOMException('Aborted', 'AbortError');
            const index = next++;
            results[index] = await worker(items[index], index);
        }
    }
    const workers = Array.from({ length: Math.min(limit, items.length) }, run);
    await Promise.all(workers);
    return results;
}

async function lookupPlaylistLyrics(playlist, tracks, signal, language) {
    const progress = element('spotifyPlaylistProgress');
    progress?.classList.remove('hidden');
    const db = await openLyricsDb();
    const active = new Map();
    let done = 0;
    const counts = { lyrics: 0, instrumental: 0, miss: 0, error: 0, cached: 0 };
    renderProgress(0, tracks.length, []);

    try {
        const results = await mapPool(tracks, LOOKUP_CONCURRENCY, async track => {
            active.set(track.id, songLabel(track));
            renderProgress(done, tracks.length, [...active.values()]);
            let record;
            try {
                record = await lookupTrack(db, track, playlist, signal);
            } catch (error) {
                if (error?.name === 'AbortError') throw error;
                record = {
                    spotifyId: track.id,
                    title: track.title,
                    artist: track.artist,
                    status: 'error',
                    error: error?.message || 'lookup failed',
                    fetchedAt: new Date().toISOString()
                };
            }
            active.delete(track.id);
            done += 1;
            if (record.fromCache) counts.cached += 1;
            counts[record.status] = (counts[record.status] || 0) + 1;
            appendLogRow(track, record.fromCache ? 'cached' : record.status);
            if (_importMode === 'live') {
                setLogStatus(track, 'saving');
                try {
                    const saved = await postPlaylistLive('savePlaylistLiveTracks', {
                        language,
                        playlistId: playlist.id,
                        playlistName: playlist.name,
                        records: [record]
                    });
                    setLogStatus(track, saved.ok ? 'saved' : (record.fromCache ? 'cached' : record.status));
                } catch (error) {
                    console.warn('Playlist track save failed:', error);
                    setLogStatus(track, record.fromCache ? 'cached' : record.status);
                }
            }
            renderProgress(done, tracks.length, [...active.values()]);
            return record;
        }, signal);

        const lyricsCount = counts.lyrics;
        await putImportSummary(db, {
            id: playlist.id,
            playlistName: playlist.name,
            importedAt: new Date().toISOString(),
            trackCount: tracks.length,
            lyricsCount,
            instrumentalCount: counts.instrumental,
            missCount: counts.miss,
            errorCount: counts.error,
            cachedCount: counts.cached
        }).catch(() => {});

        return { results, counts, lyricsCount };
    } finally {
        db.close();
    }
}

function renderPlaylistList(playlists, onSelect) {
    const list = element('spotifyPlaylistList');
    list.replaceChildren();
    if (!playlists.length) return;
    const fragment = document.createDocumentFragment();
    for (const playlist of playlists) {
        const button = document.createElement('button');
        button.type = 'button';
        button.className = 'song-set-option spotify-playlist-option';
        const copy = document.createElement('span');
        const title = document.createElement('strong');
        title.textContent = playlist.name;
        copy.appendChild(title);
        const small = document.createElement('small');
        if (playlist.canReadItems === false) {
            button.disabled = true;
            button.classList.add('is-disabled');
            small.textContent = 'Followed or Spotify mix — songs are hidden';
        } else {
            small.textContent = `${playlist.trackCount} track${playlist.trackCount === 1 ? '' : 's'}`;
        }
        copy.appendChild(small);
        button.appendChild(copy);
        button.addEventListener('click', event => {
            event.preventDefault();
            event.stopPropagation();
            onSelect(playlist, button);
        });
        fragment.appendChild(button);
    }
    list.appendChild(fragment);
}

async function ensureSpotifyModule() {
    if (!window.isSpotifyConnected) {
        await import(SPOTIFY_MODULE).catch(error => {
            console.warn('Spotify controls deferred:', error);
        });
    }
}

async function openSpotifyPlaylistImport(matchingArtists, language, options = {}) {
    const modal = element('spotifyPlaylistModal');
    const status = element('spotifyPlaylistStatus');
    const useBtn = element('useSpotifyMatchesBtn');
    const liveBtn = element('useSpotifyLiveBtn');
    if (!modal || !status || !useBtn) return;

    document.getElementById('lyricsSourceSheet')?.remove();
    _importMode = options.live ? 'live' : 'filter';
    _matchState = null;
    _liveState = null;
    _importAbort?.abort();
    _importAbort = null;
    useBtn.hidden = true;
    if (liveBtn) liveBtn.hidden = true;
    const reconnect = element('reconnectSpotifyPlaylistBtn');
    if (reconnect) reconnect.hidden = true;
    setImportBusy(false);
    _ignoreBackdropUntil = Date.now() + 600;
    resetProgressUi();
    const title = element('spotifyPlaylistTitle');
    const intro = element('spotifyPlaylistIntro');
    if (title) title.textContent = _importMode === 'live' ? 'Live playlist' : 'Match a Spotify playlist';
    if (intro) {
        intro.textContent = _importMode === 'live'
            ? 'Choose a playlist you created. Spotify no longer lets apps read mixes or playlists you only follow. Fluency then looks up lyrics, saves each song to your Fluency account, and builds a study deck.'
            : 'Choose a playlist you created. Fluency keeps only the songs already in the published lyrics library.';
    }
    element('spotifyPlaylistList').replaceChildren();
    element('spotifyPlaylistList').classList.remove('hidden');
    modal.classList.remove('hidden');
    status.textContent = 'Connecting to Spotify…';

    await ensureSpotifyModule();
    if (!window.isSpotifyConnected) {
        status.textContent = 'Spotify sign-in is temporarily unavailable. Please reload the app and try again.';
        return;
    }

    if (!window.isSpotifyConnected?.()) {
        const connected = await window.spotifyLogin?.();
        if (!connected) {
            status.textContent = 'Could not connect to Spotify.';
            return;
        }
    }

    status.textContent = 'Loading your playlists…';
    let playlists;
    try {
        playlists = await window.fetchSpotifyPlaylists();
    } catch (error) {
        status.textContent = error?.message || 'Could not load your playlists.';
        return;
    }
    status.textContent = playlists.length
        ? (_importMode === 'live' ? 'Choose a playlist you created.' : 'Choose a playlist you created to match.')
        : 'No playlists found on this Spotify account.';
    if (playlists.length && playlists.every(playlist => playlist.canReadItems === false)) {
        status.textContent = 'Spotify listed playlists, but none are ones you own. Create a playlist in Spotify, then try again.';
    }

    renderPlaylistList(playlists, async (playlist, button) => {
        _importAbort?.abort();
        const abort = new AbortController();
        _importAbort = abort;
        _matchState = null;
        _liveState = null;
        useBtn.hidden = true;
        if (liveBtn) liveBtn.hidden = true;
        const reconnect = element('reconnectSpotifyPlaylistBtn');
        if (reconnect) reconnect.hidden = true;
        setImportBusy(true);
        setDismissLock();
        button.disabled = true;
        status.textContent = `Loading tracks from "${playlist.name}"…`;
        try {
            if (_importMode === 'filter') {
                const [catalog, trackIds] = await Promise.all([
                    buildLanguageCatalog(matchingArtists),
                    window.fetchSpotifyPlaylistTrackIds(playlist.id, {
                        tracksHref: playlist.tracksHref,
                        canReadItems: playlist.canReadItems
                    })
                ]);
                if (abort.signal.aborted) return;
                element('spotifyPlaylistList').classList.add('hidden');
                const matches = catalog.songs.filter(song => song.spotifyTrackId && trackIds.has(song.spotifyTrackId));
                if (!matches.length) {
                    element('spotifyPlaylistList').classList.remove('hidden');
                    status.textContent = `None of "${playlist.name}"'s tracks are in Fluency's library yet.`;
                    return;
                }
                _matchState = {
                    language,
                    playlistName: playlist.name,
                    songIds: matches.map(song => String(song.id)),
                    artistSlugs: artistSlugsForMatches(catalog, matches.map(song => song.id))
                };
                status.textContent = `${matches.length} of ${trackIds.size} tracks matched your library.`;
                useBtn.hidden = false;
                return;
            }

            const tracks = await window.fetchSpotifyPlaylistTracks(playlist.id, {
                tracksHref: playlist.tracksHref,
                canReadItems: playlist.canReadItems
            });
            if (abort.signal.aborted) return;
            if (!tracks.length) {
                status.textContent = `"${playlist.name}" has no playable Spotify tracks.`;
                return;
            }
            element('spotifyPlaylistList').classList.add('hidden');
            resetProgressUi({ keepVisible: true });
            const nowEl = element('spotifyPlaylistNow');
            if (nowEl) nowEl.textContent = `Looking up lyrics for ${tracks.length} songs…`;
            status.textContent = `Looking up lyrics for ${tracks.length} songs…`;
            const { counts, lyricsCount, results } = await lookupPlaylistLyrics(playlist, tracks, abort.signal, language);
            if (abort.signal.aborted) return;
            status.textContent = `Building your deck from ${lyricsCount} songs…`;
            const deck = await window.buildPlaylistLiveDeck({
                playlist,
                language,
                records: results
            });
            if (abort.signal.aborted) return;
            const missCount = counts.miss + counts.error;
            const parts = [
                `${lyricsCount} of ${tracks.length} had lyrics`,
                counts.instrumental ? `${counts.instrumental} instrumental` : '',
                missCount ? `${missCount} with no lyrics` : '',
                `${deck.matchedCount} speech-deck words from ${deck.tokenCount} tokens`
            ].filter(Boolean);
            if (!deck.matchedCount) {
                status.textContent = `${parts.join('. ')}. None of those tokens are in the speech deck.`;
                return;
            }
            _liveState = { language, playlistName: playlist.name, matchedCount: deck.matchedCount };
            status.textContent = `${parts.join('. ')}. Saving the deck to Fluency…`;
            try {
                const saved = await window.savePlaylistLiveDeckToServer?.(deck);
                if (saved?.ok) {
                    status.textContent = `${parts.join('. ')}. Saved to Fluency. Opening study…`;
                } else if (namedSyncUser()) {
                    status.textContent = `${parts.join('. ')}. Deck is ready here, but Fluency did not keep a copy.`;
                } else {
                    status.textContent = `${parts.join('. ')}. Sign in with initials to keep this deck on Fluency.`;
                }
            } catch (error) {
                console.warn('Playlist deck save failed:', error);
                status.textContent = `${parts.join('. ')}. Deck is ready here, but Fluency did not keep a copy.`;
            }
            if (liveBtn) liveBtn.hidden = false;
            confirmSpotifyLiveDeck();
        } catch (error) {
            if (error?.name === 'AbortError') return;
            setImportBusy(false);
            element('spotifyPlaylistList').classList.remove('hidden');
            element('spotifyPlaylistProgress')?.classList.add('hidden');
            status.textContent = error?.message || 'Could not look up that playlist.';
            const blocked = /403|blocked|scope|forbidden|only shares songs/i.test(error?.message || '');
            if (blocked) {
                status.textContent = `${error.message} Reconnect only helps if Spotify never showed the playlist list.`;
            }
            const reconnect = element('reconnectSpotifyPlaylistBtn');
            if (reconnect) reconnect.hidden = !blocked;
        } finally {
            if (!element('spotifyPlaylistModal')?.classList.contains('hidden') && !_liveState) {
                setImportBusy(false);
            }
            button.disabled = false;
        }
    });
}

function closeSpotifyPlaylistImport() {
    if (Date.now() < _ignoreBackdropUntil) return;
    _importAbort?.abort();
    _importAbort = null;
    setImportBusy(false);
    element('cancelSpotifyPlaylistBtn') && (element('cancelSpotifyPlaylistBtn').disabled = false);
    element('closeSpotifyPlaylistModal') && (element('closeSpotifyPlaylistModal').disabled = false);
    element('spotifyPlaylistModal')?.classList.add('hidden');
    _matchState = null;
    _liveState = null;
}

function activatePlaylistLiveStudy(language) {
    const deck = window.playlistLiveDeck?.();
    if (!deck?.matchedCount || !language) return;
    document.body.classList.add('playlist-live-mode');
    const sourceName = document.getElementById('selectedSourceInline');
    if (sourceName && deck.playlistName) {
        sourceName.textContent = `Live · ${deck.playlistName}`;
    }
    replaceRoute({
        kind: 'live',
        language: routeCodeFor(language, typeof config !== 'undefined' ? config?.languages : null)
    });
    window.showAppLoading?.('Opening your live deck', `${deck.playlistName} · ${deck.matchedCount} words`);
    sessionStorage.setItem('fluencyPendingSpeechLanguage', language);
    sessionStorage.setItem('fluencyPendingLiveStudy', '1');
    window.invalidatePreparedSetupVocabulary?.();
    window.invalidateLyricsSourceCaches?.(language);
    window.resetActiveArtist?.();
    const liveTab = document.querySelector(`.lang-tab[data-lang="${CSS.escape(language)}"]`);
    if (liveTab && !liveTab.disabled) {
        liveTab.click();
    } else if (window.continueToSpeechAfterLive) {
        window.continueToSpeechAfterLive();
    } else {
        window.hideAppLoading?.();
    }
}

function confirmSpotifyLiveDeck() {
    if (!_liveState) return;
    const language = _liveState.language;
    setImportBusy(false);
    element('spotifyPlaylistModal')?.classList.add('hidden');
    _importAbort = null;
    activatePlaylistLiveStudy(language);
}

function confirmSpotifyMatches() {
    if (!_matchState) return;
    window.clearPlaylistLiveSession?.();
    const record = {
        songIds: _matchState.songIds,
        artistSlugs: _matchState.artistSlugs,
        updatedAt: new Date().toISOString()
    };
    try {
        localStorage.setItem(CUSTOM_SONG_SET_KEY, JSON.stringify(record));
    } catch (_) {}
    window.showAppLoading?.('Building your deck', `Matching ${_matchState.playlistName}…`, true);
    goToRoute({
        kind: 'songs',
        language: routeCodeFor(_matchState.language, typeof config !== 'undefined' ? config?.languages : null)
    });
}

async function reconnectSpotifyForPlaylist() {
    const status = element('spotifyPlaylistStatus');
    const reconnect = element('reconnectSpotifyPlaylistBtn');
    if (reconnect) reconnect.hidden = true;
    if (status) status.textContent = 'Reconnecting Spotify…';
    const connected = await window.spotifyLogin?.(null, 0, null, { showDialog: true });
    if (status) {
        status.textContent = connected
            ? 'Spotify reconnected. Tap the playlist again.'
            : 'Spotify reconnect cancelled.';
    }
    if (reconnect) reconnect.hidden = Boolean(connected);
}

function setupSpotifyPlaylistImport() {
    const modal = element('spotifyPlaylistModal');
    if (!modal || modal.dataset.listenersReady === '1') return;
    modal.dataset.listenersReady = '1';
    element('closeSpotifyPlaylistModal')?.addEventListener('click', closeSpotifyPlaylistImport);
    element('cancelSpotifyPlaylistBtn')?.addEventListener('click', closeSpotifyPlaylistImport);
    element('reconnectSpotifyPlaylistBtn')?.addEventListener('click', reconnectSpotifyForPlaylist);
    element('useSpotifyMatchesBtn')?.addEventListener('click', confirmSpotifyMatches);
    element('useSpotifyLiveBtn')?.addEventListener('click', confirmSpotifyLiveDeck);
    modal.addEventListener('click', event => {
        if (event.target !== modal) return;
        if (_importBusy || Date.now() < _ignoreBackdropUntil) return;
        closeSpotifyPlaylistImport();
    });
    document.addEventListener('keydown', event => {
        if (event.key !== 'Escape' || modal.classList.contains('hidden')) return;
        if (_importBusy || Date.now() < _ignoreBackdropUntil) return;
        closeSpotifyPlaylistImport();
    });
}

setupSpotifyPlaylistImport();

window.postPlaylistLive = postPlaylistLive;
window.openSpotifyPlaylistImport = openSpotifyPlaylistImport;
window.FLUENCY_PLAYLIST_LYRICS_DB = LYRICS_DB_NAME;
window.FLUENCY_PLAYLIST_LYRICS_CONCURRENCY = LOOKUP_CONCURRENCY;
