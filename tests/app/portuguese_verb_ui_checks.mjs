// Render the reported Portuguese records through the real card UI at phone/desktop widths.
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
  page.on('pageerror',error=>console.error(error.message));
  page.on('console',message=>{if(message.type()==='warning')console.error(message.text());});
  await page.route('https://**/*',route=>route.abort());
  await page.goto(`http://127.0.0.1:${server.address().port}/app/index.html`);
  await page.waitForFunction(()=>typeof window.updateCard==='function');
  await page.addStyleTag({content:'.modal {display:none !important;} #flashcard, #flashcard * {transition:none !important;animation:none !important;}'});
  await page.evaluate(({config,rows})=>{
   globalThis.config=config;selectedLanguage='portuguese';activeArtist=null;
   currentUser={initials:'TEST'};itemProgressData={};progressData={};stats.levelNumber=1;
   window._cachedJoinedIndex=rows;
   document.getElementById('setupPanel').style.display='none';
   document.getElementById('appContent').classList.remove('hidden');
   for(let el=document.getElementById('flashcard').parentElement;el;el=el.parentElement){el.classList.remove('hidden');if(getComputedStyle(el).display==='none')el.style.display='block';}
   flashcards=rows.map(row=>({...row,fullId:`pt-${row.id}`,targetWord:row.word,citationForm:row.word==='tem'?'ter':row.word==='acabou'?'acabar':row.word,displaySurface:row.word,isMultiMeaning:true,partOfSpeech:'verb',links:[],meanings:row.meanings.map(m=>({...m,meaning:m.translation,senseId:m.sense_id,percentage:Number(m.frequency),canonicalExample:m.canonical_example,allExamples:[]}))}));
   window.showTestWord=word=>{currentIndex=flashcards.findIndex(c=>c.targetWord===word);currentMeaningIndex=0;currentMWEIndex=0;currentExampleIndex=0;currentGroupSelection=null;document.getElementById('flashcard').classList.add('flipped');window.updateCard({announceHeadword:true});};
  },{config,rows});
  await page.evaluate(()=>{
   const cards=flashcards.filter(card=>['ter','tem'].includes(card.targetWord));
   for(const card of cards) card.lemmaModeCompanions=cards.map(other=>({id:other.id,surface:other.targetWord}));
   showTestWord('ter');document.getElementById('flashcard').classList.remove('flipped');
  });
  await page.locator('.lemma-companion-cards button').click();
  assert.equal(await page.evaluate(()=>flashcards[currentIndex].targetWord),'tem','companion links navigate to the distinct card');
  for(const word of ['tratar','procurar','começar','ir']) {
   await page.evaluate(word=>showTestWord(word),word);
   await page.locator('.is-frame-pill').first().waitFor();
   const pills=await page.locator('#backContent .is-frame-pill').evaluateAll(els=>els.map(el=>({right:el.getBoundingClientRect().right,rowRight:el.closest('.meaning-row').getBoundingClientRect().right,ancestors:(()=>{let out=[];for(let p=el.parentElement;p && !p.matches('.meaning-row');p=p.parentElement)out.push([p.className,getComputedStyle(p).whiteSpace,getComputedStyle(p).overflow,p.getBoundingClientRect().width]);return out;})(),text:el.textContent,size:parseFloat(getComputedStyle(el).fontSize),width:el.getBoundingClientRect().width,overflow:el.scrollWidth>el.clientWidth+1,bg:getComputedStyle(el).backgroundColor,textOutside:(()=>{const range=document.createRange();range.selectNodeContents(el);const text=range.getBoundingClientRect(),pill=el.getBoundingClientRect();return text.left<pill.left-1||text.right>pill.right+1;})()})));
   assert(pills.length>0,`${word}: has pills`);
   for(const pill of pills){assert(pill.text.startsWith(word),JSON.stringify(pill));assert(pill.size>=19);assert(!pill.overflow,JSON.stringify(pill));assert(pill.width<=width,JSON.stringify(pill));assert(pill.right<=pill.rowRight+1,JSON.stringify(pill));assert(!pill.textOutside,'pill must cover its full phrase: '+JSON.stringify(pill));}
   if(word==='ir')assert(pills.some(pill=>pill.text==='ir para'));
   if(width===320 || width===390){await mkdir('/tmp/portuguese-verb-ui',{recursive:true});await page.screenshot({path:`/tmp/portuguese-verb-ui/${word}.png`});}
  }
  await page.evaluate(()=>showTestWord('acabou'));
  try {await page.waitForFunction(()=>document.getElementById('backContent').textContent.includes('to have just'),{},{timeout:10000});} catch(error){console.error(await page.evaluate(()=>({meanings:flashcards[currentIndex].meanings.map(m=>({text:m.meaning,load:m._seeExpressionLoad,gloss:m._seeExpressionGloss})),text:document.getElementById('backContent').textContent})));throw error;}
  assert.match(await page.locator('#backContent').textContent(),/to have just/);
  await page.locator('#backContent .meaning-row').filter({hasText:'to have just'}).first().click();
  await page.getByRole('button',{name:'acabar de',exact:true}).click();
  await page.locator('#seeExpressionDialog').waitFor({state:'visible'});
  assert.match(await page.locator('#seeExpressionDialog').textContent(),/He has just left/);
  await page.keyboard.press('Escape');
  await page.evaluate(()=>showTestWord('tem'));
  assert(!(await page.locator('#backContent').innerText()).includes('there be'));
  console.log(`${width}px: all four construction cards, optional prepositions, readable full pills, existential English and acabar de definition/navigation verified`);
  await page.close();
 }
} finally {await browser?.close();server.close();}
