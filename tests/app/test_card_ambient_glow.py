"""Exercise getCardAmbientGlow POS color handling, rare use filtering, and merged lemmas."""

from pathlib import Path
import shutil
import subprocess
import unittest

ROOT = Path(__file__).resolve().parents[2]
FW_CARD = ROOT / "app/js/function-word-card.js"


class CardAmbientGlowTests(unittest.TestCase):
    @unittest.skipUnless(shutil.which("node"), "Node.js is needed to run JS vm tests")
    def test_ambient_glow_behavior(self) -> None:
        script = r"""
            const fs = require('node:fs');
            const vm = require('node:vm');
            const source = fs.readFileSync(process.argv[2], 'utf8');

            // Set up a mock environment to load getCardAmbientGlow
            const context = {
                console,
                window: {},
                getGrammarWordDefinition: () => null,
            };
            context.globalThis = context;
            context.window = context;

            // Load module contents
            // Extract getCardAmbientGlow and helpers
            vm.runInNewContext(source.replace(/^export\s+/gm, ''), context);

            const mockGetRgb = (pos) => {
                const map = {
                    'VERB': '0, 212, 170',
                    'verb': '0, 212, 170',
                    'pos-verb': '0, 212, 170',
                    'AUX': '0, 212, 170',
                    'NOUN': '74, 158, 255',
                    'noun': '74, 158, 255',
                    'pos-noun': '74, 158, 255',
                    'ADJ': '245, 166, 35',
                    'adj': '245, 166, 35',
                    'pos-adj': '245, 166, 35',
                    'PREP': '236, 72, 153',
                    'prep': '236, 72, 153',
                    'pos-prep': '236, 72, 153',
                };
                return map[pos] || '148, 163, 184';
            };

            const getGlow = (card, lang = 'es', activePos = null, isSplit = false) => {
                return context.getCardAmbientGlow(card, lang, activePos, isSplit, mockGetRgb);
            };

            // 1. Merged lemma card: must only have single verb (green) glow
            const mergedCard = {
                mergedLemma: true,
                partOfSpeech: 'VERB',
                meanings: [
                    { pos: 'VERB', meaning: 'to run', percentage: 0.8 },
                    { pos: 'NOUN', meaning: 'run', percentage: 0.2 },
                ]
            };
            const mergedGlow = getGlow(mergedCard);
            if (!mergedGlow.includes('rgba(0, 212, 170, 0.18)')) {
                throw new Error('Merged lemma should have verb green glow: ' + mergedGlow);
            }
            if (mergedGlow.includes('rgba(74, 158, 255')) {
                throw new Error('Merged lemma should NOT have noun glow: ' + mergedGlow);
            }
            if (mergedGlow.includes('radial-gradient(circle at 22%') || mergedGlow.includes('radial-gradient(circle at 78%')) {
                throw new Error('Merged lemma should only have single centered glow: ' + mergedGlow);
            }

            // 2. Word with multiple POS where one is a rare use (e.g. unassigned or low share)
            const cardWithRareNoun = {
                partOfSpeech: 'VERB',
                meanings: [
                    { pos: 'VERB', meaning: 'to speak', percentage: 0.96, targetSentence: 'Hablo español.' },
                    { pos: 'NOUN', meaning: 'speech', percentage: 0.04, targetSentence: 'El habla.' },
                ]
            };
            const rareNounGlow = getGlow(cardWithRareNoun);
            if (!rareNounGlow.includes('rgba(0, 212, 170, 0.18)')) {
                throw new Error('Card should have verb glow: ' + rareNounGlow);
            }
            if (rareNounGlow.includes('rgba(74, 158, 255')) {
                throw new Error('Card should NOT have glow for rare noun use: ' + rareNounGlow);
            }

            // 2b. Card with meaning flagged as rare / unassigned
            const cardWithUnassignedNoun = {
                partOfSpeech: 'VERB',
                meanings: [
                    { pos: 'VERB', meaning: 'to do', percentage: 1.0, allExamples: [{ target: 'hace' }] },
                    { pos: 'NOUN', meaning: 'make', unassigned: true, percentage: 0 },
                ]
            };
            const unassignedNounGlow = getGlow(cardWithUnassignedNoun);
            if (unassignedNounGlow.includes('rgba(74, 158, 255')) {
                throw new Error('Card should NOT have glow for unassigned noun: ' + unassignedNounGlow);
            }

            // 3. Genuine multi-POS word (e.g. 50% noun, 50% adjective)
            const multiPosCard = {
                partOfSpeech: 'NOUN',
                meanings: [
                    { pos: 'NOUN', meaning: 'a secret', percentage: 0.5, allExamples: [{ target: 'un secreto' }] },
                    { pos: 'ADJ', meaning: 'secret', percentage: 0.5, allExamples: [{ target: 'agente secreto' }] },
                ]
            };
            const multiPosGlow = getGlow(multiPosCard);
            if (!multiPosGlow.includes('rgba(74, 158, 255, 0.17)') || !multiPosGlow.includes('rgba(245, 166, 35, 0.17)')) {
                throw new Error('Multi-POS card should have both noun and adj colors: ' + multiPosGlow);
            }
            if (!multiPosGlow.includes('circle at 22% 16%') || !multiPosGlow.includes('circle at 78% 16%')) {
                throw new Error('Multi-POS card should have multi-corner glow: ' + multiPosGlow);
            }

            // 4. Multiple meanings that share the same color (VERB + AUX)
            const sameColorCard = {
                partOfSpeech: 'VERB',
                meanings: [
                    { pos: 'VERB', meaning: 'to have', percentage: 0.6, allExamples: [{ target: 'he' }] },
                    { pos: 'AUX', meaning: 'have (auxiliary)', percentage: 0.4, allExamples: [{ target: 'he hablado' }] },
                ]
            };
            const sameColorGlow = getGlow(sameColorCard);
            if (!sameColorGlow.includes('circle at 50% 20%')) {
                throw new Error('Same-color POS meanings should produce a single centered glow: ' + sameColorGlow);
            }

            // 5. Function word: should NOT have white halo (212, 218, 245), should have normal POS glow
            const functionWordCard = {
                word: 'de',
                targetWord: 'de',
                functionWord: true,
                partOfSpeech: 'PREP',
                meanings: [
                    { pos: 'PREP', meaning: 'of / from', percentage: 1.0, targetSentence: 'de nada' }
                ]
            };
            const fwGlow = getGlow(functionWordCard, 'pt');
            if (fwGlow.includes('212, 218, 245')) {
                throw new Error('Function word should NOT have white halo: ' + fwGlow);
            }
            if (!fwGlow.includes('rgba(236, 72, 153, 0.18)')) {
                throw new Error('Function word should have preposition POS glow: ' + fwGlow);
            }
        """
        result = subprocess.run(
            ["node", "-", str(FW_CARD)],
            input=script,
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)


if __name__ == "__main__":
    unittest.main()
