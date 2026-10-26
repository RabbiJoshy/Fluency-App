// Display-only measurements, joined to selected corpus examples by sentence id.
// Release-bound companions let existing immutable decks expose their cached
// scores. New releases carry the same metadata directly in their examples.
export function exampleTranslationAlignment(example) {
    const score = example?.metadata?.translation_alignment?.score;
    return typeof score === 'number' && Number.isFinite(score) && score >= -1 && score <= 1
        ? score : null;
}

export function attachAlignmentScores(payload, scores, manifest) {
    for (const card of Object.values(payload || {})) {
        const examples = [...(card.m || []).flat(), ...(card.u || [])];
        for (const example of examples) {
            // A native measurement belongs to its release; a companion must
            // never replace it with a newer or missing cache observation.
            if (exampleTranslationAlignment(example) !== null) continue;
            const sentenceId = example.metadata?.sentence_id;
            const score = scores[sentenceId];
            example.metadata ||= {};
            example.metadata.translation_alignment = typeof score === 'number'
                && Number.isFinite(score) && score >= -1 && score <= 1
                ? { score, model: manifest.model, version: manifest.alignment_version }
                : null;
        }
    }
    return payload;
}

export function createExampleAlignmentLoader({ readJson, releaseUrl }) {
    const loads = new Map();
    const read = path => {
        if (!loads.has(path)) {
            const pending = readJson(path).then(({ response, data }) => {
                if (!response.ok) throw new Error(`HTTP ${response.status}: ${path}`);
                return data;
            }).catch(error => { loads.delete(path); throw error; });
            loads.set(path, pending);
        }
        return loads.get(path);
    };
    return async (payload, langConfig) => {
        const path = langConfig?.exampleAlignmentPath;
        if (!path || !payload) return payload;
        try {
            const manifest = await read(path);
            if (manifest.schema !== 'example-alignment/v1' || !manifest.model || !manifest.alignment_version
                || releaseUrl(manifest.examplesPath) !== langConfig.examplesPath) return payload;
            const shardPaths = [...new Set(Object.keys(payload)
                .map(id => manifest.card_shards?.[id]).filter(Boolean))];
            const base = path.slice(0, path.lastIndexOf('/') + 1);
            const shards = await Promise.all(shardPaths.map(shard => read(base + shard)));
            const scores = Object.assign({}, ...shards);
            return attachAlignmentScores(payload, scores, manifest);
        } catch (error) {
            // Offline or missing companion: keep every example and its old order.
            console.warn('Example alignment unavailable:', error);
            return payload;
        }
    };
}
