"""collectExtras is reused within one pass of work, and never stale.

Opening a deck asked for Smart Skip's categories about a dozen times, each a
full pass over the deck. The answer is now held until the pass ends, unless a
fingerprinted setting changes or a deck rewrite calls forgetSmartSkipExtras().
"""
from pathlib import Path
import shutil
import subprocess
import unittest

ROOT = Path(__file__).resolve().parents[2]


@unittest.skipUnless(shutil.which('node'), 'Node.js required')
class SmartSkipExtrasCacheTests(unittest.TestCase):
    def test_one_pass_per_burst_and_never_stale(self):
        result = subprocess.run(['node', '-'], cwd=ROOT, text=True, capture_output=True, input=r'''
const fs = require('node:fs'), vm = require('node:vm'), assert = require('node:assert/strict');
let asked = 0;
const ctx = {console, document:{readyState:'loading',addEventListener(){},getElementById:()=>null},
 activeArtist:null, excludeCognates:true, cognateFieldAvailable:true, excludeProperNouns:false,
 useLemmaMode:false, excludeGrammarParticles:false, excludeSlang:false,
 isCognateKnown:item => { asked += 1; return item.cognate_score === 1; },
};
ctx.window = ctx;
vm.runInNewContext(fs.readFileSync('app/js/extras.js','utf8').replace(/^import .*;$/gm,''),ctx);
const deck = Array.from({length:50},(_,i)=>({id:`w${i}`,word:`w${i}`,rank:i+1,cognate_score:i<10?1:0,meanings:[]}));
ctx.setupVocabularySnapshot = deck;
(async()=>{
 const first = ctx.collectExtras();
 for (let i = 0; i < 10; i++) ctx.collectExtras();
 assert.equal(asked, 50, 'eleven asks in one pass walk the deck once');
 assert.equal(first.cognates.length, 10);

 // A setting flipped mid-pass is seen at once.
 ctx.excludeCognates = false;
 assert.equal(ctx.collectExtras().cognates.length, 0);

 // A deck rewrite that keeps the same array announces itself.
 ctx.excludeCognates = true;
 ctx.collectExtras();
 deck[20].cognate_score = 1;
 ctx.forgetSmartSkipExtras();
 assert.equal(ctx.collectExtras().cognates.length, 11);

 // Nothing survives into the next pass, even unannounced.
 deck[21].cognate_score = 1;
 await Promise.resolve();
 assert.equal(ctx.collectExtras().cognates.length, 12);

 // An unloaded deck is asked again rather than remembered as empty.
 ctx.setupVocabularySnapshot = null;
 assert.equal(ctx.collectExtras().ready, false);
 ctx.setupVocabularySnapshot = deck;
 assert.equal(ctx.collectExtras().ready, true);
})().catch(e=>{console.error(e);process.exit(1)});
''')
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_render_lookalikes_populates_table(self):
        result = subprocess.run(['node', '-'], cwd=ROOT, text=True, capture_output=True, input=r'''
const fs = require('node:fs'), vm = require('node:vm'), assert = require('node:assert/strict');

const sentinelEl = {
    insertAdjacentHTML(pos, html) { listEl.innerHTML += html; },
    remove() {}
};
const rowsEl = {
    innerHTML: '',
    insertAdjacentHTML(pos, html) {
        this.innerHTML += html;
        listEl.innerHTML += html;
    }
};
const listEl = {
    innerHTML: '',
    querySelector(sel) {
        if (sel.includes('.smart-skip-sentinel')) return sentinelEl;
        if (sel.includes('.smart-skip-group-rows')) return rowsEl;
        return null;
    },
    querySelectorAll() { return []; }
};
const body = {
    innerHTML: '',
    querySelector(sel) {
        if (sel === '.smart-skip-list') return listEl;
        return null;
    }
};
const makeStub = () => ({
    innerHTML: '', textContent: '', value: '', hidden: false,
    classList: { add(){}, remove(){}, toggle(){} },
    setAttribute(){}, getAttribute(){ return ''; },
    removeAttribute(){}, toggleAttribute(){}, addEventListener(){},
    querySelector(){ return null; }, querySelectorAll(){ return []; },
    closest(){ return makeStub(); }, remove(){}
});

const ctx = {
    console,
    selectedLanguage: 'spanish',
    excludeCognates: true,
    cognateFieldAvailable: true,
    excludeProperNouns: false,
    useLemmaMode: false,
    excludeGrammarParticles: false,
    excludeSlang: false,
    activeKnownLanguages: () => ['en'],
    strongestKnownLanguage: (item) => ({ code: 'en', score: 0.9 }),
    isCognateKnown: (item) => true,
    isCognateKnownForLanguage: (item, code) => true,
    renderSavedItems: () => {},
    document: {
        readyState: 'loading',
        addEventListener(){},
        getElementById: (id) => {
            if (id === 'skippedWordsBody') return body;
            return makeStub();
        },
        querySelector: () => makeStub(),
        querySelectorAll: () => []
    }
};
ctx.window = ctx;
ctx.globalThis = ctx;
vm.runInNewContext(fs.readFileSync('app/js/extras.js', 'utf8').replace(/^import .*;$/gm, ''), ctx);
ctx.setupVocabularySnapshot = [
    { id: '1', word: 'hotel', rank: 1, meanings: [{ translation: 'hotel' }], cognate_score: 1 },
    { id: '2', word: 'problema', rank: 2, meanings: [{ translation: 'problem' }], cognate_score: 0.9 }
];

// Selecting "cognate" (Look-alikes) in the dropdown renders the table with rows
ctx.renderSkippedWords('cognate', { force: true });
assert.ok(body.innerHTML.includes('class="smart-skip-table"'), 'Table wrapper rendered');
assert.ok(rowsEl.innerHTML.includes('extras-row--cognate'), 'Lookalike row rendered');
''')
        self.assertEqual(result.returncode, 0, result.stderr)


if __name__ == '__main__':
    unittest.main()

