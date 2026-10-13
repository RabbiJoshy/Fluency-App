from pathlib import Path
import shutil
import subprocess
import unittest

ROOT = Path(__file__).resolve().parents[2]


@unittest.skipUnless(shutil.which("node"), "Node.js required")
class MusicWorkspaceTests(unittest.TestCase):
    def test_navigation_and_control_ownership(self):
        result = subprocess.run(
            ["node", "tests/app/music_workspace_checks.mjs"],
            cwd=ROOT, capture_output=True, text=True,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
