import datetime,importlib.util,json,sqlite3,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
spec=importlib.util.spec_from_file_location('migration',ROOT/'scripts/prepare_progress_migration.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
class ProgressMigrationTests(unittest.TestCase):
    def row(self,**overrides):
        d={'user_id':'owner','lang_code':'es','item_id':'a','mode':'speech','item_type':'word','parent_id':'','language':'spanish','source':'speech','label':'test','correct_count':1,'incorrect_count':0,'first_seen_at':'','last_seen_at':'2026-10-10T00:00:00.000Z','last_correct_at':'2026-10-10T00:00:00.000Z','last_incorrect_at':'','srs_stage':4,'due_at':None,'unresolved':0,'updated_at':'2026-10-10T00:00:00.000Z'};d.update(overrides);return d
    def test_category_rules(self):
        for values,expected in [({},'known_once'),({'correct_count':3,'incorrect_count':2,'last_incorrect_at':'2026-10-01T00:00:00Z'},'known_multiple'),({'incorrect_count':1,'last_incorrect_at':'2026-10-12T00:00:00Z'},'practice'),({'correct_count':0,'incorrect_count':0},'new'),({'correct_count':0,'incorrect_count':1,'last_correct_at':''},'practice'),({'correct_count':2,'incorrect_count':4,'last_correct_at':'','last_incorrect_at':''},'known_multiple')]:
            self.assertEqual(m.classify(self.row(**values)),expected)
    def test_restore_genuine_dates_and_preserve_new_answers(self):
        at=datetime.datetime(2026,10,14,tzinfo=datetime.timezone.utc)
        old=self.row();real=self.row(last_correct_at='2026-02-01T00:00:00.000Z',last_seen_at='',srs_stage=0)
        k=m.key(old);base={k:old};source={k:real}
        p=m.prepare(base,base,source,'owner',at);a=p['changes'][0]['after']
        self.assertEqual(a['last_correct_at'],real['last_correct_at']);self.assertEqual(a['last_seen_at'],'')
        self.assertEqual(a['correct_count'],1);self.assertGreater(a['srs_stage'],0)
        self.assertEqual(a['due_at'],'2026-10-28T00:00:00.000Z')
        newer=self.row(correct_count=2,last_correct_at='2026-10-13T23:00:00.000Z')
        p=m.prepare({k:newer},base,source,'owner',at)
        self.assertEqual(p['changes'][0]['after']['last_correct_at'],newer['last_correct_at'])
        self.assertEqual(p['changes'][0]['after']['correct_count'],2)
        with self.assertRaises(AssertionError):m.prepare({k:self.row(migration_review_at='2026-10-28T00:00:00Z')},base,source,'owner',at)
    def test_guarded_sql_does_not_overwrite_post_preview_answer(self):
        c=sqlite3.connect(':memory:');c.executescript((ROOT/'backend/worker/migrations/0002_events_and_state.sql').read_text());c.executescript((ROOT/'backend/worker/migrations/0004_delta_sync.sql').read_text());c.executescript((ROOT/'backend/worker/migrations/0009_migration_review_date.sql').read_text())
        before=self.row();c.execute('INSERT INTO item_state ('+','.join(before)+') VALUES ('+','.join('?' for _ in before)+')',list(before.values()))
        k=m.key(before);p=m.prepare({k:before},{k:before},{},'owner',datetime.datetime(2026,10,14,tzinfo=datetime.timezone.utc))
        c.execute("UPDATE item_state SET correct_count=2,last_correct_at='2026-10-14T01:00:00.000Z'")
        c.executescript(m.sql(p));r=c.execute('SELECT correct_count,last_correct_at,migration_review_at FROM item_state').fetchone()
        self.assertEqual(r,(2,'2026-10-14T01:00:00.000Z',None))
