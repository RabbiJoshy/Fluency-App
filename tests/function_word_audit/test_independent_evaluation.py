import json,sys,unittest
from copy import deepcopy
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'research/function_word_audit'))
from independent_evaluate import assess
from independent_sample import OUT,normalized

class IndependentEvaluationTests(unittest.TestCase):
    def candidate(self):
        row={'result':{'status':'candidate','pattern':0,'chunks':[{'slot':'connector','text':'que'}]}}
        review={'pattern_indices':[0],'expected_chunks':[{'slot':'connector','text':'que'}], 'naturalness':'pass','translation':'pass','standalone_teaching':'pass'}
        return row,review
    def test_every_quality_gate_is_required(self):
        row,review=self.candidate()
        self.assertEqual(assess(row,review)['route'],'reviewed_ready')
        for field in ('naturalness','translation','standalone_teaching'):
            for verdict in ('hold','fail'):
                changed=deepcopy(review);changed[field]=verdict
                self.assertEqual(assess(row,changed)['route'],'review_required')
    def test_disagreements_never_auto_accept(self):
        row,review=self.candidate();review['pattern_indices']=[1]
        self.assertEqual(assess(row,review)['pattern_fit'],'unsupported')
        row,review=self.candidate();review['expected_chunks'].append({'slot':'c','text':'a statement'})
        self.assertEqual(assess(row,review)['route'],'review_required')
    def test_supported_abstention_remains_unassigned(self):
        _,review=self.candidate()
        result=assess({'result':{'status':'abstain','reason':'uncertain'}},review)
        self.assertEqual(result['route'],'unassigned');self.assertEqual(result['pattern_fit'],'missed')
    def test_frozen_sample_balance_and_separation(self):
        from collections import Counter
        sample=json.loads((OUT/'sample.json').read_text())
        self.assertEqual(len(sample['rows']),48)
        self.assertEqual(set(Counter((r['language'],r['word']) for r in sample['rows']).values()),{4})
        old=json.loads((OUT.parent/'function-word-labels/findings.json').read_text())['rows']
        self.assertFalse({normalized(r['sentence']) for r in old}&{normalized(r['sentence']) for r in sample['rows']})
        for row in sample['rows']:
            start,end=row['spans'][0]
            self.assertEqual(row['sentence'][start:end].casefold(),row['word'])
            self.assertTrue(row['source']['attribution'])
        self.assertFalse(any('holdout' in p or 'gold-' in p for p in sample['input_hashes']))
    def test_queue_is_complete_and_source_preserving(self):
        evaluation=json.loads((OUT/'evaluation.json').read_text())['rows']
        sample={r['example_id']:r for r in json.loads((OUT/'sample.json').read_text())['rows']}
        self.assertEqual(set(sample),{r['example_id'] for r in evaluation})
        for row in evaluation:
            for key in ('sentence','translation','source'):self.assertEqual(row[key],sample[row['example_id']][key])
            self.assertEqual(row['assessment'],assess(row,row['review']))
