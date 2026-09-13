"""Accounting for SpanishDict fields alongside its feature extractor."""

from __future__ import annotations

from typing import Any, Mapping

from fluency.features.metadata import MetadataAccounting
from fluency.features.spanishdict import (
    ENGLISH_GLOSS_REGIONS,
    SPANISH_USAGE_REGIONS,
    region_label,
)


STANDARD_FIELDS = frozenset({
    "_legacy_sense_id",
    "context",
    "examples",
    "headword",
    "pos",
    "regions",
    "source",
    "translation",
})


def metadata_accounting(sense: Mapping[str, Any]) -> MetadataAccounting:
    """Keep unfamiliar provider fields visible to the shared audit contract."""

    unclassified = [
        {
            "source_field": f"spanishdict.{field}",
            "value": value,
            "reason": "no canonical SpanishDict mapping",
        }
        for field, value in sorted(sense.items())
        if field not in STANDARD_FIELDS
    ]
    ignored = [
        {
            "source_field": "spanishdict.regions",
            "value": region_label(region),
            "reason": "English gloss locale, not target-language usage",
        }
        for region in sense.get("regions", []) or []
        if region_label(region) in ENGLISH_GLOSS_REGIONS
    ]
    unclassified.extend(
        {
            "source_field": "spanishdict.regions",
            "value": label,
            "reason": "region semantics are not mapped by the Spanish language policy",
        }
        for region in sense.get("regions", []) or []
        if (label := region_label(region))
        and label not in SPANISH_USAGE_REGIONS
        and label not in ENGLISH_GLOSS_REGIONS
    )
    return MetadataAccounting(
        coverage={
            "context": "parsed",
            "context_semantic_remainder": "preserved",
            "dictionary_examples": "preserved",
            "regions": "parsed",
            "usage_and_construction_notes": "parsed",
        },
        unclassified=tuple(unclassified),
        ignored=tuple(ignored),
    )
