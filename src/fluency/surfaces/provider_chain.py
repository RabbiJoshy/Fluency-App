"""Several headword sources read in a fixed order, as one ``HeadwordSource``.

Lyrics v20 (proposal 0004, 2026-09-27) resolves Spanish against SpanishDict
first and Wiktionary second. The order is a provider precedence, not a new
strategy: the resolver's own precedence (override, provider headwords,
expansion, gloss, entity, ``no_menu``) is unchanged and applied once, with
"provider headwords" meaning the first source in the chain that names a
headword it holds an entry for. So a declared gloss never outranks a
Wiktionary entry, and an expansion (``ta`` -> ``está``) resolves its target
through the same chain.

Each source answers whole or not at all: a surface's headwords all come from
one provider (``named_by``). Each headword's entry is read from the earliest
provider holding it (``answered_by`` lists them), by that provider's adapter. What every source said is kept in the notes, including
headwords a source named but holds no entry for (``despejás`` -> *despejar* in
SpanishDict's conjugation table, with no SpanishDict entry for *despejar*),
because that is the fetch queue.
"""

from __future__ import annotations

from typing import Any, Sequence

from fluency.surfaces.resolver import (
    ABSENT, FETCHED_CACHE, MENU, UNFETCHED, HeadwordSource, ProviderDeclaration,
)


class ProviderChain:
    """``HeadwordSource`` over ``sources``, earliest first."""

    def __init__(self, sources: Sequence[HeadwordSource]) -> None:
        if not sources:
            raise ValueError("a provider chain needs at least one source")
        self.sources = tuple(sources)
        self.provider = "+".join(source.provider for source in self.sources)
        self.coverage_kind = "chain"
        # (surface, headword) -> provider, for every answer given.
        self.answered: dict[tuple[str, str], str] = {}

    def source(self, provider: str) -> HeadwordSource:
        for source in self.sources:
            if source.provider == provider:
                return source
        raise KeyError(provider)

    def declare(self, surface: str) -> ProviderDeclaration:
        said: dict[str, Any] = {}
        named: list[tuple[str, ProviderDeclaration]] = []
        for source in self.sources:
            declaration = source.declare(surface)
            held = tuple(h for h in declaration.headwords if source.has_entry(h.headword, surface))
            said[source.provider] = {
                "coverage": declaration.coverage,
                "headwords": [h.headword for h in declaration.headwords],
                "headwords_without_entry": [h.headword for h in declaration.headwords if h not in held],
                **dict(declaration.notes),
            }
            if held:
                # Each headword is read from the earliest provider holding it:
                # a lemma Wiktionary names (maldades -> maldad) is read from
                # SpanishDict when SpanishDict holds it, so a lyric card shows
                # the same entry as the speech card for that lemma.
                readers = []
                for h in held:
                    reader = next(s.provider for s in self.sources if s.has_entry(h.headword, surface))
                    self.answered[(surface, h.headword)] = reader
                    if reader not in readers:
                        readers.append(reader)
                return ProviderDeclaration(surface, held, MENU,
                                           {"answered_by": "+".join(readers), "named_by": source.provider,
                                            "providers": said})
            if declaration.headwords:
                named.append((source.provider, declaration))
        # No source holds an entry for a headword it named itself. A headword
        # one provider names may still be held by another: SpanishDict's
        # conjugation table says despejás is a form of despejar, and only
        # Wiktionary holds despejar. The statement keeps its provenance; the
        # entry is read from whoever holds it.
        for provider, declaration in named:
            crossed = []
            for h in declaration.headwords:
                holder = next((s.provider for s in self.sources if s.has_entry(h.headword, surface)), None)
                if holder is not None:
                    self.answered[(surface, h.headword)] = holder
                    crossed.append(h)
            if crossed:
                return ProviderDeclaration(surface, tuple(crossed), MENU, {
                    "answered_by": self.answered[(surface, crossed[0].headword)],
                    "named_by": provider, "providers": said})
        # Nobody holds an entry. Hand the resolver the first headwords anyone
        # named, so it can say "headword_not_in_snapshot" rather than "absent".
        coverage = ABSENT
        for source in self.sources:
            if (source.coverage_kind == FETCHED_CACHE
                    and said[source.provider]["coverage"] == UNFETCHED):
                coverage = UNFETCHED  # asking that provider could still answer
        return ProviderDeclaration(surface, named[0][1].headwords if named else (), coverage,
                                   {"answered_by": None, "providers": said})

    def has_entry(self, headword: str, surface: str | None = None) -> bool:
        return any(source.has_entry(headword, surface) for source in self.sources)

    def provider_for(self, surface: str, headword: str) -> str:
        """Which source a resolved headword's menu is read from.

        A headword a provider declared is read from that provider. An override
        names headwords directly, so it is read from the first source that
        holds the entry.
        """
        found = self.answered.get((surface, headword))
        if found:
            return found
        for source in self.sources:
            if source.has_entry(headword, surface):
                return source.provider
        raise KeyError(f"no source holds {headword!r} for {surface!r}")


class FixedResolutions:
    """A resolver whose answers were already decided, for an adapter to build from.

    The sense-menu adapters take a resolver and a set of surfaces to build from
    it. Handing them the chain's answers, rather than a resolver over their own
    provider alone, keeps the precedence decided once, by the chain.
    """

    def __init__(self, source: Any, resolutions: dict[str, Any], own_provenance_prefix: str = "") -> None:
        self.source = source
        self.resolutions = resolutions
        self.own_provenance_prefix = own_provenance_prefix

    def resolve(self, surface: str) -> Any:
        return self.resolutions[surface]

    def declared_headwords(self, surface: str) -> list[str]:
        """Headwords the adapter's own lookup would not reach, so it must fetch them.

        An override's, and any a different provider stated (``external``).
        Headwords the adapter's provider reached itself are left to its own
        paths, which also carry the part-of-speech limits of a form-of chain.
        """
        found = self.resolutions.get(surface)
        if found is None:
            return []
        own = self.own_provenance_prefix
        return [h.headword for h in found.headwords
                if h.provenance == "override" or not (own and h.provenance.startswith(own))]

    def expansion_target(self, surface: str) -> str:
        found = self.resolutions.get(surface)
        return found.expanded_to if found is not None else ""
