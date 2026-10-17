"""Sampling must not reintroduce reviewed records or depend on file order."""
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT/'research/function_word_audit'))
from fresh_check import select, main


class FreshCheckTests(unittest.TestCase):
    def test_deterministic_stratified_exclusion(self):
        rows = [dict(language='pt', word='de', status=status,
                     example_id=f'{status}-{i}', parser_available=True)
                for status in ('candidate', 'abstain') for i in range(8)]
        rows.append(dict(language='es', word='lo', status='candidate',
                         example_id='unparsed', parser_available=False))
        excluded = {'candidate-0', 'abstain-0'}
        chosen = select(rows, excluded)
        self.assertEqual(chosen, select(list(reversed(rows)), excluded))
        self.assertEqual(len(chosen), 4)
        self.assertFalse({r['example_id'] for r in chosen} & (excluded | {'unparsed'}))
        self.assertEqual(sum(r['status']=='candidate' for r in chosen), 2)

    def test_frozen_replay_and_complete_review(self):
        main()
        report = json.loads((ROOT/'docs/audits/function-word-labels/fresh-check.json').read_text())
        self.assertEqual(report['sample_size'], len(report['rows']))
        self.assertEqual(len({r['example_id'] for r in report['rows']}), report['sample_size'])
        self.assertTrue(all(r['judgment']['reason'] for r in report['rows']))

if __name__ == '__main__':
    unittest.main()
