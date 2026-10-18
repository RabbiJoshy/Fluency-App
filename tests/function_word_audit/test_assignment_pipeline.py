import json,sys,unittest
from pathlib import Path
from copy import deepcopy
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'research/function_word_audit'))
sys.path.insert(0,str(ROOT/'scripts'))
from syntax_assignment import assign
from assign_function_word_examples import build

class PipelineTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        p=ROOT/'docs/audits/function-word-assignment/final-check'
        cls.rows=json.loads((p/'predictions.json').read_text())['rows']
        cls.parses=json.loads((p/'parses.json').read_text())['rows']
    def test_nominal_chunk_excludes_trailing_aside(self):
        row=next(r for r in self.rows if r['word']=='uma')
        r=assign(row,self.parses[row['example_id']])
        self.assertEqual(r['chunks'][1]['text'],'pergunta')
    def test_translation_and_review_do_not_gate_assignment(self):
        for row in self.rows:
            obs=self.parses[row['example_id']]
            changed=dict(row,translation='',source={},review={'decision':'reject'})
            self.assertEqual(assign(row,obs),assign(changed,obs))
    def test_batch_preserves_source_and_baseline(self):
        originals=deepcopy(self.rows);cache=deepcopy(self.parses)
        results,overlay=build(self.rows,self.parses)
        self.assertEqual(self.rows,originals);self.assertEqual(self.parses,cache)
        self.assertEqual(len(results),20)
        indexed={r['example_id']:r for r in self.rows}
        for words in overlay.values():
            for patterns in words.values():
                for examples in patterns.values():
                    for ex in examples:
                        raw=indexed[ex['example_id']]
                        self.assertEqual(ex['translation'],raw['translation'])
                        self.assertEqual(ex['metadata']['source'],raw['source'])
                        self.assertEqual(ex['targetHTML'],assign(raw,self.parses[raw['example_id']])['targetHTML'])
    def test_parse_source_mismatch_is_unassigned(self):
        row=next(r for r in self.rows if r['word']=='uma');cache=deepcopy(self.parses)
        cache[row['example_id']]['sentences'][0][0]['token']['text']='wrong source'
        results,overlay=build([row],cache)
        self.assertEqual(results[0]['assignment']['status'],'abstain')
        self.assertEqual(overlay,{'pt':{},'es':{}})

    def test_staging_overlay_matches_automatic_export(self):
        overlay=json.loads((ROOT/'app/data/grammar-words/syntax-trial.json').read_text())
        _,expected=build(self.rows,self.parses)
        actual={}
        for lang,words in overlay.items():
            actual[lang]={}
            for word,patterns in words.items():
                for pattern,examples in patterns.items():
                    automatic=[e for e in examples if e.get('automaticSyntax')]
                    if automatic:actual[lang].setdefault(word,{})[pattern]=automatic
        self.assertEqual(actual,expected)

    def test_unsupported_surface_has_uniform_abstention_record(self):
        row=dict(self.rows[0],word='unsupported')
        records,_=build([row],{})
        self.assertEqual(records[0]['assignment']['status'],'abstain')
        self.assertEqual(records[0]['language'],row['language'])

    def test_occurrence_specific_cache_takes_precedence(self):
        row=next(r for r in self.rows if r['word']=='uma')
        cache={row['example_id']:None,
               f"{row['language']}|{row['word']}|{row['example_id']}":self.parses[row['example_id']]}
        records,_=build([row],cache)
        self.assertEqual(records[0]['assignment']['status'],'candidate')
