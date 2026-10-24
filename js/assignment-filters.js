// Admin-only setup filters: single-sense words, assignment layers, Jev confidence/gaps,
// and parts of speech. Classification follows live precedence: Jev sidecar >
// DeepSeek (at least one accepted correction) > original. Rows are stamped once
// per loaded index; filtering never touches card IDs, progress or assignments.
import { readJsonWithTimeout } from './read-request.js?v=394bc622';
import { wsdUiCard } from './wsd-ui-sidecar.js?v=394bc622';

export const assignmentFilter = {
    excludeSingleSense: false,
    source: 'all',       // 'all' | 'deepseek' | 'jev' | 'original'
    confidence: 'all',   // 'all' | 'lowest' | 'marginal' | 'close' | 'unresolved' | 'high'
    pos: 'all'           // 'all' | 'verb' | 'noun' | 'adj' | 'adv' | 'function' | 'other'
};

const indexes = new Map();
let activeFiltersAvailable = false;

export function activeFilterCount() {
    let count = 0;
    if (assignmentFilter.excludeSingleSense) count++;
    if (assignmentFilter.source !== 'all') count++;
    if (assignmentFilter.confidence !== 'all') count++;
    if (assignmentFilter.pos !== 'all') count++;
    return count;
}

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

export function getRowPosSet(row) {
    const set = new Set();
    if (row.function_word) set.add('function');
    for (const m of row.meanings || []) {
        const p = (m.pos || '').toLowerCase();
        if (p === 'verb') set.add('verb');
        else if (p === 'noun') set.add('noun');
        else if (p === 'adj') set.add('adj');
        else if (p === 'adv') set.add('adv');
        else if (['prep', 'pron', 'conj', 'det', 'article'].includes(p)) set.add('function');
        else if (p) set.add('other');
    }
    if (set.size === 0) set.add('other');
    return set;
}

export function stampAssignmentFilters(rows, index, sidecar) {
    if (!index || !Array.isArray(rows)) {
        activeFiltersAvailable = false;
        return rows;
    }
    const single = new Set(index.single_sense);
    const deepseek = new Set(index.deepseek);
    for (const row of rows) {
        const patch = wsdUiCard(sidecar, row.id, row.surface_card_id);
        row._assignSrc = patch ? 'jev'
            : deepseek.has(row.id) ? 'deepseek' : 'original';
        row._singleSense = single.has(row.id);
        row._pos = getRowPosSet(row);

        // Confidence & unresolved status from Jev
        if (patch) {
            let minConf = 1.0;
            let hasUnres = false;
            if (patch.counts) {
                for (const [st, cnt] of Object.entries(patch.counts)) {
                    if (st !== 'assigned' && cnt > 0) hasUnres = true;
                }
            }
            if (patch.examples?.m) {
                for (const bucket of patch.examples.m) {
                    for (const ex of bucket || []) {
                        const ju = ex.ju || {};
                        if (ju.confidence !== undefined && ju.confidence !== null) {
                            minConf = Math.min(minConf, Number(ju.confidence));
                        }
                        if (ju.status && ju.status !== 'assigned') {
                            hasUnres = true;
                        }
                    }
                }
            }
            row._minConfidence = minConf;
            row._hasUnresolved = hasUnres;
        } else {
            row._minConfidence = null;
            row._hasUnresolved = false;
        }
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

    // 1. Exclude single-sense words
    if (assignmentFilter.excludeSingleSense && row._singleSense) return false;

    // 2. Assignment source
    if (assignmentFilter.source !== 'all' && row._assignSrc !== assignmentFilter.source) return false;

    // 3. Jev confidence / uncertainty
    if (assignmentFilter.confidence !== 'all') {
        const conf = assignmentFilter.confidence;
        if (conf === 'unresolved') {
            if (!row._hasUnresolved) return false;
        } else if (conf === 'lowest') {
            if (row._minConfidence === null || row._minConfidence >= 0.2) return false;
        } else if (conf === 'marginal') {
            if (row._minConfidence === null || row._minConfidence >= 0.3) return false;
        } else if (conf === 'close') {
            if (row._minConfidence === null || row._minConfidence >= 0.5) return false;
        } else if (conf === 'high') {
            if (row._minConfidence === null || row._minConfidence < 0.8) return false;
        }
    }

    // 4. Part of Speech
    if (assignmentFilter.pos !== 'all') {
        if (!row._pos || !row._pos.has(assignmentFilter.pos)) return false;
    }

    return true;
}

globalThis.assignmentFilter = assignmentFilter;
globalThis.assignmentFiltersAvailable = assignmentFiltersAvailable;
globalThis.activeFilterCount = activeFilterCount;
