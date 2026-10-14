// Render setup snapshots from the session harness and exercise the real scrubber.
import assert from 'node:assert/strict';
import {createRequire} from 'node:module';
import {readFile,mkdir} from 'node:fs/promises';
import {createServer} from 'node:http';
import {execFileSync} from 'node:child_process';
import path from 'node:path';
import os from 'node:os';
const {chromium}=createRequire(import.meta.url)('playwright');
const fixturesPath=path.join(os.tmpdir(),`session-endpoints-${process.pid}.json`);
execFileSync(process.execPath,['tests/app/study_session_checks.cjs'],{env:{...process.env,SESSION_ENDPOINT_FIXTURES:fixturesPath}});
const fixtures=JSON.parse(await readFile(fixturesPath,'utf8'));
const config=JSON.parse(await readFile('app/config/config.json','utf8'));
const root=path.resolve('.');
const server=createServer(async(req,res)=>{
 try{
  const file=path.join(root,req.url.split('?')[0]);
  res.setHeader('Content-Type',({'.html':'text/html','.css':'text/css','.json':'application/json','.woff2':'font/woff2'})[path.extname(file)]||'text/javascript');
  res.end(await readFile(file));
 }catch{res.writeHead(404);res.end();}
});
await new Promise(resolve=>server.listen(0,'127.0.0.1',resolve));
let browser;
try{
 browser=await chromium.launch({headless:true,channel:'chrome'});
 for(const width of [320,390,1000])for(const theme of ['dark','light']){
  const page=await browser.newPage({viewport:{width,height:844}});
  await page.route('https://**/*',route=>route.abort());
  await page.goto(`http://127.0.0.1:${server.address().port}/app/index.html`);
  await page.waitForFunction(()=>typeof window.updateCard==='function');
  await page.addStyleTag({content:'.modal {display:none!important} *{transition:none!important;animation:none!important}'});
  for(const [name,setup,practice]of [['long',fixtures.long,fixtures.practiceLong],['short',fixtures.short,fixtures.practice]]){
   await page.evaluate(({setup,practice,theme})=>{
    document.documentElement.dataset.theme=theme;
    document.getElementById('setupPanel').style.display='block';
    document.getElementById('appContent').classList.add('hidden');
    for(const id of ['step1','step2','step3'])document.getElementById(id)?.style.setProperty('display','none');
    const step=document.getElementById('step4');step.style.display='block';step.classList.remove('hidden');
    document.getElementById('rangeSelector').innerHTML=setup;
    document.getElementById('studySessionLevel').textContent=' · Level 4';
    document.getElementById('reviewDeckSection').hidden=false;
    document.getElementById('reviewDeckSection').style.display='block';
    document.getElementById('reviewDeckBody').innerHTML=practice;
   },{setup,practice,theme});
   assert.match(await page.locator('#studySetStartBtn').textContent(),name==='long'?/20 new/:/11 new/);
   assert.equal(await page.locator('#step4 .session-length-chip').count(),name==='long'?1:0);
   assert.equal(await page.locator('#quickReviewBtn').textContent(),'Practise');
   const sizes=await page.locator('.review-deck-summary-copy').evaluate(el=>({main:parseFloat(getComputedStyle(el.querySelector('strong')).fontSize),later:parseFloat(getComputedStyle(el.querySelector('small')).fontSize)}));
   assert(sizes.later<sizes.main);
   const overflow=await page.locator('#rangeSelector').evaluate(el=>el.scrollWidth>el.clientWidth);
   assert(!overflow,`${name} setup overflows at ${width}`);
   if(process.env.SESSION_ENDPOINT_SCREENSHOTS){await mkdir(process.env.SESSION_ENDPOINT_SCREENSHOTS,{recursive:true});await page.screenshot({path:path.join(process.env.SESSION_ENDPOINT_SCREENSHOTS,`${name}-${theme}-${width}.png`)});}
  }
  await page.evaluate(({config})=>{
   globalThis.config=config;selectedLanguage='spanish';activeArtist=null;currentUser={isGuest:true};
   currentIndex=0;currentMeaningIndex=0;currentMWEIndex=0;currentExampleIndex=0;currentGroupSelection=null;cardNavStack=[];cardChainReturnIndex=-1;stats.levelNumber=4;
   flashcards=Array.from({length:20},(_,i)=>({fullId:`session-${i}`,targetWord:`word${i}`,partOfSpeech:'NOUN',isMultiMeaning:true,meanings:[{pos:'NOUN',meaning:'word',percentage:1,allExamples:[]}],links:[]}));
   document.getElementById('setupPanel').style.display='none';document.getElementById('reviewDeckSection').hidden=true;
   document.getElementById('appContent').classList.remove('hidden');
   for(let el=document.getElementById('flashcard').parentElement;el;el=el.parentElement){el.classList.remove('hidden');if(getComputedStyle(el).display==='none')el.style.display='block';}
   document.getElementById('flashcard').classList.remove('flipped');window.updateCard();
  },{config});
  assert.equal(await page.locator('.cbs-end-label').textContent(),'20');
  assert(await page.locator('.cbs-end-label').isVisible());
  if(process.env.SESSION_ENDPOINT_SCREENSHOTS)await page.screenshot({path:path.join(process.env.SESSION_ENDPOINT_SCREENSHOTS,`scrubber-${theme}-${width}.png`)});
  const railWidth=await page.locator('.cbs-track-wrap').evaluate(el=>el.getBoundingClientRect().width);
  await page.evaluate(()=>{currentIndex=19;window.updateCard();});
  assert.equal(await page.locator('.cbs-thumb-num').textContent(),'20');
  assert.equal(await page.locator('.cbs-track-wrap').evaluate(el=>el.getBoundingClientRect().width),railWidth);
  await page.evaluate(()=>{flashcards=flashcards.slice(0,1);currentIndex=0;window.updateCard();});
  assert(!await page.locator('.cbs-end-label').isVisible());
  await page.evaluate(()=>{
   flashcards[0].splitInfo={index:1,total:2};flashcards.push({...flashcards[0],splitInfo:{index:2,total:2}});window.updateCard();
  });
  assert.equal(await page.locator('.cbs-end-label').textContent(),'1B');
  await page.evaluate(()=>{
   flashcards[0].splitInfo=null;flashcards[1].splitInfo=null;
   flashcards.push({isChainChild:true});cardChainReturnIndex=0;currentIndex=2;
   // A phrase-summary card uses dedicated content; updateCard still excludes
   // the temporary slot from the endpoint.
   flashcards[2]={...flashcards[0],isChainChild:true,chainParentWord:'word'};window.updateCard();
  });
  assert.equal(await page.locator('.cbs-end-label').textContent(),'2');
  await page.close();
 }
 console.log('Session counts, shortened tails, practice copy and scrubber endpoints passed in both themes at 320px, 390px and 1000px.');
}finally{await browser?.close();await new Promise(resolve=>server.close(resolve));}
