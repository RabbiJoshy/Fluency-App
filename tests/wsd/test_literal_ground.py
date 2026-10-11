"""LITERAL-GROUND: closed-class preposition guards and overlap specificity."""

import json
from pathlib import Path
import unittest

from fluency.speech.wsd_execute import ExactTextGlossScorer, model_profile
from fluency.wsd.candidate_policy import CandidatePreparation
from fluency.wsd.commit import CommitPolicy
from fluency.wsd.disposition import DispositionPolicy
from fluency.wsd.gloss_scoring import LeafScore
from fluency.wsd.ground import (
    GroundPolicy,
    ClosedClassEntry,
    TargetSyntax,
    ground_selection,
    load_ground_policy,
)
from fluency.wsd.languages.portuguese import PortugueseWSDAdapter
from fluency.wsd.menus import MenuAnalysis, SenseLeaf, build_analysis_id
from fluency.wsd.runner import (
    ClosedMenuWSDRunner,
    WSDComponents,
    WSDExecutionProfile,
    WSDRequest,
)

REPO = Path(__file__).resolve().parents[2]
CARD = "card_pt_" + "d" * 32


def leaf(sense_id, translation, definition=""):
    return SenseLeaf(
        sense_id=sense_id,
        translation=translation,
        definition=definition,
        source_reference=f"kaikki:{sense_id}",
        provider_metadata={},
    )


def analysis(headword, pos, *senses, key=None):
    key = key or f"pt:{headword}:{pos}"
    return MenuAnalysis(
        menu_analysis_id=build_analysis_id(
            card_id=CARD, source_adapter="wiktionary-sense-menu/v1", source_analysis_key=key
        ),
        card_id=CARD,
        surface_form=headword,
        headword=headword,
        part_of_speech=pos,
        source_adapter="wiktionary-sense-menu/v1",
        source_analysis_key=key,
        senses=senses,
        provider_metadata={},
    )


OF = leaf("de-of", "of (in relation to)")
BY = leaf("de-by", "by means of; by")
WEARING = leaf("de-wearing", "in (wearing)")
FROM = leaf("de-from", "from (born in or coming out of)")
DE = analysis("de", "prep", OF, BY, WEARING, FROM)

POLICY = GroundPolicy(
    policy_id="test-ground",
    content_id="sha256:" + "0" * 64,
    surfaces=frozenset({"de", "da"}),
    entries={("de", "prep"): ClosedClassEntry("de", "prep", "de-of", True)},
    margin_floor=0.025,
)


def syntax(dep, head_pos="NOUN", head_dep="obl", verb_form="", governor="VERB"):
    return TargetSyntax(dep, head_pos, head_dep, verb_form, governor, "test-parser@1")


class TargetSyntaxTests(unittest.TestCase):
    def test_infinitive_complement_is_governed(self):
        # gostaria de fazer, parar de falar, jeito de fazer
        self.assertEqual(
            syntax("mark", "VERB", "xcomp", "Inf").governed(), "infinitive_complement"
        )

    def test_finite_clause_is_not(self):
        # "más tiempo de lo que esperábamos" -- de is "than", not a complement
        self.assertIsNone(syntax("mark", "VERB", "acl", "Fin").governed())

    def test_verb_prepositional_object_is_governed(self):
        # precisa de dinheiro, lembrar de mim
        self.assertEqual(syntax("case", head_dep="obj").governed(), "verb_prepositional_object")

    def test_noun_complement_is_governed(self):
        # bolso da jaqueta, anel da mulher
        self.assertEqual(
            syntax("case", head_dep="nmod", governor="NOUN").governed(), "noun_complement"
        )

    def test_verb_adjunct_is_left_to_the_scorer(self):
        # vieram de bicicleta ("by"), saindo do país ("from")
        self.assertIsNone(syntax("case", head_dep="obl").governed())


