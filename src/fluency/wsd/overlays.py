"""Sense-menu overlays: an open data structure for candidate injection.

Provides a unified interface for injecting extra candidates into the closed
sense menu at WSD scoring time.

Beyond standard MWEs (idioms and locutions), this allows unlimited expansion
for:
  1. Slang / dialect-specific senses (e.g. Caribbean/Mexican/Rioplatense slang:
     "guagua" = bus, "vaina" = thing, "chabón" = guy).
  2. Conversational fillers / discourse markers (e.g. "o sea", "bueno", "vale",
     "tipo", "né", "ty vole").
  3. Domain-specific lexicons (e.g. lyrics, medical, legal, gaming).
  4. Custom curriculum overrides and user-defined candidate pairs.

Overlays join AFTER constraint filtering and BEFORE scoring, allowing them to
compete fairly against provider senses without corrupting single-word card
identities or deleting word-leaf evidence.
"""

from __future__ import annotations

from dataclasses import dataclass, field
import re
from typing import Any, Mapping, Protocol, Sequence, runtime_checkable

from fluency.wsd.menus import MenuAnalysis, SenseLeaf, build_analysis_id


OVERLAY_SOURCE_ADAPTER_PREFIX = "overlay"


@dataclass(frozen=True, slots=True)
class SenseOverlayEntry:
    """An external sense candidate eligible for injection into a sense menu.

    Attributes:
        entry_id: Unique canonical ID (e.g. "overlay:slang:caribbean:guagua").
        kind: Category ("multiword", "slang", "conversational_filler", "domain", "override").
        expression: Surface form or phrase trigger (e.g. "o sea", "guagua").
        translations: English meanings / glosses.
        part_of_speech: POS tag (e.g. "PHRASE", "SLANG", "FILLER", "NOUN").
        attach_words: Single-word card surfaces this candidate can attach to.
        domain_tags: Provenance or domain labels (e.g. ("caribbean", "puerto_rico")).
        corpus_frequency: Pre-attested occurrences in the corpus (tier 1 > 0, tier 2 == 0).
        metadata: Arbitrary provenance or syntactic hints.
    """

    entry_id: str
    kind: str
    expression: str
    translations: tuple[str, ...]
    part_of_speech: str = "PHRASE"
    attach_words: tuple[str, ...] = ()
    domain_tags: tuple[str, ...] = ()
    corpus_frequency: int = 0
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.entry_id:
            raise ValueError("SenseOverlayEntry requires entry_id")
        if not self.expression:
            raise ValueError("SenseOverlayEntry requires expression")
        if not self.translations:
            raise ValueError("SenseOverlayEntry requires at least one translation")

    def to_menu_analysis(self, card_id: str) -> MenuAnalysis:
        """Convert overlay entry into a synthetic MenuAnalysis for scoring."""
        adapter = f"{OVERLAY_SOURCE_ADAPTER_PREFIX}:{self.kind}/v1"
        analysis_id = build_analysis_id(
            card_id=card_id,
            source_adapter=adapter,
            source_analysis_key=self.expression.casefold(),
        )
        senses = tuple(
            SenseLeaf(
                sense_id=f"{self.entry_id}#{idx}",
                translation=trans,
                definition=trans,
                source_reference=self.kind,
                provider_metadata={
                    "domain_tags": list(self.domain_tags),
                    "corpus_frequency": self.corpus_frequency,
                    **dict(self.metadata),
                },
            )
            for idx, trans in enumerate(self.translations, start=1)
        )
        return MenuAnalysis(
            menu_analysis_id=analysis_id,
            card_id=card_id,
            surface_form=self.expression,
            headword=self.expression,
            part_of_speech=self.part_of_speech,
            source_adapter=adapter,
            source_analysis_key=self.expression.casefold(),
            senses=senses,
            provider_metadata={
                "entry_id": self.entry_id,
                "kind": self.kind,
                "domain_tags": list(self.domain_tags),
            },
        )


@runtime_checkable
class SenseMenuOverlaySource(Protocol):
    """Protocol for any candidate overlay provider feeding the sense menu."""

    def candidates_for_occurrence(
        self,
        *,
        card_id: str,
        surface_form: str,
        sentence: str,
        occurrence_span: tuple[int, int] | None = None,
    ) -> Sequence[tuple[MenuAnalysis, SenseOverlayEntry, tuple[int, int]]]:
        """Return candidate analyses, the overlay entry, and matching span."""
        ...


