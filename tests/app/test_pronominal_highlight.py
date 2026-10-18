"""Pronominal cards must show their reflexive pronoun in every example."""
import json
from pathlib import Path
import shutil
import subprocess
import unittest

ROOT = Path(__file__).resolve().parents[2]

CONJ = {
    'irse': {
        'gerund': 'yéndose',
        'tenses': {
            'Presente': ['me voy', 'te vas', 'se va', 'nos vamos', 'os vais', 'se van'],
            'Pretérito': ['me fui', 'te fuiste', 'se fue', 'nos fuimos', 'os fuisteis', 'se fueron'],
            'Imperativo': ['—', 'vete', 'váyase', 'vámonos', 'idos', 'váyanse'],
        },
    },
}


@unittest.skipUnless(shutil.which('node'), 'Node.js required')
class PronominalHighlightTests(unittest.TestCase):
    def run_js(self, checks):
        source = (ROOT / 'app/js/flashcards.js').read_text()
        fold_start = source.index('function foldSurfaceForm(')
        fold_end = source.index('\n}\n', fold_start) + 3
        conj_start = source.index('function activeConjugationData(')
        conj_end = source.index('\n}\n', source.index('function getConjugationEntry(')) + 3
        block_start = source.index('function isPronominalVerbCard(')
        block_end = source.index('function getExampleProductionForm(')
        script = ("const assert = require('assert');\n"
                  "const _cachedRegex = (p, f) => new RegExp(p, f);\n"
                  f"globalThis._conjugationData = {json.dumps(CONJ, ensure_ascii=False)};\n"
                  + source[fold_start:fold_end] + source[conj_start:conj_end]
                  + source[block_start:block_end] + '''
const hl = w => `<span class="example-word-highlight">${w}</span>`;
const cl = w => `<span class="example-clitic-highlight">${w}</span>`;
const irse = { targetWord: 'fue', citationForm: 'irse', isPronominal: true,
    splitInfo: { headword: 'irse' } };
const run = (html, card = irse) => highlightPronominalCliticsInSentence(html, card);
''' + checks)
        result = subprocess.run(['node', '-e', script], text=True, capture_output=True)
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_preceding_pronoun_joins_the_highlight(self):
        self.run_js('''
assert.strictEqual(run(`¿Adónde se ${hl('fue')} ayer?`), `¿Adónde ${hl(cl('se') + ' fue')} ayer?`);
assert.strictEqual(run(`Se ${hl('fue')}.`), `${hl(cl('Se') + ' fue')}.`);
assert.strictEqual(run(`No te ${hl('vayas')}.`), `No ${hl(cl('te') + ' vayas')}.`);
assert.strictEqual(run(`Me lo ${hl('voy')} a llevar.`), `${hl(cl('Me') + ' lo voy')} a llevar.`);
assert.strictEqual(run(`Se me ${hl('fue')}.`), `${hl(cl('Se') + ' ' + cl('me') + ' fue')}.`);
// Already part of the highlight (matched from the conjugation table).
assert.strictEqual(run(`Ya ${hl('nos vamos')}.`), `Ya ${hl(cl('nos') + ' vamos')}.`);
''')

    def test_attached_pronoun_is_split(self):
        self.run_js('''
assert.strictEqual(run(`Quiero ${hl('irme')}.`), `Quiero ${hl('ir' + cl('me'))}.`);
assert.strictEqual(run(`Quiero ${hl('irse')}.`), `Quiero ${hl('ir' + cl('se'))}.`);
assert.strictEqual(run(`${hl('Vete')} ya.`), `${hl('Ve' + cl('te'))} ya.`);
assert.strictEqual(run(`${hl('Vámonos')}.`), `${hl('Vámo' + cl('nos'))}.`);
assert.strictEqual(run(`Está ${hl('yéndose')}.`), `Está ${hl('yéndo' + cl('se'))}.`);
''')

    def test_lookalikes_are_left_alone(self):
        self.run_js('''
// vamos ends in clitic letters but carries no pronoun.
assert.strictEqual(run(`${hl('Vamos')} a casa.`), `${hl('Vamos')} a casa.`);
// A pronoun elsewhere in the line does not belong to this verb.
assert.strictEqual(run(`Se lo dije, y ${hl('fue')}.`), `Se lo dije, y ${hl('fue')}.`);
// Not inside another word.
assert.strictEqual(run(`Clase ${hl('fue')}.`), `Clase ${hl('fue')}.`);
''')

    def test_only_pronominal_cards(self):
        self.run_js('''
const ir = { targetWord: 'fue', citationForm: 'ir', isPronominal: false, splitInfo: { headword: 'ir' } };
assert.strictEqual(run(`Se ${hl('fue')}.`, ir), `Se ${hl('fue')}.`);
const clase = { targetWord: 'clase', citationForm: 'clase', partOfSpeech: 'NOUN' };
assert.strictEqual(run(`La ${hl('clase')}.`, clase), `La ${hl('clase')}.`);
assert.strictEqual(isPronominalVerbCard(clase), false);
assert.strictEqual(isPronominalVerbCard({ citationForm: 'quedarse' }), true);
assert.strictEqual(isPronominalVerbCard(ir), false);
''')

    def test_keeps_pooled_form_attributes(self):
        self.run_js('''
const open = '<span class="example-word-highlight example-pooled-form" title="Recorded form in this example">';
assert.strictEqual(run(`Se ${open}fueron</span>.`), `${open}${cl('Se')} fueron</span>.`);
''')


if __name__ == '__main__':
    unittest.main()
