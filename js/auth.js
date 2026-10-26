// Authentication, Google Sheets sync, and progress persistence.
// Key functions: saveWordProgress(), loadUserProgressFromSheet(), submitLogin().
import './state.js?v=fa6cd049';
import { accountPermissions } from './account-permissions.js?v=fa6cd049';
import { readJsonWithTimeout } from './read-request.js?v=fa6cd049';
import { submitProfileLogin, resetProfileLogin } from './learning-profiles.js?v=fa6cd049';
import { applyRemoteFastTrack } from './fast-track-preferences.js?v=fa6cd049';
import { dbGet, dbPut } from './offline-db.js?v=fa6cd049';
import { consumeRouteNavigation } from './routes.js?v=fa6cd049';
// Offline-durable write path. sendOrQueue() write-throughs when online and
// enqueues to IndexedDB when offline/failed. The overlay helpers keep
// un-synced card and granular knowledge answers visible after a Sheets reload.
import {
    sendOrQueue,
    applyPendingProgressOverlay,
    applyPendingItemProgressOverlay,
    applyPendingMetaProgressOverlay
} from './sync-queue.js?v=fa6cd049';
import { IS_STAGING, getIsolatedSyncUser } from './env.js?v=fa6cd049';
import { PASSWORDLESS_ENABLED, PASSWORDLESS_SYNC_URL, startPasswordlessAuth, signOutPasswordless, hideLegacyAuthChoices } from './passwordless-auth.js?v=fa6cd049';

// Shared with the server; names and retired initials do not grant access.
function userPermissions(user = currentUser) {
    return accountPermissions(user && !user.isGuest ? user.initials : '');
}
function isAuditAccount(user = currentUser) { return userPermissions(user).isAdmin; }
function isJpAccount(user = currentUser) { return userPermissions(user).isJp; }
function isReviewerAccount(user = currentUser) { return userPermissions(user).isReviewer; }
function canUserFlag(user = currentUser) { return userPermissions(user).canFlag; }

window.isAuditAccount = isAuditAccount;
window.isJpAccount = isJpAccount;
window.isReviewerAccount = isReviewerAccount;
window.canUserFlag = canUserFlag;

function createFlagId() {
    if (globalThis.crypto?.randomUUID) return globalThis.crypto.randomUUID();
    return `flag-${Date.now().toString(36)}-${Math.random().toString(36).slice(2, 12)}`;
}

function currentClientBuild() {
    try {
        const src = document.querySelector('script[src*="js/main.js"]')?.src || '';
        return new URL(src, window.location.href).searchParams.get('v') || '';
    } catch (_) {
        return '';
    }
}

async function loadSecrets() {
    // Browser-facing service endpoints and OAuth client IDs are public
    // configuration, not credentials. Static deployments deliberately
    // exclude backend/, so load them from the public app config before trying
    // the optional local/backend overrides below.
    const publicSpotifyClientId = config?.publicServices?.spotifyClientId;
    window._spotifyClientId = typeof publicSpotifyClientId === 'string'
        ? publicSpotifyClientId.trim()
        : '';
    const publicSpotifyRedirectUris = config?.publicServices?.spotifyRedirectUris;
    window._spotifyRedirectUris = publicSpotifyRedirectUris && typeof publicSpotifyRedirectUris === 'object'
        ? publicSpotifyRedirectUris
        : {};
    const publicProgressSyncUrl = config?.publicServices?.progressSyncUrl;
    GOOGLE_SCRIPT_URL = typeof publicProgressSyncUrl === 'string'
        ? publicProgressSyncUrl.trim()
        : '';
    if (PASSWORDLESS_ENABLED) GOOGLE_SCRIPT_URL = PASSWORDLESS_SYNC_URL;

    // Pages never ships backend/. Older offline workers can replay a cached
    // HTML fallback here and start recursive module preloads before updating.
    // Staging and production already have public endpoints above; do not probe that URL.
    if (IS_STAGING) return;
    const isLocal = typeof window !== 'undefined' && /^(localhost|127\.0\.0\.1)$/.test(window.location?.hostname || '');
    if (!isLocal) return;

    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), 3000);
    try {
        const response = await fetch('backend/secrets.json', { signal: controller.signal });
        if (response.ok) {
            const secrets = await response.json();
            GOOGLE_SCRIPT_URL = secrets.googleScriptUrl || GOOGLE_SCRIPT_URL;
            window._spotifyClientId = secrets.spotifyClientId || window._spotifyClientId;
        }
    } catch (error) {
        if (!GOOGLE_SCRIPT_URL) {
            console.warn('Could not load progress sync configuration - cross-device sync will be disabled');
        }
    } finally {
        clearTimeout(timeout);
    }
    if (PASSWORDLESS_ENABLED) GOOGLE_SCRIPT_URL = PASSWORDLESS_SYNC_URL;
}

// Detect whether this page load is a reload (F5 / Cmd-R) versus a fresh
// navigation (link click, mode switch to #/artist/..., new tab). Uses the
// modern Navigation Timing API with a fallback to the deprecated
// performance.navigation interface for older browsers.
function _isPageReload() {
    try {
        const nav = performance.getEntriesByType('navigation')[0];
        if (nav && nav.type) return nav.type === 'reload';
    } catch (_) {}
    if (performance && performance.navigation) {
        return performance.navigation.type === 1;  // TYPE_RELOAD
    }
    return false;
}

// Resolves once someone is signed in or has chosen guest, whichever path got
// them there. A linked word waits on it so the card never opens under the
// landing.
let _resolveAuthReady = null;
window.authReady = window.authReady || new Promise(resolve => { _resolveAuthReady = resolve; });
function _markAuthReady() { _resolveAuthReady?.(); }

// The first-run tour covers the study card; a visitor who arrived on a
// linked word sees that card first and the tour on a later visit.
function _openFirstRunTutorialUnlessLinked() {
    if (window.fluencyRoute?.kind === 'word') return;
    if (window.maybeShowKnownLanguagesIntro?.(window.selectedLanguage)) return;
    if (window.maybeShowFrequencyIntro?.()) return;
    window.openFirstRunCardTutorial?.();
}

// Check authentication on page load.
//
// Named users persist in localStorage — survive across browser sessions.
// Guest users persist in sessionStorage but ONLY across same-tab
// navigations (mode switch, artist switch). A user-initiated reload
// explicitly drops the guest session, so refreshing always surfaces the
// landing — useful for Josh's testing and for any visitor who wants to
// see the landing again without closing the tab.
//
// Summary of cases:
//   - refresh (F5/Cmd-R)   → clear guest session → landing
//   - mode/artist switch   → keep guest session → app, no landing
//   - new tab at app URL   → no session → landing
//   - new tab at #/about   → no session → landing + About on top
function onPasswordlessSignedOut() {
    if (window.authLogoutInFlight) return;
    if (currentUser?.isGuest) return;
    if (currentUser?.initials) {
        localStorage.removeItem(`progress_cache_${currentUser.initials}`);
        localStorage.removeItem(`progress_cache_${getIsolatedSyncUser(currentUser.initials)}`);
    }
    localStorage.removeItem('flashcardUser');
    clearDeviceSessionState();
    currentUser = null;
    showUserInfo();
    showAuthModal();
}

