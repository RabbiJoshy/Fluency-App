"""Spanish surface normalization for stable card identity."""

from __future__ import annotations

import re
import unicodedata

from fluency.core.identity import CardRecord, create_card_record


_WHITESPACE = re.compile(r"\s+")


def canonicalize_typography(text: str) -> str:
    """Normalize Unicode without casing or folding Spanish word punctuation.

    Needed by the Wiktionary adapter, whose redirects require the source row's
    spelling to match the surface's case (lyrics v20 reads Spanish Wiktionary).
    Lyric elisions keep their apostrophe exactly as observed.
    """

    if not isinstance(text, str):
        raise TypeError("text must be a string")
    return unicodedata.normalize("NFC", text)


def normalize_surface(surface: str) -> str:
    """Normalize typography without lemmatizing or folding Spanish accents."""

    if not isinstance(surface, str):
        raise TypeError("surface must be a string")
    normalized = unicodedata.normalize("NFC", surface)
    normalized = _WHITESPACE.sub(" ", normalized.strip()).lower()
    if not normalized:
        raise ValueError("surface must not be empty after normalization")
    return normalized


def create_spanish_card(surface: str) -> CardRecord:
    """Create a Spanish surface-card record from observed text."""

    surface_key = normalize_surface(surface)
    return create_card_record("es", surface_key)
