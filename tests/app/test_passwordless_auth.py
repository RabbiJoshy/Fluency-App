import subprocess
import unittest
from pathlib import Path


class PasswordlessAuthTests(unittest.TestCase):
    def test_guest_entry_and_navigation(self):
        root = Path(__file__).resolve().parents[2]
        result = subprocess.run(
            ["node", "backend/worker/tests/guest-auth.test.mjs"],
            cwd=root, text=True, capture_output=True,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_sessions_and_transport(self):
        root = Path(__file__).resolve().parents[2]
        result = subprocess.run(
            ["node", "backend/worker/tests/session-auth.test.mjs"],
            cwd=root, text=True, capture_output=True,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
