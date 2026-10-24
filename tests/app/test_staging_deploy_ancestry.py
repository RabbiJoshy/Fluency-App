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

    def test_warn_or_check_staging_ancestry_warns_by_default(self):
        with patch.object(deploy, 'git', side_effect=[
            subprocess.CompletedProcess([], 0, 'repair-sha\n'),
            subprocess.CompletedProcess([], 1, ''),
        ]), patch('builtins.print') as mock_print:
            # Should not raise SystemExit
            deploy.warn_or_check_staging_ancestry('concurrent-chat-sha', strict=False)
            mock_print.assert_called()
            self.assertIn('consecutively', mock_print.call_args[0][0])

    def test_warn_or_check_staging_ancestry_blocks_when_strict(self):
        with patch.object(deploy, 'git', side_effect=[
            subprocess.CompletedProcess([], 0, 'repair-sha\n'),
            subprocess.CompletedProcess([], 1, ''),
        ]):
            with self.assertRaises(SystemExit):
                deploy.warn_or_check_staging_ancestry('concurrent-chat-sha', strict=True)

    def test_staging_deployment_lock_acquires_and_releases(self):
        import tempfile
        with tempfile.TemporaryDirectory() as tmpdir:
            test_lock = Path(tmpdir) / 'deploy.lock'
            with patch.object(deploy, 'STAGING_LOCK_FILE', test_lock), \
                 patch.object(deploy, 'STAGING_METADATA_DIR', Path(tmpdir)):
                with deploy.staging_deployment_lock(timeout_seconds=5, poll_interval=0.1):
                    self.assertTrue(test_lock.exists())

    def test_staging_deployment_lock_waits_when_held(self):
        import fcntl
        import os
        import tempfile
        import threading
        import time

        with tempfile.TemporaryDirectory() as tmpdir:
            test_lock = Path(tmpdir) / 'deploy.lock'
            fd = os.open(test_lock, os.O_CREAT | os.O_RDWR, 0o644)
            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)

            def release_later():
                time.sleep(0.3)
                fcntl.flock(fd, fcntl.LOCK_UN)
                os.close(fd)

            threading.Thread(target=release_later, daemon=True).start()

            with patch.object(deploy, 'STAGING_LOCK_FILE', test_lock), \
                 patch.object(deploy, 'STAGING_METADATA_DIR', Path(tmpdir)):
                # Should wait ~0.3s and then succeed
                t0 = time.time()
                with deploy.staging_deployment_lock(timeout_seconds=5, poll_interval=0.1):
                    self.assertTrue(test_lock.exists())
                self.assertGreaterEqual(time.time() - t0, 0.2)

    def test_staging_deployment_lock_times_out(self):
        import fcntl
        import os
        import tempfile

        with tempfile.TemporaryDirectory() as tmpdir:
            test_lock = Path(tmpdir) / 'deploy.lock'
            fd = os.open(test_lock, os.O_CREAT | os.O_RDWR, 0o644)
            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
            try:
                with patch.object(deploy, 'STAGING_LOCK_FILE', test_lock), \
                     patch.object(deploy, 'STAGING_METADATA_DIR', Path(tmpdir)):
                    with self.assertRaises(TimeoutError):
                        with deploy.staging_deployment_lock(timeout_seconds=0.2, poll_interval=0.05):
                            pass
            finally:
                fcntl.flock(fd, fcntl.LOCK_UN)
                os.close(fd)