function checkAuthentication() {
    if (_isPageReload() && !consumeRouteNavigation()) {
        sessionStorage.removeItem('flashcardGuestSession');
    }
    // Guest browsing does not depend on Clerk. Restore it before starting any
    // account requests so mode/artist navigation also works without sign-in.
    if (sessionStorage.getItem('flashcardGuestSession') === '1') {
        currentUser = { isGuest: true };
        window.markProgressLoaded?.();
        window.applyGlobalStudyDefaults?.();
        showUserInfo();
        hideAuthModal();
        _markAuthReady();
        return;
    }
    if (PASSWORDLESS_ENABLED) {
        GOOGLE_SCRIPT_URL = PASSWORDLESS_SYNC_URL;
        const savedUser = localStorage.getItem('flashcardUser');
        if (savedUser) {
            try {
                const parsed = JSON.parse(savedUser);
                if (parsed && !parsed.isGuest) {
                    currentUser = parsed;
                    window.applyGlobalStudyDefaults?.();
                    showUserInfo();
                    hideAuthModal();
                    _markAuthReady();
                    setTimeout(() => window.checkAndShowAdminUpdateModal?.(), 300);
                    startPasswordlessAuth(completeProfileLogin, onPasswordlessSignedOut);
                    return;
                }
            } catch (_) {}
        }
        showAuthModal();
        startPasswordlessAuth(completeProfileLogin, onPasswordlessSignedOut);
        return;
    }
    const savedUser = localStorage.getItem('flashcardUser');
    if (savedUser) {
        try {
            const parsed = JSON.parse(savedUser);
            if (parsed && parsed.isGuest) {
                localStorage.removeItem('flashcardUser');  // legacy cleanup
            } else if (parsed) {
                currentUser = parsed;
                window.applyGlobalStudyDefaults?.();
                showUserInfo();
                hideAuthModal();
                _markAuthReady();
                setTimeout(() => window.checkAndShowAdminUpdateModal?.(), 300);
                return;
            }
        } catch (e) {
            localStorage.removeItem('flashcardUser');
        }
    }
    showAuthModal();
}

// Show authentication modal
function showAuthModal() {
    const authModal = document.getElementById('authModal');
    // Authentication is the fail-open boot surface. If configuration or an
    // imported feature stalls, never leave the visual watchdog's loading
    // layer above a modal whose controls should already be usable.
    window.hideAppLoading?.();
    document.body.classList.add('auth-active');
    hideLoginForm();
    authModal.classList.remove('hidden');
    document.getElementById('setupPanel').style.display = 'none';
}

// Hide authentication modal
function hideAuthModal() {
    const authModal = document.getElementById('authModal');
    authModal.classList.add('hidden');
    document.body.classList.remove('auth-active');
    document.getElementById('setupPanel').style.display = 'block';
}

// Show user info badge — no longer unhides #userInfo here;
// the floating toolbar is shown/hidden by showFloatingBtns() in flashcard mode.
function showUserInfo() {
    const label = document.getElementById('topBarUserName');
    if (!label) return;
    if (!currentUser) { label.textContent = ''; return; }
    if (currentUser.isGuest) {
        label.classList.remove('is-icon');
        label.textContent = 'GUEST';
        label.title = 'Log in or create an account';
        label.setAttribute('aria-label', 'Log in or create an account');
        return;
    }
    // Usernames can be long, so the top bar shows an account icon, not the name.
    const name = currentUser.username || currentUser.initials || '';
    label.classList.add('is-icon');
    label.innerHTML = '<svg viewBox="0 0 24 24" aria-hidden="true"><circle cx="12" cy="8" r="4"></circle><path d="M4 21a8 8 0 0 1 16 0"></path></svg>';
    label.title = name ? `Account: ${name}` : 'Open account settings';
    label.setAttribute('aria-label', name ? `Account settings for ${name}` : 'Open account settings');
}

// Guest mode handler.
//
// Writes a sessionStorage marker so guest state survives same-tab
// navigations (mode switch → #/artist/..., artist swap, etc.) but NOT a
// user-initiated refresh. The refresh distinction is enforced in
// checkAuthentication() via the Navigation Timing API — so refreshing
// always surfaces the landing, while clicking "Normal mode" from the top
// bar keeps you in the app as guest.
//
// Progress is still never persisted for guests.
function enterGuestMode() {
    currentUser = { isGuest: true };
    // A guest has no stored progress to wait for, so the setup screen must not
    // sit behind a promise that will never resolve.
    window.markProgressLoaded?.();
    sessionStorage.setItem('flashcardGuestSession', '1');
    showUserInfo();
    hideAuthModal();
    _markAuthReady();
    setTimeout(_openFirstRunTutorialUnlessLinked, 250);
}

// Show login form
function showLoginForm(mode = 'login') {
    if (PASSWORDLESS_ENABLED) {
        startPasswordlessAuth(completeProfileLogin, onPasswordlessSignedOut);
        return;
    }
    resetProfileLogin();
    const guestRow = document.getElementById('guestModeRow');
    if (guestRow) guestRow.style.display = 'none';
    else if (document.getElementById('guestModeBtn')) document.getElementById('guestModeBtn').style.display = 'none';
    document.getElementById('loginModeRow').style.display = 'none';
    const createRow = document.getElementById('createModeRow');
    if (createRow) createRow.style.display = 'none';
    document.getElementById('aboutProjectBtn').style.display = 'none';
    document.getElementById('loginInfoNote').classList.add('hidden');
    document.querySelector('#authModal .auth-modal-content')?.classList.add('is-login-form');
    const heading = document.querySelector('#loginForm .auth-form-heading h4');
    const subtext = document.querySelector('#loginForm .auth-form-heading p');
    const submit = document.getElementById('submitInitialsBtn');
    const loginFormEl = document.getElementById('loginForm');
    loginFormEl.dataset.mode = mode === 'create' ? 'create' : 'login';
    loginFormEl.classList.remove('needs-birthday');
    if (mode === 'create') {
        if (heading) heading.textContent = 'Create account';
        if (subtext) subtext.textContent = 'Choose a username and optional birthday to save progress.';
        if (submit) submit.textContent = 'Create account';
    } else {
        if (heading) heading.textContent = 'Log in';
        if (subtext) subtext.textContent = 'Enter your username to continue.';
        if (submit) submit.textContent = 'Log in';
    }
    document.getElementById('loginForm').classList.remove('hidden');
    document.getElementById('userInitials').focus();
}

// Hide login form
function hideLoginForm() {
    resetProfileLogin();
    const guestRow = document.getElementById('guestModeRow');
    if (guestRow) guestRow.style.display = 'flex';
    else if (document.getElementById('guestModeBtn')) document.getElementById('guestModeBtn').style.display = 'flex';
    document.getElementById('loginModeRow').style.display = 'flex';
    const createRow = document.getElementById('createModeRow');
    if (createRow) createRow.style.display = 'flex';
    document.getElementById('aboutProjectBtn').style.display = '';
    document.querySelector('#authModal .auth-modal-content')?.classList.remove('is-login-form');
    document.getElementById('loginForm').classList.add('hidden');
    document.getElementById('loginForm').classList.remove('needs-birthday');
    document.getElementById('userInitials').value = '';
    const bdayDay = document.getElementById('birthdayDay');
    if (bdayDay) bdayDay.value = '';
    const bdayMonth = document.getElementById('birthdayMonth');
    if (bdayMonth) bdayMonth.value = '';
    if (PASSWORDLESS_ENABLED) hideLegacyAuthChoices();
}

// Submit initials and login
async function submitLogin() {
    if (PASSWORDLESS_ENABLED) return startPasswordlessAuth(completeProfileLogin, onPasswordlessSignedOut);
    return submitProfileLogin(completeProfileLogin);
}