class InMemoryOverlayRegistry:
    """In-memory registry supporting arbitrary slang, fillers, and extra senses."""

    def __init__(self, entries: Sequence[SenseOverlayEntry] = ()) -> None:
        self._entries: dict[str, list[SenseOverlayEntry]] = {}
        for entry in entries:
            self.register(entry)

    def register(self, entry: SenseOverlayEntry) -> None:
        for attach in entry.attach_words or (entry.expression,):
            self._entries.setdefault(attach.casefold(), []).append(entry)

    def candidates_for_occurrence(
        self,
        *,
        card_id: str,
        surface_form: str,
        sentence: str,
        occurrence_span: tuple[int, int] | None = None,
    ) -> list[tuple[MenuAnalysis, SenseOverlayEntry, tuple[int, int]]]:
        results: list[tuple[MenuAnalysis, SenseOverlayEntry, tuple[int, int]]] = []
        lowered_sent = sentence.casefold()
        candidates = self._entries.get(surface_form.casefold(), ())

        for entry in candidates:
            expr = entry.expression.casefold()
            start = lowered_sent.find(expr)
            if start < 0:
                continue
            span = (start, start + len(expr))
            if occurrence_span is not None:
                # Must overlap or enclose the target occurrence
                occ_start, occ_end = occurrence_span
                if not (span[0] <= occ_start and occ_end <= span[1]):
                    continue
            analysis = entry.to_menu_analysis(card_id)
            results.append((analysis, entry, span))
        return results


class CompositeOverlayProvider:
    """Aggregates multiple overlay sources (MWEs, slang, conversational fillers)."""

    def __init__(self, sources: Sequence[SenseMenuOverlaySource] = ()) -> None:
        self.sources: list[SenseMenuOverlaySource] = list(sources)

    def add_source(self, source: SenseMenuOverlaySource) -> None:
        self.sources.append(source)

    def candidates_for_occurrence(
        self,
        *,
        card_id: str,
        surface_form: str,
        sentence: str,
        occurrence_span: tuple[int, int] | None = None,
    ) -> list[tuple[MenuAnalysis, SenseOverlayEntry, tuple[int, int]]]:
        combined: list[tuple[MenuAnalysis, SenseOverlayEntry, tuple[int, int]]] = []
        seen_analysis_ids: set[str] = set()
        for source in self.sources:
            for analysis, entry, span in source.candidates_for_occurrence(
                card_id=card_id,
                surface_form=surface_form,
                sentence=sentence,
                occurrence_span=occurrence_span,
            ):
                if analysis.menu_analysis_id not in seen_analysis_ids:
                    seen_analysis_ids.add(analysis.menu_analysis_id)
                    combined.append((analysis, entry, span))
        return combined


def declared_gloss_to_overlay(entry: Any) -> SenseOverlayEntry:
    """Convert a DeclaredEntry of kind 'gloss' into a SenseOverlayEntry for WSD competition."""
    if getattr(entry, "kind", None) != "gloss":
        raise ValueError(f"expected gloss entry, got {getattr(entry, 'kind', None)}")
    translations = tuple(
        str(s.get("translation", "")).strip()
        for s in getattr(entry, "senses", [])
        if str(s.get("translation", "")).strip()
    )
    if not translations:
        raise ValueError(f"{entry.entry_id}: no translations found in gloss entry")
    cls_tag = getattr(entry, "payload", {}).get("class", "slang")
    pos_tag = (
        getattr(entry, "senses", [{}])[0].get("pos")
        or ("NOUN" if cls_tag in {"slang", "vocabulary"} else "PHRASE")
    ).upper()
    return SenseOverlayEntry(
        entry_id=entry.entry_id,
        kind=cls_tag,
        expression=entry.surface,
        translations=translations,
        part_of_speech=pos_tag,
        attach_words=(entry.surface,),
        domain_tags=tuple(k for k, v in entry.scope.items() if v),
        metadata={"declared_entry_id": entry.entry_id, "scope": dict(entry.scope)},
    )