class GroundSelectionTests(unittest.TestCase):
    def scores(self, **values):
        base = {"de-of": 0.70, "de-by": 0.70, "de-wearing": 0.70, "de-from": 0.70}
        base.update({key.replace("_", "-"): value for key, value in values.items()})
        return base

    def test_rival_inside_the_floor_keeps_the_primary(self):
        # lembrar-se de: "in (wearing)" won by 0.006 on the r3 deck
        decision = ground_selection(
            POLICY, analysis=DE, selected_sense_id="de-wearing",
            scores=self.scores(de_of=0.744, de_wearing=0.750), syntax=None,
        )
        self.assertEqual((decision.sense_id, decision.reason), ("de-of", "primary_prior_margin"))

    def test_rival_clearing_the_floor_stands(self):
        # A minha esposa é de Boston: "from" by 0.05
        decision = ground_selection(
            POLICY, analysis=DE, selected_sense_id="de-from",
            scores=self.scores(de_of=0.78, de_from=0.83), syntax=syntax("case", "PROPN", "ROOT", governor="PROPN"),
        )
        self.assertEqual((decision.sense_id, decision.reason), ("de-from", None))

    def test_governed_use_takes_the_primary_whatever_the_margin(self):
        decision = ground_selection(
            POLICY, analysis=DE, selected_sense_id="de-by",
            scores=self.scores(de_of=0.74, de_by=0.82),
            syntax=syntax("mark", "VERB", "acl", "Inf", governor="NOUN"),
        )
        self.assertEqual((decision.sense_id, decision.reason), ("de-of", "governed_bypass"))
        self.assertEqual(decision.evidence["governed"], "infinitive_complement")

    def test_undeclared_analysis_is_out_of_scope(self):
        other = analysis("o", "article", leaf("o-the", "the"))
        self.assertIsNone(ground_selection(
            POLICY, analysis=other, selected_sense_id="o-the", scores={"o-the": 0.9}, syntax=None,
        ))

    def test_a_primary_missing_from_the_menu_fails_loudly(self):
        menu = analysis("de", "prep", BY, FROM)
        with self.assertRaises(ValueError):
            ground_selection(
                POLICY, analysis=menu, selected_sense_id="de-by",
                scores={"de-by": 0.8, "de-from": 0.7}, syntax=None,
            )


class ShippedPolicyTests(unittest.TestCase):
    def test_closed_class_files_load_and_bypass_only_de(self):
        for lang in ("es", "pt"):
            path = REPO / f"config/wsd/closed-class/{lang}.json"
            policy = load_ground_policy(path, content_id="sha256:" + "0" * 64)
            self.assertEqual(policy.margin_floor, 0.025)
            bypass = {e.headword for e in policy.entries.values() if e.governed_bypass}
            self.assertEqual(bypass, {"de"} if lang == "pt" else {"de", "del"})
            # por and para were measured and left out; Spanish a / al / en too.
            self.assertFalse({"por", "para"} & policy.surfaces)
            raw = json.loads(path.read_text(encoding="utf-8"))
            self.assertIn("por", raw["not_guarded"])

    def test_v25_profiles_extend_v24_with_both_changes(self):
        for lang in ("es", "pt"):
            profile = model_profile(f"{lang}-v25-1")
            self.assertTrue(profile["gloss"]["overlap_specificity"])
            self.assertEqual(profile["gloss"]["model_revision"], "gemini-embedding-001")
            self.assertTrue(profile["ground"]["enabled"])
            self.assertFalse(model_profile(f"{lang}-v24-1").get("ground"))


class OverlapSpecificityTests(unittest.TestCase):
    def setUp(self):
        self.vectors = {"Excepto tu billetera.": [1.0, 0.0], "except": [1.0, 0.0], "except for": [1.0, 0.0]}
        self.menu = analysis(
            "excepto", "ADP", leaf("except", "except"), leaf("except-for", "except for"),
            key="es:excepto:ADP",
        )

    def score(self, translation, specificity):
        scorer = ExactTextGlossScorer(self.vectors, overlap_specificity=specificity)
        return {
            item.sense_id: item.score
            for item in scorer.score("Excepto tu billetera.", (self.menu,), translation=translation)
        }

    def test_longer_literal_cue_takes_the_bonus(self):
        scores = self.score("Except for your wallet, I couldn't find it.", True)
        self.assertGreater(scores["except-for"], scores["except"])

    def test_without_specificity_both_tie(self):
        scores = self.score("Except for your wallet, I couldn't find it.", False)
        self.assertEqual(scores["except-for"], scores["except"])

    def test_short_cue_alone_still_earns_it(self):
        scores = self.score("Except your wallet, I couldn't find it.", True)
        self.assertGreater(scores["except"], scores["except-for"])

    def test_a_different_headword_never_dominates(self):
        # hablar con ella / "talk to her": the pronominal hablarse "to talk to"
        # is another word, not a more literal reading of hablar "to talk".
        talk = analysis("hablar", "VERB", leaf("talk", "to talk"), key="es:hablar:VERB")
        talk_to = analysis("hablarse", "VERB", leaf("talk-to", "to talk to"), key="es:hablarse:VERB")
        vectors = {"Quiero hablar con ella.": [1.0], "to talk": [1.0], "to talk to": [1.0]}
        scorer = ExactTextGlossScorer(vectors, overlap_specificity=True)
        scores = {
            item.sense_id: item.score
            for item in scorer.score("Quiero hablar con ella.", (talk, talk_to), translation="I want to talk to her.")
        }
        self.assertEqual(scores["talk"], scores["talk-to"])