function clearDeviceSessionState() {
    try {
        localStorage.removeItem('fluencyPreferredLanguageV1');
        localStorage.removeItem('fluency_language_profile_v1|guest');
        localStorage.removeItem('fluency_known_languages_v1');
        localStorage.removeItem('fluency_last_study_session_v1');
        localStorage.removeItem('fluency_last_study_session_v1:user:guest');
        sessionStorage.removeItem('fluency_resume_prompt_seen_v1');
        sessionStorage.removeItem('fluencyPendingSpeechLanguage');
        sessionStorage.removeItem('flashcardGuestSession');
    } catch (_) {}
    document.getElementById('resumeLastSetCard')?.remove();
}

async function completeProfileLogin(user) {
    sessionStorage.removeItem('flashcardGuestSession');
    currentUser = user;
    if (user.isNew) {
        clearDeviceSessionState();
        document.querySelectorAll('.lang-tab').forEach(t => t.classList.remove('active'));
    }
    window.applyGlobalStudyDefaults?.();
    localStorage.setItem('flashcardUser', JSON.stringify(currentUser));
    showUserInfo();
    const activeLangTab = document.querySelector('.lang-tab.active');
    const hasEstablishedLanguage = Boolean(
        !user.isNew
        && (localStorage.getItem('fluencyPreferredLanguageV1') || activeLangTab)
    );
    if (!hasEstablishedLanguage) {
        Promise.resolve().then(() => {
            if (currentUser !== user) return;
            const step1 = document.getElementById('step1');
            if (!step1?.classList.contains('language-summary-active')) {
                window.showLanguagePicker?.(config.languages, { fromMainScreen: true });
            }
        });
    } else {
        setTimeout(_openFirstRunTutorialUnlessLinked, 250);
    }

    // Apply the local cache synchronously, but never hold successful sign-in
    // behind a remote progress or playlist request. Fresh sign-in must close
    // the same surface as a restored session.
    const progressRefresh = loadUserProgressFromSheet();
    hideAuthModal();
    _markAuthReady();
    progressRefresh.then(changed => {
        if (currentUser !== user || !changed) return;
        window.bumpProgressEpoch?.();
        const studying = !document.getElementById('appContent')?.classList.contains('hidden');
        if (!studying && selectedLanguage && selectedLevel) return window.refreshSetupAfterProgress?.();
    }).catch(error => console.warn('Progress sync deferred after login:', error));
    setTimeout(() => window.checkAndShowAdminUpdateModal?.(), 300);
    // Artist/song metadata may have initialized while the login modal was
    // still open, when there was no named user to reconcile. Complete the
    // per-user playlist restore now that identity is known.
    window.reconcileRemoteSongSet?.().catch(error => {
        console.warn('Song-set sync deferred after login:', error);
    });
    if (window.playlistLiveActive?.()) {
        const liveDeck = window.playlistLiveDeck?.();
        if (liveDeck) {
            window.savePlaylistLiveDeckToServer?.(liveDeck).catch(error => {
                console.warn('Live playlist deck save deferred after login:', error);
            });
        }
    }
}

// Settings → Account. The password is the one submitLogin keeps on this
// device (`auth_pwd_<initials>`): it guards against someone else on the
// device studying under your initials and overwriting your progress, not
// against an attacker, so the owner may read and change it here.
function devicePasswordKey() {
    return currentUser && !currentUser.isGuest ? `auth_pwd_${currentUser.initials}` : null;
}

function formatBirthdayDisplay(value) {
    if (!value) return '';
    const parts = String(value).split('-');
    if (parts.length !== 2) return String(value);
    const m = parseInt(parts[0], 10);
    const d = parseInt(parts[1], 10);
    const months = ['January','February','March','April','May','June','July','August','September','October','November','December'];
    if (m >= 1 && m <= 12 && d >= 1 && d <= 31) {
        return `${d} ${months[m - 1]}`;
    }
    return String(value);
}

function renderAccountPanel() {
    const named = Boolean(currentUser && !currentUser.isGuest);
    const badge = document.getElementById('accountUserBadge');
    if (badge) {
        badge.textContent = named ? String(currentUser.username || currentUser.initials || '?').trim().charAt(0).toUpperCase() : '?';
        badge.classList.toggle('is-guest', !named);
    }
    const name = document.getElementById('accountProfileName');
    if (name) {
        name.textContent = named ? (currentUser.username || currentUser.initials) : 'Guest';
        name.hidden = false;
        name.style.display = '';
    }
    const note = document.getElementById('accountProfileNote');
    if (note) note.textContent = named ? 'Progress syncs across devices' : 'Progress is not saved';

    const row = document.getElementById('accountPasswordRow');
    if (!row) return;
    row.hidden = !named || currentUser?.authProvider === 'clerk';
    if (row.hidden) return;
    const birthday = currentUser?.birthday || '';
    const input = document.getElementById('accountPasswordInput');
    if (document.activeElement === input) input.blur();
    input.value = birthday ? formatBirthdayDisplay(birthday) : '';
    input.placeholder = 'Not set';
    input.readOnly = true;
    input.classList.remove('is-concealed');
    const show = document.getElementById('accountPasswordShowBtn');
    if (show) {
        show.textContent = birthday ? 'Change' : 'Set';
        show.hidden = false;
    }
    const save = document.getElementById('accountPasswordSaveBtn');
    if (save) save.hidden = true;
    const status = document.getElementById('accountPasswordStatus');
    if (status) {
        status.textContent = birthday
            ? 'Used as an optional password to protect your account'
            : 'You have the option to set a birthday as an optional password to protect your account';
    }
}

function wireAccountPassword() {
    const input = document.getElementById('accountPasswordInput');
    const show = document.getElementById('accountPasswordShowBtn');
    const save = document.getElementById('accountPasswordSaveBtn');
    const status = document.getElementById('accountPasswordStatus');
    const pickerFields = document.getElementById('accountBirthdayPickerFields');
    const daySelect = document.getElementById('accountBirthdayDay');
    const monthSelect = document.getElementById('accountBirthdayMonth');
    if (!input || !show) return;

    let isEditing = false;
    const setEditing = (editing) => {
        isEditing = editing;
        if (pickerFields) pickerFields.hidden = !editing;
        input.hidden = editing;
        if (save) save.hidden = !editing;
        show.textContent = editing ? 'Cancel' : (currentUser?.birthday ? 'Change' : 'Set');
        if (editing && daySelect && monthSelect) {
            const bday = currentUser?.birthday || '';
            if (bday && bday.includes('-')) {
                const [m, d] = bday.split('-');
                monthSelect.value = String(parseInt(m, 10));
                daySelect.value = String(parseInt(d, 10));
            } else {
                daySelect.value = '';
                monthSelect.value = '';
            }
            if (status) status.textContent = 'Choose your birthday as an optional password to protect your account';
        } else if (!editing) {
            renderAccountPanel();
        }
    };

    show.addEventListener('click', () => {
        if (!currentUser) return;
        setEditing(!isEditing);
    });

    if (save) {
        save.addEventListener('click', () => {
            if (!currentUser) return;
            const d = parseInt(daySelect?.value, 10);
            const m = parseInt(monthSelect?.value, 10);
            if (!daySelect?.value && !monthSelect?.value) {
                currentUser.birthday = '';
            } else if (d >= 1 && d <= 31 && m >= 1 && m <= 12) {
                currentUser.birthday = `${String(m).padStart(2, '0')}-${String(d).padStart(2, '0')}`;
            } else {
                if (status) status.textContent = 'Please choose both a day and month.';
                return;
            }
            localStorage.setItem('flashcardUser', JSON.stringify(currentUser));
            setEditing(false);
            renderAccountPanel();
            if (status) {
                status.textContent = currentUser.birthday
                    ? 'Birthday updated! Used as an optional password to protect your account.'
                    : 'Birthday removed. You have the option to set one anytime.';
            }
        });
    }
}

