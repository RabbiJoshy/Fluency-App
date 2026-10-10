// Environment detection, environment identification, and storage/sync isolation.
// This module defines the contract between production and staging environments.

export function detectEnvironment() {
    if (typeof window === 'undefined') {
        return { env: 'production', isStaging: false };
    }
    const explicit = window.__FLUENCY_ENV__ || window.__FLUENCY_ENVIRONMENT__;
    if (explicit === 'staging') return { env: 'staging', isStaging: true };
    if (explicit === 'production') return { env: 'production', isStaging: false };

    const host = window.location.hostname || '';
    const isStagingHost = host.includes('pages.dev') ||
                          host.includes('staging') ||
                          host.startsWith('stg.');
    return {
        env: isStagingHost ? 'staging' : 'production',
        isStaging: isStagingHost
    };
}

const envInfo = detectEnvironment();
export const ENV_NAME = envInfo.env;
export const IS_STAGING = envInfo.isStaging;

// Storage isolation:
// Staging uses a dedicated IndexedDB database name so local-first offline
// transactions and stores never contend with or pollute production data.
export const OFFLINE_DB_NAME = IS_STAGING ? 'fluency-offline-staging' : 'fluency-offline';

// Sync user isolation:
// When staging connects to the backend sync service, user identifiers are namespaced
// (e.g. 'stg_JST') so production progress rows (review_events, item_state, user_meta)
// in Cloudflare D1 and Google Sheets remain 100% untouched and protected.
export function getIsolatedSyncUser(initialsOrId) {
    if (!initialsOrId) return '';
    if (!IS_STAGING) return initialsOrId;
    const str = String(initialsOrId);
    return str.startsWith('stg_') ? str : `stg_${str}`;
}

// Staging candidate deck selection:
// Staging allows selecting candidate deck versions independently of production
// without modifying production data or requiring duplicate infrastructure.
const CANDIDATE_STORAGE_KEY = 'fluency_candidate_decks';

export function getCandidateDeckOverrides() {
    if (typeof window === 'undefined') return {};
    try {
        const stored = localStorage.getItem(CANDIDATE_STORAGE_KEY);
        return stored ? JSON.parse(stored) : {};
    } catch (_) {
        return {};
    }
}

export function setCandidateDeckOverride(langKey, releaseIdOrPath) {
    if (typeof window === 'undefined') return;
    try {
        const current = getCandidateDeckOverrides();
        if (releaseIdOrPath) {
            current[langKey] = releaseIdOrPath;
        } else {
            delete current[langKey];
        }
        localStorage.setItem(CANDIDATE_STORAGE_KEY, JSON.stringify(current));
    } catch (_) {}
}

export function clearCandidateDeckOverrides() {
    if (typeof window === 'undefined') return;
    try {
        localStorage.removeItem(CANDIDATE_STORAGE_KEY);
    } catch (_) {}
}
