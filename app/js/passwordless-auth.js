import { IS_STAGING } from './env.js?v=20261010airlock';

export const PASSWORDLESS_ENABLED = IS_STAGING;
export const PASSWORDLESS_SYNC_URL = 'https://fluency-auth-staging.rabbijoshy.workers.dev';
const CLERK_DOMAIN = 'hardy-feline-9737.clerk.accounts.dev';
const PUBLISHABLE_KEY = 'pk_test_aGFyZHktZmVsaW5lLTk3MzcuY2xlcmsuYWNjb3VudHMuZGV2JA';
let loading;
let mounted = false;
let activeUserId = null;

export function authenticatedSyncFetch(nativeFetch, getSession, endpoint) {
    return async (input, options = {}) => {
        const url = typeof input === 'string' ? input : (input instanceof URL ? input.href : input.url);
        if (new URL(url, window.location.href).href !== endpoint) return nativeFetch(input, options);
        const token = await getSession()?.getToken();
        if (!token) throw Object.assign(new Error('Sign in to sync your progress.'), { auth: true });
        const headers = new Headers(input instanceof Request ? input.headers : undefined);
        new Headers(options.headers).forEach((value, key) => headers.set(key, value));
        headers.set('Authorization', `Bearer ${token}`);
        return nativeFetch(input, { ...options, headers });
    };
}

// One narrow transport seam covers the existing progress, song-set and queued
// write paths. Tokens are attached only to the exact isolated staging API URL.
if (PASSWORDLESS_ENABLED) {
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

export async function startPasswordlessAuth(onSignedIn, onSignedOut) {
    hideLegacyAuthChoices();
    let container = document.getElementById('passwordlessSignIn');
    if (!container) {
        container = document.createElement('div');
        container.id = 'passwordlessSignIn';
        document.querySelector('#authModal .auth-body').prepend(container);
        const style = document.createElement('style');
        style.textContent = '#passwordlessSignIn {display:flex;justify-content:center;max-width:100%;} #passwordlessSignIn .cl-rootBox {width:100%;} #passwordlessSignIn .cl-card {box-shadow:none;width:100%;max-width:100%;} #passwordlessSignIn .cl-cardBox {width:100%;max-width:100%;}';
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
                if (activeUserId === user.id) return;
                activeUserId = user.id;
                await onSignedIn({
                    initials: `clerk_${user.id}`, profileId: user.id, authProvider: 'clerk',
                    username: user.fullName || user.primaryEmailAddress?.emailAddress || 'Learner', isGuest: false
                });
                window.dispatchEvent(new Event('fluency-auth-restored'));
            };
            window.Clerk.addListener(state => { handle(state).catch(console.error); });
            await handle(window.Clerk);
        })().catch(error => { loading = null; throw error; });
    }
    try {
        await loading;
        if (!window.Clerk.user && !mounted) {
            container.replaceChildren();
            const returnUrl = window.location.origin + window.location.pathname + window.location.hash;
            window.Clerk.mountSignIn(container, {
                routing: 'virtual', signInForceRedirectUrl: returnUrl, signUpForceRedirectUrl: returnUrl,
                appearance: { variables: { colorPrimary: '#334155', borderRadius: '12px' } }
            });
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
