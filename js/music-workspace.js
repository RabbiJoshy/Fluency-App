import { beginRegionLoading } from './loading-ui.js?v=183eb417';
// Music owns its browsing, song selection and study setup. Existing deck
// loaders still own vocabulary/progress; route handoffs reopen this workspace.
const HANDOFF_KEY = 'fluency_music_workspace_v1';
const SETUP_IDS = ['artistSourceStep', 'dataLoadingIndicator', 'personalCoverageWrapper',
    'step2', 'step4', 'reviewDeckSection', 'extrasDeckSection', 'loadingMessage'];
let workspace;
let options = {};
let stage = 'artists';
let active = false;
let busy = false;
let playlistReturn = false;
let sourceMode = 'music';
function isSeriesDeck(deck) { return deck?.sourceKind === 'series' || deck?.playlistId === 'la-casa-de-papel'; }
window.seriesOpenFor = language => language === 'spanish';
window.isSeriesStudy = () => Boolean(window.playlistLiveActive?.() && isSeriesDeck(window.playlistLiveDeck?.()));
window.seriesWorkspaceActive = () => active && sourceMode === 'series';
let returnFocus;
const homes = new Map();

function rememberHome(element) {
    if (!element || homes.has(element)) return;
    const marker = document.createComment(`music-home:${element.id}`);
    element.before(marker);
    homes.set(element, marker);
}

function init() {
    if (workspace) return;
    workspace = document.createElement('section');
    workspace.id = 'musicWorkspace';
    workspace.hidden = true;
    workspace.setAttribute('aria-labelledby', 'musicWorkspaceTitle');
    workspace.innerHTML = `
        <header class="music-workspace-header">
            <div class="music-workspace-titlebar">
                <button type="button" id="musicBackBtn" class="music-back" hidden>‹ Back</button>
                <h1 id="musicWorkspaceTitle" tabindex="-1">Music</h1>
            </div>
            <nav class="music-workspace-nav" aria-label="Music source">
                <button type="button" data-music-stage="artists">Artists</button>
                <button type="button" data-music-stage="playlists">Spotify playlists</button>
                <button type="button" data-music-stage="setup" id="musicSetupBtn" hidden aria-hidden="true" tabindex="-1">Study setup</button>
            </nav>
        </header>
        <div class="music-workspace-layout">
            <div class="music-workspace-main">
                <div id="musicArtistBrowser" hidden>
                    <div class="music-artist-tools">
                        <input type="search" id="musicArtistSearch" placeholder="Search artists" autocomplete="off" aria-label="Search artists">
                        <button type="button" id="musicMixBtn" class="music-mix-btn" hidden>Mix several</button>
                    </div>
                    <div id="musicArtistList"></div>
                </div>
                <div id="seriesBrowser" hidden>
                    <p>Choose a TV series</p>
                    <button type="button" id="casaSeriesBtn" class="music-artist-option">
                        <span class="music-artist-image" aria-hidden="true">LCDP</span>
                        <span><strong>La Casa de Papel</strong><small>30 episodes · Seasons 1–4 sample · Spanish dialogue</small></span>
                    </button>
                    <button type="button" id="eliteSeriesBtn" class="music-artist-option">
                        <span class="music-artist-image" aria-hidden="true">É</span>
                        <span><strong>Élite</strong><small>8 episodes · Season 1 sample · Spanish with English examples</small></span>
                    </button>
                </div>
                <div id="musicPickerHost"></div>
                <div id="musicStudySetup" hidden></div>
            </div>
            <aside class="music-selection-summary" aria-labelledby="musicSelectionTitle" hidden>
                <span class="music-summary-eyebrow">Your selection</span>
                <h2 id="musicSelectionTitle">Choose some music</h2>
                <p id="musicSelectionCount"></p>
                <ul id="musicSelectionPreview"></ul>
                <button type="button" id="musicEditSongsBtn" hidden>Choose songs</button>
            </aside>
        </div>`;
    document.getElementById('topBar').after(workspace);
    workspace.querySelectorAll('[data-music-stage]').forEach(button => {
        button.addEventListener('click', () => {
            if (busy) return;
            const next = button.dataset.musicStage;
            if (next === 'playlists') openPlaylists();
            else if (next === 'setup') showMusicStudySetup();
            else showArtists();
        });
    });
    document.getElementById('musicBackBtn').addEventListener('click', back);
    for (const [buttonId, seriesId, title] of [
        ['casaSeriesBtn', 'la-casa-de-papel', 'La Casa de Papel'],
        ['eliteSeriesBtn', 'elite', 'Élite']
    ]) document.getElementById(buttonId).addEventListener('click', async () => {
        if (busy || options.language !== 'spanish') return;
        window.setMusicWorkspaceBusy?.(true);
        window.showAppLoading?.(`Loading ${title}`, 'Preparing your series vocabulary…');
        try {
            await window.loadSeriesPreset(seriesId);
            dismissMusicWorkspace();
            window.activatePlaylistLiveStudy('spanish');
        } catch (error) {
            window.hideAppLoading?.();
            alert(error.message || `Could not load ${title}.`);
        } finally { window.setMusicWorkspaceBusy?.(false); }
    });
    document.getElementById('musicEditSongsBtn').addEventListener('click', () => {
        if (window.playlistLiveActive?.()) openPlaylists();
        else window.showSongSetPicker?.();
    });
}

