import subprocess
import unittest
from pathlib import Path
class UpkeepTests(unittest.TestCase):
    def test_migration_scheduling_and_write_safety(self):
        result = subprocess.run(['node','backend/worker/tests/upkeep.test.mjs'],cwd=Path(__file__).resolve().parents[2],capture_output=True,text=True)
        self.assertEqual(result.returncode,0,result.stdout+result.stderr)
