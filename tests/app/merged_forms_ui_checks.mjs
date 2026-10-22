// Exercise the real front renderer and disclosure across phone/desktop layouts.
import assert from 'node:assert/strict';
import {createRequire} from 'node:module';
import {readFile,mkdir} from 'node:fs/promises';
import {createServer} from 'node:http';
import path from 'node:path';
const {chromium}=createRequire(import.meta.url)('playwright');
const root=path.resolve('.');
const config=JSON.parse(await readFile('app/config/config.json','utf8'));
const rows=JSON.parse(await readFile('tests/app/fixtures/portuguese_verb_ui.json','utf8'));
const server=createServer(async(req,res)=>{
 try {
  const file=path.join(root,req.url.split('?')[0]);
  res.setHeader('Content-Type',({'.html':'text/html','.css':'text/css','.json':'application/json','.woff2':'font/woff2'})[path.extname(file)]||'text/javascript');
  res.end(await readFile(file));
 } catch {res.writeHead(404);res.end();}
});
await new Promise(resolve=>server.listen(0,'127.0.0.1',resolve));
let browser;
try {
 browser=await chromium.launch({headless:true,channel:'chrome'});
 for(const width of [320,390,1440]) {
  const page=await browser.newPage({viewport:{width,height:900},serviceWorkers:'block'});
  await page.route('https://**/*',route=>route.abort());
  await page.goto(`http://127.0.0.1:${server.address().port}/app/index.html`);
  await page.waitForFunction(()=>typeof window.updateCard==='function');
  await page.addStyleTag({content:'.modal {display:none !important;} #flashcard, #flashcard * {transition:none !important;animation:none !important;}'});
  await page.evaluate(({config,rows})=>{
   globalThis.config=config;selectedLanguage='portuguese';activeArtist=null;
   currentUser={initials:'TEST'};itemProgressData={};progressData={};stats.levelNumber=2;
   window._cachedJoinedIndex=rows;
   document.getElementById('setupPanel').style.display='none';
   document.getElementById('appContent').classList.remove('hidden');
   for(let el=document.getElementById('flashcard').parentElement;el;el=el.parentElement){el.classList.remove('hidden');if(getComputedStyle(el).display==='none')el.style.display='block';}
   const source=rows.find(row=>row.word==='saber');
   const base={...source,fullId:'pt-sabe',targetWord:'sabe',citationForm:'saber',displaySurface:'sabe',mergedLemma:true,
    mergedGroupSurfaces:['sabe','saberá','soubesses','sabermos','saberes','saberás'],rank:106,stableRank:106,vocabularyRank:106,
    sourceFrequency:1832,sourceFrequencyUnit:'per_million',sourceFrequencyBasis:'own',
    isMultiMeaning:true,partOfSpeech:'verb',links:[],meanings:source.meanings.map(m=>({...m,meaning:m.translation,senseId:m.sense_id,percentage:Number(m.frequency),canonicalExample:m.canonical_example,allExamples:[]}))};
   flashcards=[base,{...base,targetWord:'saber',displaySurface:'saber',mergedGroupSurfaces:['saber']},
    {...base,targetWord:'estar',displaySurface:'estar',citationForm:'estar',mergedGroupSurfaces:['estar','estamos']}];
   window.showTestCard=index=>{isFlipped=false;currentIndex=index;currentMeaningIndex=0;currentMWEIndex=0;currentExampleIndex=0;currentGroupSelection=null;document.getElementById('flashcard').classList.remove('flipped');window.updateCard({announceHeadword:true});};
  },{config,rows});
  for(const theme of ['dark','light']) {
   await page.evaluate(theme=>{document.documentElement.dataset.theme=theme;showTestCard(0);},theme);
   const trigger=page.locator('.merged-forms-trigger');
   await trigger.waitFor({state:'visible'});
   await page.waitForTimeout(150);
   assert.equal(await page.locator('#frontWord').innerText(),'sabe');
   assert.equal(await trigger.innerText(),'+5 other forms');
   assert.equal(await page.locator('#frontPOS').innerText().then(s=>s.includes('saber')),true);
   assert.equal(await page.locator('#frontMergedForms').evaluate(el=>!!el.closest('#flipBtn')),false);
   const geometry=await page.evaluate(()=>{
    const w=frontWord.getBoundingClientRect(),c=frontMergedForms.getBoundingClientRect(),r=frontRanking.getBoundingClientRect();
    return {below:c.top>=w.bottom,aboveStats:c.bottom<r.top,center:Math.abs((c.left+c.right)/2-(w.left+w.right)/2)<2};
   });
   assert(geometry.below&&geometry.aboveStats&&geometry.center,JSON.stringify({width,geometry}));
   await trigger.focus();
   await page.keyboard.press('Enter');
   await page.locator('#mergedFormsTooltip').waitFor({state:'visible'});
   assert.equal(await page.locator('#mergedFormsHeading').innerText(),'Merged by Smart Skip');
   assert.equal(await page.locator('.merged-forms-list span').count(),6);
   assert.equal(await page.locator('#flashcard').evaluate(el=>el.classList.contains('flipped')),false,'disclosure must not flip card');
   const panel=await page.locator('#mergedFormsTooltip').evaluate(el=>{
    const r=el.getBoundingClientRect(),p=el.closest('.card-front').getBoundingClientRect();
    return {inside:r.left>=p.left&&r.right<=p.right&&r.top>=p.top&&r.bottom<=p.bottom,align:getComputedStyle(el).textAlign};
   });
   assert(panel.inside,JSON.stringify({width,panel}));assert.equal(panel.align,'center');
   await mkdir('/tmp/merged-forms-ui',{recursive:true});
   await page.screenshot({path:`/tmp/merged-forms-ui/${width}-${theme}.png`});
   await page.keyboard.press('Escape');
   assert(await page.locator('#mergedFormsTooltip').isHidden());
   assert.equal(await trigger.getAttribute('aria-expanded'),'false');
   await page.evaluate(()=>showTestCard(1));
   assert(await page.locator('#frontMergedForms').isHidden(),'singleton has no cue');
   await page.evaluate(()=>showTestCard(2));
   assert.equal(await trigger.innerText(),'+1 other form');
   await page.evaluate(()=>{isFlipped=true;window.updateCard();});
   assert(await page.locator('#frontMergedForms').isHidden(),'English prompt has no target-form cue');
  }
  await page.close();
 }
 console.log('Merged forms: title, count, singular, membership, centering, no flip, keyboard dismissal, singleton and reverse direction verified at 320/390/1440px in both themes.');
} finally {await browser?.close();server.close();}
