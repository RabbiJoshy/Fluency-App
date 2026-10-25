import { readJsonWithTimeout } from './read-request.js?v=1';
import { IS_STAGING } from './env.js?v=20261010airlock';

export const PASSWORDLESS_ENABLED = true;
export const PASSWORDLESS_SYNC_URL = IS_STAGING
    ? 'https://fluency-auth-staging.rabbijoshy.workers.dev'
    : 'https://fluency-api.rabbijoshy.workers.dev';
const CLERK_DOMAIN = 'hardy-feline-9737.clerk.accounts.dev';
const PUBLISHABLE_KEY = 'pk_test_aGFyZHktZmVsaW5lLTk3MzcuY2xlcmsuYWNjb3VudHMuZGV2JA';
let loading;
let mounted = false;
let cancelSignInLayout = () => {};
let resetSessionHandler = () => {};

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
        const timer = setTimeout(() => { script.remove(); reject(new Error('Sign-in is taking too long. Please retry.')); }, 15000);
        script.onload = () => { clearTimeout(timer); resolve(); };
        script.onerror = () => { clearTimeout(timer); script.remove(); reject(new Error('Could not load sign-in. Check your connection and retry.')); };
        document.head.appendChild(script);
    });
}

export function hideLegacyAuthChoices() {
    // Guest entry is independent of the account provider and stays available
    // while sign-in loads, including when the provider is unavailable.
    for (const id of ['loginModeRow', 'createModeRow', 'loginForm', 'loginInfoNote']) {
        const el = document.getElementById(id);
        if (el) el.style.display = 'none';
    }
}

async function resolveProfile(user, container) {
    async function account(name) {
        const { response, data: result } = await readJsonWithTimeout(PASSWORDLESS_SYNC_URL, { method: 'POST',
            body: JSON.stringify({ action: 'account', ...(name ? { name } : {}) }),
        }, 15000);
        if (!response.ok || !result?.success) throw new Error(result?.message || 'Could not load your account.');
        return result.data.profile;
    }
    const existing = await account();
    if (existing) return existing;
    cancelSignInLayout();
    finishSignInLoading();
    document.getElementById('passwordlessMoreOptions')?.remove();
    document.getElementById('passwordlessAccountSwitch')?.remove();
    if (mounted) { window.Clerk.unmountSignIn(container); window.Clerk.unmountSignUp(container); mounted = false; }
    container.replaceChildren();
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
    resetSessionHandler();
    cancelSignInLayout();
    mounted = false;
    if (window.Clerk) {
        try {
            await window.Clerk.signOut();
        } catch (error) {
            console.warn('Clerk signOut error:', error);
        }
    }
}

const APPLE_EMAIL = /@(icloud|me|mac)\.com\s*$/i;

function showAppleEmailDialog(container) {
    if (document.getElementById('appleEmailDialog')) return;
    const overlay = document.createElement('div');
    overlay.id = 'appleEmailDialog';
    overlay.className = 'passwordless-dialog-overlay';
    overlay.innerHTML = `
        <div class="passwordless-dialog" role="alertdialog" aria-modal="true" aria-labelledby="appleEmailDialogTitle" aria-describedby="appleEmailDialogText">
            <h3 id="appleEmailDialogTitle">iCloud emails can't sign in yet</h3>
            <p id="appleEmailDialogText">Email codes aren't reaching iCloud, me.com or mac.com addresses at the moment. Please continue with Google or Microsoft, or use a different email address.</p>
            <button type="button" class="auth-submit-btn">Use another email</button>
        </div>`;
    const button = overlay.querySelector('button');
    const close = () => {
        overlay.remove();
        document.removeEventListener('keydown', onKey, true);
        const field = container.querySelector('input');
        if (field) { field.focus(); field.select?.(); }
    };
    const onKey = event => {
        if (event.key === 'Escape') { event.preventDefault(); close(); }
        else if (event.key === 'Tab') { event.preventDefault(); button.focus(); }
    };
    button.addEventListener('click', close);
    document.addEventListener('keydown', onKey, true);
    document.body.appendChild(overlay);
    button.focus();
}

