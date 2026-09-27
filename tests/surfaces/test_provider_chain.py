"""Lyrics v20: one resolver over SpanishDict then Wiktionary, and elisions first in lyrics."""

import unittest

from fluency.surfaces import trust
from fluency.surfaces.provider_chain import FixedResolutions, ProviderChain
from fluency.surfaces.resolver import (
    ABSENT, EXPANSION, HEADWORDS, MENU, NO_MENU, UNFETCHED, Headword, ModePolicy,
    ProviderDeclaration, Resolver,
)
from fluency.surfaces.declared import Context
from tests.surfaces.test_declared_and_resolver import entry, registry


class Source:
    def __init__(self, provider, coverage_kind, declared=None, entries=(), unfetched=()):
        self.provider, self.coverage_kind = provider, coverage_kind
        self.declared, self.entries, self.unfetched = declared or {}, set(entries), set(unfetched)

    def declare(self, surface):
        heads = tuple(Headword(h, f"{self.provider}-{rel}", trust.PROVIDER, "", rel)
                      for h, rel in self.declared.get(surface, ()))
        coverage = MENU if heads else (UNFETCHED if surface in self.unfetched else ABSENT)
        return ProviderDeclaration(surface, heads, coverage)

    def has_entry(self, headword, surface=None):
        return headword in self.entries


def sd(**kw):
    return Source("spanishdict", "fetched_cache", **kw)


def wikt(**kw):
    return Source("wiktionary", "complete_dump", **kw)


LYRICS = Context(language="es", mode="lyrics", artist="bad-bunny")


def resolver(chain, reg, *, expansion_first=True):
    return Resolver(chain, reg, LYRICS, ModePolicy("lyrics", trust.DERIVED, True, expansion_first))


class ProviderChainTests(unittest.TestCase):
    def test_the_first_provider_holding_an_entry_answers(self):
        chain = ProviderChain([sd(declared={"muerdo": [("muerdo", "self"), ("morder", "form")]},
                                  entries={"muerdo", "morder"}),
                               wikt(declared={"muerdo": [("morder", "form")]}, entries={"morder"})])
        found = resolver(chain, registry()).resolve("muerdo")
        self.assertEqual(found.headword_names, ["muerdo", "morder"])
        self.assertEqual(chain.provider_for("muerdo", "morder"), "spanishdict")

    def test_wiktionary_answers_when_spanishdict_holds_nothing(self):
        chain = ProviderChain([sd(unfetched={"bichote"}),
                               wikt(declared={"bichote": [("bichote", "self")]}, entries={"bichote"})])
        found = resolver(chain, registry()).resolve("bichote")
        self.assertEqual((found.strategy, found.notes["answered_by"]), (HEADWORDS, "wiktionary"))

    def test_a_headword_one_provider_names_is_read_from_the_one_that_holds_it(self):
        chain = ProviderChain([sd(declared={"despejás": [("despejar", "form")]}),
                               wikt(entries={"despejar"})])
        found = resolver(chain, registry()).resolve("despejás")
        self.assertEqual(found.headword_names, ["despejar"])
        self.assertEqual(found.headwords[0].provenance, "spanishdict-form")
        self.assertEqual((found.notes["named_by"], chain.provider_for("despejás", "despejar")),
                         ("spanishdict", "wiktionary"))

    def test_a_lemma_wiktionary_names_is_read_from_spanishdict_when_it_holds_it(self):
        chain = ProviderChain([sd(unfetched={"maldades"}, entries={"maldad"}),
                               wikt(declared={"maldades": [("maldad", "form")]}, entries={"maldad"})])
        found = resolver(chain, registry()).resolve("maldades")
        self.assertEqual((found.notes["named_by"], found.notes["answered_by"]), ("wiktionary", "spanishdict"))
        self.assertEqual(found.headwords[0].provenance, "wiktionary-form")

    def test_each_headword_is_read_from_the_earliest_provider_holding_it(self):
        chain = ProviderChain([sd(unfetched={"flores"}, entries={"flor"}),
                               wikt(declared={"flores": [("flor", "form"), ("florar", "form")]},
                                    entries={"flor", "florar"})])
        found = resolver(chain, registry()).resolve("flores")
        self.assertEqual(found.notes["answered_by"], "spanishdict+wiktionary")
        self.assertEqual([chain.provider_for("flores", h) for h in ("flor", "florar")],
                         ["spanishdict", "wiktionary"])

    def test_a_declared_gloss_never_outranks_a_wiktionary_entry(self):
        reg = registry(entry("g", "gloss", "perreo", {"senses": [{"translation": "grinding"}]}))
        chain = ProviderChain([sd(unfetched={"perreo"}),
                               wikt(declared={"perreo": [("perreo", "self")]}, entries={"perreo"})])
        self.assertEqual(resolver(chain, reg).resolve("perreo").strategy, HEADWORDS)

    def test_nobody_answering_is_unfetched_while_a_fetch_could_still_help(self):
        chain = ProviderChain([sd(unfetched={"xq"}), wikt()])
        found = resolver(chain, registry()).resolve("xq")
        self.assertEqual((found.strategy, found.reason), (NO_MENU, "unfetched"))
        self.assertEqual(found.notes["providers"]["wiktionary"]["coverage"], ABSENT)


class ExpansionFirstTests(unittest.TestCase):
    ELISION = entry("ta", "expansion", "ta", {"expands_to": "está", "class": "abbreviation"},
                    scope={"mode": "lyrics"})

    def chain(self):
        return ProviderChain([sd(declared={"ta": [("TA", "self")], "está": [("está", "self"), ("estar", "form")]},
                                 entries={"TA", "está", "estar"}), wikt()])

    def test_in_lyrics_an_elision_replaces_the_page_for_the_bare_letters(self):
        found = resolver(self.chain(), registry(self.ELISION)).resolve("ta")
        self.assertEqual((found.strategy, found.expanded_to), (EXPANSION, "está"))
        self.assertEqual(found.headword_names, ["está", "estar"])
        self.assertEqual(found.notes["provider_headwords_replaced"], ["TA"])

    def test_without_the_policy_the_provider_page_still_wins(self):
        found = resolver(self.chain(), registry(self.ELISION), expansion_first=False).resolve("ta")
        self.assertEqual(found.headword_names, ["TA"])

    def test_the_repository_policy_turns_it_on_for_lyrics_only(self):
        from pathlib import Path
        path = Path(__file__).resolve().parents[2] / "config/surfaces/strategy.json"
        self.assertTrue(ModePolicy.load(path, "lyrics").expansion_first)
        self.assertFalse(ModePolicy.load(path, "speech").expansion_first)


class FixedResolutionsTests(unittest.TestCase):
    def test_an_adapter_is_told_to_fetch_only_headwords_its_own_paths_miss(self):
        chain = ProviderChain([sd(declared={"despejás": [("despejar", "form")]}), wikt(entries={"despejar"})])
        found = resolver(chain, registry()).resolve("despejás")
        fixed = FixedResolutions(chain, {"despejás": found}, own_provenance_prefix="wiktionary")
        self.assertEqual(fixed.declared_headwords("despejás"), ["despejar"])
        own = FixedResolutions(chain, {"despejás": found}, own_provenance_prefix="spanishdict")
        self.assertEqual(own.declared_headwords("despejás"), [])


if __name__ == "__main__":
    unittest.main()
