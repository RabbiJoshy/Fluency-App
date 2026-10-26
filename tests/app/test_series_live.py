"""Exercise the series preset through the shared browser deck engine."""
from pathlib import Path
import shutil
import subprocess
import unittest

ROOT = Path(__file__).resolve().parents[2]

RUNNER = r"""
const fs = require('node:fs');
const vm = require('node:vm');
const assert = require('node:assert/strict');
const read = path => fs.readFileSync(path, 'utf8');
const preset = JSON.parse(read('app/data/series/casa-de-papel-deck.json'));
const dialogue = JSON.parse(read('app/data/series/casa-de-papel.json'));
const inventory = Object.keys(JSON.parse(read('app/data/speech-frequency/es-literal-ground-r6-fw1.json')).values);
let stored = null, fetches = [], invalidations = 0, saves = 0, workerStarts = 0;
const request = result => {
    const req = {};
    queueMicrotask(() => { req.result = result; req.onsuccess?.(); });
    return req;
};
const db = {
    close() {},
    transaction() { return { objectStore() { return {
        get() { return request(structuredClone(stored)); },
        put(value) { stored = structuredClone(value); return request('live'); },
        delete() { throw new Error('Must not delete a usable deck'); }
    }; } }; }
};
let route = 'preset';
const context = {
    console, URL, AbortController, setTimeout, clearTimeout, queueMicrotask,
    Worker: function() { workerStarts++; throw new Error('Offline imports must never start WSD'); },
    window: {
        _normalModeLangConfigs: { spanish: { indexPath: 'speech/vocabulary.index.json' } },
        location: { hash: '#/es/live' },
        invalidatePreparedSetupVocabulary() { invalidations++; },
    },
    document: { readyState: 'loading', addEventListener() {}, body: { classList: { remove() {} } } },
    releaseUrl: path => path,
    parseRoute: () => ({ kind: 'live' }), clearRoute() {},
    fetch: async url => {
        const path = String(url); fetches.push(path);
        if (path.includes('speech/vocabulary.index.manifest.json')) return { ok: true, json: async () => ({columns: 'columns.json'}) };
        if (path.includes('speech/columns.json')) return { ok: true, json: async () => ({ word: inventory }) };
        if (route === 'offline') throw new Error('Offline');
        if (path.includes('/turbo/')) return {ok: true, json: async () => JSON.parse(read('app/turbo/' + path.split('/').at(-1)))};
        if (path.includes('spanish-lexicon.json')) return {ok:true, json:async () => JSON.parse(read('app/data/series/spanish-lexicon.json'))};
        if (path.includes('elite-deck.json')) return {ok:true, json:async () => JSON.parse(read('app/data/series/elite-deck.json'))};
        if (path.includes('casa-de-papel-deck.json')) return {ok: route === 'preset', json: async () => structuredClone(preset)};
        if (path.includes('casa-de-papel.json')) return {ok: true, json: async () => structuredClone(dialogue)};
        throw new Error('Unexpected fetch: ' + path);
    },
    indexedDB: { open() { return request(db); } }
};
context.window.indexedDB = context.indexedDB;
vm.createContext(context);
function load(path) {
    const source = read(path).replace(/^import .*;\n/gm, '').replace(/^export /gm, '')
        .replaceAll('import.meta.url', JSON.stringify('http://localhost/js/' + path.split('/').at(-1)));
    vm.runInContext(source, context);
}
load('app/js/lexical-guards.js');
load('app/js/offline-intake.js');
load('app/js/series-vocabulary.js');
load('app/js/playlist-live.js');
load('app/js/subtitle-import.js');
const w = context.window;
w.savePlaylistLiveDeckToServer = () => { saves++; return new Promise(() => {}); };
(async () => {
    // A server that never settles cannot hold the local preset or rebuild open.
    let deck = await context.loadCasaDePapelPreset();
    assert.equal(deck.matchedCount, 12706);
    assert.equal(stored.presetRevision, 'offline-30-episodes-v5-all-forms');
    route = 'rebuild';
    w.config = {languages: {spanish: {indexPath: 'wrong-artist/vocabulary.index.json'}}};
    deck = await context.loadCasaDePapelPreset();
    assert.equal(deck.trackCount, 30);
    assert.equal(deck.matchedCount, 12706);
    assert.equal(deck.coverage.complete, false);
    assert.equal(deck.coverage.missing.length, 11);
    assert.equal(deck.isTurboEngine, undefined);
    assert.equal(deck.intake.mode, 'no-wsd');
    assert.equal(deck.intake.surfaces.inspectora.frequencyRank, 14086);
    assert.equal(deck.intake.surfaces.atracadores.frequencyRank, 38609);
    assert.equal(deck.intake.surfaces.inspectora.inStudyInventory, false);
    assert.equal(deck.intake.surfaces.profesor.count, deck.surfaces.profesor.count);
    assert.equal(JSON.stringify(deck.intake.summary), JSON.stringify(preset.intake.summary));
    assert.equal(deck.surfaces.profesor.lines[0].text.length > 0, true);
    assert.equal(deck.surfaces.profesor.lines[0].song.startsWith('S01E'), true);
    assert.ok(deck.surfaces.profesor.lines[0].english);
    assert.equal(deck.tokenCount, preset.tokenCount);
    for (const [word, entry] of Object.entries(preset.surfaces)) {
        assert.equal(deck.surfaces[word].count, entry.count, `Count changed for ${word}`);
    }
    assert.equal(JSON.stringify(deck).includes('[object Object]'), false);
    assert.equal(invalidations > 0, true);

    // Canonical definitions hydrate after ranking; a subset must not shrink the deck.
    const canonical = inventory.map((word, i) => ({ id: String(i), word, rank: i + 1, meanings: [], _indexRowsPending: true }));
    w._cachedJoinedIndex = canonical;
    const ranked = w.applyPlaylistLiveVocabulary(canonical);
    assert.equal(ranked.length, 12706);
    const professor = ranked.find(card => card.word === 'profesor');
    const original = canonical.find(card => card.word === 'profesor');
    assert.equal(professor.sourceRank, original.rank);
    assert.equal(professor.offlineRecognition.frequencyRank, 852);
    assert.equal(professor.offlineRecognition.unassigned, true);
    assert.notEqual(professor.rank, original.rank);
    original.meanings = [{translation: 'teacher', frequency: 0.8}, {translation: 'rare', frequency: 0.01}];
    original._indexRowsPending = false;
    const refreshed = w.refreshPlaylistLiveEntry(professor);
    assert.equal(refreshed.rank, professor.rank);
    assert.equal(refreshed.sourceRank, original.rank);
    assert.equal(refreshed.meanings.length, 2);
    assert.equal(refreshed.meanings[0].translation, 'teacher');
    assert.equal(refreshed.meanings[0].examples[0].unassigned, true);
    assert.equal(refreshed.meanings[0].examples[0].spanish.length > 0, true);
    assert.ok(refreshed.meanings[0].examples[0].english);
    assert.equal(refreshed.meanings[0].examples[0].complete_context, true);
    w.applyPlaylistLiveVocabulary([original]);
    assert.equal(w.playlistLiveDeck().matchedCount, 12706);
    assert.equal(original.meanings[0].examples, undefined);
    const berlin = canonical.find(card => card.word === 'berlín');
    berlin.meanings = [{pos:'PHRASE',translation:'Berlin Wall',headword:'muro de berlín',frequency:1}];
    berlin._indexRowsPending = false;
    const berlinCard = w.refreshPlaylistLiveEntry(ranked.find(card => card.word === 'berlín'));
    assert.equal(berlinCard.meanings[0].translation, 'Berlin');
    assert.equal(berlinCard.meanings[0].pos, 'PROPN');
    assert.equal(berlinCard.meanings[0].examples[0].unassigned, true);
    assert.equal(berlin.meanings[0].translation, 'Berlin Wall');

    // An artist's partial song selection can remain in memory when the
    // series is opened. Exercise the real shared index loader and song filter.
    load('app/js/song-sets-core.js');
    const songSets = read('app/js/song-sets.js');
    vm.runInContext(songSets.slice(songSets.indexOf('export function filterActiveSongVocabulary('),
        songSets.indexOf('export function clearActiveExamplesData(')).replace(/^export /gm, ''), context);
    const vocabSource = read('app/js/vocab.js');
    Object.assign(context, {
        activeArtist: null, selectedLanguage: 'spanish',
        artistSongCatalog: { songs: [{id: 'selected', cardIds: [canonical[0].id]}, {id: 'other', cardIds: [canonical[1].id]}] },
        selectedSongIds: ['selected'],
        fetchAndJoinIndex: async () => canonical,
        config: {languages: {spanish: {}}},
        validateExamplesSplit() {}
    });
    w.filterActiveSongVocabulary = context.filterActiveSongVocabulary;
    vm.runInContext(vocabSource.slice(vocabSource.indexOf('async function fetchActiveVocabularyIndex('),
        vocabSource.indexOf('async function ensureLemmaPoolingData(')), context);
    const untrimmed = await context.fetchActiveVocabularyIndex({indexPath: 'speech/vocabulary.index.json'});
    assert.equal(untrimmed.length, canonical.length);
    assert.equal(w.applyPlaylistLiveVocabulary(untrimmed).length, 12706);
    const dialogueExample = { [original.id]: {m: [[{spanish: 'El profesor.', english: 'The teacher.', song: 'S01E01'}]]} };
    assert.equal(context.setActiveExamplesData(dialogueExample), dialogueExample);
    // Choosing a song still filters an ordinary artist deck.
    const savedActive = w.playlistLiveActive;
    w.playlistLiveActive = () => false;
    context.activeArtist = {slug: 'previous-artist'};
    assert.equal(context.filterActiveSongVocabulary(canonical).length, 1);
    context.activeArtist = null;
    assert.equal(context.filterActiveSongVocabulary(canonical).length, canonical.length);
    w.playlistLiveActive = savedActive;

    // The function-word renderer must not replace a live card's own examples
    // or suppress its ordinary example panel with fixed Speech constructions.
    load('app/js/function-word-card.js');
    assert.equal(context.getGrammarWordDefinition({targetWord: 'y'}, 'spanish') !== null, true);
    const liveFunctionWord = {targetWord: 'y', playlistId: 'la-casa-de-papel', functionWord: {uses: []}};
    assert.equal(context.getGrammarWordDefinition(liveFunctionWord, 'spanish'), null);
    assert.equal(context.isFunctionWordCard(liveFunctionWord, 'spanish'), false);
    assert.equal(context.functionWordBlockHTML(liveFunctionWord, 'spanish'), '');

    // Render the actual level selector against matched vocabulary, even if
    // older metadata claims there are only 900 words (nine levels).
    const selector = {classList: {add() {}}, innerHTML: ''};
    const total = {};
    Object.assign(context, {
        currentUser: null, activeArtist: null, useLemmaMode: false,
        selectedLanguage: 'spanish', selectedLevel: null, percentageMode: false,
        ppmData: null, releaseStudyStructure: null, _smartLevelRangesCache: null,
        _levelSliderRawCache: {}, STUDY_LEVEL_TARGET_CARDS: 100,
        resetSetupStateMemo() {}, setActiveSetupStep() {},
        _loadLevelSliderSamples: async () => ranked,
        getActiveLevelRanges: () => context._smartLevelRangesCache,
        _levelBandMetrics: level => ({start: level.startRank, end: level.endRank - 1, count: level.cardCount}),
        config: {languages: {spanish: {}}}
    });
    context.document.getElementById = id => id === 'levelSelector' ? selector : id === 'step2DeckTotal' ? total : null;
    context.document.querySelectorAll = () => [];
    const ui = read('app/js/ui.js');
    vm.runInContext(ui.slice(ui.indexOf('async function renderLevelSelector('), ui.indexOf('function _escapeAttr(')), context);
    w.playlistLiveDeck().matchedCount = 900;
    await context.renderLevelSelector('spanish');
    assert.equal(context._smartLevelRangesCache.length, 128);
    assert.equal(selector.innerHTML.includes('data-level="128"'), true);
    assert.equal(total.textContent.includes('12,706 words across 128 levels'), true);
    for (const level of context._smartLevelRangesCache.slice(126)) {
        const cards = ranked.filter(card => card.rank >= level.startRank && card.rank < level.endRank);
        assert.equal(cards.length, level.level === 127 ? 100 : 6);
        for (const card of cards) {
            const row = canonical.find(item => item.id === card.id);
            if (!row) {
                const loaded = w.refreshPlaylistLiveEntry(card);
                assert.ok(loaded.meanings.length);
                assert.equal(loaded.sourceRank, -1);
                assert.equal(loaded.meanings[0].examples[0].unassigned, true);
                continue;
            }
            row.meanings = [{translation: 'loaded definition', frequency: 1}];
            row._indexRowsPending = false;
            const loaded = w.refreshPlaylistLiveEntry(card);
            assert.equal(loaded.meanings[0].translation, 'loaded definition');
            assert.equal(loaded.meanings[0].examples[0].unassigned, true);
            assert.equal(loaded.rank, card.rank);
        }
    }
    await w.cacheLiveDeck(preset);
    assert.equal(w.playlistLiveDeck().matchedCount, 12706);

    // Search stays in the live source and popup hydration requests Speech
    // ranks, then renders a projected card with the series examples.
    const main = read('app/js/main.js');
    Object.assign(context, {
        _findWordIndex: null, _findWordIndexKey: null,
        excludeCognates: false, hideSingleOccurrence: false, excludeProperNouns: false,
        excludeNoise: false, excludeSlang: false, excludeGrammarParticles: false,
        excludeEnglishLoanwords: false, artistVocabularyScope: 'core'
    });
    w.fetchAndJoinIndex = async () => canonical;
    w.getWordId = item => item.id;
    w.buildFilteredVocab = () => { throw new Error('Live search must not use Speech filters'); };
    vm.runInContext(main.slice(main.indexOf('function findWordCacheKey('), main.indexOf("let _findWordFilter =")), context);
    const search = await context.buildFindWordIndex();
    assert.equal(search.length, 12706);
    const found = search.find(item => item.targetWord === 'profesor');
    assert.equal(found.sourceEntry.sourceRank, original.rank);
    original.meanings = [];
    original._indexRowsPending = true;
    found.sourceEntry._indexRowsPending = true;
    const requests = [];
    w.ensureIndexRowsForRange = async (cfg, start, end, ranks) => {
        requests.push([...ranks]);
        original.meanings = [{translation: 'teacher', frequency: 1}];
        original._indexRowsPending = false;
    };
    context.config.languages.spanish.examplesPath = 'speech/vocabulary.examples.json';
    w.generateLinks = () => ({});
    w.showFloatingBtns = () => {};
    w.initializeApp = () => {};
    const element = {classList: {contains: () => false, add() {}, remove() {}}};
    context.document.getElementById = () => element;
    Object.assign(context, {
        flashcards: [], cardNavStack: [], currentIndex: 0,
        currentMeaningIndex: 0, currentExampleIndex: 0, currentMWEIndex: 0,
        projectInspectableMeaning: meaning => ({meaning: meaning.translation, allExamples: meaning.examples}),
        splitAwareTempCard: (entry, card, meaningIndex) => ({card, meaningIndex})
    });
    const modals = read('app/js/flashcards-modals.js');
    vm.runInContext(modals.slice(modals.indexOf('async function popupFoundWord('), modals.indexOf('function navigateBack(')), context);
    await context.popupFoundWord(found, {});
    assert.equal(requests[0][0], original.rank);
    assert.equal(context.flashcards[0].meanings[0].meaning, 'teacher');
    assert.equal(context.flashcards[0].meanings[0].allExamples[0].unassigned, true);
    assert.equal(context.flashcards[0].meanings[0].allExamples[0].spanish.length > 0, true);
    assert.equal(context.flashcards[0].rank, found.rank);

    // Outside the original inventory, cards retain their full dictionary menu,
    // examples, independent study rank and no canonical shard request rank.
    const extra = ranked.find(card => card.word === 'cojonudo');
    assert.ok(extra);
    assert.equal(extra.sourceRank, -1);
    assert.ok(extra.meanings.some(m => /great|brilliant/.test(m.translation)));
    assert.ok(extra.meanings[0].examples.length);
    let repeated = extra;
    for (let i = 0; i < 3; i++) repeated = w.refreshPlaylistLiveEntry(repeated);
    assert.equal(repeated.meanings[0].examples.length, extra.meanings[0].examples.length);
    assert.equal(JSON.stringify(repeated.meanings[0].metadata), JSON.stringify(extra.meanings[0].metadata));
    assert.ok(extra.offlineRecognition.examples[0].text);
    const inspectora = ranked.find(card => card.word === 'inspectora');
    assert.ok(inspectora.meanings.some(m => /inspector/.test(m.translation)));
    assert.equal(new Set(ranked.map(card => card.word)).size, 12706);
    assert.ok(ranked.some(card => card.definitionStatus === 'pending'));
    const elite = await context.loadSeriesPreset('elite');
    assert.equal(elite.matchedCount, 4482);
    assert.equal(w.applyPlaylistLiveVocabulary(canonical).length, 4482);
    assert.ok(w.applyPlaylistLiveVocabulary(canonical).some(card => card.meanings.some(m => m.examples?.some(e => e.english))));
    assert.equal(workerStarts, 0);
    await w.cacheLiveDeck(preset);

    // Reopen and failed revision refresh preserve a genuinely small deck.
    stored = {...preset, presetRevision: 'old', matchedCount: 1, surfaces: { profesor: preset.surfaces.profesor }};
    route = 'offline';
    deck = await w.preparePlaylistLiveSession('spanish');
    assert.equal(deck.matchedCount, 1);
    assert.equal(deck.presetRevision, 'old');
    deck = await context.loadCasaDePapelPreset();
    assert.equal(deck.matchedCount, 1);
    assert.equal(stored.surfaces.profesor.count, preset.surfaces.profesor.count);
    route = 'preset';
    delete stored.sourceKind; // Legacy Casa caches still refresh by registered identity.
    deck = await w.preparePlaylistLiveSession('spanish');
    assert.equal(deck.matchedCount, 12706);
    const before = fetches.length;
    await w.preparePlaylistLiveSession('spanish');
    assert.equal(fetches.length, before + 1);

    // Custom text remains its own source, even with fewer than 1,000 words.
    deck = await context.buildSeriesLiveDeck({ title: 'Custom Subtitles', lines: ['El profesor.', {spanish: 'La casa.', english: 'The house.'}] });
    assert.equal(deck.playlistId, 'subtitle-upload');
    assert.equal(deck.presetRevision, undefined);
    assert.equal(deck.surfaces.casa.lines[0].english, 'The house.');
    assert.equal(deck.matchedCount < 1000, true);
    assert.equal((await w.preparePlaylistLiveSession('spanish')).playlistId, 'subtitle-upload');
    assert.equal(saves >= 3, true);

    // Whole bilingual groups are examples only; original fragments supply counts.
    const translation = {spanish: 'El profesor. La casa.', english: 'The teacher. The house.',
        start_ms: 1000, end_ms: 5000, source: 'checked', policy: 'precision-timing-v1'};
    deck = await context.buildSeriesLiveDeck({lines: [
        {spanish: 'Profesor.'}, {spanish: 'El profesor.', translation}, {spanish: 'La casa.', translation}
    ]});
    assert.equal(deck.surfaces.profesor.count, 2);
    assert.equal(deck.surfaces.casa.count, 1);
    assert.equal(deck.tokenCount, 5);
    assert.equal(deck.surfaces.profesor.lines[0].text, translation.spanish);
    assert.equal(deck.surfaces.profesor.lines[0].english, translation.english);
    assert.equal(deck.surfaces.casa.lines[0].text, translation.spanish);

    // Entering live study from an artist route restores the Speech config
    // before the language tab loads definitions and renders setup.
    let entered = false;
    context.config.languages.spanish = { indexPath: 'artist/vocabulary.index.json' };
    context.activeArtist = {slug: 'artist'};
    w.resetActiveArtist = () => { context.activeArtist = null; };
    context.sessionStorage = {setItem() {}};
    context.CSS = {escape: value => value};
    context.replaceRoute = () => {};
    context.routeCodeFor = value => value;
    context.document.body.classList.add = () => {};
    context.document.querySelector = () => ({click() {
        assert.equal(context.activeArtist, null);
        assert.equal(context.config.languages.spanish.indexPath, 'speech/vocabulary.index.json');
        entered = true;
    }});
    const importer = read('app/js/spotify-playlist-import.js');
    vm.runInContext(importer.slice(importer.indexOf('function activatePlaylistLiveStudy('), importer.indexOf('function confirmSpotifyLiveDeck(')), context);
    context.activatePlaylistLiveStudy('spanish');
    assert.equal(entered, true);

    // Unknown forms are real cards; only empty dialogue fails admission.
    const unknown = await context.buildSeriesLiveDeck({lines:['zzzzzznonword']});
    assert.equal(unknown.matchedCount, 1);
    assert.equal(unknown.surfaces.zzzzzznonword.card.definitionStatus, 'pending');
    await assert.rejects(context.buildSeriesLiveDeck({lines:[]}));
    assert.equal(stored.playlistId, 'subtitle-upload');
    route = 'preset';
    w.savePlaylistLiveDeckToServer = async () => { throw new Error('Server unavailable'); };
    assert.equal((await context.loadCasaDePapelPreset()).matchedCount, 12706);
    const plain = await w.buildPlaylistLiveDeck({ playlist: {id:'plain-offline',name:'Plain'},
        language:'spanish', records:[{title:'Example',plainLyrics:'El profesor.'}] });
    assert.equal(plain.isTurboEngine, undefined);
    assert.equal(plain.intake.mode, 'no-wsd');
    assert.equal(workerStarts, 0);
    console.log('Series build, cache recovery, rank hydration, and nonblocking save passed.');
})().catch(error => { console.error(error); process.exitCode = 1; });
"""


@unittest.skipUnless(shutil.which('node'), 'Node.js is needed for browser logic tests')
class SeriesLiveTests(unittest.TestCase):
    def test_series_deck_lifecycle(self):
        result = subprocess.run(['node', '-'], input=RUNNER, cwd=ROOT,
                                capture_output=True, text=True, timeout=30)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
