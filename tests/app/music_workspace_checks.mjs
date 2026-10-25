import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';

// A small DOM harness exercises ownership and navigation without loading
// account services, Spotify or the vocabulary releases.
const elements = new Map();
class Element {
    constructor(id = '') {
        this.id = id; this.children = []; this.attrs = {}; this.dataset = {};
        this.listeners = {}; this.hidden = false; this.style = {}; this.classes = new Set();
        this.classList = { add: (...names) => names.forEach(n => this.classes.add(n)),
            remove: (...names) => names.forEach(n => this.classes.delete(n)), contains: n => this.classes.has(n) };
    }
    set innerHTML(_html) {
        // The workspace template is static. Only these buttons need selectors.
        for (const id of ['musicBackBtn', 'musicWorkspaceTitle', 'musicArtistSearch', 'musicMixBtn', 'musicArtistBrowser', 'musicArtistList', 'musicPickerHost', 'musicStudySetup',
            'seriesBrowser', 'casaSeriesBtn', 'musicSelectionTitle', 'musicSelectionCount', 'musicSelectionPreview', 'musicEditSongsBtn']) {
            const element = new Element(id); elements.set(id, element); this.appendChild(element);
        }
        this.nav = ['artists', 'playlists', 'setup'].map(next => {
            const button = new Element(next === 'setup' ? 'musicSetupBtn' : next);
            button.dataset.musicStage = next;
            elements.set(button.id, button); this.appendChild(button); return button;
        });
    }
    getAttribute(name) { return this.attrs[name] ?? null; }
    getBoundingClientRect() { return {height: 0}; }
    remove() { if (this.parent) this.parent.children = this.parent.children.filter(child => child !== this); }
    setAttribute(name, value) { this.attrs[name] = value; }
    removeAttribute(name) { delete this.attrs[name]; }
    addEventListener(name, handler) { (this.listeners[name] ||= []).push(handler); }
    click() { if (!this.disabled) (this.listeners.click || []).forEach(handler => handler()); }
    focus() { document.activeElement = this; }
    querySelectorAll() { return this.nav || []; }
    querySelector() { return null; }
    appendChild(child) {
        if (child.parent) child.parent.children = child.parent.children.filter(element => element !== child);
        child.parent = this; this.children.push(child); return child;
    }
    append(...children) { children.forEach(child => this.appendChild(child)); }
    before(child) { this.place(child, 0); }
    after(child) { this.place(child, 1); }
    place(child, offset) {
        const parent = this.parent;
        if (child.parent) child.parent.children = child.parent.children.filter(element => element !== child);
        const index = parent.children.indexOf(this) + offset;
        parent.children.splice(index, 0, child); child.parent = parent;
    }
    replaceChildren(...children) { this.children.forEach(child => { child.parent = null; }); this.children = []; this.append(...children); }
}
const setup = new Element('setupPanel'), body = new Element('body');
body.appendChild(setup);
for (const id of ['topBar', 'artistSourceStep', 'dataLoadingIndicator', 'personalCoverageWrapper',
    'step2', 'step4', 'reviewDeckSection', 'extrasDeckSection', 'loadingMessage', 'songSetModal', 'spotifyPlaylistModal']) {
    const element = new Element(id); elements.set(id, element);
    (id.endsWith('Modal') ? body : setup).appendChild(element);
}
const trigger = new Element('trigger');
globalThis.document = { activeElement: trigger, body, createElement: () => new Element(),
    createComment: () => new Element(), getElementById: id => elements.get(id), querySelector: () => null };
globalThis.window = globalThis;
const storage = new Map();
globalThis.sessionStorage = { setItem: (key, value) => storage.set(key, value),
    getItem: key => storage.get(key) || null, removeItem: key => storage.delete(key) };
