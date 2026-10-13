from pathlib import Path
import shutil
import subprocess
import unittest

ROOT = Path(__file__).resolve().parents[2]


@unittest.skipUnless(shutil.which("node"), "Node.js required")
class SavedItemsTests(unittest.TestCase):
    def test_persistence_and_phrase_examples(self):
        result = subprocess.run(["node", "tests/app/saved_items_checks.mjs"],
                                cwd=ROOT, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
