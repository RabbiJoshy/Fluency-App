import json
from pathlib import Path
import subprocess
import sys
import unittest

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'research/function_word_audit'))
from check import scan, markup_errors, count_words
from pilot import build
from discover import normalise, inventory


def suite(target="<span class='fw-token-connector'>É</span> café.", translation='It is coffee.'):
    return {'pt': {'é': {'relations': [dict(tag='A word',formulaHTML="<span class='fw-token-connector'>é</span>",rule='Links words.',examples=[dict(targetHTML=target,translation=translation)])]}}}


class AuditTests(unittest.TestCase):
    def test_accents_and_markup_are_not_extra_words(self):
        self.assertEqual(count_words("<span class='fw-token-v'>Nós</span> não saímos daqui."),4)
        self.assertEqual(scan(suite()),[])

    def test_jargon_and_thresholds(self):
        data=suite();r=data['pt']['é']['relations'][0]
        r['rule']=' '.join(['word']*20)
        self.assertNotIn('long_rule',[f['code'] for f in scan(data)])
        r['rule']+=' clitic'
        codes={f['code'] for f in scan(data)}
        self.assertTrue({'jargon','long_rule'}<=codes)
        r['examples'][0]['targetHTML']="<span class='fw-token-connector'>É</span> "+' '.join(['café']*15)
        self.assertIn('long_sentence',[f['code'] for f in scan(data)])
        self.assertNotIn('long_sentence',[f['code'] for f in scan(data,sentence_limit=16)])

    def test_missing_translation_and_duplicate_identity(self):
        data=suite(translation=' ');r=data['pt']['é']['relations'][0]
        r['examples'].append(dict(r['examples'][0]))
        findings=scan(data)
        duplicate=next(f for f in findings if f['code']=='duplicate_example')
        self.assertEqual((duplicate['language'],duplicate['word'],duplicate['pattern'],duplicate['example']),('pt','é',0,1))
        self.assertEqual(sum(f['code']=='missing_translation' for f in findings),2)

    def test_malformed_and_unsafe_highlights(self):
        for text in ["<span class='fw-token-connector'>de", "de</span>", "<span class='unknown'>de</span>",
                     "<span class='fw-token-connector'></span>", "<span class='fw-token-connector' onclick='x()'>de</span>",
                     "<span class='fw-token-connector'><span class='fw-token-c'>de</span></span>", '<script>x()</script>', '<span']:
            with self.subTest(text=text): self.assertTrue(markup_errors(text))

    def test_duplicate_scope_preserves_language_and_word(self):
        data=suite();data['es']=data['pt']
        self.assertNotIn('duplicate_example',[f['code'] for f in scan(data)])

    def test_pilot_coverage_provenance_and_anchor(self):
        originals,proposals,ledger=build()
        self.assertEqual(sum(len(d) for d in proposals.values()),12)
        self.assertEqual(sum(len(e['relations']) for d in proposals.values() for e in d.values()),24)
        self.assertEqual(sum(r['example'] is not None for r in ledger),121)
        self.assertEqual(scan(proposals),[])
        for row in ledger:
            if row['example'] is not None and row['before']['source']!=row['after']['source']:
                self.assertEqual(row['after']['source'],'Original teaching example · Function-word pilot')
        for data in proposals.values():
            for entry in data.values():
                for r in entry['relations']:
                    self.assertEqual(r['targetHTML'],r['examples'][0]['targetHTML'])
                    self.assertEqual(r['translation'],r['examples'][0]['translation'])

    def test_discovery_normalisation_preserves_distinctions(self):
        self.assertEqual(normalise('  NÓS '),'nós')
        self.assertNotEqual(normalise('nos'),normalise('nós'))
        self.assertNotEqual(normalise('el'),normalise('él'))
        self.assertIn('àqueles',inventory(ROOT/'research/cascade/trouble-words/labeller_pt.py'))

    def test_cli_outputs_valid_json_without_mutation(self):
        paths=[ROOT/f'app/data/grammar-words/{l}.json' for l in ('es','pt')]
        before=[p.read_bytes() for p in paths]
        run=subprocess.run([sys.executable,str(ROOT/'research/function_word_audit/check.py'),'--format','json'],check=True,text=True,capture_output=True)
        self.assertTrue(json.loads(run.stdout))
        self.assertEqual(before,[p.read_bytes() for p in paths])


if __name__=='__main__': unittest.main()
