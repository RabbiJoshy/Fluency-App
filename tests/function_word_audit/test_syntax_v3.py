import json
import sys
import unittest
from copy import deepcopy
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'research/function_word_audit'))
from syntax_bridge_v3 import decide, OUT

class SyntaxV3Tests(unittest.TestCase):
    def sample(self,word):
        rows=json.loads((OUT/'findings.json').read_text())['rows']
        row=next(r for r in rows if word in r['sentence'] and r['word']=='de')
        cache=json.loads((OUT/'parse-evidence.json').read_text())['rows']
        return row,deepcopy(cache[row['language']+'|de|'+row['example_id']])
    def test_action_span_and_pattern(self):
        for phrase,pattern in [('um jeito de fazer',1),('te impedir de fazer',0)]:
            row,obs=self.sample(phrase);r=decide(row,obs)
            self.assertEqual(r['pattern'],pattern)
            self.assertEqual(r['chunks'][-1]['text'],'fazer isso')
    def test_unknown_governor_and_finite_complement_abstain(self):
        row,obs=self.sample('um jeito de fazer')
        next(w for s in obs['sentences'] for w in s if w['text']=='jeito')['lemma']='dúvida'
        self.assertEqual(decide(row,obs)['status'],'abstain')
        row,obs=self.sample('um jeito de fazer')
        next(w for s in obs['sentences'] for w in s if w['text']=='fazer')['feats']='VerbForm=Fin'
        self.assertEqual(decide(row,obs)['status'],'abstain')
    def test_multiple_occurrences_not_forced(self):
        row,obs=self.sample('um jeito de fazer');obs['spans']*=2
        self.assertEqual(decide(row,obs)['status'],'abstain')
