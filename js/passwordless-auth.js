import { IS_STAGING } from './env.js?v=7f0d8f06';

export const PASSWORDLESS_ENABLED = true;
export const PASSWORDLESS_SYNC_URL = IS_STAGING
    ? 'https://fluency-auth-staging.rabbijoshy.workers.dev'
    : 'https://fluency-api.rabbijoshy.workers.dev';
const CLERK_DOMAIN = 'hardy-feline-9737.clerk.accounts.dev';
const PUBLISHABLE_KEY = 'pk_test_aGFyZHktZmVsaW5lLTk3MzcuY2xlcmsuYWNjb3VudHMuZGV2JA';
let loading;
let mounted = false;
let activeUserId = null;
let resolvingUserId = null;

export function authenticatedSyncFetch(nativeFetch, getSession, endpoint) {
    const selectedEndpoint = new URL(endpoint).href;
    return async (input, options = {}) => {
        const url = typeof input === 'string' ? input : (input instanceof URL ? input.href : input.url);
        const resolved = new URL(url, window.location.href).href;
        const legacyEndpoint = 'https://fluency-api.rabbijoshy.workers.dev/';
        if (resolved !== selectedEndpoint && resolved !== legacyEndpoint) return nativeFetch(input, options);
        const token = await getSession()?.getToken();
        if (!token) throw Object.assign(new Error('Sign in to sync your progress.'), { auth: true });
        const headers = new Headers(input instanceof Request ? input.headers : undefined);
        new Headers(options.headers).forEach((value, key) => headers.set(key, value));
        headers.set('Authorization', `Bearer ${token}`);
        // Old configuration/cache values must never send staging writes to the
        // live database. Route every recognized progress URL to this environment.
        const target = resolved === selectedEndpoint ? input : (input instanceof Request ? new Request(endpoint, input) : endpoint);
        return nativeFetch(target, { ...options, headers });
    };
}

// One narrow transport seam covers progress, song sets and queued writes.
// Only recognized progress URLs receive tokens, always at this environment's API.
if (PASSWORDLESS_ENABLED && window.fetch) {
    window.fetch = authenticatedSyncFetch(window.fetch.bind(window), () => window.Clerk?.session, PASSWORDLESS_SYNC_URL);
}

function loadScript(src, attributes = {}) {
    return new Promise((resolve, reject) => {
        const script = document.createElement('script');
        script.src = src;
        script.crossOrigin = 'anonymous';
        Object.entries(attributes).forEach(([key, value]) => script.setAttribute(key, value));
        const timer = setTimeout(() => reject(new Error('Sign-in is taking too long. Please retry.')), 15000);
        script.onload = () => { clearTimeout(timer); resolve(); };
        script.onerror = () => { clearTimeout(timer); script.remove(); reject(new Error('Could not load sign-in. Check your connection and retry.')); };
        document.head.appendChild(script);
    });
}

export function hideLegacyAuthChoices() {
    for (const id of ['guestModeRow', 'loginModeRow', 'createModeRow', 'loginForm', 'loginInfoNote']) {
        const el = document.getElementById(id);
        if (el) el.style.display = 'none';
    }
}

async function resolveProfile(user, container) {
    async function account(name) {
        const response = await fetch(PASSWORDLESS_SYNC_URL, { method: 'POST',
            body: JSON.stringify({ action: 'account', ...(name ? { name } : {}) }),
            signal: AbortSignal.timeout(15000) });
        const result = await response.json();
        if (!response.ok || !result.success) throw new Error(result.message || 'Could not load your account.');
        return result.data.profile;
    }
    const existing = await account();
    if (existing) return existing;
    if (mounted) { window.Clerk.unmountSignIn(container); window.Clerk.unmountSignUp(container); mounted = false; }
    container.replaceChildren();
    return new Promise(resolve => {
        const form = document.createElement('form');
        form.style.width = '100%';
        const heading = document.createElement('h4'); heading.textContent = 'Choose your username';
        const note = document.createElement('p'); note.textContent = 'This name labels your saved progress. You’ll sign in with Google or an email code.';
        const label = document.createElement('label'); label.textContent = 'Username'; label.htmlFor = 'newAccountName';
        const input = document.createElement('input'); input.id = 'newAccountName'; input.required = true;
        input.maxLength = 40; input.className = 'initials-input'; input.autocomplete = 'nickname';
        input.value = user.primaryEmailAddress?.emailAddress === 'rabbijoshy@gmail.com' ? 'JOSHUA' : (user.firstName || '');
        const error = document.createElement('p'); error.setAttribute('role', 'alert');
        const submit = document.createElement('button'); submit.type = 'submit'; submit.className = 'auth-submit-btn'; submit.textContent = 'Create account';
        form.append(heading, note, label, input, error, submit); container.append(form);
        form.onsubmit = async event => {
            event.preventDefault(); submit.disabled = true; error.textContent = '';
            try { resolve(await account(input.value.trim())); }
            catch (failure) { error.textContent = failure.message; submit.disabled = false; }
        };
        input.focus();
    });
}

