"""Parallel staging deployments must not silently remove another repair."""
import importlib.util
from pathlib import Path
import subprocess
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location('deploy_staging_guard', ROOT / 'scripts/deploy_staging.py')
deploy = importlib.util.module_from_spec(spec)
spec.loader.exec_module(deploy)


class StagingDeployAncestryTests(unittest.TestCase):
    def test_rejects_branch_that_drops_the_staged_repair(self):
        with patch.object(deploy, 'git', side_effect=[
            subprocess.CompletedProcess([], 0, 'repair-sha\n'),
            subprocess.CompletedProcess([], 1, ''),
        ]):
            with self.assertRaisesRegex(SystemExit, 'does not include.*staging release'):
                deploy.check_staging_ancestry('older-branch')

    def test_accepts_a_build_including_the_current_staging_release(self):
        with patch.object(deploy, 'git', side_effect=[
            subprocess.CompletedProcess([], 0, 'repair-sha\n'),
            subprocess.CompletedProcess([], 0, ''),
        ]) as git:
            deploy.check_staging_ancestry('merged-build')
            self.assertEqual(git.call_args.args, ('merge-base', '--is-ancestor', 'repair-sha', 'merged-build'))

    def test_allows_the_first_staging_deployment(self):
        with patch.object(deploy, 'git', return_value=subprocess.CompletedProcess([], 128, '')):
            deploy.check_staging_ancestry('first-build')
