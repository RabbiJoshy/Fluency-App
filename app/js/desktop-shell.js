// Setup uses a persistent desktop navigation; studying gives the gutters
// back to side-dock.js. Reuse the real header buttons and their handlers.
const PAGE_IDS = [
    'settingsModal', 'totalStatsModal', 'reviewHomeModal', 'helpModal',
    'learningContextModal', 'extrasModal', 'cognateRulesModal',
    'fastModeModal', 'vocabularyImportModal', 'aboutProjectModal',
    'extraModal',
];
const NAV_IDS = ['desktopStudyBtn', 'desktopExploreBtn', 'topBarProgressBtn',
    'topBarGearBtn', 'topBarUserName', 'helpBtn', 'desktopAboutBtn'];

// The trail: language, then vocabulary, then (for Music) the artist or playlist,
// stacked under one another in the sidebar. Each chip opens the choices at its
// own level and switches there, instead of sending the learner back to the
// start. State is read from the same globals the rest of the app uses; the
// actions are main.js's desktopTrailActions.
const TRAIL_CHECK = '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="m5 12.5 4.5 4.5L19 7.5"></path></svg>';

function initDesktopTrail(closePages) {
    const chip = document.getElementById('learningContextBtn');
    if (!chip || document.getElementById('desktopTrail')) return;
    const trail = document.createElement('nav');
    trail.id = 'desktopTrail';
    trail.className = 'desktop-trail';
    trail.setAttribute('aria-label', 'Vocabulary');
    trail.hidden = true;
    trail.innerHTML = `
        <div class="desktop-trail-level" data-level="mode">
            <button type="button" class="desktop-trail-chip" aria-expanded="false" aria-controls="desktopTrailModeMenu">
                <span class="desktop-trail-icon" aria-hidden="true"></span>
                <span class="desktop-trail-copy"><small>Vocabulary</small><strong></strong></span>
                <span class="desktop-trail-caret" aria-hidden="true">›</span>
            </button>
            <div class="desktop-trail-menu" id="desktopTrailModeMenu" role="group" aria-label="Vocabulary" hidden></div>
        </div>
        <div class="desktop-trail-level" data-level="music" hidden>
            <button type="button" class="desktop-trail-chip" aria-expanded="false" aria-controls="desktopTrailMusicMenu">
                <span class="desktop-trail-icon" aria-hidden="true"></span>
                <span class="desktop-trail-copy"><small>Music</small><strong></strong></span>
                <span class="desktop-trail-caret" aria-hidden="true">›</span>
            </button>
            <div class="desktop-trail-menu" id="desktopTrailMusicMenu" role="group" aria-label="Music options" hidden></div>
        </div>
        <div class="desktop-trail-level" data-level="source" hidden>
            <button type="button" class="desktop-trail-chip" aria-expanded="false" aria-controls="desktopTrailSourceMenu">
                <span class="desktop-trail-icon desktop-trail-photo" aria-hidden="true"></span>
                <span class="desktop-trail-copy"><small>Artist</small><strong></strong></span>
                <span class="desktop-trail-caret" aria-hidden="true">›</span>
            </button>
            <div class="desktop-trail-menu" id="desktopTrailSourceMenu" role="group" aria-label="Artist or playlist" hidden></div>
        </div>`;
    chip.after(trail);
    const levels = {
        mode: trail.querySelector('[data-level="mode"]'),
        music: trail.querySelector('[data-level="music"]'),
        source: trail.querySelector('[data-level="source"]'),
    };
    let sourceEntries = null;
    let sourceEntriesLanguage = '';
    let renderToken = 0;

    const inWorkspace = () => document.body.classList.contains('desktop-workspace');
    const busy = () => Boolean(window.musicWorkspaceBusy?.());
    const language = () => {
        if (window.activeArtist && window.activeArtist.language && window.activeArtist.language === window.selectedLanguage) {
            return window.activeArtist.language;
        }
        return window.selectedLanguage;
    };
    function state() {
        let mode = window.currentLearningMode?.() || null;
        if (!mode && window.musicWorkspaceActive?.()) mode = 'lyrics';
        return { mode, language: language() };
    }
    function closeMenus(except = null) {
        for (const level of Object.values(levels)) {
            if (level === except) continue;
            level.querySelector('.desktop-trail-menu').hidden = true;
            level.querySelector('.desktop-trail-chip').setAttribute('aria-expanded', 'false');
        }
    }
    function option(label, { icon = '', detail = '', selected = false, disabled = false, onSelect }) {
        const button = document.createElement('button');
        button.type = 'button';
        button.className = 'desktop-trail-option';
        button.setAttribute('role', 'menuitemradio');
        button.setAttribute('aria-checked', String(selected));
        button.disabled = disabled;
        button.title = label;
        const mark = document.createElement('span');
        mark.className = 'desktop-trail-icon';
        mark.setAttribute('aria-hidden', 'true');
        if (icon instanceof Node) mark.appendChild(icon); else mark.innerHTML = icon;
        const copy = document.createElement('span');
        copy.className = 'desktop-trail-copy';
        const name = document.createElement('strong');
        name.textContent = label;
        copy.appendChild(name);
        if (detail) {
            const small = document.createElement('small');
            small.textContent = detail;
            copy.appendChild(small);
        }
        const tick = document.createElement('span');
        tick.className = 'desktop-trail-tick';
        tick.setAttribute('aria-hidden', 'true');
        if (selected) tick.innerHTML = TRAIL_CHECK;
        button.append(mark, copy, tick);
        button.addEventListener('click', () => {
            closeMenus();
            if (!selected) onSelect?.();
        });
        return button;
    }
    function photoFor(entry) {
        const holder = document.createElement('span');
        holder.className = 'desktop-trail-photo';
        const art = entry.pickerImage || entry.image || entry.defaultAlbumArt || '';
        if (art) holder.style.backgroundImage = `url("${String(art).replace(/"/g, '%22')}")`;
        else holder.textContent = entry.initials || '♪';
        return holder;
    }
    function paintChipPhoto(el, entry) {
        el.replaceChildren();
        el.style.backgroundImage = '';
        const art = entry?.pickerImage || entry?.image || entry?.defaultAlbumArt || '';
        if (art) el.style.backgroundImage = `url("${String(art).replace(/"/g, '%22')}")`;
        else el.textContent = entry?.customSongSource ? '♫' : (entry?.initials || '♪');
    }

    function renderModeMenu({ mode, language: lang }) {
        const copy = window.learningModeCopy?.(lang);
        const menu = levels.mode.querySelector('.desktop-trail-menu');
        menu.replaceChildren();
        if (!copy) return;
        const capabilities = window._normalModeLangConfigs?.[lang]?.capabilities
            || window.config?.languages?.[lang]?.capabilities || {};
        const speechAvailable = capabilities.speech !== false;
        const musicAvailable = (capabilities.lyrics !== false || speechAvailable)
            && window.musicOpenFor?.(lang) !== false;
        const inMusic = mode === 'lyrics' || mode === 'live';
        menu.append(
            option(copy.speech.label, {
                icon: copy.speech.iconHTML, selected: mode === 'speech', disabled: !speechAvailable,
                onSelect: () => window.desktopTrailActions?.chooseSpeech(lang),
            }),
            option(copy.lyrics.label, {
                icon: copy.lyrics.iconHTML, selected: inMusic, disabled: !musicAvailable,
                onSelect: () => window.desktopTrailActions?.chooseMusic(lang),
            }),
        );
    }

    function renderMusicMenu({ language: lang }) {
        const menu = levels.music.querySelector('.desktop-trail-menu');
        menu.replaceChildren();
        const copy = window.learningModeCopy?.(lang);
        const stage = window.musicWorkspaceStage?.() || '';
        const isLive = Boolean(window.playlistLiveDeck?.() && !window.activeArtist) || stage === 'playlists';
        const spotifyIcon = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M3 6h12M3 12h12M3 18h8"></path><path d="M19 8v9"></path><circle cx="17" cy="17" r="2"></circle></svg>';
        menu.append(
            option('Artists', {
                icon: copy?.lyrics?.iconHTML || '', selected: !isLive && (stage === 'artists' || !stage),
                onSelect: () => window.desktopTrailActions?.chooseArtists ? window.desktopTrailActions.chooseArtists(lang) : window.desktopTrailActions?.chooseMusic(lang, 'artists'),
            }),
            option('Spotify playlists', {
                icon: spotifyIcon, selected: isLive,
                onSelect: () => window.desktopTrailActions?.openPlaylists(lang),
            }),
        );
    }

    async function renderSourceMenu({ language: lang }) {
        const menu = levels.source.querySelector('.desktop-trail-menu');
        const token = ++renderToken;
        if (sourceEntriesLanguage !== lang || !sourceEntries) {
            menu.replaceChildren(Object.assign(document.createElement('p'), {
                className: 'desktop-trail-note', textContent: 'Loading artists…',
            }));
            try { sourceEntries = await window.desktopTrailActions.artistEntries(lang); }
            catch (_) { sourceEntries = []; }
            sourceEntriesLanguage = lang;
        }
        if (token !== renderToken) return;
        const live = window.playlistLiveDeck?.();
        const current = window.activeArtist;
        menu.replaceChildren();
        if (live && !current) {
            const spotify = document.createElement('span');
            spotify.className = 'desktop-trail-note-icon';
            spotify.innerHTML = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M3 6h12M3 12h12M3 18h8"></path><path d="M19 8v9"></path><circle cx="17" cy="17" r="2"></circle></svg>';
            menu.appendChild(option(live.playlistName || 'Current playlist', {
                icon: spotify, selected: true,
                onSelect: () => window.desktopTrailActions.openPlaylists(lang),
            }));
            menu.appendChild(option('Change Spotify playlist…', {
                icon: spotify, selected: false,
                onSelect: () => window.desktopTrailActions.openPlaylists(lang),
            }));
        } else {
            for (const entry of sourceEntries) {
                const isMix = entry.slug === '__custom__' || /^mix several/i.test(entry.name);
                const selected = Boolean(current) && !live
                    && (isMix ? current.customSongSource === true : (current.slug === entry.slug || current.name === entry.name));
                menu.appendChild(option(isMix ? 'Mix artists' : entry.name, {
                    icon: photoFor(entry), selected,
                    onSelect: () => window.desktopTrailActions.chooseArtist(entry, lang),
                }));
            }
        }
    }

    function refresh() {
        const lang = language();
        const visible = inWorkspace() && !chip.hidden && Boolean(lang);
        trail.hidden = !visible;
        if (!visible) {
            closeMenus();
            if (chip.getAttribute('aria-label')?.startsWith('Language:')) chip.setAttribute('aria-label', 'Open learning settings');
            return;
        }
        const current = state();
        const copy = window.learningModeCopy?.(lang);
        const inMusic = current.mode === 'lyrics' || current.mode === 'live';
        const live = window.playlistLiveDeck?.();
        const artist = window.activeArtist;
        const spotifyIcon = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M3 6h12M3 12h12M3 18h8"></path><path d="M19 8v9"></path><circle cx="17" cy="17" r="2"></circle></svg>';

        // Level 1: Vocabulary (Speech vs Music)
        const modeChip = levels.mode.querySelector('.desktop-trail-chip');
        const modeIcon = modeChip.querySelector('.desktop-trail-icon');
        modeChip.querySelector('strong').textContent = current.mode === 'speech' ? 'Speech'
            : inMusic ? 'Music' : 'Choose…';
        modeChip.querySelector('small').textContent = 'Vocabulary';
        modeIcon.innerHTML = current.mode === 'speech' ? (copy?.speech.iconHTML || '')
            : inMusic ? (copy?.lyrics.iconHTML || '') : '';
        levels.mode.dataset.state = current.mode || 'empty';
        if (levels.mode.querySelector('.desktop-trail-menu').hidden) renderModeMenu(current);

        // Level 2: Music option subrow (Artists vs Spotify playlists)
        levels.music.hidden = !inMusic;
        if (inMusic) {
            const isLive = Boolean(live && !artist);
            const stage = window.musicWorkspaceStage?.() || (isLive ? 'playlists' : (artist ? 'artists' : 'choices'));
            const inChoices = stage === 'choices' && !artist && !live;
            const musicChip = levels.music.querySelector('.desktop-trail-chip');
            const musicIcon = musicChip.querySelector('.desktop-trail-icon');
            musicChip.querySelector('small').textContent = 'Music';
            musicChip.querySelector('strong').textContent = inChoices ? 'Choose…' : (isLive || stage === 'playlists' ? 'Spotify playlists' : 'Artists');
            musicIcon.innerHTML = inChoices ? '' : ((isLive || stage === 'playlists') ? spotifyIcon : (copy?.lyrics.iconHTML || ''));
            levels.music.dataset.state = inChoices ? 'empty' : 'chosen';
            if (levels.music.querySelector('.desktop-trail-menu').hidden) renderMusicMenu(current);
        } else {
            const menu = levels.music.querySelector('.desktop-trail-menu');
            menu.hidden = true;
            levels.music.querySelector('.desktop-trail-chip').setAttribute('aria-expanded', 'false');
        }

        // Level 3: Source (Artist name or Playlist name)
        const hasSource = Boolean(artist || live);
        levels.source.hidden = !inMusic || !hasSource;
        if (inMusic && hasSource) {
            const isLive = Boolean(live && !artist);
            const sourceChip = levels.source.querySelector('.desktop-trail-chip');
            const label = isLive ? (live.playlistName || 'Spotify playlist')
                : artist ? (artist.name || 'Artist') : 'Choose artist';
            sourceChip.querySelector('strong').textContent = label;
            sourceChip.querySelector('small').textContent = isLive ? 'Playlist' : 'Artist';
            const photo = sourceChip.querySelector('.desktop-trail-icon');
            if (artist) paintChipPhoto(photo, artist);
            else { photo.replaceChildren(); photo.style.backgroundImage = ''; photo.innerHTML = spotifyIcon; }
            levels.source.dataset.state = 'chosen';
        } else {
            const menu = levels.source.querySelector('.desktop-trail-menu');
            menu.hidden = true;
            levels.source.querySelector('.desktop-trail-chip').setAttribute('aria-expanded', 'false');
        }
        const locked = busy();
        trail.querySelectorAll('.desktop-trail-chip').forEach(button => { button.disabled = locked; });
        chip.setAttribute('aria-label', `Language: ${document.getElementById('learningContextLanguageOnly')?.textContent || ''}. Change language`);
    }

    for (const [key, level] of Object.entries(levels)) {
        const button = level.querySelector('.desktop-trail-chip');
        const menu = level.querySelector('.desktop-trail-menu');
        button.addEventListener('click', event => {
            event.stopPropagation();
            const opening = menu.hidden;
            closeMenus(level);
            if (!opening) { menu.hidden = true; button.setAttribute('aria-expanded', 'false'); return; }
            if (key === 'source') renderSourceMenu(state());
            else if (key === 'music') renderMusicMenu(state());
            else renderModeMenu(state());
            menu.hidden = false;
            button.setAttribute('aria-expanded', 'true');
            menu.querySelector('button:not(:disabled)')?.focus({ preventScroll: true });
        });
        menu.addEventListener('keydown', event => {
            const items = [...menu.querySelectorAll('button:not(:disabled)')];
            const at = items.indexOf(document.activeElement);
            if (event.key === 'ArrowDown') { event.preventDefault(); items[(at + 1) % items.length]?.focus(); }
            else if (event.key === 'ArrowUp') { event.preventDefault(); items[(at - 1 + items.length) % items.length]?.focus(); }
            else if (event.key === 'Escape') { event.stopPropagation(); closeMenus(); button.focus(); }
        });
    }
    document.addEventListener('click', event => {
        if (!trail.contains(event.target)) closeMenus();
    });

    // On the desktop sidebar the language chip is the language level: it opens
    // the language choices directly. Learning settings, with its Explore
    // activities, moved to the Explore item below.
    chip.addEventListener('click', event => {
        if (!inWorkspace()) return;
        event.stopImmediatePropagation();
        closePages();
        if (!busy()) window.desktopTrailActions?.changeLanguage();
    }, { capture: true });
    const explore = document.getElementById('desktopExploreBtn');
    explore?.addEventListener('click', () => {
        if (typeof window.openExtraModal === 'function') {
            window.openExtraModal();
        } else {
            window.updateLearningContextUI?.();
            document.getElementById('learningContextModal')?.classList.remove('hidden');
        }
    });

    let queued = false;
    const schedule = () => {
        if (queued) return;
        queued = true;
        requestAnimationFrame(() => { queued = false; refresh(); explore && (explore.hidden = chip.hidden); });
    };
    const observer = new MutationObserver(schedule);
    observer.observe(chip, { attributes: true, attributeFilter: ['hidden'], childList: true, subtree: true, characterData: true });
    const step1 = document.getElementById('step1');
    if (step1) observer.observe(step1, { attributes: true, attributeFilter: ['class'] });
    observer.observe(document.body, { attributes: true, attributeFilter: ['class'] });
    window.addEventListener('hashchange', schedule);
    window.refreshDesktopTrail = schedule;
    schedule();
    return schedule;
}