function hasDeck() {
    return Boolean(window.activeArtist || window.playlistLiveActive?.());
}

function enter() {
    init();
    if (!active) returnFocus = document.activeElement;
    active = true;
    workspace.hidden = false;
    document.body.classList.add('music-workspace-active');
    document.getElementById('step1')?.classList.remove('source-speech-active');
    const studyNav = document.querySelector('#desktopStudyBtn .desktop-shell-label');
    if (studyNav) studyNav.textContent = sourceMode === 'series' ? 'TV Series' : 'Music';
    // Moving the real controls preserves all their handlers and source state.
    for (const id of SETUP_IDS) {
        const element = document.getElementById(id);
        if (id === 'step4' && element?.parentElement?.classList?.contains('level-choosing')) continue;
        rememberHome(element);
        if (element) document.getElementById('musicStudySetup').appendChild(element);
    }
    for (const id of ['songSetModal', 'spotifyPlaylistModal']) {
        const panel = document.getElementById(id);
        rememberHome(panel);
        if (!panel) continue;
        document.getElementById('musicPickerHost').appendChild(panel);
        panel.classList.add('music-inline-panel');
        panel.setAttribute('role', 'region');
        panel.removeAttribute('aria-modal');
    }
    document.getElementById('musicSetupBtn').disabled = !hasDeck();
    updateMusicSelection();
    window.updateLearningContextUI?.();
    window.refreshDesktopTrail?.();
}

function showStage(next, { focus = true } = {}) {
    stage = next;
    document.getElementById('seriesBrowser').hidden = next !== 'series';
    workspace.dataset.sourceMode = sourceMode;
    const artistBrowser = document.getElementById('musicArtistBrowser');
    if (artistBrowser) artistBrowser.hidden = next !== 'artists';
    const pickerHost = document.getElementById('musicPickerHost');
    if (pickerHost) pickerHost.hidden = !['songs', 'playlists'].includes(next);
    const studySetup = document.getElementById('musicStudySetup');
    if (studySetup) studySetup.hidden = next !== 'setup';
    workspace.dataset.stage = next;
    workspace.querySelectorAll('[data-music-stage]').forEach(button => {
        const selected = button.dataset.musicStage === next || (next === 'songs' && button.dataset.musicStage === 'artists');
        if (selected) button.setAttribute('aria-current', 'page');
        else button.removeAttribute('aria-current');
    });
    const isPick = ['artists', 'playlists', 'series'].includes(next);
    const backButton = document.getElementById('musicBackBtn');
    if (backButton) {
        // The pick screens are the top level: Back only appears to return to a deck.
        backButton.hidden = isPick && !hasDeck();
        backButton.textContent = isPick ? `‹ ${window.activeArtist?.name || window.playlistLiveDeck?.()?.playlistName || 'Back'}` : '‹ Back';
    }
    const nav = workspace.querySelector('.music-workspace-nav');
    if (nav) nav.hidden = !isPick || sourceMode === 'series';
    const title = document.getElementById('musicWorkspaceTitle');
    if (title) {
        title.textContent = next === 'songs' ? 'Choose songs' : next === 'setup' ? 'Study setup' : sourceMode === 'series' ? 'TV Series' : 'Music';
    }
    updateMusicSelection();
    window.refreshDesktopTrail?.();
    if (focus && title) title.focus({ preventScroll: true });
}

function closePickers() {
    window.closeSpotifyPlaylistImport?.({ force: true });
    window.closeSubtitleImport?.();
    document.getElementById('songSetModal')?.classList.add('hidden');
}

// There is no separate chooser any more: the tabs on the pick screen are it.
export function showChoices() {
    showArtists();
}

export function showArtists({ focus = true } = {}) {
    sourceMode = 'music';
    enter();
    closePickers();
    showStage('artists', { focus });
}

