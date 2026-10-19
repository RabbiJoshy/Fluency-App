"""Example highlights join the words a sense is built from, and only those."""
import json
from pathlib import Path
import shutil
import subprocess
import unittest

ROOT = Path(__file__).resolve().parents[2]

CONJ = {
    'pasar': {'gerund': 'pasando', 'past_participle': 'pasado', 'tenses': {}},
    'hablar': {'gerund': 'hablando', 'past_participle': 'hablado', 'tenses': {}},
    'aprender': {'gerund': 'aprendiendo', 'past_participle': 'aprendido', 'tenses': {}},
    'hacer': {'gerund': 'haciendo', 'past_participle': 'hecho', 'tenses': {}},
    'trabajar': {'gerund': 'trabajando', 'past_participle': 'trabajado', 'tenses': {}},
    'acordarse': {'gerund': 'acordándose', 'past_participle': 'acordado',
                  'tenses': {'Presente': ['me acuerdo', 'te acuerdas', 'se acuerda']}},
}


@unittest.skipUnless(shutil.which('node'), 'Node.js required')
class ExampleFrameHighlightTests(unittest.TestCase):
    def run_js(self, checks):
        source = (ROOT / 'app/js/flashcards.js').read_text()

        def between(start, end):
            a = source.index(start)
            return source[a:source.index(end, a)]

        script = ("const assert = require('assert');\n"
                  "const _cachedRegex = (p, f) => new RegExp(p, f);\n"
                  "let companionTerms = [];\n"
                  "const extractSenseCompanion = () => companionTerms.length ? { terms: companionTerms } : null;\n"
                  "const parseSpanishDictUsageContext = () => null;\n"
                  f"globalThis._conjugationData = {json.dumps(CONJ, ensure_ascii=False)};\n"
                  + between('function foldSurfaceForm(', 'function getExampleOccurrenceSurface')
                  + between('const COMPANION_SURFACE_VARIANTS', '// Choose a type scale')
                  + between('function isPronominalVerbCard(', 'function getExampleProductionForm(')
                  + '''
const hl = w => `<span class="example-word-highlight">${w}</span>`;
const cl = w => `<span class="example-clitic-highlight">${w}</span>`;
const co = w => `<span class="example-word-highlight example-companion-highlight" title="Collocation with this sense">${w}</span>`;
const companion = (html, terms, card = { targetWord: 'x' }) => {
    companionTerms = terms;
    return highlightUnifiedCompanionInSentence(html, {}, card, 'spanish').html;
};
const frame = (html, meaning) => highlightComplementFrameInSentence(html, meaning, {});
''' + checks)
        result = subprocess.run(['node', '-e', script], text=True, capture_output=True)
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_companion_joins_a_highlight_holding_a_pronoun(self):
        self.run_js('''
const acordarse = { targetWord: 'acuerda', citationForm: 'acordarse', isPronominal: true };
const withPronoun = highlightPronominalCliticsInSentence(`No se ${hl('acuerda')} de nada.`, acordarse);
assert.strictEqual(companion(withPronoun, ['de'], acordarse),
    `No ${hl(cl('se') + ' acuerda de')} nada.`);
assert.strictEqual(companion(`Me ${hl('acuerdo')} del día.`, ['de']), `Me ${hl('acuerdo del')} día.`);
''')

    def test_companion_one_word_away_or_not_at_all(self):
        self.run_js('''
assert.strictEqual(companion(`${hl('Tengo')} mucho que aprender.`, ['que']),
    `${hl('Tengo')} mucho ${co('que')} aprender.`);
// Further away the word belongs to something else in the line.
assert.strictEqual(companion(`No ${hl('estoy')} de acuerdo con tus conclusiones.`, ['con']),
    `No ${hl('estoy')} de acuerdo con tus conclusiones.`);
// Never before the target unless right next to it.
assert.strictEqual(companion(`Con ella no ${hl('estoy')}.`, ['con']), `Con ella no ${hl('estoy')}.`);
''')

    def test_frame_is_read_from_the_sense(self):
        self.run_js('''
assert.strictEqual(senseComplementFrame({ context: 'used in compound tenses' }), 'participle');
assert.strictEqual(senseComplementFrame({ context: 'to have; used with a participle to describe a state' }), 'participle');
assert.strictEqual(senseComplementFrame({ context: 'used with an infinitive' }), 'infinitive');
assert.strictEqual(senseComplementFrame({ context: 'often used with "a" and an infinitive' }), 'infinitive');
assert.strictEqual(senseComplementFrame({ context: 'used with a gerund' }), 'gerund');
assert.strictEqual(senseComplementFrame({ metadata: { sense_metadata: { features: [
    { family: 'construction', kind: 'auxiliary_frame', value: 'progressive construction' }] } } }), 'gerund');
assert.strictEqual(senseComplementFrame({ context: 'past participle of hacer' }), '');
assert.strictEqual(senseComplementFrame({ context: 'used with "que"' }), '');
''')

    def test_participle_infinitive_and_gerund_join(self):
        self.run_js('''
const perfect = { context: 'used in compound tenses' };
assert.strictEqual(frame(`No sé qué le ${hl('ha')} pasado.`, perfect), `No sé qué le ${hl('ha pasado')}.`);
assert.strictEqual(frame(`Lo ${hl('has')} hecho bien.`, perfect), `Lo ${hl('has hecho')} bien.`);
// Not a participle: nothing joins.
assert.strictEqual(frame(`${hl('Ha')} de venir.`, perfect), `${hl('Ha')} de venir.`);
const inf = { context: 'used with an infinitive' };
assert.strictEqual(frame(`No ${hl('suelo')} hablar de eso.`, inf), `No ${hl('suelo hablar')} de eso.`);
assert.strictEqual(frame(`No ${hl('suelo')} hacerlo.`, inf), `No ${hl('suelo hacerlo')}.`);
// After the companion has joined, the infinitive follows it.
assert.strictEqual(frame(`${hl('Pongámonos a')} trabajar.`, { context: 'often used with "a" and an infinitive' }),
    `${hl('Pongámonos a trabajar')}.`);
assert.strictEqual(frame(`${hl('Estoy')} aprendiendo.`, { context: 'used with a gerund' }),
    `${hl('Estoy aprendiendo')}.`);
// Senses without a frame are untouched.
assert.strictEqual(frame(`${hl('Estoy')} aprendiendo.`, { context: 'to be' }), `${hl('Estoy')} aprendiendo.`);
''')

    def test_frame_keeps_nested_pronoun_accent(self):
        self.run_js('''
assert.strictEqual(frame(`${hl(cl('se') + ' ha')} pasado.`, { context: 'used in compound tenses' }),
    `${hl(cl('se') + ' ha pasado')}.`);
''')


if __name__ == '__main__':
    unittest.main()
