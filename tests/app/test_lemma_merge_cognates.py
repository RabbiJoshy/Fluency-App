import os
import shutil
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
VOCAB_JS = ROOT / "app/js/vocab.js"


class LemmaMergeCognatesTests(unittest.TestCase):
    @unittest.skipUnless(shutil.which("node"), "Node.js is needed to run JS vm tests")
    def test_anti_hydra_lemma_cognate_skipping(self) -> None:
        script = r"""
            const fs = require('node:fs');
            const vm = require('node:vm');
            let vocabSource = fs.readFileSync(process.env.VOCAB_JS, 'utf8')
                .replace(/^import .*$/mg, '')
                .replace(/^export /mg, '');
            const context = {
                console, localStorage: { getItem: () => null, setItem: () => {} },
                document: { readyState: 'complete', getElementById: () => null, addEventListener: () => {} },
                window: { addEventListener: () => {} },
                selectedLanguage: 'spanish',
                activeArtist: null,
                artistVocabularyScope: 'main',
                config: { languages: { spanish: { routeCode: 'es', name: 'Spanish' } } },
                cognateThreshold: 0.75,
                isCognateKnown: item => (item.cognate_scores?.en || item.cognate_score || 0) >= 0.75,
                percentageMode: false,
                excludeSlang: false,
                excludeProperNouns: false,
                excludeEnglishLoanwords: false,
                excludeGrammarParticles: false,
                spuriousSelfInfinitives: new Set(),
            };
            context.globalThis = context;
            vm.runInNewContext(vocabSource, context);

            const fail = msg => { console.error(msg); process.exit(1); };

            // Mock deck with a cognate infinitive and non-cognate past tense form
            const mockDeck = [
                {
                    word: 'decidir',
                    stableRank: 10,
                    rank: 10,
                    corpus_count: 500,
                    meanings: [{ pos: 'VERB', headword: 'decidir', translation: 'to decide' }],
                    cognate_score: 0.85,
                    cognate_scores: { en: 0.85 } // Cognate in English
                },
                {
                    word: 'decidió',
                    stableRank: 20,
                    rank: 20,
                    corpus_count: 300,
                    meanings: [{ pos: 'VERB', headword: 'decidir', translation: 'he decided' }],
                    cognate_score: 0.50,
                    cognate_scores: { en: 0.50 } // Below cutoff (not cognate on surface)
                },
                {
                    word: 'casa',
                    stableRank: 30,
                    rank: 30,
                    corpus_count: 1000,
                    meanings: [{ pos: 'NOUN', headword: 'casa', translation: 'house' }],
                    cognate_scores: { en: 0.10 } // Not cognate
                }
            ];

            // TEST 1: Merge Lemmas is ON and Exclude Cognates is ON
            // The lemma 'decidir' is a cognate. 'decidió' must NOT sprout as a zombie representative card.
            context.useLemmaMode = true;
            context.lemmaFieldAvailable = true;
            context.excludeCognates = true;
            context.cognateFieldAvailable = true;

            const filteredMerged = context.buildFilteredVocab(mockDeck);
            const wordsMerged = (filteredMerged.vocab || filteredMerged).map(item => item.word);
            if (wordsMerged.includes('decidir')) fail('decidir should be excluded as a cognate in merged mode');
            if (wordsMerged.includes('decidió')) fail('Anti-Hydra violation: decidió sprouted as a zombie card in merged mode!');
            if (!wordsMerged.includes('casa')) fail('casa should remain in merged deck');

            // TEST 2: Merge Lemmas is OFF (Surface Mode) and Exclude Cognates is ON
            // 'decidir' is excluded as a cognate. 'decidió' must STAY in the deck for surface practice.
            context.useLemmaMode = false;
            context.excludeCognates = true;

            const filteredSurface = context.buildFilteredVocab(mockDeck);
            const wordsSurface = (filteredSurface.vocab || filteredSurface).map(item => item.word);
            if (wordsSurface.includes('decidir')) fail('decidir should be excluded as a cognate in surface mode');
            if (!wordsSurface.includes('decidió')) fail('decidió should remain in surface mode for conjugation drill');
            if (!wordsSurface.includes('casa')) fail('casa should remain in surface mode');

            console.log('Anti-hydra and surface mode tests passed successfully');
        """
        completed = subprocess.run(
            ["node", "-e", script],
            env={**os.environ, "VOCAB_JS": str(VOCAB_JS)},
            capture_output=True, text=True,
        )
        self.assertEqual(completed.returncode, 0, completed.stderr + completed.stdout)


if __name__ == "__main__":
    unittest.main()
