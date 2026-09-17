"""Tests for v14 MWE non-decomposition policy, inventory indexing, and dual-write."""

from __future__ import annotations

import unittest
from pathlib import Path

from fluency.core.hashing import content_id
from fluency.mwe.policy import classify_mwe
from fluency.projections import materialize_selection
from fluency.wsd.config import _load
from fluency.wsd.disposition import DispositionPolicy
from fluency.wsd.gloss_scoring import LeafScore
from fluency.wsd.languages.spanish import SpanishWSDAdapter
from fluency.wsd.menus import MenuAnalysis, SenseLeaf, build_analysis_id
from fluency.wsd.multiword import (
    MULTIWORD_SOURCE_ADAPTER,
    MultiwordEntry,
    index_multiword_senses,
)
from fluency.wsd.runner import (
    ClosedMenuWSDRunner,
    WSDComponents,
    WSDExecutionProfile,
    WSDRequest,
)


CARD_ID = "card_es_" + "1" * 32
SENTENCE_ID = "sentence_" + "2" * 32


class FakeGlossScorer:
    model_revision = "gemini-embedding-001"

    def __init__(self, scores: dict[tuple[str, str], float]) -> None:
        self.scores = scores

    def score(
        self,
        sentence: str,
        analyses: tuple[MenuAnalysis, ...],
        **kwargs: Any,
    ) -> list[LeafScore]:
        results = []
        for analysis in analyses:
            for sense in analysis.senses:
                score_val = self.scores.get(
                    (analysis.menu_analysis_id, sense.sense_id), 0.5
                )
                results.append(
                    LeafScore(
                        menu_analysis_id=analysis.menu_analysis_id,
                        sense_id=sense.sense_id,
                        score=score_val,
                    )
                )
        results.sort(key=lambda item: item.score, reverse=True)
        return results


def make_menu(headword: str, pos: str, senses: tuple[tuple[str, str], ...]) -> MenuAnalysis:
    key = f"{headword}|{pos}"
    aid = build_analysis_id(card_id=CARD_ID, source_adapter="wiktionary/v1", source_analysis_key=key)
    return MenuAnalysis(
        menu_analysis_id=aid,
        card_id=CARD_ID,
        surface_form=headword,
        headword=headword,
        part_of_speech=pos,
        source_adapter="wiktionary/v1",
        source_analysis_key=key,
        senses=tuple(
            SenseLeaf(
                sense_id=sid,
                translation=trans,
                definition=trans,
                source_reference="wiktionary",
                provider_metadata={},
            )
            for sid, trans in senses
        ),
        provider_metadata={},
    )


class TestMWEPolicy(unittest.TestCase):
    def test_spanish_policy(self):
        # Keep true idioms/locutions
        k1 = classify_mwe("en serio", ["seriously", "for real"], "es", corpus_freq=50)
        self.assertEqual(k1.verdict, "keep")
        self.assertTrue(k1.non_compositional)

        k2 = classify_mwe("por qué", ["why"], "es", corpus_freq=100)
        self.assertEqual(k2.verdict, "keep")

        # Exclude compositional noise
        d1 = classify_mwe("muy serio", ["very serious"], "es", corpus_freq=20)
        self.assertEqual(d1.verdict, "exclude")
        self.assertEqual(d1.reason, "compositional")
        self.assertFalse(d1.non_compositional)

        d2 = classify_mwe("si puedo", ["if I can"], "es", corpus_freq=5)
        self.assertEqual(d2.verdict, "exclude")
        self.assertEqual(d2.reason, "compositional")

        # Tier 2 (zero frequency) non-compositional expression
        t2 = classify_mwe("a duras penas", ["with difficulty"], "es", corpus_freq=0)
        self.assertEqual(t2.verdict, "exclude")
        self.assertEqual(t2.reason, "zero_freq")
        self.assertTrue(t2.non_compositional)

    def test_portuguese_policy(self):
        k1 = classify_mwe("de novo", ["again"], "pt", corpus_freq=200)
        self.assertEqual(k1.verdict, "keep")
        self.assertTrue(k1.non_compositional)

        k2 = classify_mwe("não me diga", ["you do not say"], "pt", corpus_freq=15)
        self.assertEqual(k2.verdict, "keep")

        d1 = classify_mwe("muito sério", ["very serious"], "pt", corpus_freq=10)
        self.assertEqual(d1.verdict, "exclude")
        self.assertEqual(d1.reason, "compositional")

    def test_czech_policy(self):
        k1 = classify_mwe("dobrý den", ["good day"], "cs", corpus_freq=65)
        self.assertEqual(k1.verdict, "keep")

        k2 = classify_mwe("ty vole", ["dude", "man"], "cs", corpus_freq=30)
        self.assertEqual(k2.verdict, "keep")

        d1 = classify_mwe("velmi vážný", ["very serious"], "cs", corpus_freq=10)
        self.assertEqual(d1.verdict, "exclude")
        self.assertEqual(d1.reason, "compositional")


