"""A misaligned pair must not consume a model call.

The harvest judges each side of a pair on its own form; nothing judged whether
the two are the same sentence. A pair below the alignment floor cannot be
displayed whatever WSD decides about it, so it is dropped before the execution
cap rather than ranked below it -- otherwise the cap spends embeddings on
sentences that are already disqualified.
"""

import unittest

from fluency.harvest.alignment import DEFAULT_ALIGNMENT_FLOOR, below_floor
from fluency.wsd.sampling import OccurrenceSamplingPolicy, select_occurrences


def candidate(sentence_id: str, score: float) -> dict:
    return {"sentence_id": sentence_id, "metrics": {"score": score}}


class AlignmentFloorTests(unittest.TestCase):
    def setUp(self) -> None:
        self.policy = OccurrenceSamplingPolicy(cap_per_surface=2)
        self.candidates = [candidate("a", 1.0), candidate("b", 2.0), candidate("c", 3.0)]

    def test_a_misaligned_pair_yields_its_slot_to_the_next_candidate(self) -> None:
        selection = select_occurrences(
            self.candidates, self.policy, card_id="card", misaligned={"b"}
        )
        self.assertEqual(selection.selected, ("a", "c"))
        self.assertIn("b", selection.overflow)

    def test_without_scores_nothing_changes(self) -> None:
        selection = select_occurrences(self.candidates, self.policy, card_id="card")
        self.assertEqual(selection.selected, ("a", "b"))

    def test_every_candidate_is_still_accounted_for(self) -> None:
        selection = select_occurrences(
            self.candidates, self.policy, card_id="card", misaligned={"a"}
        )
        self.assertEqual(
            sorted(selection.selected + selection.overflow), ["a", "b", "c"]
        )

    def test_an_unscored_sentence_keeps_its_place(self) -> None:
        """Silence is not evidence of misalignment."""
        rejected = below_floor({"a": 0.1}, ["a", "b"], DEFAULT_ALIGNMENT_FLOOR)
        self.assertEqual(rejected, {"a"})

    def test_the_floor_admits_idiomatic_translation(self) -> None:
        """0.58 is "Afastem-se, deixem os medicos passarem." rendered as
        "Just stick against the wall and let the doctors through." -- loose,
        correct, and exactly the subtitle register the decks are for."""
        self.assertEqual(below_floor({"x": 0.58}, ["x"], DEFAULT_ALIGNMENT_FLOOR), set())


if __name__ == "__main__":
    unittest.main()
