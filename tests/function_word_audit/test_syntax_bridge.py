import json,sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'research/function_word_audit'))
from syntax_bridge import OUT,decide,render
from check import plain

class SyntaxBridgeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rows=json.loads((OUT/'findings.json').read_text())['rows']
        cls.cache=json.loads((OUT/'parse-evidence.json').read_text())
    def lookup(self,suffix):
        row=next(r for r in self.rows if r['example_id']=='example_'+suffix)
        return row,self.cache['rows'].get(row['language']+'|'+row['word']+'|'+row['example_id'])
    def test_structural_distinctions_and_parser_conflicts(self):
        row,obs=self.lookup('55143d2aa238635349259dc09306b14b')
        self.assertIn('whether',decide(row,obs)['reason'])
        row,obs=self.lookup('7eb389477abd97efa50a86c472508735')
        self.assertEqual(decide(row,obs)['pattern'],0)
        row,obs=self.lookup('1a0c7b5923bc374a6b0df3ec63d95813')
        self.assertEqual(decide(row,obs)['pattern'],0)
        row,obs=self.lookup('4970a72aaaf048e0eb5205e04a6ad6ca')
        self.assertIn('split or merged',decide(row,obs)['reason'])
        row,obs=self.lookup('ee3c9f97393c4de9248214c6bb557439')
        self.assertIn('Time/rate',decide(row,obs)['reason'])
    def test_no_gold_dependence_and_lossless_spans(self):
        for row in self.rows:
            obs=self.cache['rows'].get(row['language']+'|'+row['word']+'|'+row['example_id'])
            result=decide(row,obs)
            changed={**row,'review':{'decision':'arbitrary','chunks':[]},'candidate_patterns':[999]}
            self.assertEqual(result,decide(changed,obs))
            if result['status']=='candidate':
                self.assertEqual(plain(render(row['sentence'],result['chunks'])),row['sentence'])
                self.assertEqual(sum(c['slot']=='connector' for c in result['chunks']),1)
                for c in result['chunks']:self.assertEqual(row['sentence'][c['start']:c['end']],c['text'])
    def test_only_development_inputs_and_explicit_missing_parse(self):
        for path in self.cache['input_hashes']:
            self.assertIn('development',path)
            self.assertNotIn('gold',path)
            self.assertNotIn('holdout',path)
        self.assertEqual(decide(self.rows[0],None)['status'],'abstain')
    def test_trial_preserves_automatic_spans(self):
        trial=json.loads((OUT/'syntax-trial.json').read_text())
        predictions={r['example_id']:r for r in json.loads((OUT/'syntax-findings.json').read_text())['rows']}
        added=[e for words in trial.values() for entry in words.values() for rel in entry['relations'] for e in rel['examples'] if e.get('syntax_bridge_review')]
        self.assertEqual(len(added),6)
        for e in added:
            p=predictions[e['example_id']]
            self.assertEqual(e['targetHTML'],p['targetHTML'])
            self.assertEqual(e['translation'],p['translation'])