// Logout handler. Guests skip the confirm (nothing to lose); named users get
// the prompt since they might have unsaved progress in flight.
async function logout() {
    if (PASSWORDLESS_ENABLED) {
        if (window.authLogoutInFlight) return;
        window.authLogoutInFlight = true;
        // Cover account cleanup before its first await. Provider signed-out
        // callbacks must not expose a half-mounted login panel before reload.
        document.body.classList.remove('auth-active');
        document.body.classList.add('auth-logging-out');
        window.showAppLoading?.('Signing out', 'Returning to sign-in…', true);
        await window.flushQueue?.().catch(() => {});
        if (currentUser?.initials) {
            localStorage.removeItem(`progress_cache_${currentUser.initials}`);
            localStorage.removeItem(`progress_cache_${getIsolatedSyncUser(currentUser.initials)}`);
        }
        localStorage.removeItem('flashcardUser');
        clearDeviceSessionState();
        currentUser = null;
        showUserInfo();
        await signOutPasswordless();
        window.location.reload();
        return;
    }
    const isGuest = currentUser?.isGuest;
    if (!isGuest && !confirm('Are you sure you want to logout? Unsaved progress will be lost.')) {
        return;
    }

    if (currentUser?.initials) {
        localStorage.removeItem(`progress_cache_${currentUser.initials}`);
        localStorage.removeItem(`progress_cache_${getIsolatedSyncUser(currentUser.initials)}`);
    }
    localStorage.removeItem('flashcardUser');
    clearDeviceSessionState();
    currentUser = null;
    window.applyGlobalStudyDefaults?.();
    progressData = {}; window.bumpProgressEpoch?.();
    itemProgressData = {}; window.bumpProgressEpoch?.();
    levelEstimates = {};
    document.getElementById('userInfo').classList.add('hidden');

    // Reset app state
    flashcards = [];
    currentIndex = 0;
    stats = {
        studied: new Set(),
        correct: 0,
        incorrect: 0,
        total: 0,
        cardStats: {}
    };

    // Hide app content and show auth modal
    document.getElementById('appContent').classList.add('hidden');
    showAuthModal();
}

// ========== ID MIGRATION (one-time) ==========

// Migrate localStorage progress from old rank-based IDs to new md5-based IDs
async function migrateLocalStorageIds() {
    if (localStorage.getItem('id_migration_v1') === 'done') return;

    const key = 'flashcard_progress_guest';
    const guestProgress = JSON.parse(localStorage.getItem(key) || '{}');
    if (Object.keys(guestProgress).length === 0) {
        localStorage.setItem('id_migration_v1', 'done');
        return;
    }

    // Determine which languages have progress (from the 2-char prefix of fullIds)
    const langMap = { es: 'Spanish', fi: 'Finnish', sv: 'Swedish', it: 'Italian', nl: 'Dutch', pl: 'Polish' };
    const neededLangs = new Set();
    for (const fullId of Object.keys(guestProgress)) {
        const prefix = fullId.slice(0, 2);
        if (langMap[prefix]) neededLangs.add(prefix);
    }

    // Load migration mappings for needed languages
    const mappings = {};
    for (const prefix of neededLangs) {
        const lang = langMap[prefix];
        try {
            const resp = await fetch(`Data/${lang}/id_migration.json`);
            if (resp.ok) mappings[prefix] = await resp.json();
        } catch (e) {
            console.warn(`Could not load ID migration for ${lang}:`, e);
        }
    }

    // Remap keys
    const migrated = {};
    let remapped = 0;
    for (const [fullId, data] of Object.entries(guestProgress)) {
        const prefix = fullId.slice(0, 2);
        const mode = fullId[2];
        const oldHex = fullId.slice(3);
        const mapping = mappings[prefix];

        if (mapping && mode === '0' && mapping[oldHex]) {
            const newFullId = prefix + mode + mapping[oldHex];
            migrated[newFullId] = data;
            remapped++;
        } else {
            migrated[fullId] = data; // keep as-is (artist mode IDs unchanged, or no mapping)
        }
    }

    if (remapped > 0) {
        localStorage.setItem(key, JSON.stringify(migrated));
        console.log(`Migrated ${remapped} localStorage progress IDs`);
    }
    localStorage.setItem('id_migration_v1', 'done');
}

// Migrate localStorage progress through Data/{Lang}/id_migration.json.
//
// v3 carries speech mode from word|lemma card IDs to surface-form IDs. The map
// is composed, so a learner still sitting on a pre-clitic ID resolves to its
// final surface ID in this single lookup.
//
// This is NOT idempotent and the flag version is what enforces once-only. Some
// new surface IDs are themselves old word|lemma IDs, so a second pass would
// remap an already-migrated card onto a different word. Never reuse a flag
// version to re-run a migration; add the next one.
async function migrateLocalStorageIdsV2() {
    if (localStorage.getItem('id_migration_v3') === 'done') return;

    const key = 'flashcard_progress_guest';
    const guestProgress = JSON.parse(localStorage.getItem(key) || '{}');
    if (Object.keys(guestProgress).length === 0) {
        localStorage.setItem('id_migration_v3', 'done');
        return;
    }

    const langMap = { es: 'Spanish', fi: 'Finnish', sv: 'Swedish', it: 'Italian', nl: 'Dutch', pl: 'Polish' };
    const neededLangs = new Set();
    for (const fullId of Object.keys(guestProgress)) {
        const prefix = fullId.slice(0, 2);
        if (langMap[prefix]) neededLangs.add(prefix);
    }

    const mappings = {};
    for (const prefix of neededLangs) {
        const lang = langMap[prefix];
        try {
            const resp = await fetch(`Data/${lang}/id_migration.json`);
            if (resp.ok) mappings[prefix] = await resp.json();
        } catch (e) {
            console.warn(`Could not load ID migration for ${lang}:`, e);
        }
    }

    const migrated = {};
    let remapped = 0;
    for (const [fullId, data] of Object.entries(guestProgress)) {
        const prefix = fullId.slice(0, 2);
        const mode = fullId[2];
        const oldHex = fullId.slice(3);
        const mapping = mappings[prefix];

        if (mapping && mode === '0' && mapping[oldHex]) {
            const newFullId = prefix + mode + mapping[oldHex];
            migrated[newFullId] = data;
            remapped++;
        } else {
            migrated[fullId] = data;
        }
    }

    if (remapped > 0) {
        localStorage.setItem(key, JSON.stringify(migrated));
        console.log(`Migrated ${remapped} localStorage progress IDs (4-char → 6-char)`);
    }
    localStorage.setItem('id_migration_v3', 'done');
}

// ========== GOOGLE SHEETS INTEGRATION ==========

function getProgressMode() {
    return activeArtist ? 'artist' : 'normal';
}

function getProgressSheetName() {
    if (progressBackendSchemaVersion >= 4) return 'Progress';
    return activeArtist ? 'Lyrics' : 'UserProgress';
}

