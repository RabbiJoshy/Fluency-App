"""Cached Portuguese development regressions, not independent accuracy claims."""
import copy
import importlib.util
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location('syntax_assignment_pt', ROOT / 'research/function_word_audit/syntax_assignment_pt.py')
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)
DECIDE = MODULE.decide_pt
BASE = ROOT / 'docs/audits/function-word-independent'
ROWS = json.loads((BASE / 'predictions.json').read_text())['rows']
PARSES = json.loads((BASE / 'parses.json').read_text())['rows']


def case(suffix):
    row = next(r for r in ROWS if r['example_id'].endswith(suffix))
    return copy.deepcopy(row), copy.deepcopy(PARSES[row['example_id']])


class PortugueseRecoveryTests(unittest.TestCase):
    def check_chunks(self, row, result):
        previous = 0
        for chunk in result['chunks']:
            self.assertGreaterEqual(chunk['start'], previous)
            self.assertEqual(chunk['text'], row['sentence'][chunk['start']:chunk['end']])
            previous = chunk['end']

    def test_four_shared_token_demonstrative_contractions(self):
        for suffix, noun in [('803eb8a7ea', 'momento'), ('96ebdf87e', 'idioma'),
                             ('cc73bd6', 'momento'), ('2b3e2e9b', 'corredor')]:
            row, obs = case(suffix)
            result = DECIDE(row, obs)
            self.assertEqual((result['status'], result['pattern']), ('candidate', 0))
            self.assertEqual(result['chunks'][-1]['text'], noun)
            self.check_chunks(row, result)

    def test_nos_time_phrase_retains_modifiers(self):
        row, obs = case('388fff51')
        result = DECIDE(row, obs)
        self.assertEqual((result['status'], result['pattern']), ('candidate', 1))
        self.assertEqual(result['chunks'][-1]['text'], 'últimos 2 meses')
        self.check_chunks(row, result)

    def test_merged_adposition_representation(self):
        row, obs = case('388fff51')
        sentence = obs['sentences'][0]
        case_node = next(n for n in sentence if n['text'] == 'em')
        det_id = next(n['id'] for n in sentence if n['token'] == case_node['token'] and n['upos'] == 'DET')
        sentence[:] = [n for n in sentence if n['id'] != det_id]
        case_node['text'] = case_node['lemma'] = 'nos'
        self.assertEqual(DECIDE(row, obs)['status'], 'candidate')

    def test_split_character_contraction_offsets(self):
        row, obs = case('cc73bd6')
        focus = [n for n in obs['sentences'][0] if n['token']['start_char'] == 14]
        focus[0]['token'] = dict(text='n', start_char=14, end_char=15)
        focus[1]['token'] = dict(text='aquele', start_char=15, end_char=21)
        self.assertEqual(DECIDE(row, obs)['status'], 'candidate')

    def test_finite_verb_cannot_be_contraction_head(self):
        row, obs = case('388fff51')
        case_node = next(n for n in obs['sentences'][0] if n['text'] == 'em')
        noun = next(n for n in obs['sentences'][0] if n['id'] == case_node['head'])
        noun.update(upos='VERB', feats='Gender=Masc|Number=Plur|VerbForm=Fin|Person=3')
        self.assertEqual(DECIDE(row, obs)['status'], 'abstain')

    def test_contraction_must_not_swallow_a_finite_verb(self):
        row, obs = case('388fff51')
        modifier = next(n for n in obs['sentences'][0] if n['text'] == 'últimos')
        modifier.update(upos='VERB', deprel='acl', feats='VerbForm=Fin|Person=3|Number=Plur')
        self.assertEqual(DECIDE(row, obs)['status'], 'abstain')

    def test_object_nos_and_reciprocal_are_distinct(self):
        row, obs = case('84613158b')
        result = DECIDE(row, obs)
        self.assertEqual((result['status'], result['pattern']), ('candidate', 0))
        self.assertEqual(result['chunks'][-1]['text'], 'dará')
        self.check_chunks(row, result)
        row, obs = case('233a5c1f')
        self.assertEqual(DECIDE(row, obs)['status'], 'abstain')

    def test_enclitic_shared_verb_span_is_not_preposed(self):
        row, obs = case('29414f60')
        self.assertEqual(DECIDE(row, obs)['status'], 'abstain')

    def test_conditional_climbs_modal_and_keeps_complete_result(self):
        row, obs = case('9d6860e71')
        result = DECIDE(row, obs)
        self.assertEqual((result['status'], result['pattern']), ('candidate', 0))
        self.assertEqual([c['text'] for c in result['chunks']],
                         ['Se', 'ele cooperar e falar', 'podemos seguir essa pista até ao topo'])
        self.check_chunks(row, result)

    def test_embedded_whether_is_not_conditional(self):
        row, obs = case('a02af336')
        self.assertEqual(DECIDE(row, obs)['status'], 'abstain')

    def test_bad_component_head_missing_agreement_and_multiple_focus(self):
        row, obs = case('388fff51')
        det = next(n for n in obs['sentences'][0] if n['upos'] == 'DET' and n['token']['start_char'] == 51)
        det['head'] = 3
        self.assertEqual(DECIDE(row, obs)['status'], 'abstain')
        row, obs = case('388fff51')
        next(n for n in obs['sentences'][0] if n['text'] == 'meses')['feats'] = None
        self.assertEqual(DECIDE(row, obs)['status'], 'abstain')
        row, obs = case('388fff51')
        obs['spans'].append(obs['spans'][0])
        self.assertEqual(DECIDE(row, obs)['status'], 'abstain')

    def test_other_words_use_frozen_fallback(self):
        row, obs = case('6e30683d')
        self.assertIsNone(DECIDE(row, obs))


if __name__ == '__main__':
    unittest.main()
