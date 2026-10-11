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
 cardNavStack:[], stats:{rangeString:'1-25',setSize:25,levelSession:true,remainingSessionCards:7},
 document:{getElementById:()=>({classList:{contains:key=>key==='flipped'}}),querySelectorAll:()=>[]},
 config:{languages:{Spanish:{name:'Spanish'}}}, selectedLanguage:'Spanish', selectedLevel:'1',
 activeArtist:null, window:{}, selectedSongIds:[], groupSize:25,
 useLemmaMode:false, excludeCognates:false, hideSingleOccurrence:true,
 excludeProperNouns:true,excludeNoise:true,excludeSlang:false,excludeGrammarParticles:false,
 excludeEnglishLoanwords:true, isFlipped:false,speechEnabled:true,
 currentMeaningIndex:0,currentExampleIndex:0,currentMWEIndex:0,
 LAST_STUDY_SESSION_KEY:'session', studySessionStorageKey:key=>key, studySessionScope:()=> 'speech:Spanish',
 localStorage:{setItem:(key,value)=>saved.set(key,JSON.parse(value))}
};
const start = source.indexOf('function _writeStudySessionSnapshot()');
const end = source.indexOf("if (typeof window !== 'undefined')",start);
vm.runInNewContext(source.slice(start,end),context);
context._writeStudySessionSnapshot();
assert.equal(saved.get('session').levelSession,true);
assert.equal(saved.get('session').remainingSessionCards,7);
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

    def test_return_prompt_uses_safe_personal_greeting_and_saved_card(self):
        result = subprocess.run(['node', '-'], cwd=ROOT, text=True, capture_output=True, input=r'''
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const source = fs.readFileSync('app/js/vocab.js', 'utf8');
const nodes = new Map();
const getNode = id => {
 if (!nodes.has(id)) nodes.set(id, {textContent:'', addEventListener(type, fn){this[type]=fn;}, focus(){this.focused=true;}});
 return nodes.get(id);
};
const card = {setAttribute(){}, querySelector:id=>getNode(id.slice(1)),
 addEventListener(type,fn){this[type]=fn;}, remove(){this.removed=true;}};
const snapshot = {languageName:'Spanish', language:'spanish', mode:'speech',
 levelNumber:2, setNumber:3, currentWord:'<saved word>', savedAt:'snapshot'};
const saved = new Map();
const context = {
 currentUser:{username:'<Alex>',isGuest:false}, URLSearchParams,
 window:{location:{search:''}}, getLastStudySession:()=>snapshot,
 sessionStorage:{getItem:key=>saved.get(key),setItem:(key,val)=>saved.set(key,val)},
 document:{querySelector:()=>null,getElementById:id=>nodes.get(id),
 createElement:()=>card,body:{appendChild(){getNode('resumeLastSetBtn');getNode('dismissResumeLastSetBtn');}}},
 resumeLastStudySession(){context.continued=true;}
};
vm.runInNewContext(source.slice(source.indexOf('function renderResumeLastSetCard()'),
 source.indexOf('function clearStudySessionSnapshot()')), context);
context.renderResumeLastSetCard();
assert.equal(nodes.get('resumeEntryGreeting').textContent,'Welcome back, <Alex>');
assert.equal(nodes.get('resumeEntryWord').textContent,'<saved word>');
assert.equal(nodes.get('resumeEntrySet').textContent,'Level 2 · Saved session');
assert.ok(!card.innerHTML.includes('<Alex>'));
assert.ok(nodes.get('resumeLastSetBtn').focused);
nodes.get('resumeLastSetBtn').click();
assert.ok(card.removed);
assert.ok(context.continued);
assert.equal(saved.get('fluency_resume_prompt_seen_v1'),'snapshot');
context.currentUser={isGuest:true};
saved.clear();
context.renderResumeLastSetCard();
assert.equal(nodes.get('resumeEntryGreeting').textContent,'Welcome back');
card.keydown({key:'Escape'});
assert.ok(card.removed);
''')
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_explicit_speech_switch_cannot_resume_last_lyrics_set(self):
        result = subprocess.run(['node', '-'], cwd=ROOT, text=True, capture_output=True, input=r'''
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const source = fs.readFileSync('app/js/vocab.js', 'utf8');
const lyrics = {mode:'lyrics',artistSlug:'bad-bunny',language:'spanish'};
const speech = {mode:'speech',language:'spanish'};
const saved = new Map([['session',lyrics],['session:speech:spanish',speech],['session:lyrics:bad-bunny',lyrics]]);
const storage = new Map();
let speechChosen = false;
const context = {
 activeArtist:null,selectedLanguage:'spanish',selectedSongIds:[],LAST_STUDY_SESSION_KEY:'session',
 window:{fluencyRoute:{kind:'home'},_urlArtistSlug:'bad-bunny',_selectedArtistSlugs:['bad-bunny']},
 document:{getElementById:()=>({classList:{contains:()=>speechChosen}})},
 sessionStorage:{getItem:key=>storage.get(key)},
 readStudySession:key=>saved.get(key)||null,
 studySessionScope:s=>`${s.mode}:${s.artistSlug||s.language}`,
 studySessionMatchesCurrentRelease:()=>true
};
vm.runInNewContext(source.slice(source.indexOf('function activeStudySessionScope()'),source.indexOf('function currentLyricsReleaseId()')),context);
vm.runInNewContext(source.slice(source.indexOf('function getLastStudySession()'),source.indexOf('function renderResumeLastSetCard()')),context);
// Normal landing retains the latest saved deck.
assert.equal(context.getLastStudySession(),lyrics);
// A pending switch is scoped even before asynchronous Speech setup finishes.
storage.set('fluencyPendingSpeechLanguage','spanish');
assert.equal(context.getLastStudySession(),speech);
storage.clear();speechChosen=true;
assert.equal(context.getLastStudySession(),speech);
saved.delete('session:speech:spanish');
assert.equal(context.getLastStudySession(),null);
// Legacy global speech snapshots still work, but a different language does not.
saved.set('session',speech);assert.equal(context.getLastStudySession(),speech);
context.selectedLanguage='portuguese';assert.equal(context.getLastStudySession(),null);
// An explicitly chosen Lyrics deck retains its own history.
context.activeArtist={language:'spanish'};assert.equal(context.getLastStudySession(),lyrics);
''')
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_activity_entry_waits_for_a_choice_and_translation_is_lyrics_only(self):
        result = subprocess.run(['node', '-'], cwd=ROOT, text=True, capture_output=True, input=r'''
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const main = fs.readFileSync('app/js/main.js','utf8');
let mode='speech', sheet=null, closed=0;
const context = {
 activeArtist:null,selectedLanguage:'spanish',window:{location:{href:'original'},currentLearningMode:()=>mode},
 document:{getElementById:()=>null},
 closeLearningContext:()=>closed++,showChoiceSheet:options=>{sheet=options;},languageDisplayName:()=> 'Spanish',learningContextModal:null
};
const start=main.indexOf('    const openActivityChoice =');
const end=main.indexOf("    document.getElementById('learningContextVerbsBtn')",start);
vm.runInNewContext(main.slice(start,end)+'\nthis.openActivityChoice=openActivityChoice;',context);
context.openActivityChoice('translation','lyrics-view/');
assert.equal(sheet,null);assert.equal(context.window.location.href,'original');
context.openActivityChoice('verbs','conjugation/?lang=es');
assert.equal(closed,1);assert.equal(context.window.location.href,'original');
assert.equal(sheet.title,'Verb conjugations');sheet.entries[0].onSelect();
assert.equal(context.window.location.href,'conjugation/?lang=es');
mode='lyrics';context.openActivityChoice('translation','lyrics-view/');
assert.equal(sheet.title,'Song translation');
assert.equal(context.window.location.href,'conjugation/?lang=es');
sheet.entries[0].onSelect();assert.equal(context.window.location.href,'lyrics-view/');
const ui=fs.readFileSync('app/js/ui.js','utf8');
const row={hidden:false,dataset:{}};
const visibility={document:{getElementById:()=>row},modeKey:'speech'};
const a=ui.indexOf("    const lyricsViewRow = document.getElementById('learningContextLyricsViewBtn');");
const b=ui.indexOf('    const activities =',a);
vm.runInNewContext(ui.slice(a,b).replace('const lyricsViewRow','var lyricsViewRow'),visibility);assert.equal(row.hidden,true);
visibility.modeKey='lyrics';vm.runInNewContext(ui.slice(a,b).replace('const lyricsViewRow','var lyricsViewRow'),visibility);assert.equal(row.hidden,false);
''')
        self.assertEqual(result.returncode, 0, result.stderr)
