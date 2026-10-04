"""Surface scorers are discovered, declared per pair, and edit-distance/v1
behaves the way decision 0027 says it does."""

import json
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path

from fluency.features.cognates import CognatePolicy, CognatePolicyError, form_score, load_policy
from fluency.features.surface_scorers import available_scorers

CONFIG_ROOT = Path(__file__).resolve().parents[2] / "config"


class DiscoveryTests(unittest.TestCase):
    def test_scorers_are_found_by_listing_the_package(self) -> None:
        self.assertIn("edit-distance/v1", available_scorers())
        self.assertIn("legacy-max4/v1", available_scorers())

    def test_an_unknown_scorer_is_refused(self) -> None:
        with self.assertRaises(CognatePolicyError):
            CognatePolicy(target_language="es", known_language="en", surface_scorer="nope/v1")

    def test_a_policy_file_must_name_its_scorer(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "cognates").mkdir()
            (root / "cognates" / "es-en.json").write_text(
                json.dumps({"target_language": "es", "known_language": "en"}), encoding="utf-8"
            )
            with self.assertRaises(CognatePolicyError):
                load_policy(root, "es", "en")

    def test_every_shipped_pair_declares_one(self) -> None:
        for path in sorted((CONFIG_ROOT / "cognates").glob("*.json")):
            target, known = path.stem.split("-", 1)
            policy = load_policy(CONFIG_ROOT, target, known)
            self.assertEqual(policy.surface_scorer, "learner-align/v1", path.name)


class EditDistanceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.es = load_policy(CONFIG_ROOT, "es", "en")

    def test_short_lookalikes_no_longer_pass(self) -> None:
        # Jaro-Winkler gave these 0.75-0.85; they are not transparent.
        self.assertLess(form_score("este", "east", self.es), 0.6)
        self.assertLess(form_score("toho", "the", load_policy(CONFIG_ROOT, "cs", "en")), 0.6)

    def test_the_length_guard_is_part_of_the_score(self) -> None:
        self.assertEqual(form_score("eres", "be", self.es), 0.0)

    def test_regular_endings_are_read_through(self) -> None:
        self.assertEqual(form_score("necesidad", "necessity", self.es), 1.0)
        self.assertEqual(form_score("información", "information", self.es), 1.0)

    def test_rewrite_rules_apply_to_both_sides(self) -> None:
        # The one-sided c->k rule dropped this to 0.55.
        self.assertGreaterEqual(form_score("comunicar", "communicate", self.es), 0.8)

    def test_the_legacy_scorer_is_still_reachable(self) -> None:
        legacy = replace(self.es, surface_scorer="legacy-max4/v1")
        self.assertGreater(form_score("este", "east", legacy), 0.8)


class LearnerAlignTests(unittest.TestCase):
    def setUp(self) -> None:
        self.es = replace(load_policy(CONFIG_ROOT, "es", "en"), surface_scorer="learner-align/v1")
        self.pt = replace(load_policy(CONFIG_ROOT, "pt", "en"), surface_scorer="learner-align/v1")
        self.cs_pl = replace(load_policy(CONFIG_ROOT, "cs", "pl"), surface_scorer="learner-align/v1")
        self.cs_en = replace(load_policy(CONFIG_ROOT, "cs", "en"), surface_scorer="learner-align/v1")

    def test_captures_obvious_cognates_missed_by_edit_distance(self) -> None:
        # Decision 0027: capitán/captain and número/number missed by edit-distance
        self.assertGreaterEqual(form_score("capitán", "captain", self.es), 0.75)
        self.assertGreaterEqual(form_score("número", "number", self.es), 0.75)
        self.assertGreaterEqual(form_score("capitão", "captain", self.pt), 0.75)
        self.assertGreaterEqual(form_score("número", "number", self.pt), 0.75)

    def test_regular_endings_preserved(self) -> None:
        self.assertEqual(form_score("eternidad", "eternity", self.es), 1.0)
        self.assertEqual(form_score("necesidad", "necessity", self.es), 1.0)
        self.assertEqual(form_score("información", "information", self.es), 1.0)

    def test_short_lookalikes_do_not_overmatch(self) -> None:
        # Short words do not get vowel substitution discounts
        self.assertLess(form_score("este", "east", self.es), 0.6)
        self.assertLess(form_score("toho", "the", self.cs_en), 0.6)

    def test_length_guard_enforced(self) -> None:
        self.assertEqual(form_score("eres", "be", self.es), 0.0)

    def test_czech_polish_shared_inflections(self) -> None:
        self.assertEqual(form_score("můj", "mój", self.cs_pl), 1.0)
        self.assertEqual(form_score("bůh", "bóg", self.cs_pl), 1.0)



if __name__ == "__main__":
    unittest.main()
