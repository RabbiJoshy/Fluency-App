import assert from 'node:assert/strict';
import fs from 'node:fs';
import vm from 'node:vm';
import {spawnSync} from 'node:child_process';
import {deriveEvents,insertEventStmt} from '../src/store.js';
const operations=new Map(),receipts=new Map(),posts=[];let nextId=0,reply;
const browser=vm.createContext({
 currentUser:{initials:'owner'},GOOGLE_SCRIPT_URL:'https://test.example/',
 navigator:{onLine:false},document:{getElementById:()=>null},
 window:{dispatchEvent(){}},CustomEvent:class{},console,AbortController,
 setTimeout:()=>1,clearTimeout(){},Date,
 localStorage:{getItem:()=>null,setItem(){},removeItem(){}},
 openOfflineDb:async()=>{},dbGetAll:async()=>[],
 dbPut:async(table,row)=>{(table==='operations'?operations:receipts).set(row.id||row.idempotencyKey,structuredClone(row));},
 dbDelete:async(table,id)=>operations.delete(id),makeOperationId:()=>`op-${++nextId}`,
 fetch:async(url,init)=>{const body=JSON.parse(init.body);posts.push(body);if(posts.length===1)return await new Promise(resolve=>reply=()=>resolve({ok:true,json:async()=>({success:true})}));return{ok:true,json:async()=>({success:true})};}
});
const source=fs.readFileSync('app/js/sync-queue.js','utf8').replace(/^import .*;\n/gm,'').replace(/^export /gm,'');
vm.runInContext(source,browser);
// Several offline answers must coalesce in memory as well as durable storage.
await vm.runInContext("sendOrQueue({action:'save',user:'owner',wordId:'es0a',correct:1},'word|a')",browser);
await vm.runInContext("sendOrQueue({action:'save',user:'owner',wordId:'es0a',correct:2},'word|a')",browser);
let queue=await vm.runInContext('inspectQueue()',browser);
assert.equal(queue.length,1);assert.equal(queue[0].payload.correct,2);
assert.equal([...operations.values()][0].payload.correct,2);
// A newer answer during a pending request must survive the old acknowledgement.
browser.navigator.onLine=true;
const flush=vm.runInContext('flushQueue()',browser);
for(let i=0;i<10&&!reply;i++)await new Promise(resolve=>setImmediate(resolve));assert(reply);
await vm.runInContext("sendOrQueue({action:'save',user:'owner',wordId:'es0a',correct:3},'word|a')",browser);
queue=await vm.runInContext('inspectQueue()',browser);assert.equal(queue.length,2);
assert.notEqual(queue[0].idempotencyKey,queue[1].idempotencyKey);
reply();await flush;
assert.deepEqual(posts.map(p=>p.correct),[2,3]);assert.equal(operations.size,0);
assert.equal(vm.runInContext('getPendingCount()',browser),0);
// If the server saved an earlier prefix before a timeout, a coalesced retry
// appends only newly gained answers, even though it uses the same operation ID.
const meta={userId:'owner',itemId:'a',itemType:'word',langCode:'es',language:'spanish',mode:'speech',idempotencyKey:'retry-op'};
const events=[...deriveEvents(null,{correct:1,wrong:1,lastSeen:'2026-10-17T00:00:00Z'},meta),
 ...deriveEvents({correct_count:1,incorrect_count:1},{correct:3,wrong:2,lastSeen:'2026-10-17T01:00:00Z'},meta)];
assert.equal(new Set(events.map(e=>e.idempotencyKey)).size,5);
assert.equal(deriveEvents({correct_count:3,incorrect_count:2},{correct:3,wrong:2},meta).length,0);
const statements=[];for(const event of [...events,...events])insertEventStmt({prepare(sql){return{bind(...args){statements.push({sql,args});}}}},event);
const py=`import sqlite3,json,sys,pathlib\nc=sqlite3.connect(':memory:');c.executescript(pathlib.Path('backend/worker/migrations/0002_events_and_state.sql').read_text())\nfor x in json.load(sys.stdin):c.execute(x['sql'],x['args'])\nassert c.execute('SELECT count(*) FROM review_events').fetchone()[0]==5\nassert c.execute(\"SELECT count(*) FROM review_events WHERE outcome='correct'\").fetchone()[0]==3`;
const result=spawnSync('python3',['-c',py],{input:JSON.stringify(statements),encoding:'utf8'});assert.equal(result.status,0,result.stderr);
console.log('Offline coalescing, in-flight answers, prefix retries and real SQLite event deduplication passed.');
