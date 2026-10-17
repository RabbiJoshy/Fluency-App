import json
import sys
import unittest
from pathlib import Path
from copy import deepcopy
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'research/function_word_audit'))
from syntax_bridge_v2 import decide, render, OUT
from check import plain

class SyntaxV2Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rows=json.loads((OUT/'findings.json').read_text())['rows']
        cls.cache=json.loads((OUT/'parse-evidence.json').read_text())['rows']
    def lookup(self,sentence):
        row=next(r for r in self.rows if r['sentence']==sentence)
        return row,deepcopy(self.cache[row['language']+'|'+row['word']+'|'+row['example_id']])
    def test_full_verb_and_modal_spans(self):
        for sentence,expected in [
            ('Jamás se ha echado para atrás en situaciones difíciles.','ha echado para atrás'),
            ('Encontra alguém que se possa mover no mundo dele.','possa mover')]:
            row,obs=self.lookup(sentence)
            self.assertIn(expected,[c['text'] for c in decide(row,obs)['chunks']])
    def test_noun_modifier_ambiguity_is_not_truncated(self):
        row,obs=self.lookup('Nós precisamos de mais pessoas como você.')
        self.assertEqual(decide(row,obs)['status'],'abstain')
        # When the parser actually links the comparison to the noun, retain it.
        node=next(w for w in obs['sentences'][0] if w['text']=='você')
        node.update(head=5,deprel='nmod')
        self.assertIn('mais pessoas como você',[c['text'] for c in decide(row,obs)['chunks']])
    def test_semantic_and_parser_conflicts_stay_unassigned(self):
        for sentence in ('El número de minas navales no coincide.','O mau tempo nos impediu de sair.','Nos dê algumas horas.'):
            row,obs=self.lookup(sentence)
            self.assertEqual(decide(row,obs)['status'],'abstain')
    def test_modal_complement_and_destination(self):
        for sentence,pattern in [('Bueno, creo que debes ir a por ello.',0),('Se apresuró para subir al autobús.',0)]:
            row,obs=self.lookup(sentence)
            self.assertEqual(decide(row,obs)['pattern'],pattern)
    def test_all_spans_preserve_source(self):
        for row in self.rows:
            result=decide(row,self.cache.get(row['language']+'|'+row['word']+'|'+row['example_id']))
            if result['status']=='candidate':
                self.assertEqual(plain(render(row['sentence'],result['chunks'])),row['sentence'])
    def test_overlay_only_contains_explicit_approvals(self):
        overlay=json.loads((ROOT/'app/data/grammar-words/syntax-trial.json').read_text())
        examples=[e for words in overlay.values() for patterns in words.values() for group in patterns.values() for e in group]
        self.assertEqual(len(examples),8)
        predictions={r['example_id']:r for r in json.loads((OUT/'syntax-v2-findings.json').read_text())['rows']}
        for ex in examples:
            self.assertEqual(ex['targetHTML'],predictions[ex['example_id']]['targetHTML'])
            self.assertTrue(ex['metadata']['source']['source_record_id'])
            self.assertTrue(ex['syntax_trial_review'])
