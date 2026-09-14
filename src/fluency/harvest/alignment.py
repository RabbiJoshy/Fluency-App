"""Translation alignment scoring for harvested candidate pairs.

A harvested pair is a target sentence and the English a corpus offers as its
translation. The harvest's form rules judge each side on its own; nothing
until now judged whether the two are the same sentence. OpenSubtitles rows
drift out of alignment -- "Porque este bebe esta a bater a porta." paired with
"Is the Sarah parade over?" -- and a learner reading the English for meaning
has no way to tell.

The score is LaBSE cosine similarity, a bi-encoder trained for bitext mining.
Measured on the Portuguese 10,000-card harvest (53,772 pairs):

    Tatoeba mean 0.885, OpenSubtitles mean 0.802

The gap is register, not error. Tatoeba is literal and subtitle translation is
idiomatic, so the score reads as literalness rather than correctness, and a cut
high enough to remove a useful number of pairs removes good idiom with them:
in the 0.35-0.50 band roughly three of every four pairs are sound
("O fim esta se aproximando." / "The sands are running out."). The floor is
therefore set low, where the model is unambiguous -- every pair below 0.30 read
by hand was genuinely misaligned -- and it is a floor, not a ranking. Above it
no preference is expressed, so the subtitle register survives intact.

This buys roughly 0.55% of candidates. That is a tenth of what a higher cut
would take and it is the part that is actually wrong.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Iterable, Mapping

# Below this, hand reading found no correctly-aligned pair. Above it the model
# is measuring how literal a translation is, which is not a defect.
DEFAULT_ALIGNMENT_FLOOR = 0.30
ALIGNMENT_VERSION = "labse-cosine/v1"
MODEL_ID = "sentence-transformers/LaBSE"


def _load_model(device: str | None = None):
    import torch
    from sentence_transformers import SentenceTransformer

    if device is None:
        device = "mps" if torch.backends.mps.is_available() else "cpu"
    return SentenceTransformer(MODEL_ID, device=device)


def score_pairs(
    pairs: list[tuple[str, str]], *, device: str | None = None, batch_size: int = 256
) -> list[float]:
    """Cosine similarity between each target and its translation."""
    if not pairs:
        return []
    model = _load_model(device)
    encode = lambda texts: model.encode(
        texts,
        batch_size=batch_size,
        convert_to_numpy=True,
        normalize_embeddings=True,
        show_progress_bar=False,
    )
    left = encode([pair[0] for pair in pairs])
    right = encode([pair[1] for pair in pairs])
    return [float(value) for value in (left * right).sum(1)]


def read_cache(path: Path) -> dict[str, float]:
    if not path.exists():
        return {}
    payload = json.loads(path.read_text())
    return {str(k): float(v) for k, v in (payload.get("scores") or {}).items()}


def write_cache(path: Path, scores: Mapping[str, float]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(
            {
                "alignment_version": ALIGNMENT_VERSION,
                "model": MODEL_ID,
                "scores": {k: round(float(v), 6) for k, v in sorted(scores.items())},
            },
            sort_keys=True,
        )
    )


def below_floor(
    scores: Mapping[str, float], sentence_ids: Iterable[str], floor: float
) -> set[str]:
    """Sentence ids the floor rejects. An unscored sentence is never rejected.

    Silence is not evidence of misalignment: a pair the scorer never saw must
    keep its place rather than be dropped for want of a measurement.
    """
    rejected = set()
    for sentence_id in sentence_ids:
        value = scores.get(sentence_id)
        if value is not None and value < floor:
            rejected.add(sentence_id)
    return rejected
