"""Grouped subtitle alignment must preserve complete, disjoint examples."""
import importlib.util
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location('casa_alignment', ROOT / 'scripts/audit_casa_bilingual_alignment.py')
alignment = importlib.util.module_from_spec(spec)
spec.loader.exec_module(alignment)


def cue(start, end, text):
    return {'start_ms': start, 'end_ms': end, 'spanish': text}


class CasaBilingualAlignmentTests(unittest.TestCase):
    def test_two_spanish_cues_get_one_complete_translation(self):
        es = [cue(1000, 2000, 'Berlín, ha pasado algo...'), cue(2200, 3500, 'Grave.')]
        en = [cue(1000, 3500, 'Berlin, something serious happened.')]
        groups = alignment.align_groups(es, en)
        self.assertEqual(len(groups), 1)
        self.assertEqual((groups[0]['spanish_start'], groups[0]['spanish_end']), (0, 2))
        self.assertEqual(groups[0]['spanish'], 'Berlín, ha pasado algo... Grave.')
        self.assertEqual(groups[0]['english'], en[0]['spanish'])
        self.assertEqual(groups[0]['status'], 'timing-candidate')

    def test_one_spanish_cue_can_use_two_english_cues(self):
        es = [cue(1000, 3500, 'No me preguntes por qué.')]
        en = [cue(1000, 2000, 'Do not ask me'), cue(2200, 3500, 'why.')]
        groups = alignment.align_groups(es, en)
        self.assertEqual(groups[0]['english'], 'Do not ask me why.')
        self.assertEqual(groups[0]['english_end'], 2)

    def test_missing_cue_does_not_shift_later_pairs(self):
        es = [cue(1000, 2000, 'Uno.'), cue(3000, 4000, 'Missing.'), cue(9000, 10000, 'Dos.')]
        en = [cue(1000, 2000, 'One.'), cue(9000, 10000, 'Two.')]
        groups = alignment.align_groups(es, en)
        self.assertEqual([g['spanish'] for g in groups], ['Uno.', 'Dos.'])
        self.assertEqual([g['english_start'] for g in groups], [0, 1])

    def test_no_group_over_long_silence(self):
        es = [cue(1000, 2000, 'Hola.'), cue(12000, 14000, 'Adiós.')]
        en = [cue(1000, 14000, 'Hello and goodbye.')]
        self.assertEqual(alignment.align_groups(es, en), [])

    def test_no_english_reuse_or_crossing_groups(self):
        es = [cue(1000, 2000, 'Uno.'), cue(2200, 3500, 'Dos.'), cue(5000, 6000, 'Tres.')]
        en = [cue(1000, 3500, 'One. Two.'), cue(5000, 6000, 'Three.')]
        groups = alignment.align_groups(es, en)
        self.assertEqual(len(groups), 2)
        for first, second in zip(groups, groups[1:]):
            self.assertLessEqual(first['spanish_end'], second['spanish_start'])
            self.assertLessEqual(first['english_end'], second['english_start'])

    def test_timing_jumps_require_many_supporting_cues(self):
        es = [cue(w + i * 8000, w + i * 8000 + 2000, str(i))
              for w in (0, 300000) for i in range(12)]
        en = [dict(c, start_ms=c['start_ms'] + (950 if i >= 12 else 0),
                   end_ms=c['end_ms'] + (950 if i >= 12 else 0)) for i, c in enumerate(es)]
        offsets, evidence = alignment.local_offsets(es, en, 0)
        self.assertEqual(offsets, [0] * 12 + [950] * 12)
        groups = alignment.align_groups(es, en, offsets=offsets)
        self.assertEqual(sum(g['spanish_end'] - g['spanish_start'] for g in groups), 24)
        self.assertEqual(sum(e['adjusted'] for e in evidence), 1)
        offsets, _ = alignment.local_offsets(es[:1], [cue(950, 2950, 'One.')], 0)
        self.assertEqual(offsets, [0])

    def test_fragment_coverage_is_reported_as_expanded_context(self):
        group = {'spanish': 'Hola. Adiós.', 'english': 'Hello. Goodbye.'}
        deck = {'surfaces': {'hola': {'lines': [{'song': 'S01E01', 'text': 'Hola.'}]},
                             'otro': {'lines': [{'song': 'S01E01', 'text': 'Otro.'}]}}}
        result = alignment.measure_examples(deck, {('S01E01', 'Hola.'): group}, set())
        self.assertEqual(result['examples'], 2)
        self.assertEqual(result['grouped_examples'], 1)
        self.assertEqual(result['expanded_examples'], 1)
        self.assertEqual(result['cards_with_translation_candidate'], 1)

    def test_invalid_timestamps_and_out_of_sync_sources_rejected(self):
        with self.assertRaises(ValueError):
            alignment.align_groups([cue(2000, 1000, 'Bad.')], [])
        self.assertEqual(alignment.align_groups([cue(0, 1000, 'Hola.')],
                                               [cue(5000, 6000, 'Hello.')]), [])
