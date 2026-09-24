"""Pre-WSD Lyrics Occurrence Sampling and Quality Sieve.

Implements the multi-tiered WSD execution budget based on frequency rank and
menu polysemy (sense count), coupled with a deterministic lyrics quality sieve
that prioritizes rich, well-aligned, non-repetitive lyric sentences.
"""

from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Any, Mapping, Sequence

from fluency.harvest.matching import example_identity

DEFAULT_MIN_TOKEN_LENGTH = 5
DEFAULT_MAX_TOKEN_LENGTH = 18
MIN_ALIGNMENT_RATIO = 0.40
MAX_ALIGNMENT_RATIO = 2.50


@dataclass(frozen=True, slots=True)
class LyricsSamplingConfig:
    """Configurable budget parameters for lyrics WSD occurrence sampling."""

    tier1_rank_ceiling: int = 1000
    tier1_floor: int = 10
    tier1_multiplier: float = 3.0

    tier2_rank_ceiling: int = 5000
    tier2_floor: int = 8
    tier2_multiplier: float = 2.0


DEFAULT_SAMPLING_CONFIG = LyricsSamplingConfig()


def calculate_lyrics_wsd_budget(
    rank: int,
    sense_count: int,
    available_lines: int,
    config: LyricsSamplingConfig = DEFAULT_SAMPLING_CONFIG,
) -> int:
    """Calculate the exact number of occurrences of a card that should reach WSD.

    - Top Tier (Rank 1–1,000): Hard floor of 10 lines (even for monosemous words), scaling up to 24+ for polysemous words.
    - Mid Tier (Rank 1,001–5,000): Floor of 8 lines.
    - Tail/Slang (Rank 5,001+): 100% of available lines.
    """
    if available_lines <= 0:
        return 0

    senses = max(1, sense_count)
    if rank <= config.tier1_rank_ceiling:
        budget = max(config.tier1_floor, int(config.tier1_multiplier * senses + 0.5))
    elif rank <= config.tier2_rank_ceiling:
        budget = max(config.tier2_floor, int(config.tier2_multiplier * senses + 0.5))
    else:
        # Tail / slang: 100% of available supply
        return available_lines

    return min(available_lines, budget)


def score_lyric_line_quality(
    line_text: str,
    translation_text: str | None = None,
    alignment_score: float | None = None,
) -> float:
    """Score a candidate lyric line for learner clarity and lexical quality.

    Higher is better (0.0 to 1.0 scale).
    Penalizes extreme short/long lines and wildly divergent translation ratios.
    """
    tokens = [t for t in re.split(r"\s+", line_text.strip()) if t]
    token_count = len(tokens)
    if token_count == 0:
        return 0.0

    score = 1.0

    # 1. Length sweet-spot (ideally 5 to 18 tokens)
    if token_count < DEFAULT_MIN_TOKEN_LENGTH:
        # Very short fragment / sound effect penalty
        score -= 0.35 * (DEFAULT_MIN_TOKEN_LENGTH - token_count)
    elif token_count > DEFAULT_MAX_TOKEN_LENGTH:
        # Very long run-on rap bar penalty
        score -= min(0.40, 0.02 * (token_count - DEFAULT_MAX_TOKEN_LENGTH))

    # 2. Translation alignment ratio (if translation exists)
    if translation_text:
        trans_tokens = [t for t in re.split(r"\s+", translation_text.strip()) if t]
        if trans_tokens:
            ratio = len(tokens) / len(trans_tokens)
            if ratio < MIN_ALIGNMENT_RATIO or ratio > MAX_ALIGNMENT_RATIO:
                score -= 0.30

    # 3. Alignment confidence bonus
    if alignment_score is not None:
        score += 0.20 * min(1.0, max(0.0, alignment_score))

    # 4. Clean punctuation bonus (complete thought with punctuation)
    if line_text.endswith((".", "!", "?", "—", "...")):
        score += 0.05

    return round(max(0.01, score), 4)


def select_best_lyrics_occurrences(
    occurrences: Sequence[Mapping[str, Any]],
    lines_by_id: Mapping[str, Mapping[str, Any]],
    alignments_by_line: Mapping[str, Mapping[str, Any]],
    *,
    budget: int,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Sieve occurrences deterministically: deduplicate, score quality, and slice to budget.

    Returns (selected, overflow).
    """
    if budget <= 0:
        return [], list(occurrences)

    seen_line_identities: set[str] = set()
    scored_candidates: list[tuple[float, str, dict[str, Any]]] = []
    skipped_duplicates: list[dict[str, Any]] = []

    for occ in occurrences:
        line_id = str(occ.get("line_id", ""))
        line = lines_by_id.get(line_id, {})
        line_text = str(line.get("text", "")).strip()

        # Deduplication check
        ident = example_identity(line_text)
        if ident in seen_line_identities:
            skipped_duplicates.append(dict(occ))
            continue
        seen_line_identities.add(ident)

        alignment = alignments_by_line.get(line_id)
        trans_text = str(alignment.get("target", {}).get("text", "")) if alignment else None
        align_score = alignment.get("score") if alignment else None

        q_score = score_lyric_line_quality(line_text, trans_text, align_score)
        scored_candidates.append((q_score, str(occ.get("occurrence_id", "")), dict(occ)))

    # Sort deterministically: highest score first, tie-break on occurrence_id
    scored_candidates.sort(key=lambda item: (-item[0], item[1]))

    selected = [item[2] for item in scored_candidates[:budget]]
    overflow = [item[2] for item in scored_candidates[budget:]] + skipped_duplicates

    return selected, overflow
