"""Czech runs with no POS model, and says so.

spaCy publishes no Czech pipeline. A POS gate is only ever subtractive -- it
removes senses the observed tag rules out, while the embedding chooses among
what is left -- so an uncalibrated gate is not neutral but destructive:
unbridged filtering deleted every sense on 34% of real Portuguese occurrences.
Declaring the absence is therefore safer than approximating a tagger.
"""

import unittest

from fluency.wsd.bindings import binding_for, pos_gate_for


class CzechBindingTests(unittest.TestCase):
    def test_czech_declares_that_it_has_no_pos_model(self) -> None:
        self.assertIsNone(binding_for("cs").pos_model_role)

    def test_czech_reads_wiktionary_like_every_language_after_spanish(self) -> None:
        self.assertEqual(binding_for("cs").menu_provider, "wiktionary")

    def test_a_language_without_a_tagger_keeps_every_sense_eligible(self) -> None:
        compatible, orthogonal = pos_gate_for("cs")
        self.assertTrue(compatible("noun", "VERB"))
        self.assertTrue(compatible("verb", "NOUN"))
        self.assertFalse(orthogonal("noun"))

    def test_a_language_with_a_tagger_still_discriminates(self) -> None:
        """The absence must be scoped to Czech and not weaken anyone else."""

        compatible, _ = pos_gate_for("pt")
        self.assertFalse(compatible("noun", "VERB"))


class CzechAdapterTests(unittest.TestCase):
    def test_diacritics_are_matched_never_folded(self) -> None:
        from fluency.wsd.languages.czech import CzechWSDAdapter

        adapter = CzechWSDAdapter()
        self.assertEqual(len(adapter.locate("Musí to být pravda.", "být")), 1)
        # byt (flat) and byt (to be) are different Czech words.
        self.assertEqual(adapter.locate("Mám malý byt.", "být"), ())


class CzechHomographTests(unittest.TestCase):
    def setUp(self):
        from fluency.wsd.menus import MenuAnalysis, SenseLeaf, build_analysis_id

        self.conj_ze = MenuAnalysis(
            menu_analysis_id=build_analysis_id(card_id="c1", source_adapter="wik", source_analysis_key="ze:conj"),
            card_id="c1", surface_form="že", headword="že", part_of_speech="CONJ",
            source_adapter="wik", source_analysis_key="ze:conj",
            senses=(SenseLeaf("s_conj", "that", "", "ref", {}),),
            provider_metadata={},
        )
        self.intj_ze = MenuAnalysis(
            menu_analysis_id=build_analysis_id(card_id="c1", source_adapter="wik", source_analysis_key="ze:intj"),
            card_id="c1", surface_form="že", headword="že", part_of_speech="INTJ",
            source_adapter="wik", source_analysis_key="ze:intj",
            senses=(SenseLeaf("s_intj", "right?", "", "ref", {}),),
            provider_metadata={},
        )
        self.prep_se = MenuAnalysis(
            menu_analysis_id=build_analysis_id(card_id="c2", source_adapter="wik", source_analysis_key="se:prep"),
            card_id="c2", surface_form="se", headword="s", part_of_speech="ADP",
            source_adapter="wik", source_analysis_key="se:prep",
            senses=(SenseLeaf("s_prep", "with", "", "ref", {}),),
            provider_metadata={},
        )
        self.pron_se = MenuAnalysis(
            menu_analysis_id=build_analysis_id(card_id="c2", source_adapter="wik", source_analysis_key="se:pron"),
            card_id="c2", surface_form="se", headword="se", part_of_speech="PRON",
            source_adapter="wik", source_analysis_key="se:pron",
            senses=(SenseLeaf("s_pron", "oneself", "", "ref", {}),),
            provider_metadata={},
        )

    def test_ze_subordinating_clause_prunes_interjection(self):
        from fluency.wsd.languages.spanish import SpanishV5CandidatePolicy

        policy = SpanishV5CandidatePolicy(language="cs", constraint_mode="filter")
        prepared = policy.prepare(
            sentence="Jak to, že tohle je v pořádku?",
            surface_form="že",
            observed_pos=None,
            analyses=(self.conj_ze, self.intj_ze),
        )
        self.assertEqual(len(prepared.analyses), 1)
        self.assertEqual(prepared.analyses[0].part_of_speech, "CONJ")

    def test_ze_tag_question_keeps_interjection(self):
        from fluency.wsd.languages.spanish import SpanishV5CandidatePolicy

        policy = SpanishV5CandidatePolicy(language="cs", constraint_mode="filter")
        prepared = policy.prepare(
            sentence="Byl tam taky, že?",
            surface_form="že",
            observed_pos=None,
            analyses=(self.conj_ze, self.intj_ze),
        )
        self.assertEqual(len(prepared.analyses), 2)

    def test_se_instrumental_prunes_pronoun(self):
        from fluency.wsd.languages.spanish import SpanishV5CandidatePolicy

        policy = SpanishV5CandidatePolicy(language="cs", constraint_mode="filter")
        prepared = policy.prepare(
            sentence="Pojď se mnou.",
            surface_form="se",
            observed_pos=None,
            analyses=(self.prep_se, self.pron_se),
        )
        self.assertEqual(len(prepared.analyses), 1)
        self.assertEqual(prepared.analyses[0].part_of_speech, "ADP")

    def test_se_reflexive_preserves_pronoun(self):
        from fluency.wsd.languages.spanish import SpanishV5CandidatePolicy

        policy = SpanishV5CandidatePolicy(language="cs", constraint_mode="filter")
        prepared = policy.prepare(
            sentence="On se směje.",
            surface_form="se",
            observed_pos=None,
            analyses=(self.prep_se, self.pron_se),
        )
        self.assertEqual(len(prepared.analyses), 2)


if __name__ == "__main__":
    unittest.main()
