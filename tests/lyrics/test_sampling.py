import unittest

from fluency.lyrics.sampling import (
    calculate_lyrics_wsd_budget,
    score_lyric_line_quality,
    select_best_lyrics_occurrences,
)


class TestLyricsSamplingBudget(unittest.TestCase):
    def test_top_tier_monosemous_gets_floor_of_10(self):
        # Rank 200 (core), 1 sense, 50 lines available -> exactly 10 lines
        budget = calculate_lyrics_wsd_budget(rank=200, sense_count=1, available_lines=50)
        self.assertEqual(budget, 10)

    def test_top_tier_polysemous_scales_with_senses(self):
        # Rank 200 (core), 8 senses, 50 lines available -> 24 lines (3.0 * 8)
        budget = calculate_lyrics_wsd_budget(rank=200, sense_count=8, available_lines=50)
        self.assertEqual(budget, 24)

    def test_top_tier_bounded_by_available_supply(self):
        # Rank 200, wants 10, but only 4 lines exist in the catalog
        budget = calculate_lyrics_wsd_budget(rank=200, sense_count=1, available_lines=4)
        self.assertEqual(budget, 4)

    def test_mid_tier_budget(self):
        # Rank 2,500, 2 senses, 30 lines available -> floor of 8
        budget = calculate_lyrics_wsd_budget(rank=2500, sense_count=2, available_lines=30)
        self.assertEqual(budget, 8)

        # Rank 2,500, 5 senses, 30 lines available -> 13 (2.5 * 5 = 12.5 -> 13)
        budget = calculate_lyrics_wsd_budget(rank=2500, sense_count=5, available_lines=30)
        self.assertEqual(budget, 13)

    def test_rare_tail_accepts_100_percent_of_supply(self):
        # Rank 8,000 (rare slang), 3 lines available -> accepts all 3
        budget = calculate_lyrics_wsd_budget(rank=8000, sense_count=1, available_lines=3)
        self.assertEqual(budget, 3)


class TestLyricsQualitySieve(unittest.TestCase):
    def test_deduplication_collapses_chorus_repeats(self):
        lines = {
            "l1": {"line_id": "l1", "text": "Tú no eres bebecita, tú eres bebesota."},
            "l2": {"line_id": "l2", "text": "— Tú no eres bebecita, tú eres bebesota..."},
            "l3": {"line_id": "l3", "text": "Yo quiero bailar contigo esta noche."},
        }
        alignments = {}
        occurrences = [
            {"occurrence_id": "occ_1", "line_id": "l1"},
            {"occurrence_id": "occ_2", "line_id": "l2"},
            {"occurrence_id": "occ_3", "line_id": "l3"},
        ]

        selected, overflow = select_best_lyrics_occurrences(
            occurrences=occurrences,
            lines_by_id=lines,
            alignments_by_line=alignments,
            budget=2,
        )

        selected_occ_ids = {item["occurrence_id"] for item in selected}
        # l1 and l2 are duplicate variants; only one should be selected
        self.assertIn("occ_3", selected_occ_ids)
        self.assertTrue("occ_1" in selected_occ_ids or "occ_2" in selected_occ_ids)
        self.assertFalse("occ_1" in selected_occ_ids and "occ_2" in selected_occ_ids)
        self.assertEqual(len(selected), 2)
        self.assertEqual(len(overflow), 1)

    def test_line_length_scoring_prefers_complete_sentences_over_fragments(self):
        fragment_score = score_lyric_line_quality("Yeh.")
        good_line_score = score_lyric_line_quality("Ella se prepara para salir a la pista de baile.")
        self.assertGreater(good_line_score, fragment_score)


if __name__ == "__main__":
    unittest.main()
