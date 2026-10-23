// Admin-only setup filters: single-sense words, and which assignment layer a
// card shows. Classification follows the live precedence: Jev sidecar >
// DeepSeek (at least one accepted correction) > original. Rows are stamped once
// per loaded index; filtering never touches card IDs, progress or assignments.
import { readJsonWithTimeout } from './read-request.js?v=1';
import { wsdUiCard } from './wsd-ui-sidecar.js?v=1';

export const assignmentFilter = { excludeSingleSense: false, source: 'all' };
const indexes = new Map();
let activeFiltersAvailable = false;

export function validateAssignmentFilterIndex(payload, langConfig) {
    if (payload?.schema !== 'assignment-filter-index/v1' || !payload.release_id
        || !String(langConfig?.indexPath || '').includes(`/${payload.release_id}/`)
        || !Array.isArray(payload.single_sense) || !Array.isArray(payload.deepseek)) {
        throw new Error('Assignment filter index does not match this vocabulary release');
    }
    return payload;
}

async function loadAssignmentFilterIndex(langConfig) {
    const path = langConfig?.assignmentFilterPath;
    if (!path) return null;
    if (!indexes.has(path)) {
        const pending = readJsonWithTimeout(path).then(({ response, data }) => {
            if (!response.ok) throw new Error(`Assignment filter index HTTP ${response.status}`);
            return validateAssignmentFilterIndex(data, langConfig);
        }).catch(error => { indexes.delete(path); throw error; });
        indexes.set(path, pending);
    }
    return indexes.get(path);
}

export function stampAssignmentFilters(rows, index, sidecar) {
    if (!index || !Array.isArray(rows)) {
        activeFiltersAvailable = false;
        return rows;
    }
    const single = new Set(index.single_sense);
    const deepseek = new Set(index.deepseek);
    for (const row of rows) {
        row._assignSrc = wsdUiCard(sidecar, row.id, row.surface_card_id) ? 'jev'
            : deepseek.has(row.id) ? 'deepseek' : 'original';
        row._singleSense = single.has(row.id);
    }
    activeFiltersAvailable = rows.length > 0 && Boolean(rows[0]._assignSrc);
    return rows;
}

// Failing to load the optional index must never block the deck: the filters
// then simply stay unavailable.
export async function prepareAssignmentFilters(rows, langConfig, sidecar) {
    try {
        const index = await loadAssignmentFilterIndex(langConfig);
        stampAssignmentFilters(rows, index, sidecar);
    } catch (error) {
        activeFiltersAvailable = false;
        console.warn('Assignment filters unavailable:', error);
    }
    globalThis.syncAssignmentFilterControls?.();
}

export function assignmentFiltersAvailable() {
    return (activeFiltersAvailable
        || Boolean(globalThis.cachedVocabularyData?.[0]?._assignSrc)
        || Boolean(globalThis._cachedJoinedIndex?.[0]?._assignSrc)
        || Boolean(globalThis.window?._cachedJoinedIndex?.[0]?._assignSrc)
        || Boolean(globalThis.setupVocabularySnapshot?.[0]?._assignSrc))
        && !globalThis.activeArtist && !globalThis.playlistLiveActive?.();
}

export function passesAssignmentFilters(row) {
    if (!row?._assignSrc || !globalThis.isAuditAccount?.()
        || globalThis.activeArtist || globalThis.playlistLiveActive?.()) return true;
    if (assignmentFilter.excludeSingleSense && row._singleSense) return false;
    return assignmentFilter.source === 'all' || row._assignSrc === assignmentFilter.source;
}

globalThis.assignmentFilter = assignmentFilter;
globalThis.assignmentFiltersAvailable = assignmentFiltersAvailable;
