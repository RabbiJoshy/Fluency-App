"""The headword set is decided first, from recorded facts, and the menu follows.

Surfaces are from the 105 empty-meanings cards of es-speech-v15-10000x10.
"""

import json
import tempfile
import unittest
from pathlib import Path

from fluency.surfaces import trust
from fluency.surfaces.declared import Context, DeclaredError, DeclaredRegistry
from fluency.surfaces.resolver import (
    ABSENT, DECLARED_GLOSS, ENTITY, EXPANSION, HEADWORDS, MENU, NO_MENU, UNFETCHED,
    Headword, ModePolicy, ProviderDeclaration, Resolver, ResolverError,
)

REPO = Path(__file__).resolve().parents[2]
SPEECH = Context(language="es", mode="speech")


def entry(entry_id, kind, surface, payload, **extra):
    return {"entry_id": entry_id, "kind": kind, "surface": surface, "payload": payload,
            "reason": "test", "author": "test", "created_at": "2026-09-23", **extra}


def registry(*entries, language="es"):
    with tempfile.TemporaryDirectory() as tmp:
        folder = Path(tmp) / language
        folder.mkdir()
        (folder / "test.json").write_text(json.dumps(
            {"schema": "declared-entries/v1", "language": language, "entries": list(entries)}))
        return DeclaredRegistry.load(Path(tmp), language)


class FakeSource:
    provider = "fake"
    coverage_kind = "fetched_cache"

    def __init__(self, declared=None, entries=(), unfetched=()):
        self.declared = declared or {}
        self.entries = set(entries)
        self.unfetched = set(unfetched)

    def declare(self, surface):
        heads = tuple(Headword(h, p, t) for h, p, t in self.declared.get(surface, ()))
        coverage = MENU if heads else (UNFETCHED if surface in self.unfetched else ABSENT)
        return ProviderDeclaration(surface, heads, coverage)

    def has_entry(self, headword, surface=None):
        return headword in self.entries


def resolver(source, reg, mode="speech", **context):
    policy = ModePolicy.load(REPO / "config/surfaces/strategy.json", mode)
    return Resolver(source, reg, Context(language="es", mode=mode, **context), policy)


class DeclaredFormatTests(unittest.TestCase):
    def test_every_entry_needs_provenance(self) -> None:
        bad = entry("x", "gloss", "bum", {"senses": [{"translation": "boom"}]})
        del bad["author"]
        with self.assertRaises(DeclaredError):
            registry(bad)

    def test_two_entries_at_one_scope_are_an_error_not_a_precedence(self) -> None:
        with self.assertRaises(DeclaredError):
            registry(entry("a", "gloss", "uy", {"senses": [{"translation": "oops"}]}),
                     entry("b", "gloss", "uy", {"senses": [{"translation": "ouch"}]}))

    def test_the_narrowest_matching_scope_wins(self) -> None:
        reg = registry(
            entry("es", "gloss", "yeh", {"senses": [{"translation": "yeah"}]}),
            entry("bb", "gloss", "yeh", {"senses": [{"translation": "ad-lib"}]},
                  scope={"mode": "lyrics", "artist": "bad-bunny"}))
        lyrics = Context(language="es", mode="lyrics", artist="bad-bunny")
        self.assertEqual(reg.select("yeh", "gloss", lyrics, trust.DERIVED).entry_id, "bb")
        self.assertEqual(reg.select("yeh", "gloss", SPEECH, trust.DERIVED).entry_id, "es")

    def test_a_scope_that_does_not_match_is_invisible(self) -> None:
        reg = registry(entry("bb", "gloss", "yeh", {"senses": [{"translation": "ad-lib"}]},
                             scope={"mode": "lyrics"}))
        self.assertIsNone(reg.select("yeh", "gloss", SPEECH, trust.DERIVED))

    def test_a_consumer_does_not_see_entries_below_its_trust_floor(self) -> None:
        reg = registry(entry("h", "gloss", "brr", {"senses": [{"translation": "brr"}]},
                             trust="heuristic"))
        self.assertIsNone(reg.select("brr", "gloss", SPEECH, trust.DERIVED))
        self.assertIsNotNone(reg.select("brr", "gloss", Context("es", "live"), trust.HEURISTIC))

    def test_the_repository_declared_lists_load(self) -> None:
        DeclaredRegistry.load(REPO / "config/declared", "es")


