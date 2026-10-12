"""Lyrics vocabulary must stay reachable inside the shared Smart Skip browser."""
from pathlib import Path
import shutil
import subprocess
import unittest

ROOT = Path(__file__).resolve().parents[2]


@unittest.skipUnless(shutil.which('node'), 'Node.js required')
class LyricsSmartSkipTests(unittest.TestCase):
    def test_supplementary_words_do_not_duplicate_setting_skips_and_study_is_bounded(self):
        result = subprocess.run(['node', '-'], cwd=ROOT, text=True, capture_output=True, input=r'''
const fs = require('node:fs'), vm = require('node:vm'), assert = require('node:assert/strict');
const nodes = new Map();
const node = id => {
 if (!nodes.has(id)) nodes.set(id, {hidden:true,disabled:false,value:'',setAttribute(k,v){this[k]=v;},classList:{add(){},remove(){}}});
 return nodes.get(id);
};
const ctx = {console, document:{readyState:'loading',addEventListener(){},getElementById:node},
 activeArtist:{name:'Fixture artist'},selectedLanguage:'spanish',selectedSongIds:[],
 excludeCognates:true, cognateFieldAvailable:true, excludeProperNouns:true,
 useLemmaMode:false, excludeGrammarParticles:false,excludeSlang:false,
 isCognateKnown:item=>item.cognate_score === 1,
 getWordId:item=>item.id,
 getWordProgressState:id=>({seen:id==='known'}),
 getWordKnowledgeReviewInfo:()=>({needsReview:false}),
 showAppLoading(){},hideAppLoading(){},getActiveLevelRanges:()=>[],
};
ctx.window = ctx;
const vocab = fs.readFileSync('app/js/vocab.js','utf8');
vm.runInNewContext(vocab.slice(vocab.indexOf('const ARTIST_EXTRA_CATEGORIES'),vocab.indexOf('function assignExtraCategoryRanks')),ctx);
vm.runInNewContext(fs.readFileSync('app/js/extras.js','utf8').replace(/^import .*;$/gm,''),ctx);
const words = Array.from({length:35},(_,i)=>({id:`song${i}`,word:`songword${i}`,rank:i+1,
 extra_category:'proper_noun',cognate_score:1,is_propernoun:true,
 meanings:[{translation:'place',pos:'PROPN'}]}));
ctx.setupVocabularySnapshot = [...words,{id:'core',word:'idea',rank:100,cognate_score:1,
 meanings:[{translation:'idea'}]}, {id:'known',word:'known',rank:101,extra_category:'english',meanings:[]}];
let extras = ctx.collectExtras();
assert.equal(extras.supplementary.length,36);
assert.equal(extras.cognates.length,1);
assert.equal(extras.cognates[0].item.id,'core');
assert.equal(extras.entities.length,0); // a supplementary name has one home
assert.equal(extras.supplementaryByCategory['song:proper_noun'].length,35);
// Still browse every supplementary word with all shortcuts disabled.
ctx.excludeCognates=false;ctx.excludeProperNouns=false;
extras=ctx.collectExtras();
assert.equal(extras.allSkipped.length,0);assert.equal(extras.supplementary.length,36);
vm.runInNewContext("_ssSource='songs'; _activeSkippedCategory='song:all';",ctx);
let options=vm.runInNewContext('smartSkipMenu(collectExtras()).options',ctx);
assert.equal(options.length,3);
assert(options.some(o=>o.id==='song:english'));
// The search filters words and meanings before selecting a bounded study deck.
(async()=>{
 let loaded;
 ctx.loadVocabularyData=async(range,opts)=>{loaded={range,opts};return true;};
 node('smartSkipStudySongsBtn').disabled=false;
 await vm.runInNewContext('studySupplementarySongWords()',ctx);
 assert.equal(loaded.opts.fastTrackCards.length,20);
 assert.equal(loaded.opts.sessionLimit,20);
 assert.equal(loaded.opts.isFastTrack,true);
 vm.runInNewContext("updateSupplementaryStudyButton(collectExtras(),'song:all','')",ctx);
 assert.equal(node('smartSkipStudySongsBtn').textContent,'Study 20 words');
 assert.equal(ctx.artistVocabularyScope,undefined); // study never switches the main deck
 vm.runInNewContext("_ssQuery='songword34';",ctx);
 vm.runInNewContext("updateSupplementaryStudyButton(collectExtras(),'song:all','songword34')",ctx);
 assert.equal(node('smartSkipStudySongsBtn').textContent,'Study 1 match');
 await vm.runInNewContext('studySupplementarySongWords()',ctx);
 assert.equal(loaded.opts.fastTrackCards.length,1);
 assert.equal(loaded.opts.fastTrackCards[0].id,'song34');
 vm.runInNewContext("_ssQuery='no-match';",ctx);loaded=null;
 await vm.runInNewContext('studySupplementarySongWords()',ctx);
 assert.equal(loaded,null);
 // Speech has the same browser with no supplementary vocabulary source.
 ctx.activeArtist=null;
 assert.equal(ctx.collectExtras().supplementary.length,0);
 console.log('Lyrics Smart Skip execution checks passed');
})().catch(e=>{console.error(e);process.exit(1)});
''')
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_resume_keeps_supplementary_and_skipped_ids_in_saved_order(self):
        result = subprocess.run(['node', '-'], cwd=ROOT, text=True, capture_output=True, input=r'''
const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict');
const source=fs.readFileSync('app/js/vocab.js','utf8');
const ctx={getWordId:item=>item.id};
vm.runInNewContext(source.slice(source.indexOf('function resumeVocabularyEntries'),source.indexOf('async function resumeLastStudySession')),ctx);
const all=[{id:'core'}, {id:'loanword',extra_category:'loanword'}, {id:'name',extra_category:'proper_noun'}, {id:'skip'}];
const snapshot={order:['name::split::noun','loanword','name::split::verb','skip']};
assert.deepEqual(Array.from(ctx.resumeVocabularyEntries(all,snapshot),x=>x.id),['name','loanword','skip']);
assert.equal(all.length,4); // source ordering is never mutated
''')
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_legacy_unlock_gate_and_separate_panel_are_not_exposed(self):
        main = (ROOT/'app/js/main.js').read_text()
        ui = (ROOT/'app/js/ui.js').read_text()
        vocab = (ROOT/'app/js/vocab.js').read_text()
        html = (ROOT/'app/index.html').read_text()
        self.assertNotIn('ARTIST_EXTRA_UNLOCK_PCT', main)
        self.assertNotIn('Unlocks at 60%', ui)
        self.assertNotIn('Artist Extra unlocks', vocab)
        self.assertNotIn('id="extraScopeModal"', html)
        self.assertIn("window.openSkippedWords?.('song:all')", main)


if __name__ == '__main__':
    unittest.main()
