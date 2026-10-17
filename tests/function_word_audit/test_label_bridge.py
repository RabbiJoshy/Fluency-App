import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'research/function_word_audit'))
from label_bridge import build,candidate
from check import plain

class LabelBridgeTests(unittest.TestCase):
    def test_does_not_force_broad_or_unrelated_labels(self):
        self.assertEqual(candidate('pt','de',{'kind':'role','value':'prep'})[0],[0,1])
        self.assertEqual(candidate('es','que',{'kind':'unit','value':'tener que','rule':'tener_que'})[0],[])
        self.assertEqual(candidate('pt','nos',{})[0],[])
        self.assertIn('whether',candidate('pt','se',{'kind':'role','value':'conj_if'})[1])
        self.assertEqual(candidate('es','al',{'kind':'unit','value':'al + infinitive','rule':'temporal_infinitive'})[0],[1])
    def test_only_reviewed_fresh_examples_enter_trial(self):
        rows,trial=build()
        self.assertEqual(len(rows),334)
        self.assertEqual(sum(bool(r['review']) for r in rows),24)
        added={e['example_id']:e for words in trial.values() for entry in words.values() for rel in entry['relations'] for e in rel['examples'] if e.get('label_bridge_review')}
        self.assertEqual(len(added),13)
        for r in rows:
            if r['example_id'] in added:
                self.assertFalse(r['already_in_pilot'])
                self.assertEqual(r['review']['decision'],'accept')
                self.assertEqual(plain(added[r['example_id']]['targetHTML']),r['sentence'])
                self.assertEqual(added[r['example_id']]['translation'],r['translation'])
                self.assertEqual(added[r['example_id']]['metadata']['source'],r['source'])
