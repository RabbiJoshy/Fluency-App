from pathlib import Path
import shutil
import subprocess
import unittest

ROOT = Path(__file__).resolve().parents[2]


@unittest.skipUnless(shutil.which('node'), 'Node.js is required for progress overview checks')
class ProgressOverviewTests(unittest.TestCase):
    def test_knowledge_counts_and_dialog_lifecycle(self):
        result = subprocess.run(['node', str(ROOT / 'tests/app/progress_overview_checks.mjs')], cwd=ROOT, text=True, capture_output=True)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