export async function startPasswordlessAuth(onSignedIn, onSignedOut) {
    hideLegacyAuthChoices();
    let container = document.getElementById('passwordlessSignIn');
    if (!container) {
        container = document.createElement('div');
        container.id = 'passwordlessSignIn';
        document.querySelector('#authModal .auth-body').prepend(container);
        const style = document.createElement('style');
        document.querySelector('#authModal .auth-modal-content')?.classList.add('passwordless-modal');
        style.textContent = '.passwordless-modal {max-height:calc(100dvh - 32px);overflow-y:auto;padding:20px!important;} .passwordless-modal .auth-welcome-mark {display:none;} .passwordless-modal .auth-welcome-copy {margin-bottom:16px;} .passwordless-modal .auth-welcome-copy h3 {font-size:24px;} #passwordlessSignIn {display:flex;justify-content:center;max-width:100%;} #passwordlessSignIn .cl-rootBox {width:100%;} #passwordlessSignIn .cl-card {box-shadow:none;width:100%;max-width:100%;} #passwordlessSignIn .cl-cardBox {width:100%;max-width:100%;}';
        document.head.appendChild(style);
    }
    container.style.display = 'flex';
    if (!loading) {
        container.textContent = 'Loading secure sign-in…';
        loading = (async () => {
            await loadScript(`https://${CLERK_DOMAIN}/npm/@clerk/ui@1/dist/ui.browser.js`);
            await loadScript(`https://${CLERK_DOMAIN}/npm/@clerk/clerk-js@6/dist/clerk.browser.js`, {
                'data-clerk-publishable-key': PUBLISHABLE_KEY
            });
            await window.Clerk.load({ ui: { ClerkUI: window.__internal_ClerkUICtor } });
            const handle = async ({ user, session }) => {
                if (!user || !session) {
                    if (activeUserId) { activeUserId = null; onSignedOut(); }
                    return;
                }
                if (activeUserId === user.id || resolvingUserId === user.id) return;
                resolvingUserId = user.id;
                let profile;
                try { profile = await resolveProfile(user, container); }
                finally { resolvingUserId = null; }
                activeUserId = user.id;
                await onSignedIn({
                    initials: IS_STAGING ? profile.id.replace(/^stg_/, '') : profile.id,
                    profileId: profile.id, authProvider: 'clerk',
                    username: profile.name, isGuest: false
                });
                window.dispatchEvent(new Event('fluency-auth-restored'));
            };
            window.Clerk.addListener(state => { handle(state).catch(error => {
                container.replaceChildren();
                const message = document.createElement('p'); message.textContent = error.message;
                const retry = document.createElement('button'); retry.className = 'auth-submit-btn'; retry.textContent = 'Retry sign-in';
                retry.onclick = () => window.location.reload(); container.append(message, retry);
            }); });
            await handle(window.Clerk);
        })().catch(error => { loading = null; throw error; });
    }
    try {
        await loading;
        if (!window.Clerk.user && !mounted) {
            container.replaceChildren();
            const returnUrl = window.location.origin + window.location.pathname + window.location.hash;
            const signupUrl = new URL(window.location.href);
            signupUrl.searchParams.set('account', 'create');
            const props = {
                routing: 'virtual', forceRedirectUrl: returnUrl,
                signInForceRedirectUrl: returnUrl, signUpForceRedirectUrl: returnUrl,
                signInUrl: returnUrl, signUpUrl: signupUrl.href,
                appearance: { variables: {
                    colorPrimary: '#a5b4fc', colorForeground: '#f8fafc', colorMutedForeground: '#cbd5e1',
                    colorBackground: '#1f2937', colorInputBackground: '#111827',
                    colorInputText: '#f8fafc', borderRadius: '12px'
                } }
            };
            if (new URLSearchParams(window.location.search).get('account') === 'create') {
                window.Clerk.mountSignUp(container, props);
            } else {
                window.Clerk.mountSignIn(container, props);
            }
            mounted = true;
        }
    } catch (error) {
        container.replaceChildren();
        const message = document.createElement('p');
        message.textContent = error.message;
        const retry = document.createElement('button');
        retry.className = 'auth-submit-btn';
        retry.textContent = 'Retry sign-in';
        retry.onclick = () => startPasswordlessAuth(onSignedIn, onSignedOut);
        container.append(message, retry);
    }
}
