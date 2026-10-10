"""Every live Speech deck ships a Merge Lemmas list built for that deck.

The app ignores a list built for another release, or under another noun-merge
rule, and then merges nothing until a set's senses load. v23 went live on
2026-10-04 with v21 lists and nobody saw it for five days. The deploy runs
this test, so a deck cannot go live without its list.
"""

import json
import re
import unittest
from pathlib import Path

from fluency.sense_menu.noun_merge import RULE_VERSION


APP = Path(__file__).resolve().parents[2] / "app"
REBUILD = (
    "rebuild it: python scripts/build_merge_exceptions.py --language <code> "
    "[--extract <kaikki dump>] --release-index <workspace release>/app/vocabulary.index.json"
)


class MergeExceptionsCurrentTests(unittest.TestCase):
    def test_app_and_builder_agree_on_the_rule(self) -> None:
        vocab = (APP / "js/vocab.js").read_text(encoding="utf-8")
        accepted = set(re.findall(r"noun_merge_rule === '([^']+)'", vocab))
        self.assertEqual(accepted, {RULE_VERSION})

    def test_each_live_speech_deck_has_a_current_list(self) -> None:
        config = json.loads((APP / "config/config.json").read_text(encoding="utf-8"))
        checked = 0
        for name, language in config["languages"].items():
            index = str(language.get("indexPath") or "")
            if not index.startswith("releases/"):
                continue
            checked += 1
            with self.subTest(language=name):
                path = language.get("mergeExceptionsPath")
                self.assertTrue(path, f"{name} has a live deck but no mergeExceptionsPath")
                payload = json.loads((APP / path).read_text(encoding="utf-8"))
                release = payload.get("release_id")
                live = [index, str(language.get("releaseManifestPath") or "")]
                self.assertTrue(
                    release and any(f"/{release}/" in value for value in live),
                    f"{path} was built for {release}, but {name} serves {index}; {REBUILD}",
                )
                self.assertEqual(
                    payload.get("noun_merge_rule"), RULE_VERSION,
                    f"{path} predates noun merge rule {RULE_VERSION}; {REBUILD}",
                )
        self.assertGreater(checked, 0)


if __name__ == "__main__":
    unittest.main()
