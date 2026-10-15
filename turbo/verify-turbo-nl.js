import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';
import { TurboEngine } from './turbo-engine.js';

const __dirname = path.dirname(fileURLToPath(import.meta.url));

async function main() {
    console.log('--- TURBO Dutch Node Verification Test ---');
    const startLoad = performance.now();
    const assetsPath = path.join(__dirname, 'nl_turbo_assets.json');
    const songsPath = path.join(__dirname, 'nl_probe_songs.json');
    const data50kPath = path.join(__dirname, 'nl_50k_data.json');

    const assets = JSON.parse(fs.readFileSync(assetsPath, 'utf8'));
    const songs = JSON.parse(fs.readFileSync(songsPath, 'utf8'));
    const data50k = JSON.parse(fs.readFileSync(data50kPath, 'utf8'));

    console.log(`Loaded assets: ${Object.keys(assets.dictionary).length} dict words, ${Object.keys(assets.mwes).length} MWEs, ${Object.keys(assets.elisions).length} elisions in ${(performance.now() - startLoad).toFixed(1)} ms`);
    console.log(`Loaded ${songs.length} Dutch probe songs.`);

    const engine = new TurboEngine(assets, data50k);

    console.log('\nRunning Turbo intake pipeline on probe songs...');
    const result = await engine.processPlaylist(songs.slice(0, 5), {
        onProgress: ({ stage, message }) => {
            console.log(`  [Stage ${stage}]: ${message}`);
        }
    });

    console.log('\n--- Test Run Results ---');
    console.log(`Speed: ${result.elapsedMs} ms total pipeline execution time`);
    console.log(`Total Cards Produced: ${result.totalCards}`);
    console.log(`  Word Cards: ${result.wordCardsCount}`);
    console.log(`  MWE Idiom Cards: ${result.mweCardsCount}`);
    console.log(`  Wikipedia Entity Cards: ${result.entityCardsCount}`);

    console.log('\nTop 10 Playlist Cards:');
    result.cards.slice(0, 10).forEach(c => {
        console.log(`  #${c.rank} [${c.type.toUpperCase()}] ${c.word} (${c.playlistCount}x) -> "${c.translation}" | Ex: "${c.examples[0]?.text}"`);
    });

    if (result.cards.some(c => c.type === 'entity')) {
        console.log('\nSample Entity Cards:');
        result.cards.filter(c => c.type === 'entity').slice(0, 5).forEach(c => {
            console.log(`  - ${c.word} (${c.entity?.entityType}): ${c.translation}`);
        });
    }

    if (result.elapsedMs < 10000 && result.totalCards > 20) {
        console.log('\n✅ VERIFICATION PASSED: Dutch Turbo Intake is fast and accurate.');
    } else {
        console.error('\n❌ VERIFICATION FAILED');
        process.exit(1);
    }
}

main().catch(err => {
    console.error('Test error:', err);
    process.exit(1);
});