function prepareAuthChoices(container) {
    const modal = document.getElementById('authModal');
    const returnUrl = window.location.origin + window.location.pathname + window.location.hash;
    const signupUrl = new URL(window.location.href);
    signupUrl.searchParams.set('account', 'create');
    const isSignUp = new URLSearchParams(window.location.search).get('account') === 'create';
    const optionsLabel = isSignUp ? 'More sign-up options' : 'More sign-in options';
    modal.classList.add('passwordless-options-collapsed');
    let moreOptions = document.getElementById('passwordlessMoreOptions');
    if (!moreOptions) {
        moreOptions = document.createElement('button');
        moreOptions.id = 'passwordlessMoreOptions';
        moreOptions.type = 'button';
        moreOptions.className = 'passwordless-options-toggle';
        moreOptions.setAttribute('aria-controls', container.id);
        moreOptions.onclick = () => {
            const collapsed = modal.classList.toggle('passwordless-options-collapsed');
            moreOptions.setAttribute('aria-expanded', String(!collapsed));
            moreOptions.textContent = collapsed ? optionsLabel : 'Show fewer options';
        };
        container.after(moreOptions);
    }
    moreOptions.setAttribute('aria-expanded', 'false');
    moreOptions.textContent = optionsLabel;
    let accountSwitch = document.getElementById('passwordlessAccountSwitch');
    if (!accountSwitch) {
        accountSwitch = document.createElement('p');
        accountSwitch.id = 'passwordlessAccountSwitch';
        accountSwitch.className = 'passwordless-account-switch';
        moreOptions.after(accountSwitch);
    }
    const accountLink = document.createElement('a');
    accountLink.href = isSignUp ? returnUrl : signupUrl.href;
    accountLink.textContent = isSignUp ? 'Sign in' : 'Sign up';
    accountSwitch.replaceChildren(
        document.createTextNode(isSignUp ? 'Have an account? ' : 'New here? '), accountLink
    );
    moreOptions.disabled = true;
    moreOptions.hidden = false;
    if (!document.getElementById('passwordlessAttributionSpace')) {
        const space = document.createElement('div');
        space.id = 'passwordlessAttributionSpace';
        space.setAttribute('aria-hidden', 'true');
        accountSwitch.after(space);
    }
}

function showSignInLoading(container) {
    const modal = document.getElementById('authModal');
    modal.setAttribute('data-auth-loading', 'true');
    container.setAttribute('aria-busy', 'true');
    let status = document.getElementById('passwordlessLoadingStatus');
    if (!status) {
        status = document.createElement('div');
        status.id = 'passwordlessLoadingStatus';
        status.className = 'passwordless-loading-container';
        status.setAttribute('role', 'status');
        status.innerHTML = '<span class="passwordless-spinner" aria-hidden="true"></span><span class="passwordless-loading-text">Loading secure sign-in…</span>';
        container.after(status);
    }
    status.hidden = false;
}

function finishSignInLoading() {
    document.getElementById('authModal')?.removeAttribute('data-auth-loading');
    document.getElementById('passwordlessSignIn')?.removeAttribute('aria-busy');
    const status = document.getElementById('passwordlessLoadingStatus');
    if (status) status.hidden = true;
}

function showAuthFailure(container, error, retryAction) {
    cancelSignInLayout();
    finishSignInLoading();
    const more = document.getElementById('passwordlessMoreOptions');
    if (more) { more.disabled = true; more.hidden = true; }
    const feedback = document.createElement('div');
    feedback.className = 'passwordless-auth-feedback';
    const message = document.createElement('p');
    message.setAttribute('role', 'alert'); message.textContent = error.message;
    const retry = document.createElement('button');
    retry.type = 'button'; retry.className = 'auth-submit-btn'; retry.textContent = 'Retry sign-in';
    retry.onclick = () => {
        retry.disabled = true; retry.textContent = 'Signing in…';
        message.textContent = 'Loading your account…'; retryAction();
    };
    feedback.append(message, retry); container.replaceChildren(feedback);
}

