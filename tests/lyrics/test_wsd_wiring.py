"""Tests for Lyrics WSD wiring: overlays, deterministic declared bypass, and validation."""

from pathlib import Path
import unittest

from fluency.wsd.contracts import WSDAssignment
from fluency.wsd.importer import _validated_multiword_fields
from fluency.wsd.menus import MenuAnalysis, SenseLeaf, build_analysis_id
from fluency.wsd.languages.base import LanguageAdapter, TargetOccurrence
from fluency.wsd.overlays import (
    CompositeOverlayProvider,
    InMemoryOverlayRegistry,
    SenseOverlayEntry,
    build_lyrics_overlay_provider,
    declared_gloss_to_overlay,
)
from fluency.wsd.runner import (
    ClosedMenuWSDRunner,
    CommitPolicy,
    DispositionPolicy,
    LeafScore,
    WSDComponents,
    WSDExecutionProfile,
    WSDRequest,
)
from fluency.wsd.splice import declared_row, _is_declared_default


class DummySpanishAdapter(LanguageAdapter):
    language_code = "es"

    def locate(self, sentence: str, surface_form: str):
        idx = sentence.casefold().find(surface_form.casefold())
        if idx >= 0:
            return (TargetOccurrence(surface_form, surface_form.casefold(), idx, idx + len(surface_form)),)
        return ()


class DummyGlossScorer:
    model_revision = "gemini-embedding-001"

    def __init__(self, overlay_score: float = 0.9, provider_score: float = 0.4):
        self.overlay_score = overlay_score
        self.provider_score = provider_score

    def score(self, sentence: str, analyses: tuple[MenuAnalysis, ...], **kwargs):
        scores = []
        for a in analyses:
            for leaf in a.senses:
                score = self.overlay_score if "overlay" in leaf.sense_id or "bb-slang" in leaf.sense_id else self.provider_score
                scores.append(LeafScore(a.menu_analysis_id, leaf.sense_id, score))
        return tuple(scores)


class TestLyricsWSDWiring(unittest.TestCase):
    def setUp(self):
        self.repo_root = Path(__file__).parents[2]
        self.workspace = self.repo_root.parent / "Fluency-Workspace"

    def test_overlay_provider_wiring_and_competition_win(self):
        provider = build_lyrics_overlay_provider(
            self.repo_root,
            "es",
            workspace=self.workspace if self.workspace.is_dir() else None,
            artist="bad-bunny",
        )
        self.assertIsInstance(provider, CompositeOverlayProvider)

        comps = WSDComponents(
            language=DummySpanishAdapter(),
            gloss=DummyGlossScorer(overlay_score=0.9, provider_score=0.4),
            overlay_provider=provider,
        )
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
            commit=CommitPolicy(strategy="margin", unresolved_outcome="assign"),
        )
        runner = ClosedMenuWSDRunner(profile, comps)

        cid = "card_es_" + "1" * 32
        sid = "sentence_" + "2" * 32
        aid = build_analysis_id(card_id=cid, source_adapter="spanishdict", source_analysis_key="conejo")
        leaf = SenseLeaf("animal_1", "rabbit", "an animal", "spanishdict", {})
        analysis = MenuAnalysis(aid, cid, "conejo", "conejo", "NOUN", "spanishdict", "conejo", (leaf,), {})
        req = WSDRequest(
            card_id=cid,
            surface_form="conejo",
            sentence_id=sid,
            sentence="El Conejo Malo está aquí",
            translation="Bad Bunny is here",
            sense_menu_content_id="sha256:" + "0" * 64,
            analyses=(analysis,),
        )

        assignment = runner.assign(req)
        self.assertEqual(assignment.status, "assigned")
        self.assertEqual(assignment.active_selection_projection, "mwe_augmented")
        self.assertEqual(assignment.selected_sense_id, "bb-slang-conejo#1")
        self.assertEqual(assignment.evidence.get("selected_multiword"), "conejo")

        # Verify dual-write of word leaf
        word_leaf = assignment.evidence.get("word_leaf")
        self.assertIsNotNone(word_leaf)
        self.assertEqual(word_leaf["sense_id"], "animal_1")
        self.assertEqual(word_leaf["translation"], "rabbit")

        # Verify importer validates this overlay winner
        validated = _validated_multiword_fields(
            assignment,
            menu_analysis_id=assignment.menu_analysis_id,
            selected_sense_id=assignment.selected_sense_id,
            selected_tuple=assignment.selected_tuple,
            source_kind="multiword",
            pair=(cid, sid),
        )
        self.assertEqual(validated, ("conejo", "NOUN", {"bb-slang-conejo#1"}))

    def test_single_sense_declared_card_deterministic_bypass(self):
        cid = "card_es_" + "3" * 32
        sid = "sentence_" + "4" * 32
        menu_content_id = "sha256:" + "5" * 64
        aid = build_analysis_id(card_id=cid, source_adapter="overlay:entity/v1", source_analysis_key="benito")

        menu_card = {
            "card_id": cid,
            "surface_form": "benito",
            "resolution": {
                "strategy": "entity",
                "entry": {"entry_id": "bb-entity-benito"},
            },
            "analyses": [
                {
                    "menu_analysis_id": aid,
                    "headword": "benito",
                    "part_of_speech": "PROPN",
                    "senses": [
                        {
                            "sense_id": "bb-entity-benito#1",
                            "translation": "Benito Antonio Martínez Ocasio (Bad Bunny)",
                            "definition": "person",
                        }
                    ],
                }
            ],
        }

        # Produce declared row
        row = declared_row(
            card_id=cid,
            surface_form="benito",
            sentence_id=sid,
            menu_card=menu_card,
            sense_menu_content_id=menu_content_id,
        )

        # Must have zero model revisions and deterministic default
        self.assertEqual(row["decision_kind"], "deterministic_default")
        self.assertEqual(row["model_revisions"], {})
        self.assertEqual(row["selected_sense_id"], "bb-entity-benito#1")

        # Verify _is_declared_default accepts it
        assignment = WSDAssignment.from_dict(row)
        card_menu_tuples = {
            aid: ("benito", "PROPN", {"bb-entity-benito#1"})
        }
        self.assertTrue(_is_declared_default(assignment, card_menu_tuples))


if __name__ == "__main__":
    unittest.main()
