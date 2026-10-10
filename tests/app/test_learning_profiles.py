"""Profile collision handling, legacy progress preservation and birth-date limits."""
from pathlib import Path
import shutil
import subprocess
import unittest
ROOT = Path(__file__).resolve().parents[2]

@unittest.skipUnless(shutil.which('node'), 'Node.js required')
class LearningProfileTests(unittest.TestCase):
    def run_node(self, source):
        result = subprocess.run(['node','--input-type=module','-'],cwd=ROOT,input=source,text=True,capture_output=True)
        self.assertEqual(result.returncode,0,result.stderr)

    def test_client_identity_and_fields(self):
        self.run_node(r'''
import assert from 'node:assert/strict';
import {birthdayValue,optionalBirthdayValue,userForProfile,profileContext} from './app/js/learning-profiles.js';
assert.equal(birthdayValue(29,2),'02-29');
assert.equal(optionalBirthdayValue('',''),'');
assert.equal(optionalBirthdayValue('29','2'),'02-29');
for (const [day,month] of [['29',''],['','2'],['30','2']]) assert.throws(()=>optionalBirthdayValue(day,month));
for (const [day,month] of [[30,2],[31,4],[0,1],[1,13],[1.5,1],['','']]) assert.equal(birthdayValue(day,month),'');
const first=userForProfile({id:'profile_a',name:'Josh',birthday:'10-08'});
const second=userForProfile({id:'profile_b',name:'Josh',birthday:'10-08'});
assert.notEqual(first.initials,second.initials);
assert.equal(first.username,second.username);
assert.equal(userForProfile({id:'JST',name:'JST',legacy:true,birthday:'10-08'}).initials,'JST');
assert(profileContext({languages:['spanish'],lastStudied:'2026-10-01T12:00:00Z',legacy:true}).includes('spanish'));
''')

    def test_directory_against_sqlite(self):
        self.run_node(r'''
import assert from 'node:assert/strict';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import {execFileSync} from 'node:child_process';
import {lookupProfiles,createProfile,claimLegacyProfile,profileFields} from './backend/worker/src/profiles.js';
const temp=fs.mkdtempSync(path.join(os.tmpdir(),'learning-profiles-'));
const dbPath=path.join(temp,'profiles.sqlite');
const execute=(sql,args=[],script=false)=>JSON.parse(execFileSync('python3',['-c',`
import sqlite3,json,sys
c=sqlite3.connect(sys.argv[1]);c.row_factory=sqlite3.Row
sql,args,script=json.loads(sys.argv[2])
if script:c.executescript(sql);rows=[]
else:
 cursor=c.execute(sql,args);rows=[dict(row) for row in cursor.fetchall()]
c.commit();print(json.dumps(rows))
`,dbPath,JSON.stringify([sql,args,script])],{encoding:'utf8'}));
execute(`CREATE TABLE users(user_id TEXT PRIMARY KEY);CREATE TABLE item_state(user_id TEXT,language TEXT,last_seen_at TEXT);
INSERT INTO users VALUES ('JST');INSERT INTO item_state VALUES('JST','spanish','2026-10-01T12:00:00Z');`
+fs.readFileSync('backend/worker/migrations/0006_learning_profiles.sql','utf8')
+fs.readFileSync('backend/worker/migrations/0007_unique_profile_names.sql','utf8'),[],true);
const db={prepare(sql){let args=[];return {bind(...values){args=values;return this;},
 async all(){return {results:execute(sql,args)};},async first(){return execute(sql,args)[0]||null;},async run(){execute(sql,args);}};}};
try {
 assert.throws(()=>profileFields({name:'J',birthday:'02-30'}));
 assert.equal(profileFields({name:'J'}).birthday,'');
 const fields={name:'JST',birthday:'10-08'};
 const legacy=(await lookupProfiles(db,fields)).profiles[0];
 assert.equal(legacy.id,'JST');assert.equal(legacy.legacy,true);assert.equal(legacy.needsLink,true);assert.deepEqual(legacy.languages,['spanish']);
 assert.equal(legacy.lastStudied,'2026-10-01T12:00:00Z');
 await claimLegacyProfile(db,{...fields,id:'JST'});
 assert.equal(execute("SELECT COUNT(*) AS n FROM item_state WHERE user_id='JST'")[0].n,1);
 assert.equal((await lookupProfiles(db,{...fields,birthday:'10-09'})).profiles.length,0);
 await assert.rejects(claimLegacyProfile(db,{...fields,id:'JST',birthday:'10-09'}));
 const a='profile_00000000-0000-4000-8000-000000000001',b='profile_00000000-0000-4000-8000-000000000002';
 // One identity per name, in any case. The claimed legacy profile owns "JST".
 await assert.rejects(createProfile(db,{...fields,id:a}),/already taken/);
 await assert.rejects(createProfile(db,{name:'jst',id:a}),/already taken/);
 // A new name works, and retrying the same ID is idempotent rather than a collision.
 await createProfile(db,{name:'Josh',birthday:'10-08',id:a});
 await createProfile(db,{name:'Josh',birthday:'10-08',id:a});
 assert.equal(execute("SELECT COUNT(*) AS n FROM learning_profiles WHERE name_key='josh'")[0].n,1);
 // Same name in another case, with or without another birthday, is refused.
 await assert.rejects(createProfile(db,{name:'JOSH',birthday:'03-04',id:b}),/already taken/);
 await assert.rejects(createProfile(db,{name:'josh',id:b}),/already taken/);
 await assert.rejects(createProfile(db,{name:'Josh',id:a,birthday:'10-09'}));
 assert.equal(execute("SELECT COUNT(*) AS n FROM learning_profiles")[0].n,2);
 // The database enforces it too, for creates that race past the check.
 assert.throws(()=>execute("INSERT INTO learning_profiles VALUES ('profile_x','josh','josh','','new','2026-10-10')"));
 // A supplied birthday still finds birthday-free profiles.
 const c='profile_00000000-0000-4000-8000-000000000003';
 await createProfile(db,{name:'Ann',id:c});
 const dated=(await lookupProfiles(db,{name:'Ann',birthday:'10-08'})).profiles;
 assert.equal(dated.length,1);assert.equal(dated[0].birthday,'');
 assert.equal((await lookupProfiles(db,{name:'ANN',birthday:'10-09'})).profiles.length,1);
 // An unclaimed legacy identity owns its name until it is claimed.
 execute("INSERT INTO users VALUES ('NEW');INSERT INTO item_state VALUES ('NEW','czech','2026-10-08');",[],true);
 await assert.rejects(createProfile(db,{name:'New',id:b}),/already taken/);
 await claimLegacyProfile(db,{name:'NEW',id:'NEW'});
 const undatedLegacy=(await lookupProfiles(db,{name:'NEW',birthday:'10-08'})).profiles[0];
 assert.equal(undatedLegacy.id,'NEW');assert.equal(undatedLegacy.needsLink,false);
 assert.equal(execute("SELECT COUNT(*) AS n FROM item_state WHERE user_id='NEW'")[0].n,1);
} finally {fs.rmSync(temp,{recursive:true,force:true});}
''')
