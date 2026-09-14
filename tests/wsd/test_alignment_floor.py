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
            self.candidates, self.policy, card_id="card", ineligible={"b"}
        )
        self.assertEqual(selection.selected, ("a", "c"))
        self.assertIn("b", selection.overflow)

    def test_without_scores_nothing_changes(self) -> None:
        selection = select_occurrences(self.candidates, self.policy, card_id="card")
        self.assertEqual(selection.selected, ("a", "b"))

    def test_every_candidate_is_still_accounted_for(self) -> None:
        selection = select_occurrences(
            self.candidates, self.policy, card_id="card", ineligible={"a"}
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


class VarietyTaggingTests(unittest.TestCase):
    """European and Brazilian Portuguese are tagged, not filtered.

    Measured on the 375,598-sentence Portuguese bank: Tatoeba is 17.4%
    Brazilian against 2.6% European, OpenSubtitles 14.8% European against 8.5%
    Brazilian. For a European deck it is Tatoeba, not the subtitles, that pulls
    the wrong way. 76% of sentences signal neither, so a tag is the right
    output and a filter is not.
    """

    def test_the_progressive_separates_the_two(self) -> None:
        from fluency.harvest.conditioning import variety

        self.assertEqual(variety("Estou a fazer o jantar.")[0], "european")
        self.assertEqual(variety("Estou fazendo o jantar.")[0], "brazilian")

    def test_everyday_lexis_separates_them(self) -> None:
        from fluency.harvest.conditioning import variety

        self.assertEqual(variety("Apanhei o autocarro para casa.")[0], "european")
        self.assertEqual(variety("Peguei o ônibus para casa.")[0], "brazilian")

    def test_most_sentences_belong_to_neither(self) -> None:
        from fluency.harvest.conditioning import variety

        self.assertEqual(variety("O livro está na mesa.")[0], "neutral")

    def test_fato_is_claimed_by_neither(self) -> None:
        """A suit in Lisbon and a fact in Sao Paulo: it says nothing alone."""
        from fluency.harvest.conditioning import variety

        self.assertEqual(variety("Ele comprou um fato novo.")[0], "neutral")

    def test_a_rejected_candidate_keeps_its_reason(self) -> None:
        from fluency.harvest.conditioning import condition_candidate

        entry = condition_candidate(
            {"sentence_id": "s", "metrics": {"score": 1.0, "target_tokens": 8}},
            text="Estou a fazer o jantar.",
            source="opensubtitles",
            alignment=0.12,
            alignment_floor=0.70,
        )
        self.assertFalse(entry["eligible"])
        self.assertEqual(entry["rejected_for"], "below_alignment_floor")
        self.assertEqual(entry["tags"]["variety"], "european")

    def test_an_unscored_pair_stays_eligible(self) -> None:
        from fluency.harvest.conditioning import condition_candidate

        entry = condition_candidate(
            {"sentence_id": "s", "metrics": {"score": 1.0, "target_tokens": 8}},
            text="O livro está na mesa.",
            source="tatoeba",
            alignment=None,
            alignment_floor=0.70,
        )
        self.assertTrue(entry["eligible"])
