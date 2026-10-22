import assert from 'node:assert/strict';
import fs from 'node:fs';
import vm from 'node:vm';

const source = fs.readFileSync('app/js/auth.js', 'utf8');
function storage() {
    const values = new Map();
    return {
        getItem: key => values.get(key) ?? null,
        setItem: (key, value) => values.set(key, value),
        removeItem: key => values.delete(key)
    };
}
function scenario({ reload = false, route = false } = {}) {
    const calls = [];
    const ctx = vm.createContext({
        currentUser: null, PASSWORDLESS_ENABLED: true,
        PASSWORDLESS_SYNC_URL: 'https://sync.example', GOOGLE_SCRIPT_URL: '',
        sessionStorage: storage(), localStorage: storage(),
        _isPageReload: () => reload, consumeRouteNavigation: () => route,
        window: {
            markProgressLoaded: () => calls.push('progress'),
            applyGlobalStudyDefaults: () => calls.push('defaults')
        },
        showUserInfo: () => calls.push('badge'),
        hideAuthModal: () => calls.push('hide'),
        showAuthModal: () => calls.push('landing'),
        _markAuthReady: () => calls.push('ready'),
        startPasswordlessAuth: () => calls.push('clerk'),
        completeProfileLogin() {}, clearDeviceSessionState() { calls.push('clear'); },
        _openFirstRunTutorialUnlessLinked() {}, setTimeout() {}
    });
    vm.runInContext(source.slice(source.indexOf('function onPasswordlessSignedOut'),
        source.indexOf('// Show authentication modal')), ctx);
    vm.runInContext(source.slice(source.indexOf('function enterGuestMode'),
        source.indexOf('// Show login form')), ctx);
    return { ctx, calls, run: code => vm.runInContext(code, ctx) };
}

const guest = scenario();
guest.run('checkAuthentication()');
assert.deepEqual(guest.calls, ['landing', 'clerk']);
guest.calls.length = 0;
guest.run('enterGuestMode()');
assert.equal(guest.ctx.currentUser.isGuest, true);
assert.equal(guest.ctx.sessionStorage.getItem('flashcardGuestSession'), '1');
assert.deepEqual(guest.calls, ['progress', 'badge', 'hide', 'ready']);
assert.equal(guest.ctx.localStorage.getItem('flashcardUser'), null);
guest.calls.length = 0;
guest.run('onPasswordlessSignedOut()');
assert.deepEqual(guest.calls, []); // Delayed account events cannot close guest browsing.

for (const route of [false, true]) {
    const restored = scenario({ reload: route, route });
    restored.ctx.sessionStorage.setItem('flashcardGuestSession', '1');
    restored.run('checkAuthentication()');
    assert.equal(restored.ctx.currentUser.isGuest, true);
    assert.deepEqual(restored.calls, ['progress', 'defaults', 'badge', 'hide', 'ready']);
}
const refreshed = scenario({ reload: true });
refreshed.ctx.sessionStorage.setItem('flashcardGuestSession', '1');
refreshed.run('checkAuthentication()');
assert.equal(refreshed.ctx.sessionStorage.getItem('flashcardGuestSession'), null);
assert.deepEqual(refreshed.calls, ['landing', 'clerk']);

// Keep guest entry visible while replacing the retired account controls.
globalThis.window = { location: { hostname: 'localhost', href: 'http://localhost/' } };
const rows = Object.fromEntries(['guestModeRow', 'loginModeRow', 'createModeRow', 'loginForm', 'loginInfoNote']
    .map(id => [id, { style: { display: 'flex' } }]));
globalThis.document = { getElementById: id => rows[id] };
const { hideLegacyAuthChoices } = await import('../../../app/js/passwordless-auth.js');
hideLegacyAuthChoices();
assert.equal(rows.guestModeRow.style.display, 'flex');
assert.equal(rows.loginModeRow.style.display, 'none');
assert.equal(rows.createModeRow.style.display, 'none');
console.log('Guest entry, readiness, provider independence, navigation and reload passed.');
