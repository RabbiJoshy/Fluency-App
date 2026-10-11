"""Closed-class function-word safeguards (GROUND).

Prepositions such as es/pt *de*, *a*, *en*/*em*, *por*, *para* carry almost no
topical meaning, so a sentence embedding cannot tell their governed, functional
use from a rare idiomatic sense: pt *de* scored "in (wearing)" over "of" on
*lembrar-se de* by 0.006, and "by means of; by" won 11 of 26 *de* sentences
because that gloss sits near every infinitive. Two guards act only on the
preposition analyses a language declares in ``config/wsd/closed-class/<lang>.json``:

1. **Primary prior.** A non-primary leaf must beat the declared primary leaf
   by ``margin_floor``; otherwise the primary is kept.
2. **Governed bypass.** Where the parse shows the preposition introducing an
   infinitive complement, a verb's prepositional object or a noun's
   complement, the primary is chosen without consulting the embedding.

The primary leaf is declared per provider menu, not inferred from menu order:
SpanishDict lists *de* "from" first and the Wiktionary menu is sorted by id.

No card-level fold lives here. The app already moves a sense holding under 10%
of a card's sentences to Rarer uses (``MAIN_CARD_MIN_SHARE`` in
``app/js/vocab.js``), pooled by translation for prepositions, and keeps the
sentences' own sense. Reassigning them here would change what they mean.
"""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Any, Mapping

from fluency.wsd.menus import MenuAnalysis

POLICY_VERSION = "closed-class-ground/v1"


@dataclass(frozen=True, slots=True)
class ClosedClassEntry:
    headword: str
    part_of_speech: str
    primary_sense_id: str
    governed_bypass: bool


@dataclass(frozen=True, slots=True)
class TargetSyntax:
    """The parse around one target token, as the governed bypass reads it."""

    dep: str
    head_pos: str
    head_dep: str
    head_verb_form: str
    governor_pos: str
    parser: str

    def governed(self) -> str | None:
        if self.dep == "mark" and self.head_pos in {"VERB", "AUX"} and self.head_verb_form == "Inf":
            return "infinitive_complement"
        if self.dep == "case" and self.head_dep == "obj" and self.governor_pos in {"VERB", "AUX"}:
            return "verb_prepositional_object"
        if self.dep == "case" and self.head_dep == "nmod" and self.governor_pos in {"NOUN", "PROPN", "PRON"}:
            # X de Y between nouns: "bolso da jaqueta", "anel da mulher". The
            # embedding reads the topic (clothes -> "in (wearing)"), not the link.
            return "noun_complement"
        return None

    def to_dict(self) -> dict[str, str]:
        return {
            "dep": self.dep,
            "head_pos": self.head_pos,
            "head_dep": self.head_dep,
            "head_verb_form": self.head_verb_form,
            "governor_pos": self.governor_pos,
            "parser": self.parser,
        }


@dataclass(frozen=True, slots=True)
class GroundPolicy:
    policy_id: str
    content_id: str
    surfaces: frozenset[str]
    entries: Mapping[tuple[str, str], ClosedClassEntry]
    margin_floor: float

    def __post_init__(self) -> None:
        if self.margin_floor < 0:
            raise ValueError("ground margin floor must not be negative")

    def applies_to(self, surface_form: str) -> bool:
        return surface_form.casefold() in self.surfaces

    def entry(self, headword: str, part_of_speech: str) -> ClosedClassEntry | None:
        return self.entries.get((headword.casefold(), part_of_speech))

    def entry_for(self, analysis: MenuAnalysis) -> ClosedClassEntry | None:
        return self.entry(analysis.headword, analysis.part_of_speech)


def load_ground_policy(path: Path, *, content_id: str) -> GroundPolicy:
    raw = json.loads(path.read_text(encoding="utf-8"))
    if raw.get("policy_version") != POLICY_VERSION:
        raise ValueError(f"{path} is not {POLICY_VERSION}")
    entries = {}
    for item in raw["entries"]:
        entry = ClosedClassEntry(
            headword=item["headword"].casefold(),
            part_of_speech=item["part_of_speech"],
            primary_sense_id=item["primary_sense_id"],
            governed_bypass=bool(item.get("governed_bypass", False)),
        )
        entries[(entry.headword, entry.part_of_speech)] = entry
    return GroundPolicy(
        policy_id=raw["policy_id"],
        content_id=content_id,
        surfaces=frozenset(surface.casefold() for surface in raw["surfaces"]),
        entries=entries,
        margin_floor=float(raw["margin_floor"]),
    )


@dataclass(frozen=True, slots=True)
class GroundDecision:
    sense_id: str
    reason: str | None
    evidence: dict[str, Any]


def ground_selection(
    policy: GroundPolicy,
    *,
    analysis: MenuAnalysis,
    selected_sense_id: str,
    scores: Mapping[str, float],
    syntax: TargetSyntax | None,
) -> GroundDecision | None:
    """Return the grounded leaf for one occurrence, or ``None`` when out of scope.

    ``scores`` maps this analysis's sense ids to their final gloss scores.
    """

    entry = policy.entry_for(analysis)
    if entry is None:
        return None
    primary = entry.primary_sense_id
    if primary not in scores:
        raise ValueError(
            f"declared primary {primary} is not a leaf of {analysis.headword}/{analysis.part_of_speech}"
        )
    evidence: dict[str, Any] = {
        "policy_id": policy.policy_id,
        "policy_content_id": policy.content_id,
        "primary_sense_id": primary,
        "from_sense_id": selected_sense_id,
        "syntax": None if syntax is None else syntax.to_dict(),
    }
    governed = syntax.governed() if (syntax is not None and entry.governed_bypass) else None
    if governed is not None:
        evidence["governed"] = governed
        return GroundDecision(primary, "governed_bypass", evidence)
    if selected_sense_id == primary:
        return GroundDecision(primary, None, evidence)
    margin = scores[selected_sense_id] - scores[primary]
    evidence["margin_over_primary"] = margin
    evidence["margin_floor"] = policy.margin_floor
    if margin < policy.margin_floor:
        return GroundDecision(primary, "primary_prior_margin", evidence)
    return GroundDecision(selected_sense_id, None, evidence)
