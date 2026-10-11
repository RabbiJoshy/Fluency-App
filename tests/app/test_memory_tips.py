"""Memory tips build a step-by-step link from the card's own English glosses."""

import shutil
import subprocess
import unittest
from pathlib import Path


MODULE = Path(__file__).resolve().parents[2] / "app/js/memory-tips.js"


class MemoryTipTests(unittest.TestCase):
    def _run(self, body: str) -> str:
        script = (
            f"import('{MODULE.as_uri()}').then(m => {{"
            "const tip = (w, g, l='spanish') => m.memoryTipFor("
            "{targetWord: w, meanings: [{meaning: g}]}, l);"
            f"{body}}});"
        )
        return subprocess.run(
            ["node", "-e", script], capture_output=True, text=True, check=True
        ).stdout.strip()

    @unittest.skipUnless(shutil.which("node"), "Node.js is needed to run JS tests")
    def test_adverb_ending_is_a_named_pattern_with_steps(self) -> None:
        out = self._run(
            "const t = tip('rápidamente','quickly; rapidly');"
            "console.log(t.english, t.tier, t.from, t.to, t.steps.map(s => s.kind).join('>'));"
        )
        self.assertEqual(out, "rapidly pattern mente ly accent>rule>drop")

    @unittest.skipUnless(shutil.which("node"), "Node.js is needed to run JS tests")
    def test_same_spelling_and_verb_drop(self) -> None:
        out = self._run(
            "console.log(tip('hotel','hotel').tier, tip('informar','to inform').tier,"
            " tip('informar','to inform').english);"
        )
        self.assertEqual(out, "same pattern inform")

    @unittest.skipUnless(shutil.which("node"), "Node.js is needed to run JS tests")
    def test_a_loose_link_is_offered_as_loose(self) -> None:
        out = self._run("const t = tip('tiempo','time'); console.log(t.tier, t.english);")
        self.assertEqual(out, "loose time")

    @unittest.skipUnless(shutil.which("node"), "Node.js is needed to run JS tests")
    def test_unrelated_meaning_gets_no_tip(self) -> None:
        # Same ending shape, but the card's own gloss is a different word.
        out = self._run(
            "console.log(tip('actualmente','currently'), tip('chica','girl'),"
            " tip('embarazada','pregnant'));"
        )
        self.assertEqual(out, "null null null")

    @unittest.skipUnless(shutil.which("node"), "Node.js is needed to run JS tests")
    def test_the_decks_own_lemma_is_not_an_english_partner(self) -> None:
        out = self._run(
            "console.log(m.memoryTipFor({targetWord:'gostaram', meanings:["
            "{meaning:'gostar', headword:'gostar'}]}, 'portuguese'));"
        )
        self.assertEqual(out, "null")

    @unittest.skipUnless(shutil.which("node"), "Node.js is needed to run JS tests")
    def test_unsupported_language_has_no_tip(self) -> None:
        out = self._run("console.log(tip('rychle','quickly','czech'));")
        self.assertEqual(out, "null")


if __name__ == "__main__":
    unittest.main()
