"""Level coverage reads each card's share by its observed surface, not its headword.

Setup samples carry the display headword as `word` (ten for the card "to"), while
coverage shares are keyed by surface. Reading by headword showed Czech level 1 as
32.0% of speech instead of 43.9%, and level 31 as 0.9% instead of 0.27%.
"""
from pathlib import Path
import shutil
import subprocess
import unittest

ROOT = Path(__file__).resolve().parents[2]


@unittest.skipUnless(shutil.which('node'), 'Node.js required')
class CoverageSurfaceLookupTests(unittest.TestCase):
    def test_band_share_uses_the_card_surface(self):
        result = subprocess.run(['node', '-'], cwd=ROOT, text=True, capture_output=True, input=r'''
const fs = require('node:fs'), vm = require('node:vm'), assert = require('node:assert/strict');
const ctx = {console, localStorage:{getItem:()=>null,setItem(){}},
 document:{readyState:'complete', getElementById:()=>null, querySelectorAll:()=>[]},
 config:{languages:{czech:{coveragePath:'coverage.json'}}}, selectedLanguage:'czech',
 fetch: async () => ({ok:true, json: async () => ({shares:{to:0.036, ten:0.002, je:0.024, 'být':0.001}})}),
};
ctx.globalThis = ctx;
vm.runInNewContext(fs.readFileSync('app/js/coverage.js','utf8').replace(/^import .*;$/gm,''), ctx);
(async () => {
 await ctx.loadCoverage({coveragePath:'coverage.json'});
 const samples = [
  {word:'ten', stableRank:1, item:{word:'to'}},
  {word:'být', stableRank:2, item:{word:'je'}},
 ];
 assert.equal(Math.round(ctx.levelCoverage(samples, 1, 3) * 1000) / 1000, 0.06);
 // Samples without an item (other callers) still read their own word.
 assert.equal(ctx.levelCoverage([{word:'to', stableRank:1}], 1, 2), 0.036);
})().catch(e => { console.error(e); process.exit(1); });
''')
        self.assertEqual(result.returncode, 0, result.stderr)


if __name__ == '__main__':
    unittest.main()
