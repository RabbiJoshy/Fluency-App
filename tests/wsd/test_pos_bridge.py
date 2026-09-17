"""A POS filter without a bridge deletes correct senses on the commonest words.

Measured on the real Portuguese menu: comparing a tagger's UD tag directly
against Wiktionary's categories loses every sense on 12 of the 13 most frequent
surfaces -- a, o, do, da, no, na, ao, um, uma, e, esta, que. The bridge exists
to absorb that, and the same failure is recorded for Spanish in
docs/reference/wsd_dead_ends.md.
"""

import unittest

from fluency.wsd.pos_bridge import (
    PosBridgeError,
    acceptable_categories,
    compatible,
    dictionary_pos_family,
    is_orthogonal,
    tagger_pos_is_noise_against_single_family,
)


class WiktionaryBridgeTests(unittest.TestCase):
    def test_contraction_is_reachable_from_adp_and_det(self) -> None:
        """do, ao, da, na are filed only as `contraction`; UD has no such tag."""

        for tag in ("ADP", "DET"):
            with self.subTest(tag=tag):
                self.assertTrue(compatible("wiktionary", tag, "contraction"))

    def test_auxiliaries_reach_verb(self) -> None:
        """Wiktionary has no `aux`; e and esta are plain verbs."""

        self.assertTrue(compatible("wiktionary", "AUX", "verb"))

    def test_determiners_do_not_keep_object_pronouns(self) -> None:
        """as pessoas is DET "the"; vi-as is PRON "them"."""

        self.assertFalse(compatible("wiktionary", "DET", "pron"))
        self.assertTrue(compatible("wiktionary", "PRON", "pron"))
        self.assertTrue(compatible("wiktionary", "DET", "article"))

    def test_fused_prepositional_pronouns_filed_as_adv_survive_a_pron_tag(self) -> None:
        self.assertTrue(
            tagger_pos_is_noise_against_single_family(
                dictionary_parts_of_speech=("adv",),
                observed_pos="PRON",
            )
        )

    def test_genuine_mismatches_are_still_rejected(self) -> None:
        """The bridge must widen the filter, not disable it."""

        self.assertFalse(compatible("wiktionary", "NOUN", "verb"))
        self.assertFalse(compatible("wiktionary", "ADP", "noun"))
        self.assertFalse(compatible("wiktionary", "INTJ", "noun"))

    def test_absent_tag_is_no_evidence(self) -> None:
        self.assertTrue(compatible("wiktionary", None, "noun"))

    def test_unmapped_tag_keeps_every_sense(self) -> None:
        """Refusing to guess is cheaper than deleting a correct sense."""

        self.assertEqual(acceptable_categories("wiktionary", "X"), frozenset())
        self.assertTrue(compatible("wiktionary", "X", "noun"))

    def test_orthogonal_categories_make_no_claim(self) -> None:
        for category in ("phrase", "proverb", "character", "suffix"):
            with self.subTest(category=category):
                self.assertTrue(is_orthogonal("wiktionary", category))
                self.assertTrue(compatible("wiktionary", "NOUN", category))

    def test_unknown_provider_is_refused(self) -> None:
        with self.assertRaises(PosBridgeError):
            acceptable_categories("spanishdict-unbridged", "NOUN")

    def test_verb_subtypes_share_a_family_on_both_providers(self) -> None:
        self.assertEqual(dictionary_pos_family("transitive verb"), "verb")
        self.assertEqual(dictionary_pos_family("verb"), "verb")
        self.assertEqual(dictionary_pos_family("PHRASE"), "phrase")

    def test_a_one_category_verb_menu_survives_a_subordinator_tag(self) -> None:
        self.assertTrue(
            tagger_pos_is_noise_against_single_family(
                dictionary_parts_of_speech=("verb",),
                observed_pos="NOUN",
            )
        )
        self.assertTrue(
            tagger_pos_is_noise_against_single_family(
                dictionary_parts_of_speech=("verb",),
                observed_pos="SCONJ",
            )
        )
        self.assertTrue(
            tagger_pos_is_noise_against_single_family(
                dictionary_parts_of_speech=("PHRASE",),
                observed_pos="VERB",
            )
        )

    def test_a_two_category_menu_is_a_real_fight(self) -> None:
        self.assertFalse(
            tagger_pos_is_noise_against_single_family(
                dictionary_parts_of_speech=("prep", "verb"),
                observed_pos="PRON",
            )
        )

    def test_noun_menu_does_not_absorb_a_verb_tag(self) -> None:
        self.assertFalse(
            tagger_pos_is_noise_against_single_family(
                dictionary_parts_of_speech=("NOUN",),
                observed_pos="VERB",
            )
        )


class RegressionTests(unittest.TestCase):
    COMMON = {
        "do": "ADP", "ao": "ADP", "na": "ADP", "no": "ADP", "da": "ADP",
        "a": "DET", "o": "DET", "um": "DET", "uma": "DET",
        "é": "AUX", "está": "AUX", "se": "PRON", "que": "SCONJ",
    }
    # As published by Wiktionary for those surfaces.
    CATEGORIES = {
        "do": ["contraction"], "ao": ["contraction"], "na": ["contraction", "pron"],
        "no": ["contraction", "pron"], "da": ["contraction", "verb"],
        "a": ["article", "pron", "prep"], "o": ["article", "pron"],
        "um": ["article", "num"], "uma": ["article", "num"],
        "é": ["verb", "intj", "noun"], "está": ["verb"],
        "se": ["pron", "conj"], "que": ["conj", "pron", "adv"],
    }

    def test_no_common_surface_loses_every_sense(self) -> None:
        for surface, tag in self.COMMON.items():
            categories = self.CATEGORIES[surface]
            kept = [c for c in categories if compatible("wiktionary", tag, c)]
            with self.subTest(surface=surface):
                self.assertTrue(kept, f"{surface} ({tag}) lost every sense")

    def test_the_unbridged_comparison_would_have_failed(self) -> None:
        """Guards the bridge's reason for existing, not just its behaviour."""

        casualties = [
            surface for surface, tag in self.COMMON.items()
            if not [c for c in self.CATEGORIES[surface] if c.upper() == tag]
        ]
        self.assertGreaterEqual(len(casualties), 10)


if __name__ == "__main__":
    unittest.main()
