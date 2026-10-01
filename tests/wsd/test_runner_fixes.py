import unittest

from fluency.wsd.candidate_policy import CandidatePreparation
from fluency.wsd.commit import CommitPolicy
from fluency.wsd.disposition import DispositionPolicy
from fluency.wsd.gloss_scoring import LeafScore
from fluency.wsd.languages.portuguese import PortugueseWSDAdapter
from fluency.wsd.menus import MenuAnalysis, SenseLeaf, build_analysis_id
from fluency.wsd.runner import (
    ClosedMenuWSDRunner,
    WSDComponents,
    WSDExecutionProfile,
    WSDRequest,
)


class DummyGlossScorer:
    model_revision = "test-model"

    def __init__(self, scores):
        self._scores = scores

    def score(self, sentence, analyses, translation=""):
        return self._scores


class DummyCandidatePolicy:
    def __init__(self, prep):
        self._prep = prep

    def prepare(self, **kwargs):
        return self._prep

    def adjust_scores(self, scores, analyses):
        return scores

    def repair_leaf(self, *, selected, **kwargs):
        return selected


class RunnerFixesTests(unittest.TestCase):
    def setUp(self):
        self.card_id = "card_pt_" + "a" * 32
        self.leaf_adj = SenseLeaf(
            sense_id="sense_estupendo_adj",
            translation="wonderful",
            definition="",
            source_reference="kaikki:estupendo:adj",
            provider_metadata={},
        )
        self.analysis_adj = MenuAnalysis(
            menu_analysis_id=build_analysis_id(
                card_id=self.card_id,
                source_adapter="wiktionary-sense-menu/v1",
                source_analysis_key="pt:estupendo:adj:0",
            ),
            card_id=self.card_id,
            surface_form="estupendo",
            headword="estupendo",
            part_of_speech="adj",
            source_adapter="wiktionary-sense-menu/v1",
            source_analysis_key="pt:estupendo:adj:0",
            senses=(self.leaf_adj,),
            provider_metadata={},
        )

    def test_no_compatible_analysis_does_not_abstain(self):
        """When spaCy tags VERB on estupendo (menu has only adj), runner must NOT abstain."""
        prep = CandidatePreparation(
            analyses=(self.analysis_adj,),
            evidence={
                "pos_match_status": "no_compatible_analysis",
                "observed_pos": "VERB",
            },
        )
        scores = (
            LeafScore(
                menu_analysis_id=self.analysis_adj.menu_analysis_id,
                sense_id=self.leaf_adj.sense_id,
                score=0.92,
            ),
        )
        components = WSDComponents(
            language=PortugueseWSDAdapter(),
            gloss=DummyGlossScorer(scores),
            candidate_policy=DummyCandidatePolicy(prep),
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
            card_id=self.card_id,
            surface_form="estupendo",
            sentence_id="sentence_" + "1" * 32,
            sentence="O jantar foi estupendo.",
            translation="Dinner was wonderful.",
            sense_menu_content_id="sha256:" + "0" * 64,
            analyses=(self.analysis_adj,),
            observed_pos="VERB",
        )
        assignment = runner.assign(request)
        self.assertEqual(assignment.status, "assigned")
        self.assertEqual(assignment.selected_sense_id, "sense_estupendo_adj")
        self.assertEqual(assignment.emitted_level, "leaf")
        commit_evidence = assignment.evidence.get("commit", {})
        self.assertIn("tagger_pos_disagrees_with_single_menu_category", commit_evidence.get("evidence_guards", []))

    def test_provider_order_votes_false_lets_gloss_winner_prevail(self):
        """When Wiktionary lists sense 1 first but gloss prefers sense 2, sense 2 wins cleanly."""
        leaf_1 = SenseLeaf(
            sense_id="sense_because",
            translation="because",
            definition="",
            source_reference="kaikki:que:conj:1",
            provider_metadata={},
        )
        leaf_2 = SenseLeaf(
            sense_id="sense_that",
            translation="that",
            definition="",
            source_reference="kaikki:que:conj:2",
            provider_metadata={},
        )
        analysis_que = MenuAnalysis(
            menu_analysis_id=build_analysis_id(
                card_id=self.card_id,
                source_adapter="wiktionary-sense-menu/v1",
                source_analysis_key="pt:que:conj:0",
            ),
            card_id=self.card_id,
            surface_form="que",
            headword="que",
            part_of_speech="conj",
            source_adapter="wiktionary-sense-menu/v1",
            source_analysis_key="pt:que:conj:0",
            senses=(leaf_1, leaf_2),
            provider_metadata={},
        )
        prep = CandidatePreparation(
            analyses=(analysis_que,),
            evidence={"pos_match_status": "matched", "observed_pos": "SCONJ"},
        )
        # Gloss scorer strongly prefers sense_that
        scores = (
            LeafScore(
                menu_analysis_id=analysis_que.menu_analysis_id,
                sense_id=leaf_2.sense_id,
                score=0.95,
            ),
            LeafScore(
                menu_analysis_id=analysis_que.menu_analysis_id,
                sense_id=leaf_1.sense_id,
                score=0.88,
            ),
        )
        components = WSDComponents(
            language=PortugueseWSDAdapter(),
            gloss=DummyGlossScorer(scores),
            candidate_policy=DummyCandidatePolicy(prep),
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
                cross_analysis_vote="gloss_margin",
                cross_analysis_margin=0.02,
            ),
        )
        runner = ClosedMenuWSDRunner(profile, components)
        request = WSDRequest(
            card_id=self.card_id,
            surface_form="que",
            sentence_id="sentence_" + "2" * 32,
            sentence="Acho que sim.",
            translation="I think that yes.",
            sense_menu_content_id="sha256:" + "0" * 64,
            analyses=(analysis_que,),
            observed_pos="SCONJ",
        )
        assignment = runner.assign(request)
        self.assertEqual(assignment.status, "assigned")
        self.assertEqual(assignment.selected_sense_id, "sense_that")
        self.assertEqual(assignment.emitted_level, "leaf")


if __name__ == "__main__":
    unittest.main()
