"""Decision 0033: every form shares its word's card unless the form is privileged."""
import json
import shutil
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def sense(headword, pos, translation, sense_id, *, ref=None, tags=(), marks=(), page_marks=()):
    features = [{'kind': 'grammar_tag', 'value': t} for t in tags]
    features += [{'kind': 'surface_mark', 'value': m} for m in marks]
    features += [{'kind': 'sense_mark', 'value': m} for m in page_marks]
    return {'headword': headword, 'pos': pos, 'translation': translation, 'sense_id': sense_id,
            'source_reference': ref or f'kaikki:{headword}:{translation}',
            'metadata': {'sense_metadata': {'features': features}}}


def row(word, senses):
    return {'word': word, 'meanings': [s for s, _ in senses],
            'wsd_distribution': {'published_leaf_counts': {s['sense_id']: n for s, n in senses}}}


GIVE = lambda i: sense('dar', 'verb', 'to give', f'give{i}')
POSSIBLE = lambda i, marks: sense('dar', 'verb', 'to be possible', f'pos{i}',
                                  tags=['impersonal'], marks=marks)
ROWS = [
    # dá: impersonal "it's possible" on a third-person form, rare elsewhere.
    row('dá', [(GIVE(1), 15), (POSSIBLE(1, ['person=3']), 10)]),
    row('dou', [(GIVE(2), 30), (POSSIBLE(2, ['person=1']), 4)]),
    row('dei', [(GIVE(3), 30)]),
    row('damos', [(GIVE(4), 30)]),
    # A stray example from another word does not split a form.
    row('darei', [(GIVE(5), 29), (sense('dardo', 'noun', 'dart', 'dart'), 1)]),
    # fue: "went" spread over two senses of ir still adds up to another word.
    row('fue', [(sense('ser', 'VERB', 'to be', 'be1'), 22),
                (sense('ir', 'VERB', 'to go', 'go1'), 2),
                (sense('ir', 'VERB', 'to attend', 'go2'), 2),
                (sense('irse', 'VERB', 'to leave', 'go3'), 2)]),
    row('era', [(sense('ser', 'VERB', 'to be', 'be2'), 30)]),
    # SpanishDict: hay's own page has its own meaning; dime's is decir + "me";
    # pensé's restates pensar for that form.
    row('hay', [(sense('haber', 'VERB', 'there is', 'h1', ref='spanishdict-menu:hay:449'), 25)]),
    row('había', [(sense('haber', 'VERB', 'to have', 'h2', ref='spanishdict-menu:haber:d62'), 25)]),
    row('he', [(sense('haber', 'VERB', 'to have', 'h3', ref='spanishdict-menu:haber:d62'), 25)]),
    row('dime', [(sense('decir', 'VERB', 'tell me', 'd1', ref='spanishdict-menu:dime:1'), 30)]),
    row('digo', [(sense('decir', 'VERB', 'to say', 'd2', ref='spanishdict-menu:decir:2'), 30)]),
    row('pensé', [(sense('pensar', 'VERB', 'I thought', 'p1', ref='spanishdict-menu:pensé:8',
                         page_marks=['mood=indicative', 'person=1']), 30)]),
    row('pienso', [(sense('pensar', 'VERB', 'to think', 'p2', ref='spanishdict-menu:pensar:3'), 30)]),
    # haver: the impersonal sense is the main use of every form.
    row('há', [(sense('haver', 'verb', 'there be', 'x1', tags=['impersonal'], marks=['person=3']), 25)]),
    row('havia', [(sense('haver', 'verb', 'there be', 'x2', tags=['impersonal'], marks=['person=3']), 25)]),
    # Wiktionary lists deu as a contraction (de + eu, nonstandard), but its
    # examples are dar's; real contractions stay off their parts' cards.
    {**row('deu', [(GIVE(6), 30)]), 'is_contraction': True},
    {**row('no', [(sense('em', 'prep', 'in', 'em1'), 27)]), 'is_contraction': True},
    row('em', [(sense('em', 'prep', 'in', 'em2'), 30)]),
    {**row('aonde', [(sense('onde', 'adv', 'where', 'on1'), 20)]), 'is_contraction': True},
    row('onde', [(sense('onde', 'adv', 'where', 'on2'), 30)]),
    # An expression on the form does not keep it apart.
    row('sé', [(sense('saber', 'VERB', 'to know', 's1'), 17),
               ({**sense('no sé', 'PHRASE', "I don't know", 's2'), 'pos': 'PHRASE'}, 13)]),
    row('sabe', [(sense('saber', 'VERB', 'to know', 's3'), 30)]),
]


@unittest.skipUnless(shutil.which('node'), 'Node.js required')
class FormPrivilegeTests(unittest.TestCase):
    def test_named_forms(self):
        script = (
            "const {build} = require(" + json.dumps(str(ROOT / 'scripts/build_form_privilege_merges.cjs')) + ");"
            "process.stdout.write(JSON.stringify(build(" + json.dumps(ROWS) + ", {})));")
        result = subprocess.run(['node', '-e', script], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        verdicts = json.loads(result.stdout)
        lemma = {word: v['lemma'] for word, v in verdicts.items()}
        self.assertEqual(verdicts['dá'], {'lemma': '', 'reasons': ['form_restricted']})
        for word in ('dou', 'dei', 'damos', 'darei'):
            self.assertEqual(lemma[word], 'dar', word)
        self.assertEqual(verdicts['fue'], {'lemma': '', 'reasons': ['other_word']})
        self.assertEqual(lemma['era'], 'ser')
        self.assertEqual(verdicts['hay'], {'lemma': '', 'reasons': ['own_page']})
        self.assertEqual((lemma['había'], lemma['he']), ('haber', 'haber'))
        self.assertEqual((lemma['dime'], lemma['digo']), ('decir', 'decir'))
        self.assertEqual((lemma['pensé'], lemma['pienso']), ('pensar', 'pensar'))
        self.assertEqual((lemma['há'], lemma['havia']), ('haver', 'haver'))
        self.assertEqual((lemma['sé'], lemma['sabe']), ('saber', 'saber'))
        self.assertEqual(lemma['deu'], 'dar')
        self.assertEqual((lemma['no'], lemma['aonde']), ('', ''))

    def test_fully_loaded_deck_without_verdicts_runs_the_rule_in_the_app(self):
        source = (ROOT / 'app/js/vocab.js').read_text()
        blocks = []
        for name in ('lemma-merge-pure', 'low-share-pure'):
            start, end = source.index(f'// {name}\n'), source.index(f'// /{name}')
            blocks.append(source[start:end])
        start = source.index('function stampMergeExceptionValues(')
        end = source.index('\nasync function fetchActiveVocabularyIndex(', start)
        script = '\n'.join(blocks) + '\n' + source[start:end] + (
            "\nconst rows = " + json.dumps(ROWS) + ";"
            "stampMergeExceptionValues(rows, new Set(), null);"
            "const key = w => lemmaStudyGroupKey(rows.find(r => r.word === w)).split('\\u001f')[0];"
            "if (key('dou') !== 'dar' || key('dá') !== '' || key('fue') !== '') throw Error('full deck');"
            "const partial = JSON.parse(JSON.stringify(rows)); partial.slice(3).forEach(r => { r.meanings = []; });"
            "stampMergeExceptionValues(partial, new Set(), null);"
            "if (partial.some(r => r._formPrivilegeOverlay)) throw Error('partly loaded deck must not run it');")
        result = subprocess.run(['node', '-e', script], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr[-2000:])


if __name__ == '__main__':
    unittest.main()
