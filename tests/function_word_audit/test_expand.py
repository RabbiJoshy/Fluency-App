import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'research/function_word_audit'))
from pilot import build
from expand import expand
from check import plain
from slot_review import REVIEW
from formula_copy import DROP_CONTEXT

class ExpansionTests(unittest.TestCase):
    def test_coverage_types_and_unchanged_nonpilot_examples(self):
        originals,pilot,_=build()
        expanded,ledger=expand(originals,pilot)
        self.assertEqual(sum(map(len,expanded.values())),81)
        self.assertEqual(len(ledger),115)
        for lang,words in expanded.items():
            self.assertEqual(set(words),set(originals[lang]))
            self.assertEqual(words['que']['relations'][0]['slotTypes'],{'v':'verb','c':'clause'})
            self.assertEqual(words['que']['relations'][2]['slotTypes']['v'],'phrase')
            for word,entry in words.items():
                for i,r in enumerate(entry['relations']):
                    self.assertTrue(set(r['slotTypes'].values()) <= {'noun','verb','adj','prep','pron','clause','phrase','mixed'})
                    if word not in pilot[lang]:
                        for after,before in zip(r['examples'],originals[lang][word]['relations'][i]['examples']):
                            self.assertEqual(plain(after['targetHTML']),plain(before['targetHTML']))
                            self.assertEqual({k:v for k,v in after.items() if k!='targetHTML'}, {k:v for k,v in before.items() if k!='targetHTML'})
                        self.assertIn('pending',entry['previewReviewStatus'])
        self.assertEqual(expanded['pt']['para']['relations'][1]['slotTypes']['c'],'verb')
        self.assertEqual(expanded['es']['yo']['relations'][0]['slotTypes']['v'],'verb')
        self.assertNotIn('slotTypes',originals['pt']['que']['relations'][0])

    def test_reviewed_slots_and_exact_highlights(self):
        originals,pilot,_=build()
        expanded,ledger=expand(originals,pilot)
        import re
        for (lang,word,i),(label,kind,chunks) in REVIEW.items():
            relation=expanded[lang][word]['relations'][i]
            self.assertEqual(relation['slotTypes']['v'],kind)
            if (word,i) not in DROP_CONTEXT[lang]:
                self.assertIn('>'+label+'</span>',relation['formulaHTML'])
            else:
                self.assertNotIn('fw-token-v',relation['formulaHTML'])
            for ex,chunk in zip(relation['examples'],chunks):
                if chunk is not None:
                    self.assertEqual(re.findall(r'<span class="fw-token-v">(.*?)</span>',ex['targetHTML']),[chunk])
        self.assertEqual(expanded['pt']['para']['relations'][2]['slotTypes']['v'],'noun')
        self.assertEqual(expanded['pt']['sobre']['relations'][0]['slotTypes']['v'],'mixed')
        for words in expanded.values():
            for entry in words.values():
                for r in entry['relations']:
                    self.assertNotIn('an action / situation',r['formulaHTML'])

    def test_short_formula_keeps_distinctions_and_sentence_types(self):
        originals,pilot,_=build()
        expanded,_=expand(originals,pilot)
        for lang in ('pt','es'):
            self.assertEqual(plain(expanded[lang]['que']['relations'][0]['formulaHTML']),'think / say / know / hope + que')
            self.assertEqual(plain(expanded[lang]['de']['relations'][0]['formulaHTML']),'verb + de')
            self.assertEqual(plain(expanded[lang]['de']['relations'][1]['formulaHTML']),'noun + de')
            place='em' if lang=='pt' else 'en'
            self.assertIn('a place',plain(expanded[lang][place]['relations'][0]['formulaHTML']))
            self.assertIn('a time / period',plain(expanded[lang][place]['relations'][1]['formulaHTML']))
        self.assertIn('what happens then',plain(expanded['pt']['se']['relations'][0]['formulaHTML']))
        self.assertEqual(plain(expanded['es']['y']['relations'][0]['formulaHTML']).count(' + '),2)
        self.assertIn('em + o',plain(expanded['pt']['no']['relations'][0]['formulaHTML']))
