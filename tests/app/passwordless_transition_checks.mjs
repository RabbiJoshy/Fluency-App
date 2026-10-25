import assert from 'node:assert/strict';
import fs from 'node:fs';
import vm from 'node:vm';

globalThis.window = { location: { hostname: 'localhost', href: 'http://localhost/' }, dispatchEvent() {} };
const { createPasswordlessSessionHandler } = await import('../../app/js/passwordless-auth.js');
const deferred = () => { let resolve, reject; const promise = new Promise((yes, no) => { resolve = yes; reject = no; }); return { promise, resolve, reject }; };
const state = { user: { id: 'first' }, session: { id: 'session' } };
let guest = false, lookups = 0, signedIn = 0, signedOut = 0, mounted = 0, retry;
let profile = deferred();
const coordinator = createPasswordlessSessionHandler({
    resolveUser: () => { lookups++; return profile.promise; },
    onSignedIn: async () => { signedIn++; }, onSignedOut: () => { signedOut++; },
    mount: () => { mounted++; }, isGuest: () => guest, hasSavedUser: () => false,
    onError: (_, action) => { retry = action; }
});
const first = coordinator.handle(state);
const duplicate = coordinator.handle(state);
assert.equal(first, duplicate, 'Duplicate provider events must share the profile lookup');
assert.equal(lookups, 1);
profile.resolve({ id: 'profile' }); await first;
await coordinator.handle(state);
assert.equal(signedIn, 1, 'A completed session must not sign in twice');
await coordinator.handle({});
assert.equal(signedOut, 1); assert.equal(mounted, 1);

profile = deferred();
const stale = coordinator.handle(state);
await coordinator.handle({});
profile.resolve({}); await stale;
assert.equal(signedIn, 1, 'A signed-out session cannot complete an old login');
profile = deferred();
const guestRace = coordinator.handle(state);
guest = true; profile.resolve({}); await guestRace;
assert.equal(signedIn, 1, 'Choosing Guest must win over a pending account lookup');
guest = false;
profile = deferred(); const failure = coordinator.handle(state);
profile.reject(new Error('Account unavailable')); await failure;
assert.equal(typeof retry, 'function', 'Essential account failures must offer an in-place retry');
profile = deferred(); const retried = retry(); profile.resolve({}); await retried;
assert.equal(signedIn, 2);

// Execute the actual fresh-login completion function against a hung progress
// request. This reproduces the original stuck panel without real credentials.
const source = process.env.AUTH_SOURCE ? fs.readFileSync(process.env.AUTH_SOURCE, 'utf8') : fs.readFileSync('app/js/auth.js', 'utf8');
const login = source.slice(source.indexOf('async function completeProfileLogin('), source.indexOf('// Settings → Account.'));
for (const rejects of [false, true]) {
    const progress = deferred(), playlist = deferred();
    const calls = [];
    const ctx = vm.createContext({
        currentUser: null, selectedLanguage: 'spanish', selectedLevel: 'level1',
        sessionStorage: { removeItem() {} }, localStorage: { setItem() {}, getItem: () => 'spanish' },
        document: { querySelector: () => null, querySelectorAll: () => [],
            getElementById: () => ({classList:{contains:()=>true}}) },
        window: { reconcileRemoteSongSet: () => playlist.promise, refreshSetupAfterProgress: () => calls.push('refresh') },
        showUserInfo() {}, clearDeviceSessionState() {}, setTimeout() {}, _openFirstRunTutorialUnlessLinked() {},
        hideAuthModal: () => calls.push('hide'), _markAuthReady: () => calls.push('ready'),
        loadUserProgressFromSheet: () => progress.promise, console: { warn() {} }
    });
    vm.runInContext(login, ctx);
    const completion = vm.runInContext('completeProfileLogin({initials:"clerk_test",isGuest:false})', ctx);
    await Promise.resolve();
    assert.deepEqual(calls, ['hide', 'ready'], 'Sign-in must dismiss its panel and release readiness before remote sync settles');
    await completion;
    if (rejects) { progress.reject(new Error('Offline')); playlist.reject(new Error('Offline')); }
    else { progress.resolve(true); playlist.resolve(); }
    await new Promise(resolve => setImmediate(resolve));
    assert.equal(calls.filter(call => call === 'hide').length, 1);
    assert.equal(calls.includes('refresh'), !rejects);
}
console.log('Fresh login, duplicate callbacks, sign-out/Guest races, background failure and retry passed.');
