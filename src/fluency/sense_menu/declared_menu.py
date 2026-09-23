"""Menu analyses from a hand-written gloss, for any provider.

A ``declared_gloss`` resolution means no dictionary entry exists and a person
wrote the meaning down (``fluency.surfaces.declared``). Its menu analysis names
its own adapter, never the provider's, so nothing downstream can mistake a
hand-written sense for one SpanishDict or Wiktionary supplied (Invariant 3).
Provider-neutral: the SpanishDict and Kaikki adapters both call this.
"""

from __future__ import annotations

from typing import Any

from fluency.menus import MenuAnalysis, SenseLeaf, build_analysis_id

DECLARED_GLOSS_ADAPTER = "declared-gloss/v1"


def declared_gloss_analyses(card_id: str, surface: str, resolution: Any) -> list[MenuAnalysis]:
    entry = resolution.entry
    stamp = resolution.stamp()
    by_pos: dict[str, list[tuple[int, dict[str, Any]]]] = {}
    for index, sense in enumerate(entry.senses, start=1):
        by_pos.setdefault(str(sense.get("pos") or "X").strip() or "X", []).append((index, sense))
    analyses = []
    for order, (part_of_speech, senses) in enumerate(by_pos.items()):
        key = f"{entry.entry_id}:{part_of_speech}"
        leaves = tuple(
            SenseLeaf(
                sense_id=f"{entry.entry_id}#{index}",
                translation=str(sense["translation"]).strip(),
                definition=str(sense.get("definition") or "").strip(),
                source_reference=f"declared:{entry.entry_id}#{index}",
                provider_metadata={
                    "declared": {"entry_id": entry.entry_id, "trust": entry.trust,
                                 "scope": dict(entry.scope), "source_file": entry.source_file},
                    "translation_status": "present",
                },
            )
            for index, sense in senses
        )
        analyses.append(MenuAnalysis(
            menu_analysis_id=build_analysis_id(
                card_id=card_id, source_adapter=DECLARED_GLOSS_ADAPTER, source_analysis_key=key),
            card_id=card_id,
            surface_form=surface,
            headword=surface,
            part_of_speech=part_of_speech,
            source_adapter=DECLARED_GLOSS_ADAPTER,
            source_analysis_key=key,
            senses=leaves,
            provider_metadata={"resolver": stamp, "menu_order_prior": order},
        ))
    return analyses
