"""Memory tips name a real ending shift, and only against the card's own gloss."""

import shutil
import subprocess
import unittest
from pathlib import Path


MODULE = Path(__file__).resolve().parents[2] / "app/js/memory-tips.js"


class MemoryTipTests(unittest.TestCase):
    def _run(self, body: str) -> str:
        script = (
            f"import('{MODULE.as_uri()}').then(m => {{"
            "const tip = (w, g, l='spanish') => m.memoryTipFor({targetWord: w, meanings: [{meaning: g}]}, l);"
            f"{body}}});"
        )
        return subprocess.run(
            ["node", "-e", script], capture_output=True, text=True, check=True
        ).stdout.strip()

    @unittest.skipUnless(shutil.which("node"), "Node.js is needed to run JS tests")
    def test_adverb_ending_maps_to_ly(self) -> None:
        out = self._run("const t = tip('rápidamente','quickly; rapidly');"
                        "console.log(t.english, t.from, t.to);")
        self.assertEqual(out, "rapidly mente ly")

    @unittest.skipUnless(shutil.which("node"), "Node.js is needed to run JS tests")
    def test_false_friends_get_no_tip(self) -> None:
        # Same ending, different meaning: the gloss does not match the shift.
        out = self._run("console.log(tip('actualmente','currently'), tip('chica','girl'),"
                        " tip('guardia','guard'));")
        self.assertEqual(out, "null null null")

    @unittest.skipUnless(shutil.which("node"), "Node.js is needed to run JS tests")
    def test_unsupported_language_has_no_tip(self) -> None:
        out = self._run("console.log(tip('rychle','quickly','czech'));")
        self.assertEqual(out, "null")


if __name__ == "__main__":
    unittest.main()
