// Browser integration: normal-sized links, real dictionary data, and a
// reference-only expression card that returns to the original study card.
import assert from 'node:assert/strict';
import {createRequire} from 'node:module';
import {readFile, mkdir} from 'node:fs/promises';
import {createServer} from 'node:http';
import path from 'node:path';
const {chromium} = createRequire(import.meta.url)('playwright');
const root = path.resolve('app');
const source = await readFile(path.join(root, 'js/flashcards.js'), 'utf8');
const helpers = source.slice(source.indexOf('function senseCrossReferences('), source.indexOf('/**\n * Condense a sense context'));
const server = createServer(async (request, response) => {
    if (request.url === '/') {
        response.setHeader('Content-Type','text/html');
        return response.end('<html data-theme="dark"><meta name="viewport" content="width=device-width,initial-scale=1"><link rel="stylesheet" href="/css/style.css"><body style="margin:16px"><h1>havia</h1><main id="backContent"></main></body></html>');
    }
    try {
        const file = path.join(root, request.url.split('?')[0]);
        response.setHeader('Content-Type',({'.css':'text/css','.json':'application/json','.woff2':'font/woff2'})[path.extname(file)] || 'text/javascript');
        response.end(await readFile(file));
    } catch { response.writeHead(404); response.end(); }
});
await new Promise(resolve => server.listen(0,'127.0.0.1',resolve));
let browser;
try {
    browser = await chromium.launch({headless:true,channel:'chrome'});
    for (const width of [320,390,1000]) {
        const page = await browser.newPage({viewport:{width,height:844}});
        await page.goto(`http://127.0.0.1:${server.address().port}`);
        await page.evaluate(async helpers => {
            const refs = await import('/js/sense-reference-cards.js');
            const {fitSenseRowText} = await import('/js/card-row-layout.js');
            const cfg = await fetch('/config/config.json').then(r=>r.json());
            window.testCards=[{id:'original',targetWord:'havia'}];
            window.testProgress={original:{seen:true}};
            window._cachedJoinedIndex=[{id:'haver',word:'haver',meanings:[]}];
            window.popupCalls=0;window.popupFoundWord=()=>{window.popupCalls++};
            const escape = text => String(text).replace(/[&<>"']/g, char=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[char]));
            window.referenceHelpers = new Function('isSeeExpressionReference','resolveSeeExpression','showSeeExpressionCard',
                'flashcards','currentIndex','selectedLanguage','config','activeArtist','escapeCardText','foldSurfaceForm',
                helpers+';return {senseCrossReferenceHTML,openSenseCrossReference};')(
                    refs.isSeeExpressionReference,refs.resolveSeeExpression,refs.showSeeExpressionCard,
                    testCards,0,'portuguese',cfg,null,escape,text=>String(text||'').toLowerCase());
            window.openSenseCrossReference=referenceHelpers.openSenseCrossReference;
            const html=referenceHelpers.senseCrossReferenceHTML({meaning:'See haver de.'},'See haver de.',true);
            const root=document.getElementById('backContent');
            root.innerHTML=`<div class="meanings-scroll inline-sense-rows"><div class="meaning-row meaning-row-regular is-current-sense row-text-xl"><div class="meaning-row-body"><span class="meaning-row-gloss" style="font-size:20px">${html}</span></div></div></div>`;
            fitSenseRowText(root);
            window.shortcutCalls=0;document.addEventListener('keydown',()=>window.shortcutCalls++);
        },helpers);
        const size = await page.locator('.sense-cross-reference').evaluate(button=>({
            size:parseFloat(getComputedStyle(button).fontSize),
            parent:parseFloat(getComputedStyle(button.closest('.meaning-row-gloss')).fontSize),
            height:button.getBoundingClientRect().height, width:button.getBoundingClientRect().width,
            label:button.textContent
        }));
        assert.equal(size.size,size.parent);assert.ok(size.size>=16);assert.ok(size.height>=44);assert.ok(size.width>=44);
        assert.equal(size.label,'haver de');
        await page.locator('.sense-cross-reference').click();
        await page.locator('#seeExpressionDialog').waitFor({state:'visible'});
        assert.equal(await page.locator('#seeExpressionTitle').textContent(),'haver de');
        assert.match(await page.locator('#seeExpressionDialog').textContent(),/ought to; shall/);
        assert.equal(await page.evaluate(()=>popupCalls),0,'never falls back to the haver card');
        assert.equal(await page.evaluate(()=>testCards.length),1);
        assert.equal(await page.evaluate(()=>JSON.stringify(testProgress)),JSON.stringify({original:{seen:true}}));
        const layout=await page.locator('#seeExpressionDialog').evaluate(dialog=>({
            width:dialog.getBoundingClientRect().width, overflow:dialog.scrollWidth>dialog.clientWidth+1
        }));
        assert.ok(layout.width<=width);assert.equal(layout.overflow,false);
        await page.keyboard.press('ArrowRight');
        assert.equal(await page.evaluate(()=>shortcutCalls),0,'dialog keys must not move or grade the study card');
        if(width===390){
            await mkdir('docs/audits/see-reference-cards',{recursive:true});
            await page.screenshot({path:'docs/audits/see-reference-cards/mobile.png'});
        }
        await page.keyboard.press('Escape');
        await page.locator('#seeExpressionDialog').waitFor({state:'detached'});
        assert.equal(await page.evaluate(()=>document.activeElement.classList.contains('sense-cross-reference')),true);
        // An unresolvable expression gets an honest empty state, never a word fallback.
        await page.evaluate(()=>openSenseCrossReference(null,'missing expression','see'));
        assert.match(await page.locator('#seeExpressionDialog').textContent(),/not available yet/);
        await page.locator('.see-expression-close').click();
        await page.locator('#seeExpressionDialog').waitFor({state:'detached'});
        // No MWE reference-card entry point is added for non-See relations.
        await page.evaluate(()=>openSenseCrossReference(null,'haver de','after_prepositions'));
        assert.equal(await page.locator('#seeExpressionDialog').count(),0);
        console.log(`${width}px: normal link text, 44px targets, correct MWE card, keyboard return and no progress writes`);
        await page.close();
    }
} finally { await browser?.close(); server.close(); }
