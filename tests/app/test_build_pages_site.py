"""The deploy build stamps one version into every cache-busting tag."""

import importlib.util
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[2]
_spec = importlib.util.spec_from_file_location("build_pages_site", ROOT / "scripts/build_pages_site.py")
build_pages_site = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(build_pages_site)
stamp = build_pages_site.stamp


class StampTests(unittest.TestCase):
    def test_rewrites_tags_constants_and_cache_name(self) -> None:
        source = (
            "import './flashcards.js?v=20260927m3';\n"
            '<link rel="stylesheet" href="css/style.css?v=20260921freq">\n'
            "const ASSET_VERSION = '20260922mod';\n"
            "const MODALS_ASSET_VERSION = \"20260921rt\";\n"
            "const CACHE_NAME = 'flashcards-v570';\n"
            "const SHELL_CACHE_PREFIX = 'flashcards-v';\n"
            "`/js/offline-db.js?v=${ASSET_VERSION}`\n"
            "fetch('config/config.json')\n"
        )
        out = stamp(source, "abc12345")
        self.assertIn("import './flashcards.js?v=abc12345';", out)
        self.assertIn('css/style.css?v=abc12345"', out)
        self.assertIn("const ASSET_VERSION = 'abc12345';", out)
        self.assertIn('const MODALS_ASSET_VERSION = "abc12345";', out)
        # The number is kept so the shell-cache prefix still matches.
        self.assertIn("const CACHE_NAME = 'flashcards-v570-abc12345';", out)
        self.assertIn("const SHELL_CACHE_PREFIX = 'flashcards-v';", out)
        self.assertIn("`/js/offline-db.js?v=${ASSET_VERSION}`", out)
        self.assertIn("fetch('config/config.json')", out)

    def test_restamping_replaces_rather_than_appends(self) -> None:
        once = stamp("const CACHE_NAME = 'flashcards-v570';", "aaaa1111")
        self.assertEqual(stamp(once, "bbbb2222"), "const CACHE_NAME = 'flashcards-v570-bbbb2222';")

    def test_shipped_shell_carries_a_single_version(self) -> None:
        # One version across the shell means no module loads under two tags.
        for rel in ("index.html", "service-worker.js", "js/main.js", "js/flashcards.js"):
            text = stamp((ROOT / "app" / rel).read_text(encoding="utf-8"), "abc12345")
            tags = set(re.findall(r"\.(?:js|css)\?v=([A-Za-z0-9_.-]+)", text))
            self.assertLessEqual(tags, {"abc12345"}, rel)


if __name__ == "__main__":
    unittest.main()
