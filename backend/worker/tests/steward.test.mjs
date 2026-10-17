import assert from 'node:assert/strict';
import fs from 'node:fs';
import vm from 'node:vm';
import { generateKeyPair, SignJWT } from 'jose';
import { accountPermissions } from '../../../app/js/account-permissions.js';
import { authorizeProgress } from '../src/session-auth.js';
const accounts = {
 admin: 'clerk_user_3KkMOyRxK2i4qZlXgT5VHJRmNTT',
 joshua: 'clerk_user_3KdfOQ19QCngxtBsj0NsX3qlMjl',
 jp: 'clerk_user_3KllLK7ajq5RWtvjlNdrCH2PTLk',
 diego: 'clerk_user_3Kgzy4F3Q9I6f2hcx7SlxSXjjgv'
};
const {privateKey,publicKey}=await generateKeyPair('RS256');
for (const environment of ['production','staging']) {
 const env={CLERK_ISSUER:'https://example.clerk.accounts.dev',CLERK_ORIGIN:'https://example.com',CLERK_ENVIRONMENT:environment};
 for (const [role,id] of Object.entries(accounts)) {
  const identity=(environment==='staging'?'stg_':'')+id;
  const token=await new SignJWT({sub:id.slice('clerk_'.length),sid:'sess_test',azp:env.CLERK_ORIGIN})
   .setProtectedHeader({alg:'RS256'}).setIssuer(env.CLERK_ISSUER).setIssuedAt().setNotBefore('0s').setExpirationTime('2m').sign(privateKey);
  const req=new Request('https://example.com',{headers:{Authorization:`Bearer ${token}`}});
  const authorize=p=>authorizeProgress(req,p,env,publicKey);
  await authorize({action:'load',user:identity});
  await authorize({action:'account',name:'SafariMS'}); // A name cannot elevate a learner.
  for(const action of ['save','bulkSave','delete']) {
   const p={action,sheet:'FlaggedWords',user:identity};
   if(role==='diego')await assert.rejects(authorize(p),e=>e.status===403);else await authorize(p);
  }
  const nested={action:'bulkSave',rows:[{sheet:'FlaggedWords',user:identity}]};
  if(role==='diego')await assert.rejects(authorize(nested),e=>e.status===403);else await authorize(nested);
  if(role==='admin')await authorize({action:'dump'});else await assert.rejects(authorize({action:'dump'}),e=>e.status===403);
  await assert.rejects(authorize({action:'save',sheet:'FlaggedWords',user:identity+'spoof'}),e=>e.status===403);
  assert.equal(accountPermissions(identity).isAdmin,role==='admin');
  assert.equal(accountPermissions(identity).isJp,role==='jp');
 }
}
for(const id of ['SafariMS','safari','JP','JST','JSTA','Joshua', 'clerk_user_fake'])assert.equal(accountPermissions(id).canFlag,false);
// Exercise the real frontend role helpers, including sign-out / guest behavior.
const auth=fs.readFileSync('app/js/auth.js','utf8');
const ctx=vm.createContext({accountPermissions,currentUser:null,window:{}});
vm.runInContext(auth.slice(auth.indexOf('function userPermissions'),auth.indexOf('function createFlagId')),ctx);
for(const [role,id]of Object.entries(accounts)){
 ctx.currentUser={initials:id,name:'SafariMS'};
 assert.equal(vm.runInContext('isAuditAccount()',ctx),role==='admin');
 assert.equal(vm.runInContext('canUserFlag()',ctx),role!=='diego');
 ctx.currentUser.isGuest=true;assert.equal(vm.runInContext('canUserFlag()',ctx),false);
}
ctx.currentUser=null;assert.equal(vm.runInContext('isAuditAccount()',ctx),false);
// Regress the actual bug: meaning #2, cycled example #2 must not report meaning #1/example #1.
const modal=fs.readFileSync('app/js/flashcards-modals.js','utf8');
const example={id:'visible-2',spanish:'Visible sentence',english:'Visible translation',assignment_method:'tested',source_record_id:'record-2'};
const card={fullId:'es0card',targetWord:'prueba',meanings:[{sense_id:'sense-1',meaning:'First',allExamples:[{spanish:'Wrong first example'}]},{sense_id:'sense-2',meaning:'Second',pos:'noun',allExamples:[{spanish:'Hidden first example'}]}]};
const sent=[];
const ui=vm.createContext({window:{canUserFlag:()=>true,_currentDisplayedExample:example,_activeReleaseProvenance:{releaseId:'release-test',runId:'run-test'}},config:{languages:{spanish:{examplesPath:'examples-test.json'}}},selectedLanguage:'spanish',activeArtist:null,currentMeaningIndex:1,currentExampleIndex:1,flashcards:[card],currentIndex:0,document:{getElementById:()=>null},flagWord:async(...args)=>{sent.push(args);return true;},console});
vm.runInContext(modal.slice(modal.indexOf('const FLAG_QUICK_CANONICAL'),modal.indexOf('function _flagActiveDetail')),ui);
vm.runInContext(modal.slice(modal.indexOf('function _flagRunProvenance'),modal.indexOf('function showFlagMenu')),ui);
vm.runInContext('let _simpleFlagBusy=false;function showFlagSentToast(){} function hideFlagMenu(){}\n'+modal.slice(modal.indexOf('function _simpleFlagExample'),modal.indexOf('function _renderSimpleSenses')),ui);
assert.equal(await vm.runInContext("_sendSimpleFlag('wsd')",ui),true);
let [sentCard,path,report,fields]=sent[0];
assert.equal(sentCard.fullId,card.fullId);assert.equal(path,'sense:sense-2:wsd');
assert(report.includes('Visible sentence'));assert(!report.includes('Wrong first example'));
assert.equal(fields.senseId,'sense-2');assert.equal(fields.example,'Visible sentence');
assert.equal(fields.translation,'Visible translation');assert.equal(fields.exampleId,'visible-2');
assert.equal(fields.releaseId,'release-test');assert.equal(fields.runId,'run-test');
assert.equal(fields.sourceRecordId,'record-2');assert.equal(fields.exampleIndex,1);
assert.deepEqual(JSON.parse(fields.exampleJson),example);
// Without the display cache, select the actual cycled example rather than first.
ui.window._currentDisplayedExample=null;card.meanings[1].allExamples.push(example);
assert.equal(await vm.runInContext("_sendSimpleFlag('wsd')",ui),true);assert.equal(sent[1][3].exampleId,'visible-2');
await vm.runInContext("_sendSimpleFlag('card')",ui);assert.equal(sent[2][3].target,'card');
ui.window.canUserFlag=()=>false;
assert.equal(await vm.runInContext("_sendSimpleFlag('wsd')",ui),false);assert.equal(sent.length,3);
// Test the real Worker upsert against SQLite: a flag ID owned by another user cannot be overwritten.
const worker=fs.readFileSync('backend/worker/src/index.js','utf8');
const match=worker.slice(worker.indexOf('async function saveFlag'),worker.indexOf('async function deleteFlag')).match(/db.prepare\(`([\s\S]*?)`\)/);
assert(match);const {spawnSync}=await import('node:child_process');
const py=`import sqlite3,json,sys\nsql=json.load(sys.stdin)\nc=sqlite3.connect(':memory:')\nc.executescript(open('backend/worker/migrations/0002_events_and_state.sql').read())\nargs=['same-id','owner','2026-10-17','card','word','es','spanish','speech','','','sense','translation','original',None,'{}']\nc.execute(sql,args)\nargs[1]='attacker';args[12]='tampered';c.execute(sql,args)\nassert c.execute('select user_id,note from flags').fetchone()==('owner','original')\nargs[1]='owner';args[12]='owner update';c.execute(sql,args)\nassert c.execute('select note from flags').fetchone()[0]=='owner update'\nprint('Flag ownership retained')`;
const result=spawnSync('python3',['-c',py],{input:JSON.stringify(match[1]),encoding:'utf8'});
assert.equal(result.status,0,result.stderr);
console.log('STEWARD: verified roles in both environments, name spoofing, guest/sign-out, server gates, flag ownership and exact displayed-example capture.');
