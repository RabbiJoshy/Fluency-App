"""Vocabulary-group sampling and placement must remain distinct measurements."""
import shutil
import subprocess
import unittest
from pathlib import Path


@unittest.skipUnless(shutil.which('node'), 'Node.js required')
class EstimationTests(unittest.TestCase):
    def test_group_estimation_and_placement(self):
        result = subprocess.run(
            ['node', str(Path(__file__).with_name('estimation_checks.cjs'))],
            capture_output=True, text=True,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_detached_preparation(self):
        result = subprocess.run(
            ['node', str(Path(__file__).with_name('estimation_loading_checks.cjs'))],
            capture_output=True, text=True,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_recognition_choices_cognates_and_auto(self):
        result = subprocess.run(
            ['node', str(Path(__file__).with_name('estimation_placement_checks.cjs'))],
            capture_output=True, text=True,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_early_level_and_set_placement(self):
        result = subprocess.run(
            ['node', str(Path(__file__).with_name('estimation_set_checks.cjs'))],
            capture_output=True, text=True,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
