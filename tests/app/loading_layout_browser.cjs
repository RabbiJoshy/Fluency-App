// Run against a local app-root server: FLUENCY_TEST_URL=http://127.0.0.1:8876
// node tests/app/loading_layout_browser.cjs (requires Playwright on NODE_PATH).
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const os = require('node:os');
const { chromium } = require('playwright');
const base = process.env.FLUENCY_TEST_URL || 'http://127.0.0.1:8876';
const out = process.env.FLUENCY_REVIEW_DIR || fs.mkdtempSync(path.join(os.tmpdir(), 'fluency-loading-'));
// Resolve the real import graph locally, or the shared build stamp on a
// deployed preview, so tests never instantiate a second copy of an app module.
const appRoot = path.join(__dirname, '../../app');
const mainSource = fs.readFileSync(path.join(appRoot, 'js/main.js'), 'utf8');
const versions = Object.fromEntries([...mainSource.matchAll(/['"]\.\/([\w-]+)\.js\?v=([^'"]+)['"]/g)].map(match => [match[1],match[2]]));
versions['flashcards-conj'] = fs.readFileSync(path.join(appRoot, 'js/flashcards.js'), 'utf8').match(/const ASSET_VERSION = '([^']+)'/)[1];
const rawMainVersion = fs.readFileSync(path.join(appRoot, 'index.html'), 'utf8').match(/script[^>]+src="js\/main\.js\?v=([^"]+)"/)[1];
const pause = ms => new Promise(resolve => setTimeout(resolve, ms));
(async () => {
    const browser = await chromium.launch({ headless: true,
        ...(process.env.CHROME_PATH ? { executablePath: process.env.CHROME_PATH } : {}) });
    try {
        for (const [name, width, height] of [['desktop', 1440, 1000], ['mobile', 390, 844]]) {
            const context = await browser.newContext({ viewport: { width, height }, serviceWorkers: 'block' });
            const page = await context.newPage();
            const errors = [];
            page.on('pageerror', error => errors.push(error.message));
            const cdp = await context.newCDPSession(page);
            await cdp.send('Emulation.setCPUThrottlingRate', { rate: 4 });
            await page.addInitScript(({ versions, rawMainVersion }) => {
                window.importAppModuleForTest = name => {
                    const script = document.querySelector('script[src*="js/main.js"]');
                    const stamp = new URL(script.src).searchParams.get('v');
                    const version = stamp !== rawMainVersion ? stamp : versions[name];
                    return import(new URL(`js/${name}.js?v=${version}`, location.href).href);
                };
            }, { versions, rawMainVersion });
            await page.addInitScript(() => {
                localStorage.setItem('fluencyCardWalkthroughSeenV1', '1');
                localStorage.setItem('fluencySeenFrequencyIntroV2', '1');
                const profile = JSON.stringify({ languages: ['en'], labels: {}, confirmed: true });
                localStorage.setItem('fluency_language_profile_v1|guest', profile);
                localStorage.setItem('fluency_language_profile_v1|clerk_loading_test', profile);
            });
            let accountFailures = 1;
            await page.route('**/*', async route => {
                const url = route.request().url();
                if (url.includes('clerk.accounts.dev')) {
                    if (url.includes('/ui.browser.js')) return route.fulfill({ contentType: 'text/javascript', body: 'window.__internal_ClerkUICtor = function(){};' });
                    return route.fulfill({ contentType: 'text/javascript', body: `
                        const session = {id:'test_session',getToken:async()=> 'local-test-token'};
                        window.Clerk = {
                            user: localStorage.getItem('flashcardUser') ? {id:'loading_test'} : null,
                            session: localStorage.getItem('flashcardUser') ? session : null,
                            load: async()=>{}, addListener(fn){this.listener=fn; fn(this);},
                            mountSignIn(container){ const b=document.createElement('button'); b.textContent='Test sign-in';
                                b.onclick=()=>{this.user={id:'loading_test'};this.session=session;this.listener(this);this.listener(this);};
                                container.replaceChildren(b); },
                            mountSignUp(container){this.mountSignIn(container)},
                            unmountSignIn(){}, unmountSignUp(){}, signOut:async()=>{}
                        };` });
                }
                if (url.includes('fluency-api.rabbijoshy.workers.dev')) {
                    const body = route.request().postDataJSON();
                    if (body?.action === 'account' && accountFailures-- > 0) return route.fulfill({status:503,json:{success:false,message:'Account temporarily unavailable'}});
                    if (body?.action === 'account') return route.fulfill({json:{success:true,data:{profile:{id:'clerk_loading_test',name:'Loading test'}}}});
                    // Remote progress never finishes; sign-in must still complete.
                    if (['load','loadItems','capabilities'].includes(body?.action)) return;
                    return route.fulfill({json:{success:true,data:{}}});
                }
                if (url.endsWith('/albums-for-loading-test.json')) {
                    await pause(1000); return route.fulfill({json:{'Test album':['One']}});
                }
                if (/fonts\.(googleapis|gstatic)/.test(url)) return route.abort();
                if (route.request().resourceType() === 'image') await pause(800);
                if (/\/js\/|\/css\//.test(url)) await pause(25);
                return route.continue();
            });
            await page.goto(base, { waitUntil: 'domcontentloaded' });
            await page.getByRole('button', { name: 'Test sign-in', exact: true }).waitFor({ timeout: 30000 });
            await page.evaluate(() => {
                localStorage.setItem('fluencyPreferredLanguageV1', 'spanish');
                window.maybeShowKnownLanguagesIntro = () => false;
                window.maybeShowFrequencyIntro = () => false;
                window.openFirstRunCardTutorial = () => {};
            });
            await page.getByRole('button', { name: 'Test sign-in', exact: true }).click();
            await page.getByRole('button', { name: 'Retry sign-in', exact: true }).click();
            await page.waitForFunction(() => document.getElementById('authModal').classList.contains('hidden'));
            assert.equal(await page.evaluate(() => JSON.parse(localStorage.getItem('flashcardUser')).initials), 'clerk_loading_test');
            console.log(`${name}: fresh login completes with hung progress and duplicate provider events`);

            await pause(300);
            await page.evaluate(() => window.closeChoiceSheet?.('languageChoiceSheet', true));

            // Exercise real search UI with a slow index, a user typing while it
            // loads, then a failed read and a successful in-place retry.
            await page.evaluate(() => {
                window.fetchAndJoinIndex = () => new Promise(resolve => { window.releaseSearch = resolve; });
                window.openFindWord();
            });
            await page.locator('#findWordResults[aria-busy="true"]').waitFor();
            await page.locator('#findWordInput').fill('hola');
            await pause(250); // Let the intentional dialog entrance animation finish.
            const searchBefore = await page.locator('#findWordInput').boundingBox();
            await page.screenshot({ path: path.join(out, `${name}-search-loading.png`) });
            await page.evaluate(() => releaseSearch([{ id: 'hola', word: 'hola', rank: 1, meanings: [{translation:'hello'}] }]));
            await page.locator('.find-word-result').first().waitFor();
            const searchAfter = await page.locator('#findWordInput').boundingBox();
            assert.ok(Math.abs(searchAfter.y - searchBefore.y) < 2, `Search input shifted from ${searchBefore.y} to ${searchAfter.y}`);
            assert.equal(await page.locator('#findWordInput').inputValue(), 'hola');
            await page.evaluate(() => window.closeFindWord());

            await page.evaluate(() => {
                useLemmaMode = !useLemmaMode;
                window.fetchAndJoinIndex = async () => { throw new Error('Test connection failed'); };
                window.openFindWord();
            });
            await page.locator('#findWordResults .region-retry').waitFor();
            await page.evaluate(() => { window.fetchAndJoinIndex = async () => [{id:'hola',word:'hola',rank:1,meanings:[{translation:'hello'}]}]; });
            await page.locator('#findWordResults .region-retry').click();
            await page.waitForFunction(() => document.getElementById('findWordStatus').textContent.includes('words loaded'));
            await page.evaluate(() => { useLemmaMode = false; window.closeFindWord(); });

            // Test progress modal skeletons with real DOM and actual styling.
            await page.evaluate(async () => {
                const { openProgressOverview } = await window.importAppModuleForTest('progress-overview');
                window.openProgressOverviewForTest = openProgressOverview;
                openProgressOverview({ isCurrent: () => true, getId: c => c.id, getState: () => ({}),
                    getProgress: () => ({}), coverageLabel: 'Speech coverage',
                    loadVocabulary: () => new Promise(resolve => { window.releaseProgress = resolve; }) });
            });
            await page.locator('#progressOverviewContent[aria-busy="true"]').waitFor();
            const progressBefore = await page.locator('#closeTotalStatsModal').boundingBox();
            assert.equal(await page.locator('#progressOverviewContent .progress-coverage-card').isVisible(), false, 'Unloaded zero counts must be hidden');
            await page.screenshot({ path: path.join(out, `${name}-progress-loading.png`) });
            await page.evaluate(() => releaseProgress([{id:'word',corpus_count:10}]));
            await page.waitForFunction(() => !document.getElementById('progressOverviewContent').hasAttribute('aria-busy'));
            const progressAfter = await page.locator('#closeTotalStatsModal').boundingBox();
            assert.ok(Math.abs(progressBefore.y - progressAfter.y) < 2, `Progress close button shifted ${progressAfter.y-progressBefore.y}px`);
            await page.locator('#closeTotalStatsModal').click();

            // Render actual setup controls against a delayed vocabulary fixture.
            await page.evaluate(() => {
                window.enterGuestMode();
                window.closeChoiceSheet?.('languageChoiceSheet', true);
                const cards = Array.from({length:240}, (_, i) => ({
                    id:String(i + 1),word:`casa${String.fromCharCode(97+Math.floor(i/26))}${String.fromCharCode(97+i%26)}`,
                    rank:i+1,corpus_count:240-i,lemma:`casa${i}`,meanings:[{translation:'house',pos:'NOUN',headword:`casa${i}`}]
                }));
                window.setupCards = cards;
                const pending = new Promise(resolve => { window.releaseSetup = () => resolve(cards); });
                window.fetchActiveVocabularyData = () => pending;
                selectedLevel = null; activeArtist = null; useLemmaMode = false; excludeCognates = false;
                delete document.getElementById('setupPanel').dataset.sourceChoice;
                document.getElementById('step2').style.display = 'block';
                document.body.classList.add('has-learning-context');
                document.getElementById('step1').classList.add('source-speech-active');
                window.setupRender = window.renderLevelSelector('spanish', {preferActionable:true});
            });
            await page.locator('#step2 .level-choosing[aria-busy="true"]').waitFor();
            await page.screenshot({path:path.join(out,`${name}-setup-loading.png`)});
            await page.evaluate(async () => { releaseSetup(); await setupRender; });
            await page.locator('#homeLevelStepper').waitFor();
            assert.equal(await page.locator('#step2 .region-load-error').count(),0,'Setup fixture must render successfully');
            await page.screenshot({path:path.join(out,`${name}-setup-loaded.png`)});
            await page.evaluate(() => { window.fetchAndJoinIndex = async () => setupCards; });

            // Leaving a slow Speech transition must not reveal its levels
            // underneath the new language's Speech/Music choice.
            await page.evaluate(() => {
                document.querySelector('.lang-tab[data-lang="portuguese"]').click();
                window.loadReleaseStudyStructure = () => new Promise(resolve => { window.finishOldSpeech = resolve; });
                document.getElementById('standardSourceSpeechBtn').click();
            });
            await page.waitForFunction(() => typeof window.finishOldSpeech === 'function');
            assert.equal(await page.locator('#setupPanel').getAttribute('data-source-choice'), null, 'Selecting Speech releases the source-choice guard');
            await page.evaluate(() => document.querySelector('.lang-tab[data-lang="spanish"]').click());
            assert.equal(await page.locator('#standardSourceCard').isVisible(), true);
            assert.equal(await page.locator('#step2').isVisible(), false);
            await page.evaluate(() => window.finishOldSpeech());
            await pause(250);
            assert.equal(await page.locator('#step1').evaluate(el => el.classList.contains('context-ready')), false, 'Old Speech completion must not mark the new source ready');
            // Even a late presentation-only update cannot override source state.
            await page.evaluate(() => {
                for (const id of ['step2','step4','reviewDeckSection','extrasDeckSection']) {
                    const el = document.getElementById(id); el.hidden = false; el.style.display = 'block';
                }
            });
            for (const id of ['step2','step4','reviewDeckSection','extrasDeckSection']) {
                assert.equal(await page.locator(`#${id}`).isVisible(), false, `${id} must stay hidden during source choice`);
            }
            await page.screenshot({path:path.join(out,`${name}-source-choice.png`)});
            console.log(`${name}: source choice hides stale levels after a delayed Speech transition`);

            // Music shell and image slots, independent of production catalogues.
            await page.evaluate(async () => {
                const { openMusicWorkspace } = await window.importAppModuleForTest('music-workspace');
                window.openMusicForTest = openMusicWorkspace;
                openMusicWorkspace({language:'spanish',artists:[],loading:true});
            });
            await page.locator('#musicArtistList[aria-busy="true"]').waitFor();
            const musicBefore = await page.locator('#musicArtistSearch').boundingBox();
            await page.screenshot({ path: path.join(out, `${name}-music-loading.png`) });
            await page.evaluate(() => {
                openMusicForTest({language:'spanish',focus:false,artists:[{slug:'test',name:'Test artist',description:'One album',image:'icons/icon-192.png'}]});
            });
            const musicAfter = await page.locator('#musicArtistSearch').boundingBox();
            assert.ok(Math.abs(musicBefore.y-musicAfter.y) < 2);
            const imageBefore = await page.locator('#musicArtistList .music-artist-image').boundingBox();
            await pause(1200);
            const imageAfter = await page.locator('#musicArtistList .music-artist-image').boundingBox();
            assert.deepEqual(imageAfter, imageBefore, 'Delayed artist images must keep their slot');

            // Album loading must not insert controls or rebuild focused rows.
            await page.evaluate(async () => {
                const { showSongSetPicker } = await window.importAppModuleForTest('song-sets');
                activeArtist = {name:'Test artist',albumsDictionary:'albums-for-loading-test.json'};
                artistSongCatalog = {songs:[{id:'one',title:'One',artist:'Test artist'}]}; selectedSongIds=['one'];
                showSongSetPicker();
            });
            await page.locator('#songSetAlbum[aria-busy="true"]').waitFor();
            await page.locator('#songSetList input').first().focus();
            const songBefore = await page.locator('#songSetList input').first().boundingBox();
            await page.evaluate(() => { window.focusedSong = document.activeElement; });
            await page.waitForFunction(() => !document.getElementById('songSetAlbum').hasAttribute('aria-busy'));
            assert.equal(await page.evaluate(() => document.activeElement === window.focusedSong), true, 'Album metadata must preserve checkbox focus and DOM');
            assert.deepEqual(await page.locator('#songSetList input').first().boundingBox(), songBefore);
            assert.equal(await page.locator('#songSetAlbum').isDisabled(), false);
            await page.screenshot({ path: path.join(out, `${name}-songs.png`) });
            await page.evaluate(() => {
                activeArtist.albumsDictionary = 'albums-unavailable-test.json';
                window.showSongSetPicker();
            });
            await page.waitForFunction(() => !document.getElementById('songSetAlbum').hasAttribute('aria-busy'));
            assert.equal(await page.locator('#songSetAlbum').isVisible(), true);
            assert.equal(await page.locator('#songSetAlbum').isDisabled(), true);
            assert.equal(await page.locator('#songSetAlbum').innerText(), 'Albums unavailable');

            // Study-card conjugations expose a close control even while loading.
            await page.evaluate(async () => {
                window.dismissMusicWorkspace?.();
                const panel = document.createElement('div');
                panel.id = 'conjugationTable'; panel.className = 'conjugation-panel';
                panel.dataset.lemma = 'hablar'; panel.dataset.target = 'hablo';
                document.body.appendChild(panel);
                await window.importAppModuleForTest('flashcards-conj');
                window.loadConjugationData = () => new Promise(resolve => { window.releaseConjugations = resolve; });
                window.conjugationLoad = window.toggleConjugationTable();
            });
            await page.locator('#conjugationTable[aria-busy="true"]').waitFor();
            await page.locator('#conjugationTable .region-loading-cancel').click();
            await page.evaluate(async () => { releaseConjugations(); await conjugationLoad; });
            assert.equal(await page.locator('#conjugationTable').evaluate(panel => panel.classList.contains('visible')), false, 'Cancelled drawer must not reopen after its data arrives');
            await page.evaluate(() => { document.getElementById('conjugationTable').remove(); });

            // Reduced-motion is applied to actual placeholder animations.
            await page.emulateMedia({ reducedMotion: 'reduce' });
            const helper = await page.evaluate(async () => {
                const { beginRegionLoading, boundedLoad } = await window.importAppModuleForTest('loading-ui');
                const region = document.getElementById('songSetList');
                const finishOld = beginRegionLoading(region);
                const finishNew = beginRegionLoading(region);
                finishOld();
                const stillBusy = region.getAttribute('aria-busy') === 'true';
                const motion = getComputedStyle(region.querySelector('.region-loading-line')).animationName;
                finishNew();
                let timeout = false;
                try { await boundedLoad(new Promise(() => {}), 5); } catch (_) { timeout = true; }
                return { stillBusy, motion, timeout, busy:region.hasAttribute('aria-busy'),
                    overflow:document.documentElement.scrollWidth > innerWidth + 1 };
            });
            assert.deepEqual(helper, {stillBusy:true,motion:'none',timeout:true,busy:false,overflow:false});
            assert.deepEqual(errors, [], `${name} browser errors`);
            console.log(`${name}: setup/search/progress/music geometry, song focus, drawer cancellation, failures, reduced motion and overflow passed`);
            await context.close();
        }
    } finally { await browser.close(); }
    console.log(`Screenshots: ${out}`);
})().catch(error => { console.error(error); process.exitCode = 1; });
