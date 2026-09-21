"""Display-only sibling-sense collapse for Spanish set-1 function words."""

from pathlib import Path
import shutil
import subprocess
import unittest


GRAMMAR_CARDS = Path(__file__).resolve().parents[2] / "app/js/grammar-cards.js"


class GrammarCardOverlayTests(unittest.TestCase):
    @unittest.skipUnless(shutil.which("node"), "Node.js is needed to run JS module tests")
    def test_lo_and_de_sibling_collapse(self) -> None:
        script = f"""
            import {{ applyGrammarCardOverlay, mergeGrammarMeanings }} from {GRAMMAR_CARDS.resolve().as_uri()!r};

            const lo = {{
                word: 'lo',
                meanings: [
                    {{ pos: 'PRON', translation: 'it', context: 'direct object', examples: [{{ text: 'Cocínalo despacio.' }}] }},
                    {{ pos: 'PRON', translation: 'him', context: 'direct object', examples: [{{ text: 'Lo vi en Roma.' }}] }},
                    {{ pos: 'PRON', translation: 'you', context: 'direct object', examples: [{{ text: 'Lo admiro.' }}] }},
                    {{ pos: 'PRON', translation: 'things', context: 'possessive', examples: [{{ text: 'Lo mío está bajo el escritorio.' }}] }},
                    {{ pos: 'PRON', translation: 'what', context: 'in relative constructions; used with "que"', examples: [{{ text: 'Lo que no me gusta.' }}] }},
                ],
            }};
            applyGrammarCardOverlay(lo, 'spanish');
            const loGlosses = lo.meanings.map(m => m.translation);
            if (loGlosses.length !== 3) throw new Error('lo should show 3 leaves, got ' + JSON.stringify(loGlosses));
            if (loGlosses[0] !== 'it / him / you') throw new Error('lo object clitic join failed: ' + loGlosses[0]);
            if ((lo.meanings[0].examples || []).length !== 3) throw new Error('lo object examples were not unioned');
            if (!loGlosses.includes('things') || !loGlosses.includes('what')) throw new Error('lo kept leaves missing');

            applyGrammarCardOverlay(lo, 'spanish');
            if (lo.meanings.map(m => m.translation).join('|') !== loGlosses.join('|')) {{
                throw new Error('second apply should be idempotent');
            }}

            const de = {{
                word: 'de',
                meanings: [
                    {{ pos: 'ADP', translation: 'from', context: 'used to indicate origin', examples: [{{ text: 'vienen de Nicaragua' }}] }},
                    {{ pos: 'ADP', translation: 'of', context: 'used to indicate material', examples: [{{ text: 'de plástico' }}] }},
                    {{ pos: 'ADP', translation: 'of', context: 'used to indicate characteristics', examples: [{{ text: 'de gran calidad' }}] }},
                    {{ pos: 'ADP', translation: 'of', context: 'used to indicate content', examples: [{{ text: 'bolsa de canicas' }}] }},
                    {{ pos: 'ADP', translation: 'in', context: 'used to indicate time', examples: [{{ text: 'de mañana' }}] }},
                    {{ pos: 'ADP', translation: 'with', context: 'used to express cause', examples: [{{ text: 'de pena' }}] }},
                ],
            }};
            applyGrammarCardOverlay(de, 'es');
            if (de.meanings.length !== 1) throw new Error('de should collapse to 1 ADP leaf, got ' + de.meanings.length);
            if (de.meanings[0].translation !== 'from / of / in / with') throw new Error('de join failed: ' + de.meanings[0].translation);
            if ((de.meanings[0].examples || []).length !== 6) throw new Error('de examples were not unioned');

            const personalA = mergeGrammarMeanings([
                {{ pos: 'ADP', translation: 'to', context: 'used to indicate direction' }},
                {{ pos: 'ADP', translation: 'to', context: 'the personal "a"' }},
                {{ pos: 'ADP', translation: 'at', context: 'used to indicate an exact moment' }},
            ], [{{ pos: 'ADP', translations: ['to', 'at'], contextExcludes: 'personal' }}]);
            if (personalA.length !== 2) throw new Error('personal a should remain separate, got ' + personalA.length);
            if (personalA[0].translation !== 'to / at') throw new Error('a join failed: ' + personalA[0].translation);
            if (personalA[1].translation !== 'to') throw new Error('personal a gloss lost');

            console.log('ALL_GRAMMAR_CARD_TESTS_PASSED');
        """
        result = subprocess.run(
            ["node", "--input-type=module"],
            input=script,
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
        self.assertIn("ALL_GRAMMAR_CARD_TESTS_PASSED", result.stdout)


if __name__ == "__main__":
    unittest.main()
