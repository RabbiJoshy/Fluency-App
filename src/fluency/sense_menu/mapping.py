"""Source-to-target mapping for Portuguese Wiktionary dictionary senses.

Preserves exact source evidence, raw records and identifiers alongside derived
WSD target descriptions and non-exhaustive learner presentation cues.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
import re
from typing import Any, Mapping, Sequence

from fluency.features.parenthetical import leading_parenthetical, split_top_level_commas
from fluency.sense_menu.kaikki import (
    _glosses,
    _regions,
    _sense_id,
    _sense_tags,
)

MAPPING_VERSION = "wiktionary-source-to-target/v1"
PINNED_SNAPSHOT_ID = "enwiktionary-2026-08-20"
PINNED_SNAPSHOT_HASH = (
    "sha256:29c17be277879653aa60fc24413ba071e81845b6bb1b1bb7e7828d239796209d"
)


@dataclass(frozen=True, slots=True)
class RawConstruction:
    raw_expansion: str
    template_name: str | None
    template_args: dict[str, Any]
    is_template: bool


@dataclass(frozen=True, slots=True)
class SourceLocator:
    snapshot_file: str
    line_number: int | None


@dataclass(frozen=True, slots=True)
class ProvenanceRecord:
    provider: str
    snapshot_id: str
    snapshot_content_id: str
    mapping_version: str
    source_reference: str


@dataclass(frozen=True, slots=True)
class DeterministicSourceRecord:
    source_sense_id: str
    locator: SourceLocator
    headword: str
    part_of_speech: str
    raw_gloss_sequence: tuple[str, ...]
    leaf_gloss: str
    constructions: tuple[RawConstruction, ...]
    tags: tuple[str, ...]
    examples: tuple[dict[str, Any], ...]
    synonyms: tuple[dict[str, Any], ...]
    antonyms: tuple[dict[str, Any], ...]
    links: tuple[list[str], ...]
    raw_sense_payload: dict[str, Any]
    provenance: ProvenanceRecord


@dataclass(frozen=True, slots=True)
class WsdTargetDescription:
    wsd_definition: str
    definition_path: tuple[str, ...]
    construction_frame: str | None
    usage_tags: tuple[str, ...]
    regions: tuple[str, ...]
    domains: tuple[str, ...]
    examples: tuple[dict[str, Any], ...]


@dataclass(frozen=True, slots=True)
class LearnerPresentationCue:
    heading: str
    context_subrow: str
    chips: tuple[str, ...]
    is_non_exhaustive_cue: bool = True


@dataclass(frozen=True, slots=True)
class TargetMeaningRecord:
    source: DeterministicSourceRecord
    wsd_target: WsdTargetDescription
    learner: LearnerPresentationCue
    uncertainty_flags: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "source": asdict(self.source),
            "wsd_target": asdict(self.wsd_target),
            "learner": asdict(self.learner),
            "uncertainty_flags": list(self.uncertainty_flags),
        }


def extract_raw_constructions(sense: dict[str, Any]) -> tuple[RawConstruction, ...]:
    """Extract all explicit and bracketed constructions losslessly."""
    constructions: list[RawConstruction] = []
    seen_expansions: set[str] = set()

    for tmpl in sense.get("info_templates", []) or []:
        if isinstance(tmpl, dict) and tmpl.get("name") == "+obj":
            expansion = str(tmpl.get("expansion") or "").strip()
            args = dict(tmpl.get("args") or {})
            if expansion:
                constructions.append(
                    RawConstruction(
                        raw_expansion=expansion,
                        template_name="+obj",
                        template_args=args,
                        is_template=True,
                    )
                )
                seen_expansions.add(expansion.strip().strip("[]").casefold())

    for raw in _glosses(sense, "raw_glosses"):
        match = re.search(r"\[with\s+[^\]]+\]", raw, re.IGNORECASE)
        if match:
            bracket_text = match.group(0).strip()
            if bracket_text.strip().strip("[]").casefold() not in seen_expansions:
                constructions.append(
                    RawConstruction(
                        raw_expansion=bracket_text,
                        template_name=None,
                        template_args={},
                        is_template=False,
                    )
                )
                seen_expansions.add(bracket_text.strip().strip("[]").casefold())

    return tuple(constructions)


def parse_raw_gloss(raw_gloss: str) -> tuple[str | None, str, str | None]:
    """Separate leading parenthetical label and trailing bracketed construction from core text.

    Returns: (leading_parenthetical, core_definition, bracketed_construction)
    """
    text = raw_gloss.strip()
    lp = leading_parenthetical(text)
    if lp:
        text = text[len(lp) + 2 :].strip()

    bracket_match = re.search(r"\s*\[with\s+([^\]]+)\]\s*$", text, re.IGNORECASE)
    bracket = bracket_match.group(1).strip() if bracket_match else None
    if bracket_match:
        text = text[: bracket_match.start()].strip()

    return lp, text, bracket


def format_source_construction_cue(raw_construction_text: str) -> str:
    """Format an accurate, non-exhaustive context cue directly from the source construction.

    Does not invent prepositions or syntactic constraints not present in the source text.
    """
    s = raw_construction_text.strip()
    # Strip leading [with or [ and trailing ]
    s = re.sub(r"^\[(?:with\s+)?", "", s, flags=re.IGNORECASE).rstrip("]")
    s = re.sub(r"^with\s+", "", s, flags=re.IGNORECASE)

    # Strip quoted explanatory meanings in typographic quotes ‘...’ or ASCII quotes '...'
    s = re.sub(r"‘[^’]+’", "", s)
    s = re.sub(r"'[^']+'", "", s)

    # Clean up whitespace and punctuation
    s = re.sub(r"\s*,\s*", ", ", s)
    s = re.sub(r"\s+", " ", s).strip(" ,")

    if not s.startswith("+"):
        s = f"+ {s}"
    return s


def build_context_subrow(
    constructions: Sequence[RawConstruction],
    leading_qualifier: str | None,
    tags: Sequence[str],
) -> tuple[str, bool]:
    """Derive accurate, non-exhaustive learner context subrow from source evidence."""
    cues: list[str] = []

    for c in constructions:
        formatted = format_source_construction_cue(c.raw_expansion)
        if formatted:
            cues.append(formatted)

    if not cues and leading_qualifier:
        parts = split_top_level_commas(leading_qualifier)
        semantic_parts = [
            p
            for p in parts
            if p.casefold()
            not in {
                "transitive",
                "intransitive",
                "copulative",
                "auxiliary",
                "catenative",
                "reflexive",
                "pronominal",
                "impersonal",
                "colloquial",
                "slang",
                "dated",
                "archaic",
                "vulgar",
            }
        ]
        if semantic_parts:
            cues.append(", ".join(semantic_parts))

    joined = "; ".join(dict.fromkeys(cues))
    return joined, bool(joined)


def map_kaikki_sense_to_target(
    row: dict[str, Any],
    sense: dict[str, Any],
    *,
    language_code: str = "pt",
    policy: dict[str, Any] | None = None,
    snapshot_file: str = "kaikki.org-dictionary-Portuguese.jsonl",
    line_number: int | None = None,
    snapshot_id: str = PINNED_SNAPSHOT_ID,
    snapshot_content_id: str = PINNED_SNAPSHOT_HASH,
    provider_id_collides: bool | None = None,
    sense_keys_collide: bool | None = None,
) -> TargetMeaningRecord:
    """Map one raw Kaikki sense losslessly into Deterministic, WSD, and Learner structures."""
    headword = str(row.get("word") or "")
    pos = str(row.get("pos") or "")

    raw_id = sense.get("id")
    row_senses = row.get("senses", [])
    if provider_id_collides is None:
        provider_id_collides = (
            isinstance(raw_id, str)
            and sum(1 for s in row_senses if s.get("id") == raw_id) > 1
        )
    if sense_keys_collide is None:
        from fluency.sense_menu.kaikki import _sense_keys
        my_keys = _sense_keys(sense)
        sense_keys_collide = (
            sum(1 for s in row_senses if _sense_keys(s) == my_keys) > 1
        )

    sense_id, source_reference = _sense_id(
        sense,
        language_code=language_code,
        headword=headword,
        part_of_speech=pos,
        provider_id_collides=provider_id_collides,
        sense_keys_collide=sense_keys_collide,
    )

    raw_gloss_seq = tuple(
        _glosses(sense, "raw_glosses") or _glosses(sense, "glosses") or []
    )
    terminal_raw_gloss = raw_gloss_seq[-1] if raw_gloss_seq else ""
    lp, core_def, bracket = parse_raw_gloss(terminal_raw_gloss)
    clean_leaf = core_def or terminal_raw_gloss

    constructions = extract_raw_constructions(sense)
    tags = tuple(sorted(_sense_tags(sense)))
    examples = tuple(
        item for item in (sense.get("examples") or []) if isinstance(item, dict)
    )
    synonyms = tuple(
        item for item in (sense.get("synonyms") or []) if isinstance(item, dict)
    )
    antonyms = tuple(
        item for item in (sense.get("antonyms") or []) if isinstance(item, dict)
    )
    links = tuple(
        [str(x) for x in item]
        for item in (sense.get("links") or [])
        if isinstance(item, (list, tuple))
    )

    locator = SourceLocator(
        snapshot_file=snapshot_file,
        line_number=line_number,
    )
    provenance = ProvenanceRecord(
        provider="wiktionary",
        snapshot_id=snapshot_id,
        snapshot_content_id=snapshot_content_id,
        mapping_version=MAPPING_VERSION,
        source_reference=source_reference,
    )

    deterministic = DeterministicSourceRecord(
        source_sense_id=sense_id,
        locator=locator,
        headword=headword,
        part_of_speech=pos,
        raw_gloss_sequence=raw_gloss_seq,
        leaf_gloss=clean_leaf,
        constructions=constructions,
        tags=tags,
        examples=examples,
        synonyms=synonyms,
        antonyms=antonyms,
        links=links,
        raw_sense_payload=dict(sense),
        provenance=provenance,
    )

    raw_frame_text = " | ".join(c.raw_expansion for c in constructions) or None
    usage_tags = tuple(
        t
        for t in tags
        if t
        in {
            "colloquial",
            "slang",
            "archaic",
            "dated",
            "vulgar",
            "formal",
            "informal",
        }
    )
    regions = tuple(_regions(sense, policy or {}))
    domains = tuple(t for t in (sense.get("topics") or []) if isinstance(t, str))

    wsd_target = WsdTargetDescription(
        wsd_definition=clean_leaf,
        definition_path=raw_gloss_seq,
        construction_frame=raw_frame_text,
        usage_tags=usage_tags,
        regions=regions,
        domains=domains,
        examples=examples,
    )

    heading = clean_leaf
    context_subrow, has_context = build_context_subrow(
        constructions=constructions,
        leading_qualifier=lp,
        tags=tags,
    )
    chips = tuple(sorted(set([*regions, *usage_tags])))

    learner = LearnerPresentationCue(
        heading=heading,
        context_subrow=context_subrow,
        chips=chips,
        is_non_exhaustive_cue=has_context,
    )

    uncertainty_flags: list[str] = []
    if has_context:
        uncertainty_flags.append("non_exhaustive_cue")
    if examples:
        uncertainty_flags.append("untested_example_addition")

    return TargetMeaningRecord(
        source=deterministic,
        wsd_target=wsd_target,
        learner=learner,
        uncertainty_flags=tuple(uncertainty_flags),
    )
