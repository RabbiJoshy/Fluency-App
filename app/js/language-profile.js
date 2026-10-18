// One language background per account, independent of any deck's skip policy.
import { sendOrQueue } from './sync-queue.js?v=856f738a';
import { getIsolatedSyncUser } from './env.js?v=856f738a';

const PREFIX = 'fluency_language_profile_v1';
const LEGACY = 'fluency_known_languages_v1';
const OWNER = 'fluency_language_profile_legacy_owner_v1';
const memory = new Map();
const account = () => typeof currentUser !== 'undefined' && currentUser && !currentUser.isGuest
    ? String(currentUser.initials) : 'guest';
const key = () => `${PREFIX}|${account()}`;
function get(key) { try { return localStorage.getItem(key); } catch (_) { return null; } }
function parse(raw) { try { return JSON.parse(raw); } catch (_) { return null; } }
function normalize(value) {
    if (!value || !Array.isArray(value.languages)) return null;
    return { schema: 1, languages: [...new Set(value.languages.filter(c => typeof c === 'string' && /^(?:[a-z]{2,3}|x-[a-z0-9-]+)$/.test(c)))],
        labels: Object.fromEntries(Object.entries(value.labels || {}).filter(([code, label]) => typeof label === 'string' && label.trim()).map(([code,label]) => [code,label.trim().slice(0,100)])),
        confirmed: value.confirmed === true, updatedAt: Number(value.updatedAt) || 0 };
}
function read() {
    const saved = normalize(parse(get(key()))) || memory.get(key());
    if (saved) return saved;
    // Adopt the old browser preference once; never seed unrelated accounts.
    const owner = get(OWNER);
    const legacy = parse(get(LEGACY));
    const isLegacyAccount = /^[A-Z]{2,4}$/.test(account());
    if (Array.isArray(legacy) && ((!owner && isLegacyAccount) || owner === account())) {
        const migrated = normalize({languages: legacy, confirmed: true, updatedAt: 0});
        store(migrated);
        try { localStorage.setItem(OWNER, account()); } catch (_) {}
        return migrated;
    }
    return {schema: 1, languages: ['en'], labels: {}, confirmed: false, updatedAt: 0};
}
function store(profile, source = 'local') {
    memory.set(key(), profile);
    try { localStorage.setItem(key(), JSON.stringify(profile)); } catch (_) {}
    window.dispatchEvent(new CustomEvent('language-profile-change', {detail: {source}}));
    return profile;
}
function queue(profile) {
    if (account() === 'guest') return;
    const syncUser = getIsolatedSyncUser(account());
    sendOrQueue({action: 'saveMeta', user: syncUser, metaKey: 'language-profile', metaId: 'profile',
        mode: 'all', language: 'all', value: JSON.stringify(profile),
        lastSeen: new Date(profile.updatedAt).toISOString()}, `meta|language-profile|${syncUser}`).catch(error =>
        console.warn('Could not queue language profile', error));
}
function save(languages, labels = read().labels || {}) {
    const profile = store(normalize({languages, labels, confirmed: true, updatedAt: Date.now()}));
    queue(profile);
    return profile;
}
function remote(rows, {full = false} = {}) {
    if (account() === 'guest' || !Array.isArray(rows)) return;
    const row = rows.find(r => r.metaKey === 'language-profile' && r.metaId === 'profile');
    const received = row && normalize(parse(row.value));
    let local = read();
    if (!received && full && !local.confirmed) {
        const guest = normalize(parse(get(`${PREFIX}|guest`)));
        if (guest?.confirmed) local = {...guest, updatedAt: Date.now()};
    }
    if (received && received.updatedAt >= local.updatedAt) store(received, 'remote');
    else if (local.confirmed && (received || full)) {
        const stamped = local.updatedAt ? local : {...local, updatedAt: Date.now()};
        store(stamped);
        queue(stamped);
    }
}
window.readLanguageProfile = read;
window.saveLanguageProfile = save;
window.applyRemoteLanguageProfile = remote;
