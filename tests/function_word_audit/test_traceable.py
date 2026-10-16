import json
from pathlib import Path
import sys
import unittest

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'research/function_word_audit'))
from pilot import build
from traceable import attach,highlighted,OUT
from check import plain,markup_errors
from provenance_preview import script


class TraceableTests(unittest.TestCase):
    def test_all_patterns_have_real_unchanged_source_examples(self):
        _,proposals,_=build();proposals,review=attach(proposals)
        self.assertEqual(len(review),71)
        records={r['example_id']:r for r in review}
        seen_patterns=0
        for words in proposals.values():
            for card in words.values():
                for pattern in card['relations']:
                    seen_patterns+=1
                    self.assertGreaterEqual(len(pattern['examples']),2)
                    self.assertEqual(pattern['targetHTML'],pattern['examples'][0]['targetHTML'])
                    for example in pattern['examples']:
                        row=records[example['example_id']]
                        self.assertEqual(plain(example['targetHTML']),row['sentence'])
                        self.assertEqual(example['translation'],row['translation'])
                        self.assertEqual(example['metadata']['source'],row['source'])
                        self.assertEqual(markup_errors(example['targetHTML']),[])
                        self.assertIn(example['source'],('tatoeba','opensubtitles'))
                        self.assertTrue(example['metadata']['source']['source_record_id'])
                        for chunk in row['chunks']:
                            self.assertEqual(row['sentence'][chunk['start']:chunk['end']],chunk['text'])
        self.assertEqual(seen_patterns,24)

    def test_substrings_do_not_match_inside_words(self):
        html,spans=highlighted('Depende de ti.', [('v','Depende'),('connector','de'),('c','ti')])
        self.assertEqual(spans[1]['start'],8)
        with self.assertRaises(ValueError):highlighted('Depende.', [('connector','de')])
        html,_=highlighted('É "o" & pronto.', [('connector','o')])
        self.assertEqual(plain(html),'É "o" & pronto.')

    def test_provenance_uses_existing_app_components(self):
        output=script()
        for name in ('normalizedExampleProvenance','exampleProvenanceHTML','exampleSourceChipHTML','outboundChipHTML'):
            self.assertIn('function '+name+'(',output)
        self.assertIn('https://www.imdb.com/title/',output)
        self.assertIn('data:image/svg+xml;base64,',output)
        self.assertIn('Source not verified',output)

    def test_revised_preview_renders_traceable_credit(self):
        from preview import render
        originals,proposals,ledger=build();proposals,_=attach(proposals)
        html=render(originals,proposals,ledger)
        self.assertIn('paintPreviewProvenance();',html)
        self.assertIn('metadata?.source?.source_record_id',html)
        self.assertIn('e.target===panel',html)
        self.assertIn('OpenSubtitles.org</a>',html)

if __name__=='__main__':unittest.main()
