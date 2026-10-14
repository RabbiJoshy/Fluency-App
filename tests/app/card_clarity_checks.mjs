// Exercise real card construction, rendering and controls in both themes.
import assert from 'node:assert/strict';
import { createRequire } from 'node:module';
import { readFile, mkdir } from 'node:fs/promises';
import { createServer } from 'node:http';
import path from 'node:path';
const { chromium } = createRequire(import.meta.url)('playwright');
const root = path.resolve('.');
const config = JSON.parse(await readFile('app/config/config.json', 'utf8'));
const server = createServer(async (req, res) => {
    try {
        const file = path.join(root, req.url.split('?')[0]);
        res.setHeader('Content-Type', ({'.html':'text/html','.css':'text/css','.json':'application/json','.woff2':'font/woff2'})[path.extname(file)] || 'text/javascript');
        res.end(await readFile(file));
    } catch { res.writeHead(404); res.end(); }
});
await new Promise(resolve => server.listen(0,'127.0.0.1',resolve));
let browser;
try {
    browser = await chromium.launch({ headless:true, channel:'chrome' });
    for (const width of [320,390,1000]) for (const theme of ['light','dark']) {
        const page = await browser.newPage({viewport:{width,height:844}});
        await page.route('https://**/*', route => route.abort());
        await page.goto(`http://127.0.0.1:${server.address().port}/app/index.html`);
        await page.waitForFunction(() => typeof window.updateCard === 'function');
        await page.addStyleTag({content:'.modal {display:none !important;} #flashcard, #flashcard * {transition:none !important;animation:none !important;}'});
        await page.evaluate(({config,theme}) => {
            globalThis.config=config; selectedLanguage='spanish'; activeArtist=null;
            currentUser={initials:'TEST'}; itemProgressData={}; progressData={};
            currentIndex=0; currentMeaningIndex=0; currentMWEIndex=0; currentExampleIndex=0; currentGroupSelection=null;
            stats.levelNumber=4;
            document.documentElement.dataset.theme=theme;
            document.getElementById('authModal')?.classList.add('hidden');
            document.getElementById('setupPanel').style.display='none';
            document.getElementById('appContent').classList.remove('hidden');
            for(let el=document.getElementById('flashcard').parentElement;el;el=el.parentElement) {
                el.classList.remove('hidden');
                if(getComputedStyle(el).display==='none') el.style.display='block';
            }
            const meanings=['that','which','what'].map((meaning,i)=>({pos:'PRON',meaning,senseId:`que-${i}`,headword:'que',percentage:[.6,.3,.1][i],targetSentence:'¿Qué quieres?',englishSentence:'What do you want?',allExamples:[]}));
            const card={fullId:'es-que',targetWord:'que',isMultiMeaning:true,partOfSpeech:'PRON',meanings,links:[]};
            const item=window.getCardKnowledgeItems(card)[0];
            itemProgressData[item.itemId]={correct:2,lastCorrect:new Date().toISOString(),lastSeen:new Date().toISOString(),srsStage:3};
            flashcards=[window.buildKnowledgeAwareCard(card)];
            document.getElementById('flashcard').classList.add('flipped');
            window.updateCard({announceHeadword:true});
        },{config,theme});
        const rows=page.locator('#backContent .meaning-row');
        assert.equal(await rows.count(),3);
        assert.match(await page.locator('#frontPracticeBadge').textContent(),/2 meanings to practise · 1 already known/);
        for(const index of [1,2]) {
            await rows.filter({hasText:index===1?'which':'what'}).click();
            assert.equal(await page.evaluate(()=>currentMeaningIndex),index);
        }
        // Identical short glosses must not swallow the unknown senses.
        await page.evaluate(()=>{
            flashcards[0].meanings.forEach(m=>{m.meaning='that';});
            flashcards[0]._grouping=null;window.updateCard();
        });
        assert.equal(await rows.count(),3);
        await rows.nth(2).click();
        assert.equal(await page.evaluate(()=>currentMeaningIndex),2);
        await page.evaluate(()=>{
            const card=flashcards[0];
            delete itemProgressData[window.getCardKnowledgeItems(card)[0].itemId];
            window.updateCard();
        });
        assert.equal(await page.locator('.meaning-row-known, .is-known-meaning').count(),0);
        await page.evaluate(()=>{
            const card={fullId:'es-que-cycle',targetWord:'que',isMultiMeaning:true,partOfSpeech:'PRON',links:[],meanings:[{pos:'SENSE_CYCLE',cycle_pos:'PRON',headword:'que',meaning:'that',allSenses:['that','which','what'].map((translation,i)=>({sense_id:`cycle-${i}`,translation,pos:'PRON'})),allExamples:[]}]};
            const item=window.getCardKnowledgeItems(card)[0];
            itemProgressData[item.itemId]={correct:2,lastCorrect:new Date().toISOString(),lastSeen:new Date().toISOString(),srsStage:3};
            flashcards=[window.buildKnowledgeAwareCard(card)];currentMeaningIndex=0;currentMWEIndex=0;currentGroupSelection=null;
            window.updateCard({announceHeadword:true});
        });
        assert.equal(await page.locator('.sense-cycle-choice').count(),3);
        assert.equal(await page.locator('.sense-cycle-choice.is-known-subsense').count(),1);
        if(process.env.CARD_CLARITY_SCREENSHOT_DIR) {
            await mkdir(process.env.CARD_CLARITY_SCREENSHOT_DIR,{recursive:true});
            await page.screenshot({path:path.join(process.env.CARD_CLARITY_SCREENSHOT_DIR,`que-${theme}-${width}.png`)});
        }
        assert.equal(await page.evaluate(()=>currentMWEIndex),1);
        for(const index of [2,0,1]) {
            await page.locator('.sense-cycle-choice').nth(index).click();
            assert.equal(await page.evaluate(()=>currentMWEIndex),index);
        }
        assert.match(await page.locator('#frontPracticeBadge').textContent(),/2 meanings to practise · 1 already known/);
        await page.evaluate(()=>{
            const card=flashcards[0];
            flashcards=[window.buildKnowledgeAwareCard(card)];
            window.updateCard();
        });
        assert.equal(await page.locator('.sense-cycle-choice').count(),3);
        await page.evaluate(()=>{
            const card=flashcards[0];
            const item=window.getCardKnowledgeItems(card)[0];
            delete itemProgressData[item.itemId]; window.updateCard();
        });
        assert.equal(await page.locator('.meaning-row-known').count(),0);
        await page.evaluate(()=>{
            itemProgressData={};
            const readings=[{headword:'ir',pos:'VERB',share:.63},{headword:'ser',pos:'VERB',share:.27},{headword:'fuera',pos:'ADV',share:.10}];
            const meanings=readings.map((r,i)=>({pos:r.pos,headword:r.headword,meaning:['to go','to be','outside'][i],senseId:`split-${i}`,percentage:1,allExamples:[]}));
            flashcards=readings.map((r,i)=>({fullId:`es-split-${i}`,targetWord:'fuera',citationForm:r.headword,isMultiMeaning:true,meanings:[meanings[i]],splitInfo:{...r,index:i+1,total:3,kind:'homograph',readings},vocabularyRank:20,vocabularySize:1000,sourceFrequency:100,sourceFrequencyUnit:'per_million',links:[],unusedMenuSenses:Array.from({length:12},(_,i)=>({sense_id:`rare-${i}`,pos:r.pos,translation:`rare ${i}`,headword:r.headword}))}));
            currentIndex=0;cardNavStack=[];currentMeaningIndex=0;currentMWEIndex=0;currentGroupSelection=null;
            document.getElementById('flashcard').classList.remove('flipped');window.updateCard();
        });
        const colours=await page.locator('.split-pill-count').evaluateAll(els=>els.map(el=>getComputedStyle(el).color));
        assert.match(await page.locator('.split-usage-share').textContent(),/63%/);
        await page.locator('.front-lemma-pair').nth(2).focus();
        await page.keyboard.press('Enter');
        assert.equal(await page.evaluate(()=>currentIndex),2);
        assert.deepEqual(await page.locator('.split-pill-count').evaluateAll(els=>els.map(el=>getComputedStyle(el).color)),colours);
        assert.match(await page.locator('.split-usage-share').textContent(),/10%/);
        const styles=await page.evaluate(async ()=>{
            const {renderBack, REPLICA_CARDS}=await import('/app/js/card-replica.js');
            const replica=document.createElement('div');
            replica.innerHTML=renderBack({...REPLICA_CARDS.cielo,rareUses:[{}]},0,0);
            document.body.append(replica);
            const badge=document.querySelector('.ref-tile-count-badge');
            const style=getComputedStyle(badge);
            const fraction=getComputedStyle(document.querySelector('.ref-tile-fraction') || badge);
            const replicaBadge=replica.querySelector('.ref-tile-count-badge');
            const result={border:style.borderWidth,font:style.fontFamily,fraction:fraction.fontFamily,
                replicaBorder:getComputedStyle(replicaBadge).borderWidth,replicaFont:getComputedStyle(replicaBadge).fontFamily,
                level:getComputedStyle(document.querySelector('[data-study-level]')).fontSize,count:badge.textContent};
            replica.remove();return result;
        });
        assert.equal(styles.border,'0px');assert.equal(styles.font,styles.fraction);assert.equal(styles.level,'15px');assert.equal(styles.count,'12');assert.equal(styles.replicaBorder,'0px');assert.equal(styles.replicaFont,styles.fraction);
        if(process.env.CARD_CLARITY_SCREENSHOT_DIR) {
            await mkdir(process.env.CARD_CLARITY_SCREENSHOT_DIR,{recursive:true});
            await page.screenshot({path:path.join(process.env.CARD_CLARITY_SCREENSHOT_DIR,`companion-${theme}-${width}.png`)});
            await page.evaluate(()=>document.getElementById('flashcard').classList.add('flipped'));
            await page.screenshot({path:path.join(process.env.CARD_CLARITY_SCREENSHOT_DIR,`rare-uses-${theme}-${width}.png`)});
        }
        await page.evaluate(()=>{delete flashcards[currentIndex].splitInfo.share;window.updateCard();});
        assert.equal(await page.locator('.split-usage-share').count(),0);
        await page.close();
    }
    console.log('Meaning inventory, cycle selection, companion selection, colours and typography passed in both themes at 320px, 390px and 1000px.');
} finally { await browser?.close(); await new Promise(resolve=>server.close(resolve)); }
