"""Exercise the rare-sense summary with a real part-of-speech badge."""

from pathlib import Path
import shutil
import subprocess
import unittest


FLASHCARDS = Path(__file__).resolve().parents[2] / "app/js/flashcards.js"


class RareSenseRenderTests(unittest.TestCase):
    @unittest.skipUnless(shutil.which("node"), "Node.js is needed to run the card renderer")
    def test_rare_sense_with_part_of_speech_renders(self) -> None:
        script = r"""
            const fs = require('node:fs');
            const vm = require('node:vm');
            const source = fs.readFileSync(process.argv[2], 'utf8');
            const start = source.indexOf('function posDisplayName(pos)');
            const end = source.indexOf('// Backup example sentences', start);
            if (start < 0 || end < 0) throw new Error('Rare-sense renderer missing');
            const context = {
                cardChainQueue: [{kind: 'RARE_SENSE', pos: 'NOUN', translation: 'a rare meaning', examples: []}],
                cardNavStack: [],
                escapeCardText: value => String(value),
                getPosColorClass: () => 'pos-noun',
                getPosAccentRgb: () => '100, 100, 100',
                exampleTargetText: () => '',
            };
            vm.runInNewContext(source.slice(start, end), context);
            const html = vm.runInNewContext("renderPhraseSummaryBack({chainParentWord: 'word'})", context);
            if (!html.includes('Noun') || !html.includes('a rare meaning')) {
                throw new Error('Rare sense was not rendered');
            }
        """
        result = subprocess.run(
            ["node", "-", str(FLASHCARDS)], input=script, text=True,
            capture_output=True, check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)


if __name__ == "__main__":
    unittest.main()
