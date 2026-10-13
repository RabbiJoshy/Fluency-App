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
            <button type="button" id="musicBackBtn" class="music-back">‹ Back</button>
            <div><small id="musicWorkspaceLanguage"></small><h1 id="musicWorkspaceTitle" tabindex="-1">Your music</h1></div>
        </header>
        <div class="music-workspace-layout">
            <nav class="music-workspace-nav" aria-label="Music">
                <button type="button" data-music-stage="artists">Artists</button>
                <button type="button" data-music-stage="playlists">Spotify playlists</button>
                <button type="button" data-music-stage="setup" id="musicSetupBtn">Study setup</button>
            </nav>
            <div class="music-workspace-main">
                <div id="musicArtistBrowser"><h2>Choose your music</h2><p>Pick an artist, or mix songs from several artists.</p><div id="musicArtistList"></div></div>
                <div id="musicPickerHost"></div>
                <div id="musicStudySetup" hidden></div>
            </div>
            <aside class="music-selection-summary" aria-labelledby="musicSelectionTitle">
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
    const studyNav = document.querySelector('#desktopStudyBtn .desktop-shell-label');
    if (studyNav) studyNav.textContent = 'Music';
    // Moving the real controls preserves all their handlers and source state.
    for (const id of SETUP_IDS) {
        const element = document.getElementById(id);
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
    const language = options.language || window.activeArtist?.language || window.selectedLanguage;
    document.getElementById('musicWorkspaceLanguage').textContent = options.languageName || language || '';
    document.getElementById('musicSetupBtn').disabled = !hasDeck();
    updateMusicSelection();
}

function showStage(next, { focus = true } = {}) {
    stage = next;
    document.getElementById('musicArtistBrowser').hidden = next !== 'artists';
    document.getElementById('musicPickerHost').hidden = !['songs', 'playlists'].includes(next);
    document.getElementById('musicStudySetup').hidden = next !== 'setup';
    workspace.dataset.stage = next;
    workspace.querySelectorAll('[data-music-stage]').forEach(button => {
        const selected = button.dataset.musicStage === next || (next === 'songs' && button.dataset.musicStage === 'artists');
        if (selected) button.setAttribute('aria-current', 'page');
        else button.removeAttribute('aria-current');
    });
    const backButton = document.getElementById('musicBackBtn');
    backButton.textContent = next === 'artists' ? '‹ Back to vocabulary' : '‹ Back';
    updateMusicSelection();
    if (focus) document.getElementById('musicWorkspaceTitle').focus({ preventScroll: true });
}

function closePickers() {
    window.closeSpotifyPlaylistImport?.({ force: true });
    document.getElementById('songSetModal')?.classList.add('hidden');
}

function showArtists() {
    enter();
    closePickers();
    showStage('artists');
}

function openPlaylists() {
    enter();
    closePickers();
    showStage('playlists');
    options.onSelectPlaylist?.();
}

function back() {
    if (busy) return;
    if (stage === 'songs' && playlistReturn) openPlaylists();
    else if (stage !== 'artists') showArtists();
    else leaveMusicWorkspace();
}

export function openMusicWorkspace(nextOptions = {}) {
    options = { ...options, ...nextOptions };
    enter();
    const list = document.getElementById('musicArtistList');
    list.replaceChildren();
    const entries = options.artists || [];
    for (const entry of entries) {
        const button = document.createElement('button');
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
        description.textContent = entry.description || 'Choose all their songs, or just a few.';
        copy.append(name, description);
        button.append(image, copy);
        button.addEventListener('click', () => {
            playlistReturn = false;
            options.onSelectArtist?.(entry);
        });
        list.appendChild(button);
    }
    if (!entries.length) {
        const empty = document.createElement('p');
        empty.textContent = 'No artists are available for this language yet. You can build from a Spotify playlist.';
        list.appendChild(empty);
    }
    const requested = nextOptions.stage || 'artists';
    if (requested === 'setup') showMusicStudySetup();
    else if (requested === 'songs') window.showSongSetPicker?.();
    else if (requested === 'playlists') openPlaylists();
    else showArtists();
}

export function showMusicSongPicker() {
    enter();
    window.closeSpotifyPlaylistImport?.({ force: true });
    showStage('songs', { focus: false });
}

export function showMusicStudySetup() {
    if (!hasDeck()) return;
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
    document.getElementById('musicSelectionTitle').textContent = sourceName || artist?.name || live?.playlistName || 'Choose some music';
    document.getElementById('musicSelectionCount').textContent = artist || songs
        ? `${selected.length} song${selected.length === 1 ? '' : 's'} selected`
        : live ? `${live.trackCount || 0} songs · ${live.matchedCount} words ready to study` : 'Your songs will appear here.';
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
    edit.hidden = (!artist && !live) || stage === 'songs';
    edit.textContent = live && !artist ? 'Change playlist songs' : 'Choose songs';
}

export function leaveMusicWorkspace() {
    if (busy) return;
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
    workspace.hidden = true;
    document.body.classList.remove('music-workspace-active');
    const studyNav = document.querySelector('#desktopStudyBtn .desktop-shell-label');
    if (studyNav) studyNav.textContent = 'Choose a set';
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
window.showMusicSongPicker = showMusicSongPicker;
window.showMusicStudySetup = showMusicStudySetup;
window.updateMusicSelection = updateMusicSelection;
window.musicWorkspaceActive = () => active;
window.musicWorkspaceBusy = () => busy;
window.navigateMusicWorkspace = navigateMusicWorkspace;
window.musicWorkspaceBack = back;
window.setMusicWorkspaceBusy = value => {
    busy = Boolean(value);
    if (!workspace) return;
    document.getElementById('musicBackBtn').disabled = busy;
    workspace.querySelectorAll('[data-music-stage]').forEach(button => {
        button.disabled = busy || (button.dataset.musicStage === 'setup' && !hasDeck());
    });
};
