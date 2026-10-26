// Build-time use of the same grounded, exact-title entity resolver as Turbo.
// No sense assignment. Cache misses and lookup failures retain their cards.
import fs from 'node:fs';
import path from 'node:path';
import { TurboEngine } from '../app/turbo/turbo-engine.js';
import { entityTitleMatchesQuery } from '../app/js/lexical-guards.js';
const [queriesFile, outputFile, existingCacheDir] = process.argv.slice(2);
const queries = JSON.parse(fs.readFileSync(queriesFile, 'utf8'));
const assets = JSON.parse(fs.readFileSync(new URL('../app/turbo/turbo_assets.json', import.meta.url), 'utf8'));
const engine = new TurboEngine(assets, {});
const results = fs.existsSync(outputFile) ? JSON.parse(fs.readFileSync(outputFile, 'utf8')) : {};
if (existingCacheDir && fs.existsSync(existingCacheDir)) {
    for (const file of fs.readdirSync(existingCacheDir).filter(f => f.startsWith('es_') && f.endsWith('.json'))) {
        const item = JSON.parse(fs.readFileSync(path.join(existingCacheDir, file), 'utf8'));
        if (!item) continue;
        const title = item.canonicalTitle || item.canonical_title;
        if (!item.query || !title || !entityTitleMatchesQuery(item.query, title)) continue;
        const entity = {...item, canonicalTitle: title, englishTitle: item.englishTitle || title,
            entityType: item.entityType || item.entity_type, source:'cached-wikipedia'};
        engine.entityCache.set(`es:${item.query.toLowerCase()}`, entity);
    }
}
const originalFetch = globalThis.fetch;
let throttled = false;
globalThis.fetch = async (url, opts = {}) => {
    const response = await originalFetch(url, {...opts, signal:AbortSignal.timeout(7000)});
    if (response.status === 429) throttled = true;
    return response;
};
const pending = queries.filter(word => !results[word]);
for (let i = 0; i < pending.length && !throttled; i += 12) {
    const batch = pending.slice(i, i + 12);
    const found = await engine.resolveEntitiesBatch(batch, 'es');
    for (const word of batch) {
        const entity = found.get(word) || null;
        if (throttled && !entity) continue;
        results[word] = {entity, entityRecognition: entity ? 'turbo-entity-candidate' : 'turbo-no-confident-entity'};
    }
    fs.writeFileSync(outputFile, JSON.stringify(results));
    console.log(`${Math.min(i+12,pending.length)}/${pending.length} checked; ${Object.values(results).filter(r=>r.entity).length} entity candidates`);
}
if (throttled) console.log('Provider throttled; remaining words retain pending entity status.');
