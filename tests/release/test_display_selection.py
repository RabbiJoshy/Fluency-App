"""Stage 5 may only show sentences WSD actually disambiguated."""

import unittest

from fluency.release.run_candidate import (
    display_pool_for_card,
    without_canonical_example_lists,
)


class DisplayPoolTests(unittest.TestCase):
    def test_when_wsd_ran_only_sensed_sentences_remain(self) -> None:
        pool = [{"sentence_id": "kept"}, {"sentence_id": "unseen"}]
        assignments = {
            ("card_1", "kept"): {"selected_sense_id": "sense_a"},
            ("card_1", "unseen"): {"status": "not_evaluated_example_cap"},
        }
        shown = display_pool_for_card(pool, assignments, "card_1", wsd_ran=True)
        self.assertEqual([item["sentence_id"] for item in shown], ["kept"])

    def test_missing_stage_04_keeps_the_full_pool(self) -> None:
        pool = [{"sentence_id": "a"}, {"sentence_id": "b"}]
        self.assertEqual(
            display_pool_for_card(pool, {}, "card_1", wsd_ran=False),
            pool,
        )


class ProviderExampleStripTests(unittest.TestCase):
    def test_nested_example_lists_are_dropped_and_other_fields_remain(self) -> None:
        payload = {
            "spanishdict": {
                "examples": [{"original": "x", "translated": "y"}],
                "gender": "m",
            },
            "keep": 1,
        }
        self.assertEqual(
            without_canonical_example_lists(payload),
            {"spanishdict": {"gender": "m"}, "keep": 1},
        )