class TestMWEIndex(unittest.TestCase):
    def test_index_filters_compositional_and_unattested(self):
        payload = {
            "mwes": {
                "en serio": {
                    "id": "mwe:en serio",
                    "expression": "en serio",
                    "translations": ["seriously"],
                    "attach_words": ["serio"],
                    "corpus_freq": 100,
                    "verdict": "keep",
                    "non_compositional": True,
                },
                "muy serio": {
                    "id": "mwe:muy serio",
                    "expression": "muy serio",
                    "translations": ["very serious"],
                    "attach_words": ["serio"],
                    "corpus_freq": 50,
                    "verdict": "exclude",
                    "reason": "compositional",
                    "non_compositional": False,
                },
                "a duras penas": {
                    "id": "mwe:a duras penas",
                    "expression": "a duras penas",
                    "translations": ["with difficulty"],
                    "attach_words": ["penas"],
                    "corpus_freq": 0,
                    "verdict": "exclude",
                    "reason": "zero_freq",
                    "non_compositional": True,
                },
            }
        }
        idx = index_multiword_senses(payload, minimum_corpus_frequency=1, filter_compositional=True)
        self.assertIn("serio", idx)
        exprs = [e.expression for e in idx["serio"]]
        self.assertIn("en serio", exprs)
        self.assertNotIn("muy serio", exprs)
        self.assertNotIn("penas", idx)


class TestMWEDualWrite(unittest.TestCase):
    def test_runner_dual_write_when_mwe_wins(self):
        serio_menu = make_menu("serio", "ADJ", (("s1", "serious"), ("s2", "grave")))
        mwe_aid = build_analysis_id(
            card_id=CARD_ID,
            source_adapter=MULTIWORD_SOURCE_ADAPTER,
            source_analysis_key="en serio",
        )

        mwe_entry = MultiwordEntry(
            expression="en serio",
            translations=("seriously", "for real"),
            corpus_frequency=150,
            sources=("spanishdict", "wiktionary"),
            entry_id="mwe:en serio",
        )
        mwe_index = {"serio": (mwe_entry,)}

        scores = {
            (serio_menu.menu_analysis_id, "s1"): 0.70,
            (serio_menu.menu_analysis_id, "s2"): 0.65,
            (mwe_aid, "mwe:en serio"): 0.95,
        }

        profile = WSDExecutionProfile(
            token_tuple_vote=False,
            tuple_vote_minimum_margin=0.0,
            calibration=False,
            alignment=False,
            generative_escalation=False,
            disposition=DispositionPolicy(minimum_confidence=None, weak="retain"),
            candidate_preparation=False,
            multiword_candidates=True,
            active_projection="mwe_augmented",
        )
        components = WSDComponents(
            language=SpanishWSDAdapter(),
            gloss=FakeGlossScorer(scores),
            multiword_index=mwe_index,
            multiword_inventory_content_id=content_id(b"fake_mwe_inv"),
        )
        runner = ClosedMenuWSDRunner(profile, components)

        request = WSDRequest(
            card_id=CARD_ID,
            surface_form="serio",
            sentence_id=SENTENCE_ID,
            sentence="¿Me lo dices en serio?",
            translation="Are you telling me seriously?",
            sense_menu_content_id=content_id(b"fake_menu"),
            analyses=(serio_menu,),
            target_span=(16, 21),
            target_observed_form="serio",
        )

        assignment = runner.assign(request)

        self.assertEqual(assignment.status, "assigned")
        self.assertEqual(assignment.active_selection_projection, "mwe_augmented")
        self.assertEqual(assignment.evidence["selected_multiword"], "en serio")

        # Verify dual-write: provider word-leaf is captured beside MWE winner
        word_leaf = assignment.evidence.get("word_leaf")
        self.assertIsNotNone(word_leaf)
        self.assertEqual(word_leaf["headword"], "serio")
        self.assertEqual(word_leaf["sense_id"], "s1")
        self.assertEqual(word_leaf["translation"], "serious")
        self.assertEqual(word_leaf["score"], 0.70)
        self.assertEqual(word_leaf["emitted_level"], "leaf")

        # Verify projection materialization
        as_dict = assignment.to_dict()
        mwe_proj = materialize_selection(as_dict, "mwe_augmented")
        self.assertEqual(mwe_proj["evidence"]["selected_multiword"], "en serio")
        self.assertIsNotNone(mwe_proj["evidence"]["word_leaf"])

        prov_proj = materialize_selection(as_dict, "provider_only")
        self.assertEqual(prov_proj["selected_sense_id"], "s1")
        self.assertEqual(prov_proj["selected_tuple"]["headword"], "serio")


