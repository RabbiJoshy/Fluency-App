// Deterministic desktop/mobile UI smoke check using the real shell and estimator.
// FLUENCY_TEST_URL must serve app/. Requires playwright on NODE_PATH.
const {chromium}=require('playwright');
const fs=require('node:fs');
const assert=require('node:assert/strict');
const path=require('node:path');
const base=process.env.FLUENCY_TEST_URL || 'http://127.0.0.1:8879';
(async()=>{
 const browser=await chromium.launch({headless:true,executablePath:process.env.CHROME_PATH});
 try {
  for(const [name,width,height] of [['desktop',1440,1000],['mobile',390,844]]) {
   const page=await browser.newPage({viewport:{width,height},serviceWorkers:'block'});
   await page.route('**/*',route=>{
    const url=new URL(route.request().url());
    if(url.origin!==new URL(base).origin) return route.abort();
    if(url.pathname==='/placement-test.html') {
     const html=fs.readFileSync(path.join(__dirname,'../../app/index.html'),'utf8').replace(/<script\b[^>]*>[\s\S]*?<\/script>/gi,'').replace(/<link[^>]+rel="modulepreload"[^>]*>/g,'');
     return route.fulfill({contentType:'text/html',body:html});
    }
    return route.continue();
   });
   await page.goto(base+'/placement-test.html');
   await page.evaluate(async()=>{
    await import('./js/state.js?v=20260825ak');
    await import('./js/estimation.js?v=20261026extension');
    currentUser={isGuest:true}; selectedLanguage='spanish'; activeArtist=null;
    config={languages:{spanish:{}}}; levelEstimates={};
    document.getElementById('appLoadingScreen')?.remove();
    document.querySelectorAll('.modal').forEach(el=>el.classList.add('hidden'));
    const holder=document.createElement('div'); holder.className='level-selector-buttons'; holder.hidden=true;
    holder.innerHTML=Array.from({length:12},(_,i)=>`<button class="level-btn" data-start-rank="${i*10+1}" data-end-rank="${i*10+11}" data-rank-basis="stable"></button>`).join('');
    document.body.append(holder);
    window.fixtureRows=Array.from({length:120},(_,i)=>({id:String(i+1),word:`word${i+1}`,rank:i+1,stableRank:i+1,meanings:[{pos:'NOUN',translation:`Meaning ${i+1}`}]}));
    window.loadEstimationVocabulary=async()=>fixtureRows;
    window.loadSpeechSourceFrequency=async()=>({values:Object.fromEntries(fixtureRows.map(r=>[r.word,121-r.rank]))});
    window.prepareEstimationCognates=async()=>{};
    window.finishCardMeanings=(_,meanings)=>({meanings});
    window.buildSplitCardPair=()=>null; window.lemmaStudyGroupKey=()=>null;
    window.isCognateKnown=()=>false; window.isGrammarParticleItem=()=>false;
    window.LANG_CODES={spanish:'es'};
    window.saveLevelEstimateToSheet=()=>{};
    window.renderLevelSelector=async()=>{};
    openEstimationModal(); await startEstimation();
   });
   await page.locator('#estimationReveal').waitFor({state:'visible'});
   for(let i=0;i<30;i++) {
    if(await page.locator('#estimationResult').isVisible()) break;
    await page.evaluate(()=>{revealTranslation();handleAnswer(estimationState.currentWord.rank<=70);});
    await page.waitForTimeout(10);
   }
   await page.locator('#estimationResult').waitFor({state:'visible'});
   assert.ok(await page.locator('#estimationPlacementOptions button').count());
   // Force the uncertain boundary so both viewport runs exercise the opt-in UI.
   await page.evaluate(()=>{
    estimationState.wordsTestedCount=30;
    estimationState.placementHistory=[];
    showEstimationResult();
   });
   await page.getByRole('button',{name:'Answer a few more questions',exact:true}).waitFor({state:'visible'});
   await page.screenshot({path:`/tmp/placement-${name}-extension-offer.png`});
   const previousAnswers=await page.evaluate(()=>estimationState.answers.length);
   await page.getByRole('button',{name:'Answer a few more questions',exact:true}).click();
   assert.equal(await page.evaluate(()=>estimationState.answers.length),previousAnswers);
   assert.equal(await page.locator('#estimationCount').textContent(),'30/45');
   for(let i=0;i<15;i++) {
    if(await page.locator('#estimationResult').isVisible()) break;
    await page.evaluate(()=>{revealTranslation();handleAnswer(estimationState.currentWord.rank<=70);});
    await page.waitForTimeout(10);
   }
   await page.locator('#estimationResult').waitFor({state:'visible'});
   assert.equal(await page.locator('#estimationExtensionOffer').isVisible(),false);
   await page.screenshot({path:`/tmp/placement-${name}-initial.png`});
   await page.evaluate(async()=>{
    await useEstimatedLevel(0);
    const key='fluency-placement-v1:guest:spanish';
    const session=JSON.parse(localStorage.getItem(key));
    // Deterministic first-set fixture for a sufficiently broad eligible sample.
    session.choice={...session.choice,startRank:61,sourceRank:60,rankBasis:'stable',levelNumber:7};
    session.answers=[]; levelEstimates.spanish=60;localStorage.setItem(key,JSON.stringify(session));
    const cards=fixtureRows.slice(60,80).map(r=>({...r,fullId:`es0${r.id}`,targetWord:r.word}));
    const context={studyMode:'new',rangeString:'61-81',rangeBasis:'stable'};
    beginPlacementStudySet(cards,context);
    cards.forEach(c=>recordPlacementStudyAnswer(c,false,{recognition:true}));
    completePlacementStudySet(context);
    document.getElementById('deckCompleteModal').classList.remove('hidden');
    window.hideDeckCompleteModal=()=>document.getElementById('deckCompleteModal').classList.add('hidden');
   });
   await page.locator('#placementRecheckOffer').waitFor({state:'visible'});
   await page.screenshot({path:`/tmp/placement-${name}-offer.png`});
   await page.getByRole('button',{name:'Recheck starting point',exact:true}).click();
   await page.locator('#estimationReveal').waitFor({state:'visible'});
   for(let i=0;i<15;i++) {
    if(await page.locator('#estimationResult').isVisible()) break;
    const rank=await page.evaluate(()=>estimationState.currentWord.rank);
    assert.ok(rank<61);
    await page.evaluate(()=>{revealTranslation();handleAnswer(false);});
    await page.waitForTimeout(10);
   }
   await page.locator('#estimationKeepPosition').waitFor({state:'visible'});
   assert.equal(await page.evaluate(()=>levelEstimates.spanish),60);
   await page.screenshot({path:`/tmp/placement-${name}-recheck.png`});
   await page.getByRole('button',{name:'Keep my current position',exact:true}).click();
   assert.equal(await page.evaluate(()=>levelEstimates.spanish),60);
   console.log(`${name}: initial estimate, first-set offer, earlier-only recheck and keep-position flow passed`);
   await page.close();
  }
 } finally {await browser.close();}
})();