let navigated, playlistOpens = 0, left = 0;
window.fluencyRoutes = { formatRoute: route => JSON.stringify(route), goToRoute: route => { navigated = route; } };
window.closeSpotifyPlaylistImport = () => elements.get('spotifyPlaylistModal').classList.add('hidden');
window.activeArtist = { name: 'Artist', language: 'spanish' };
window.artistSongCatalog = { songs: [{ id: 'one', title: 'One' }, { id: 'two', title: 'Two' }] };
window.selectedSongIds = ['one'];
const source = await readFile(new URL('../../app/js/music-workspace.js', import.meta.url), 'utf8');
const module = await import('../../app/js/music-workspace.js');

module.openMusicWorkspace({ language: 'spanish', artists: [{ name: 'Artist', slug: 'artist' }],
    onSelectPlaylist: () => { playlistOpens++; }, onLeave: () => { left++; } });
assert.equal(elements.get('step2').parent.id, 'musicStudySetup', 'move the real study controls into Music');
assert.equal(elements.get('songSetModal').attrs.role, 'region', 'song selection is an inline page');
assert.equal(elements.get('musicStudySetup').hidden, true, 'browsing must hide study setup');
assert.equal(elements.get('musicSelectionCount').textContent, '1 song selected');
elements.get('playlists').click();
assert.equal(playlistOpens, 1);
assert.equal(elements.get('musicPickerHost').hidden, false);
window.setMusicWorkspaceBusy(true);
elements.get('artists').click();
assert.equal(elements.get('musicArtistBrowser').hidden, true, 'do not switch source during a deck build');
window.setMusicWorkspaceBusy(false);
window.showSongSetPicker = () => module.showMusicSongPicker();
module.showMusicSongPicker();
assert.equal(elements.get('musicStudySetup').hidden, true);
module.showMusicStudySetup();
assert.equal(elements.get('musicStudySetup').hidden, false);
assert.equal(elements.get('musicPickerHost').hidden, true);

const route = { kind: 'songs', language: 'es' };
module.navigateMusicWorkspace(route, 'songs', { fromPlaylist: true });
assert.deepEqual(navigated, route);
window.fluencyRoute = route;
assert.equal(module.consumeMusicHandoff(), 'songs');
assert.equal(module.consumeMusicHandoff(), null, 'handoffs are consumed once');
module.navigateMusicWorkspace(route);
window.fluencyRoute = { kind: 'language', language: 'fr' };
assert.equal(module.consumeMusicHandoff(), null, 'a stale handoff must not affect another route');
module.leaveMusicWorkspace();
assert.equal(elements.get('step2').parent, setup, 'restore Speech controls to their original parent');
assert.equal(elements.get('songSetModal').parent, body);
assert.equal(elements.get('songSetModal').attrs.role, 'dialog');
assert.equal(window.musicWorkspaceActive(), false);
assert.equal(left, 1);
window.activeArtist = null;
module.openMusicWorkspace({ artists: [] });
assert.equal(elements.get('musicSetupBtn').disabled, true, 'no study setup until music is selected');
module.showChoices();
assert.equal(elements.get('musicArtistBrowser').hidden, false, 'the pick screen is the artists tab: no separate chooser');
assert.equal(elements.get('musicBackBtn').hidden, true, 'no back button on the pick screen when no deck is open');
assert.equal(elements.get('musicWorkspaceTitle').textContent, 'Music');
module.showArtists();
assert.equal(elements.get('musicArtistBrowser').hidden, false);
window.activeArtist = { name: 'Artist', language: 'spanish' };
module.showArtists();
assert.equal(elements.get('musicBackBtn').hidden, false, 'with a deck open, Back returns to it');
assert.equal(elements.get('musicBackBtn').textContent, '‹ Artist');
// TV Series is a separate Spanish-only picker and uses the existing deck engine.
assert.equal(window.seriesOpenFor('spanish'), true);
assert.equal(window.seriesOpenFor('french'), false);
module.showSeriesChoices('spanish');
assert.equal(window.seriesWorkspaceActive(), true);
assert.equal(elements.get('musicWorkspaceTitle').textContent, 'TV Series');
assert.equal(elements.get('seriesBrowser').hidden, false);
assert.equal(elements.get('musicArtistBrowser').hidden, true);
assert.equal(elements.get('musicPickerHost').hidden, true);
assert.equal(elements.get('musicEditSongsBtn').hidden, true);
module.showSeriesChoices('french');
assert.equal(window.seriesWorkspaceActive(), true, 'an unsupported language cannot replace the picker');
let casaLoads = 0, activations = 0;
window.loadCasaDePapelPreset = async () => { casaLoads++; };
window.activatePlaylistLiveStudy = language => { assert.equal(language, 'spanish'); activations++; };
await elements.get('casaSeriesBtn').listeners.click[0]();
assert.equal(casaLoads, 1);
assert.equal(activations, 1);
assert.equal(window.musicWorkspaceActive(), false);
window.activeArtist = null;
window.playlistLiveActive = () => true;
window.playlistLiveDeck = () => ({ playlistId: 'la-casa-de-papel', playlistName: 'La Casa de Papel' });
assert.equal(window.isSeriesStudy(), true);
module.showMusicStudySetup();
assert.equal(window.seriesWorkspaceActive(), true, 'Casa returns to TV Series setup');
assert.equal(elements.get('musicStudySetup').hidden, false);
assert.equal(elements.get('musicEditSongsBtn').hidden, true);
window.playlistLiveDeck = () => ({ playlistId: 'spotify-playlist' });
assert.equal(window.isSeriesStudy(), false, 'ordinary playlists remain Music');
module.openMusicWorkspace({ language: 'spanish', artists: [{ name: 'Artist', slug: 'artist' },
    { name: 'La Casa de Papel', slug: 'la-casa-de-papel', isSeries: true }] });
