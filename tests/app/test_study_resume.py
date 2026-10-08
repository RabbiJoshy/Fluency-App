"""Save vocabulary identity when the learner stops on a temporary panel."""
from pathlib import Path
import shutil
import subprocess
import unittest

ROOT = Path(__file__).resolve().parents[2]

@unittest.skipUnless(shutil.which('node'), 'Node.js required')
class StudyResumeTests(unittest.TestCase):
    def test_phrase_panel_and_ordinary_card_snapshots(self):
        result = subprocess.run(['node', '-'], cwd=ROOT, text=True, capture_output=True, input=r'''
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const source = fs.readFileSync('app/js/vocab.js', 'utf8');
const saved = new Map();
const cards = [{fullId:'que-id', targetWord:'que', rank:1},
 {fullId:'la-id', targetWord:'la', rank:4}, {isChainChild:true, targetWord:'la'}];
const context = {
 _saveSnapshotTimer:null, flashcards:cards, currentIndex:2, cardChainReturnIndex:1,
 cardNavStack:[], stats:{rangeString:'1-25',setSize:25},
 document:{getElementById:()=>({classList:{contains:key=>key==='flipped'}}),querySelectorAll:()=>[]},
 config:{languages:{Spanish:{name:'Spanish'}}}, selectedLanguage:'Spanish', selectedLevel:'1',
 activeArtist:null, window:{}, selectedSongIds:[], groupSize:25,
 useLemmaMode:false, excludeCognates:false, hideSingleOccurrence:true,
 excludeProperNouns:true,excludeNoise:true,excludeSlang:false,excludeGrammarParticles:false,
 excludeEnglishLoanwords:true, isFlipped:false,speechEnabled:true,
 currentMeaningIndex:0,currentExampleIndex:0,currentMWEIndex:0,
 LAST_STUDY_SESSION_KEY:'session', studySessionScope:()=> 'speech:Spanish',
 localStorage:{setItem:(key,value)=>saved.set(key,JSON.parse(value))}
};
const start = source.indexOf('function _writeStudySessionSnapshot()');
const end = source.indexOf("if (typeof window !== 'undefined')",start);
vm.runInNewContext(source.slice(start,end),context);
context._writeStudySessionSnapshot();
assert.equal(saved.get('session').currentFullId,'la-id');
assert.equal(saved.get('session').currentVocabularyRank,4);
assert.equal(saved.get('session').currentWord,'la');
assert.equal(saved.get('session').cardFaceFlipped,true);
assert.deepEqual(saved.get('session').order,['que-id','la-id']);
context.currentIndex=0;
context._writeStudySessionSnapshot();
assert.equal(saved.get('session').currentFullId,'que-id');
assert.deepEqual(saved.get('session:speech:Spanish'),saved.get('session'));
''')
        self.assertEqual(result.returncode, 0, result.stderr)
