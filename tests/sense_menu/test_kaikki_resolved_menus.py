"""Provider parity: Wiktionary (Kaikki) resolves headword sets the same way SpanishDict does."""

import json
import tempfile
import unittest
from pathlib import Path

from fluency.core.identity import create_card_record
from fluency.sense_menu.config import load_sense_menu_language_policy
from fluency.sense_menu.declared_menu import DECLARED_ENTITY_ADAPTER, DECLARED_GLOSS_ADAPTER
from fluency.sense_menu.kaikki import KaikkiHeadwordSource, KaikkiSenseMenuAdapter
from fluency.surfaces.declared import Context, DeclaredRegistry
from fluency.surfaces.resolver import ModePolicy, Resolver

REPO = Path(__file__).resolve().parents[2]
ROWS = [
    {"word": "être", "lang_code": "fr", "pos": "verb",
     "senses": [{"id": "en-etre-verb-be", "glosses": ["to be"]}]},
    {"word": "est", "lang_code": "fr", "pos": "verb",
     "senses": [{"id": "en-est-form", "glosses": ["inflection of être"],
                 "tags": ["form-of"], "form_of": [{"word": "être"}]}]},
    {"word": "dame", "lang_code": "fr", "pos": "noun",
     "senses": [{"id": "en-dame-lady", "glosses": ["lady"]}]},
]
SURFACES = ("être", "est", "dame", "bof", "peugeot", "estes")


def entry(entry_id, kind, surface, payload):
    return {"entry_id": entry_id, "kind": kind, "surface": surface, "payload": payload,
            "reason": "test", "author": "test", "created_at": "2026-09-23"}


class KaikkiResolvedMenuTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        root = Path(self.temporary.name)
        self.snapshot = root / "kaikki.jsonl"
        self.snapshot.write_text("\n".join(json.dumps(r, ensure_ascii=False) for r in ROWS), encoding="utf-8")
        folder = root / "declared" / "fr"
        folder.mkdir(parents=True)
        (folder / "test.json").write_text(json.dumps({
            "schema": "declared-entries/v1", "language": "fr", "entries": [
                entry("fr-gloss-bof", "gloss", "bof", {"class": "interjection",
                      "senses": [{"translation": "meh", "pos": "interjection"}]}),
                entry("fr-entity-peugeot", "entity", "peugeot", {
                      "name": "Peugeot", "entity_type": "brand", "description": "French car maker"}),
                entry("fr-headwords-estes", "headwords", "estes", {"headwords": ["être"]}),
            ]}), encoding="utf-8")
        self.registry = DeclaredRegistry.load(root / "declared", "fr")
        self.policy = load_sense_menu_language_policy(REPO, policy_id="fr-v1", language="fr")
        self.cards = [create_card_record("fr", s).to_dict() for s in SURFACES]

    def tearDown(self):
        self.temporary.cleanup()

    def build(self, surfaces=frozenset()):
        adapter = KaikkiSenseMenuAdapter(self.snapshot, language_code="fr", language_policy=self.policy)
        if surfaces:
            adapter.resolver = Resolver(
                KaikkiHeadwordSource(), self.registry, Context(language="fr", mode="speech"),
                ModePolicy.load(REPO / "config/surfaces/strategy.json", "speech"))
            adapter.resolver_surfaces = frozenset(surfaces)
        menu, report = adapter.build(self.cards, snapshot_id="fixture")
        return {c["surface_form"]: c for c in menu["cards"]}, report

    def test_unresolved_cards_are_byte_identical(self):
        legacy, _ = self.build()
        resolved, _ = self.build({"est", "bof", "peugeot", "estes"})
        for surface in ("être", "dame"):
            self.assertEqual(json.dumps(legacy[surface], sort_keys=True),
                             json.dumps(resolved[surface], sort_keys=True))

    def test_a_form_of_chain_is_a_provider_statement(self):
        resolved, _ = self.build({"est"})
        card = resolved["est"]
        self.assertEqual({a["headword"] for a in card["analyses"]}, {"être"})
        self.assertEqual(card["resolution"]["word_class"], "inflection")
        heads = card["resolution"]["headwords"]
        self.assertEqual([(h["headword"], h["provenance"], h["trust"]) for h in heads],
                         [("être", "wiktionary-form-of", "provider")])

    def test_declared_entries_fill_what_wiktionary_does_not_have(self):
        legacy, _ = self.build()
        self.assertEqual([legacy[s]["analyses"] for s in ("bof", "peugeot", "estes")], [[], [], []])
        resolved, report = self.build({"bof", "peugeot", "estes"})
        self.assertEqual([a["source_adapter"] for a in resolved["bof"]["analyses"]], [DECLARED_GLOSS_ADAPTER])
        self.assertEqual([a["source_adapter"] for a in resolved["peugeot"]["analyses"]], [DECLARED_ENTITY_ADAPTER])
        self.assertEqual(resolved["peugeot"]["analyses"][0]["senses"][0]["definition"], "French car maker")
        # An override's headword is read from the dump even though no path reached it.
        self.assertEqual({a["headword"] for a in resolved["estes"]["analyses"]}, {"être"})
        classes = {r["surface_form"]: r.get("strategy") for r in report["per_surface"]}
        self.assertEqual((classes["bof"], classes["peugeot"], classes["estes"]),
                         ("declared_gloss", "entity", "headwords"))


if __name__ == "__main__":
    unittest.main()
