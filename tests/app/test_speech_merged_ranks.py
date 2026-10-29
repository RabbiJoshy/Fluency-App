"""Speech ranks follow level membership, not the currently loaded example shards."""
import shutil
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


@unittest.skipUnless(shutil.which('node'), 'Node.js required')
class SpeechMergedRankTests(unittest.TestCase):
    def test_redo_level_has_no_gaps_and_loading_examples_cannot_change_ranks(self):
        result = subprocess.run(['node', '-'], cwd=ROOT, capture_output=True, text=True, input=r'''
const fs = require('node:fs'), vm = require('node:vm'), assert = require('node:assert/strict');
const ctx = {
 console, localStorage: {getItem:()=>null,setItem(){}},
 document:{readyState:'complete',getElementById:()=>null,addEventListener(){}},
 window:{addEventListener(){}}, passesAssignmentFilters:()=>true,
 selectedLanguage:'spanish',activeArtist:null,artistVocabularyScope:'main',
 config:{languages:{spanish:{routeCode:'es'}}},cognateThreshold:0.75,
 isCognateKnown:()=>false,percentageMode:false,excludeSlang:false,
 excludeProperNouns:false,excludeEnglishLoanwords:false,excludeGrammarParticles:false,
 useLemmaMode:true,lemmaFieldAvailable:true,excludeCognates:false,cognateFieldAvailable:true
};
ctx.globalThis=ctx;
vm.runInNewContext(fs.readFileSync('app/js/vocab.js','utf8')
 .replace(/^import .*$/mg,'').replace(/^export /mg,''),ctx);
const examples = n => Array.from({length:n},(_,i)=>({target:`example ${i}`}));
const row = (word,headword,n=0) => ({word,id:word,
 meanings:[{pos:'VERB',headword,translation:'to act',examples:examples(n)}]});
// Source positions 1–6 form one level. Example sampling used to move the two
// later words between its fourth and fifth cards, yielding 1,2,3,4,7,8 on redo.
const words=['hablar','comer','vivir','mirar','beber','abrir','cantar','bailar'];
const data=words.map((word,i)=>row(word,word,i<4?3:i<6?1:2));
const ranks = () => ctx.buildFilteredVocab(data).vocab;
let ranked=ranks();
assert.deepEqual(Array.from(ranked.filter(x=>x.stableRank<=6),x=>x.displayRank),[1,2,3,4,5,6]);
const initial=Array.from(ranked,x=>[x.id,x.displayRank]);
// Loading another level must not alter the existing rank or order.
data[7].meanings[0].examples=examples(100);
assert.deepEqual(Array.from(ranks(),x=>[x.id,x.displayRank]),initial);
// A citation form later in the file still belongs at its earliest sibling's
// position. Collapsing the sibling leaves consecutive configuration ranks.
const merged=[row('hablo','hablar',1),row('comer','comer',2),row('hablar','hablar',40)];
ranked=ctx.buildFilteredVocab(merged).vocab;
assert.deepEqual(Array.from(ranked,x=>[x.word,x.stableRank,x.displayRank]),
 [['hablar',1,1],['comer',2,2]]);
console.log('Speech redo rank and lazy-example regression checks passed');
''')
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
