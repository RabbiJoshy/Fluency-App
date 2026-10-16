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
            <button type="button" id="musicBackBtn" class="music-back" hidden>‹ Back</button>
            <div class="music-workspace-title-group">
                <small id="musicWorkspaceLanguage"></small>
                <h1 id="musicWorkspaceTitle" tabindex="-1">Choose your music</h1>
            </div>
            <nav class="music-workspace-nav" aria-label="Music source" hidden>
                <button type="button" data-music-stage="artists">Artists</button>
                <button type="button" data-music-stage="playlists">Spotify playlists</button>
                <button type="button" data-music-stage="setup" id="musicSetupBtn" hidden aria-hidden="true" tabindex="-1">Study setup</button>
            </nav>
        </header>
        <div class="music-workspace-layout">
            <div class="music-workspace-main">
                <div id="musicSourceChoices" class="music-source-choices">
                    <p class="music-browser-intro">Pick how you want to learn from music.</p>
                    <div class="music-source-grid">
                        <button type="button" class="music-source-card" data-music-stage="artists">
                            <span class="music-source-card-icon" aria-hidden="true"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="9" cy="8" r="3.5"></circle><path d="M2.5 20a6.5 6.5 0 0 1 13 0"></path><path d="M16 4.5a3.5 3.5 0 0 1 0 7"></path><path d="M18.5 14.5A6.5 6.5 0 0 1 21.5 20"></path></svg></span>
                            <span class="music-source-card-copy">
                                <strong>Artists</strong>
                                <small id="musicArtistsChoiceDesc">Learn from catalog songs and popular artists</small>
                            </span>
                            <span class="music-source-card-arrow" aria-hidden="true">›</span>
                        </button>
                        <button type="button" class="music-source-card" data-music-stage="playlists">
                            <span class="music-source-card-icon music-source-spotify" aria-hidden="true"><svg viewBox="0 0 24 24" fill="currentColor"><path d="M12 0C5.4 0 0 5.4 0 12s5.4 12 12 12 12-5.4 12-12S18.66 0 12 0zm5.521 17.34c-.24.359-.66.48-1.021.24-2.82-1.74-6.36-2.101-10.561-1.141-.418.122-.779-.179-.899-.539-.12-.421.18-.78.54-.9 4.56-1.021 8.52-.6 11.64 1.32.42.18.479.659.301 1.02zm1.44-3.3c-.301.42-.841.6-1.262.3-3.239-1.98-8.159-2.58-11.939-1.38-.479.12-1.02-.12-1.14-.6-.12-.48.12-1.021.6-1.141C9.6 9.9 15 10.561 18.72 12.84c.361.181.54.78.241 1.2zm.12-3.36C15.24 8.4 8.82 8.16 5.16 9.301c-.6.179-1.2-.181-1.38-.721-.18-.601.18-1.2.72-1.381 4.26-1.26 11.28-1.02 15.721 1.621.539.3.719 1.02.42 1.56-.299.421-1.02.599-1.559.3z"/></svg></span>
                            <span class="music-source-card-copy">
                                <strong>Spotify playlists</strong>
                                <small id="musicPlaylistsChoiceDesc">Build custom decks from your Spotify playlists</small>
                            </span>
                            <span class="music-source-card-arrow" aria-hidden="true">›</span>
                        </button>
                    </div>
                </div>
                <div id="musicArtistBrowser" hidden><p class="music-browser-intro">Pick an artist, or mix songs from several artists.</p><div id="musicArtistList"></div></div>
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
    if (studyNav) studyNav.textContent = 'Music';
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
    const language = options.language || window.selectedLanguage;
    const langDisplayName = options.languageName || (window._normalModeLangConfigs?.[language]?.name || window.config?.languages?.[language]?.name || language);
    document.getElementById('musicWorkspaceLanguage').textContent = `${langDisplayName} · Music`;
    document.getElementById('musicSetupBtn').disabled = !hasDeck();
    updateMusicSelection();
    window.updateLearningContextUI?.();
    window.refreshDesktopTrail?.();
}

function showStage(next, { focus = true } = {}) {
    stage = next;
    const choicesEl = document.getElementById('musicSourceChoices');
    if (choicesEl) choicesEl.hidden = next !== 'choices';
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
    const backButton = document.getElementById('musicBackBtn');
    if (backButton) {
        if (next === 'choices') {
            backButton.hidden = true;
        } else {
            backButton.hidden = false;
            backButton.textContent = '‹ Back';
        }
    }
    const title = document.getElementById('musicWorkspaceTitle');
    if (title) {
        if (next === 'choices') title.textContent = 'Choose your music';
        else if (next === 'artists') title.textContent = 'Choose an artist';
        else if (next === 'playlists') title.textContent = 'Spotify playlists';
        else if (next === 'songs') title.textContent = 'Choose songs';
        else if (next === 'setup') title.textContent = 'Study setup';
    }
    updateMusicSelection();
    window.refreshDesktopTrail?.();
    if (focus && title) title.focus({ preventScroll: true });
}

function closePickers() {
    window.closeSpotifyPlaylistImport?.({ force: true });
    document.getElementById('songSetModal')?.classList.add('hidden');
}

export function showChoices() {
    enter();
    closePickers();
    showStage('choices');
}

export function showArtists() {
    enter();
    closePickers();
    showStage('artists');
}

export function openPlaylists() {
    enter();
    closePickers();
    showStage('playlists');
    options.onSelectPlaylist?.();
}

function back() {
    if (busy) return;
    if (stage === 'songs') {
        if (playlistReturn) openPlaylists();
        else showArtists();
    } else if (stage === 'artists' || stage === 'playlists') {
        showChoices();
    } else if (stage === 'setup') {
        if (hasDeck()) window.showSongSetPicker?.();
        else showChoices();
    }
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
    const realArtists = entries.filter(e => e.slug !== '__custom__');
    const artistDescEl = document.getElementById('musicArtistsChoiceDesc');
    const playlistDescEl = document.getElementById('musicPlaylistsChoiceDesc');
    const langName = options.languageName || (window._normalModeLangConfigs?.[options.language]?.name || window.config?.languages?.[options.language]?.name || options.language) || '';
    if (artistDescEl) {
        if (realArtists.length) {
            const names = realArtists.slice(0, 3).map(a => a.name).join(', ');
            artistDescEl.textContent = `Curated catalog: ${names}${realArtists.length > 3 ? '…' : ''} · Full lyrics & vocabulary`;
        } else {
            artistDescEl.textContent = `No curated catalog artists in ${langName} yet · Use Spotify instead`;
        }
    }
    if (playlistDescEl) {
        playlistDescEl.textContent = `Build custom decks from any ${langName} playlist, album, or track with Spotify`;
    }
    const requested = nextOptions.stage || (hasDeck() ? 'artists' : 'choices');
    if (requested === 'setup') showMusicStudySetup();
    else if (requested === 'songs') window.showSongSetPicker?.();
    else if (requested === 'playlists') openPlaylists();
    else if (requested === 'artists') showArtists();
    else showChoices();
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
