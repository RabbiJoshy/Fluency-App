const assert = require('node:assert/strict');
const {createHarness} = require('./estimation_harness.cjs');
(async () => {
    const h = createHarness();
    const activeIndex = [{id: 'artist'}], activeExamples = { artist: {} };
    h._cachedJoinedIndex = activeIndex; h._cachedJoinedIndexPath = 'artist/index.json';
    h._cachedExamplesData = activeExamples; h._cachedExamplesDataPath = 'artist/examples.json';
    h.activeArtist = { name: 'Artist' };
    const config = { indexPath: 'speech/index.json', examplesPath: 'speech/examples.json',
        frequencyPath: 'frequency.json', mergeExceptionsPath: 'exceptions.json' };
    const shards = Array.from({length:9}, (_, i) => ({path:`rows-${i}.json`}));
    let inflight = 0, peak = 0, loads = 0;
    const progress = [];
    h.fetch = async url => {
        if (url.endsWith('vocabulary.index.manifest.json')) return {ok:true, json:async()=>({columns:'columns.json',shards})};
        if (url.endsWith('columns.json')) return {ok:true, json:async()=>({n:9, id:Array.from({length:9},(_,i)=>String(i)),word:Array.from({length:9},(_,i)=>`form${i}`),rank:Array.from({length:9},(_,i)=>i+1)})};
        if (url.includes('rows-')) {
            inflight++; loads++; peak = Math.max(peak, inflight);
            await new Promise(r=>setTimeout(r,1)); inflight--;
            const i = Number(url.match(/rows-(\d+)/)[1]);
            return {ok:true,json:async()=>({[i]:{meanings:[{headword:'root',pos:'VERB',translation:'meaning'}]}})};
        }
        if (url === 'exceptions.json') return {ok:true,json:async()=>({contractions:['form2']})};
        if (url === 'frequency.json') return {ok:true,json:async()=>({schema:'speech-source-frequency/v1',indexPath:'speech/index.json',values:{form0:100}})};
        if (url.endsWith('vocabulary.examples.manifest.json')) return {ok:true,json:async()=>({example_format:'slim-example/v1',sources:{},shards:[{path:'examples-1.json',start_rank:1,end_rank:3},{path:'examples-2.json',start_rank:4,end_rank:9}]})};
        if (url.endsWith('examples-1.json')) return {ok:true,json:async()=>({'0':{m:[[{t:'Target sentence',e:'English',s:'test'}]]}})};
        throw new Error('Unexpected fetch: '+url);
    };
    const words = await h.loadEstimationVocabulary(config,(done,total)=>progress.push([done,total]));
    assert.equal(words.length,9); assert.equal(words[2].is_contraction,true);
    assert.equal(words.every(item=>item.meanings.length === 1),true);
    assert.equal(peak,8); assert.deepEqual(progress,[[8,9],[9,9]]);
    assert.equal(await h.loadEstimationVocabulary(config),words); assert.equal(loads,9);
    assert.equal((await h.loadSpeechSourceFrequency(config,{detached:true})).values.form0,100);
    const examples = await h.loadEstimationExamples(config,[1]);
    assert.equal(examples['0'].m[0][0].target,'Target sentence');
    assert.equal(h._cachedJoinedIndex,activeIndex); assert.equal(h._cachedJoinedIndexPath,'artist/index.json');
    assert.equal(h._cachedExamplesData,activeExamples); assert.equal(h._cachedExamplesDataPath,'artist/examples.json');

    const retry = createHarness(); let fail = true;
    retry.fetch = async url => {
        if (url.endsWith('vocabulary.index.manifest.json')) return {ok:false,status:404};
        if (fail) return {ok:false,status:503};
        return {ok:true,json:async()=>[{id:'word',word:'word',rank:1,meanings:[]}]};
    };
    await assert.rejects(retry.loadEstimationVocabulary({indexPath:'other/index.json'}));
    fail=false;
    assert.equal((await retry.loadEstimationVocabulary({indexPath:'other/index.json'})).length,1);
    const incomplete = createHarness();
    incomplete.fetch = async url => {
        if (url.endsWith('vocabulary.index.manifest.json')) return {ok:true,json:async()=>({columns:'columns.json',shards:[{path:'rows.json'}]})};
        if (url.endsWith('columns.json')) return {ok:true,json:async()=>({n:2,id:['a','b'],word:['a','b'],rank:[1,2]})};
        return {ok:true,json:async()=>({a:{meanings:[]}})};
    };
    await assert.rejects(incomplete.loadEstimationVocabulary({indexPath:'partial/index.json'}), /incomplete/);

    console.log('Detached metadata, bounded loading, frequency matching, lazy examples and retry checks passed.');
})().catch(error=>{console.error(error);process.exitCode=1;});
