const assert=require('node:assert/strict');
const {createHarness}=require('./estimation_harness.cjs');
(async()=>{
    const h=createHarness(); h.loadModule('ui.js');
    const baseline=Array.from({length:1200},(_,index)=>({rank:index+1,stableRank:index+1,id:`word${index}`}));
    const items=baseline.map(source=>({estimationKey:source.id,estimationMembers:[{source,weight:1}]}));
    const levels=Array.from({length:12},(_,index)=>({number:index+1,startRank:index*100+1,endRank:(index+1)*100+1,rankBasis:'stable'}));
    const regions=h.buildEstimationPlacementRegions(levels);
    assert.equal(regions.filter(region=>region.number===10).length,4);
    assert.equal(regions.filter(region=>region.number===11).length,1);
    assert.equal(regions.find(region=>region.number===11).setNumber,null);
    const partial=h.buildStableSetRanges(101,136,'source');
    assert.deepEqual(Array.from(partial,set=>[set.startRank,set.endRank]),[[101,126],[126,136]]);
    assert.equal(h.buildStableSetRanges(1,1).length,0);
    assert.equal(h.buildEstimationPlacementRegions([{number:1,startRank:1,endRank:21}])[0].setNumber,null);
    const largeBands=h.buildEstimationBands(Array.from({length:7500},()=>({})));
    assert.equal(largeBands[0].size,40);
    assert.equal(largeBands.at(-1).end,7500);
    assert.equal(largeBands.reduce((sum,band)=>sum+band.size,0),7500);
    largeBands.forEach((band,index)=>{assert.ok(band.size>0); if(index) assert.equal(band.start,largeBands[index-1].end);});
    assert.ok(largeBands.at(-1).size>largeBands[0].size);

    const bands=[
        {start:0,end:25,size:25,sampleSize:25,answers:50,known:49},
        {start:25,end:150,size:125,sampleSize:125,answers:50,known:29},
        {start:150,end:1200,size:1050,sampleSize:1050,answers:50,known:0}
    ];
    const result=h.calculateRecognitionPlacement(items,bands,levels,baseline);
    assert.deepEqual(Array.from(result.choices,choice=>[choice.levelNumber,choice.setNumber,choice.sourceRank]),[[1,2,25],[1,3,50]]);
    // Two different sets in one level remain two choices.
    assert.equal(result.choices.length,2);
    const shifted=baseline.map(source=>({...source,rank:source.rank+500}));
    const shiftedItems=shifted.map(source=>({estimationKey:source.id,estimationMembers:[{source,weight:1}]}));
    const shiftedPlacement=h.calculateRecognitionPlacement(shiftedItems,bands,levels,shifted);
    assert.deepEqual(Array.from(shiftedPlacement.choices,choice=>choice.sourceRank),[525,550]);
    const laterBands=[
        {start:0,end:900,size:900,sampleSize:900,answers:20,known:20},
        {start:900,end:950,size:50,sampleSize:50,answers:20,known:19},
        {start:950,end:1200,size:250,sampleSize:250,answers:20,known:14}
    ];
    const later=h.calculateRecognitionPlacement(items,laterBands,levels,baseline);
    assert.deepEqual(Array.from(later.choices,choice=>[choice.levelNumber,choice.setNumber]),[[10,3],[11,null]]);
    assert.equal(later.choices[1].startRank,1001);
    const zero=h.calculateRecognitionPlacement(items,bands.map(band=>({...band,known:0})),levels,baseline);
    assert.equal(zero.choices.length,1); assert.equal(zero.choices[0].setNumber,1); assert.equal(zero.choices[0].sourceRank,0);
    const full=h.calculateRecognitionPlacement(items,bands.map(band=>({...band,known:band.answers})),levels,baseline);
    assert.equal(full.choices.length,1); assert.equal(full.choices[0].levelNumber,12); assert.equal(full.choices[0].setNumber,null);

    h.input=items; h.bands=bands; h.levels=levels; h.baseline=baseline;
    let resolveDots;
    const dotsReady=new Promise(resolve=>{resolveDots=resolve;});
    const buttons=levels.map((level,index)=>({
        dataset:{startRank:String(level.startRank),endRank:String(level.endRank),rankBasis:'stable'},
        click(){h.clickedLevel=index+1;this._rangeRenderPromise=dotsReady;}
    }));
    h.document.querySelectorAll=()=>buttons;
    h.document.querySelector=selector=>selector.includes('data-index="2"')?{disabled:false,click(){h.clickedSet=3;}}:null;
    h.renderLevelSelector=async()=>{};
    h.run(`estimationState=createEstimationState(); estimationState.validWords=input;
        estimationState.bands=bands; estimationState.maxLevel=input.length;
        estimationState.placementLevels=levels; estimationState.placementBaseline=baseline;
        showEstimationResult();`);
    assert.match(h.elements.get('estimationPlacementOptions').innerHTML,/Level 1 · Set 2/);
    assert.match(h.elements.get('estimationPlacementOptions').innerHTML,/Level 1 · Set 3/);
    const applying=h.useEstimatedLevel(1);
    await new Promise(resolve=>setTimeout(resolve,0));
    assert.equal(h.savedRank,50); assert.equal(h.clickedLevel,1); assert.equal(h.clickedSet,undefined);
    resolveDots(); await applying; assert.equal(h.clickedSet,3);
    h.document.querySelector=()=>({disabled:true,click(){throw new Error('An unavailable set must not be clicked');}});
    await h.selectLevelForRank(51,3);
    console.log('Early level/set choices, level-10 cutoff, source-rank compatibility and asynchronous set routing passed.');
})().catch(error=>{console.error(error);process.exitCode=1;});
