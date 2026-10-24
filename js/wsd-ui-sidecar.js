// Release-pinned assignment overlay. Source releases and progress IDs stay intact.
import { readJsonWithTimeout } from './read-request.js?v=70c90599';

const sidecars = new Map();

export function validateWsdUiSidecar(payload, langConfig) {
    if (payload?.schema !== 'wsd-ui-sidecar/v1' || !payload.release_id
        || !String(langConfig?.indexPath || '').includes(`/${payload.release_id}/`)) {
        throw new Error('WSD sidecar does not match this vocabulary release');
    }
    if (!payload.cards || typeof payload.cards !== 'object' || Array.isArray(payload.cards)) {
        throw new Error('WSD sidecar has no card assignments');
    }
    for (const [id, card] of Object.entries(payload.cards)) {
        if (!Array.isArray(card.meanings) || !Array.isArray(card.examples?.m)
            || card.meanings.length !== card.examples.m.length) {
            throw new Error(`Invalid WSD sidecar buckets for ${id}`);
        }
        card.meanings.forEach((meaning, index) => {
            if (meaning._masterSenseIndex !== index || !Array.isArray(card.examples.m[index])) {
                throw new Error(`Invalid WSD sidecar sense index for ${id}`);
            }
        });
    }
    return payload;
}

export async function loadWsdUiSidecar(langConfig) {
    const path = langConfig?.wsdSidecarPath;
    if (!path) return null;
    // The same language config may select a candidate release on staging.
    // Its source-specific sidecar must never leak into another release.
    const pinnedRelease = langConfig?.wsdSidecarRelease;
    if (!pinnedRelease || !String(langConfig?.indexPath || '').includes(`/${pinnedRelease}/`)) return null;
    const key = `${path}:${pinnedRelease}`;
    if (!sidecars.has(key)) {
        const pending = readJsonWithTimeout(path).then(({ response, data }) => {
            if (!response.ok) throw new Error(`WSD sidecar HTTP ${response.status}`);
            return validateWsdUiSidecar(data, langConfig);
        }).catch(error => { sidecars.delete(key); throw error; });
        sidecars.set(key, pending);
    }
    return sidecars.get(key);
}

export function wsdUiCard(sidecar, shortId, surfaceCardId = null) {
    if (!sidecar) return null;
    return sidecar.cards[surfaceCardId || sidecar.card_ids?.[shortId] || shortId] || null;
}

export function applyWsdUiIndex(rows, sidecar) {
    if (!sidecar) return rows;
    for (const row of rows || []) {
        const patch = wsdUiCard(sidecar, row.id, row.surface_card_id);
        if (!patch) continue;
        const allMeanings = JSON.parse(JSON.stringify(patch.meanings));
        // Source bucket positions remain on _masterSenseIndex even when a
        // corrected sense has no remaining uses. Keep such senses in the menu,
        // rather than presenting a zero-evidence row on the main card.
        const key = meaning => meaning.source_sense_id
            || (String(meaning.source_reference || '').startsWith('kaikki:')
                ? meaning.source_reference.slice('kaikki:'.length) : null)
            || meaning.sense_id
            || [meaning.pos, meaning.headword, meaning.translation].join('\u0000');
        const used = new Set(allMeanings.filter(m => Number(m.frequency) > 0).map(key));
        const unused = new Map((row.unused_menu_senses || []).map(m => [key(m), m]));
        for (const meaning of allMeanings) {
            if (Number(meaning.frequency) <= 0 && !meaning.unassigned) unused.set(key(meaning), meaning);
        }
        row.unused_menu_senses = [...unused.values()].filter(m => !used.has(key(m)));
        row.meanings = allMeanings.filter(m => Number(m.frequency) > 0);
        // Deck construction mutates meanings; its restore template must carry
        // the same overlay, rather than resurrecting the original assignments.
        row._base_meanings = JSON.parse(JSON.stringify(row.meanings));
        if (patch.wsd_distribution) row.wsd_distribution = JSON.parse(JSON.stringify(patch.wsd_distribution));
        row.wsd_ui_sidecar = { release_id: sidecar.release_id, sidecar_id: sidecar.sidecar_id || null,
            method: sidecar.method || 'jev',
            frequency_basis: patch.frequency_basis || sidecar.frequency_basis || 'exported_examples' };
        delete row._visibleSenseMergeOverlay;
    }
    return rows;
}

export function wsdUiExamplePayload(payload, sidecar) {
    if (!sidecar) return {};
    const result = {};
    for (const id of Object.keys(payload || {})) {
        const card = wsdUiCard(sidecar, id);
        if (card) result[id] = card.examples;
    }
    return result;
}