function watchSignInLayout(container) {
    cancelSignInLayout();
    let frame = 0, cancelled = false;
    const stop = () => {
        cancelled = true; observer.disconnect(); styles.disconnect(); clearTimeout(timer);
        document.removeEventListener('load', check, true);
        cancelAnimationFrame(frame);
    };
    const check = () => {
        if (frame || cancelled) return;
        const control = container.querySelector('button:not([aria-hidden="true"]), input');
        if (!control || parseFloat(getComputedStyle(control).minHeight) < 44) return;
        const header = container.querySelector('.cl-header');
        if (header && getComputedStyle(header).display !== 'none') return;
        frame = requestAnimationFrame(() => {
            frame = requestAnimationFrame(() => {
                frame = 0;
                if (cancelled || !control.isConnected || !control.getClientRects().length) return;
                stop(); finishSignInLoading();
                const more = document.getElementById('passwordlessMoreOptions');
                if (more) more.disabled = false;
            });
        });
    };
    const observer = new MutationObserver(check);
    observer.observe(container, { childList: true, subtree: true, attributes: true });
    const styles = new MutationObserver(check);
    styles.observe(document.head, { childList: true, subtree: true, characterData: true });
    document.addEventListener('load', check, true);
    const timer = setTimeout(() => {
        stop();
        showAuthFailure(container, new Error('Sign-in is taking too long. Please retry.'), () => {
            window.Clerk.unmountSignIn(container); window.Clerk.unmountSignUp(container);
            mounted = false; mountSignInUI(container);
        });
    }, 15000);
    cancelSignInLayout = stop;
    check();
}

function mountSignInUI(container) {
    if (mounted || !window.Clerk) return;
    const modal = document.getElementById('authModal');
    const subtitle = modal?.querySelector('.auth-welcome-copy p');
    if (subtitle) subtitle.style.display = '';
    prepareAuthChoices(container);
    showSignInLoading(container);
    container.replaceChildren();
    const returnUrl = window.location.origin + window.location.pathname + window.location.hash;
    const signupUrl = new URL(window.location.href);
    signupUrl.searchParams.set('account', 'create');
    const isSignUp = new URLSearchParams(window.location.search).get('account') === 'create';
    const optionsLabel = isSignUp ? 'More sign-up options' : 'More sign-in options';
    const props = {
        routing: 'virtual', forceRedirectUrl: returnUrl,
        signInForceRedirectUrl: returnUrl, signUpForceRedirectUrl: returnUrl,
        signInUrl: returnUrl, signUpUrl: signupUrl.href,
        appearance: { layout: { socialButtonsVariant: 'blockButton' }, elements: {
            header: { display: 'none' },
            socialButtons: { display: 'flex', flexDirection: 'column', gap: '10px' },
            card: { boxShadow: 'none', background: 'transparent', border: 'none', padding: '0' },
            cardBox: { boxShadow: 'none', width: '100%', borderRadius: '0' },
            socialButtonsBlockButton: { minHeight: '48px', width: '100%', fontSize: '14px', fontWeight: '600' },
            formButtonPrimary: { minHeight: '48px', fontSize: '14px', fontWeight: '600' },
            formFieldInput: { minHeight: '48px', fontSize: '14px' }
        }, variables: {
            fontFamily: 'var(--font-reading, sans-serif)',
            colorPrimary: '#a5b4fc', colorForeground: '#f8fafc', colorMutedForeground: '#cbd5e1',
            colorBackground: '#1a222c', colorInputBackground: '#111827',
            colorInputText: '#f8fafc', borderRadius: '12px'
        } }
    };
    if (isSignUp) {
        window.Clerk.mountSignUp(container, props);
    } else {
        window.Clerk.mountSignIn(container, props);
    }
    mounted = true;
    watchSignInLayout(container);
}

export function createPasswordlessSessionHandler({ resolveUser, onSignedIn, onSignedOut,
    mount, isGuest, hasSavedUser, onError }) {
    let active = null, pending = null, generation = 0;
    const reset = () => { generation++; active = null; pending = null; };
    const handle = state => {
        if (isGuest()) { reset(); return Promise.resolve(); }
        const { user, session } = state;
        if (!user || !session) {
            const shouldSignOut = active || pending || hasSavedUser();
            reset();
            if (shouldSignOut) onSignedOut();
            mount();
            return Promise.resolve();
        }
        if (active === user.id) return Promise.resolve();
        if (pending?.id === user.id) return pending.promise;
        const token = ++generation;
        const attempt = { id: user.id };
        pending = attempt;
        attempt.promise = (async () => {
            try {
                const profile = await resolveUser(user);
                if (token !== generation || isGuest()) return;
                await onSignedIn(profile);
                if (token !== generation || isGuest()) return;
                active = user.id;
                window.dispatchEvent(new Event('fluency-auth-restored'));
            } catch (error) {
                if (token === generation && !isGuest()) onError(error, () => handle(state));
            } finally {
                if (pending === attempt) pending = null;
            }
        })();
        return attempt.promise;
    };
    return { handle, reset };
}