function getProgressSource(options = {}) {
    const mode = options.mode || getProgressMode();
    if (mode !== 'artist' && mode !== 'lyrics') return 'speech';
    if (options.source) return String(options.source);
    const slugs = (options.artistSlugs || window._selectedArtistSlugs || [])
        .filter(Boolean)
        .map(String)
        .sort();
    if (slugs.length > 0) return slugs.join('+');
    if (options.artistSlug || window._urlArtistSlug) {
        return String(options.artistSlug || window._urlArtistSlug);
    }
    return String(activeArtist?.name || 'artist')
        .toLowerCase()
        .replace(/[^a-z0-9]+/g, '-')
        .replace(/^-|-$/g, '');
}

// Stable suggestion scope. Word and sense progress remains shared across
// artist catalogues as before; only routing metadata needs the source slug.
function getProgressScopeKey(options = {}) {
    const rawMode = options.mode || getProgressMode();
    const mode = rawMode === 'lyrics' ? 'artist' : rawMode === 'speech' ? 'normal' : rawMode;
    const language = options.language || selectedLanguage || 'unknown';
    const source = mode === 'artist' ? getProgressSource({ ...options, mode }) : 'speech';
    return `${mode}|${language}|${source}`;
}

const PROGRESS_CACHE_DELAY_MS = 750;
let progressCacheTimer = null;
let progressCacheIdleHandle = null;
let progressCacheWrite = Promise.resolve();

// Progress changes rarely between sessions, but the client refetched all of it
// on every startup — ~9,500 rows and 1.4MB — to re-learn what it already had
// cached. These track how current the cache is so a startup can ask only for
// what changed. A periodic full sync still runs, because a delta cannot report
// rows that were deleted.
let progressSyncVersion = '';
let progressLastFullSyncAt = 0;
const FULL_SYNC_INTERVAL_MS = 3 * 24 * 60 * 60 * 1000;

function flushProgressCache() {
    if (progressCacheTimer !== null) clearTimeout(progressCacheTimer);
    if (progressCacheIdleHandle !== null && window.cancelIdleCallback) {
        window.cancelIdleCallback(progressCacheIdleHandle);
    }
    progressCacheTimer = null;
    progressCacheIdleHandle = null;
    if (!currentUser || currentUser.isGuest) return;
    const effectiveUser = getIsolatedSyncUser(currentUser.initials);
    const record = {
        key: `progress|${effectiveUser}`,
        progress: progressData,
        itemProgress: itemProgressData,
        estimates: levelEstimates,
        backendSchema: progressBackendSchemaVersion >= 4 ? progressBackendSchemaVersion : 0,
        // Watermark for incremental sync: the newest updated_at the backend has
        // sent us. Next startup asks only for rows changed after this.
        syncVersion: progressSyncVersion,
        lastFullSyncAt: progressLastFullSyncAt,
        updatedAt: Date.now()
    };
    // Serialize once per answer burst, outside the tap/swipe handler. IndexedDB
    // writes are kept in order so an earlier slow transaction cannot overwrite
    // a newer snapshot.
    progressCacheWrite = progressCacheWrite
        .then(() => dbPut('localState', record))
        .catch(error => console.warn('Could not persist local progress to IndexedDB', error));
    try {
        localStorage.setItem(`progress_cache_${effectiveUser}`, JSON.stringify({
            progress: record.progress, itemProgress: record.itemProgress,
            estimates: record.estimates,
            backendSchema: record.backendSchema,
            syncVersion: record.syncVersion, lastFullSyncAt: record.lastFullSyncAt
        }));
    } catch (_) {
        // Cache is best-effort; the durable queue still owns remote writes.
    }
}

function cacheProgressLocally({ immediate = false } = {}) {
    if (!currentUser || currentUser.isGuest) return;
    if (immediate) {
        flushProgressCache();
        return;
    }
    if (progressCacheTimer !== null || progressCacheIdleHandle !== null) return;
    if (window.requestIdleCallback) {
        progressCacheIdleHandle = window.requestIdleCallback(
            () => flushProgressCache(),
            { timeout: PROGRESS_CACHE_DELAY_MS }
        );
    } else {
        progressCacheTimer = setTimeout(flushProgressCache, PROGRESS_CACHE_DELAY_MS);
    }
}

window.addEventListener('pagehide', flushProgressCache);
document.addEventListener('visibilitychange', () => {
    if (document.visibilityState === 'hidden') flushProgressCache();
});

// Setup renders immediately from the local cache while Sheets refreshes in
// the background. Compare the actual UI-driving state after that refresh — a
// row-count comparison misses the common case where an existing card changes
// from unseen/review to known and leaves the set picker stale.
function getProgressUiFingerprint() {
    return JSON.stringify({
        progress: progressData || {},
        itemProgress: itemProgressData || {},
        estimates: levelEstimates || {}
    });
}

function setProgressReadFailed(failed) {
    const button = document.getElementById('progressReadRetry');
    if (!button) return;
    button.hidden = !failed;
    button.classList.toggle('hidden', !failed);
    button.onclick = async () => {
        button.disabled = true;
        try {
            const changed = await loadUserProgressFromSheet();
            if (changed) await window.refreshSetupAfterProgress?.();
        } finally {
            button.disabled = false;
        }
    };
}

async function detectProgressBackendSchema() {
    try {
        const { data: result } = await readJsonWithTimeout(GOOGLE_SCRIPT_URL, {
            method: 'POST',
            body: JSON.stringify({ action: 'capabilities' })
        }, 5000);
        const version = Number(result?.data?.schemaVersion) || 0;
        progressBackendSchemaVersion = result?.success && version >= 4 ? version : 3;
    } catch (_) {
        progressBackendSchemaVersion = 3;
    }
    return progressBackendSchemaVersion;
}

async function loadLegacyProgress(cacheKey, cached) {
    const effectiveUser = getIsolatedSyncUser(currentUser.initials);
    const fetchSheet = sheet => readJsonWithTimeout(GOOGLE_SCRIPT_URL, {
        method: 'POST',
        body: JSON.stringify({ action: 'load', user: effectiveUser, sheet })
    }, 12000).then(({ data }) => data).catch(() => null);
    const [normalResult, artistResult, itemResult] = await Promise.all([
        fetchSheet('UserProgress'),
        fetchSheet('Lyrics'),
        readJsonWithTimeout(GOOGLE_SCRIPT_URL, {
            method: 'POST',
            body: JSON.stringify({ action: 'loadItems', user: effectiveUser })
        }, 12000).then(({ data }) => data).catch(() => null)
    ]);
    if (!normalResult?.success || !artistResult?.success) {
        setProgressReadFailed(true);
        window.markProgressLoaded?.();
        applyPendingProgressOverlay(progressData);
        applyPendingItemProgressOverlay(itemProgressData);
        applyPendingMetaProgressOverlay(levelEstimates);
        return false;
    }

    setProgressReadFailed(!normalResult?.success || !artistResult?.success || !itemResult?.success);
    const previousUiState = getProgressUiFingerprint();
    progressData = {}; window.bumpProgressEpoch?.();
    const mergeWords = result => {
        if (!result?.success || !Array.isArray(result.data?.progress)) return;
        result.data.progress.forEach(item => {
            progressData[item.wordId] = {
                word: item.word,
                language: item.language,
                correct: item.correct,
                wrong: item.wrong,
                lastCorrect: item.lastCorrect,
                lastWrong: item.lastWrong,
                lastSeen: item.lastSeen,
                srsStage: item.srsStage,
                    migrationReviewAt: item.migrationReviewAt || null
            };
        });
    };
    mergeWords(normalResult);
    mergeWords(artistResult);
    if (itemResult?.success && Array.isArray(itemResult.data?.items)) {
        itemProgressData = {}; window.bumpProgressEpoch?.();
        itemResult.data.items.forEach(item => {
            itemProgressData[item.itemId] = { ...item };
        });
    }
    levelEstimates = {
        ...(artistResult?.data?.levelEstimates || {}),
        ...(normalResult?.data?.levelEstimates || {})
    };
    applyPendingProgressOverlay(progressData);
    applyPendingItemProgressOverlay(itemProgressData);
    applyPendingMetaProgressOverlay(levelEstimates);
    updateIncorrectButtonVisibility();
    updateTotalStatsButtonVisibility();
    cacheProgressLocally();
    return getProgressUiFingerprint() !== previousUiState || !cached;
}

