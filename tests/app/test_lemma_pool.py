"""lemma-pool/v1: merged cards get their other forms' sentences, cycled by form."""
import json
from pathlib import Path
import shutil
import subprocess
import unittest

ROOT = Path(__file__).resolve().parents[2]


class LemmaPoolFilesTests(unittest.TestCase):
    def test_pool_is_bound_to_the_configured_release(self):
        config = json.loads((ROOT / 'app/config/config.json').read_text(encoding='utf-8'))
        for language in ('portuguese', 'spanish'):
            cfg = config['languages'][language]
            manifest = json.loads((ROOT / 'app' / cfg['lemmaPoolPath']).read_text(encoding='utf-8'))
            self.assertEqual(manifest['rule'], 'lemma-pool/v1')
            self.assertIn(f"/{manifest['release_id']}/", cfg['indexPath'])
            self.assertEqual(manifest['merge_keys_from'], cfg['mergeExceptionsPath'])
            for shard in manifest['shards']:
                self.assertTrue((ROOT / 'app' / cfg['lemmaPoolPath']).parent.joinpath(shard['path']).exists())


@unittest.skipUnless(shutil.which('node'), 'Node required')
class LemmaPoolAppTests(unittest.TestCase):
    def run_js(self, script):
        result = subprocess.run(['node', '--input-type=module', '-'], input=script,
                                cwd=ROOT, text=True, capture_output=True)
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_pooled_forms_are_taken_in_turn(self):
        self.run_js(r'''
import fs from 'node:fs';
import vm from 'node:vm';
import assert from 'node:assert/strict';
const source=fs.readFileSync('app/js/flashcards.js','utf8');
const start=source.indexOf('function sortExamplesByRelevance(');
const end=source.indexOf('\n}\n',start)+3;
const ex=(target,score,form,english='x')=>({target,english,pooledFrom:form,
 metadata:{translation_alignment:{score}}});
const ctx={getReinforcementWords:()=>new Set(),filterPersonalisedExamples:e=>e,activeArtist:null,
 exampleTranslationAlignment:e=>e.metadata.translation_alignment.score,exampleIsSingleSentence:()=>true,
 exampleConfidenceTier:()=>1,exampleReinforcementScore:()=>0,exampleSungByActiveArtist:()=>false};
vm.createContext(ctx);vm.runInContext(source.slice(start,end),ctx);
const own1=ex('é 1',0.9),own2=ex('é 2',0.8),foi1=ex('foi 1',0.95,'foi'),foi2=ex('foi 2',0.7,'foi'),
 era1=ex('era 1',0.5,'era'),bare=ex('era 2',0.99,'era','');
const order=[...ctx.sortExamplesByRelevance([own1,own2,foi1,foi2,era1,bare]).map(e=>e.target)];
assert.deepEqual(order,['foi 1','é 1','era 1','foi 2','é 2','era 2']);
// A card with no pooled lines keeps the plain relevance order.
assert.deepEqual([...ctx.sortExamplesByRelevance([own2,own1]).map(e=>e.target)],['é 1','é 2']);
''')

    def test_unloaded_form_donates_from_the_pool(self):
        self.run_js(r'''
import fs from 'node:fs';
import vm from 'node:vm';
import assert from 'node:assert/strict';
const source=fs.readFileSync('app/js/vocab.js','utf8');
const block=name=>source.slice(source.indexOf(`// ${name}\n`),source.indexOf(`// /${name}`));
const fn=name=>{const s=source.indexOf(`function ${name}(`);return source.slice(s,source.indexOf('\n}\n',s)+3);};
const ctx={console,window:{}};
vm.createContext(ctx);
vm.runInContext(block('lemma-merge-pure'),ctx);
for (const name of ['exampleSentenceKey','examplesForMeaning','poolLemmaSiblingExamples']) vm.runInContext(fn(name),ctx);
const overlay={rule:'form-privilege/v3',lemma:'ser'};
const sense={headword:'ser',pos:'verb',source_reference:'kaikki:ser-1',translation:'to be'};
const host={id:'h',word:'é',_formPrivilegeOverlay:overlay,meanings:[{...sense,examples:[{target:'É bom.'}]}]};
// foi's own set is not loaded: no rows, no sentences.
const foi={id:'f',word:'foi',_formPrivilegeOverlay:overlay,_indexRowsPending:true,meanings:[]};
ctx.window._lemmaPool={rows:{f:{word:'foi',meanings:[sense]}},
 examples:{f:{m:[[{target:'Foi bom.'},{target:'É bom.'}]]}}};
vm.runInContext('window=globalThis.window',ctx);
ctx.poolLemmaSiblingExamples([host],[host,foi],{});
assert.deepEqual([...host.meanings[0].examples.map(e=>e.target)],['É bom.','Foi bom.']);
assert.equal(host.meanings[0].examples[1].pooledFrom,'foi');
assert.equal(host.lemma_example_count,2);
''')


if __name__ == '__main__':
    unittest.main()
