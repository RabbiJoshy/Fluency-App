"""Master Smart Skip advances empty levels without overriding learner navigation."""
from pathlib import Path
import shutil
import subprocess
import unittest

ROOT = Path(__file__).resolve().parents[2]


@unittest.skipUnless(shutil.which('node'), 'Node.js required')
class SmartSkipAdvanceTests(unittest.TestCase):
    def test_actionable_levels_and_stale_toggle(self):
        script = r'''
const fs=require('fs'),vm=require('vm'),assert=require('node:assert/strict');
const source=fs.readFileSync('app/js/ui.js','utf8');
const start=source.indexOf('async function findFirstIncompleteLevelBtn(');
const end=source.indexOf('async function renderLevelSelector(',start);
const counts=[0,0,2], buttons=counts.map((_,i)=>({
 dataset:{level:String(i+1),startRank:String(i+1),endRank:String(i+2),rankBasis:'stable'},
 classList:{toggle(){}},style:{setProperty(){}},
 click(){ctx.selectedLevel=this.dataset.level;ctx.__studySessionContext={unseenCount:counts[i]};this._rangeRenderPromise=Promise.resolve();}
}));
const vocab=counts.map((n,i)=>({stableRank:i+1,new:n}));
const ctx={console,selectedLanguage:'spanish',selectedLevel:'1',activeArtist:null,
 artistVocabularyScope:'main',config:{languages:{spanish:{}}},levelEstimates:{},currentUser:{isGuest:true},
 fetchActiveVocabularyData:async()=>vocab,getPreparedSetupVocabulary:()=>({vocab}),
 getSetupLearningState:item=>({seen:!item.new}),_levelRankAccessor:()=>x=>x.stableRank,
 _findRangeSlice:(v,rank,min,max)=>v.filter(x=>rank(x)>=min&&rank(x)<max),
 _findLevelButtonIndex:(bs,level)=>bs.findIndex(b=>b.dataset.level===level),
 _scrollLevelSegToCenter:()=>{},__studySessionContext:{unseenCount:1},
 document:{getElementById:()=>({classList:{contains:()=>false}}),
 querySelectorAll:s=>s.includes('lswSlider')?[]:buttons}};
ctx.window=ctx;
vm.runInNewContext(source.slice(start,end),ctx);
(async()=>{
 assert.equal(await ctx.advanceSmartSkipLevel('spanish','1'),null);
 assert.equal(ctx.selectedLevel,'1','stay when new words remain');
 ctx.__studySessionContext.unseenCount=0;
 assert.equal(await ctx.advanceSmartSkipLevel('spanish','1'),
 'No new words left in Level 1 · Moved to Level 3');
 assert.equal(ctx.selectedLevel,'3','skip completed middle levels');
 ctx.__studySessionContext.unseenCount=0;
 assert.equal(await ctx.advanceSmartSkipLevel('spanish','3'),'No new words in this or later levels.');
 assert.equal(ctx.selectedLevel,'3','no wraparound or review fallback');
 ctx.selectedLevel='1';
 assert.equal(await ctx.advanceSmartSkipLevel('spanish','1',()=>false),null,'disabled toggle cancels');
 const original=ctx.fetchActiveVocabularyData;
 ctx.fetchActiveVocabularyData=async()=>{ctx.selectedLevel='2';return vocab;};
 assert.equal(await ctx.advanceSmartSkipLevel('spanish','1'),null,'manual navigation wins during await');
 assert.equal(ctx.selectedLevel,'2');
 ctx.fetchActiveVocabularyData=original;
})().catch(e=>{console.error(e);process.exit(1)});
'''
        result = subprocess.run(['node', '-'], input=script, cwd=ROOT, text=True, capture_output=True)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
