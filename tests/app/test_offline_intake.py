"""Offline recognition must preserve surfaces without WSD or wiki requests."""
from pathlib import Path
import shutil
import subprocess
import unittest

ROOT = Path(__file__).resolve().parents[2]
RUNNER = r"""
const fs = require('node:fs'), vm = require('node:vm'), assert = require('node:assert/strict');
const context = { URL, console, fetch() { throw new Error('Recognition must never fetch a wiki or run WSD'); } };
vm.createContext(context);
vm.runInContext(fs.readFileSync('app/js/offline-intake.js','utf8').replace(/^export /gm,'')
    .replaceAll('import.meta.url', JSON.stringify('https://app.test/js/offline-intake.js')), context);
const input = {
 speechSurfaces: new Set(['matar', 'irse']),
 assets: { dictionary: {matar: {}, irse: {}}, curatedEntities: {
   'puerto rico': {canonicalTitle:'Puerto Rico', entityType:'place', source:'curated'},
   'prada': {canonicalTitle:'Prada', entityType:'brand', source:'curated'} } },
 extra50k: { ranks: {inspectora: 14086, matarme:1938, matar:900, irse:1111}, lemmas: {matarme:'matar'} },
 records: [{title:'S01E01', dialogueLines:[{text:'Inspectora, matarme matarme irse. Puerto Rico y Prada.'},
   {text:'Puerto. Rico. inventadísimo'}]}, {status:'error', plainLyrics:'ignored'}]
};
const result = context.recognizeOfflineRecords(input);
assert.equal(result.mode,'no-wsd');
assert.equal(result.grouping,'original-surface');
assert.equal(result.surfaces.matarme.count,2);
assert.equal(result.surfaces.matarme.lemmaHint,'matar');
assert.equal(result.surfaces.matar,undefined);
assert.equal(result.surfaces.irse.count,1);
assert.equal(result.surfaces.irse.lemmaHint,null);
assert.equal(result.surfaces.inspectora.frequencyRank,14086);
assert.equal(result.surfaces.inspectora.inStudyInventory,false);
assert.equal(result.surfaces['inventadísimo'].frequencyRank,null);
assert.equal(result.surfaces.ignored,undefined);
assert.equal(result.entityCandidates.length,2);
assert.equal(result.entityCandidates.find(e=>e.canonicalTitle==='Puerto Rico').count,1);
assert.equal(result.entityCandidates[0].assignment,'candidate');
for (const item of Object.values(result.surfaces)) {
 assert.equal(item.unassigned,true);
 assert.equal(item.meanings,undefined);
 for(const example of item.examples) assert.equal(example.text.slice(example.start,example.end),example.surface);
}
assert.equal(Object.values(result.surfaces).reduce((sum,w)=>sum+w.count,0),result.summary.tokenCount);
// Missing local assets can be retried; a successful load is reused.
let fetches = 0, fail = true;
context.fetch = async () => {fetches++; return {ok:!fail,status:503,json:async()=>({})};};
(async()=>{
 await assert.rejects(context.loadOfflineIntakeAssets('spanish'));
 fail=false;
 assert.ok(await context.loadOfflineIntakeAssets('spanish'));
 const before=fetches;
 await context.loadOfflineIntakeAssets('spanish');
 assert.equal(fetches,before);
 assert.equal(await context.loadOfflineIntakeAssets('unsupported'),null);
})().catch(e=>{console.error(e);process.exitCode=1});
"""


@unittest.skipUnless(shutil.which('node'), 'Node.js is needed for browser logic tests')
class OfflineIntakeTests(unittest.TestCase):
    def test_recognition_without_routing_or_network(self):
        result = subprocess.run(['node', '-'], input=RUNNER, cwd=ROOT,
                                capture_output=True, text=True, timeout=20)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
