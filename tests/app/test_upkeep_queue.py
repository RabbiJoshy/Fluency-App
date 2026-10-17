from pathlib import Path
import subprocess
import unittest

class UpkeepQueueTests(unittest.TestCase):
    def test_answers_survive_coalescing_and_inflight_acknowledgements(self):
        result = subprocess.run(['node', 'backend/worker/tests/upkeep-queue.test.mjs'],
            cwd=Path(__file__).resolve().parents[2], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
