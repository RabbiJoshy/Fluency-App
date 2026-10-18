import { IS_STAGING } from './env.js?v=87a002f6';

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
    document.getElementById('passwordlessEmailNotice')?.classList.add('hidden');
    return new Promise(resolve => {
        const form = document.createElement('form');
        form.className = 'passwordless-profile-form';
        const heading = document.createElement('h4'); heading.textContent = 'Choose your username';
        const note = document.createElement('p'); note.textContent = 'This name labels your saved progress. Your progress stays with your account on every device.';
        const label = document.createElement('label'); label.textContent = 'Username'; label.htmlFor = 'newAccountName';
        const input = document.createElement('input'); input.id = 'newAccountName'; input.required = true;
        input.maxLength = 40; input.className = 'initials-input'; input.autocomplete = 'nickname';
        const error = document.createElement('p'); error.setAttribute('role', 'alert');
        const submit = document.createElement('button'); submit.type = 'submit'; submit.className = 'auth-submit-btn'; submit.textContent = 'Create account';
        form.append(heading, note, label, input, error, submit); container.append(form);
        form.onsubmit = async event => {
            event.preventDefault(); submit.disabled = true; error.textContent = '';
            try {
                const created = await account(input.value.trim());
                resolve({ ...created, isNew: true });
            }
            catch (failure) { error.textContent = failure.message; submit.disabled = false; }
        };
        input.focus();
    });
}

export async function signOutPasswordless() {
    activeUserId = null;
    resolvingUserId = null;
    mounted = false;
    if (loading) {
        try { await loading; } catch (_) {}
    }
    if (window.Clerk) {
        try {
            await window.Clerk.signOut();
        } catch (error) {
            console.warn('Clerk signOut error:', error);
        }
    }
}

function mountSignInUI(container) {
    if (mounted || !window.Clerk) return;
    const modal = document.getElementById('authModal');
    const subtitle = modal?.querySelector('.auth-welcome-copy p');
    if (subtitle) subtitle.style.display = '';
    const notice = document.getElementById('passwordlessEmailNotice');
    if (notice) {
        notice.classList.remove('hidden');
        notice.style.display = '';
    }
    container.replaceChildren();
    const returnUrl = window.location.origin + window.location.pathname + window.location.hash;
    const signupUrl = new URL(window.location.href);
    signupUrl.searchParams.set('account', 'create');
    const props = {
        routing: 'virtual', forceRedirectUrl: returnUrl,
        signInForceRedirectUrl: returnUrl, signUpForceRedirectUrl: returnUrl,
        signInUrl: returnUrl, signUpUrl: signupUrl.href,
        appearance: { layout: { socialButtonsVariant: 'blockButton' }, elements: {
            header: { display: 'none' },
            socialButtons: { display: 'flex', flexDirection: 'column', gap: '10px' },
            card: { boxShadow: 'none', background: 'transparent', border: 'none', padding: '0' },
            cardBox: { boxShadow: 'none', width: '100%', borderRadius: '0' },
            socialButtonsBlockButton: { minHeight: '44px', width: '100%' }
        }, variables: {
            colorPrimary: '#a5b4fc', colorForeground: '#f8fafc', colorMutedForeground: '#cbd5e1',
            colorBackground: '#1a222c', colorInputBackground: '#111827',
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

export async function startPasswordlessAuth(onSignedIn, onSignedOut) {
    hideLegacyAuthChoices();
    let container = document.getElementById('passwordlessSignIn');
    if (!container) {
        container = document.createElement('div');
        container.id = 'passwordlessSignIn';
        document.querySelector('#authModal .auth-body').prepend(container);
        const modal = document.getElementById('authModal');
        modal.classList.add('passwordless-auth-active');
        modal.querySelector('.auth-modal-content')?.classList.add('passwordless-modal');
        const heading = modal.querySelector('.auth-welcome-copy h3');
        if (heading) heading.textContent = 'Fluency';
        const subtitle = modal.querySelector('.auth-welcome-copy p');
        if (subtitle) subtitle.textContent = 'Sign in to save your learning across devices.';
        const notice = document.createElement('p');
        notice.id = 'passwordlessEmailNotice';
        notice.className = 'passwordless-email-notice';
        notice.setAttribute('role', 'note');
        notice.textContent = 'Email codes currently aren’t reaching iCloud or me.com addresses. Please use Google, Microsoft or another email address.';
        container.after(notice);
        const stylesheet = document.createElement('link');
        stylesheet.rel = 'stylesheet';
        const stylesheetUrl = new URL('../css/passwordless-auth.css', import.meta.url);
        stylesheetUrl.search = new URL(import.meta.url).search;
        stylesheet.href = stylesheetUrl.href;
        document.head.appendChild(stylesheet);
    }
    const modal = document.getElementById('authModal');
    const subtitle = modal?.querySelector('.auth-welcome-copy p');
    const notice = document.getElementById('passwordlessEmailNotice');
    if (!mounted && !window.Clerk?.user) {
        if (subtitle) subtitle.style.display = 'none';
        if (notice) notice.style.display = 'none';
        container.innerHTML = `
            <div class="passwordless-loading-container" role="status">
                <div class="passwordless-spinner" aria-hidden="true"></div>
                <span class="passwordless-loading-text">Loading secure sign-in…</span>
            </div>
        `;
    }
    container.style.display = 'flex';
    if (!loading) {
        loading = (async () => {
            await loadScript(`https://${CLERK_DOMAIN}/npm/@clerk/ui@1/dist/ui.browser.js`);
            await loadScript(`https://${CLERK_DOMAIN}/npm/@clerk/clerk-js@6/dist/clerk.browser.js`, {
                'data-clerk-publishable-key': PUBLISHABLE_KEY
            });
            await window.Clerk.load({ ui: { ClerkUI: window.__internal_ClerkUICtor } });
            const handle = async ({ user, session }) => {
                if (!user || !session) {
                    if (activeUserId) {
                        activeUserId = null;
                        onSignedOut();
                    } else if (localStorage.getItem('flashcardUser')) {
                        onSignedOut();
                    }
                    if (!mounted && window.Clerk) {
                        mountSignInUI(container);
                    }
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
                    username: profile.name, isGuest: false,
                    isNew: Boolean(profile?.isNew)
                });
                window.dispatchEvent(new Event('fluency-auth-restored'));
            };
            window.Clerk.addListener(state => { handle(state).catch(error => {
                if (subtitle) subtitle.style.display = 'none';
                if (notice) notice.style.display = 'none';
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
        if (!window.Clerk.user) {
            mountSignInUI(container);
        }
    } catch (error) {
        if (subtitle) subtitle.style.display = 'none';
        if (notice) notice.style.display = 'none';
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
