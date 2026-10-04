import json
import os
import shutil
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


class SplitCardsAppTests(unittest.TestCase):
    @unittest.skipUnless(shutil.which("node"), "Node.js is needed to run JS vm tests")
    def test_split_card_detection_and_structure(self) -> None:
        script = r"""
            const fs = require('node:fs');
            const vm = require('node:vm');
            const vocab = fs.readFileSync(process.env.VOCAB_JS, 'utf8');
            const pure = vocab.slice(vocab.indexOf('// lemma-merge-pure'), vocab.indexOf('// /lemma-merge-pure'));
            const context = { console };
            context.globalThis = context;
            vm.runInNewContext(pure, context);

            const fueItem = {
                word: 'fue',
                meanings: [
                    { headword: 'ser', pos: 'VERB', translation: 'was/were', percentage: 50 },
                    { headword: 'ser', pos: 'VERB', translation: 'existed', percentage: 31 },
                    { headword: 'ir', pos: 'VERB', translation: 'went', percentage: 15 },
                    { headword: 'ir', pos: 'VERB', translation: 'departed', percentage: 4 }
                ]
            };

            const splitFue = context.detectSplitCardTuples(fueItem, 'es');

            const llamaItem = {
                word: 'llama',
                meanings: [
                    { headword: 'llamar', pos: 'VERB', translation: 'to call', percentage: 45 },
                    { headword: 'llamar', pos: 'VERB', translation: 'to name', percentage: 15 },
                    { headword: 'llamarse', pos: 'VERB', translation: 'to be named', percentage: 35 },
                    { headword: 'llamarse', pos: 'VERB', translation: 'to be called', percentage: 5 }
                ]
            };

            const splitLlama = context.detectSplitCardTuples(llamaItem, 'es');

            const regularItem = {
                word: 'banco',
                meanings: [
                    { headword: 'banco', pos: 'NOUN', translation: 'bank', percentage: 70 },
                    { headword: 'banco', pos: 'NOUN', translation: 'bench', percentage: 20 },
                    { headword: 'banco', pos: 'NOUN', translation: 'school of fish', percentage: 10 }
                ]
            };
            const splitRegular = context.detectSplitCardTuples(regularItem, 'es');

            const hacerItem = {
                word: 'hace',
                meanings: [
                    { headword: 'hacer', pos: 'VERB', translation: 'he makes', percentage: 55 },
                    { headword: 'hacer', pos: 'VERB', translation: 'he does', percentage: 20 },
                    { headword: 'hacerse', pos: 'VERB', translation: 'he becomes', percentage: 20 },
                    { headword: 'hacerse', pos: 'VERB', translation: 'he pretends', percentage: 5 }
                ]
            };
            const splitHacer = context.detectSplitCardTuples(hacerItem, 'es');

            const fazerItem = {
                word: 'faz',
                meanings: [
                    { headword: 'fazer', pos: 'VERB', translation: 'faz / makes', percentage: 70 },
                    { headword: 'fazer', pos: 'VERB', translation: 'does', percentage: 10 },
                    { headword: 'fazerse', pos: 'VERB', translation: 'torna-se / becomes', percentage: 15 },
                    { headword: 'fazerse', pos: 'VERB', translation: 'pretends', percentage: 5 }
                ]
            };
            const splitFazer = context.detectSplitCardTuples(fazerItem, 'pt');

            process.stdout.write(JSON.stringify({ splitFue, splitLlama, splitRegular, splitHacer, splitFazer }));
        """
        completed = subprocess.run(
            ["node", "-e", script], check=False, capture_output=True, text=True,
            env={**os.environ, "VOCAB_JS": str(ROOT / "app/js/vocab.js")},
        )
        if completed.returncode != 0:
            self.fail(completed.stderr or completed.stdout)
        data = json.loads(completed.stdout)

        split_fue = data["splitFue"]
        self.assertIsNotNone(split_fue)
        self.assertEqual(split_fue["kind"], "homograph")
        self.assertEqual(split_fue["tuple1"]["headword"], "ser")
        self.assertEqual(split_fue["tuple2"]["headword"], "ir")
        self.assertGreaterEqual(split_fue["tuple1"]["share"], 0.5)
        self.assertGreaterEqual(split_fue["tuple2"]["share"], 0.14)

        split_llama = data["splitLlama"]
        self.assertIsNotNone(split_llama)
        self.assertEqual(split_llama["kind"], "reflexive")
        self.assertEqual(split_llama["tuple1"]["headword"], "llamar")
        self.assertEqual(split_llama["tuple2"]["headword"], "llamarse")

        self.assertIsNone(data["splitRegular"])

        split_hacer = data["splitHacer"]
        self.assertIsNotNone(split_hacer)
        self.assertEqual(split_hacer["kind"], "reflexive")
        self.assertEqual(split_hacer["tuple1"]["headword"], "hacer")
        self.assertEqual(split_hacer["tuple2"]["headword"], "hacerse")

        split_fazer = data["splitFazer"]
        self.assertIsNotNone(split_fazer)
        self.assertEqual(split_fazer["kind"], "reflexive")
        self.assertEqual(split_fazer["tuple1"]["headword"], "fazer")
        self.assertEqual(split_fazer["tuple2"]["headword"], "fazerse")


if __name__ == "__main__":
    unittest.main()