function initDesktopShell() {
    const setup = document.getElementById('setupPanel');
    const app = document.getElementById('appContent');
    const header = document.getElementById('topBar');
    if (!setup || !app || !header) return;
    const pages = PAGE_IDS.map(id => document.getElementById(id)).filter(Boolean);
    const modalAttributes = new Map(pages.map(el => [el, el.getAttribute('aria-modal')]));
    let activeNav = 'desktopStudyBtn';

    function closePages() {
        for (const page of pages.filter(el => !el.hidden && !el.classList.contains('hidden'))) {
            // Run the existing close handler so its cleanup/back behavior is kept.
            document.getElementById(`close${page.id[0].toUpperCase()}${page.id.slice(1)}`)?.click();
            page.classList.add('hidden');
        }
    }
    function refresh() {
        const zoom = parseFloat(getComputedStyle(document.body).zoom) || 1;
        const desktop = window.innerWidth >= 1024 && window.innerWidth / zoom >= 1024;
        const studying = !app.classList.contains('hidden');
        const workspace = desktop && !studying && !setup.classList.contains('hidden');
        document.body.classList.toggle('desktop-workspace', workspace);
        document.body.classList.toggle('desktop-studying', desktop && studying);
        header.setAttribute('role', workspace ? 'navigation' : 'region');
        header.setAttribute('aria-label', workspace ? 'Main navigation' : 'App controls');
        let anyPage = false;
        for (const page of pages) {
            page.classList.toggle('desktop-workspace-page', workspace);
            const original = modalAttributes.get(page);
            if (workspace) page.setAttribute('aria-modal', 'false');
            else if (original !== null) page.setAttribute('aria-modal', original);
            else page.removeAttribute('aria-modal');
            if (!page.hidden && !page.classList.contains('hidden')) anyPage = true;
        }
        if (!anyPage) activeNav = 'desktopStudyBtn';
        for (const id of NAV_IDS) {
            const button = document.getElementById(id);
            if (workspace && id === activeNav) button?.setAttribute('aria-current', 'page');
            else button?.removeAttribute('aria-current');
        }
        // The setup underneath a workspace page must not receive keyboard focus.
        for (const child of setup.children) {
            if (child !== header) child.inert = workspace && anyPage;
        }
    }
    initDesktopTrail(closePages);
    for (const id of NAV_IDS) {
        document.getElementById(id)?.addEventListener('click', () => {
            if (!document.body.classList.contains('desktop-workspace')) return;
            closePages();
            activeNav = id;
        }, { capture: true });
    }
    document.getElementById('desktopStudyBtn')?.addEventListener('click', () => {
        refresh();
    });
    document.getElementById('desktopAboutBtn')?.addEventListener('click', () => {
        window.openAboutProjectModal?.();
    });
    const observer = new MutationObserver(refresh);
    observer.observe(setup, { attributes: true, attributeFilter: ['class'] });
    observer.observe(app, { attributes: true, attributeFilter: ['class'] });
    // Observe visibility only; writing navigation attributes cannot retrigger it.
    for (const page of pages) observer.observe(page, { attributes: true, attributeFilter: ['class', 'hidden'] });
    window.addEventListener('resize', refresh);
    new MutationObserver(refresh).observe(document.documentElement, {
        attributes: true, attributeFilter: ['data-text-size'],
    });
    refresh();
}

if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initDesktopShell, { once: true });
} else {
    initDesktopShell();
}