class ResolverTests(unittest.TestCase):
    def test_provider_headwords_are_the_set(self) -> None:
        source = FakeSource({"condones": [("condonar", "page", "provider"), ("condón", "page", "provider")]})
        found = resolver(source, registry()).resolve("condones")
        self.assertEqual((found.strategy, found.headword_names), (HEADWORDS, ["condonar", "condón"]))

    def test_an_override_replaces_the_provider_set(self) -> None:
        source = FakeSource({"atrevo": [("atrezo", "page", "provider")]}, entries={"atreverse"})
        reg = registry(entry("o", "headwords", "atrevo", {"headwords": ["atreverse"]}))
        found = resolver(source, reg).resolve("atrevo")
        self.assertEqual(found.headword_names, ["atreverse"])
        self.assertEqual(found.headwords[0].trust, trust.CURATED)
        self.assertEqual(found.entry.entry_id, "o")

    def test_an_override_naming_no_real_entry_fails_loudly(self) -> None:
        reg = registry(entry("o", "headwords", "atrevo", {"headwords": ["atreverze"]}))
        with self.assertRaises(ResolverError):
            resolver(FakeSource(), reg).resolve("atrevo")

    def test_a_gloss_fills_only_an_empty_set(self) -> None:
        reg = registry(entry("g", "gloss", "bum", {"senses": [{"translation": "boom"}]}))
        self.assertEqual(resolver(FakeSource(), reg).resolve("bum").strategy, DECLARED_GLOSS)
        full = FakeSource({"bum": [("bum", "page", "provider")]})
        self.assertEqual(resolver(full, reg).resolve("bum").strategy, HEADWORDS)

    def test_an_expansion_borrows_the_target_set(self) -> None:
        source = FakeSource({"usted": [("usted", "page", "provider")]})
        reg = registry(entry("e", "expansion", "ud", {"expands_to": "usted"}))
        found = resolver(source, reg).resolve("ud")
        self.assertEqual((found.strategy, found.headword_names, found.expanded_to),
                         (EXPANSION, ["usted"], "usted"))

    def test_entities_are_off_in_speech_and_on_in_lyrics(self) -> None:
        reg = registry(entry("f", "entity", "ferrari",
                             {"name": "Ferrari", "entity_type": "brand", "description": "Italian sports-car maker"}))
        speech = resolver(FakeSource(), reg).resolve("ferrari")
        self.assertEqual((speech.strategy, speech.reason), (NO_MENU, "entity_not_in_mode"))
        self.assertEqual(resolver(FakeSource(), reg, mode="lyrics").resolve("ferrari").strategy, ENTITY)

    def test_absent_and_unfetched_are_declared_apart(self) -> None:
        source = FakeSource(unfetched={"borda"})
        self.assertEqual(resolver(source, registry()).resolve("borda").reason, UNFETCHED)
        self.assertEqual(resolver(source, registry()).resolve("tai").reason, ABSENT)

    def test_derived_headwords_are_refused_below_a_provider_floor(self) -> None:
        source = FakeSource({"quédatelo": [("quedar", "enclitic", "derived")]})
        strict = Resolver(source, registry(), SPEECH, ModePolicy("speech", trust.PROVIDER, False))
        found = strict.resolve("quédatelo")
        self.assertEqual((found.strategy, found.reason), (NO_MENU, "below_minimum_trust"))


if __name__ == "__main__":
    unittest.main()
