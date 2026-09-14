"""Sound as a third reading of the form question."""

from __future__ import annotations

import unittest

from fluency.features.phonetics import (
    best_pronunciation_similarity,
    normalise_ipa,
    phone_distance,
    phonetic_similarity,
    segments,
)


class NormalisationTests(unittest.TestCase):
    def test_citation_wrappers_and_stress_are_notation_not_sound(self):
        self.assertEqual(normalise_ipa("/ˈɡra.tis/"), "ɡratis")
        self.assertEqual(normalise_ipa("[ˈabort]"), "abort")

    def test_length_marks_do_not_become_a_phone(self):
        self.assertEqual(normalise_ipa("/ˈmlɛːko/"), "mlɛko")

    def test_combining_diacritics_are_dropped_rather_than_read_as_segments(self):
        # A syllabic mark under the r must not become a phone of its own.
        self.assertEqual(normalise_ipa("/ˈbratr̩/"), "bratr")

    def test_an_empty_transcription_normalises_to_nothing(self):
        self.assertEqual(normalise_ipa(""), "")
        self.assertEqual(normalise_ipa("//"), "")


class SegmentationTests(unittest.TestCase):
    def test_a_tie_barred_affricate_is_one_sound(self):
        self.assertEqual(segments("/ˈt͡ʃas/"), ("tʃ", "a", "s"))

    def test_an_untied_affricate_reads_the_same_way(self):
        self.assertEqual(segments("[ˈtʃas]"), ("tʃ", "a", "s"))

    def test_an_ordinary_word_is_one_phone_per_letter(self):
        self.assertEqual(segments("/sklɛp/"), ("s", "k", "l", "ɛ", "p"))


class PhoneDistanceTests(unittest.TestCase):
    def test_a_phone_is_identical_to_itself(self):
        self.assertEqual(phone_distance("p", "p"), 0.0)

    def test_voicing_alone_is_the_cheapest_difference(self):
        voicing = phone_distance("p", "b")
        place = phone_distance("p", "t")
        self.assertLess(voicing, place)

    def test_place_cost_grows_with_distance_along_the_mouth(self):
        self.assertLess(phone_distance("p", "t"), phone_distance("p", "k"))

    def test_a_consonant_against_a_vowel_is_maximal(self):
        self.assertEqual(phone_distance("p", "a"), 1.0)

    def test_neighbouring_vowels_are_closer_than_opposite_ones(self):
        self.assertLess(phone_distance("i", "ɪ"), phone_distance("i", "ɑ"))

    def test_an_unknown_symbol_never_manufactures_similarity(self):
        self.assertEqual(phone_distance("p", "ʔʔ"), 1.0)
        self.assertEqual(phone_distance("§", "p"), 1.0)

    def test_distance_is_symmetric(self):
        for left, right in (("p", "k"), ("i", "u"), ("s", "ʃ"), ("m", "n")):
            self.assertAlmostEqual(
                phone_distance(left, right), phone_distance(right, left)
            )


class SimilarityTests(unittest.TestCase):
    def test_the_same_pronunciation_scores_one(self):
        self.assertEqual(phonetic_similarity("/sklɛp/", "/ˈsklɛp/"), 1.0)

    def test_an_orthographic_difference_that_is_not_a_sound_difference(self):
        """Czech ``čas`` and Polish ``czas``: two letters apart, one sound."""

        self.assertGreater(phonetic_similarity("/ˈt͡ʃas/", "/ˈt͡ʂas/"), 0.9)

    def test_a_correspondence_no_rewrite_rule_captures(self):
        """Czech ``hlava`` against Polish ``głowa`` — 0.20 on letters."""

        self.assertGreater(phonetic_similarity("/ˈɦlava/", "/ˈɡwova/"), 0.6)

    def test_unrelated_words_sit_far_below_any_cutoff(self):
        """Feature weighting gives partial credit, so the floor is not zero.

        It only has to stay well clear of the loosest cutoff a pair ships
        (0.75), which it does by a wide margin.
        """

        self.assertLess(phonetic_similarity("/ˈsklɛp/", "/ˈkɲiʐka/"), 0.5)

    def test_an_absent_transcription_scores_zero_rather_than_matching(self):
        self.assertEqual(phonetic_similarity("", "/ˈsklɛp/"), 0.0)
        self.assertEqual(phonetic_similarity("/ˈsklɛp/", ""), 0.0)

    def test_similarity_is_symmetric(self):
        self.assertAlmostEqual(
            phonetic_similarity("/ˈɦlava/", "/ˈɡwova/"),
            phonetic_similarity("/ˈɡwova/", "/ˈɦlava/"),
        )

    def test_a_score_is_never_negative(self):
        self.assertGreaterEqual(phonetic_similarity("/a/", "/ˈkɲiʐka/"), 0.0)


class BestPronunciationTests(unittest.TestCase):
    def test_the_closest_recorded_variant_wins(self):
        score = best_pronunciation_similarity(
            ["/ˈbɹit.ɪʃ/", "/ˈsklɛp/"],
            ["/ˈsklɛp/"],
        )
        self.assertEqual(score, 1.0)

    def test_no_transcription_on_either_side_is_zero(self):
        self.assertEqual(best_pronunciation_similarity([], ["/ˈsklɛp/"]), 0.0)
        self.assertEqual(best_pronunciation_similarity(["/ˈsklɛp/"], []), 0.0)

    def test_empty_strings_are_skipped_not_scored(self):
        self.assertEqual(best_pronunciation_similarity(["", None or ""], ["/a/"]), 0.0)


if __name__ == "__main__":
    unittest.main()
