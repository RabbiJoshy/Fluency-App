"""End-to-end probe tests verifying Portuguese WSD improvements on benchmark target words.

Target words:
- `que`: SCONJ tag disambiguates to conj ("that"), provider_order does not vote "because",
  translation "that" gives overlap bonus.
- `milhões`: NUM tag bridges to Wiktionary noun without no_compatible_analysis abstention.
- `estupendo`: VERB tag bridges to Wiktionary adj without no_compatible_analysis abstention.
"""

import unittest
from fluency.wsd.bindings import pos_gate_for
from fluency.wsd.menus import MenuAnalysis, SenseLeaf, build_analysis_id
from fluency.wsd.commit import CommitPolicy
from fluency.wsd.disposition import DispositionPolicy
from fluency.wsd.gloss_scoring import LeafScore
from fluency.wsd.languages.portuguese import PortugueseWSDAdapter
from fluency.wsd.languages.spanish import SpanishV5CandidatePolicy
from fluency.wsd.pos_bridge import (
    WIKTIONARY_BRIDGE,
    compatible,
    tagger_pos_is_noise_against_single_family,
)
from fluency.wsd.runner import (
    ClosedMenuWSDRunner,
    WSDComponents,
    WSDExecutionProfile,
    WSDRequest,
)
from fluency.speech.wsd_execute import (
    _is_conflicting_regional_leaf,
    _regional_register_penalty,
    _translation_overlap_bonus,
)


def make_leaf(sense_id: str, translation: str, definition: str = "") -> SenseLeaf:
    return SenseLeaf(
        sense_id=sense_id,
        translation=translation,
        definition=definition,
        source_reference=f"wiktionary:{sense_id}",
        provider_metadata={"raw_glosses": [translation]},
    )


def make_analysis(card_id: str, headword: str, pos: str, leaves: list[SenseLeaf]) -> MenuAnalysis:
    return MenuAnalysis(
        menu_analysis_id=build_analysis_id(
            card_id=card_id,
            source_adapter="kaikki/v1",
            source_analysis_key=f"pt:{headword}:{pos}",
        ),
        card_id=card_id,
        surface_form=headword,
        headword=headword,
        part_of_speech=pos,
        source_adapter="kaikki/v1",
        source_analysis_key=f"pt:{headword}:{pos}",
        senses=tuple(leaves),
        provider_metadata={},
    )


