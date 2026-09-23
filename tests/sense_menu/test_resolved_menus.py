"""Stage 02 builds a named set of cards from the resolver, and no other card moves."""

import json
import tempfile
import unittest
from pathlib import Path

from fluency.core.hashing import file_content_id
from fluency.core.identity import create_card_record
from fluency.sense_menu.config import load_sense_menu_language_policy
from fluency.sense_menu.declared_menu import DECLARED_GLOSS_ADAPTER
from fluency.sense_menu.spanishdict import SpanishDictSenseMenuAdapter
from fluency.sense_menu.spanishdict_lemmas import SpanishDictHeadwordSource, SpanishDictLemmaRule
from fluency.surfaces.declared import Context, DeclaredRegistry
from fluency.surfaces.resolver import ModePolicy, Resolver

REPO = Path(__file__).resolve().parents[2]
SURFACES = ("está", "usted", "cura", "sr", "estate", "bum")


def sense(pos, translation, context=""):
    return {"pos": pos, "translation": translation, "context": context, "source": "spanishdict"}


def write_snapshot(root: Path) -> Path:
    """A pinned SpanishDict snapshot small enough to read in one screen."""
    snapshot = root / "snapshot"
    snapshot.mkdir()
    payloads = {
        "surface_cache.json": {
            "está": {"query": "está", "entry_lang": "es",
                     "dictionary_analyses": [{"headword": "está", "senses": [sense("PHRASE", "he's")]}],
                     "possible_results": [{"headword": "estar", "heuristic": "conjugation"}]},
            "usted": {"query": "usted", "entry_lang": "es",
                      "dictionary_analyses": [{"headword": "usted", "senses": [sense("PRON", "you")]}],
                      "possible_results": []},
            "cura": {"query": "cura", "entry_lang": "es",
                     "dictionary_analyses": [{"headword": "cura", "senses": [sense("NOUN", "treatment")]}],
                     "possible_results": []},
            "sr": {"query": "sr", "dictionary_analyses": [{"headword": "Sr.", "senses": [sense("NOUN", "Mr.")]}],
                   "possible_results": []},
        },
        "headword_cache.json": {
            "estar": {"dictionary_analyses": [{"headword": "estar", "senses": [
                sense("VERB", "to be"), sense("VERB", "to stay")]}]},
        },
        "spanish_forms.json": {"cura": {}, "estar": {}, "usted": {}},
        "conjugation_reverse.json": {"está": [{"lemma": "estar", "mood": "imperativo", "person": "2s"}]},
    }
    files = []
    for name, payload in payloads.items():
        path = snapshot / name
        path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
        files.append({"path": name, "sha256": file_content_id(path).removeprefix("sha256:")})
    (snapshot / "artifact.json").write_text(json.dumps({
        "schema_version": "spanishdict-snapshot/v1", "artifact_kind": "dictionary_menu_source",
        "language": "es", "provider": "spanishdict", "snapshot_id": "fixture-2026-08",
        "content_files": files}), encoding="utf-8")
    return snapshot


class ResolvedMenuTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.snapshot = snapshot = write_snapshot(Path(self.temporary.name))
        self.policy = load_sense_menu_language_policy(REPO, policy_id="es-spanishdict-v1", language="es")
        load = lambda name: json.loads((snapshot / name).read_text(encoding="utf-8"))
        folder = Path(self.temporary.name) / "declared" / "es"
        folder.mkdir(parents=True)
        (folder / "glosses.json").write_text(json.dumps({
            "schema": "declared-entries/v1", "language": "es", "entries": [{
                "entry_id": "es-gloss-bum", "kind": "gloss", "surface": "bum",
                "payload": {"senses": [{"translation": "boom", "pos": "interjection"}]},
                "reason": "onomatopoeia; SpanishDict answers in English",
                "author": "test", "created_at": "2026-09-23"}]}))
        source = SpanishDictHeadwordSource(
            SpanishDictLemmaRule(load("conjugation_reverse.json"),
                                 known_headwords=frozenset(load("headword_cache.json"))),
            load("surface_cache.json"), load("headword_cache.json"))
        self.resolver = Resolver(
            source, DeclaredRegistry.load(Path(self.temporary.name) / "declared", "es"),
            Context(language="es", mode="speech"),
            ModePolicy.load(REPO / "config/surfaces/strategy.json", "speech"))
        self.cards = [{**create_card_record("es", s).to_dict(), "rank": i + 1}
                      for i, s in enumerate(SURFACES)]

    def tearDown(self):
        self.temporary.cleanup()

    def build(self, surfaces=frozenset()):
        adapter = SpanishDictSenseMenuAdapter(
            self.snapshot, language_policy=self.policy,
            resolver=self.resolver if surfaces else None, resolver_surfaces=frozenset(surfaces))
        return adapter.build(self.cards, snapshot_id="fixture-2026-08")

    def test_cards_outside_the_resolved_set_are_byte_identical(self):
        legacy, legacy_report = self.build()
        resolved, resolved_report = self.build({"sr", "estate", "bum"})
        for before, after in zip(legacy["cards"], resolved["cards"]):
            if before["surface_form"] not in {"sr", "estate", "bum"}:
                self.assertEqual(json.dumps(before, sort_keys=True), json.dumps(after, sort_keys=True))
        others = lambda report: [r for r in report["per_surface"] if r["surface_form"] in {"está", "usted", "cura"}]
        self.assertEqual(others(legacy_report), others(resolved_report))

    def test_the_legacy_path_left_these_three_empty(self):
        legacy, _ = self.build()
        empty = {c["surface_form"] for c in legacy["cards"] if not c["analyses"]}
        self.assertEqual(empty, {"sr", "estate", "bum"})

    def test_a_dotted_self_headword_is_the_menu(self):
        menu, report = self.build({"sr"})
        card = next(c for c in menu["cards"] if c["surface_form"] == "sr")
        self.assertEqual([a["headword"] for a in card["analyses"]], ["Sr."])
        stamp = card["analyses"][0]["provider_metadata"]["resolver"]
        self.assertEqual((stamp["strategy"], stamp["headword_provenance"], stamp["headword_trust"]),
                         ("headwords", "spanishdict-page-self", "provider"))
        row = next(r for r in report["per_surface"] if r["surface_form"] == "sr")
        self.assertEqual((row["status"], row["strategy"], row["coverage"]), ("ready", "headwords", "menu"))

    def test_an_enclitic_surface_borrows_its_verbs_entry(self):
        menu, _ = self.build({"estate"})
        card = next(c for c in menu["cards"] if c["surface_form"] == "estate")
        self.assertEqual({a["headword"] for a in card["analyses"]}, {"estar"})
        self.assertEqual({t["translation"] for a in card["analyses"] for t in a["senses"]},
                         {"to be", "to stay"})
        stamp = card["analyses"][0]["provider_metadata"]["resolver"]
        self.assertEqual(stamp["headword_trust"], "derived")
        self.assertIn("estate = esta + te", stamp["headword_detail"])

    def test_a_declared_gloss_names_its_own_adapter(self):
        menu, report = self.build({"bum"})
        card = next(c for c in menu["cards"] if c["surface_form"] == "bum")
        self.assertEqual([a["source_adapter"] for a in card["analyses"]], [DECLARED_GLOSS_ADAPTER])
        self.assertEqual(card["analyses"][0]["senses"][0]["translation"], "boom")
        self.assertEqual(card["resolution"]["entry"]["entry_id"], "es-gloss-bum")


if __name__ == "__main__":
    unittest.main()
