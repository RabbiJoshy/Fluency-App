"""Exclude Cognates sets a card aside only when every sense it shows is free."""

import os
import shutil
import subprocess
import unittest
from pathlib import Path

COGNATES = Path(__file__).resolve().parents[2] / "app/js/cognates.js"


class EverySenseTests(unittest.TestCase):
    @unittest.skipUnless(shutil.which("node"), "Node.js is needed to run JS vm tests")
    def test_every_shown_sense_must_be_a_free_cognate(self) -> None:
        script = r"""
            const fs = require('node:fs');
            const vm = require('node:vm');
            const source = fs.readFileSync(process.env.COGNATES_JS, 'utf8').replace(/^import .*$/mg, '');
            const payload = {
                schema: 'cognate-score/v4', language: 'cs',
                known_languages: ['en', 'pl'], thresholds: { en: 0.75, pl: 0.8 },
                built_from_release_id: 'cs-speech-test',
                scores: {
                    idea: { idea: { idea: { en: 1.0 } } },
                    banco: { banco: { bank: { en: 0.8 }, bench: { en: 0.6 } } },
                    problema: { problema: { problem: { en: 0.88 } } },
                    tres: { tres: { three: { en: 0.7 } } },
                    kotě: { kotě: { kitten: { pl: 0.9 } } },
                },
                matches: { kotě: { kotě: { kitten: { pl: 'kocię' } } } },
                cards: { familia: { en: [0.86, 'family'] } },
            };
            const context = {
                console, localStorage: { getItem: () => null, setItem: () => {} },
                document: { getElementById: () => null },
                fetch: async () => ({ ok: true, json: async () => payload }),
            };
            context.globalThis = context;
            context.isExpressionSenseForLemma = meaning => meaning.pos === 'PHRASE';
            vm.runInNewContext(source, context);
            const fail = message => { throw new Error(message); };
            (async () => {
                await context.loadCognateScores({ cognatesPath: 'x', indexPath: 'releases/cs/speech/cs-speech-test/app/vocabulary.index.json' });
                context.localStorage.getItem = () => JSON.stringify(['en', 'pl']);
                const deck = [
                    { word: 'idea', meanings: [{ headword: 'idea', translation: 'idea' }] },
                    // bank is free, "school (of fish)" is not a cognate: kept.
                    { word: 'banco', meanings: [
                        { headword: 'banco', translation: 'bank' },
                        { headword: 'banco', translation: 'school (of fish)' },
                    ]},
                    // Expressions are never free cognates.
                    { word: 'problema', meanings: [
                        { headword: 'problema', translation: 'problem' },
                        { headword: 'no hay problema', pos: 'PHRASE', translation: 'no problem' },
                    ]},
                    // Below the cutoff.
                    { word: 'tres', meanings: [{ headword: 'tres', translation: 'three' }] },
                    // Rows still loading show no sense: never free.
                    { word: 'idea', meanings: [] },
                    // Not in the map at all.
                    { word: 'casa', meanings: [{ headword: 'casa', translation: 'house' }] },
                    // Senses not loaded: the pipeline's card verdict decides.
                    { word: 'familia', meanings: [] },
                    // A Polish reader gets kotě free; an English reader does not.
                    { word: 'kotě', meanings: [{ headword: 'kotě', translation: 'kitten' }] },
                ];
                context.applyCognateScores(deck, 'cs');
                const verdicts = deck.map(item => context.isCognateKnown(item));
                const expected = [true, false, false, false, false, false, true, true];
                if (JSON.stringify(verdicts) !== JSON.stringify(expected)) fail('verdicts ' + JSON.stringify(verdicts));
                const named = context.matchedKnownWord(deck[0]);
                if (!named || named.word !== 'idea') fail('the deciding word is named');
                if (context.cognateScoreFor(deck[1], 'en') !== 0) fail('a card scores as its weakest sense');
                if (context.cognateScoreFor(deck[7], 'en') !== 0) fail('kotě is not free in English');
                const polish = context.matchedKnownWord(deck[7]);
                if (!polish || polish.code !== 'pl' || polish.word !== 'kocię') fail('the Polish word is named: ' + JSON.stringify(polish));
            })().catch(error => { console.error(error.message); process.exit(1); });
        """
        completed = subprocess.run(
            ["node", "-e", script],
            check=False,
            capture_output=True,
            text=True,
            env={**os.environ, "COGNATES_JS": str(COGNATES)},
        )
        if completed.returncode != 0:
            self.fail(completed.stderr or completed.stdout)


if __name__ == "__main__":
    unittest.main()
