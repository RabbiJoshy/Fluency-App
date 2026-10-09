// Run against the exact runtime rules, using a local workspace's release files.
// Usage: node scripts/audit_estimation_pools.cjs /path/to/Fluency-Workspace
const fs = require('node:fs/promises');
const path = require('node:path');
const { createHarness, ROOT } = require('../tests/app/estimation_harness.cjs');
const workspace = path.resolve(process.argv[2] || '../Fluency-Workspace');
async function localFetch(url) {
    const value = String(url).split('?')[0];
    const file = value.startsWith('releases/') ? path.join(workspace, value) : path.join(ROOT, 'app', value);
    try {
        const data = await fs.readFile(file, 'utf8');
        return { ok: true, status: 200, json: async () => JSON.parse(data) };
    } catch (error) {
        if (error.code !== 'ENOENT') throw error;
        return { ok: false, status: 404 };
    }
}
(async () => {
    const config = JSON.parse(await fs.readFile(path.join(ROOT, 'app/config/config.json'), 'utf8'));
    const result = [];
    for (const [language, langConfig] of Object.entries(config.languages)) {
        const h = createHarness({ selectedLanguage: language, fetch: localFetch, console: { ...console, warn() {} } });
        if (!langConfig.capabilities?.speech) {
            result.push({ language, status: 'not_shipped' });
            continue;
        }
        try {
            const [vocabulary, frequency] = await Promise.all([
                h.loadEstimationVocabulary(langConfig), h.loadSpeechSourceFrequency(langConfig, { detached: true })
            ]);
            const pool = h.buildEstimationPool(vocabulary, frequency);
            const needingExamples = pool.filter(item => item.splitInfo && !item.estimationExample);
            const examples = await h.loadEstimationExamples(langConfig, [...new Set(needingExamples.map(item => Number(item.rank)))]);
            pool.forEach(item => h.attachEstimationExample(item, examples));
            const prepared = h.finalizeEstimationPool(pool);
            result.push({ language, status: 'measured', release: langConfig.indexPath,
                surfaces: vocabulary.length, eligibleSurfaces: prepared.placementWords.length,
                groups: prepared.items.length,
                mergedGroups: prepared.items.filter(item => item.estimationKey.startsWith('lemma:')).length,
                standaloneSurfaces: prepared.items.filter(item => item.estimationKey.startsWith('surface:')).length,
                splitReadings: prepared.items.filter(item => item.splitInfo).length,
                missingSplitExamples: pool.length - prepared.items.length,
                frequencySource: frequency?.source || null,
                missingFrequencies: vocabulary.filter(item => !h.estimationSurfaceFrequency(item, frequency)).length,
                hay: language === 'spanish' ? prepared.items.filter(item => item.word === 'hay').map(item => ({ key: item.estimationKey, members: item.estimationMembers.map(m => m.source.word) })) : undefined
            });
        } catch (error) {
            result.push({ language, status: 'unavailable', error: error.message });
        }
    }
    console.log(JSON.stringify(result, null, 2));
})().catch(error => { console.error(error); process.exitCode = 1; });