class PassThroughPolicy:
    def __init__(self, analyses):
        self.analyses = analyses

    def prepare(self, **kwargs):
        return CandidatePreparation(analyses=self.analyses, evidence={"pos_match_status": "matched"})

    def adjust_scores(self, scores, analyses):
        return scores

    def repair_leaf(self, *, selected, **kwargs):
        return selected


class FixedScorer:
    model_revision = "test-model"

    def __init__(self, scores):
        self.scores = scores

    def score(self, sentence, analyses, translation=""):
        return tuple(
            LeafScore(DE.menu_analysis_id, sense_id, value) for sense_id, value in self.scores.items()
        )


class RunnerGroundTests(unittest.TestCase):
    def assign(self, scores, *, ground, syntax=None, commit=None):
        profile = WSDExecutionProfile(
            token_tuple_vote=False,
            tuple_vote_minimum_margin=0.0,
            calibration=False,
            alignment=False,
            generative_escalation=False,
            disposition=DispositionPolicy(minimum_confidence=None, weak="retain"),
            candidate_preparation=True,
            commit=commit or CommitPolicy(),
            ground=ground,
        )
        runner = ClosedMenuWSDRunner(profile, WSDComponents(
            language=PortugueseWSDAdapter(),
            gloss=FixedScorer(scores),
            candidate_policy=PassThroughPolicy((DE,)),
        ))
        return runner.assign(WSDRequest(
            card_id=CARD,
            surface_form="de",
            sentence_id="sentence_" + "1" * 32,
            sentence="Minha esposa parece não se lembrar de mim.",
            translation="My wife doesn't seem to remember me.",
            sense_menu_content_id="sha256:" + "0" * 64,
            analyses=(DE,),
            target_syntax=syntax,
        ))

    SCORES = {"de-of": 0.744, "de-by": 0.70, "de-wearing": 0.750, "de-from": 0.71}

    def test_without_ground_the_rare_sense_wins(self):
        self.assertEqual(self.assign(self.SCORES, ground=None).selected_sense_id, "de-wearing")

    def test_ground_restores_the_primary_and_says_why(self):
        result = self.assign(self.SCORES, ground=POLICY)
        self.assertEqual(result.selected_sense_id, "de-of")
        self.assertIn("ground", result.decision_path)
        self.assertEqual(result.evidence["ground"]["reason"], "primary_prior_margin")
        self.assertEqual(result.selection_projections["provider_only"].selected_sense_id, "de-of")

    def test_grounded_leaf_commits_where_rank_agreement_would_abstain(self):
        # The raw gloss winner and the grounded leaf disagree; under v24's
        # abstain-on-unresolved policy that disagreement is the noise GROUND
        # absorbs, so the row is published as a declared default.
        commit = CommitPolicy(
            strategy="rank_agreement", evidence_guards=True,
            unresolved_outcome="abstain", provider_order_votes=False,
        )
        result = self.assign(
            self.SCORES, ground=POLICY, commit=commit,
            syntax=syntax("case", "PRON", "obj", governor="VERB"),
        )
        self.assertEqual(result.status, "assigned")
        self.assertEqual(result.selected_sense_id, "de-of")
        self.assertEqual(result.emitted_level, "leaf")
        self.assertEqual(result.evidence["ground"]["governed"], "verb_prepositional_object")
        self.assertEqual(
            result.evidence["commit"]["ground_override"]["reason"], "governed_bypass"
        )


if __name__ == "__main__":
    unittest.main()
