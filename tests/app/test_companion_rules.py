"""Companions follow assigned usage, not dictionary menu size or label counts."""
import json
import os
import shutil
import subprocess
import unittest
from pathlib import Path

from fluency.enrichments.card_rules import detect_split_card_tuples

ROOT = Path(__file__).resolve().parents[2]


def sense(hw, gloss, weight=1, *, tags=(), context='', pos='VERB', **extra):
    return dict(headword=hw, translation=gloss, frequency=weight, pos=pos,
                context=context, metadata={'sense_provider_metadata': {'tags': list(tags)}}, **extra)


CASES = [
    ('two senses can split pronominally', 'es', 'va', [sense('ir', 'to go'), sense('irse', 'to leave')], 'reflexive', 2),
    ('small pronominal share still splits', 'es', 'va', [sense('ir', 'to go', 99), sense('irse', 'to leave', 1)], 'reflexive', 2),
    ('Portuguese shared headword tags', 'pt', 'fica', [sense('ficar', 'to stay'), sense('ficar', 'to become', tags=['pronominal'])], 'reflexive', 2),
    ('Portuguese reflexive also counts', 'pt', 'lembra', [sense('lembrar', 'to remind'), sense('lembrar', 'to remember', tags=['reflexive'])], 'reflexive', 2),
    ('Portuguese hyphenated headword', 'pt', 'lembra', [sense('lembrar', 'to remind'), sense('lembrar-se', 'to remember')], 'reflexive', 2),
    ('Portuguese irregular infinitive', 'pt', 'põe', [sense('pôr', 'to put'), sense('pôr-se', 'to become')], 'reflexive', 2),
    ('placeholder cannot create companion', 'es', 'va', [sense('ir', 'to go'), sense('irse', 'to leave', pos='SENSE_CYCLE')], None, 0),
    ('all definitions exactly match', 'es', 'lava', [sense('lavar', ' TO WASH. '), sense('lavarse', 'to wash')], None, 0),
    ('one different definition defeats exception', 'es', 'pone', [sense('poner', 'to put on'), sense('ponerse', 'to put on'), sense('ponerse', 'to become')], 'reflexive', 2),
    ('semantic contexts distinguish matching gloss', 'es', 'pone', [sense('poner', 'to get', context='to obtain'), sense('ponerse', 'to get', context='to become')], 'reflexive', 2),
    ('grammatical contexts do not distinguish gloss', 'pt', 'lava', [sense('lavar', 'to wash', context='transitive'), sense('lavar', 'to wash', context='reflexive')], None, 0),
    ('explicit shared definition', 'pt', 'senta', [sense('sentar', 'to seat'), sense('sentar', 'to sit', tags=['transitive', 'reflexive'])], None, 0),
    ('ambitransitive shared definition', 'pt', 'senta', [sense('sentar', 'to seat'), sense('sentar', 'to sit', tags=['ambitransitive', 'reflexive'])], None, 0),
    ('shared and exclusive definitions', 'pt', 'faz', [sense('fazer', 'to make'), sense('fazer', 'to make', tags=['transitive', 'reflexive']), sense('fazer', 'to become', tags=['pronominal'])], 'reflexive', 2),
    ('unused meaning changing sense ignored', 'es', 'lava', [sense('lavar', 'to wash'), sense('lavarse', 'to wash'), sense('lavarse', 'to disappear', 0)], None, 0),
    ('unassigned sense with frequency ignored', 'es', 'va', [sense('ir', 'to go'), sense('irse', 'to leave', 1, unassigned=True)], None, 0),
    ('passive se is not lexical pronominal', 'pt', 'vende', [sense('vender', 'to sell'), sense('vender', 'to be sold', tags=['reflexive', 'passive'])], None, 0),
    ('only pronominal family remains one', 'es', 'va', [sense('irse', 'to leave'), sense('irse', 'to go away')], None, 0),
    ('noun ending se is not reflexive', 'es', 'clase', [sense('clase', 'class', pos='NOUN'), sense('clase', 'kind', pos='NOUN')], None, 0),
    ('many meanings of one lemma stay together', 'es', 'banco', [sense('banco', g, pos='NOUN') for g in ['bank','bench','shoal','school of fish']], None, 0),
    ('polysemy minimum four senses', 'es', 'fue', [sense('ser', 'to be'), sense('ir', 'to go')], None, 0),
    ('usage not number of rows decides', 'es', 'fue', [sense('ser', 'to be', 97), sense('ser', 'to exist', 1), sense('ir', 'to go', 1), sense('ir', 'to leave', 1)], None, 0),
    ('ten percent boundary qualifies', 'es', 'fue', [sense('ser', 'to be', 80), sense('ser', 'to exist', 10), sense('ir', 'to go', 5), sense('ir', 'to leave', 5)], 'homograph', 2),
    ('Portuguese noun and verb', 'pt', 'conta', [sense('conta', 'bill', 4, pos='noun'), sense('conta', 'account', 9, pos='noun'), sense('contar', 'to tell', 5), sense('contar', 'to matter', 2)], 'homograph', 2),
    ('three major lemmas retained', 'es', 'fuera', [sense('ser', 'to be', 4), sense('ser', 'to exist', 2), sense('ir', 'to go', 3), sense('fuera', 'outside', 3, pos='ADV')], 'homograph', 3),
    ('MWE cannot create fourth lexical sense', 'es', 'fue', [sense('ser', 'to be'), sense('ir', 'to go'), sense('ir', 'to leave'), sense('ir bien', 'to go well', pos='PHRASE')], None, 0),
]

