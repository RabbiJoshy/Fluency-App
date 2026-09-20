// One Fast Track choice per language. The legacy global study defaults seed a
// language until it has its own choice; they are never changed by this module.
import { sendOrQueue } from './sync-queue.js?v=20260825ak';

const PREFIX = 'fluency_fast_track_v1';
const LEGACY_KEY = 'fluency_global_study_defaults_v1';
const META_KEY = 'fast-track';

function account() {
    return currentUser && !currentUser.isGuest ? String(currentUser.initials) : 'guest';
}

function key(language, user = account()) {
    return `${PREFIX}|${user}|${String(language || 'spanish').toLowerCase()}`;
}

function normalize(value) {
    if (!value || typeof value !== 'object') return null;
    const merge = value.merge === true;
    const skip = value.skip === true;
    return {
        enabled: value.enabled === true && (merge || skip),
        merge, skip,
        updatedAt: Number(value.updatedAt) || 0
    };
}

function seed() {
    try {
        const old = JSON.parse(localStorage.getItem(LEGACY_KEY) || 'null') || {};
        const merge = old.mergeLemmas === true;
        const skip = old.excludeCognates === true;
        return { enabled: merge || skip, merge, skip, updatedAt: 0 };
    } catch (_) {
        return { enabled: false, merge: false, skip: false, updatedAt: 0 };
    }
}

export function readFastTrack(language) {
    try {
        return normalize(JSON.parse(localStorage.getItem(key(language)) || 'null')) || seed();
    } catch (_) {
        return seed();
    }
}

function writeLocal(language, preference, source = 'local') {
    const normalized = normalize(preference);
    if (!normalized) return null;
    try { localStorage.setItem(key(language), JSON.stringify(normalized)); } catch (_) {}
    window.dispatchEvent(new CustomEvent('fast-track-preference-change', { detail: { language, source } }));
    return normalized;
}

export function saveFastTrack(language, changes) {
    const previous = readFastTrack(language);
    const preference = writeLocal(language, { ...previous, ...changes, updatedAt: Date.now() });
    if (preference && currentUser && !currentUser.isGuest) {
        sendOrQueue({
            action: 'saveMeta', user: currentUser.initials, metaKey: META_KEY,
            metaId: language, mode: 'all', language, value: JSON.stringify(preference),
            lastSeen: new Date(preference.updatedAt).toISOString()
        }, `meta|fast-track|${currentUser.initials}|${language}`).catch(error =>
            console.warn('Could not queue Fast Track preference', error));
    }
    return preference;
}

// Progress already loads metadata for the whole account. Reuse that reply, and
// let a pending local edit win over an older server copy until it syncs.
export function applyRemoteFastTrack(metaRows, { full = false } = {}) {
    if (!currentUser || currentUser.isGuest || !Array.isArray(metaRows)) return;
    const remoteLanguages = new Set();
    for (const row of metaRows) {
        if (row.metaKey !== META_KEY || !row.language) continue;
        remoteLanguages.add(row.language);
        let remote;
        try { remote = normalize(JSON.parse(row.value)); } catch (_) { continue; }
        if (!remote) continue;
        const local = readFastTrack(row.language);
        if (remote.updatedAt > local.updatedAt) writeLocal(row.language, remote, 'remote');
        else if (local.updatedAt > remote.updatedAt) saveFastTrack(row.language, local);
    }
    // Carry an existing global choice into the account once. Unchanged Off is
    // the default and needs no remote row.
    if (!full) return;
    for (const language of Object.keys(globalThis.config?.languages || {})) {
        if (remoteLanguages.has(language)) continue;
        const local = readFastTrack(language);
        if (local.updatedAt || local.enabled) saveFastTrack(language, local);
    }
}
