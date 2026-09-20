"""Non-decomposition policy for multiword expressions.

A learner needs a multiword expression when its meaning cannot be derived from
its constituent parts.

The filter policy is defined in two sentences:
1. Candidate source rule: Multiword expressions must appear in Wiktionary as
   multiword entries; pure SpanishDict phrasebook collocations without Wiktionary
   backing are excluded as compositional noise.
2. Part-of-speech rule: Within Wiktionary, transparent noun compounds (entries
   whose only Wiktionary POS is "noun") are excluded as compositional; non-noun
   locutions (adverbials, prepositions, conjunctions, interjections, idioms)
   with corpus_freq > 0 are kept as tier-1 for WSD offering.

Absence is declared: compositional entries retain their place in the snapshot
with `verdict="exclude"` and `reason="compositional"`, never omitted implicitly.
Tier-2 content (corpus_freq == 0) is marked `verdict="exclude"`, `reason="zero_freq"`.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Sequence


@dataclass(frozen=True, slots=True)
class MWEDisposition:
    verdict: str  # "keep" or "exclude"
    reason: str   # "non_compositional", "compositional", "zero_freq"
    status: str   # "keep" or "compositional"
    non_compositional: bool

    def to_dict(self) -> dict[str, Any]:
        return {
            "verdict": self.verdict,
            "reason": self.reason,
            "status": self.status,
            "non_compositional": self.non_compositional,
        }


def classify_mwe(
    expression: str,
    translations: Sequence[str] = (),
    language: str = "es",
    *,
    corpus_freq: int = 0,
    sources: Sequence[str] = (),
    pos: str | Sequence[str] | None = None,
    in_wiktionary: bool | None = None,
) -> MWEDisposition:
    """Classify an MWE into keep (non-compositional) or exclude.

    Rule 1 (Source): Must be in Wiktionary. Pure SpanishDict collocations are excluded.
    Rule 2 (POS): Noun compounds (only POS is noun) are excluded as compositional.
    Tiering: corpus_freq > 0 is tier 1 (keep); corpus_freq == 0 is tier 2 (zero_freq).
    """
    lang = language.lower()

    # Determine Wiktionary membership
    wiktionary_present = in_wiktionary
    if wiktionary_present is None:
        if "wiktionary" in sources:
            wiktionary_present = True
        elif lang in ("pt", "cs"):
            # Portuguese and Czech candidate snapshots are 100% Wiktionary-derived
            wiktionary_present = True
        else:
            # Spanish: if not explicitly declared in sources, check fallback
            wiktionary_present = False

    # Rule 1: SpanishDict phrases without Wiktionary backing are compositional collocations
    if not wiktionary_present:
        return MWEDisposition(
            verdict="exclude",
            reason="compositional",
            status="compositional",
            non_compositional=False,
        )

    # Rule 2: Noun compounds in Wiktionary are transparent compounds, not idioms for learners
    is_noun_compound = False
    if pos is not None:
        if isinstance(pos, str):
            poses = {pos.lower()}
        else:
            poses = {p.lower() for p in pos}
        if poses and poses == {"noun"}:
            is_noun_compound = True

    if is_noun_compound:
        return MWEDisposition(
            verdict="exclude",
            reason="compositional",
            status="compositional",
            non_compositional=False,
        )

    # Non-compositional: separate tier 1 (attested, can carry evidence) from tier 2 (zero frequency)
    if corpus_freq > 0:
        return MWEDisposition(
            verdict="keep",
            reason="non_compositional",
            status="keep",
            non_compositional=True,
        )
    else:
        return MWEDisposition(
            verdict="exclude",
            reason="zero_freq",
            status="keep",
            non_compositional=True,
        )