// Load unified Google Sheets progress while retaining cross-mode sharing.
// Loads from localStorage cache first (instant), then refreshes from Sheets.
// Returns true if the Sheets fetch brought different data than the cache.
// The refresh in flight, if any. Setup is drawn from the cached progress while
// this runs, so a set can look unfinished on screen and be finished in the
// progress that arrives a few seconds later (answers made on another device).
// Starting a set waits for it — see progressRefreshSettled().
let progressRefreshInFlight = null;

function loadUserProgressFromSheet() {
    const run = loadUserProgressFromSheetNow();
    progressRefreshInFlight = run;
    run.finally(() => {
        window.markProgressLoaded?.();
        if (progressRefreshInFlight === run) progressRefreshInFlight = null;
    }).catch(() => {});
    return run;
}

// Resolves once no progress refresh is running, or after capMs, whichever is
// first. Never rejects: a failed refresh leaves the cached progress in force.
function progressRefreshSettled(capMs = 5000) {
    if (!progressRefreshInFlight) return Promise.resolve();
    return Promise.race([
        progressRefreshInFlight.catch(() => {}),
        new Promise(resolve => setTimeout(resolve, capMs))
    ]);
}
window.progressRefreshSettled = progressRefreshSettled;

async function loadUserProgressFromSheetNow() {
    if (!currentUser || currentUser.isGuest) return false;

    const applyCachedProgress = raw => {
        if (!raw) return false;
        try {
            const { progress, itemProgress, estimates, backendSchema,
                    syncVersion, lastFullSyncAt } =
                typeof raw === 'string' ? JSON.parse(raw) : raw;
            progressSyncVersion = typeof syncVersion === 'string' ? syncVersion : '';
            progressLastFullSyncAt = Number(lastFullSyncAt) || 0;
            progressData = progress || {}; window.bumpProgressEpoch?.();
            itemProgressData = itemProgress || {}; window.bumpProgressEpoch?.();
            levelEstimates = estimates || {};
            progressBackendSchemaVersion = Number(backendSchema) >= 4 ? Number(backendSchema) : 0;
            // The cache is the learner's real progress, not a placeholder —
            // enough to lay out the setup screen correctly while the Sheets
            // refresh runs behind it.
            window.markProgressLoaded?.();
            updateIncorrectButtonVisibility();
            updateTotalStatsButtonVisibility();
            return true;
        } catch (error) {
            console.warn('Failed to parse progress cache:', error);
            return false;
        }
    };

    // 1. Apply localStorage synchronously before the first await so initial
    // setup routing cannot briefly choose Level 1 from empty progress. Then
    // prefer the durable IndexedDB snapshot when it becomes available.
    const effectiveUser = getIsolatedSyncUser(currentUser.initials);
    const cacheKey = `progress_cache_${effectiveUser}`;
    let cached = localStorage.getItem(cacheKey);
    if (applyCachedProgress(cached)) {
        console.log(`Loaded ${Object.keys(progressData).length} cached card entries and ${Object.keys(itemProgressData).length} knowledge items`);
    }
    try {
        const durable = await dbGet('localState', `progress|${effectiveUser}`);
        if (durable) {
            cached = JSON.stringify(durable);
            applyCachedProgress(durable);
        }
    } catch (_) {}

    // Authentication and local studying never wait for the optional remote
    // endpoint. loadSecrets() may still be resolving, or the app may have
    // launched entirely offline; the durable queue will reconcile later.
    if (!GOOGLE_SCRIPT_URL) return false;

    // Confirm v4 before addressing Progress directly. Cached/older clients
    // continue through the legacy names, which v4 maps into Progress; this
    // prevents a half-deployed frontend from creating a stray Progress tab on
    // the still-live v3 backend.
    await detectProgressBackendSchema();
    if (progressBackendSchemaVersion < 4) {
        return loadLegacyProgress(cacheKey, cached);
    }

    // 2. Fetch fresh data from the single Progress tab. Word IDs still carry
    // the normal/artist bit, so one all-mode load preserves the old sharing.
    try {
        // Ask only for what changed when the cache carries a watermark. A
        // delta cannot report deletions, so a full sync still runs
        // periodically and whenever there is nothing cached to build on.
        const fullSyncDue = !progressSyncVersion
            || (Date.now() - progressLastFullSyncAt) > FULL_SYNC_INTERVAL_MS;
        const since = fullSyncDue ? null : progressSyncVersion;
        const [progressResult, itemResult] = await Promise.all([
            readJsonWithTimeout(GOOGLE_SCRIPT_URL, {
                method: 'POST',
                body: JSON.stringify({
                    action: 'load',
                    sheet: 'Progress',
                    mode: 'all',
                    user: effectiveUser,
                    ...(since ? { since } : {})
                })
            }, 12000).then(({ data }) => data).catch(() => null),
            readJsonWithTimeout(GOOGLE_SCRIPT_URL, {
                method: 'POST',
                body: JSON.stringify({
                    action: 'loadItems',
                    sheet: 'Progress',
                    mode: 'all',
                    user: effectiveUser,
                    ...(since ? { since } : {})
                })
            }, 12000).then(({ data }) => data).catch(() => null)
        ]);

        // The unified load failed (offline, or endpoint unreachable). Keep the
        // cached progressData loaded in step 1 rather than wiping it to empty —
        // then overlay any writes still queued locally so freshly-answered
        // offline cards remain visible. Returning false leaves the UI on cache.
        if (!progressResult?.success) {
            setProgressReadFailed(true);
            applyPendingProgressOverlay(progressData);
            applyPendingItemProgressOverlay(itemProgressData);
            applyPendingMetaProgressOverlay(levelEstimates);
            // We have looked. Even a failed fetch settles the question the
            // setup screen is waiting on, and waiting longer will not help.
            window.markProgressLoaded?.();
            updateIncorrectButtonVisibility();
            updateTotalStatsButtonVisibility();
            return false;
        }

        setProgressReadFailed(!itemResult?.success);
        const previousUiState = getProgressUiFingerprint();
        // A delta reply describes only what changed, so the cached rows must
        // survive. Only a full reply is authoritative enough to replace them.
        const gotDelta = progressResult?.data?.delta === true;
        if (!gotDelta) { progressData = {}; window.bumpProgressEpoch?.(); }

        if (progressResult?.success && Array.isArray(progressResult.data?.progress)) {
            progressResult.data.progress.forEach(item => {
                progressData[item.wordId] = {
                    word: item.word,
                    language: item.language,
                    correct: item.correct,
                    wrong: item.wrong,
                    lastCorrect: item.lastCorrect,
                    lastWrong: item.lastWrong,
                    lastSeen: item.lastSeen,
                    srsStage: item.srsStage,
                    migrationReviewAt: item.migrationReviewAt || null
                };
            });
            console.log(`Loaded ${progressResult.data.progress.length} unified card progress rows`);
        }

        if (itemResult?.success && Array.isArray(itemResult.data?.items)) {
            if (itemResult.data.delta !== true) {
                itemProgressData = {}; window.bumpProgressEpoch?.();
            }
            itemResult.data.items.forEach(item => {
                itemProgressData[item.itemId] = {
                    itemId: item.itemId,
                    parentWordId: item.parentWordId,
                    itemType: item.itemType,
                    label: item.label,
                    language: item.language,
                    correct: item.correct,
                    wrong: item.wrong,
                    lastCorrect: item.lastCorrect,
                    lastWrong: item.lastWrong,
                    lastSeen: item.lastSeen,
                    schemaVersion: item.schemaVersion || 1,
                    srsStage: item.srsStage,
                    migrationReviewAt: item.migrationReviewAt || null
                };
            });
            console.log(`Loaded ${Object.keys(itemProgressData).length} granular knowledge items`);
        }

        levelEstimates = progressResult?.success
            ? (progressResult.data?.levelEstimates || {})
            : levelEstimates;
        applyRemoteFastTrack(progressResult.data?.meta, { full: !gotDelta });
        window.applyRemoteLanguageProfile?.(progressResult.data?.meta, { full: !gotDelta });
        window.applyRemotePinnedMeanings?.(progressResult.data?.meta);

        // Overlay any still-queued (un-synced) local writes on top of the
        // freshly-loaded sheet data — those answers are newer than what Sheets
        // knows, so a reconnect reload must not visually regress them.
        applyPendingProgressOverlay(progressData);
        applyPendingItemProgressOverlay(itemProgressData);
        applyPendingMetaProgressOverlay(levelEstimates);

        updateIncorrectButtonVisibility();
        updateTotalStatsButtonVisibility();

        // Advance the watermark to the newest row either reply carried. On a
        // full sync also stamp the time, so the next periodic full sync — the
        // only thing that can notice a deleted row — is scheduled from here.
        const newest = [progressResult?.data?.version, itemResult?.data?.version]
            .filter(v => typeof v === 'string' && v)
            .reduce((a, b) => (a > b ? a : b), progressSyncVersion || '');
        // A timed-out half must be fetched again; do not skip its rows on retry.
        if (itemResult?.success) {
            if (newest) progressSyncVersion = newest;
            if (!gotDelta) progressLastFullSyncAt = Date.now();
        }
        window.markProgressLoaded?.();
        window.bumpProgressEpoch?.();

        // 3. Update cache
        cacheProgressLocally({ immediate: true });

        // Existing rows change far more often than rows are added. Returning
        // the full state comparison lets setup refresh its Known/Review/Unseen
        // segments before a learner opens a set that has become complete.
        return getProgressUiFingerprint() !== previousUiState || !cached;
    } catch (error) {
        console.error('Failed to load progress from Google Sheets:', error);
        setProgressReadFailed(true);
        applyPendingProgressOverlay(progressData);
        applyPendingItemProgressOverlay(itemProgressData);
        applyPendingMetaProgressOverlay(levelEstimates);
        // A thrown fetch settles the question too. Leaving the setup screen
        // waiting on a promise that can never resolve is worse than laying it
        // out from whatever cache we have.
        window.markProgressLoaded?.();
        // Continue with cached data if available
        return false;
    }
}

