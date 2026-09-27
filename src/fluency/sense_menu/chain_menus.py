"""Closed menus for a set of surfaces from a provider chain, built by the stage-02 adapters.

Lyrics v20 (proposal 0004): every card's headword set comes from
``fluency.surfaces.resolver`` over SpanishDict then Wiktionary
(``fluency.surfaces.provider_chain``), with declared entries at the consumer's
scope. The menu is then built from those headwords' entries by the adapter of
the provider that holds them -- ``SpanishDictSenseMenuAdapter`` and
``KaikkiSenseMenuAdapter``, the same code speech's stage 02 runs. Nothing here
reads a dictionary itself, so a fix to either adapter reaches lyrics
(Invariant 4).

Wiktionary parity follows from using the Kaikki adapter: a form-of gloss
("first-person singular present indicative of morder") is never a sense; the
adapter follows the form-of chain to *morder* and builds its senses.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Any, Iterable

from fluency.languages.surfaces import normalizer_for_language
from fluency.sense_menu.config import load_sense_menu_language_policy
from fluency.sense_menu.kaikki import KaikkiHeadwordSource, KaikkiSenseMenuAdapter
from fluency.sense_menu.spanishdict import SpanishDictSenseMenuAdapter
from fluency.sense_menu.spanishdict_lemmas import SpanishDictHeadwordSource, SpanishDictLemmaRule
from fluency.surfaces.declared import Context, DeclaredRegistry
from fluency.surfaces.provider_chain import FixedResolutions, ProviderChain
from fluency.surfaces.resolver import (
    DECLARED_GLOSS, ENTITY, EXPANSION, HEADWORDS, ModePolicy, Resolution, Resolver,
)


@dataclass(frozen=True)
class ChainMenu:
    surface: str
    resolution: Resolution
    provider: str | None          # whose entries the menu was read from ("a+b" when both); None when declared or empty
    analyses: tuple[dict[str, Any], ...]


def _cards(surfaces: Iterable[str]) -> list[dict[str, Any]]:
    return [{"card_id": f"s{index:06d}", "surface_key": surface}
            for index, surface in enumerate(sorted(set(surfaces)))]


def build_chain_menus(
    repository_root: Path,
    surfaces: Iterable[str],
    *,
    spanishdict_snapshot: Path,
    kaikki_snapshot: Path,
    registry: DeclaredRegistry,
    context: Context,
    policy: ModePolicy,
    spanishdict_policy_id: str = "es-spanishdict-v1",
    wiktionary_policy_id: str = "es-wiktionary-v1",
) -> tuple[dict[str, ChainMenu], dict[str, Any]]:
    """Resolve and build a menu for every surface. Returns menus and provenance to pin."""
    language = context.language
    normalize = normalizer_for_language(language)
    surfaces = {normalize(s) for s in surfaces if s and normalize(s)}

    sd = SpanishDictSenseMenuAdapter(
        spanishdict_snapshot,
        language_policy=load_sense_menu_language_policy(
            repository_root, policy_id=spanishdict_policy_id, language=language))
    reverse = json.loads((sd.path / "conjugation_reverse.json").read_text(encoding="utf-8"))
    sd_source = SpanishDictHeadwordSource(
        SpanishDictLemmaRule(reverse, known_headwords=frozenset(sd.headword_cache)),
        sd.surface_cache, sd.headword_cache)

    kk = KaikkiSenseMenuAdapter(
        kaikki_snapshot, language_code=language,
        language_policy=load_sense_menu_language_policy(
            repository_root, policy_id=wiktionary_policy_id, language=language))
    kk_source = KaikkiHeadwordSource()

    # Wiktionary is read in passes over the dump, so everything the chain may
    # ask it about is named up front: the surfaces, expansion targets, override
    # headwords, and every headword SpanishDict names (it may hold no entry
    # for one that Wiktionary does).
    probe = Resolver(sd_source, registry, context, policy)
    targets = {probe.expansion_target(s) for s in surfaces} - {""}
    overrides = {h for s in surfaces | targets for h in probe.declared_headwords(s)}
    named = {h.headword for s in surfaces | targets for h in sd_source.declare(s).headwords}
    scan = {normalize(s) or s for s in surfaces | targets | overrides | named}
    kk.resolver = Resolver(kk_source, registry, context, policy)  # binds kk_source to the scan
    kk.resolver_surfaces = frozenset()
    kk.build(_cards(scan), snapshot_id="scan")

    chain = ProviderChain([sd_source, kk_source])
    resolver = Resolver(chain, registry, context, policy)
    resolutions = {s: resolver.resolve(s) for s in surfaces}

    # Which provider each headword's entry is read from. A card may be read
    # from both (flores: SpanishDict's flor, Wiktionary's florar).
    by_reader: dict[str, dict[str, Resolution]] = {"spanishdict": {}, "wiktionary": {}}
    readers_of: dict[str, list[str]] = {}
    for surface, found in resolutions.items():
        if found.strategy in (HEADWORDS, EXPANSION):
            page = found.expanded_to or surface
            split: dict[str, list] = {}
            for h in found.headwords:
                split.setdefault(chain.provider_for(page, h.headword), []).append(h)
            for reader, heads in split.items():
                by_reader[reader][surface] = replace(found, headwords=tuple(heads))
            readers_of[surface] = list(split)
        elif found.strategy in (DECLARED_GLOSS, ENTITY):
            by_reader["spanishdict"][surface] = found  # either adapter builds a declared menu
            readers_of[surface] = []
        else:
            readers_of[surface] = []

    built: dict[str, list[dict[str, Any]]] = {s: [] for s in surfaces}
    for reader, adapter in (("spanishdict", sd), ("wiktionary", kk)):
        group = by_reader[reader]
        if not group:
            continue
        adapter.resolver = FixedResolutions(chain, group, own_provenance_prefix=reader)
        adapter.resolver_surfaces = frozenset(group)
        snapshot_id = sd.snapshot_id if adapter is sd else "lyrics-chain"
        menu, _report = adapter.build(_cards(group), snapshot_id=snapshot_id)
        for card in menu["cards"]:
            built[card["surface_form"]].extend(card["analyses"])

    menus = {
        s: ChainMenu(s, resolutions[s], "+".join(readers_of[s]) or None, tuple(built[s]))
        for s in surfaces
    }
    pinned = {
        "spanishdict_snapshot_id": sd.snapshot_id,
        "spanishdict_snapshot_content_id": sd.snapshot_content_id,
        "wiktionary_snapshot_content_id": kk.snapshot_content_id,
        "spanishdict_policy_id": spanishdict_policy_id,
        "wiktionary_policy_id": wiktionary_policy_id,
        "chain": chain.provider,
    }
    return menus, pinned
