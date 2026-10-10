const assert = require('node:assert/strict');
const {createHarness} = require('./estimation_harness.cjs');
(async () => {
    const h = createHarness();
    const activeIndex = [{id: 'artist'}], activeExamples = { artist: {} };
    h._cachedJoinedIndex = activeIndex; h._cachedJoinedIndexPath = 'artist/index.json';
    h._cachedExamplesData = activeExamples; h._cachedExamplesDataPath = 'artist/examples.json';
    h.activeArtist = { name: 'Artist' };
    const config = { indexPath: 'speech/index.json', examplesPath: 'speech/examples.json',
        frequencyPath: 'frequency.json', mergeExceptionsPath: 'exceptions.json' };
    const shards = Array.from({length:9}, (_, i) => ({path:`rows-${i}.json`}));
    let inflight = 0, peak = 0, loads = 0;
    const progress = [];
    h.fetch = async url => {
        if (url.endsWith('vocabulary.index.manifest.json')) return {ok:true, json:async()=>({columns:'columns.json',shards})};
        if (url.endsWith('columns.json')) return {ok:true, json:async()=>({n:9, id:Array.from({length:9},(_,i)=>String(i)),word:Array.from({length:9},(_,i)=>`form${i}`),rank:Array.from({length:9},(_,i)=>i+1)})};
        if (url.includes('rows-')) {
            inflight++; loads++; peak = Math.max(peak, inflight);
            await new Promise(r=>setTimeout(r,1)); inflight--;
            const i = Number(url.match(/rows-(\d+)/)[1]);
            return {ok:true,json:async()=>({[i]:{meanings:[{headword:'root',pos:'VERB',translation:'meaning'}]}})};
        }
        if (url === 'exceptions.json') return {ok:true,json:async()=>({contractions:['form2']})};
        if (url === 'frequency.json') return {ok:true,json:async()=>({schema:'speech-source-frequency/v1',indexPath:'speech/index.json',values:{form0:100}})};
        if (url.endsWith('vocabulary.examples.manifest.json')) return {ok:true,json:async()=>({example_format:'slim-example/v1',sources:{},shards:[{path:'examples-1.json',start_rank:1,end_rank:3},{path:'examples-2.json',start_rank:4,end_rank:9}]})};
        if (url.endsWith('examples-1.json')) return {ok:true,json:async()=>({'0':{m:[[{t:'Target sentence',e:'English',s:'test'}]]}})};
        throw new Error('Unexpected fetch: '+url);
    };
    const words = await h.loadEstimationVocabulary(config,(done,total)=>progress.push([done,total]));
    assert.equal(words.length,9); assert.equal(words[2].is_contraction,true);
    assert.equal(words.every(item=>item.meanings.length === 1),true);
    assert.equal(peak,8); assert.deepEqual(progress,[[8,9],[9,9]]);
    assert.equal(await h.loadEstimationVocabulary(config),words); assert.equal(loads,9);
    assert.equal((await h.loadSpeechSourceFrequency(config,{detached:true})).values.form0,100);
    const examples = await h.loadEstimationExamples(config,[1]);
    assert.equal(examples['0'].m[0][0].target,'Target sentence');
    assert.equal(h._cachedJoinedIndex,activeIndex); assert.equal(h._cachedJoinedIndexPath,'artist/index.json');
    assert.equal(h._cachedExamplesData,activeExamples); assert.equal(h._cachedExamplesDataPath,'artist/examples.json');

    const retry = createHarness(); let fail = true;
    retry.fetch = async url => {
        if (url.endsWith('vocabulary.index.manifest.json')) return {ok:false,status:404};
        if (fail) return {ok:false,status:503};
        return {ok:true,json:async()=>[{id:'word',word:'word',rank:1,meanings:[]}]};
    };
    await assert.rejects(retry.loadEstimationVocabulary({indexPath:'other/index.json'}));
    fail=false;
    assert.equal((await retry.loadEstimationVocabulary({indexPath:'other/index.json'})).length,1);
    const incomplete = createHarness();
    incomplete.fetch = async url => {
        if (url.endsWith('vocabulary.index.manifest.json')) return {ok:true,json:async()=>({columns:'columns.json',shards:[{path:'rows.json'}]})};
        if (url.endsWith('columns.json')) return {ok:true,json:async()=>({n:2,id:['a','b'],word:['a','b'],rank:[1,2]})};
        return {ok:true,json:async()=>({a:{meanings:[]}})};
    };
    await assert.rejects(incomplete.loadEstimationVocabulary({indexPath:'partial/index.json'}), /incomplete/);

    // Precomputed estimation pool fast-path tests
    const precomputedHarness = createHarness();
    let precomputedFetches = 0;
    precomputedHarness.fetch = async url => {
        if (url === 'pools/es.json') {
            precomputedFetches++;
            return {
                ok: true,
                json: async () => ({
                    schema: 'estimation-pool/v1',
                    release: 'speech/index.json',
                    language: 'spanish',
                    n: 1,
                    items: [{
                        id: 'fast_word', word: 'rápido', rank: 1, stableRank: 1,
                        k: 'lemma:rápido', f: 50, r: 1, ak: 0,
                        m: [['ADJ', 'fast']],
                        mem: [[1, 1, 1, 0]]
                    }],
                    baseline: [[1, 1]]
                })
            };
        }
        throw new Error('Unexpected fetch in precomputed harness: ' + url);
    };

    // Missing estimationPoolPath returns null cleanly
    assert.equal(await precomputedHarness.loadPrecomputedEstimationPool({}), null);

    // 404 returns null cleanly
    precomputedHarness.fetch = async () => ({ ok: false, status: 404 });
    assert.equal(await precomputedHarness.loadPrecomputedEstimationPool({ estimationPoolPath: 'missing.json' }), null);

    // Valid precomputed pool hydrates cleanly and caches
    precomputedHarness.fetch = async url => ({
        ok: true,
        json: async () => ({
            schema: 'estimation-pool/v1',
            release: 'speech/index.json',
            language: 'spanish',
            n: 1,
            items: [{
                id: 'fast_word', word: 'rápido', rank: 1, stableRank: 1,
                k: 'lemma:rápido', f: 50, r: 1, ak: 0,
                m: [['ADJ', 'fast']],
                mem: [[1, 1, 1, 0]]
            }],
            baseline: [[1, 1]]
        })
    });
    const poolConfig = { estimationPoolPath: 'pools/es.json' };
    const pool = await precomputedHarness.loadPrecomputedEstimationPool(poolConfig);
    assert.ok(pool);
    assert.equal(pool.items.length, 1);
    assert.equal(pool.items[0].word, 'rápido');
    assert.equal(pool.items[0].meanings[0].translation, 'fast');
    assert.equal(pool.placementWords.length, 1);

    // Fast-path in startEstimation skips loadEstimationVocabulary completely
    let dynamicCalled = false;
    precomputedHarness.loadEstimationVocabulary = () => { dynamicCalled = true; throw new Error('Should not be called'); };
    precomputedHarness.config.languages.spanish = poolConfig;
    await precomputedHarness.startEstimation();
    assert.equal(dynamicCalled, false);
    assert.equal(precomputedHarness.estimationState.active, true);
    assert.equal(precomputedHarness.estimationState.currentWord.word, 'rápido');
    precomputedHarness.closeEstimationModal();

    // Shipped estimation pools contain valid, non-null stable ranks
    const fs = require('node:fs');
    const path = require('node:path');
    const { ROOT } = require('./estimation_harness.cjs');
    const shippedPools = ['spanish.json', 'portuguese.json', 'finnish.json', 'czech.json', 'french.json'];
    for (const poolFile of shippedPools) {
        const poolPath = path.join(ROOT, 'app/data/estimation-pools', poolFile);
        if (!fs.existsSync(poolPath)) continue;
        const poolJson = JSON.parse(fs.readFileSync(poolPath, 'utf8'));
        assert.ok(poolJson.items.length > 0, `Pool ${poolFile} should have items`);
        assert.ok(poolJson.baseline.length > 0, `Pool ${poolFile} should have baseline`);
        // Verify all baseline and item members have valid positive integer stableRank
        const nullBaseline = poolJson.baseline.filter(b => !Number.isInteger(b[1]) || b[1] <= 0);
        assert.equal(nullBaseline.length, 0, `Pool ${poolFile} has invalid baseline stable ranks`);
        const nullMem = poolJson.items.filter(i => (i.mem || []).some(m => !Number.isInteger(m[1]) || m[1] <= 0));
        assert.equal(nullMem.length, 0, `Pool ${poolFile} has invalid member stable ranks`);
    }

    // Hydrated precomputed pool produces differentiated placements across proficiency levels
    const spanishPoolData = JSON.parse(fs.readFileSync(path.join(ROOT, 'app/data/estimation-pools/spanish.json'), 'utf8'));
    const allButtons = Array.from({ length: 92 }, (_, i) => ({
        dataset: { startRank: String(i * 100 + 1), endRank: String((i + 1) * 100 + 1), rankBasis: 'stable' }
    }));
    const testHarness = createHarness({
        selectedLanguage: 'spanish',
        document: {
            querySelectorAll: sel => (sel.includes('level-btn') ? allButtons : []),
            querySelector: () => allButtons[0],
            getElementById: () => ({ textContent: '', hidden: false, style: {}, classList: { add() {}, remove() {}, contains: () => false } })
        }
    });
    testHarness.loadModule('ui.js');
    const preparedPool = testHarness.hydratePrecomputedEstimationPool(spanishPoolData);
    const testLevels = testHarness.getEstimationPlacementLevels(preparedPool.placementWords);
    assert.equal(testLevels.length, 92, 'Should resolve 92 speech placement levels');

    // Advanced learner (100% known) should place at highest levels
    const advancedBands = testHarness.buildEstimationBands(preparedPool.items);
    advancedBands.forEach(b => { b.answers = 2; b.known = 2; });
    const advancedPlacement = testHarness.calculateRecognitionPlacement(
        preparedPool.items, advancedBands, testLevels, preparedPool.placementWords
    );
    assert.ok(advancedPlacement.choices.length > 0, 'Advanced learner should have choices');
    assert.ok(advancedPlacement.choices[0].levelNumber > 50, 'Advanced learner should place in high levels');

    // Intermediate learner (known in early bands, unknown in late bands) should place in intermediate levels
    const intermediateBands = testHarness.buildEstimationBands(preparedPool.items);
    intermediateBands.forEach((b, i) => { b.answers = 2; b.known = i < 4 ? 2 : 0; });
    const intermediatePlacement = testHarness.calculateRecognitionPlacement(
        preparedPool.items, intermediateBands, testLevels, preparedPool.placementWords
    );
    assert.ok(intermediatePlacement.choices.length > 0, 'Intermediate learner should have choices');
    assert.ok(intermediatePlacement.choices[0].levelNumber >= 2 && intermediatePlacement.choices[0].levelNumber <= 15,
        'Intermediate learner should place in early-intermediate levels');

    // Beginner learner (0% known) should place at Level 1 Set 1
    const beginnerBands = testHarness.buildEstimationBands(preparedPool.items);
    beginnerBands.forEach(b => { b.answers = 2; b.known = 0; });
    const beginnerPlacement = testHarness.calculateRecognitionPlacement(
        preparedPool.items, beginnerBands, testLevels, preparedPool.placementWords
    );
    assert.ok(beginnerPlacement.choices.length > 0, 'Beginner learner should have choices');
    assert.equal(beginnerPlacement.choices[0].levelNumber, 1, 'Beginner learner should place at level 1');
    assert.equal(beginnerPlacement.choices[0].setNumber, 1, 'Beginner learner should place at set 1');

    console.log('Detached metadata, precomputed pool fast-path, bounded loading, frequency matching, lazy examples and retry checks passed.');
})().catch(error=>{console.error(error);process.exitCode=1;});