// Save the level estimate as metadata in the unified Progress tab.
async function saveLevelEstimateToSheet(rank) {
    if (!currentUser || currentUser.isGuest) return;
    const effectiveUser = getIsolatedSyncUser(currentUser.initials);
    const language = selectedLanguage;
    const unified = progressBackendSchemaVersion >= 4;
    sendOrQueue(unified ? {
        action: 'saveMeta',
        sheet: 'Progress',
        user: effectiveUser,
        metaKey: 'level-estimate',
        metaId: language,
        mode: 'normal',
        source: 'speech',
        language,
        value: rank,
        lastSeen: new Date().toISOString()
    } : {
        action: 'save',
        sheet: getProgressSheetName(),
        user: effectiveUser,
        word: '_LEVEL_ESTIMATE_',
        wordId: rank,
        language
    }, `meta|level-estimate|${effectiveUser}|${language}`);
}

// Save progress for a single word to Google Sheets
async function saveWordProgress(card, isCorrect) {
    const wordId = card.fullId; // composite ID: {lang}{mode}{hex} e.g. "es00001", "es10039"
    const word = card.targetWord;
    const language = selectedLanguage;
    const timestamp = new Date().toISOString();

    // Guest sessions are ephemeral — nothing to persist.
    if (!currentUser || currentUser.isGuest) return;
    const effectiveUser = getIsolatedSyncUser(currentUser.initials);

    // Update local progress data
    if (!progressData[wordId]) {
        progressData[wordId] = {
            word: word,
            language: language,
            correct: 0,
            wrong: 0,
            lastCorrect: null,
            lastWrong: null,
            lastSeen: null,
            srsStage: 0
        };
    }

    progressData[wordId].srsStage = advanceSrsStage(progressData[wordId], isCorrect);
    delete progressData[wordId].migrationReviewAt;
    if (isCorrect) {
        progressData[wordId].correct++;
        progressData[wordId].lastCorrect = timestamp;
    } else {
        progressData[wordId].wrong++;
        progressData[wordId].lastWrong = timestamp;
    }
    progressData[wordId].lastSeen = timestamp;
    progressData[wordId].word = word;
    progressData[wordId].language = language;
    // Invalidate the progress/knowledge indexes: they no longer count keys to
    // detect this, so an answer has to say so.
    window.bumpProgressEpoch?.();

    // Coalesce whole-state cache snapshots outside the answer interaction.
    // The per-answer sync operation below is still durably queued immediately.
    cacheProgressLocally();

    // Save to Google Sheets via the offline-durable queue. Write-through when
    // online (same latency as before); enqueued and retried when offline or on
    // a transient failure. De-dupe key keeps only the latest cumulative state
    // per word+mode in the queue.
    const mode = getProgressMode();
    const sheet = getProgressSheetName();
    sendOrQueue({
        action: 'save',
        sheet,
        mode,
        user: effectiveUser,
        word: word,
        language: language,
        wordId: wordId,
        correct: progressData[wordId].correct,
        wrong: progressData[wordId].wrong,
        lastCorrect: progressData[wordId].lastCorrect,
        lastWrong: progressData[wordId].lastWrong,
        lastSeen: progressData[wordId].lastSeen,
        srsStage: progressData[wordId].srsStage
    }, `save|${sheet}|${mode}|${wordId}`);
}