class PortugueseWSDProbeTests(unittest.TestCase):
    def test_milhoes_num_matches_wiktionary_noun(self) -> None:
        """milhões tagged NUM by spaCy bridges directly to noun, avoiding no_compatible_analysis."""
        self.assertIn("noun", WIKTIONARY_BRIDGE["NUM"])
        self.assertTrue(compatible("wiktionary", "NUM", "noun"))
        self.assertTrue(
            tagger_pos_is_noise_against_single_family(
                dictionary_parts_of_speech=["noun"],
                observed_pos="NUM",
            )
        )

    def test_estupendo_verb_matches_wiktionary_adj(self) -> None:
        """estupendo tagged VERB by spaCy bridges to adj, avoiding no_compatible_analysis."""
        self.assertIn("adj", WIKTIONARY_BRIDGE["VERB"])
        self.assertTrue(compatible("wiktionary", "VERB", "adj"))
        self.assertTrue(
            tagger_pos_is_noise_against_single_family(
                dictionary_parts_of_speech=["adj"],
                observed_pos="VERB",
            )
        )

    def test_que_sconj_filters_out_pronoun_and_adverb_entries(self) -> None:
        """When que is tagged SCONJ, SpanishV5CandidatePolicy does NOT restore pronoun/determiner/adverb."""
        sense_compatible, pos_is_orthogonal = pos_gate_for("pt")
        policy = SpanishV5CandidatePolicy(
            language="pt",
            menu_prior=0.0,
            sense_compatible=sense_compatible,
            pos_is_orthogonal=pos_is_orthogonal,
            keep_self_reading_pos=frozenset({"adv", "pron", "det"}),
        )
        leaf_sconj = make_leaf("sconj_that", "that")
        leaf_pron = make_leaf("pron_what", "what")
        leaf_adv = make_leaf("adv_how", "how")

        analysis_sconj = make_analysis("card_" + "1" * 32, "que", "conj", [leaf_sconj])
        analysis_pron = make_analysis("card_" + "1" * 32, "que", "pron", [leaf_pron])
        analysis_adv = make_analysis("card_" + "1" * 32, "que", "adv", [leaf_adv])

        prep = policy.prepare(
            sentence="Eu acho que você precisa de ajuda.",
            surface_form="que",
            observed_pos="SCONJ",
            analyses=(analysis_sconj, analysis_pron, analysis_adv),
        )
        surviving_pos = {cand.part_of_speech for cand in prep.analyses}
        self.assertEqual(surviving_pos, {"conj"})
        self.assertNotIn("pron", surviving_pos)
        self.assertNotIn("adv", surviving_pos)

    def test_que_translation_overlap_picks_that_over_because(self) -> None:
        """Translation matching on English sentence 'I think that you need help' boosts 'that'."""
        leaf_because = make_leaf("sense_because", "because")
        leaf_that = make_leaf("sense_that", "that")

        sentence_en = "I think that you need help"
        bonus_because = _translation_overlap_bonus(leaf_because, sentence_en)
        bonus_that = _translation_overlap_bonus(leaf_that, sentence_en)

        self.assertEqual(bonus_because, 0.0)
        self.assertEqual(bonus_that, 0.04)

    def test_provider_order_deactivation_prevents_alphabetical_veto(self) -> None:
        """When provider_order_votes is False, first-listed 'because' cannot veto 'that'."""
        card_id = "card_pt_" + "1" * 32
        leaf_because = make_leaf("sense_because", "because", "cause")  # order 0
        leaf_that = make_leaf("sense_that", "that", "conjunction")       # order 1

        analysis = make_analysis(card_id, "que", "conj", [leaf_because, leaf_that])

        class QueGlossScorer:
            model_revision = "test"
            def score(self, sentence, analyses, translation=""):
                return (
                    LeafScore(analysis.menu_analysis_id, "sense_because", 0.85),
                    LeafScore(analysis.menu_analysis_id, "sense_that", 0.89),
                )

        sense_compatible, pos_is_orthogonal = pos_gate_for("pt")
        candidate_policy = SpanishV5CandidatePolicy(
            language="pt",
            menu_prior=0.0,
            sense_compatible=sense_compatible,
            pos_is_orthogonal=pos_is_orthogonal,
        )

        components = WSDComponents(
            language=PortugueseWSDAdapter(),
            gloss=QueGlossScorer(),
            candidate_policy=candidate_policy,
        )
        profile = WSDExecutionProfile(
            token_tuple_vote=False,
            tuple_vote_minimum_margin=0.0,
            calibration=False,
            alignment=False,
            generative_escalation=False,
            disposition=DispositionPolicy(minimum_confidence=None, weak="retain"),
            candidate_preparation=True,
            commit=CommitPolicy(
                strategy="rank_agreement",
                evidence_guards=True,
                unresolved_outcome="abstain",
                provider_order_votes=False,  # Wiktionary: order does not vote
            ),
        )
        runner = ClosedMenuWSDRunner(profile, components)
        request = WSDRequest(
            card_id=card_id,
            surface_form="que",
            sentence_id="sentence_" + "1" * 32,
            sentence="Eu acho que você precisa de ajuda.",
            translation="I think that you need help.",
            sense_menu_content_id="sha256:" + "0" * 64,
            analyses=(analysis,),
            observed_pos="SCONJ",
        )
        assignment = runner.assign(request)
        self.assertEqual(assignment.status, "assigned")
        self.assertEqual(assignment.selected_sense_id, "sense_that")
        self.assertEqual(assignment.emitted_level, "leaf")

    def test_se_reflexive_vs_brazil_ce_disambiguation(self) -> None:
        card_id = "card_pt_" + "2" * 32
        ce_leaf = SenseLeaf(
            sense_id="sense_ce_you",
            translation="you",
            definition="",
            source_reference="wiktionary:cê",
            provider_metadata={"regions": ["Brazil"], "tags": ["Brazil", "informal"]},
        )
        reflexive_leaf = SenseLeaf(
            sense_id="sense_se_yourself",
            translation="second-person singular and plural reflexive and reciprocal pronoun; yourself; yourselves",
            definition="",
            source_reference="wiktionary:se",
            provider_metadata={"regions": [], "tags": []},
        )
        analysis_ce = make_analysis(card_id, "cê", "pron", [ce_leaf])
        analysis_se = make_analysis(card_id, "se", "pron", [reflexive_leaf])

        class SeGlossScorer:
            model_revision = "gemini-embedding-001"
            def score(self, sentence: str, analyses, translation: str = ""):
                # Raw embedding gives slightly higher score to short "you" (0.80) than long gloss (0.78),
                # plus translation has "you", but regional penalty penalizes Brazil by 0.06 and denies overlap bonus.
                scores = []
                for analysis in analyses:
                    for leaf in analysis.senses:
                        val = 0.80 if leaf.sense_id == "sense_ce_you" else 0.78
                        # Overlap:
                        if translation and not _is_conflicting_regional_leaf(leaf, "pt-PT"):
                            val += _translation_overlap_bonus(leaf, translation)
                        val -= _regional_register_penalty(leaf, "pt-PT")
                        scores.append(LeafScore(analysis.menu_analysis_id, leaf.sense_id, val))
                return scores

        sense_compatible, pos_is_orthogonal = pos_gate_for("pt")
        candidate_policy = SpanishV5CandidatePolicy(
            language="pt",
            menu_prior=0.0,
            sense_compatible=sense_compatible,
            pos_is_orthogonal=pos_is_orthogonal,
        )
        components = WSDComponents(
            language=PortugueseWSDAdapter(),
            gloss=SeGlossScorer(),
            candidate_policy=candidate_policy,
        )
        profile = WSDExecutionProfile(
            token_tuple_vote=False,
            tuple_vote_minimum_margin=0.0,
            calibration=False,
            alignment=False,
            generative_escalation=False,
            disposition=DispositionPolicy(minimum_confidence=None, weak="retain"),
            candidate_preparation=True,
            commit=CommitPolicy(
                strategy="rank_agreement",
                evidence_guards=True,
                unresolved_outcome="abstain",
                provider_order_votes=False,
            ),
        )
        runner = ClosedMenuWSDRunner(profile, components)
        request = WSDRequest(
            card_id=card_id,
            surface_form="se",
            sentence_id="sentence_" + "2" * 32,
            sentence="Está a sentir-se bem?",
            translation="You doing okay?",
            sense_menu_content_id="sha256:" + "0" * 64,
            analyses=(analysis_ce, analysis_se),
            observed_pos="PRON",
        )
        assignment = runner.assign(request)
        self.assertEqual(assignment.status, "assigned")
        self.assertEqual(assignment.selected_sense_id, "sense_se_yourself")
        self.assertEqual(assignment.emitted_level, "leaf")


if __name__ == "__main__":
    unittest.main()
