// Exercise sign-in and repeated logout/login with deliberately delayed widget
// markup and provider styles. Set FLUENCY_TEST_URL to a local or staged app.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const os = require('node:os');
const {chromium} = require('playwright');
const base = process.env.FLUENCY_TEST_URL || 'http://127.0.0.1:8877/';
const output = process.env.FLUENCY_REVIEW_DIR || fs.mkdtempSync(path.join(os.tmpdir(),'fluency-auth-layout-'));
const pause = ms => new Promise(resolve => setTimeout(resolve,ms));
const getBoxes = page => page.evaluate(() => Object.fromEntries(['.auth-welcome-copy','#guestModeRow','#passwordlessMoreOptions','#passwordlessAccountSwitch']
    .map(selector=>[selector,document.querySelector(selector).getBoundingClientRect().toJSON()])));
(async()=>{
    const browser = await chromium.launch({headless:true,...(process.env.CHROME_PATH ? {executablePath:process.env.CHROME_PATH}:{})});
    try {
        for (const [name,width,height] of [['mobile',390,844],['desktop',1440,1000]]) {
            const context = await browser.newContext({viewport:{width,height},serviceWorkers:'block'});
            const page = await context.newPage();
            const errors = [];page.on('pageerror',error=>errors.push(error.message));
            const cdp = await context.newCDPSession(page);
            await cdp.send('Emulation.setCPUThrottlingRate',{rate:4});
            await page.route('**/*',async route=>{
                const url=route.request().url();
                if (/fonts\.(googleapis|gstatic)/.test(url)) return route.abort();
                if (url.includes('clerk.accounts.dev')) {
                    await pause(650);
                    if (url.includes('/ui.browser.js')) return route.fulfill({contentType:'text/javascript',body:'window.__internal_ClerkUICtor=function(){};'});
                    return route.fulfill({contentType:'text/javascript',body:`
                        window.Clerk={user:null,session:null,load:async()=>{},
                            addListener(fn){this.listener=fn;fn(this)},
                            mountSignIn(container){
                                setTimeout(()=>{
                                    container.classList.add('cl-rootBox');
                                    container.innerHTML='<div class="cl-cardBox"><div class="cl-card"><div class="cl-header">Unstyled provider heading</div><button type="button" class="cl-socialButtonsBlockButton__google cl-socialButtonsBlockButton">Sign in with Google</button></div><div class="cl-footer" style="height:44px">Secured by Clerk</div></div>';
                                    const button=container.querySelector('button');
                                    button.onclick=()=>{this.user={id:'layout_test'};this.session={getToken:async()=> 'test-token'};this.listener(this)};
                                    setTimeout(()=>{container.querySelector('.cl-header').style.display='none';button.style.minHeight='48px';},300);
                                },350);
                            },mountSignUp(container){this.mountSignIn(container)},
                            unmountSignIn(){},unmountSignUp(){},
                            signOut:async function(){await new Promise(r=>setTimeout(r,350));this.user=null;this.session=null;this.listener(this)}
                        };
                    `});
                }
                if (/fluency-(?:api|auth-staging)\.rabbijoshy\.workers\.dev/.test(url)) {
                    const body=route.request().postDataJSON();
                    if(body?.action==='account') return route.fulfill({json:{success:true,data:{profile:{id:'clerk_layout_test',name:'Layout test'}}}});
                    if(['load','loadItems','capabilities'].includes(body?.action)) return;
                    return route.fulfill({json:{success:true,data:{}}});
                }
                return route.continue();
            });
            await page.goto(base,{waitUntil:'domcontentloaded'});
            for (let cycle=0;cycle<2;cycle++) {
                await page.locator('#passwordlessLoadingStatus').waitFor();
                const before=await getBoxes(page);
                assert.equal(await page.locator('#passwordlessMoreOptions').isDisabled(),true);
                await page.screenshot({path:path.join(output,`${name}-${cycle}-loading.png`)});
                await page.locator('.cl-header').waitFor({state:'attached'});
                // Provider markup exists but its own styles have not arrived.
                assert.equal(await page.locator('#authModal').getAttribute('data-auth-loading'),'true');
                assert.equal(await page.getByText('Unstyled provider heading',{exact:true}).isVisible(),false);
                await page.locator('.cl-socialButtonsBlockButton__google').waitFor();
                const after=await getBoxes(page);
                for(const selector of Object.keys(before)) {
                    for(const axis of ['x','y','width','height']) assert.ok(Math.abs(before[selector][axis]-after[selector][axis])<1,`${name} ${selector} ${axis} moved on cycle ${cycle}`);
                }
                assert.equal(await page.locator('#passwordlessMoreOptions').isDisabled(),false);
                await page.screenshot({path:path.join(output,`${name}-${cycle}-ready.png`)});
                await page.evaluate(()=>{
                    window.maybeShowKnownLanguagesIntro=()=>false;window.maybeShowFrequencyIntro=()=>false;window.openFirstRunCardTutorial=()=>{};
                    window.transitionFrames=[];
                    const record=()=>{
                        const auth=!document.getElementById('authModal').classList.contains('hidden');
                        const choice=Boolean(document.getElementById('languageChoiceSheet'));
                        transitionFrames.push({auth,choice});
                        if(transitionFrames.length<30)requestAnimationFrame(record);
                    };requestAnimationFrame(record);
                });
                await page.locator('.cl-socialButtonsBlockButton__google').click();
                await page.locator('#languageChoiceSheet').waitFor();
                assert.equal(await page.evaluate(()=>transitionFrames.some(frame=>!frame.auth&&!frame.choice)),false,'Login must not paint bare setup before the language choice');
                // Queue flush and provider sign-out are both asynchronous.
                await page.evaluate(()=>{
                    window.flushQueue=()=>new Promise(resolve=>setTimeout(resolve,300));
                    window.logout();
                });
                await page.locator('#appLoadingScreen').waitFor();
                assert.equal(await page.locator('#appLoadingTitle').innerText(),'Signing out');
                assert.equal(await page.evaluate(()=>Boolean(document.elementFromPoint(innerWidth/2,innerHeight/2)?.closest('#appLoadingScreen'))),true,'Logout cover must sit above existing dialogs');
                await page.waitForFunction(()=>window.authLogoutInFlight===true);
                assert.equal(await page.locator('#authModal').isVisible(),false,'Logout must not flash provider callbacks before the reload');
                await page.waitForURL(base,{waitUntil:'domcontentloaded'});
                // waitForURL can resolve on the old URL; wait for the old document's flag to clear.
                await page.waitForFunction(()=>window.authLogoutInFlight!==true);
            }
            assert.deepEqual(errors,[]);
            console.log(`${name}: stable sign-in geometry, delayed styles and two logout/login cycles passed`);
            await context.close();
        }
    }finally{await browser.close()}
    console.log(`Screenshots: ${output}`);
})().catch(error=>{console.error(error);process.exitCode=1});
