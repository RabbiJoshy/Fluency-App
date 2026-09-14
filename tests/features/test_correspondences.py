"""A language pair learning its own correspondences, unsupervised."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from fluency.features.correspondences import (
    GAP,
    Correspondences,
    align,
    learn_correspondences,
    load_correspondences,
)


def plain(left: str, right: str) -> float:
    """A baseline that only ever agrees with itself, so seeding is explicit."""

    if not left or not right:
        return 0.0
    same = sum(1 for a, b in zip(left, right) if a == b)
    return same / max(len(left), len(right))


class AlignTests(unittest.TestCase):
    def test_equal_words_align_position_for_position(self):
        self.assertEqual(align("kot", "kot"), [("k", "k"), ("o", "o"), ("t", "t")])

    def test_a_substitution_is_one_aligned_pair(self):
        self.assertEqual(align("kot", "kat"), [("k", "k"), ("o", "a"), ("t", "t")])

    def test_a_deletion_produces_a_gap_on_the_right(self):
        self.assertIn(("t", GAP), align("kot", "ko"))

    def test_an_insertion_produces_a_gap_on_the_left(self):
        self.assertIn((GAP, "t"), align("ko", "kot"))

    def test_empty_against_a_word_is_all_gaps(self):
        self.assertEqual(align("", "ko"), [(GAP, "k"), (GAP, "o")])


class LearningTests(unittest.TestCase):
    """v/w recurs across the seeds; q/z happens once and is noise."""

    def corpus(self) -> list[tuple[str, str]]:
        pairs = [
            ("voda", "woda"),
            ("vino", "wino"),
            ("veta", "weta"),
            ("vosa", "wosa"),
            ("vlas", "wlas"),
            ("vrata", "wrata"),
            ("qat", "zat"),
        ]
        return pairs

    def learn(self, **overrides) -> Correspondences:
        settings = dict(
            target_language="cs",
            known_language="pl",
            baseline=plain,
            seed_threshold=0.6,
            minimum_count=3,
            rounds=1,
        )
        settings.update(overrides)
        return learn_correspondences(self.corpus(), **settings)

    def test_a_recurring_correspondence_is_found(self):
        self.assertIn(("v", "w"), self.learn().costs)

    def test_a_one_off_is_noise_and_is_not_learned(self):
        self.assertNotIn(("q", "z"), self.learn().costs)

    def test_a_learned_correspondence_costs_less_than_an_unrelated_one(self):
        learned = self.learn()
        self.assertLess(learned.cost("v", "w"), learned.cost("v", "k"))

    def test_identity_is_free_and_never_stored(self):
        learned = self.learn()
        self.assertEqual(learned.cost("a", "a"), 0.0)
        self.assertNotIn(("a", "a"), learned.costs)

    def test_an_unknown_pair_costs_a_full_substitution(self):
        self.assertEqual(self.learn().cost("x", "q"), 1.0)

    def test_a_regular_correspondence_is_cheap_but_never_free(self):
        """Or two words differing only in it would be indistinguishable."""

        self.assertGreater(self.learn().cost("v", "w"), 0.0)

    def test_similarity_rises_once_the_correspondence_is_known(self):
        learned = self.learn()
        # Plain agreement scores voda/woda at 3 of 4; knowing v>w costs 0.15
        # instead of a whole substitution, so the pair scores higher.
        self.assertGreater(learned.similarity("voda", "woda"), 0.8)

    def test_nothing_alike_enough_to_seed_learns_nothing(self):
        learned = self.learn(seed_threshold=1.01)
        self.assertEqual(learned.costs, {})
        self.assertEqual(learned.seed_count, 0)

    def test_the_seed_count_and_rounds_are_recorded(self):
        learned = self.learn(rounds=2)
        self.assertGreater(learned.seed_count, 0)
        self.assertEqual(learned.rounds, 2)

    def test_normalising_is_applied_before_alignment(self):
        learned = learn_correspondences(
            [("vóda", "woda"), ("víno", "wino"), ("véta", "weta")],
            target_language="cs",
            known_language="pl",
            baseline=plain,
            normalise=lambda word: word.replace("ó", "o").replace("í", "i").replace("é", "e"),
            seed_threshold=0.6,
            minimum_count=3,
            rounds=1,
        )
        self.assertIn(("v", "w"), learned.costs)


class SimilarityTests(unittest.TestCase):
    def table(self) -> Correspondences:
        return Correspondences("cs", "pl", {("v", "w"): 0.15, ("h", "g"): 0.3})

    def test_an_identical_word_scores_one(self):
        self.assertEqual(self.table().similarity("kot", "kot"), 1.0)

    def test_an_empty_side_scores_zero_rather_than_matching(self):
        self.assertEqual(self.table().similarity("", "kot"), 0.0)
        self.assertEqual(self.table().similarity("kot", ""), 0.0)

    def test_a_score_stays_inside_the_unit_interval(self):
        score = self.table().similarity("abcdef", "zzzzzz")
        self.assertGreaterEqual(score, 0.0)
        self.assertLessEqual(score, 1.0)

    def test_a_cheap_correspondence_beats_an_unknown_one(self):
        table = self.table()
        self.assertGreater(table.similarity("voda", "woda"), table.similarity("voda", "koda"))

    def test_an_unlearned_pair_scores_as_a_plain_substitution(self):
        self.assertAlmostEqual(self.table().similarity("voda", "koda"), 0.75)


class RoundTripTests(unittest.TestCase):
    def test_a_table_survives_being_written_and_read(self):
        original = Correspondences("cs", "pl", {("v", "w"): 0.15}, seed_count=7, rounds=2)
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "cs-pl.json"
            original.write(path)
            restored = Correspondences.read(path)
        self.assertEqual(restored.costs, original.costs)
        self.assertEqual(restored.seed_count, 7)
        self.assertEqual(restored.rounds, 2)
        self.assertEqual(restored.target_language, "cs")

    def test_a_tab_in_the_key_separates_the_two_symbols(self):
        payload = Correspondences("cs", "pl", {("v", "w"): 0.15}).to_dict()
        self.assertIn("v\tw", payload["costs"])

    def test_an_absent_table_is_none_not_an_empty_one(self):
        """Never derived and derived-but-empty are different claims."""

        with tempfile.TemporaryDirectory() as directory:
            self.assertIsNone(load_correspondences(Path(directory), "cs", "pl"))

    def test_a_present_table_is_loaded_from_beside_the_policy(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            table = Correspondences("cs", "pl", {("v", "w"): 0.15})
            (root / "cognates" / "correspondences").mkdir(parents=True)
            (root / "cognates" / "correspondences" / "cs-pl.json").write_text(
                json.dumps(table.to_dict()), encoding="utf-8"
            )
            loaded = load_correspondences(root, "cs", "pl")
        assert loaded is not None
        self.assertEqual(loaded.cost("v", "w"), 0.15)


if __name__ == "__main__":
    unittest.main()
