"""A row fetched in Speech must hydrate a later live index for the same release."""
from pathlib import Path
import shutil
import subprocess
import unittest

ROOT = Path(__file__).resolve().parents[2]


@unittest.skipUnless(shutil.which('node'), 'Node.js required')
class LiveDefinitionCacheTests(unittest.TestCase):
    def test_switching_indexes_reuses_definitions_not_just_loaded_flags(self):
        source = (ROOT / 'app/js/vocab.js').read_text()
        functions = source[source.index('const loadedIndexRowShards'):source.index('function parseStudyRangeString')]
        sidecar = (ROOT / 'app/js/wsd-ui-sidecar.js').read_text()
        sidecar = '\n'.join(line for line in sidecar.splitlines() if not line.startswith('import ')).replace('export ', '')
        script = r"""
const assert = require('node:assert/strict');
let fetches = 0;
const window = {_cachedJoinedIndex:[{id:'segundos',word:'segundos',meanings:[],_indexRowsPending:true}]};
const readJsonWithTimeout = async () => { fetches++; return {response:{ok:true},data:{segundos:{meanings:[{translation:'second',pos:'NOUN'}]}}}; };
const trackDataFreshness = () => {};
const promoteSubglossTranslations = () => {};
""" + sidecar + functions + r"""
(async()=>{
const cfg={indexPath:'speech/vocabulary.index.json'}, shard={path:'rows/943.json'};
await fetchIndexRowShard(cfg,shard);
assert.equal(window._cachedJoinedIndex[0].meanings[0].translation,'second');
// Study rendering must not mutate the cached source payload.
window._cachedJoinedIndex[0].meanings[0].translation='mutated by previous study';
window._cachedJoinedIndex=[{id:'segundos',word:'segundos',meanings:[],_indexRowsPending:true}];
await fetchIndexRowShard(cfg,shard);
assert.equal(window._cachedJoinedIndex[0].meanings[0]?.translation,'second');
assert.equal(window._cachedJoinedIndex[0]._indexRowsPending,false);
assert.equal(fetches,1);
})().catch(e=>{console.error(e);process.exitCode=1});
"""
        result = subprocess.run(['node','-'], input=script, text=True, capture_output=True, cwd=ROOT)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