export function openPlaylists() {
    sourceMode = 'music';
    enter();
    closePickers();
    showStage('playlists');
    options.onSelectPlaylist?.();
}

export function showSeriesChoices(language = 'spanish') {
    if (!window.seriesOpenFor(language)) return;
    sourceMode = 'series';
    options = { ...options, language };
    enter();
    closePickers();
    showStage('series');
}
window.showSeriesChoices = showSeriesChoices;

function back() {
    if (busy) return;
    if (stage === 'songs') {
        const unfinishedMix = window.activeArtist?.customSongSource && !(window.selectedSongIds || []).length;
        if (playlistReturn) openPlaylists();
        else if (hasDeck() && !unfinishedMix) window.dismissMusicWorkspace?.();
        else showArtists();
    } else if (stage === 'artists' || stage === 'playlists' || stage === 'series') {
        // Back from a pick screen returns to the deck you came from.
        if (hasDeck()) window.dismissMusicWorkspace?.();
        else showArtists();
    } else if (stage === 'setup') {
        if (sourceMode === 'series') showSeriesChoices(options.language);
        else showArtists();
    }
}

export function openMusicWorkspace(nextOptions = {}) {
    sourceMode = 'music';
    options = { ...options, ...nextOptions };
    enter();
    const list = document.getElementById('musicArtistList');
    list.replaceChildren();
    const entries = (options.artists || []).filter(entry => !entry.isSeries && entry.slug !== 'la-casa-de-papel');
    const mixEntry = entries.find(e => e.slug === '__custom__');
    const mixBtn = document.getElementById('musicMixBtn');
    mixBtn.hidden = !mixEntry;
    mixBtn.onclick = () => { playlistReturn = false; options.onSelectArtist?.(mixEntry); };
    const search = document.getElementById('musicArtistSearch');
    search.value = nextOptions.query || '';
    search.oninput = () => {
        const query = search.value.trim().toLocaleLowerCase();
        list.querySelectorAll('.music-artist-option').forEach(tile => {
            tile.hidden = Boolean(query) && !tile.dataset.name.includes(query);
        });
    };
    for (const entry of entries.filter(e => e.slug !== '__custom__')) {
        const button = document.createElement('button');
        button.dataset.name = String(entry.name || '').toLocaleLowerCase();
        button.type = 'button';
        button.className = 'music-artist-option';
        const image = document.createElement('span');
        image.className = 'music-artist-image';
        if (entry.image) {
            const img = document.createElement('img');
            img.src = entry.image;
            img.alt = '';
            image.appendChild(img);
        } else image.textContent = entry.initials || '♪';
        const copy = document.createElement('span');
        const name = document.createElement('strong');
        name.textContent = entry.name;
        const description = document.createElement('small');
        description.textContent = entry.description || '';
        copy.append(name, description);
        button.append(image, copy);
        button.addEventListener('click', () => {
            playlistReturn = false;
            options.onSelectArtist?.(entry);
        });
        list.appendChild(button);
    }
    workspace.querySelectorAll('[data-music-stage]').forEach(button => {
        button.disabled = Boolean(nextOptions.loading) || (button.dataset.musicStage === 'setup' && !hasDeck());
    });
    if (nextOptions.loading) {
        beginRegionLoading(list, { label: 'Loading artists…', shape: 'artists' });
    } else {
        // Clear a previous request's loading owner before publishing real tiles.
        beginRegionLoading(list, { preserve: true })();
    }
    if (!entries.length && !nextOptions.loading) {
        const empty = document.createElement('p');
        empty.textContent = 'No artists are available for this language yet. You can build from a Spotify playlist.';
        list.appendChild(empty);
    }
    search.oninput();
    const requested = nextOptions.stage || 'artists';
    if (requested === 'setup') showMusicStudySetup();
    else if (requested === 'songs') window.showSongSetPicker?.();
    else if (requested === 'playlists') openPlaylists();
    else if (requested === 'artists') showArtists({ focus: nextOptions.focus !== false });
    else showArtists({ focus: nextOptions.focus !== false });
}

export function showMusicSongPicker() {
    enter();
    window.closeSpotifyPlaylistImport?.({ force: true });
    showStage('songs', { focus: false });
}

export function showMusicStudySetup() {
    if (!hasDeck()) return;
    sourceMode = window.isSeriesStudy?.() ? 'series' : 'music';
    enter();
    closePickers();
    showStage('setup');
    updateMusicSelection();
}

