"""A syntax error in any boot module must block deployment, not strand sign-in."""
from pathlib import Path
import shutil
import subprocess
import unittest
ROOT = Path(__file__).resolve().parents[2]

@unittest.skipUnless(shutil.which('node'), 'Node.js required')
class JavaScriptSyntaxTests(unittest.TestCase):
    def test_app_modules_parse(self):
        for file in sorted((ROOT/'app/js').glob('*.js')):
            with self.subTest(module=file.name):
                result=subprocess.run(['node','--check',str(file)],capture_output=True,text=True)
                self.assertEqual(result.returncode,0,result.stderr)
