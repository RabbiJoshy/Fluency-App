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

    // SETWISE-2 session lengths and return times.
    const planSource=fs.readFileSync('app/js/session-plan.js','utf8').replace(/\nexport \{[\s\S]*?\};\s*$/,'');
    const store=new Map();
    const planContext={localStorage:{getItem:k=>store.get(k)??null,setItem:(k,v)=>store.set(k,String(v))},
        dispatchEvent(){},CustomEvent:class{constructor(type,init){this.type=type;this.detail=init?.detail;}}};
    planContext.globalThis=planContext;
    vm.runInNewContext(planSource,planContext);
    const plan=planContext.SessionPlan;
    assert.equal(plan.getSessionLength(),'5');
    assert.equal(plan.sessionCardLimit('new'),20);
    assert.equal(plan.sessionCardLimit('practice'),30);
    assert.equal(plan.sessionCardLimit('new','10'),40);
    assert.equal(plan.sessionCardLimit('practice','10'),60);
    assert.equal(plan.sessionCardLimit('new','all'),plan.NO_LIMIT_CARDS);
    assert.equal(plan.cycleSessionLength(),'10');
    assert.equal(store.get('fluencySessionLengthV1'),'10');
    assert.equal(plan.cycleSessionLength(),'all');
    assert.equal(plan.cycleSessionLength(),'5');
    const noon=new Date(2026,9,12,12,0,0).getTime();
    const H=3600*1000, D=24*H;
    assert.equal(plan.formatReturnTime(noon+30*60*1000,noon),'within the hour');
    assert.equal(plan.formatReturnTime(noon+3*H,noon),'in 3 hours');
    assert.equal(plan.formatReturnTime(noon+D,noon),'tomorrow');
    assert.equal(plan.formatReturnTime(noon+3*D,noon),'on Thursday');
    assert.equal(plan.formatReturnTime(noon+9*D,noon),'next week');
    assert.equal(plan.formatReturnTime(noon+21*D,noon),'in 3 weeks');
    const upcoming=plan.summariseUpcoming([noon+D,noon+D+H,noon+3*D,noon+20*D,noon-H],noon);
    assert.deepEqual([upcoming.total,upcoming.nextCount,upcoming.nextLabel,upcoming.laterThisWeek],[4,2,'tomorrow',1]);
    assert.equal(plan.describeUpcoming(upcoming),'2 words come back tomorrow, 1 more this week.');
    assert.equal(plan.describeUpcoming(plan.summariseUpcoming([],noon)),'');

    const ui=fs.readFileSync('app/js/ui.js','utf8');
    const elements=new Map();
    const node=id=>{if(!elements.has(id))elements.set(id,{style:{},dataset:{},querySelector(){return null;},addEventListener(type,fn){this[type]=fn;}});return elements.get(id);};
    const level={dataset:{level:'c100',startRank:'1',endRank:'101',rankBasis:'stable'},addEventListener(){}};
    const baseline=Array.from({length:100},(_,i)=>({rank:i+1,stableRank:i+1,id:`id${i}`}));
    let vocab=baseline.filter(item=>item.rank>10);
    let stateOf=item=>item.rank<=25?{seen:true,estimated:true}:item.rank<=30?{seen:true,needsReview:true,reviewReason:'due'}:item.rank<=50?{seen:true,needsReview:false}:{seen:false};
    const context={
        window:{isFastTrackOn:()=>true,SessionPlan:plan},config:{languages:{spanish:{}}},selectedLanguage:'spanish',
        activeArtist:null,currentUser:{isGuest:true},selectedLevel:'c100',percentageMode:true,ppmData:[{}],
        levelEstimates:{},STABLE_SET_SLOT_COUNT:25,STUDY_SESSION_LIMIT:20,QUICK_REVIEW_LIMIT:20,_studySessionStarting:false,
        LEVEL_CHOICE_MIN_PRACTICE:10,_levelChoiceDeclined:new Set(),
        document:{getElementById:node,querySelector:()=>level,querySelectorAll:()=>[level]},
        resetSetupStateMemo(){},fetchActiveVocabularyData:async()=>baseline,
        getPreparedSetupVocabulary:()=>({vocab,stableBaseline:baseline}),
        _levelRankAccessor:()=>item=>item.stableRank,buildStableSetRanges:h.buildStableSetRanges,
        getSetupLearningState:item=>stateOf(item),
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
    assert.match(html,/--level-new-end:50%;--level-review-end:55%;--level-known-end:75%;--level-estimated-end:90%/);
    assert.ok(!html.includes('study-set-dot'));
    assert.match(html,/>Go<\/button>/);
    assert.match(html,/data-session-length-toggle[\s\S]*>5 min<\/button>/);
    assert.match(html,/data-level-state="new"/);
    assert.match(html,/15 Estimated familiar/);
    assert.match(html,/5 Practice/);
    assert.match(html,/10 Skipped/);
    assert.match(html,/20 Known/);
    assert.ok(html.indexOf('50 New') < html.indexOf('5 Practice'));
    assert.ok(html.indexOf('5 Practice') < html.indexOf('20 Known'));
    assert.ok(html.indexOf('20 Known') < html.indexOf('15 Estimated familiar'));
    assert.ok(html.indexOf('15 Estimated familiar') < html.indexOf('10 Skipped'));
    assert.equal(context.window.__studySessionContext.range,'1-101');
    assert.equal(context.window.__studySessionContext.unseenCount,50);
    assert.equal(context.window.__studySessionContext.levelState,'new');
    // More of the level waits in Practise than is new: Go asks first.
    const original=stateOf;
    stateOf=item=>item.rank<=80?{seen:true,needsReview:true,reviewReason:'incorrect'}:{seen:false};
    await context.renderRangeSelector();
    assert.equal(context.window.__studySessionContext.levelState,'choice');
    context._levelChoiceDeclined.add(context.window.__studySessionContext.levelKey);
    await context.renderRangeSelector();
    assert.equal(context.window.__studySessionContext.levelState,'new');
    stateOf=item=>({seen:true,needsReview:item.rank<=40,nextReviewAt:item.rank>40?Date.now()+86400000:0});
    await context.renderRangeSelector();
    assert.equal(context.window.__studySessionContext.levelState,'met');
    assert.equal(context.window.__studySessionContext.levelUpcoming.total,60);
    stateOf=()=>({seen:true,needsReview:false});
    await context.renderRangeSelector();
    assert.equal(context.window.__studySessionContext.levelState,'done');
    stateOf=original;
    vocab=[];
    await context.renderRangeSelector();
    assert.match(node('rangeSelector').innerHTML,/100 Skipped/);
    assert.match(node('rangeSelector').innerHTML,/--level-new-end:0%;--level-review-end:0%;--level-known-end:0%;--level-estimated-end:0%/);
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