export function updateMusicSelection(songs = null, sourceName = '') {
    if (!workspace) return;
    const artist = window.activeArtist;
    const live = window.playlistLiveDeck?.();
    const selected = songs || (window.artistSongCatalog?.songs || []).filter(song =>
        (window.selectedSongIds || []).map(String).includes(String(song.id)));
    const isSeries = isSeriesDeck(live);
    const liveUnit = isSeries ? (live?.trackCount === 1 ? 'episode' : 'episodes') : (live?.trackCount === 1 ? 'song' : 'songs');
    const tokenPart = live?.tokenCount ? `${Number(live.tokenCount).toLocaleString()} ${isSeries ? 'dialogue' : 'lyric'} words · ` : '';
    document.getElementById('musicSelectionTitle').textContent = sourceName || artist?.name || live?.playlistName || 'Choose some music';
    document.getElementById('musicSelectionCount').textContent = artist || songs
        ? `${selected.length} song${selected.length === 1 ? '' : 's'} selected`
        : live ? `${live.trackCount || 0} ${liveUnit} · ${tokenPart}${Number(live.matchedCount || 0).toLocaleString()} words ready to study` : 'Your songs will appear here.';
    const preview = document.getElementById('musicSelectionPreview');
    preview.replaceChildren();
    selected.slice(0, 5).forEach(song => {
        const item = document.createElement('li');
        item.textContent = song.title;
        preview.appendChild(item);
    });
    if (selected.length > 5) {
        const item = document.createElement('li');
        item.textContent = `+ ${selected.length - 5} more`;
        preview.appendChild(item);
    }
    const edit = document.getElementById('musicEditSongsBtn');
    edit.hidden = sourceMode === 'series' || (!artist && !live) || stage === 'songs';
    edit.textContent = live && !artist ? 'Change playlist songs' : 'Choose songs';
}

export function dismissMusicWorkspace() {
    closePickers();
    for (const [element, marker] of homes) {
        marker.after(element);
        if (element.classList.contains('music-inline-panel')) {
            element.classList.remove('music-inline-panel');
            element.setAttribute('role', 'dialog');
            element.setAttribute('aria-modal', 'true');
        }
    }
    active = false;
    if (workspace) workspace.hidden = true;
    document.body.classList.remove('music-workspace-active');
    const studyNav = document.querySelector('#desktopStudyBtn .desktop-shell-label');
    if (studyNav) studyNav.textContent = 'Vocabulary';
    window.updateLearningContextUI?.();
    window.refreshDesktopTrail?.();
}

export function leaveMusicWorkspace() {
    if (busy) return;
    dismissMusicWorkspace();
    if (options.onLeave) options.onLeave();
    else {
        window.fluencyRoutes?.replaceRoute({ kind: 'language', language: window.fluencyRoutes.routeCodeFor(options.language, window.config?.languages) });
        returnFocus?.focus?.();
    }
}

export function navigateMusicWorkspace(route, nextStage = 'songs', { fromPlaylist = false } = {}) {
    try {
        sessionStorage.setItem(HANDOFF_KEY, JSON.stringify({ stage: nextStage, fromPlaylist,
            route: window.fluencyRoutes.formatRoute(route) }));
    } catch (_) {}
    window.fluencyRoutes.goToRoute(route);
}

export function consumeMusicHandoff() {
    try {
        const stored = JSON.parse(sessionStorage.getItem(HANDOFF_KEY) || 'null');
        sessionStorage.removeItem(HANDOFF_KEY);
        if (stored?.route !== window.fluencyRoutes.formatRoute(window.fluencyRoute)) return null;
        playlistReturn = Boolean(stored.fromPlaylist);
        return stored.stage;
    } catch (_) { return null; }
}

window.openMusicWorkspace = openMusicWorkspace;
window.dismissMusicWorkspace = dismissMusicWorkspace;
window.showMusicSongPicker = showMusicSongPicker;
window.showMusicStudySetup = showMusicStudySetup;
window.updateMusicSelection = updateMusicSelection;
window.musicWorkspaceActive = () => active;
window.musicWorkspaceBusy = () => busy;
window.navigateMusicWorkspace = navigateMusicWorkspace;
window.musicWorkspaceBack = back;
window.showMusicChoices = showChoices;
window.musicWorkspaceStage = () => stage;
window.setMusicWorkspaceBusy = value => {
    busy = Boolean(value);
    if (!workspace) return;
    document.getElementById('musicBackBtn').disabled = busy;
    workspace.querySelectorAll('[data-music-stage]').forEach(button => {
        button.disabled = busy || (button.dataset.musicStage === 'setup' && !hasDeck());
    });
};
