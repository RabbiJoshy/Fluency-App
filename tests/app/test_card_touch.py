"""Exercise the real touch arbiter without claiming physical-device coverage."""
from pathlib import Path
import shutil
import subprocess
import unittest

ROOT = Path(__file__).resolve().parents[2]


@unittest.skipUnless(shutil.which('node'), 'Node.js required')
class CardTouchTests(unittest.TestCase):
    def test_touch_arbitration(self):
        result = subprocess.run(['node', '--input-type=module', '-'], cwd=ROOT,
                                text=True, capture_output=True, input=r'''
import assert from 'node:assert/strict';
import fs from 'node:fs';
import vm from 'node:vm';
const source = fs.readFileSync('app/js/card-touch.js', 'utf8');
const {installCardTouch} = await import('data:text/javascript;base64,' + Buffer.from(source).toString('base64'));
function classes(initial=[]) {
 const s=new Set(initial);
 return {contains:k=>s.has(k),add:k=>s.add(k),remove:(...ks)=>ks.forEach(k=>s.delete(k)),
 toggle(k,value){if(value)s.add(k);else s.delete(k);}};
}
function fixture({flipped=true,control=false,scroll=false,scrubber=false}={}) {
 const listeners={}, grades=[], cycles=[], haptics=[];let feedback=null, busy=false, pressesCancelled=0, flips=0;
 const card={dataset:{},classList:classes(flipped?['flipped']:[]),style:{},
  addEventListener(k,fn){(listeners[k]||=[]).push(fn);}};
 const port={parentElement:card,scrollHeight:500,clientHeight:100,overflowY:'auto'};
 const target={parentElement:scroll?port:card,overflowY:'visible',closest(selector){
  if(selector==='.card-back-scrubber')return scrubber?{}:null;
  return control?{}:null;
 }};
 const correctIndicator={classList:classes()},incorrectIndicator={classList:classes()};
 const options={card,correctIndicator,incorrectIndicator,grade:d=>grades.push(d),cycle:s=>cycles.push(s),
  feedback:d=>feedback=d,busy:()=>busy,cancelPress:()=>pressesCancelled++,haptic:ms=>haptics.push(ms),getStyle:n=>n};
 installCardTouch(options);installCardTouch(options); // setup is idempotent
 const flashcardsSource=fs.readFileSync('app/js/flashcards.js','utf8');
 const clickStart=flashcardsSource.indexOf("    flashcard.addEventListener('click'",flashcardsSource.indexOf('// Flip on back side'));
 const clickEnd=flashcardsSource.indexOf('// Arrow buttons',clickStart);
 vm.runInNewContext(flashcardsSource.slice(clickStart,clickEnd),{
  flashcard:card,suppressCardFlipUntil:0,Date,flipCard:()=>flips++});
 const touch=(x=0,y=0,id=1)=>({identifier:id,clientX:150+x,clientY:100+y});
 function emit(type,extra={}) {
  const e={target,touches:[],changedTouches:[],cancelable:true,detail:1,
   preventDefault(){this.prevented=true;},stopImmediatePropagation(){this.stopped=true;},...extra};
  for(const fn of listeners[type]||[]){fn(e);if(e.stopped)break;}
  return e;
 }
 return {card,grades,cycles,haptics,correctIndicator,incorrectIndicator,
  start:()=>emit('touchstart',{touches:[touch()]}),
  move:(x,y=0)=>emit('touchmove',{touches:[touch(x,y)]}),
  end:(x,y=0)=>emit('touchend',{changedTouches:[touch(x,y)]}),
  cancel:()=>emit('touchcancel'),click:extra=>emit('click',extra),
  multi:()=>emit('touchstart',{touches:[touch(),touch(0,0,2)]}),
  setBusy:v=>busy=v,feedback:()=>feedback,pressesCancelled:()=>pressesCancelled,flips:()=>flips};
}
for(const sign of [-1,1]) {
 const f=fixture();f.start();f.move(sign*49);
 const activeIndicator=sign>0?f.correctIndicator:f.incorrectIndicator;
 const commitClass=sign>0?'swipe-commit-correct':'swipe-commit-incorrect';
 assert.equal(f.feedback(),null);assert.equal(f.card.classList.contains('swiping'),true);
 assert.equal(activeIndicator.classList.contains('dragging'),true);
 assert.equal(activeIndicator.classList.contains('visible'),false);
 assert.deepEqual(f.haptics,[]);
 f.move(sign*50);assert.equal(f.feedback(),sign>0?'correct':'incorrect');
 assert.equal(activeIndicator.classList.contains('visible'),true);
 assert.equal(f.card.classList.contains(commitClass),true);
 assert.deepEqual(f.haptics,[8]);
 // Further movement beyond threshold does not spam haptics.
 f.move(sign*65);assert.deepEqual(f.haptics,[8]);
 const release=f.end(sign*50);assert.equal(release.stopped,true);
 assert.deepEqual(f.grades,[sign>0?'correct':'incorrect']);
 assert.equal(f.card.style.transform,'');assert.equal(f.feedback(),null);
 assert.equal(activeIndicator.classList.contains('dragging'),false);
 assert.equal(f.card.classList.contains(commitClass),false);
 assert.equal(f.click().prevented,true);
}
for(const distance of [0,9,13,49]) {
 const f=fixture();f.start();f.move(distance);const release=f.end(distance);
 assert.deepEqual(f.grades,[]);assert.deepEqual(f.cycles,[]);
 if(distance<10){assert.equal(release.prevented,undefined);assert.equal(f.click().prevented,undefined);}
 else assert.equal(f.click().prevented,true);
}
// A final changedTouch, rather than a stale last move, decides commitment.
{const f=fixture();f.start();f.move(60);f.end(20);assert.deepEqual(f.grades,[]);}
{const f=fixture();f.start();f.move(60);f.move(60,140);assert.equal(f.feedback(),null);
 f.end(60,140);assert.deepEqual(f.grades,[]);assert.deepEqual(f.cycles,[]);}
{const f=fixture();f.start();f.move(0,15);f.move(80,15);f.end(80,15);
 assert.deepEqual(f.grades,[]);}
{const f=fixture();f.start();f.move(60,60);f.end(60,60);assert.deepEqual(f.grades,[]);}
// Actual overflow owns vertical motion; no preventDefault, content cycling or grade.
{const f=fixture({scroll:true});f.start();const move=f.move(0,-60);
 assert.equal(move.prevented,undefined);f.cancel();assert.equal(f.card.style.transform,'');
 assert.deepEqual(f.cycles,[]);assert.deepEqual(f.grades,[]);}
{const f=fixture({scroll:true});f.start();f.move(0,60);f.end(0,60);assert.deepEqual(f.cycles,[]);}
for(const step of [-1,1]) {
 const f=fixture();f.start();assert.equal(f.move(0,-step*40).prevented,true);
 f.end(0,-step*40);assert.deepEqual(f.cycles,[step]);
}
{const f=fixture({control:true});f.start();f.end(0);assert.equal(f.click().prevented,undefined);
 f.start();f.move(-60);f.end(-60);assert.deepEqual(f.grades,['incorrect']);
 assert.equal(f.click().prevented,true);assert.ok(f.pressesCancelled()>0);
 // A subsequent deliberate button tap still works.
 f.start();f.end(0);assert.equal(f.click().prevented,undefined);}
{const f=fixture({control:true});f.start();f.move(0,40);f.end(0,40);assert.deepEqual(f.cycles,[]);}
for(const stop of ['cancel','multi']) {
 const f=fixture();f.start();f.move(60);f[stop]();assert.equal(f.end(60).stopped,true);
 assert.deepEqual(f.grades,[]);assert.equal(f.card.style.transform,'');
 assert.equal(f.correctIndicator.classList.contains('visible'),false);
 assert.equal(f.card.classList.contains('swiping'),false);
}
{const f=fixture({scrubber:true});f.start();f.move(60);f.end(60);assert.deepEqual(f.grades,[]);}
{const f=fixture();f.setBusy(true);f.start();f.move(60);f.end(60);assert.deepEqual(f.grades,[]);}
{const f=fixture();f.start();f.move(60);f.setBusy(true);f.end(60);assert.deepEqual(f.grades,[]);}
// Front and back taps have one owner: no flip callback in the touch arbiter.
for(const flipped of [false,true]) {
 const f=fixture({flipped});f.start();f.end(0);assert.equal(f.click().prevented,undefined);
 assert.equal(f.flips(),1);
 f.start();f.move(60);f.end(60);
 f.click();assert.equal(f.flips(),1);
 assert.equal(f.click({detail:0}).prevented,undefined);
 assert.equal(f.click({sourceCapabilities:{firesTouchEvents:false}}).prevented,undefined);
}
''')
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_grading_guard_and_hint(self):
        result = subprocess.run(['node', '-'], cwd=ROOT, text=True,
                                capture_output=True, input=r'''
const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict');
const source=fs.readFileSync('app/js/flashcards.js','utf8');
const start=source.indexOf('let gradingInProgress = false;');
const end=source.indexOf('// Position labels',start);
let hints=0,records=0,advance=0,callbacks=[];
const card={classList:{contains:()=>false,add(){},remove(){}},style:{}};
const context={flashcards:[{}],currentIndex:0,cardNavStack:[],rememberGradingSwipe:()=>hints++,
 stopExampleAutoplay(){},document:{getElementById:()=>card},recordCardResult:()=>records++,
 setTimeout:fn=>callbacks.push(fn),stepToSplitSibling:()=>false,advanceToNextDeckCard:()=>advance++,
 buildCardChildren:async()=>[],startCardChain(){},finishPhraseChain(){}};
vm.runInNewContext(source.slice(start,end),context);
(async()=>{
 context.handleSwipeAction('incorrect');context.handleSwipeAction('incorrect',{gesture:true});
 assert.equal(records,1);assert.equal(hints,0);assert.equal(callbacks.length,1);
 await callbacks.shift()();assert.equal(advance,1);
 context.handleSwipeAction('incorrect',{gesture:true});assert.equal(hints,1);
 await callbacks.shift()();
 // The guard also releases after an asynchronous chain-building failure.
 context.buildCardChildren=async()=>{throw new Error('failed fetch');};
 context.handleSwipeAction('correct',{gesture:true});
 await assert.rejects(callbacks.shift()());
 context.handleSwipeAction('incorrect');assert.equal(records,4);
 await callbacks.shift()();
})();
''')
        self.assertEqual(result.returncode, 0, result.stderr)
