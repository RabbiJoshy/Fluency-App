const domain = 'hardy-feline-9737.clerk.accounts.dev';
const publicKey = 'pk_test_aGFyZHktZmVsaW5lLTk3MzcuY2xlcmsuYWNjb3VudHMuZGV2JA';
const api = 'https://fluency-auth-staging.rabbijoshy.workers.dev';
const container = document.getElementById('sign-in');
let signedInUser;

function script(src, attributes = {}) {
    return new Promise((resolve, reject) => {
        const element = document.createElement('script');
        element.src = src;
        element.crossOrigin = 'anonymous';
        for (const [name, value] of Object.entries(attributes)) element.setAttribute(name, value);
        const timeout = setTimeout(() => reject(new Error('Sign-in could not load. Refresh to retry.')), 15000);
        element.onload = () => { clearTimeout(timeout); resolve(); };
        element.onerror = () => { clearTimeout(timeout); reject(new Error('Sign-in could not load. Refresh to retry.')); };
        document.head.appendChild(element);
    });
}

async function showAccount({ user, session }) {
    if (!user || !session) {
        if (signedInUser) window.location.reload();
        return;
    }
    if (signedInUser === user.id) return;
    signedInUser = user.id;
    container.hidden = true;
    document.getElementById('result').hidden = false;
    const email = user.primaryEmailAddress?.emailAddress || user.fullName || 'your account';
    document.getElementById('identity').textContent = `Signed in as ${email}`;
    document.getElementById('sign-out').onclick = async () => { await window.Clerk.signOut(); window.location.reload(); };
    try {
        const token = await session.getToken();
        const response = await fetch(api, {
            method: 'POST', headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
            body: JSON.stringify({ action: 'capabilities' }), signal: AbortSignal.timeout(15000)
        });
        const result = await response.json();
        if (!response.ok || !result.success) throw new Error(result.message || 'Session check failed.');
        document.getElementById('verification').textContent = 'Success: sign-in works on this address, and the Fluency server accepts your session.';
    } catch (error) {
        document.getElementById('verification').textContent = `Sign-in succeeded, but the server check failed: ${error.message}`;
    }
}

try {
    await script(`https://${domain}/npm/@clerk/ui@1/dist/ui.browser.js`);
    await script(`https://${domain}/npm/@clerk/clerk-js@6/dist/clerk.browser.js`, { 'data-clerk-publishable-key': publicKey });
    await window.Clerk.load({ ui: { ClerkUI: window.__internal_ClerkUICtor } });
    window.Clerk.addListener(state => { showAccount(state).catch(console.error); });
    await showAccount(window.Clerk);
    if (!window.Clerk.user) {
        container.replaceChildren();
        const url = new URL(window.location.href);
        url.search = '';
        const props = { routing: 'virtual', forceRedirectUrl: url.href, signInForceRedirectUrl: url.href,
            signUpForceRedirectUrl: url.href, signInUrl: url.href, signUpUrl: `${url.href}?create=1`,
            appearance: { variables: { colorPrimary: '#a5b4fc', colorForeground: '#f8fafc',
                colorBackground: '#1f2937', colorInputBackground: '#111827', colorInputText: '#f8fafc' } } };
        if (new URLSearchParams(window.location.search).has('create')) window.Clerk.mountSignUp(container, props);
        else window.Clerk.mountSignIn(container, props);
    }
} catch (error) {
    container.textContent = error.message;
}
