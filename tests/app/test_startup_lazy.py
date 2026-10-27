"""Optional tutorial loading must preserve onboarding and retry behavior."""
from pathlib import Path
import shutil
import subprocess
import unittest

ROOT = Path(__file__).resolve().parents[2]


@unittest.skipUnless(shutil.which('node'), 'Node.js required')
class StartupLazyTests(unittest.TestCase):
    def test_optional_tutorial_loading(self):
        result = subprocess.run(
            ['node', 'tests/app/startup_lazy_checks.mjs'],
            cwd=ROOT, capture_output=True, text=True,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
