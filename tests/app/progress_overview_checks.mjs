import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
const source = await readFile(new URL('../../app/js/progress-overview.js', import.meta.url), 'utf8');
const { summarizeProgress, openProgressOverview, closeProgressOverview } = await import(`data:text/javascript;base64,${Buffer.from(source).toString('base64')}`);
const cards = [
    {id:'known',corpus_count:60,state:{known:true,seen:true},record:{correct:3}},
    {id:'due',corpus_count:20,state:{known:true,seen:true,needsReview:true,isDue:true},record:{correct:2}},
    {id:'mistake',corpus_count:10,state:{seen:true,needsReview:true},record:{wrong:1}},
    {id:'new',corpus_count:10},
];
const methods = {getId:c=>c.id,getState:c=>c.state,getProgress:c=>c.record};
const summary = summarizeProgress([...cards,cards[0]],methods);
assert.deepEqual(summary,{total:4,known:1,practice:2,new:1,due:1,correct:5,wrong:1,coverage:80});
assert.equal(summarizeProgress([],methods).coverage,0);
const granular = summarizeProgress([{id:'sense-due',state:{known:true,seen:true,needsReview:true,reviewReason:'due'}},{id:'sense-wrong',state:{known:true,seen:true,needsReview:true,reviewReason:'incorrect'}}],methods);
assert.equal(granular.due,1);
assert.equal(granular.coverage,50,'An unresolved sense must not count as covered vocabulary');
assert.equal(summarizeProgress([{id:'bad',corpus_count:-1},{id:'nan',corpus_count:'bad'}],methods).new,2);

class Element {
    constructor(id) { this.id=id; this.hidden=false; this.disabled=false; this.textContent=''; this.isConnected=true; this.listeners={}; this.attrs={}; this.classes=new Set(); this.classList={contains:c=>this.classes.has(c),add:c=>this.classes.add(c),remove:c=>this.classes.delete(c),toggle:(c,on)=>on?this.classes.add(c):this.classes.delete(c)}; this.style={setProperty:(k,v)=>this.attrs[k]=v}; }
    addEventListener(k,fn) { (this.listeners[k] ||= []).push(fn); }
    setAttribute(k,v) { this.attrs[k]=v; }
    removeAttribute(k) { delete this.attrs[k]; }
    focus() { document.activeElement=this; }
    getClientRects() { return [{}]; }
    closest() { return null; }
    querySelector(selector) { return elements.get(selector) || new Element(selector); }
    querySelectorAll() { return [elements.get('closeTotalStatsModal'),elements.get('progressRefreshBtn')]; }
    contains(el) { return this.querySelectorAll().includes(el); }
}
const ids=['totalStatsModal','closeTotalStatsModal','progressRefreshBtn','progressOverviewContent','progressOverviewFlag','progressCoverageNote','progressSkippedCard','progressSkippedCount','progressOverviewStatus','totalStatsCoverage','totalStatsCoverageLabel','progressCoverageDescription','progressCoverageRing','totalStatsWords','progressKnownCount','progressPracticeCount','progressNewCount','progressPracticeDetail','progressWordTrack','progressScopeNote','.is-known','.is-practice','.is-new','trigger'];
const elements=new Map(ids.map(id=>[id,new Element(id)]));
globalThis.document={getElementById:id=>elements.get(id),activeElement:elements.get('trigger')};
const modal=elements.get('totalStatsModal');modal.classList.add('hidden');
const options={...methods,source:'Spanish',mode:'Everyday speech',coverageLabel:'Estimated speech coverage',isCurrent:()=>true,canImport:true,loadVocabulary:async()=>cards};
await openProgressOverview(options);
assert.equal(elements.get('totalStatsCoverage').textContent,'80.0%');
assert.equal(elements.get('progressOverviewContent').hidden,false,elements.get('progressOverviewStatus').textContent);
assert.equal(document.activeElement.id,'closeTotalStatsModal');
const keys=modal.listeners.keydown;
keys[0]({key:'Escape',preventDefault(){},stopPropagation(){}});
assert.equal(modal.classList.contains('hidden'),true);
assert.equal(document.activeElement.id,'trigger');

let resolve;
const pending=openProgressOverview({...options,loadVocabulary:()=>new Promise(r=>resolve=r)});
assert.equal(modal.classList.contains('hidden'),false,'Dialog must open before data finishes loading');
closeProgressOverview();resolve(cards);await pending;
assert.equal(modal.classList.contains('hidden'),true,'A late response must not reopen the dialog');

let staleResolve,current=true;
const stale=openProgressOverview({...options,isCurrent:()=>current,loadVocabulary:()=>new Promise(r=>staleResolve=r)});
current=false;staleResolve(cards);await stale;
assert.equal(modal.classList.contains('hidden'),true,'Switching source must discard the previous source response');

let olderResolve;
const older=openProgressOverview({...options,loadVocabulary:()=>new Promise(r=>olderResolve=r)});
await openProgressOverview({...options,loadVocabulary:async()=>[]});
olderResolve(cards);await older;
assert.equal(elements.get('totalStatsCoverage').textContent,'0.0%','An older request must not overwrite a newer snapshot');

const warn=console.warn;console.warn=()=>{};
await openProgressOverview({...options,loadVocabulary:async()=>{throw Error('offline')}});
console.warn=warn;
assert.match(elements.get('progressOverviewStatus').textContent,/could not be loaded/);
assert.equal(elements.get('progressRefreshBtn').disabled,false);
await openProgressOverview({...options,loadVocabulary:async()=>[]});
assert.equal(elements.get('totalStatsCoverage').textContent,'0.0%');
assert.match(elements.get('progressOverviewStatus').textContent,/no study cards/);
assert.equal(elements.get('closeTotalStatsModal').listeners.click.length,1,'Repeated openings must not duplicate handlers');
console.log('Progress calculation and dialog lifecycle checks passed');
