"""Load only the active set's release-bound scores and preserve example identity."""
from pathlib import Path
import shutil
import subprocess
import unittest

ROOT = Path(__file__).resolve().parents[2]


@unittest.skipUnless(shutil.which('node'), 'Node required')
class ExampleAlignmentTests(unittest.TestCase):
    def test_sidecar_loading_identity_binding_and_retry(self):
        script = r'''
import fs from 'node:fs';
import assert from 'node:assert/strict';
const {createExampleAlignmentLoader,exampleTranslationAlignment}=await import(
 'data:text/javascript;base64,'+Buffer.from(fs.readFileSync('app/js/example-alignment.js','utf8')).toString('base64'));
const manifest={schema:'example-alignment/v1',examplesPath:'releases/r1/examples.json',
 model:'sentence-transformers/LaBSE',alignment_version:'labse-cosine/v1',
 card_shards:{a:'set1.json',b:'set1.json',c:'set2.json'}};
const calls=[];let fail=false;
const readJson=async path=>{calls.push(path);if(fail)throw Error('offline');return {response:{ok:true},
 data:path.endsWith('manifest.json')?manifest:{sentence_a:0,sentence_b:.97}}};
const resolve=path=>path.replace('releases/','https://releases/');
const load=createExampleAlignmentLoader({readJson,releaseUrl:resolve});
const config={examplesPath:resolve(manifest.examplesPath),exampleAlignmentPath:'data/r1/manifest.json'};
const ex=(id)=>({example_id:'example_'+id,target:id,english:id,metadata:{sentence_id:'sentence_'+id}});
const a=ex('a'),b=ex('b'),unknown=ex('unknown');const group=[b,a,unknown];
const payload={a:{m:[group],u:[ex('b')],frequency:123}};
await load(payload,config);
assert.deepEqual(calls,['data/r1/manifest.json','data/r1/set1.json']);
assert.equal(payload.a.m[0],group);assert.equal(group[0],b);assert.equal(group.length,3);
assert.equal(payload.a.frequency,123);assert.equal(exampleTranslationAlignment(a),0);
assert.equal(exampleTranslationAlignment(b),.97);assert.equal(exampleTranslationAlignment(unknown),null);
assert.equal(payload.a.u[0].metadata.translation_alignment.model,manifest.model);
assert.equal(payload.a.u[0].metadata.translation_alignment.version,manifest.alignment_version);
// Concurrent/prefetch loads reuse the manifest and the same set's score file.
await Promise.all([load({b:{m:[[ex('b')]]}},config),load({b:{m:[[ex('b')]]}},config)]);
assert.equal(calls.length,2);
// A different release never receives this companion's measurements.
const wrong=ex('a');await load({a:{m:[[wrong]]}},{...config,examplesPath:'https://releases/r2/examples.json'});
assert.equal(wrong.metadata.translation_alignment,undefined);assert.equal(calls.length,2);
// Native metadata is authoritative even if the companion has another score.
const native=ex('a');native.metadata.translation_alignment={score:.5,model:'native',version:'v2'};
await load({a:{m:[[native]]}},config);assert.equal(exampleTranslationAlignment(native),.5);
// Offline reads leave content available and retry on the next attempt.
fail=true;const retry=createExampleAlignmentLoader({readJson,releaseUrl:resolve});
const savedWarn=console.warn;console.warn=()=>{};
const offline=ex('b');await retry({b:{m:[[offline]]}},config);
assert.equal(offline.metadata.translation_alignment,undefined);
fail=false;await retry({b:{m:[[offline]]}},config);
assert.equal(exampleTranslationAlignment(offline),.97);console.warn=savedWarn;
'''
        result = subprocess.run(['node', '--input-type=module', '-'], input=script,
                                cwd=ROOT, text=True, capture_output=True)
        self.assertEqual(result.returncode, 0, result.stderr)
