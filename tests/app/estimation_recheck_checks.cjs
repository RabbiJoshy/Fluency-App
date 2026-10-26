const assert = require('node:assert/strict');
const { createHarness } = require('./estimation_harness.cjs');
const storage = new Map();
function harness(extra = {}) {
    return createHarness({ localStorage: { getItem: k => storage.get(k) || null,
        setItem: (k, v) => storage.set(k, v) }, ...extra });
}
function fixture(h, known = 0) {
    const rows = Array.from({length: 120}, (_, i) => ({id: String(i + 1), word: `word${i+1}`,
        rank: i+1, stableRank: i+1, meanings: [{pos:'NOUN', translation:'meaning'}]}));
    const items = rows.map(row => ({...row, estimationKey:`surface:${row.id}`,
        estimationMembers:[{source:row, weight:1}], estimationAssumedKnown:false}));
    h.items=items; h.rows=rows;
    h.run(`estimationState=createEstimationState(); estimationState.validWords=items;
        estimationState.placementBaseline=rows;
        estimationState.placementLevels=Array.from({length:12},(_,i)=>({number:i+1,startRank:i*10+1,endRank:i*10+11,rankBasis:'stable'}));
        estimationState.bands=buildEstimationBands(items);
        estimationState.coverageOrder=buildCoverageOrder(estimationState.bands.length);`);
    const choice={target:.9,startRank:61,sourceRank:60,rankBasis:'stable',levelNumber:7};
    h.choice=choice; h.armPlacementChecker(choice); h.levelEstimates.spanish=60;
    const cards=rows.slice(60,80).map(row=>({...row,fullId:`es0${row.id}`,targetWord:row.word}));
    const context={studyMode:'new',rangeString:'61-81',rangeBasis:'stable'};
    h.beginPlacementStudySet(cards,context);
    return {cards,context,choice};
}
(async () => {
    let h=harness(); let {cards,context}=fixture(h);
    assert.equal(h.readPlacementSession().status,'collecting');
    for (let i=0;i<cards.length;i++) {
        h.recordPlacementStudyAnswer(cards[i],i<4,{recognition:true});
        h.recordPlacementStudyAnswer(cards[i],true,{recognition:true});
    }
    assert.equal(h.readPlacementSession().evidence.length,20);
    assert.equal(h.readPlacementSession().evidence.filter(a=>a.known).length,4);
    h.completePlacementStudySet(context);
    assert.equal(h.readPlacementSession().status,'offered');
    assert.equal(h.elements.get('placementRecheckOffer').hidden,false);
    const retained=h.readPlacementSession();
    h.run('estimationState.recheck=readPlacementSession(); seedPlacementRecheck(estimationState, estimationState.recheck);');
    assert.equal(h.estimationState.bands.reduce((n,b)=>n+b.answers,0),20);
    for(let n=0;n<30;n++) assert.ok(h.pickWordFromBand(0)?.rank <61);
    h.finishPlacementRecheck();
    assert.equal(h.readPlacementSession().status,'done');
    h.completePlacementStudySet(context);
    assert.equal(h.elements.get('placementRecheckOffer').hidden,true);

    // Reload resumes evidence but does not recount an answered group.
    h=harness(); ({cards,context}=fixture(h));
    h.recordPlacementStudyAnswer(cards[0],false,{recognition:true});
    let reloaded=harness({levelEstimates:{spanish:60}});
    reloaded.beginPlacementStudySet(cards,context);
    reloaded.recordPlacementStudyAnswer(cards[0],true,{recognition:true});
    assert.equal(reloaded.readPlacementSession().evidence.length,1);
    assert.equal(reloaded.readPlacementSession().evidence[0].known,false);
    reloaded.currentUser={initials:'OTHER'};
    assert.equal(reloaded.readPlacementSession(),null);
    reloaded.currentUser=null; reloaded.selectedLanguage='french';
    reloaded.config.languages.french={}; reloaded.levelEstimates.french=60;
    assert.equal(reloaded.readPlacementSession(),null);

    // Non-recognition encounters are consumed even if later switched to recognition.
    h=harness(); ({cards,context}=fixture(h));
    h.observePlacementStudyCard(cards[0],false);
    h.recordPlacementStudyAnswer(cards[0],true,{recognition:true});
    h.recordPlacementStudyAnswer(cards[1],false,{recognition:false});
    h.recordPlacementStudyAnswer({...cards[2],previewOnly:true},false,{recognition:true});
    h.recordPlacementStudyAnswer({...cards[3],isChainChild:true},false,{recognition:true});
    h.isCognateKnown=card=>card.id===cards[4].id;
    h.recordPlacementStudyAnswer(cards[4],false,{recognition:true});
    h.getWordProgressState=()=>({seen:true});
    h.recordPlacementStudyAnswer(cards[5],false,{recognition:true});
    assert.equal(h.readPlacementSession().evidence.length,0);
    h.completePlacementStudySet(context);
    assert.equal(h.readPlacementSession().status,'done');

    for(const [n,known,expected] of [[9,0,'done'],[10,2,'offered'],[10,3,'done'],[20,0,'offered']]) {
        h=harness(); ({cards,context}=fixture(h));
        cards.slice(0,n).forEach((c,i)=>h.recordPlacementStudyAnswer(c,i<known,{recognition:true}));
        h.completePlacementStudySet(context);
        assert.equal(h.readPlacementSession().status,expected);
    }
    // Study away from the selected starting position disarms; other modes cannot trigger.
    h=harness(); ({cards,context}=fixture(h));
    h.beginPlacementStudySet(cards,{...context,rangeString:'81-101'});
    assert.equal(h.readPlacementSession().status,'done');
    h=harness(); ({cards,context}=fixture(h));
    h.activeArtist={name:'Artist'};
    cards.forEach(c=>h.recordPlacementStudyAnswer(c,false,{recognition:true}));
    h.completePlacementStudySet(context);
    assert.equal(h.readPlacementSession().evidence.length,0);
    h.activeArtist=null; h.config.languages.spanish.indexPath='new-release';
    assert.equal(h.readPlacementSession(),null);

    // Stable placement requires both five unchanged answers and one-answer robustness.
    h=harness(); fixture(h);
    h.run(`estimationState.bands.forEach(b=>{b.answers=100;b.known=0;});
        estimationState.wordsTestedCount=20;
        estimationState.placementHistory=Array(5).fill(placementSignature());`);
    assert.equal(h.placementIsStable(),true);
    h.estimationState.wordsTestedCount=19; assert.equal(h.placementIsStable(),false);
    h.estimationState.wordsTestedCount=20;
    h.estimationState.placementHistory[0]='different'; assert.equal(h.placementIsStable(),false);
    // Sampling goes toward the .9/.8 crossing, not a larger rare-word band at .5.
    h.run(`estimationState.bands=[
        {start:0,end:40,size:40,sampleSize:40,answers:20,known:18},
        {start:40,end:80,size:40,sampleSize:40,answers:20,known:16},
        {start:80,end:120,size:4000,sampleSize:40,answers:20,known:10}];
        estimationState.wordsTestedCount=21;`);
    assert.notEqual(h.chooseNextBandIndex(),2);
    h.run(`estimationState.wordsTestedCount=7;`); // fifth after 3-band coverage
    assert.ok(h.chooseNextBandIndex()<=1);

    // Inconclusive recheck cannot mutate position through the Enter shortcut.
    h=harness(); fixture(h);
    h.run(`estimationState.recheck=readPlacementSession(); showPlacementRecheckResult();`);
    assert.equal(h.estimationState.placementChoices.length,0);
    await h.useEstimatedLevel();
    assert.equal(h.levelEstimates.spanish,60);
    assert.equal(h.savedRank,undefined);
    // A supported earlier recommendation changes only the numeric estimate on acceptance.
    h=harness(); fixture(h); h.progressData={existing:{correct:2}};
    h.run(`estimationState.recheck=readPlacementSession();
        estimationState.bands.forEach(b=>{b.answers=100;b.known=0;});
        estimationState.wordsTestedCount=8;
        estimationState.placementHistory=Array(5).fill(placementSignature());
        showPlacementRecheckResult();`);
    assert.equal(h.estimationState.placementChoices[0].startRank,1);
    assert.equal(h.levelEstimates.spanish,60);
    await h.useEstimatedLevel(0);
    assert.equal(h.levelEstimates.spanish,0);
    assert.deepEqual(h.progressData,{existing:{correct:2}});

    // Cancellation and preparation failure do not change the numeric estimate.
    h=harness(); fixture(h); h.run('estimationState.recheck=readPlacementSession();');
    h.closeEstimationModal(); assert.equal(h.levelEstimates.spanish,60);
    assert.equal(h.readPlacementSession().status,'done');
    h=harness(); fixture(h);
    h.loadEstimationVocabulary=async()=>{throw new Error('expected offline');};
    await h.startEstimation(h.readPlacementSession());
    assert.equal(h.levelEstimates.spanish,60);
    assert.equal(h.readPlacementSession().status,'done');
    console.log('Placement evidence, sampling, stopping, first-set trigger, recheck and progress preservation passed.');
})();