function authStep(promise, timeoutMs = 15000) {
    let timer;
    return Promise.race([promise, new Promise((_, reject) => {
        timer = setTimeout(() => reject(new Error('Sign-in is taking too long. Please retry.')), timeoutMs);
    })]).finally(() => clearTimeout(timer));
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
        const welcome = modal.querySelector('.auth-welcome-copy');
        const mark = modal.querySelector('.auth-welcome-mark');
        if (welcome && mark) welcome.prepend(mark);
        const subtitle = modal.querySelector('.auth-welcome-copy p');
        // Email codes don't reach Apple addresses: stop the attempt and say so in
        // a dialog that has to be dismissed.
        container.addEventListener('submit', event => {
            const email = container.querySelector('input[name="identifier"], input[type="email"], input[type="text"]')?.value || '';
            if (!APPLE_EMAIL.test(email)) return;
            event.preventDefault();
            event.stopPropagation();
            showAppleEmailDialog(container);
        }, true);
        const stylesheet = document.createElement('link');
        stylesheet.rel = 'stylesheet';
        const stylesheetUrl = new URL('../css/passwordless-auth.css', import.meta.url);
        stylesheetUrl.search = new URL(import.meta.url).search;
        stylesheet.href = stylesheetUrl.href;
        document.head.appendChild(stylesheet);
    }
    const modal = document.getElementById('authModal');
    const subtitle = modal?.querySelector('.auth-welcome-copy p');
    if (!mounted && !window.Clerk?.user) {
        if (subtitle) subtitle.style.display = 'none';
        prepareAuthChoices(container);
        showSignInLoading(container);
    }
    if (!loading) {
        loading = (async () => {
            await loadScript(`https://${CLERK_DOMAIN}/npm/@clerk/ui@1/dist/ui.browser.js`);
            await loadScript(`https://${CLERK_DOMAIN}/npm/@clerk/clerk-js@6/dist/clerk.browser.js`, {
                'data-clerk-publishable-key': PUBLISHABLE_KEY
            });
            const providerLabel = new URLSearchParams(window.location.search).get('account') === 'create'
                ? 'Sign up with {{provider|titleize}}' : 'Sign in with {{provider|titleize}}';
            await authStep(window.Clerk.load({
                ui: { ClerkUI: window.__internal_ClerkUICtor },
                localization: {
                    socialButtonsBlockButton: providerLabel,
                    socialButtonsBlockButtonManyInView: providerLabel
                }
            }));
            const coordinator = createPasswordlessSessionHandler({
                isGuest: () => sessionStorage.getItem('flashcardGuestSession') === '1',
                hasSavedUser: () => Boolean(localStorage.getItem('flashcardUser')),
                onSignedOut, onSignedIn,
                mount: () => { if (!mounted) mountSignInUI(container); },
                resolveUser: async user => {
                    const profile = await resolveProfile(user, container);
                    return {
                        initials: IS_STAGING ? profile.id.replace(/^stg_/, '') : profile.id,
                        profileId: profile.id, authProvider: 'clerk',
                        username: profile.name, isGuest: false, isNew: Boolean(profile?.isNew)
                    };
                },
                onError: (error, retryAction) => {
                    if (subtitle) subtitle.style.display = 'none';
                    if (mounted) {
                        window.Clerk.unmountSignIn(container);
                        window.Clerk.unmountSignUp(container);
                        mounted = false;
                    }
                    showAuthFailure(container, error, retryAction);
                }
            });
            resetSessionHandler = coordinator.reset;
            window.Clerk.addListener(state => { coordinator.handle(state); });
            await coordinator.handle(window.Clerk);
        })().catch(error => { loading = null; throw error; });
    }
    try {
        await loading;
        if (!window.Clerk.user) {
            mountSignInUI(container);
        }
    } catch (error) {
        if (subtitle) subtitle.style.display = 'none';
        showAuthFailure(container, error, () => startPasswordlessAuth(onSignedIn, onSignedOut));
    }
}
