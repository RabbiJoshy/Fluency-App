// Run with Playwright available to Node (NODE_PATH may point to its runtime).
import assert from 'node:assert/strict';
import { createRequire } from 'node:module';
import { readFile } from 'node:fs/promises';
import { createServer } from 'node:http';
import path from 'node:path';
const { chromium } = createRequire(import.meta.url)('playwright');
const root = path.resolve('.');
const cards = await readFile('app/js/flashcards.js', 'utf8');
const noteHelpers = cards.slice(cards.indexOf('function shownTextPieces('), cards.indexOf('// Only the active sense'));
const server = createServer(async (request, response) => {
    if (request.url === '/') {
        response.setHeader('Content-Type', 'text/html');
        return response.end('<link rel="stylesheet" href="/app/css/style.css"><main id="backContent"></main>');
    }
    try {
        const file = path.join(root, request.url.split('?')[0]);
        response.setHeader('Content-Type', ({'.css':'text/css','.html':'text/html','.json':'application/json','.woff2':'font/woff2'})[path.extname(file)] || 'text/javascript');
        response.end(await readFile(file));
    } catch { response.writeHead(404); response.end(); }
});
await new Promise(resolve => server.listen(0, '127.0.0.1', resolve));
let browser;
try {
    browser = await chromium.launch({ headless: true, channel: 'chrome' });
    for (const width of [320, 390, 1000]) {
        const page = await browser.newPage({ viewport: { width, height: 844 } });
        await page.goto(`http://127.0.0.1:${server.address().port}`);
        const result = await page.evaluate(async helpers => {
            const { fitSenseRowText } = await import('/app/js/card-row-layout.js');
            const ui = await import('/app/js/card-metadata-pills.js');
            const root = document.getElementById('backContent');
            root.style.cssText = 'width:100%;display:block;';
            const render = (text, compact = false) => {
                root.innerHTML = `<div class="meanings-scroll${compact ? ' has-compact-rows' : ''}"><div class="meaning-row meaning-row-regular row-text-xl"><div class="meaning-row-body"><span class="meaning-row-translation meaning-row-gloss row-adaptive-text">${text}</span></div></div></div>`;
                return root.querySelector('.meaning-row-gloss');
            };
            // The reported near miss: shrink half a pixel to keep 'remember' whole.
            const near = render('to remember');
            const range = document.createRange(); range.selectNodeContents(near);
            const natural = range.getBoundingClientRect().width;
            near.style.setProperty('width', `${natural - 1}px`, 'important');
            fitSenseRowText(root);
            const nearSize = parseFloat(getComputedStyle(near).fontSize);
            range.selectNodeContents(near);
            const nearTextLines = new Set([...range.getClientRects()].map(rect => rect.top)).size;
            const wrap = render('to remember something important');
            wrap.style.setProperty('width', '75px', 'important');
            fitSenseRowText(root);
            const stacked = wrap.closest('.meaning-row').classList.contains('sense-row-needs-stack');
            const wordRange = document.createRange();
            wordRange.setStart(wrap.firstChild, 3); wordRange.setEnd(wrap.firstChild, 11);
            const wordLines = new Set([...wordRange.getClientRects()].map(rect => rect.top)).size;
            const compact = render('to remember something important forever', true);
            root.style.width = '220px';
            fitSenseRowText(root);
            const shortened = compact.textContent;
            const fullTitle = compact.title;
            root.style.width = '950px';
            fitSenseRowText(root);
            const restored = compact.textContent;
            // A base form and an already visible context add no information.
            const meaning = { translation: 'to remember', context: 'a fact', pos: 'verb' };
            const present = ui.learnerSensePresentation(meaning, true, {ignoreBudget:true,gloss:'remember',cardMeanings:[meaning]});
            const repeated = ui.senseNoteHTML(present);
            // DOM filtering also handles repeated fragments and empty sections.
            const functions = new Function('senseNoteTextKey', 'glossBaseStems', `${helpers}; return {placeRowInformationButtons, dropNoteLinesShownIn, fitRowInformationButtons};`)(ui.senseNoteTextKey, ui.glossBaseStems);
            root.innerHTML = `<div class="meaning-row"><span>remember</span><span>a fact</span><button class="sense-note-trigger"></button><template><div class="sense-note-copy" data-sense-note-base-gloss="to remember"><section><h3>Dictionary</h3><p>to remember</p><p>a fact</p></section></div></template></div>`;
            functions.placeRowInformationButtons(root);
            const emptyButtons = root.querySelectorAll('.sense-note-trigger').length;
            root.innerHTML = `<div class="meaning-row"><span>remember</span><button class="sense-note-trigger"></button><template><div class="sense-note-copy" data-sense-note-base-gloss="to remember"><section><p>to remember</p><p>Often used when recalling childhood events</p></section></div></template></div>`;
            functions.placeRowInformationButtons(root);
            const usefulButtons = root.querySelectorAll('.sense-note-trigger').length;
            const usefulNote = root.querySelector('template').content.textContent;
            root.innerHTML = `<div class="meaning-row"><span>remembers</span><span>known from context/shared knowledge</span><button class="sense-note-trigger"></button><template><div class="sense-note-copy" data-sense-note-base-gloss="to remember"><section><p>to remember</p><p>it is presumed to be definitely known in context or from shared knowledge</p></section></div></template></div>`;
            functions.placeRowInformationButtons(root);
            const shortenedDuplicateButtons = root.querySelectorAll('.sense-note-trigger').length;
            root.innerHTML = `<div class="meaning-row"><span>remembers</span><span>+ gerund</span><button class="sense-note-trigger"></button><template><div class="sense-note-copy" data-sense-note-base-gloss="to remember"><section><p>[with gerund (only after estar)]</p></section></div></template></div>`;
            functions.placeRowInformationButtons(root);
            const qualifiedRawNote = root.querySelector('template').content.textContent;
            const detailed = {translation:'bank (a financial institution serving local people and businesses)',pos:'noun'};
            const detailNote = ui.senseNoteHTML(ui.learnerSensePresentation(detailed,true,{ignoreBudget:true,cardMeanings:[detailed]}));
            root.style.width = '100%';
            const note = text => `<button class="sense-note-trigger"><span>i</span></button><template class="sense-note-template"><div class="sense-note-copy" data-sense-note-title="remember"><section><p>${text}</p></section></div></template>`;
            root.innerHTML = `<div class="meaning-row meaning-row-regular row-text-xl" style="position:relative"><div class="meaning-row-body"><span class="meaning-row-gloss">remember</span><span class="meaning-row-sub sense-cue-area">a fact ${note('Often used when recalling childhood events')}</span></div><div class="pct-column">●</div></div>
            <div class="meaning-row meaning-row-group row-text-xl" style="position:relative"><div class="meaning-row-body group-card-body is-stacked"><div class="group-card-shared">remember ${note('Useful general advice for recalling childhood events')}</div><div class="sense-cue-area sense-cue-group"><div class="group-card-varying-cell">a fact ${note('Specific advice about historical facts')}</div><div class="group-card-varying-cell">a person ${note('Specific advice about people you met')}</div><div class="group-card-varying-cell">an event ${note('Specific advice about past celebrations')}</div></div></div><div class="pct-column">●</div></div>`;
            functions.placeRowInformationButtons(root);
            functions.fitRowInformationButtons(root);
            const positions = [...root.querySelectorAll('.sense-note-trigger')].map(button => {
                const rect = button.getBoundingClientRect();
                const row = button.closest('.meaning-row');
                const slot = button.closest('.sense-cell-information');
                const cell = slot?._senseContextCell;
                const cellRect = cell?.getBoundingClientRect();
                return {rightGap:row.getBoundingClientRect().right-rect.right,
                    direct:button.parentElement===row || Boolean(slot),
                    aligned:!cell || Math.abs((rect.top+rect.bottom-cellRect.top-cellRect.bottom)/2)<1};
            });
            const sharedButton = root.querySelector('.meaning-row-group > .sense-note-trigger');
            ui.openSenseNote({preventDefault(){},stopPropagation(){}}, sharedButton);
            const sharedScope = document.querySelector('.sense-note-eyebrow').textContent;
            document.querySelector('.sense-note-close').click();
            const childButton = root.querySelector('.sense-cell-information > .sense-note-trigger');
            ui.openSenseNote({preventDefault(){},stopPropagation(){}}, childButton);
            const childNote = document.querySelector('.sense-note-body').textContent;
            document.querySelector('.sense-note-close').click();
            const cell = childButton.parentElement._senseContextCell;
            cell.style.display = 'none';
            functions.fitRowInformationButtons(root);
            const hiddenWithCell = childButton.parentElement.hidden;
            cell.style.display = '';
            functions.fitRowInformationButtons(root);
            const restoredWithCell = !childButton.parentElement.hidden;
            const commonnessLeft = [...root.querySelectorAll('.pct-column')].every(element => element.getBoundingClientRect().left-element.closest('.meaning-row').getBoundingClientRect().left<10);
            return {nearSize, nearTextLines, stacked, wordLines, shortened, fullTitle, restored, repeated, emptyButtons, usefulButtons, usefulNote, shortenedDuplicateButtons, qualifiedRawNote, detailNote, positions, sharedScope, childNote, hiddenWithCell, restoredWithCell, commonnessLeft};
        }, noteHelpers);
        assert.equal(result.nearSize, 21.5);
        assert.equal(result.nearTextLines, 1);
        assert.equal(result.stacked, true);
        assert.equal(result.wordLines, 1);
        assert.match(result.shortened, /…$/u);
        assert(['to…', 'to remember…', 'to remember something…', 'to remember something important…'].includes(result.shortened));
        assert.equal(result.fullTitle, 'to remember something important forever');
        assert.equal(result.restored, result.fullTitle);
        assert.equal(result.repeated, '');
        assert.equal(result.emptyButtons, 0);
        assert.equal(result.usefulButtons, 1);
        assert.match(result.usefulNote, /childhood events/);
        assert.equal(result.shortenedDuplicateButtons,0);
        assert.equal(result.qualifiedRawNote,'[with gerund (only after estar)]');
        assert.match(result.detailNote, /financial institution/);
        assert.equal(result.positions.length,5);
        for (const position of result.positions) {
            assert(Math.abs(position.rightGap-6)<1, JSON.stringify(position));
            assert(position.direct);
            assert(position.aligned);
        }
        assert.match(result.sharedScope,/All contexts/);
        assert.match(result.childNote,/historical facts/);
        assert(!result.childNote.includes('people you met'));
        assert(result.hiddenWithCell && result.restoredWithCell);
        assert(result.commonnessLeft);
        if (process.env.CARD_ROW_SCREENSHOT_DIR) await page.screenshot({path:path.join(process.env.CARD_ROW_SCREENSHOT_DIR, `flashcard-info-right-${width}.png`)});
        await page.close();
    }
    const fixture = JSON.parse(await readFile('tests/app/fixtures/spanish_shared_context.json','utf8'));
    const appConfig = JSON.parse(await readFile('app/config/config.json','utf8'));
    for (const width of [320,390,1000]) {
        const page = await browser.newPage({viewport:{width,height:844}});
        await page.route('https://**/*',route=>route.abort());
        await page.goto(`http://127.0.0.1:${server.address().port}/app/index.html`);
        await page.waitForFunction(()=>typeof window.updateCard==='function');
        await page.addStyleTag({content:'#flashcard, #flashcard * { transition:none !important; animation:none !important; }'});
        await page.evaluate(({fixture,appConfig})=>{
            config=appConfig; selectedLanguage='spanish'; activeArtist=null;
            currentIndex=0; currentMeaningIndex=0; currentExampleIndex=0; currentGroupSelection=null;
            const meanings=fixture.meanings.map(m=>({...m,meaning:m.translation,senseId:m.sense_id,
                percentage:Number(m.frequency),canonicalExample:m.canonical_example,
                targetSentence:m.canonical_example.text,englishSentence:m.canonical_example.translation,
                allExamples:[{target:m.canonical_example.text,english:m.canonical_example.translation,canonical:true}]}));
            flashcards=[{id:fixture.id,fullId:`es:${fixture.id}`,targetWord:fixture.word,word:fixture.word,
                lemma:fixture.word,language:'spanish',partOfSpeech:'ADV',isMultiMeaning:true,meanings,
                targetSentence:meanings[0].targetSentence,englishSentence:meanings[0].englishSentence,links:[]}];
            document.getElementById('authModal')?.classList.add('hidden');
            document.getElementById('setupPanel').style.display='none';
            document.getElementById('appContent').classList.remove('hidden');
            for(let element=document.getElementById('flashcard').parentElement;element;element=element.parentElement) {
                element.classList.remove('hidden');
                if(getComputedStyle(element).display==='none') element.style.display='block';
            }
            document.getElementById('flashcard').classList.add('flipped');
            window.updateCard();
        },{fixture,appConfig});
        const cells=page.locator('#backContent .meaning-row-group[data-axis="context"] .group-card-varying-cell');
        assert.equal(await cells.count(),2);
        const positions=await cells.evaluateAll(elements=>elements.map(element=>({text:element.textContent,top:element.getBoundingClientRect().top,bottom:element.getBoundingClientRect().bottom})));
        assert.match(positions[0].text,/still/);
        assert.match(positions[1].text,/yet/);
        assert(positions[0].bottom>positions[0].top);
        assert(positions[1].top>=positions[0].bottom,JSON.stringify(positions));
        await cells.nth(0).click();
        assert.equal(await page.evaluate(()=>currentMeaningIndex),0);
        assert.match(await page.evaluate(()=>window._currentDisplayedExample.english),/still at work/);
        await cells.nth(1).click();
        assert.equal(await page.evaluate(()=>currentMeaningIndex),1);
        assert.match(await page.evaluate(()=>window._currentDisplayedExample.english),/order yet/);
        assert.equal(await page.evaluate(()=>flashcards[0].meanings.length),3);
        if(process.env.CARD_ROW_SCREENSHOT_DIR) await page.locator('#flashcard').screenshot({path:path.join(process.env.CARD_ROW_SCREENSHOT_DIR,`aun-shared-context-${width}.png`)});
        // A card containing only this pair still exposes two selectable rows.
        await page.evaluate(()=>{
            flashcards[0].meanings=flashcards[0].meanings.slice(0,2);
            delete flashcards[0]._grouping;
            window.updateCard();
        });
        assert.equal(await cells.count(),2);
        const pair=await cells.evaluateAll(elements=>elements.map(element=>element.getBoundingClientRect().top));
        assert(pair[1]>pair[0]);
        await page.close();
    }
    console.log('Sense row fitting, useful notes and aún selection passed at 320px, 390px and 1000px.');
} finally {
    await browser?.close();
    await new Promise(resolve => server.close(resolve));
}
