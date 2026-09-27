"""Finnish surface normalization for stable card identity."""

from __future__ import annotations

import re
import unicodedata

from fluency.core.identity import CardRecord, create_card_record


_WHITESPACE = re.compile(r"\s+")
_TYPOGRAPHIC_TRANSLATION = str.maketrans(
    {
        "’": "'",
        "‘": "'",
        "ʼ": "'",
        "‛": "'",
        "＇": "'",
        "‐": "-",
        "‑": "-",
    }
)


def canonicalize_typography(text: str) -> str:
    """Normalize Unicode and equivalent word punctuation without casing."""

    if not isinstance(text, str):
        raise TypeError("text must be a string")
    return unicodedata.normalize("NFC", text).translate(_TYPOGRAPHIC_TRANSLATION)


def normalize_surface(surface: str) -> str:
    """Return a Finnish surface key without lemmatizing or folding diacritics."""

    if not isinstance(surface, str):
        raise TypeError("surface must be a string")
    normalized = canonicalize_typography(surface)
    normalized = _WHITESPACE.sub(" ", normalized.strip()).lower()
    if not normalized:
        raise ValueError("surface must not be empty after normalization")
    return normalized


def create_finnish_card(surface: str) -> CardRecord:
    """Create a Finnish surface-card record from observed text."""

    return create_card_record("fi", normalize_surface(surface))
