import subprocess
import unittest
from pathlib import Path

class StewardTests(unittest.TestCase):
    def test_roles_and_displayed_example_reporting(self):
        result = subprocess.run(['node', 'backend/worker/tests/steward.test.mjs'],
            cwd=Path(__file__).resolve().parents[2], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
