// Build compact precomputed estimation pool assets for shipped languages.
// Reads release files from local Fluency-Workspace and generates single-file JSON
// payloads in app/data/estimation-pools/<language>.json.
//
// Usage: node scripts/build_estimation_pools.cjs [/path/to/Fluency-Workspace]
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

async function buildPoolForLanguage(language, langConfig) {
    const h = createHarness({
        selectedLanguage: language,
        fetch: localFetch,
        console: { ...console, warn() {} }
    });

    const [vocabulary, frequency] = await Promise.all([
        h.loadEstimationVocabulary(langConfig),
        h.loadSpeechSourceFrequency(langConfig, { detached: true })
    ]);

    const pool = h.buildEstimationPool(vocabulary, frequency, { includeAssumed: true });
    const needingExamples = pool.filter(item => item.splitInfo && !item.estimationExample);
    const ranks = [...new Set(needingExamples.map(item => Number(item.rank)))];
    if (ranks.length) {
        const examples = await h.loadEstimationExamples(langConfig, ranks);
        pool.forEach(item => h.attachEstimationExample(item, examples));
    }
    const prepared = h.finalizeEstimationPool(pool);

    const slimItems = prepared.items.map(item => ({
        id: item.id,
        word: item.word,
        rank: item.rank,
        stableRank: item.stableRank,
        k: item.estimationKey,
        f: item.estimationFrequency,
        r: item.estimationRank,
        ak: item.estimationAssumedKnown ? 1 : undefined,
        ex: item.estimationExample || undefined,
        split: item.splitInfo ? 1 : undefined,
        m: (item.meanings || []).map(m => [
            m.pos || '',
            m.translation || m.meaning || ''
        ]),
        mem: item.estimationMembers.map(m => [
            m.source.rank,
            m.source.stableRank,
            m.weight === 1 ? 1 : Math.round(m.weight * 1000) / 1000,
            m.assumedKnown ? 1 : 0
        ])
    }));

    const slimPlacement = prepared.placementWords.map(s => [s.rank, s.stableRank]);

    return {
        schema: 'estimation-pool/v1',
        release: langConfig.indexPath,
        language,
        n: slimItems.length,
        items: slimItems,
        baseline: slimPlacement
    };
}

(async () => {
    const config = JSON.parse(await fs.readFile(path.join(ROOT, 'app/config/config.json'), 'utf8'));
    const outputDir = path.join(ROOT, 'app/data/estimation-pools');
    await fs.mkdir(outputDir, { recursive: true });

    for (const [language, langConfig] of Object.entries(config.languages)) {
        if (!langConfig.capabilities?.speech || !langConfig.indexPath) {
            continue;
        }

        console.log(`Building estimation pool for ${language}...`);
        try {
            const payload = await buildPoolForLanguage(language, langConfig);
            const outFile = path.join(outputDir, `${language}.json`);
            const content = JSON.stringify(payload);
            await fs.writeFile(outFile, content, 'utf8');
            console.log(`  -> Wrote ${outFile} (${payload.n} groups, ${(content.length / 1024).toFixed(1)} KB)`);
        } catch (error) {
            console.warn(`  Skipping ${language}: ${error.message}`);
        }
    }
    console.log('Estimation pool generation complete.');
})().catch(error => {
    console.error(error);
    process.exitCode = 1;
});
