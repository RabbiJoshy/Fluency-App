"""Dictionary illustrations must teach the active surface without losing alternatives."""
import json
from pathlib import Path
import shutil
import subprocess
import unittest

ROOT = Path(__file__).resolve().parents[2]


@unittest.skipUnless(shutil.which('node'), 'Node.js required')
class CanonicalFormExamplesTests(unittest.TestCase):
    def run_js(self, checks):
        source = (ROOT / 'app/js/flashcards.js').read_text()
        names = ['canonicalRecord', 'extractCanonicalDictionaryExamples',
                 'canonicalOccurrenceSurface', 'findCanonicalForCard',
                 'exampleWsdMeta', 'exampleWsdLevel', 'isCorpusDisplayExample',
                 'isReliableWsdExample', 'rankConfidentWsdExamples', 'displayExamplesForSense']
        snippets = []
        for name in names:
            start = source.index(f'function {name}(')
            end = source.index('\n}\n', start) + 3
            snippets.append(source[start:end])
        script = '''const assert = require('assert');
const currentMWEIndex = 0;
const WSD_EXAMPLE_LEVEL_RANK = {leaf:3, glosskey:2, tuple:1};
const _cachedRegex = (pattern, flags) => new RegExp(pattern, flags);
const dictionaryProviderForMeaning = m => m.source || 'SpanishDict';
const sortExamplesByRelevance = x => x;
''' + '\n'.join(snippets) + '\n' + checks
        result = subprocess.run(['node', '-e', script], text=True, capture_output=True)
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_nonmerged_searches_all_examples_for_exact_form(self):
        self.run_js('''
const meaning = {senseId:'s', canonicalExample:{text:'Quiero hablar.', translation:'I want to speak.'}};
const card = {targetWord:'hablas', dictionaryExamples:{s:[
 {text:'Hablo inglés.', translation:'I speak English.'},
 {text:'Hablas muy bien.', translation:'You speak very well.'}
]}};
assert.equal(findCanonicalForCard(card, meaning).target, 'Hablas muy bien.');
assert.equal(extractCanonicalDictionaryExamples(meaning, card).length, 3);
assert.equal(findCanonicalForCard({targetWord:'hablaste'}, meaning), null);
assert.equal(canonicalOccurrenceSurface({targetWord:'hacerlo'}, {}, 'Quiero hacer algo.'), '');
assert.equal(canonicalOccurrenceSurface({targetWord:'és'}, {}, 'O nome es está aqui.'), '');
assert.equal(canonicalOccurrenceSurface({targetWord:'ano'}, {}, 'Tenho muitos anos.'), '');
''')

    def test_merged_header_uses_exact_allowed_dictionary_form(self):
        self.run_js('''
const card = {targetWord:'estar', displaySurface:'estar', mergedLemma:true,
 mergedSurfaces:['estar','estaba','estás']};
const example = {canonical:true, target:'Estaba en casa.', bold_text_offsets:[[0,6]]};
assert.equal(canonicalOccurrenceSurface(card, example, example.target), 'Estaba');
assert.equal(canonicalOccurrenceSurface(card, {}, 'Estás en casa.'), 'Estás');
assert.equal(canonicalOccurrenceSurface(card, {}, 'Fue a casa.'), '');
const meaning = {canonicalExample:{text:example.target, translation:'He was at home.'}};
assert.equal(findCanonicalForCard(card, meaning).target, example.target);
''')

    def test_shipped_alternatives_rescue_spanishdict_and_wiktionary_forms(self):
        config = json.loads((ROOT / 'app/config/config.json').read_text())
        for lang, word, sentence in [('spanish', 'tengo', 'Tengo dos años sin verlo.'),
                                     ('portuguese', 'é', 'Essa casa é do prefeito.')]:
            asset = json.loads((ROOT / 'app' / config['languages'][lang]['dictionaryExamplesPath']).read_text())
            sense_id = next(key for key, examples in asset['examples'].items()
                            if any(example['text'] == sentence for example in examples))
            self.run_js('const data=' + json.dumps({'senseId': sense_id, 'word': word,
                'examples': asset['examples'][sense_id]}, ensure_ascii=False) + ''';
const card={targetWord:data.word,dictionaryExamples:{[data.senseId]:data.examples}};
const chosen=findCanonicalForCard(card,{senseId:data.senseId});
assert(chosen);
assert(canonicalOccurrenceSurface(card, chosen, chosen.target));
''')

    def test_wrong_form_never_enters_sequence_and_corpus_is_preserved(self):
        self.run_js('''
const meaning = {canonicalExample:{text:'Quiero hablar.', translation:'I want to speak.'}};
const corpus = {target:'Hablas muy bien.',english:'You speak very well.',wsd:{supported_level:'leaf'}};
assert.deepEqual(displayExamplesForSense(meaning, [corpus], {targetWord:'hablas'}), [corpus]);
assert.deepEqual(displayExamplesForSense(meaning, [], {targetWord:'hablas'}), []);
const match = {canonicalExample:{text:'Hablas inglés.',translation:'You speak English.'}};
assert.equal(displayExamplesForSense(match, [corpus], {targetWord:'hablas'})[1].canonical, true);
''')

    def test_release_bound_supplement_clears_on_release_change_and_survives_hydration(self):
        source = (ROOT / 'app/js/vocab.js').read_text()
        start = source.index('const dictionaryExampleLoads = new Map();')
        end = source.index('// A small per-language file', start)
        script = '''const assert=require('assert');
const lemmaGroupKey = x => x.merge_key;
let reads=0;
const readJsonWithTimeout=async path=>{reads++;return {response:{ok:true},data:{release_id:'r1',
 examples:{s:[{text:'Anos passam.',translation:'Years pass.'}]},groups:{ano:['ano','anos']}}};};
''' + source[start:end] + '''
(async()=>{
 const rows=[{word:'anos',merge_key:'ano'}];
 await stampDictionaryExamples(rows,{dictionaryExamplesPath:'a',indexPath:'releases/r1/app/index.json'});
 assert.equal(rows[0]._dictionaryExamples.s.length,1);
 Object.assign(rows[0],{meanings:[{sense_id:'s'}]});
 assert.equal(rows[0]._dictionaryExamples.s.length,1);
 await stampDictionaryExamples(rows,{dictionaryExamplesPath:'a',indexPath:'releases/r2/app/index.json'});
 assert.equal(rows[0]._dictionaryExamples,undefined);
 assert.equal(reads,1);
})().catch(e=>{console.error(e);process.exitCode=1;});
'''
        result = subprocess.run(['node', '-e', script], text=True, capture_output=True)
        self.assertEqual(result.returncode, 0, result.stderr)

