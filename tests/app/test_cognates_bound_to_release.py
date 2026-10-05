"""Each committed cognates file must be bound to the release config loads.

The app trusts a file's per-card verdicts only for `built_from_release_id`.
When config moved Portuguese and Spanish to v23 the files still named v21, so
Smart Skip silently found 0 look-alikes. Rebind with scripts/rebind_cognates.py.
"""

import json
import unittest
from pathlib import Path

APP = Path(__file__).resolve().parents[2] / "app"


class CognatesBoundToReleaseTests(unittest.TestCase):
    def test_built_from_release_matches_config(self) -> None:
        config = json.loads((APP / "config" / "config.json").read_text(encoding="utf-8"))
        checked = 0
        for name, lang in config["languages"].items():
            path = lang.get("cognatesPath")
            if not path or not (APP / path).exists():
                continue
            payload = json.loads((APP / path).read_text(encoding="utf-8"))
            built = payload.get("built_from_release_id")
            if not built or not payload.get("cards"):
                continue
            paths = [str(lang.get("indexPath") or ""), str(lang.get("releaseManifestPath") or "")]
            with self.subTest(language=name):
                self.assertTrue(any(f"/{built}/" in p for p in paths),
                                f"{path} built for {built}, config loads {paths[0]}")
            checked += 1
        self.assertGreater(checked, 0)


if __name__ == "__main__":
    unittest.main()
