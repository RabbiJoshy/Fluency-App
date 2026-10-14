import assert from 'node:assert/strict';
import fs from 'node:fs';
import vm from 'node:vm';
import { spawnSync } from 'node:child_process';
import { reviewNextAt, reviewStage, reviewUnresolved, reviewIntervalDays } from '../../../app/js/srs-policy.js';
import { computeSchedule, reconcileProgress, upsertStateStmt, stateToWireWord, stateToWireItem } from '../src/store.js';
const original = '2026-02-01T00:00:00.000Z', migration = '2026-10-28T08:00:00.000Z';
const cases = [
 {correct:1,wrong:0,lastCorrect:original,srsStage:0,migrationReviewAt:migration},
 {correct:3,wrong:2,lastCorrect:original,lastWrong:'2026-01-01T00:00:00.000Z',srsStage:9},
 {correct:1,wrong:2,lastCorrect:original,lastWrong:'2026-03-01T00:00:00.000Z',srsStage:0,migrationReviewAt:migration},
 {correct:1,wrong:0,srsStage:null,migrationReviewAt:migration},
 {correct:0,wrong:0,srsStage:8}, {correct:0,wrong:1,srsStage:0},
 {correct:8,wrong:8,lastCorrect:original,srsStage:3}
];
const policy = fs.readFileSync('app/js/srs-policy.js','utf8').replace(/^export /gm,'');
const progress = fs.readFileSync('app/js/progress.js','utf8');
const sandbox = vm.createContext({Date,Math,Number,spacedRepetitionEnabled:true});
vm.runInContext(policy+'\n'+progress.slice(progress.indexOf('const SRS_DAY_MS'),progress.indexOf('const progressSurfaceById')),sandbox);
for(const p of cases) {
 sandbox.p=p;sandbox.now=Date.parse('2026-10-20T08:00:00.000Z');
 const client=vm.runInContext('getProgressState(p,now)',sandbox), worker=computeSchedule(p);
 assert.equal(worker.unresolved,reviewUnresolved(p)?1:0);
 assert.equal(worker.stage,reviewStage(p));
 assert.equal(client.nextReviewAt, reviewUnresolved(p)?0:Date.parse(worker.dueAt||'')||0);
}
assert.equal(reviewNextAt(cases[0]),Date.parse(migration));
assert.equal(reviewStage(cases[0]),1);
assert.equal(reviewUnresolved(cases[2]),true);
assert.equal(reviewStage(cases[1]),9);
assert.equal(reviewIntervalDays(cases[1]),376);
const prior={correct_count:4,incorrect_count:2,last_correct_at:original,last_incorrect_at:'2026-01-01T00:00:00.000Z',last_seen_at:original,srs_stage:3,migration_review_at:migration};
const old=reconcileProgress(prior,{correct:1,wrong:0,lastCorrect:'2025-01-01T00:00:00.000Z',srsStage:0});
assert.equal(old.correct,4);assert.equal(old.wrong,2);assert.equal(old.srsStage,3);assert.equal(old.migrationReviewAt,migration);
const importRetry=reconcileProgress(prior,{correct:4,wrong:2,lastCorrect:'2026-10-07T00:00:00.000Z',srsStage:4});
assert.equal(importRetry.migrationReviewAt,migration);assert.equal(importRetry.lastCorrect,original);
const newer=reconcileProgress(prior,{correct:4,wrong:3,lastWrong:'2026-10-20T00:00:00.000Z',srsStage:1});
assert.equal(newer.migrationReviewAt,null);assert.equal(computeSchedule(newer).unresolved,1);
let statement;
upsertStateStmt({prepare(sql){return {bind(...values){statement={sql,values};return statement;}};}},{userId:'owner',langCode:'es',itemId:'card',mode:'speech',itemType:'word',correct:4,wrong:2,stage:3,dueAt:migration,unresolved:0,migrationReviewAt:migration});
const row={srs_stage:3,migration_review_at:migration};
assert.equal(stateToWireWord(row).migrationReviewAt,migration);assert.equal(stateToWireItem(row).migrationReviewAt,migration);
// Real SQLite checks schema compatibility, bind arity and stale-write protection.
const python=spawnSync('python3',['-c',`import sqlite3,json,sys,pathlib
x=json.load(sys.stdin);c=sqlite3.connect(':memory:')
c.executescript(pathlib.Path('backend/worker/migrations/0002_events_and_state.sql').read_text())
c.executescript(pathlib.Path('backend/worker/migrations/0004_delta_sync.sql').read_text())
c.executescript(pathlib.Path('backend/worker/migrations/0009_migration_review_date.sql').read_text())
c.execute(x['sql'],x['values'])
before=c.execute('SELECT * FROM item_state').fetchall()
x['values'][9]=1;x['values'][10]=0
c.execute(x['sql'],x['values'])
assert c.execute('SELECT * FROM item_state').fetchall()==before
assert c.execute('SELECT migration_review_at FROM item_state').fetchone()[0]=='${migration}'
`],{input:JSON.stringify(statement),encoding:'utf8'});
assert.equal(python.status,0,python.stderr);
console.log('UPKEEP schedule parity, import-date lifecycle, reachable stages and SQLite stale-write checks passed.');
