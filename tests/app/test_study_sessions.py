"""SETWISE: session size is independent of level milestones."""
import shutil
import subprocess
import unittest
from pathlib import Path


@unittest.skipUnless(shutil.which('node'), 'Node.js required')
class StudySessionTests(unittest.TestCase):
    def test_session_membership_progress_and_continuation(self):
        result = subprocess.run(
            ['node', str(Path(__file__).with_name('study_session_checks.cjs'))],
            capture_output=True, text=True,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
