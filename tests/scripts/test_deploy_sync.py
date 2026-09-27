"""scripts/deploy.py keeps a shared checkout current with main.

Reproduces the failure it exists to prevent: another session's uncommitted
edit sits in a file main also changed, git refuses the merge, and the
checkout falls behind main. Each test builds a throwaway origin and clone.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[2] / "scripts" / "deploy.py"


def run(*args: str, cwd: Path) -> str:
    env = {**os.environ, "GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@t",
           "GIT_COMMITTER_NAME": "t", "GIT_COMMITTER_EMAIL": "t@t"}
    return subprocess.run(args, cwd=cwd, check=True, text=True, capture_output=True, env=env).stdout


class DeploySyncTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = Path(tempfile.mkdtemp())
        origin, self.clone, other = self.tmp / "origin.git", self.tmp / "clone", self.tmp / "other"
        run("git", "init", "-q", "--bare", "-b", "main", str(origin), cwd=self.tmp)
        run("git", "clone", "-q", str(origin), str(self.clone), cwd=self.tmp)
        (self.clone / "scripts").mkdir()
        shutil.copy(SCRIPT, self.clone / "scripts" / "deploy.py")
        (self.clone / "page.txt").write_text("title\nbody\nfooter\n")
        run("git", "add", ".", cwd=self.clone)
        run("git", "commit", "-q", "-m", "base", cwd=self.clone)
        run("git", "push", "-q", "origin", "HEAD:main", cwd=self.clone)
        # Another session changes the first line of page.txt on main.
        run("git", "clone", "-q", str(origin), str(other), cwd=self.tmp)
        (other / "page.txt").write_text("TITLE\nbody\nfooter\n")
        run("git", "commit", "-q", "-am", "main moves", cwd=other)
        run("git", "push", "-q", "origin", "HEAD:main", cwd=other)

    def tearDown(self) -> None:
        shutil.rmtree(self.tmp, ignore_errors=True)

    def sync(self) -> subprocess.CompletedProcess[str]:
        return subprocess.run([sys.executable, "scripts/deploy.py", "--sync"], cwd=self.clone,
                              text=True, capture_output=True)

    def test_uncommitted_edit_in_a_file_main_changed_is_carried_across(self) -> None:
        (self.clone / "page.txt").write_text("title\nbody\nFOOTER (unsaved)\n")
        result = self.sync()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(run("git", "rev-list", "--count", "HEAD..origin/main", cwd=self.clone).strip(), "0")
        self.assertEqual((self.clone / "page.txt").read_text(), "TITLE\nbody\nFOOTER (unsaved)\n")
        self.assertIn("page.txt", run("git", "diff", "--name-only", cwd=self.clone))
        self.assertEqual(run("git", "stash", "list", cwd=self.clone).strip(), "")

    def test_clashing_edit_leaves_the_checkout_untouched(self) -> None:
        (self.clone / "page.txt").write_text("Title (unsaved)\nbody\nfooter\n")
        before = run("git", "rev-parse", "HEAD", cwd=self.clone)
        result = self.sync()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("page.txt", result.stderr)
        self.assertEqual(run("git", "rev-parse", "HEAD", cwd=self.clone), before)
        self.assertEqual((self.clone / "page.txt").read_text(), "Title (unsaved)\nbody\nfooter\n")
        self.assertEqual(run("git", "stash", "list", cwd=self.clone).strip(), "")
        self.assertEqual(run("git", "worktree", "list", cwd=self.clone).count("\n"), 1)


if __name__ == "__main__":
    unittest.main()
