"""One offline resolver: which dictionary entries a surface's meanings come from.

Proposal 0003, settled 2026-09-23. The load-bearing fact about a surface is its
**headword set**: the dictionary entries its menu is built from. It used to be a
side effect inside each sense-menu adapter -- unrecorded, without provenance,
impossible to override. Here it is decided first, from recorded facts, and the
menu is built from it.

Strategies, in a fixed precedence (never implicit):

1. ``headwords`` from a hand-written override (curated). It replaces the set.
2. ``headwords`` the provider declares for the exact surface (provider trust),
   or our deterministic rules reach from provider data (derived), filtered by
   the consumer's minimum trust.
3. Only if the set is still empty, the declared fallbacks:
   ``expansion`` (borrow another surface's set: ``ud`` -> ``usted``), then
   ``declared_gloss`` (no entry exists; a hand-written meaning), then
   ``entity`` (a name; on or off per mode).
4. ``no_menu``, declared, with the reason: ``absent`` (the provider was asked
   and has no entry), ``unfetched`` (never asked), or ``entity_not_in_mode``.

Every answer records the strategy, each headword's provenance and trust, and the
declared entry used, so a later change of answer is traceable. Nothing here
calls the network: providers are read from local snapshots, and a fetch is only
ever a background upgrade that arrives as provider data on the next build.

Provider-agnostic (Invariant 4): a provider plugs in as a ``HeadwordSource``.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Mapping, Protocol, runtime_checkable

from fluency.surfaces import trust
from fluency.surfaces.declared import Context, DeclaredEntry, DeclaredRegistry

RESOLVER_VERSION = "surface-resolver/v1"

HEADWORDS = "headwords"
EXPANSION = "expansion"
DECLARED_GLOSS = "declared_gloss"
ENTITY = "entity"
NO_MENU = "no_menu"

MENU = "menu"
ABSENT = "absent"
UNFETCHED = "unfetched"

COMPLETE_DUMP = "complete_dump"   # not in the dump means absent (Kaikki)
FETCHED_CACHE = "fetched_cache"   # not in the cache means unfetched (SpanishDict)


class ResolverError(ValueError):
    pass


@dataclass(frozen=True)
class Headword:
    headword: str
    provenance: str
    trust: str
    detail: str = ""

    def to_dict(self) -> dict[str, str]:
        return {"headword": self.headword, "provenance": self.provenance,
                "trust": self.trust, "detail": self.detail}


@dataclass(frozen=True)
class ProviderDeclaration:
    """What one provider says about one surface, before any policy."""

    surface: str
    headwords: tuple[Headword, ...] = ()
    coverage: str = UNFETCHED  # menu | absent | unfetched
    notes: Mapping[str, Any] = field(default_factory=dict)


@runtime_checkable
class HeadwordSource(Protocol):
    provider: str
    coverage_kind: str

    def declare(self, surface: str) -> ProviderDeclaration: ...

    def has_entry(self, headword: str, surface: str | None = None) -> bool: ...


@dataclass(frozen=True)
class ModePolicy:
    mode: str
    minimum_trust: str
    entity: bool

    @classmethod
    def load(cls, path: Path, mode: str) -> "ModePolicy":
        document = json.loads(Path(path).read_text(encoding="utf-8"))
        if document.get("schema") != "surface-strategy-policy/v1":
            raise ResolverError(f"{path}: expected surface-strategy-policy/v1")
        declared = (document.get("modes") or {}).get(mode)
        if not isinstance(declared, dict):
            raise ResolverError(f"{path}: no policy for mode {mode!r}")
        return cls(mode, trust.check(str(declared["minimum_trust"])), bool(declared.get("entity")))


@dataclass(frozen=True)
class Resolution:
    surface: str
    strategy: str
    headwords: tuple[Headword, ...] = ()
    entry: DeclaredEntry | None = None
    coverage: str = UNFETCHED
    reason: str = ""
    expanded_to: str = ""
    provider: str = ""
    notes: Mapping[str, Any] = field(default_factory=dict)
    resolver_version: str = RESOLVER_VERSION

    @property
    def headword_names(self) -> list[str]:
        return [item.headword for item in self.headwords]

    def stamp(self) -> dict[str, Any]:
        """What every menu analysis built from this answer carries."""
        return {
            "resolver_version": self.resolver_version,
            "strategy": self.strategy,
            "provider": self.provider,
            "coverage": self.coverage,
            "entry_id": self.entry.entry_id if self.entry else None,
            "expanded_to": self.expanded_to or None,
        }

    def to_dict(self) -> dict[str, Any]:
        return {
            **self.stamp(),
            "surface": self.surface,
            "reason": self.reason,
            "headwords": [item.to_dict() for item in self.headwords],
            "entry": self.entry.to_dict() if self.entry else None,
            "notes": dict(self.notes),
        }


class Resolver:
    """Resolve surfaces for one consumer context against one provider."""

    def __init__(self, source: HeadwordSource, registry: DeclaredRegistry,
                 context: Context, policy: ModePolicy) -> None:
        if context.mode != policy.mode:
            raise ResolverError(f"context mode {context.mode!r} does not match policy {policy.mode!r}")
        self.source = source
        self.registry = registry
        self.context = context
        self.policy = policy

    def _select(self, surface: str, kind: str) -> DeclaredEntry | None:
        return self.registry.select(surface, kind, self.context, self.policy.minimum_trust)

    def resolve(self, surface: str, *, _expanding: bool = False) -> Resolution:
        declaration = self.source.declare(surface)
        base = dict(surface=surface, coverage=declaration.coverage,
                    provider=self.source.provider, notes=declaration.notes)

        override = self._select(surface, "headwords")
        if override is not None:
            missing = [h for h in override.headwords if not self.source.has_entry(h, surface)]
            if missing:
                raise ResolverError(
                    f"{override.entry_id}: {surface!r} names headwords {self.source.provider} "
                    f"has no entry for: {', '.join(missing)}")
            heads = tuple(Headword(h, "override", override.trust, override.reason)
                          for h in override.headwords)
            return Resolution(strategy=HEADWORDS, headwords=heads, entry=override, **base)

        accepted = tuple(h for h in declaration.headwords
                         if trust.accepts(self.policy.minimum_trust, h.trust))
        if accepted:
            return Resolution(strategy=HEADWORDS, headwords=accepted, **base)

        expansion = self._select(surface, "expansion")
        if expansion is not None and not _expanding:
            target = self.resolve(expansion.expands_to, _expanding=True)
            if target.strategy == HEADWORDS:
                return Resolution(strategy=EXPANSION, headwords=target.headwords, entry=expansion,
                                  expanded_to=expansion.expands_to, **base)

        gloss = self._select(surface, "gloss")
        if gloss is not None:
            return Resolution(strategy=DECLARED_GLOSS, entry=gloss, **base)

        entity = self._select(surface, "entity")
        if entity is not None:
            if self.policy.entity:
                return Resolution(strategy=ENTITY, entry=entity, **base)
            return Resolution(strategy=NO_MENU, entry=entity, reason="entity_not_in_mode", **base)

        if declaration.headwords:
            reason = "below_minimum_trust"
        else:
            reason = declaration.coverage if declaration.coverage in (ABSENT, UNFETCHED) else ABSENT
        return Resolution(strategy=NO_MENU, reason=reason, **base)
