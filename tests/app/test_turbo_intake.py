"""Turbo's deck, audit and word preview must agree on recognition."""
from pathlib import Path
import shutil
import subprocess
import unittest

ROOT = Path(__file__).resolve().parents[2]
RUNNER = r"""
const fs = require('node:fs'), vm = require('node:vm'), assert = require('node:assert/strict');
const helper = fs.readFileSync('app/js/lexical-guards.js', 'utf8').replace(/^export /gm, '');
const source = fs.readFileSync('app/turbo/turbo-engine.js', 'utf8')
    .replace(/^import .*;\n/gm, '').replace(/^export /gm, '')
    .replaceAll('import.meta.url', JSON.stringify('https://app.test/turbo/turbo-engine.js'));
const context = { URL, console, performance, fetch() { throw new Error('Unexpected network request'); } };
vm.createContext(context);
vm.runInContext(helper + '\n' + source + '\nthis.TurboEngine = TurboEngine;', context);
const { TurboEngine } = context;
const entry = (rank, translation, meanings = [{pos:'VERB',translation}]) => ({
    rank, top_translation:translation, top_pos:meanings[0].pos,
    polysemous:meanings.length > 1, meaningCount:meanings.length, meanings
});
(async () => {
    // The default word list lives beside the engine, including inside a worker.
    const urls = [];
    context.fetch = async url => {
        urls.push(String(url));
        return {ok:true, json:async()=>String(url).includes('50k')
            ? {ranks:{hablamos:500},lemmas:{hablamos:'hablar'}}
            : {language:'es', dictionary:{hablar:entry(100,'speak')}}};
    };
    const engine = await TurboEngine.create('../turbo/turbo_assets.json');
    assert.equal(urls[1], 'https://app.test/turbo/es_50k_data.json');
    assert.equal(engine.resolveWordInfo('hablamos').word, 'hablar');
    // No title-cased name candidates: this test must not need any online lookup.
    context.fetch = () => { throw new Error('Unexpected network request'); };
    const result = await engine.processPlaylist([{title:'Dialogue',lyrics:'hablamos hablamos'}]);
    const card = result.cards.find(c=>c.word==='hablamos');
    assert.ok(card, 'A form recognised in preview must survive deck assembly');
    assert.equal(card.translation, 'speak');
    assert.equal(card.lemma, 'hablar');
    assert.equal(card.playlistCount, 2);
    assert.equal(card.speechRank, 100);
    assert.equal(result.annotatedSongs[0].lines[0].tokens[0].card.word, card.word);

    // Full names are counted once per mention, never as substring matches.
    const names = new TurboEngine({dictionary:{puerto:entry(200,'port'),rico:entry(201,'rich')},
        curatedEntities:{'puerto rico':{canonicalTitle:'Puerto Rico',description:'Caribbean island'}}});
    const entityResult = await names.processPlaylist([{title:'Lyrics',
        lyrics:'puerto rico puerto rico\npuerto ricola'}]);
    const island = entityResult.cards.find(c=>c.word==='Puerto Rico');
    assert.equal(island.playlistCount, 2);
    assert.equal(entityResult.cards.find(c=>c.word==='rico'), undefined, 'Name parts must not become word cards');
    assert.equal(entityResult.cards.find(c=>c.word==='puerto').playlistCount, 1);
    assert.equal(entityResult.annotatedSongs[0].lines[0].tokens.length, 2);
    assert.equal(entityResult.annotatedSongs[0].lines[1].tokens[0].type, 'word');
    const separated = await names.processPlaylist([{title:'Dialogue',lyrics:'puerto. rico'}]);
    assert.equal(separated.entityCardsCount, 0, 'Do not join names across sentence boundaries');
    assert.equal(separated.wordCardsCount, 2);

    // An unsupported sense guess must not acquire an assigned example.
    const ambiguous = new TurboEngine({dictionary:{banco:entry(300,'bank',[
        {pos:'NOUN',translation:'bank'}, {pos:'NOUN',translation:'bench'}])}});
    const ambiguousResult = await ambiguous.processPlaylist([{title:'Dialogue',lyrics:'banco'}]);
    const bank = ambiguousResult.cards[0];
    assert.equal(bank.meanings.reduce((sum,m)=>sum+m.examples.length,0), 0);
    assert.equal(bank.examples[0].text, 'banco');
    assert.equal(bank.examples[0].unassigned, true);
    // Existing contextual rules still assign examples when a rule actually matches.
    const auxiliary = new TurboEngine({dictionary:{estoy:entry(20,'be',[
        {pos:'VERB',translation:'be',context:'location'},
        {pos:'AUX',translation:'be',context:'progressive'}])}});
    const progressive = await auxiliary.processPlaylist([{title:'Lyrics',lyrics:'estoy cantando'}]);
    const be = progressive.cards.find(c=>c.word==='estoy');
    assert.equal(be.meanings[0].examples.length, 0);
    assert.equal(be.meanings[1].examples.length, 1);
    assert.equal(be.examples[0].assigned, true);
    assert.equal(be.examples[0].unassigned, false);
    // Explicit no-WSD is honoured even for monosemous words.
    engine.disambiguateWord = () => { throw new Error('No-WSD called the sense assigner'); };
    const offline = await engine.processPlaylist([{title:'Lyrics',lyrics:'hablamos'}], {skipWsd:true});
    assert.equal(offline.cards[0].meanings[0].examples.length, 0);
    assert.equal(offline.cards[0].examples[0].assignment_method, 'unassigned');

    // Language assets select their matching word list; explicit overrides still work.
    context.fetch = async url => {
        urls.push(String(url));
        return {ok:true,json:async()=>({language:'pt'})};
    };
    await TurboEngine.create('./pt_turbo_assets.json');
    assert.equal(urls.at(-1),'https://app.test/turbo/pt_50k_data.json');
    await TurboEngine.create('./custom.json', './custom-50k.json');
    assert.equal(urls.at(-1),'./custom-50k.json');
    context.fetch = async url => String(url).includes('50k') ? {ok:false,status:404}
        : {ok:true,json:async()=>({dictionary:{hablar:entry(100,'speak')}})};
    const fallback = await TurboEngine.create();
    const fallbackResult = await fallback.processPlaylist([{title:'Dialogue',lyrics:'hablar'}]);
    assert.equal(fallbackResult.cards[0].translation, 'speak');
})().catch(error => { console.error(error); process.exitCode = 1; });
"""


@unittest.skipUnless(shutil.which('node'), 'Node.js required')
class TurboIntakeTests(unittest.TestCase):
    def test_deck_and_audit_recognition(self):
        result = subprocess.run(['node', '-'], input=RUNNER, cwd=ROOT,
                                text=True, capture_output=True, timeout=30)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
