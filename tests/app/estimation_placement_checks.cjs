const assert = require('node:assert/strict');
const { createHarness } = require('./estimation_harness.cjs');
const meaning = (headword, translation, frequency = 1, extra = {}) => ({ headword, translation, frequency, pos: 'NOUN', ...extra });
const word = (text, rank, meanings, extra = {}) => ({ id: text, word: text, rank, stableRank: rank, meanings, ...extra });
function control(dataset = {}) {
    const classes = new Set();
    return { dataset, classes, style: { setProperty() {} },
        classList: { toggle(name, on) { if (on) classes.add(name); else classes.delete(name); } },
        setAttribute(name, value) { this[name] = value; } };
}
(async () => {
    let h = createHarness();
    const rows = Array.from({length: 100}, (_, index) => word(`word${index}`, index + 1, [meaning(`lemma${index}`, 'word')]));
    const items = h.buildEstimationPool(rows, {values: Object.fromEntries(rows.map(row => [row.word, 101-row.rank]))}, {includeAssumed:true});
    const levels = Array.from({length:10}, (_, index) => ({number:index+1,startRank:index*10+1,endRank:(index+1)*10+1,rankBasis:'stable'}));
    const bands = [
        {start:0,end:40,size:40,sampleSize:40,answers:20,known:19},
        {start:40,end:80,size:40,sampleSize:40,answers:20,known:15},
        {start:80,end:100,size:20,sampleSize:20,answers:20,known:5}
    ];
    let result = h.calculateRecognitionPlacement(items,bands,levels,rows);
    assert.deepEqual(Array.from(result.choices, choice => choice.levelNumber), [4,6]);
    assert.deepEqual(Array.from(result.choices, choice => choice.sourceRank), [30,50]);
    assert.ok(result.choices[0].probability > result.choices[1].probability);
    const allKnown = bands.map(band => ({...band,known:band.answers}));
    result = h.calculateRecognitionPlacement(items,allKnown,levels,rows);
    assert.equal(result.choices.length,1); assert.equal(result.choices[0].levelNumber,10);
    assert.equal(result.choices[0].sourceRank,90); // leave the final level available
    result = h.calculateRecognitionPlacement(items,bands.map(band=>({...band,known:0})),levels,rows);
    assert.equal(result.choices.length,1); assert.equal(result.choices[0].sourceRank,0);
    assert.equal(h.calculateRecognitionPlacement([],[],[],[]).choices.length,0);

    // Applying the later option persists that boundary, routes to its level,
    // and never writes sampled answers into real progress.
    h.input=items; h.profileBands=bands; h.profileLevels=levels; h.baseline=rows;
    h.progressData={existing:{seen:true}};
    h.document.querySelectorAll=()=>levels.map((level,index)=>({
        dataset:{startRank:String(level.startRank),endRank:String(level.endRank),rankBasis:'stable'},
        click(){h.clickedLevel=index+1;}
    }));
    h.renderLevelSelector=async()=>{h.annotationsRefreshed=true;};
    h.run(`estimationState=createEstimationState(); estimationState.validWords=input;
        estimationState.bands=profileBands; estimationState.maxLevel=input.length;
        estimationState.placementLevels=profileLevels; estimationState.placementBaseline=baseline;
        showEstimationResult();`);
    assert.equal(h.estimationState.placementChoices.length,2);
    assert.match(h.elements.get('estimationPlacementOptions').innerHTML,/More review/);
    assert.match(h.elements.get('estimationPlacementOptions').innerHTML,/More new vocabulary/);
    await h.useEstimatedLevel(1);
    assert.equal(h.savedRank,50); assert.equal(h.clickedLevel,6); assert.equal(h.annotationsRefreshed,true);
    assert.deepEqual(h.progressData,{existing:{seen:true}});

    // Cognates count towards recognition without becoming sampled prompts.
    const cognate = word('hospital',10,[meaning('hospital','hospital')],{cognate_score:1});
    const opaque = word('opaco',1,[meaning('opaco','opaque')]);
    const full = h.buildEstimationPool([opaque,cognate],{values:{hospital:10,opaco:20}},{includeAssumed:true});
    assert.equal(full.length,2); assert.equal(h.buildEstimationPool([opaque,cognate]).length,1);
    h.pool=full;
    h.run('estimationState=createEstimationState(); estimationState.validWords=pool; estimationState.bands=buildEstimationBands(pool);');
    assert.equal(h.pickWordFromBand(0).word,'opaco');
    h.run('estimationState.shownWordIds.add(getWordKey(pool[0]));');
    assert.equal(h.pickWordFromBand(0),null);
    const sampleBands=h.buildEstimationBands(full); sampleBands[0].answers=1; sampleBands[0].known=0;
    result=h.calculateRecognitionPlacement(full,sampleBands,[{number:1,startRank:1,endRank:11}], [opaque,cognate]);
    assert.equal(result.profile[0].probability,.5);
    assert.equal(h.calculateGroupEstimate(sampleBands,2).point,1);
    sampleBands[0].known=1; assert.equal(h.calculateGroupEstimate(sampleBands,2).point,2);
    const assumedOnly=h.buildEstimationBands([full[1]]);
    assert.equal(h.calculateGroupEstimate(assumedOnly,1).point,1);

    // Many inflections cannot outweigh a distinct recognised group in placement.
    const members=Array.from({length:20},(_,i)=>word(`form${i}`,i+1,[meaning('opaque','opaque')]));
    const grouped=[{estimationKey:'many',estimationMembers:members.map(source=>({source,weight:1}))},
        {estimationKey:'cognate',estimationAssumedKnown:true,estimationMembers:[{source:{rank:21},weight:1}]}];
    result=h.calculateRecognitionPlacement(grouped,[{start:0,end:2,size:2,sampleSize:1,answers:5,known:3}],
        [{number:1,startRank:1,endRank:22}], [...members,{rank:21}]);
    assert.ok(Math.abs(result.profile[0].probability-.8)<1e-10);

    // Mixed groups use their most frequent non-cognate form, even when a
    // cognate is the group's frequency leader.
    const nounProof={rule_version:'noun-merge/v2',allowed:true,lemma:'hospital',sense_set:'same-complete-menu'};
    const mixed=h.buildEstimationPool([
        word('hospital',1,[meaning('hospital','hospital')],{cognate_score:1,noun_merge:nounProof}),
        word('hospitales',2,[meaning('hospital','hospitals')],{noun_merge:nounProof})
    ],{values:{hospital:100,hospitales:5}},{includeAssumed:true});
    assert.equal(mixed.length,1); assert.equal(mixed[0].word,'hospitales');
    assert.equal(mixed[0].estimationAssumedKnown,false); assert.equal(mixed[0].estimationFrequency,105);
    const blocked=h.buildEstimationPool([
        word('hospital',1,[meaning('hospital','hospital')],{noun_merge:{...nounProof,allowed:false}}),
        word('hospitales',2,[meaning('hospital','hospitals')],{noun_merge:{...nounProof,allowed:false}})
    ],{values:{hospital:100,hospitales:5}},{includeAssumed:true});
    assert.equal(blocked.length,2);

    // Use the actual per-sense/per-known-language cognate engine. A split's
    // transparent reading must not hide the opaque sibling.
    h=createHarness({cognateThreshold:.83}); h.loadModule('cognates.js');
    h.fetch=async()=>({ok:true,json:async()=>({schema:'cognate-score/v4',language:'es',known_languages:['en'],thresholds:{en:.8},scores:{
        fue:{ser:{was:{en:.95},existed:{en:.95}},ir:{went:{en:.1},departed:{en:.1}}}
    }})});
    await h.loadCognateScores({cognatesPath:'scores',speechLang:'es-ES'});
    const split=word('fue',1,[
        meaning('ser','was',70,{pos:'VERB',canonical_example:{text:'Fue una buena idea.'}}),
        meaning('ser','existed',10,{pos:'VERB'}),
        meaning('ir','went',15,{pos:'VERB',canonical_example:{text:'Fue a Madrid.'}}),
        meaning('ir','departed',5,{pos:'VERB'})
    ]);
    h.applyCognateScores([split],'es');
    const splitPool=h.buildEstimationPool([split],{values:{fue:100}},{includeAssumed:true});
    assert.equal(splitPool.length,2); assert.equal(splitPool.filter(item=>item.estimationAssumedKnown).length,1);
    h.excludeCognates=false; const disabled=h.buildEstimationPool([split]);
    h.excludeCognates=true; const enabled=h.buildEstimationPool([split]);
    assert.equal(disabled.length,1); assert.equal(enabled.length,1);
    assert.equal(disabled[0].estimationKey,enabled[0].estimationKey);
    assert.equal(disabled[0].meanings[0].translation,'went');
    h.writeKnownLanguages([]); assert.equal(h.buildEstimationPool([split]).length,2);

    // AUTO annotates estimated completion; removing the estimate restores the
    // progress bar. Explicit progress is never overwritten or relabelled AUTO.
    h=createHarness(); h.loadModule('ui.js');
    const controls=[control({startRank:'1',endRank:'101'}),control({startRank:'101',endRank:'201'})];
    const segments=[control({i:'0'}),control({i:'1'})];
    const vocabulary=[{id:'a',rank:1},{id:'b',rank:50},{id:'c',rank:101}];
    h.currentUser={isGuest:false}; h.progressData={}; h.levelEstimates.spanish=100;
    h.fetchActiveVocabularyData=async()=>vocabulary;
    h.getPreparedSetupVocabulary=()=>({vocab:vocabulary});
    h.buildSeenLemmaSet=async()=>new Set();
    h.getRecordedSetupState=item=>({seen:Boolean(item.earned),needsReview:false});
    h.document.querySelectorAll=()=>segments;
    await h.findFirstIncompleteLevelBtn('spanish',controls);
    assert.equal(controls[0].classes.has('is-auto-complete'),true);
    assert.equal(segments[0]['aria-label'],'Level 1, AUTO');
    assert.equal(controls[1].classes.has('is-auto-complete'),false);
    h.levelEstimates.spanish=0;
    await h.findFirstIncompleteLevelBtn('spanish',controls);
    assert.equal(segments[0].classes.has('is-auto-complete'),false);
    vocabulary[0].earned=true; vocabulary[1].earned=true;
    h.levelEstimates.spanish=100;
    await h.findFirstIncompleteLevelBtn('spanish',controls);
    assert.equal(segments[0].classes.has('is-auto-complete'),false);
    assert.equal(segments[0]['aria-label'],'Level 1, 100% complete');
    console.log('Recognition boundaries, two choices, assumed cognates, split siblings and AUTO checks passed.');
})().catch(error=>{console.error(error);process.exitCode=1;});
