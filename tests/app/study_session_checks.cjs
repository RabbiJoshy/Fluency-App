const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const {createHarness} = require('./estimation_harness.cjs');
(async () => {
    const h = createHarness();
    const cards = Array.from({length:65}, (_, i) => ({fullId:`id${i}`,targetWord:`word${i}`,rank:i+11}));
    const batch = h.selectStudySessionCards(cards);
    assert.equal(batch.cards.length,20);
    assert.equal(batch.cards[0].rank,11);
    assert.equal(batch.cards.at(-1).rank,30); // Cross the former 25-card boundary.
    assert.equal(batch.remaining,45);
    assert.equal(h.selectStudySessionCards(cards.slice(0,7)).cards.length,7);
    assert.equal(h.selectStudySessionCards([]).remaining,0);
    cards[19]={fullId:'pair-a',targetWord:'pair',splitInfo:{index:1}};
    cards[20]={fullId:'pair-b',targetWord:'pair',splitInfo:{index:2}};
    const paired=h.selectStudySessionCards(cards);
    assert.equal(paired.cards.length,19);
    assert.equal(paired.remaining,46);
    assert.equal(h.selectStudySessionCards(cards.slice(19)).cards[1].fullId,'pair-b');

    h.currentUser={isGuest:true};
    const guestWord={word:'guestword',id:'guest-id'};
    h.recordGuestSessionAnswer({fullId:h.getWordId(guestWord)},true);
    assert.equal(h.getGuestSessionLearningState(guestWord).seen,true);
    assert.equal(h.getGuestSessionLearningState(guestWord).needsReview,false);
    h.recordGuestSessionAnswer({fullId:h.getWordId(guestWord)},false);
    assert.equal(h.getGuestSessionLearningState(guestWord).needsReview,true);
    h.selectedLanguage='portuguese';
    assert.equal(h.getGuestSessionLearningState(guestWord).seen,false);

    const ui=fs.readFileSync('app/js/ui.js','utf8');
    const elements=new Map();
    const node=id=>{if(!elements.has(id))elements.set(id,{style:{},dataset:{},querySelector(){return null;},addEventListener(type,fn){this[type]=fn;}});return elements.get(id);};
    const level={dataset:{level:'c100',startRank:'1',endRank:'101',rankBasis:'stable'}};
    const baseline=Array.from({length:100},(_,i)=>({rank:i+1,stableRank:i+1,id:`id${i}`}));
    let vocab=baseline.filter(item=>item.rank>10);
    const context={
        window:{isFastTrackOn:()=>true},config:{languages:{spanish:{}}},selectedLanguage:'spanish',
        activeArtist:null,currentUser:{isGuest:true},selectedLevel:'c100',percentageMode:true,ppmData:[{}],
        levelEstimates:{},STABLE_SET_SLOT_COUNT:25,STUDY_SESSION_LIMIT:20,QUICK_REVIEW_LIMIT:20,_studySessionStarting:false,
        document:{getElementById:node,querySelector:()=>level,querySelectorAll:()=>[level]},
        resetSetupStateMemo(){},fetchActiveVocabularyData:async()=>baseline,
        getPreparedSetupVocabulary:()=>({vocab,stableBaseline:baseline}),
        _levelRankAccessor:()=>item=>item.stableRank,buildStableSetRanges:h.buildStableSetRanges,
        getSetupLearningState:item=>item.rank<=25?{seen:true,estimated:true}:item.rank<=30?{seen:true,needsReview:true,reviewReason:'due'}:item.rank<=50?{seen:true,needsReview:false}:{seen:false},
        setActiveSetupStep(){},renderSetupExtrasSection(){},startSelectedStudySession(){},
    };
    // buildStableSetRanges is provided by ui.js, not the estimation harness's defaults.
    vm.runInNewContext(ui.slice(ui.indexOf('function buildStableSetRanges('),ui.indexOf('function computeSmartLevelRanges(')),
        {...context,STABLE_SET_SLOT_COUNT:25,window:context.window});
    context.buildStableSetRanges=context.window.buildStableSetRanges;
    vm.createContext(context);
    vm.runInContext(ui.slice(ui.indexOf('async function renderRangeSelector('),ui.indexOf('function _escapeHtml(')),context);
    await context.renderRangeSelector();
    const html=node('rangeSelector').innerHTML;
    assert.equal((html.match(/class="study-level-bar"/g)||[]).length,1);
    assert.ok(!html.includes('study-level-segment'));
    assert.match(html,/--set-known-end:20%;--set-review-end:25%;--set-estimated-end:40%;--set-new-end:90%/);
    assert.ok(!html.includes('study-set-dot'));
    assert.match(html,/Go · 20 cards/);
    assert.match(html,/15 Estimated familiar/);
    assert.match(html,/5 Practice/);
    assert.match(html,/10 Skipped/);
    assert.match(html,/20 Known/);
    assert.equal(context.window.__studySessionContext.range,'1-101');
    assert.equal(context.window.__studySessionContext.unseenCount,50);
    vocab=[];
    await context.renderRangeSelector();
    assert.match(node('rangeSelector').innerHTML,/100 Skipped/);
    assert.match(node('rangeSelector').innerHTML,/--set-known-end:0%;--set-review-end:0%;--set-estimated-end:0%;--set-new-end:0%/);
    assert.match(node('rangeSelector').innerHTML,/disabled>No cards available/);

    // Continuation recounts current progress; no practice/replay fallback.
    let calls=[];
    const nextContext={window:{progressRefreshSettled:async()=>calls.push('sync')},
        renderRangeSelector:async()=>{calls.push('recount');nextContext.window.__studySessionContext={unseenCount:7};},
        startSelectedStudySession:async options=>{calls.push(options.studyMode);return true;},
        getNextStudyLevelMeta:()=>{throw Error('Must finish this level first');}};
    vm.runInNewContext(ui.slice(ui.indexOf('async function startNextStudyLevelFirstSet('),ui.indexOf('function showStatsModal(')),nextContext);
    await nextContext.startNextStudyLevelFirstSet();
    assert.deepEqual(calls,['sync','recount','new']);
    console.log('Session boundaries, short tails, companion pairs, estimated/skipped progress, and same-level continuation passed.');
})().catch(error=>{console.error(error);process.exitCode=1;});
