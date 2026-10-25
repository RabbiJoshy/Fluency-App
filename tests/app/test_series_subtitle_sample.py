"""Precision-first subtitle acceptance and release fitting."""
import importlib.util
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location('series_sample', ROOT / 'scripts/audit_series_subtitle_sample.py')
sample = importlib.util.module_from_spec(spec)
spec.loader.exec_module(sample)


def cue(i, text, shift=0):
    return {'start_ms': i * 4000 + shift, 'end_ms': i * 4000 + 2000 + shift, 'spanish': text}


class SeriesSubtitleSampleTests(unittest.TestCase):
    def test_global_offset_requires_both_boundaries(self):
        es = [cue(i, 'Hola profesor todo listo.') for i in range(40)]
        en = [cue(i, 'Hello professor all ready.', 43000) for i in range(40)]
        fit = sample.fit_episode(es, en)
        self.assertEqual(fit['offset_ms'], 43000)
        self.assertEqual(fit['scale'], 1)
        self.assertEqual(fit['tight_boundary_support'], 40)
        groups = sample.accepted_groups(es, en, fit)
        self.assertEqual(len(groups), 38)
        self.assertEqual(groups[0]['spanish_start'], 1)
        self.assertEqual(groups[-1]['spanish_end'], 39)
        for first, second in zip(groups, groups[1:]):
            self.assertLessEqual(first['english_end'], second['english_start'])

    def test_low_episode_support_rejects_all_examples(self):
        es = [cue(i, 'Hola profesor todo listo.') for i in range(40)]
        en = [cue(i, 'Hello professor all ready.') for i in range(40)]
        self.assertEqual(sample.accepted_groups(es, en, {'scale': 1, 'offset_ms': 0,
                                                       'tight_boundary_support': 10}), [])

    def test_isolated_coincidences_do_not_become_examples(self):
        es = [cue(i, 'Hola profesor todo listo.') for i in range(40)]
        en = [cue(i, 'Hello professor all ready.') for i in (0, 20, 39)]
        self.assertEqual(sample.accepted_groups(es, en, {'scale': 1, 'offset_ms': 0,
                                                       'tight_boundary_support': 40}), [])

    def test_short_replies_are_not_used_to_raise_coverage(self):
        es = [cue(i, 'Sí, profesor.') for i in range(40)]
        en = [cue(i, 'Yes, professor.') for i in range(40)]
        self.assertEqual(sample.accepted_groups(es, en, sample.fit_episode(es, en)), [])

    def test_correct_starts_with_wrong_ends_are_not_strong_anchors(self):
        es = [cue(i, 'Hola profesor todo listo.') for i in range(40)]
        en = [dict(cue(i, 'Hello professor all ready.'), end_ms=i * 4000 + 3000) for i in range(40)]
        self.assertEqual(sample.fit_episode(es, en)['tight_boundary_support'], 0)
