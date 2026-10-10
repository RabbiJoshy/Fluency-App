const assert = require('node:assert/strict');
const { createHarness } = require('./estimation_harness.cjs');
const sense = (headword, translation, frequency = 1, extra = {}) =>
    ({ headword, translation, frequency, pos: 'VERB', ...extra });
const surface = (word, rank, meanings, extra = {}) =>
    ({ word, id: word, lemma: meanings[0]?.headword, rank, stableRank: rank, meanings, ...extra });
const split = (word = 'fue', rank = 30) => surface(word, rank, [
    sense('ser', 'was', 70, { canonical_example: { text: 'Fue una buena idea.' } }),
    sense('ser', 'existed', 10),
    sense('ir', 'went', 15, { canonical_example: { text: 'Fue a Madrid.' } }),
    sense('ir', 'departed', 5)
]);
function setup(items, values = {}) {
    const h = createHarness();
    h.input = items; h.frequency = { values };
    h.pool = h.buildEstimationPool(items, h.frequency);
    return h;
}
(async () => {
    let h = setup([
        surface('hablar', 10, [sense('hablar', 'to speak')]),
        surface('hablo', 11, [sense('hablar', 'I speak')]),
        surface('hablas', 12, [sense('hablar', 'you speak')]),
        surface('casa', 20, [sense('casa', 'house', 1, { pos: 'NOUN' })])
    ], { hablar: 4, hablo: 9, hablas: 3, casa: 12 });
    assert.equal(h.pool.length, 2);
    assert.equal(h.pool[0].word, 'hablo');
    assert.equal(h.pool[0].estimationFrequency, 16);
    assert.equal(h.pool[0].estimationMembers.length, 3);
    h.run('estimationState = createEstimationState(); estimationState.validWords = pool; estimationState.bands = buildEstimationBands(pool);');
    const first = h.pickWordFromBand(0);
    h.run('estimationState.shownWordIds.add(getWordKey(pool[0]));');
    assert.equal(h.pickWordFromBand(0).word, 'casa');
    h.run('estimationState.shownWordIds.add(getWordKey(pool[1]));');
    assert.equal(h.pickWordFromBand(0), null);

    h = setup([
        surface('casó', 10, [sense('casar', 'married')]),
        surface('casado', 20, [sense('casar', 'married'), sense('casado', 'husband')]),
        surface('sé', 30, [sense('saber', 'know'), sense('no sé', "I do not know", 1, { pos: 'PHRASE' })]),
        surface('sabe', 40, [sense('saber', 'knows')]),
        surface('contraction', 50, [sense('saber', 'know')], { is_contraction: true })
    ]);
    assert.equal(h.pool.length, 5);
    assert.ok(h.pool.find(item => item.word === 'casado').estimationKey.startsWith('surface:'));
    assert.ok(h.pool.find(item => item.word === 'sé').estimationKey.startsWith('surface:'));
    assert.ok(h.pool.find(item => item.word === 'contraction').estimationKey.startsWith('surface:'));
    assert.equal(h.buildEstimationPool([surface('bad', 1, [])]).length, 0);
    assert.equal(h.buildEstimationPool([surface('yo', 1, [sense('yo', 'I', 1, { pos: 'PRON' })])]).length, 0);
    assert.equal(h.buildEstimationPool([surface('noisy', 1, [sense('noise', 'noise')], { is_noise: true })]).length, 0);

    h = setup([split()], { fue: 100 });
    assert.equal(h.pool.length, 2);
    assert.equal(h.pool[0].estimationFrequency, 80);
    assert.equal(h.pool[1].estimationFrequency, 20);
    assert.equal(h.pool.reduce((sum, item) => sum + item.estimationMembers[0].weight, 0), 1);
    assert.match(h.pool[0].estimationExample, /idea/);
    assert.match(h.pool[1].estimationExample, /Madrid/);
    assert.equal(h.getWordTranslation(h.pool[0]).includes('went'), false);
    assert.equal(h.getWordTranslation(h.pool[1]).includes('was'), false);
    h.run('estimationState = createEstimationState(); estimationState.validWords = pool; estimationState.bands = buildEstimationBands(pool); estimationState.shownWordIds.add(getWordKey(pool[0]));');
    assert.equal(h.pickWordFromBand(0).estimationKey, h.pool[1].estimationKey);
    const prepared = h.finalizeEstimationPool(h.pool);
    assert.equal(prepared.items.length, 2);
    assert.equal(prepared.placementWords.length, 1);
    h.pool[1].estimationExample = '';
    assert.equal(h.finalizeEstimationPool(h.pool).items.length, 1);
    h.attachEstimationExample(h.pool[1], { fue: { m: [[], [], [{ target: 'Fue a Sevilla.' }], []] } });
    // canonical text remains associated with this reading, not its sibling.
    assert.match(h.pool[1].estimationExample, /Madrid/);
    const noExamples = split(); noExamples.meanings.forEach(m => { delete m.canonical_example; });
    h = setup([noExamples], { fue: 100 });
    assert.equal(h.finalizeEstimationPool(h.pool).items.length, 0);
    h.attachEstimationExample(h.pool[1], { fue: { m: [[], [], [{ target: 'Fue a Sevilla.' }], []] } });
    assert.match(h.pool[1].estimationExample, /Sevilla/);
    const noShares = split(); noShares.meanings.forEach(m => { delete m.frequency; });
    assert.equal(h.buildEstimationPool([noShares]).length, 0);

    // Placement expands merged groups into member surfaces, while the UI
    // reports groups. Old rank values remain what persistence receives.
    h = setup([
        surface('hablar', 10, [sense('hablar', 'speak')]),
        surface('hablo', 20, [sense('hablar', 'speak')]),
        surface('casa', 150, [sense('casa', 'house', 1, { pos: 'NOUN' })])
    ], { hablar: 50, hablo: 60, casa: 5 });
    h.run(`estimationState = createEstimationState();
        const prepared = finalizeEstimationPool(pool);
        estimationState.validWords = prepared.items;
        estimationState.placementWords = prepared.placementWords;
        estimationState.maxLevel = prepared.items.length;
        estimationState.bands = buildEstimationBands(prepared.items);
        estimationState.bands[0].answers = 3; estimationState.bands[0].known = 3;
        showEstimationResult();`);
    assert.equal(h.estimationState.groupEstimate.point, 2);
    assert.equal(h.estimationState.estimatedLevel, 20);
    assert.match(h.elements.get('estimationResultDesc').textContent, /vocabulary groups: about 2/);
    assert.equal(/CEFR|A1|B2|C2/.test(h.elements.get('estimationResultDesc').textContent), false);
    await h.useEstimatedLevel();
    assert.equal(h.savedRank, 20);
    assert.equal(h.clickedLevel, 2);
    h.run('estimationState.bands[0].known = 0; showEstimationResult();');
    assert.equal(h.estimationState.estimatedLevel, 0);
    await h.useEstimatedLevel(); assert.equal(h.clickedLevel, 1);
    h.run('estimationState.bands[0].known = 1; showEstimationResult();');
    assert.equal(h.estimationState.estimatedLevel, 0);
    h.activeArtist = { name: 'Artist' };
    h.renderLevelSelector = (_, options) => { h.renderedArtist = options.preferActionable; };
    h.showEstimationResult(); await h.useEstimatedLevel(); assert.equal(h.renderedArtist, true);
    assert.deepEqual(JSON.parse(JSON.stringify(h.calculateEstimationResult([], 0))), { point: 0, low: 0, high: 0 });

    // Async preparation must not reopen a closed or superseded check.
    h = createHarness();
    let resolve;
    h.loadEstimationVocabulary = () => new Promise(r => { resolve = r; });
    h.loadSpeechSourceFrequency = async () => null;
    const pending = h.startEstimation();
    h.closeEstimationModal();
    resolve([surface('hablo', 1, [sense('hablar', 'speak')])]);
    await pending;
    assert.equal(h.estimationState.active, false);
    assert.equal(h.estimationState.validWords.length, 0);
    h.loadEstimationVocabulary = async () => [surface('hablo', 1, [sense('hablar', 'speak')])];
    await h.startEstimation();
    assert.equal(h.estimationState.currentWord.word, 'hablo');
    h.revealTranslation(); h.handleAnswer(true);
    await new Promise(r => setTimeout(r, 0));
    assert.equal(h.estimationState.groupEstimate.point, 1);
    // A superseded run must not consume the retry's response or example data.
    h = createHarness();
    const waits = [];
    h.loadEstimationVocabulary = () => new Promise(resolve => waits.push(resolve));
    h.loadSpeechSourceFrequency = async () => null;
    const oldRun = h.startEstimation();
    h.retryEstimation();
    waits[0]([surface('old', 1, [sense('old', 'old')])]);
    await oldRun;
    assert.equal(h.estimationState.validWords.length, 0);
    waits[1]([surface('new', 2, [sense('new', 'new')])]);
    await new Promise(resolve => setTimeout(resolve, 0));
    assert.equal(h.estimationState.currentWord.word, 'new');
    h.closeEstimationModal();

    h.loadEstimationVocabulary = async () => [noExamples];
    let resolveExamples;
    h.loadEstimationExamples = () => new Promise(resolve => { resolveExamples = resolve; });
    const exampleRun = h.startEstimation();
    await new Promise(resolve => setTimeout(resolve, 0));
    h.closeEstimationModal();
    resolveExamples({fue: {m: [[], [], [{target: 'Fue a Sevilla.'}], []]}});
    await exampleRun;
    assert.equal(h.estimationState.validWords.length, 0);

    h.loadEstimationVocabulary = async () => { throw new Error('network'); };
    await h.startEstimation();
    assert.ok(h.lastAlert); assert.equal(h.estimationState.loading, false);
    console.log('Estimator grouping, prompts, placement, endpoints and cancellation checks passed.');
})().catch(error => { console.error(error); process.exitCode = 1; });
