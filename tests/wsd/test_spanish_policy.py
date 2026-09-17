import unittest
from dataclasses import replace

from fluency.core.identity import create_card_record
from fluency.features import SpecialistFeature
from fluency.wsd.gloss_scoring import LeafScore
from fluency.wsd.languages.spanish import (
    SpanishV5CandidatePolicy,
    se_reflexive_evidence,
    sense_compatible_bridged,
)
from fluency.wsd.menus import MenuAnalysis, SenseLeaf, build_analysis_id


def analysis(card_id, key, headword, pos, senses):
    adapter = "spanishdict-sense-menu/v1"
    return MenuAnalysis(
        menu_analysis_id=build_analysis_id(
            card_id=card_id, source_adapter=adapter, source_analysis_key=key
        ),
        card_id=card_id,
        surface_form="casa",
        headword=headword,
        part_of_speech=pos,
        source_adapter=adapter,
        source_analysis_key=key,
        senses=tuple(
            SenseLeaf(sense_id, translation, context, f"sd:{sense_id}", {"context": context})
            for sense_id, translation, context in senses
        ),
        provider_metadata={},
    )


class SpanishV5CandidatePolicyTests(unittest.TestCase):
    def setUp(self):
        card = create_card_record("es", "casa")
        self.noun = analysis(
            card.card_id, "casa:noun", "casa", "NOUN",
            (("home", "house", "building"),),
        )
        self.verb = analysis(
            card.card_id, "casar:verb", "casar", "VERB",
            (("marry", "to marry", ""), ("empty", "", "used with de")),
        )
        self.reflexive = analysis(
            card.card_id, "casarse:verb", "casarse", "VERB",
            (("get-married", "to get married", ""),),
        )
        self.phrase = analysis(
            card.card_id, "casa:phrase", "casa", "PHRASE",
            (("phrase", "at home", "provider phrase rendering"),),
        )
        self.policy = SpanishV5CandidatePolicy(constraint_mode="evidence_only")

    def test_tagset_bridge_preserves_spanishdict_determiner_categories(self):
        self.assertTrue(sense_compatible_bridged("ADJ", "DET"))
        self.assertFalse(sense_compatible_bridged("VERB", "DET"))

    def test_tagset_bridge_preserves_spanishdict_contractions_for_adpositions(self):
        self.assertTrue(sense_compatible_bridged("CONTRACTION", "ADP"))
        self.assertTrue(sense_compatible_bridged("ADP", "ADP"))

    def test_interrogative_adverbs_survive_a_pronoun_tag(self) -> None:
        """spaCy tags ¿cómo / dónde / cuándo as PRON; the menu is ADV."""

        self.assertTrue(sense_compatible_bridged("ADV", "PRON"))
        self.assertFalse(sense_compatible_bridged("INTJ", "PRON"))

    def test_spanishdict_verb_subtypes_are_verbs(self) -> None:
        self.assertTrue(sense_compatible_bridged("transitive verb", "VERB"))
        self.assertTrue(sense_compatible_bridged("pronominal verb", "AUX"))
        self.assertTrue(sense_compatible_bridged("intransitive verb", "VERB"))
        self.assertFalse(sense_compatible_bridged("transitive verb", "DET"))

    def test_se_only_gate_is_conservative(self):
        self.assertTrue(se_reflexive_evidence("casa", "Se casa hoy"))
        self.assertFalse(se_reflexive_evidence("casa", "Casa a la pareja"))
        self.assertIsNone(se_reflexive_evidence("casa", "Me casa hoy"))
        self.assertTrue(se_reflexive_evidence("diviértanse", "Diviértanse mucho"))
        self.assertFalse(se_reflexive_evidence("pensé", "Nunca pensé sobre ella"))
        self.assertFalse(
            se_reflexive_evidence(
                "quise", "No quise decir eso", {"mood": "indicative"}
            )
        )
        self.assertFalse(se_reflexive_evidence("diga", "Que se lo diga"))
        self.assertFalse(se_reflexive_evidence("tuvo", "Se tuvo que ir"))

    def test_pos_and_clitic_constraints_are_evidence_not_destructive_filters(self):
        prepared = self.policy.prepare(
            sentence="Se casa hoy", surface_form="casa", observed_pos="VERB",
            analyses=(self.noun, self.verb, self.reflexive),
        )
        self.assertEqual(prepared.analyses, (self.noun, self.verb, self.reflexive))
        self.assertEqual(prepared.evidence["policy"], "evidence_only")
        self.assertEqual(
            prepared.evidence["pos_removed_analysis_ids"],
            [self.noun.menu_analysis_id],
        )
        self.assertEqual(
            prepared.evidence["clitic_removed_analysis_ids"],
            [self.verb.menu_analysis_id],
        )
        self.assertEqual(
            prepared.evidence["constraint_supported_analysis_ids"],
            [self.reflexive.menu_analysis_id],
        )
        self.assertEqual(
            prepared.evidence["constraint_rejected_analysis_ids"],
            sorted((self.noun.menu_analysis_id, self.verb.menu_analysis_id)),
        )

    def test_filter_mode_restores_the_v6_active_candidate_set(self):
        prepared = SpanishV5CandidatePolicy(constraint_mode="filter").prepare(
            sentence="Se casa hoy", surface_form="casa", observed_pos="VERB",
            analyses=(self.noun, self.verb, self.reflexive, self.phrase),
        )
        self.assertEqual(prepared.analyses, (self.reflexive,))
        self.assertEqual(prepared.evidence["policy"], "filter")
        self.assertEqual(
            prepared.evidence["constraint_rejected_analysis_ids"],
            sorted((
                self.noun.menu_analysis_id,
                self.verb.menu_analysis_id,
                self.phrase.menu_analysis_id,
            )),
        )

    def test_constraint_mode_must_be_explicitly_supported(self):
        with self.assertRaisesRegex(ValueError, "constraint mode"):
            SpanishV5CandidatePolicy(constraint_mode="guess")

    def test_auxiliary_se_does_not_select_a_lexical_reflexive_headword(self):
        card = create_card_record("es", "ha")
        haber = analysis(
            card.card_id, "haber:verb", "haber", "VERB",
            (("aux", "to have", "auxiliary"),),
        )
        haberse = analysis(
            card.card_id, "haberse:verb", "haberse", "VERB",
            (("confront", "to have it out", "to confront"),),
        )

        prepared = SpanishV5CandidatePolicy(constraint_mode="filter").prepare(
            sentence="Se ha ido", surface_form="ha", observed_pos="AUX",
            analyses=(haber, haberse),
        )

        self.assertEqual(prepared.analyses, (haber,))
        self.assertFalse(prepared.evidence["se_reflexive_evidence"])

    def test_non_spanish_profile_can_disable_the_legacy_se_gate(self):
        prepared = SpanishV5CandidatePolicy(
            constraint_mode="filter", clitic_gate=False
        ).prepare(
            sentence="Se casa hoje", surface_form="casa", observed_pos="VERB",
            analyses=(self.verb, self.reflexive),
        )
        self.assertEqual(prepared.analyses, (self.verb, self.reflexive))
        self.assertIsNone(prepared.evidence["se_reflexive_evidence"])

    def test_menu_prior_and_leaf_repair_match_v5_order(self):
        scores = (
            LeafScore(self.verb.menu_analysis_id, "marry", 0.50),
            LeafScore(self.verb.menu_analysis_id, "empty", 0.509),
        )
        adjusted = self.policy.adjust_scores(scores, (self.verb,))
        self.assertEqual(adjusted[0].sense_id, "marry")
        repaired = self.policy.repair_leaf(
            sentence="Casa a la pareja", analyses=(self.verb,),
            selected=next(score for score in adjusted if score.sense_id == "empty"),
            ranked_scores=adjusted,
        )
        self.assertEqual(repaired.sense_id, "marry")

    def test_normalized_grammar_and_companion_features_filter_leaves(self):
        plain, needs_de = self.verb.senses
        marked = replace(
            self.verb,
            senses=(
                replace(
                    plain,
                    specialist_features=(
                        SpecialistFeature(
                            "grammar", "sense_mark", "mood=indicative", "indicative"
                        ),
                    ),
                ),
                replace(
                    needs_de,
                    translation="to marry off",
                    specialist_features=(
                        SpecialistFeature("companion", "required_word", "de", "de"),
                    ),
                ),
            ),
        )
        prepared = SpanishV5CandidatePolicy(
            constraint_mode="filter", normalized_leaf_gates=True
        ).prepare(
            sentence="Casa a la pareja",
            surface_form="casa",
            observed_pos="VERB",
            observed_grammar={"mood": "subjunctive"},
            analyses=(marked,),
        )

        self.assertEqual(len(prepared.analyses[0].senses), 1)
        # The companion leaf is rejected first; rejecting the remaining grammar
        # leaf would empty the set, so the conservative grammar gate declines.
        self.assertEqual(prepared.analyses[0].senses[0].sense_id, "marry")
        self.assertEqual(
            prepared.evidence["companion_rejected_leaf_refs"][0]["sense_id"],
            "empty",
        )

    def test_normalized_grammar_filters_when_a_compatible_sibling_survives(self):
        first, second = self.verb.senses
        marked = replace(
            self.verb,
            senses=(
                replace(
                    first,
                    specialist_features=(
                        SpecialistFeature(
                            "grammar", "sense_mark", "mood=indicative", "indicative"
                        ),
                    ),
                ),
                replace(
                    second,
                    translation="to wed",
                    specialist_features=(
                        SpecialistFeature(
                            "grammar", "sense_mark", "mood=subjunctive", "subjunctive"
                        ),
                    ),
                ),
            ),
        )
        prepared = SpanishV5CandidatePolicy(
            constraint_mode="filter", normalized_leaf_gates=True
        ).prepare(
            sentence="Quizá se case",
            surface_form="case",
            observed_pos="VERB",
            observed_grammar={"mood": "subjunctive"},
            analyses=(marked,),
        )

        self.assertEqual(
            [sense.sense_id for sense in prepared.analyses[0].senses],
            ["empty"],
        )
        self.assertEqual(
            prepared.evidence["grammar_rejected_leaf_refs"][0]["sense_id"],
            "marry",
        )

    def test_unvalidated_normalized_leaf_gates_are_evidence_only_by_default(self):
        plain, needs_de = self.verb.senses
        marked = replace(
            self.verb,
            senses=(
                plain,
                replace(
                    needs_de,
                    specialist_features=(
                        SpecialistFeature("companion", "required_word", "de", "de"),
                    ),
                ),
            ),
        )
        prepared = SpanishV5CandidatePolicy(constraint_mode="filter").prepare(
            sentence="Casa a la pareja",
            surface_form="casa",
            observed_pos="VERB",
            analyses=(marked,),
        )

        self.assertEqual(prepared.analyses, (marked,))
        self.assertEqual(
            prepared.evidence["normalized_leaf_gate_policy"], "evidence_only"
        )
        self.assertEqual(
            prepared.evidence["companion_rejected_leaf_refs"][0]["sense_id"],
            "empty",
        )

    def test_pronominal_gate_prunes_when_no_clitic(self):
        plain = self.verb.senses[0]
        pronominal = SenseLeaf(
            "die", "to pass away", "pronominal", "ref:die", {},
            specialist_features=(
                SpecialistFeature("construction", "grammar_tag", "pronominal", "pronominal"),
            ),
        )
        verb_with_pronominal = replace(self.verb, senses=(plain, pronominal))
        policy = SpanishV5CandidatePolicy(language="pt", constraint_mode="filter", pronominal_gate=True)
        prepared = policy.prepare(
            sentence="Nós vamos agora",
            surface_form="vamos",
            observed_pos="VERB",
            analyses=(verb_with_pronominal,),
        )
        self.assertEqual(len(prepared.analyses[0].senses), 1)
        self.assertEqual(prepared.analyses[0].senses[0].sense_id, plain.sense_id)
        self.assertEqual(
            prepared.evidence["pronominal_rejected_leaf_refs"][0]["sense_id"],
            "die",
        )

    def test_pronominal_gate_preserves_when_clitic_present(self):
        plain = self.verb.senses[0]
        pronominal = SenseLeaf(
            "die", "to pass away", "pronominal", "ref:die", {},
            specialist_features=(
                SpecialistFeature("construction", "grammar_tag", "pronominal", "pronominal"),
            ),
        )
        verb_with_pronominal = replace(self.verb, senses=(plain, pronominal))
        policy = SpanishV5CandidatePolicy(language="pt", constraint_mode="filter", pronominal_gate=True)
        prepared = policy.prepare(
            sentence="Ele foi-se embora",
            surface_form="foi",
            observed_pos="VERB",
            analyses=(verb_with_pronominal,),
        )
        self.assertEqual(len(prepared.analyses[0].senses), 2)
        self.assertEqual(len(prepared.evidence["pronominal_rejected_leaf_refs"]), 0)

    def test_domain_and_register_penalty(self):
        standard = SenseLeaf("standard", "service", "work", "ref:std", {})
        sports = SenseLeaf(
            "sports", "serve", "tennis serve", "ref:spt", {},
            specialist_features=(
                SpecialistFeature("domain", "topic", "sports", "sports"),
            ),
        )
        analysis_item = replace(self.noun, senses=(standard, sports))
        policy = SpanishV5CandidatePolicy(domain_penalty=0.04)
        scores = (
            LeafScore(analysis_item.menu_analysis_id, "standard", 0.50),
            LeafScore(analysis_item.menu_analysis_id, "sports", 0.51),
        )
        adjusted = policy.adjust_scores(scores, (analysis_item,))
        # sports had 0.51, but gets -0.04 penalty (effective 0.47) plus menu prior
        # standard had 0.50 + 0.02 menu prior = 0.52
        self.assertEqual(adjusted[0].sense_id, "standard")


if __name__ == "__main__":
    unittest.main()