class TestV14Profiles(unittest.TestCase):
    def test_v14_profiles_exist_and_point_to_valid_snapshots(self):
        root = Path(".")
        workspace = Path("/Users/joshuathomasamar/PycharmProjects/Fluency-Workspace")
        for pid in ("es-v14-1", "pt-v14-1", "cs-v14-1"):
            prof = _load(root, "models", pid)
            self.assertEqual(prof["profile_id"], pid)
            self.assertTrue(prof["multiword"]["enabled"])
            self.assertEqual(prof["multiword"]["active_projection"], "mwe_augmented")
            self.assertTrue(prof["multiword"]["dual_write_word_leaf"])
            rel_snap = prof["multiword"]["snapshot_path"]
            abs_snap = workspace / rel_snap
            self.assertTrue(abs_snap.exists(), f"Snapshot missing: {abs_snap}")


class TestSenseMenuOverlays(unittest.TestCase):
    def test_conversational_filler_and_slang_overlay_injection(self):
        from fluency.wsd.overlays import InMemoryOverlayRegistry, SenseOverlayEntry

        filler = SenseOverlayEntry(
            entry_id="overlay:filler:o_sea",
            kind="conversational_filler",
            expression="o sea",
            translations=("I mean", "that is to say"),
            part_of_speech="FILLER",
            attach_words=("sea",),
            domain_tags=("discourse", "conversational_filler"),
            corpus_frequency=500,
        )
        registry = InMemoryOverlayRegistry([filler])

        sea_menu = make_menu("sea", "VERB", (("v1", "be"), ("v2", "may be")))
        filler_aid = build_analysis_id(
            card_id=CARD_ID,
            source_adapter="overlay:conversational_filler/v1",
            source_analysis_key="o sea",
        )

        scores = {
            (sea_menu.menu_analysis_id, "v1"): 0.60,
            (sea_menu.menu_analysis_id, "v2"): 0.55,
            (filler_aid, "overlay:filler:o_sea#1"): 0.92,
        }

        profile = WSDExecutionProfile(
            token_tuple_vote=False,
            tuple_vote_minimum_margin=0.0,
            calibration=False,
            alignment=False,
            generative_escalation=False,
            disposition=DispositionPolicy(minimum_confidence=None, weak="retain"),
            candidate_preparation=False,
            multiword_candidates=True,
            active_projection="mwe_augmented",
        )
        components = WSDComponents(
            language=SpanishWSDAdapter(),
            gloss=FakeGlossScorer(scores),
            overlay_provider=registry,
        )
        runner = ClosedMenuWSDRunner(profile, components)

        request = WSDRequest(
            card_id=CARD_ID,
            surface_form="sea",
            sentence_id=SENTENCE_ID,
            sentence="O sea, no tiene sentido.",
            translation="I mean, it doesn't make sense.",
            sense_menu_content_id=content_id(b"fake_menu"),
            analyses=(sea_menu,),
            target_span=(2, 5),
            target_observed_form="sea",
        )

        assignment = runner.assign(request)
        self.assertEqual(assignment.status, "assigned")
        self.assertEqual(assignment.active_selection_projection, "mwe_augmented")
        self.assertEqual(assignment.selected_tuple.headword, "o sea")
        self.assertEqual(assignment.selected_tuple.part_of_speech, "FILLER")
        self.assertEqual(assignment.evidence["word_leaf"]["headword"], "sea")
        self.assertEqual(assignment.evidence["word_leaf"]["translation"], "be")