# Stable IDs also make the builder's sense ownership test the real app route.
for _, _, _, meanings, _, _ in CASES:
    for index, meaning in enumerate(meanings):
        meaning['sense_id'] = f's{index}'


class CompanionRuleTests(unittest.TestCase):
    @unittest.skipUnless(shutil.which('node'), 'Node.js needed for app parity')
    def test_policy_and_full_python_js_parity(self):
        rows = [dict(word=word, meanings=ms) for _, _, word, ms, _, _ in CASES]
        script = r"""
            const fs = require('node:fs'), vm = require('node:vm');
            const source = fs.readFileSync(process.env.VOCAB_JS, 'utf8');
            const pure = source.slice(source.indexOf('// lemma-merge-pure'), source.indexOf('// /lemma-merge-pure'));
            const context = { console }; vm.createContext(context); vm.runInContext(pure, context);
            const rows = JSON.parse(process.env.ROWS), languages = JSON.parse(process.env.LANGUAGES);
            process.stdout.write(JSON.stringify(rows.map((r, i) => context.detectSplitCardTuples(r, languages[i]))));
        """
        completed = subprocess.run(['node', '-e', script], capture_output=True, text=True,
            env={**os.environ, 'VOCAB_JS': str(ROOT / 'app/js/vocab.js'), 'ROWS': json.dumps(rows),
                 'LANGUAGES': json.dumps([case[1] for case in CASES])})
        self.assertEqual(completed.returncode, 0, completed.stderr)
        for case, row, js in zip(CASES, rows, json.loads(completed.stdout)):
            name, lang, _, _, kind, count = case
            with self.subTest(name=name):
                py = detect_split_card_tuples(row, lang)
                self.assertEqual(py, js)
                self.assertEqual(py['kind'] if py else None, kind)
                self.assertEqual(len(py['tuples']) if py else 0, count)
                if py:
                    ids = [m['sense_id'] for t in py['tuples'] for m in t['meanings']]
                    self.assertEqual(len(ids), len(set(ids)))
                    if lang == 'pt' and kind == 'reflexive':
                        self.assertTrue(py['tuple2']['headword'].endswith('-se'))

    def test_exact_published_counts_and_duplicate_ids(self):
        row = {'word': 'fue', 'meanings': [sense('ser','to be', .3, sense_id='a'),
            sense('ser','to exist', .0375, sense_id='b'), sense('ir','to go', .0125, sense_id='c'),
            sense('ir','to leave', .025, sense_id='d')],
            'wsd_distribution': {'published_leaf_counts': {'a': 24, 'b': 3, 'c': 1, 'd': 2}}}
        self.assertEqual(detect_split_card_tuples(row)['tuple2']['share'], .1)
        row['meanings'].append(dict(row['meanings'][0]))
        self.assertEqual(len(detect_split_card_tuples(row)['tuple1']['meanings']), 2)
        row['wsd_distribution']['published_leaf_counts']['c'] = 0
        self.assertIsNone(detect_split_card_tuples(row))

    @unittest.skipUnless(shutil.which('node'), 'Node.js needed for card builder')
    def test_card_builder_keeps_rare_and_unused_senses_on_their_companion(self):
        script = r"""
            const fs = require('node:fs'), vm = require('node:vm');
            const source = fs.readFileSync(process.env.VOCAB_JS, 'utf8');
            const pure = source.slice(source.indexOf('// lemma-merge-pure'), source.indexOf('// /lemma-merge-pure'));
            const low = source.slice(source.indexOf('// low-share-pure'), source.indexOf('// /low-share-pure'));
            const builder = source.slice(source.indexOf('function buildSplitCardPair('), source.indexOf('globalThis.buildSplitCardPair'));
            const context = { console }; context.window = context; context.globalThis = context;
            vm.createContext(context); vm.runInContext(pure + low + builder, context);
            const item = { id: 'go', word: 'va', meanings: [
                { sense_id: 'a', headword: 'ir', pos: 'VERB', translation: 'to go', frequency: .99 },
                { sense_id: 'b', headword: 'irse', pos: 'VERB', translation: 'to leave', frequency: .01 }
            ], unused_menu_senses: [
                { sense_id: 'c', headword: 'ir', pos: 'VERB', translation: 'to attend' },
                { sense_id: 'd', headword: 'irse', pos: 'VERB', translation: 'to disappear' }
            ] };
            const rendered = item.meanings.map(m => ({ ...m, senseId: m.sense_id,
                meaning: m.translation, percentage: m.frequency, targetSentence: 'Example ' + m.sense_id }));
            const finished = context.finishCardMeanings(item, rendered);
            const cards = context.buildSplitCardPair(item, { ...finished, fullId: 'es0go' }, finished.meanings, 'es');
            process.stdout.write(JSON.stringify(cards));
        """
        completed = subprocess.run(['node','-e',script], capture_output=True, text=True,
            env={**os.environ, 'VOCAB_JS': str(ROOT / 'app/js/vocab.js')})
        self.assertEqual(completed.returncode, 0, completed.stderr)
        cards = json.loads(completed.stdout)
        self.assertEqual(len(cards), 2)
        self.assertEqual([c['meanings'][0]['senseId'] for c in cards], ['a', 'b'])
        self.assertEqual([c['meanings'][0]['shownShare'] for c in cards], [1, 1])
        self.assertEqual([c['targetSentence'] for c in cards], ['Example a', 'Example b'])
        self.assertEqual([[m['senseId'] for m in c['unusedMenuSenses']] for c in cards], [['c'], ['d']])
        self.assertEqual(cards[1]['splitInfo']['headword'], 'irse')

    @unittest.skipUnless(shutil.which('node'), 'Node.js needed for companion navigation')
    def test_three_companions_search_focus_and_finite_navigation(self):
        case = next(c for c in CASES if c[0] == 'three major lemmas retained')
        row = dict(id='outside', word=case[2], meanings=case[3])
        script = r"""
            const fs = require('node:fs'), vm = require('node:vm');
            const source = fs.readFileSync(process.env.VOCAB_JS, 'utf8');
            const pure = source.slice(source.indexOf('// lemma-merge-pure'), source.indexOf('// /lemma-merge-pure'));
            const low = source.slice(source.indexOf('// low-share-pure'), source.indexOf('// /low-share-pure'));
            const builder = source.slice(source.indexOf('function buildSplitCardPair('), source.indexOf('globalThis.buildSplitCardPair'));
            const modals = fs.readFileSync(process.env.MODALS_JS, 'utf8');
            const navigation = modals.slice(modals.indexOf('function splitAwareTempCard('), modals.indexOf('function navigateToVocabCard('));
            const context = { console, selectedLanguage: 'es' }; context.window = context; context.globalThis = context;
            vm.createContext(context); vm.runInContext(pure + low + builder + navigation, context);
            const row = JSON.parse(process.env.ROW);
            const meanings = row.meanings.map(m => ({ ...m, senseId: m.sense_id,
                meaning: m.translation, percentage: m.frequency }));
            const finished = context.finishCardMeanings(row, meanings);
            const base = { ...finished, fullId: 'es0outside' };
            // Search focuses the fourth sense, belonging to the third companion.
            const start = context.splitAwareTempCard(row, base, 3);
            const cards = []; let card = start.card;
            while (card) {
                if (cards.length > 3) throw Error('Companion navigation cycle');
                cards.push({ headword: card.citationForm, index: card.splitInfo.index,
                    total: card.splitInfo.total, readings: card.splitInfo.readings.map(r => r.headword) });
                card = card._splitNext;
            }
            process.stdout.write(JSON.stringify({ cards, meaningIndex: start.meaningIndex }));
        """
        completed = subprocess.run(['node', '-e', script], capture_output=True, text=True,
            env={**os.environ, 'VOCAB_JS': str(ROOT / 'app/js/vocab.js'),
                 'MODALS_JS': str(ROOT / 'app/js/flashcards-modals.js'), 'ROW': json.dumps(row)})
        self.assertEqual(completed.returncode, 0, completed.stderr)
        result = json.loads(completed.stdout)
        self.assertEqual([c['headword'] for c in result['cards']], ['fuera', 'ser', 'ir'])
        self.assertEqual([c['index'] for c in result['cards']], [3, 1, 2])
        self.assertEqual(result['meaningIndex'], 0)
        self.assertTrue(all(c['total'] == 3 and c['readings'] == ['ser', 'ir', 'fuera'] for c in result['cards']))


if __name__ == '__main__':
    unittest.main()