// Flag a word as having erroneous translation/data — debugging-only path.
// Routes to a separate FlaggedWords sheet (auto-created by GAS) so it doesn't
// pollute Progress.
//
// `fields` (optional) carries the structured flag payload: stable
// target/category keys plus the individual sense/example attributes that used
// to be readable only by parsing the rendered report text. The current backend writes
// each into its own column.
//
// Deploy-order safety: `word` keeps carrying the rendered report exactly as
// before, so an un-redeployed v1 backend still records the full flag with
// nothing lost. The structured backend prefers `wordText` for the Word column and
// treats `word` as the Report blob. Same for lastCorrect/lastWrong, which v1
// overloads as fieldPath and flag timestamp.
async function flagWord(card, fieldPath, fieldValue, fields = null) {
    if (!currentUser) {
        console.warn('flagWord skipped: no user logged in');
        return false;
    }
    if (!canUserFlag(currentUser)) {
        console.warn('flagWord skipped: flagging is unavailable for this account');
        return false;
    }
    const baseId = card.fullId;
    const wordId = fieldPath ? `${baseId}#${fieldPath}` : baseId;
    const word = (fieldValue !== undefined && fieldValue !== null && fieldValue !== '')
        ? String(fieldValue)
        : card.targetWord;
    const language = selectedLanguage;
    const timestamp = new Date().toISOString();
    const flagId = createFlagId();
    const release = window._activeReleaseProvenance || {};
    const languageConfig = config?.languages?.[selectedLanguage] || {};
    let provenance = {};
    try {
        provenance = fields?.provenanceJson ? JSON.parse(fields.provenanceJson) : {};
    } catch (_) {
        provenance = {};
    }
    provenance = {
        schemaVersion: 1,
        mode: activeArtist ? 'lyrics' : 'speech',
        source: activeArtist
            ? String(window._urlArtistSlug || getProgressSource() || activeArtist?.slug || '')
            : 'speech',
        language,
        releaseId: release.releaseId || release.release_id || card.release_id || '',
        artistSlugs: (window._activeSongSetArtistSlugs || window._selectedArtistSlugs || []).slice(),
        assets: {
            index: languageConfig.indexPath || languageConfig.dataPath || '',
            examples: languageConfig.examplesPath || '',
            master: languageConfig.masterPath || ''
        },
        layers: release.layers || {},
        ...provenance
    };
    const structuredFields = {
        mode: provenance.mode,
        source: provenance.source,
        releaseId: provenance.releaseId || '',
        runId: provenance.runId || '',
        runTimestamp: provenance.runTimestamp || '',
        promptId: provenance.promptId || '',
        model: provenance.model || '',
        assignmentMethod: provenance.assignmentMethod || '',
        ...(fields || {}),
        schemaVersion: 4,
        flagId,
        clientBuild: currentClientBuild(),
        status: IS_STAGING ? 'Staging' : 'Open',
        environment: IS_STAGING ? 'staging' : 'production',
        provenanceJson: JSON.stringify(provenance).slice(0, 20000)
    };

    // Route through the offline-durable queue so flags raised offline aren't
    // lost. The event ID is also the queue de-dupe key: retries of this gesture
    // collapse safely, while a later flag on the same card remains separate.
    const effectiveUser = getIsolatedSyncUser(currentUser.initials);
    await sendOrQueue({
        action: 'save',
        sheet: 'FlaggedWords',
        user: effectiveUser,
        word: word,
        language: language,
        wordId: wordId,
        lastCorrect: fieldPath || '',
        lastWrong: timestamp,
        // Flag schema v4 structured columns. Explicit fallbacks keep the row
        // populated when a caller has not been migrated to pass `fields`.
        ...structuredFields,
        wordText: structuredFields.wordText || card.targetWord || '',
        cardId: structuredFields.cardId || baseId || '',
        fieldPath: fieldPath || '',
        flaggedAt: timestamp,
        report: fieldValue !== undefined && fieldValue !== null ? String(fieldValue) : ''
    }, `flag|${flagId}`);
    console.log(`Flagged ${word} (${wordId}) for review`);
    return true;
}

// Every About entry inside the app (sidebar, Settings, Help) opens the
// standalone About page in a new tab. It is not part of the app: it loads no
// account, language or deck (about-page.js).
function openAboutPage() {
    window.open(new URL('about.html', window.location.href).href, '_blank', 'noopener');
}

// Setup authentication modal event listeners
function setupAuthEventListeners() {
    const authModal = document.getElementById('authModal');
    if (authModal?.dataset.listenersReady === '1') return;
    if (authModal) authModal.dataset.listenersReady = '1';
    // Guest mode button
    document.getElementById('guestModeBtn').addEventListener('click', enterGuestMode);

    // Login and create mode buttons
    document.getElementById('loginModeBtn')?.addEventListener('click', () => showLoginForm('login'));
    document.getElementById('createAccountBtn')?.addEventListener('click', () => showLoginForm('create'));

    // Login info button: toggle the no-password explanation
    const loginInfoBtn = document.getElementById('loginInfoBtn');
    const loginInfoNote = document.getElementById('loginInfoNote');
    if (loginInfoBtn && loginInfoNote) {
        loginInfoBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            loginInfoNote.classList.toggle('hidden');
        });
    }

    // About is its own page (about.html), opened in a new tab.
    document.getElementById('aboutProjectBtn').addEventListener('click', openAboutPage);

    // Cancel login button
    document.getElementById('cancelLoginBtn').addEventListener('click', hideLoginForm);

    // The sign-in is a real form (so browsers can save it); Continue and
    // Enter both submit it. The inline fallback in index.html stands down.
    window.fluencyAuthHandlersReady = true;
    document.getElementById('loginForm').addEventListener('submit', (event) => {
        event.preventDefault();
        submitLogin();
    });

    // Clear level estimate button
    document.getElementById('clearLevelEstimateRow').addEventListener('click', function() {
        levelEstimates[selectedLanguage] = 0;
        saveLevelEstimateToSheet(0);
        document.getElementById('clearLevelEstimateRow').style.display = 'none';
        renderRangeSelector(); // refresh range mastered states
    });

    // Logout button (now in settings modal)
    document.getElementById('logoutBtn').addEventListener('click', function() {
        hideSettingsModal();
        logout();
    });
    wireAccountPassword();

    // Settings → Account → "About this project" row: About in its own tab.
    document.getElementById('aboutProjectSettingsRow')?.addEventListener('click', openAboutPage);

    // Gear button opens settings modal
    document.getElementById('gearBtn').addEventListener('click', function() {
        showSettingsModal();
    });

    // Settings modal tabs
    const settingsModal = document.getElementById('settingsModal');
    settingsModal.querySelectorAll('.settings-tab').forEach(tab => {
        tab.addEventListener('click', function() {
            showSettingsModalWithTab(this.dataset.tab);
        });
    });

    // Settings modal close button
    document.getElementById('closeSettingsModal').addEventListener('click', hideSettingsModal);

    // Click outside settings modal to close
    settingsModal.addEventListener('click', function(e) {
        if (e.target === this) {
            hideSettingsModal();
        }
    });

    // Total stats modal close button
    document.getElementById('closeTotalStatsModal').addEventListener('click', hideTotalStatsModal);

    // Click outside total stats modal to close
    document.getElementById('totalStatsModal').addEventListener('click', function(e) {
        if (e.target === this) {
            hideTotalStatsModal();
        }
    });
}

window.migrateLocalStorageIds = migrateLocalStorageIds;
window.migrateLocalStorageIdsV2 = migrateLocalStorageIdsV2;
window.loadSecrets = loadSecrets;
window.checkAuthentication = checkAuthentication;
window.showAuthModal = showAuthModal;
window.showUserInfo = showUserInfo;
window.hideAuthModal = hideAuthModal;
window.showUserInfo = showUserInfo;
window.enterGuestMode = enterGuestMode;
window.showLoginForm = showLoginForm;
window.openAboutPage = openAboutPage;
window.hideLoginForm = hideLoginForm;
window.submitLogin = submitLogin;
window.logout = logout;
window.renderAccountPanel = renderAccountPanel;
window.loadUserProgressFromSheet = loadUserProgressFromSheet;
window.getProgressMode = getProgressMode;
window.getProgressSheetName = getProgressSheetName;
window.getProgressSource = getProgressSource;
window.getProgressScopeKey = getProgressScopeKey;
window.cacheProgressLocally = cacheProgressLocally;
window.flushProgressCache = flushProgressCache;
window.saveLevelEstimateToSheet = saveLevelEstimateToSheet;
window.saveWordProgress = saveWordProgress;
window.flagWord = flagWord;
window.setupAuthEventListeners = setupAuthEventListeners;
