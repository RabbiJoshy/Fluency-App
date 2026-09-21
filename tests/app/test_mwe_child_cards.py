"""Unit tests for MWE expression child-card chaining."""

import json
from pathlib import Path
import shutil
import subprocess
import unittest


FLASHCARDS = Path(__file__).resolve().parents[2] / "app/js/flashcards.js"


class MWEChildCardTests(unittest.TestCase):
    @unittest.skipUnless(shutil.which("node"), "Node.js is needed to run JS vm tests")
    def test_mwe_classification_and_chaining(self) -> None:
        script = r"""
            const fs = require('node:fs');
            const vm = require('node:vm');
            const source = fs.readFileSync(process.argv[2], 'utf8');

            const start = source.indexOf('function meaningSourceAdapter(meaning)');
            const end = source.indexOf('function collectRareSenseItems(card)', start);
            if (start < 0 || end < 0) throw new Error('MWE helpers or collectChainItems missing');

            const context = {};
            vm.runInNewContext(source.slice(start, end), context);

            const {
                isInvariantMweMeaning,
                isAmbiguousMweMeaning,
                isExpressionChildMeaning,
                isHiddenExpressionOnParent,
                cardHasOnlyInvariantMwes,
                collectChainItems,
            } = context;

            const invariantMeaning = {
                pos: 'PHRASE',
                headword: 'en serio',
                translation: 'seriously',
                metadata: {
                    multiword_evidence: [{ expression: 'en serio', wsd_routing: 'deterministic_bypass' }]
                },
                examples: [{ target: '¿Hablas en serio?', english: 'Are you serious?' }]
            };

            const ambiguousMeaning = {
                pos: 'PHRASE',
                headword: 'dar vueltas',
                translation: 'to spin around',
                metadata: {
                    multiword_evidence: [{ expression: 'dar vueltas', wsd_routing: 'competitive_wsd' }]
                },
                examples: [{ target: 'Da muchas vueltas.', english: 'It spins a lot.' }]
            };

            const publishedMerged = {
                pos: 'PHRASE',
                headword: 'a salvo',
                translation: 'safe',
                metadata: { source_adapter: 'mwe-merged/v1' },
                examples: [{ target: 'Está a salvo.', english: 'He is safe.' }]
            };

            const standardDictPhrase = {
                pos: 'PHRASE',
                headword: 'déjame',
                translation: 'let me',
                metadata: {
                    source_adapter: 'spanishdict-sense-menu/v1'
                }
            };

            const literalMeaning = {
                pos: 'ADJ',
                headword: 'serio',
                translation: 'serious',
                examples: [{ target: 'Es muy serio.', english: 'He is very serious.' }]
            };

            if (!isInvariantMweMeaning(invariantMeaning)) throw new Error('invariantMeaning should be invariant');
            if (isInvariantMweMeaning(ambiguousMeaning)) throw new Error('ambiguousMeaning should not be invariant');
            if (isInvariantMweMeaning(standardDictPhrase)) throw new Error('standardDictPhrase should not be invariant');
            if (isInvariantMweMeaning(literalMeaning)) throw new Error('literalMeaning should not be invariant');

            if (!isAmbiguousMweMeaning(ambiguousMeaning)) throw new Error('ambiguousMeaning should be ambiguous');
            if (isAmbiguousMweMeaning(invariantMeaning)) throw new Error('invariantMeaning should not be ambiguous');

            const serioCard = { targetWord: 'serio', meanings: [literalMeaning, invariantMeaning] };
            if (!isExpressionChildMeaning(invariantMeaning, serioCard)) throw new Error('invariant should be a child expression');
            if (!isExpressionChildMeaning(ambiguousMeaning, { targetWord: 'dar', meanings: [literalMeaning, ambiguousMeaning] })) {
                throw new Error('ambiguous non-decompositional MWE should still be a child');
            }
            if (!isExpressionChildMeaning(publishedMerged, { targetWord: 'salvo', meanings: [literalMeaning, publishedMerged] })) {
                throw new Error('mwe-merged PHRASE should be a child even without routing stamps');
            }
            if (isExpressionChildMeaning(standardDictPhrase, { targetWord: 'déjame', meanings: [standardDictPhrase] })) {
                throw new Error('dictionary PHRASE on the card word should stay on the parent');
            }
            if (isExpressionChildMeaning(literalMeaning, serioCard)) throw new Error('literal ADJ should stay on the parent');

            const boundCard = {
                targetWord: 'repente',
                meanings: [invariantMeaning]
            };
            const polysemousCard = {
                targetWord: 'serio',
                meanings: [literalMeaning, invariantMeaning]
            };
            const ambiguousCard = {
                targetWord: 'dar',
                meanings: [literalMeaning, ambiguousMeaning]
            };
            const publishedCard = {
                targetWord: 'salvo',
                meanings: [literalMeaning, publishedMerged]
            };

            if (!cardHasOnlyInvariantMwes(boundCard)) throw new Error('boundCard should have only expression meanings');
            if (cardHasOnlyInvariantMwes(polysemousCard)) throw new Error('polysemousCard should not have only expression meanings');
            if (isHiddenExpressionOnParent(boundCard, invariantMeaning)) throw new Error('bound root must keep its only expression on the card');
            if (!isHiddenExpressionOnParent(polysemousCard, invariantMeaning)) throw new Error('polysemous parent must hide the expression sense');

            const polyItems = collectChainItems(polysemousCard);
            if (polyItems.length !== 1) throw new Error(`Expected 1 chain item for serio, got ${polyItems.length}`);
            if (polyItems[0].expression !== 'en serio') throw new Error(`Expected 'en serio', got ${polyItems[0].expression}`);
            if (polyItems[0].kind !== 'MWE') throw new Error(`Expected kind 'MWE', got ${polyItems[0].kind}`);

            const ambItems = collectChainItems(ambiguousCard);
            if (ambItems.length !== 1) throw new Error(`Expected 1 chain item for dar, got ${ambItems.length}`);
            if (ambItems[0].expression !== 'dar vueltas') throw new Error(`Expected 'dar vueltas', got ${ambItems[0].expression}`);

            const publishedItems = collectChainItems(publishedCard);
            if (publishedItems.length !== 1) throw new Error(`Expected 1 chain item for salvo, got ${publishedItems.length}`);
            if (publishedItems[0].expression !== 'a salvo') throw new Error(`Expected 'a salvo', got ${publishedItems[0].expression}`);

            const boundItems = collectChainItems(boundCard);
            if (boundItems.length !== 0) throw new Error(`Expected 0 chain items for repente, got ${boundItems.length}`);

            const dictCard = { targetWord: 'déjame', meanings: [standardDictPhrase] };
            if (collectChainItems(dictCard).length !== 0) throw new Error('dictionary PHRASE card should not chain');

            console.log('ALL_MWE_JS_TESTS_PASSED');
        """
        result = subprocess.run(
            ["node", "-", str(FLASHCARDS)], input=script, text=True,
            capture_output=True, check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr or result.stdout)
        self.assertIn("ALL_MWE_JS_TESTS_PASSED", result.stdout)


if __name__ == "__main__":
    unittest.main()