assert.equal(window.seriesWorkspaceActive(), false);
assert.equal(elements.get('seriesBrowser').hidden, true);
assert.equal(elements.get('musicArtistList').children.length, 1, 'Music does not list TV series');
assert.equal(source.includes('Series &amp; subtitles'), false);
console.log('Music and TV Series navigation and ownership checks passed');

// The playlist subset is chosen before looking up lyrics, persists by playlist
// and language, and cancellation releases the pending choice.
const importer = await readFile(new URL('../../app/js/spotify-playlist-import.js', import.meta.url), 'utf8');
const pickerSource = importer.slice(importer.indexOf('function choosePlaylistTracks('),
    importer.indexOf('async function openSpotifyPlaylistImport('));
const values = new Map();
globalThis.localStorage = { getItem: key => values.get(key), setItem: (key, value) => values.set(key, value) };
for (const id of ['spotifyPlaylistList', 'spotifyPlaylistTitle', 'spotifyPlaylistStatus']) elements.set(id, new Element(id));
const choose = new Function('element', 'setImportBusy', `return (${pickerSource.trim()});`)(
    id => elements.get(id), () => {});
const tracks = [{ id: 'a', title: 'A' }, { id: 'b', title: 'B' }];
const controller = new AbortController();
const selection = choose({ id: 'playlist', name: 'Playlist' }, tracks, controller.signal, 'spanish');
const playlistList = elements.get('spotifyPlaylistList');
const secondCheckbox = playlistList.children[2].children[0];
secondCheckbox.checked = false;
secondCheckbox.listeners.change[0]();
playlistList.children.at(-1).children[0].click();
assert.deepEqual(await selection, [tracks[0]]);
assert.equal(elements.get('musicSelectionTitle').textContent, 'Playlist');
const reopenedController = new AbortController();
const reopened = choose({ id: 'playlist', name: 'Playlist' }, tracks, reopenedController.signal, 'spanish');
assert.equal(playlistList.children[1].children[0].checked, true);
assert.equal(playlistList.children[2].children[0].checked, false, 'remember the subset when the playlist is reopened');
reopenedController.abort();
await assert.rejects(reopened, { name: 'AbortError' });
console.log('Playlist song selection, persistence and cancellation checks passed');
