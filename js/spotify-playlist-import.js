// "Import a Spotify playlist" — pick one of the user's playlists, match its
// tracks against songs Fluency already has lyrics/vocabulary for (by Spotify
// track ID, the same id each song catalog entry already carries), and land
// on the "Choose your own" custom-source flow with just those songs selected.
import './state.js?v=20260825ak';
import { combineSongCatalogs } from './song-sets-core.js?v=20260825ak';

const CUSTOM_SONG_SET_KEY = 'fluency_song_set_v1:custom';

let _matchState = null;

function element(id) {
    return document.getElementById(id);
}

async function fetchSongCatalog(path) {
    const response = await fetch(path);
    if (!response.ok) throw new Error(`Song catalog HTTP ${response.status}`);
    return response.json();
}

// Mirrors the eligibility check resolveArtist() uses to build the "Choose
// your own" source list, so a matched song is guaranteed to still be part
// of that catalog once the redirect below lands on it.
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
        small.textContent = `${playlist.trackCount} track${playlist.trackCount === 1 ? '' : 's'}`;
        copy.appendChild(small);
        button.appendChild(copy);
        button.addEventListener('click', () => onSelect(playlist));
        fragment.appendChild(button);
    }
    list.appendChild(fragment);
}

async function openSpotifyPlaylistImport(matchingArtists, language) {
    const modal = element('spotifyPlaylistModal');
    const status = element('spotifyPlaylistStatus');
    const useBtn = element('useSpotifyMatchesBtn');
    if (!modal || !status || !useBtn) return;

    _matchState = null;
    useBtn.hidden = true;
    element('spotifyPlaylistList').replaceChildren();
    modal.classList.remove('hidden');
    status.textContent = 'Connecting to Spotify…';

    // Speech-mode startup never loads the Spotify module (see main.js); this
    // entry point can be reached before it has, so load it on demand.
    if (!window.isSpotifyConnected) {
        await import('./spotify.js?v=20260831a').catch(error => {
            console.warn('Spotify controls deferred:', error);
        });
    }
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
    status.textContent = playlists.length ? 'Choose a playlist to match.' : 'No playlists found on this Spotify account.';

    renderPlaylistList(playlists, async playlist => {
        status.textContent = `Matching "${playlist.name}" against your library…`;
        useBtn.hidden = true;
        try {
            const [catalog, trackIds] = await Promise.all([
                buildLanguageCatalog(matchingArtists),
                window.fetchSpotifyPlaylistTrackIds(playlist.id)
            ]);
            const matches = catalog.songs.filter(song => song.spotifyTrackId && trackIds.has(song.spotifyTrackId));
            if (!matches.length) {
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
        } catch (error) {
            status.textContent = error?.message || 'Could not match that playlist.';
        }
    });
}

function closeSpotifyPlaylistImport() {
    element('spotifyPlaylistModal')?.classList.add('hidden');
    _matchState = null;
}

function confirmSpotifyMatches() {
    if (!_matchState) return;
    const record = {
        songIds: _matchState.songIds,
        artistSlugs: _matchState.artistSlugs,
        updatedAt: new Date().toISOString()
    };
    try {
        localStorage.setItem(CUSTOM_SONG_SET_KEY, JSON.stringify(record));
    } catch (_) {}
    window.showAppLoading?.('Building your deck', `Matching ${_matchState.playlistName}…`, true);
    window.location.href = `${window.location.pathname}?artist=custom&language=${encodeURIComponent(_matchState.language)}`;
}

function setupSpotifyPlaylistImport() {
    const modal = element('spotifyPlaylistModal');
    if (!modal || modal.dataset.listenersReady === '1') return;
    modal.dataset.listenersReady = '1';
    element('closeSpotifyPlaylistModal')?.addEventListener('click', closeSpotifyPlaylistImport);
    element('cancelSpotifyPlaylistBtn')?.addEventListener('click', closeSpotifyPlaylistImport);
    element('useSpotifyMatchesBtn')?.addEventListener('click', confirmSpotifyMatches);
    modal.addEventListener('click', event => {
        if (event.target === modal) closeSpotifyPlaylistImport();
    });
    document.addEventListener('keydown', event => {
        if (event.key === 'Escape' && !modal.classList.contains('hidden')) closeSpotifyPlaylistImport();
    });
}

setupSpotifyPlaylistImport();

window.openSpotifyPlaylistImport = openSpotifyPlaylistImport;
