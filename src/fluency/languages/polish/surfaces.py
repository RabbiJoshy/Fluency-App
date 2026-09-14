"""Polish surface normalization for stable card identity."""

from __future__ import annotations

import re
import unicodedata

from fluency.core.identity import CardRecord, create_card_record


_WHITESPACE = re.compile(r"\s+")


def canonicalize_typography(text: str) -> str:
    """Normalize Unicode without casing or folding Polish word punctuation.

    Polish writes no elision, so an apostrophe appears only in loans and in
    foreign-name inflection (``Kennedy'ego``) and is left exactly as observed.
    NFC matters because the ogonek on ``a``/``e`` and the acute on
    ``c n o s z`` are routinely supplied as combining marks.
    """

    if not isinstance(text, str):
        raise TypeError("text must be a string")
    return unicodedata.normalize("NFC", text)


def normalize_surface(surface: str) -> str:
    """Normalize typography without lemmatizing or folding Polish diacritics.

    Polish diacritics are contrastive at the surface and folding them would
    merge distinct cards: ``sad``/``sad-with-ogonek`` (orchard / they are),
    ``los``/``los-with-stroke`` (fate / elk), ``kat``/``kat-with-ogonek``
    (executioner / angle). The marks are letters, not decoration, so the
    complete observed surface is the identity and any base headword is lookup
    metadata only.

    Polish is heavily inflected, and each inflected form is its own observed
    surface -- the same rule every other language here follows.
    """

    if not isinstance(surface, str):
        raise TypeError("surface must be a string")
    normalized = unicodedata.normalize("NFC", surface)
    normalized = _WHITESPACE.sub(" ", normalized.strip()).lower()
    if not normalized:
        raise ValueError("surface must not be empty after normalization")
    return normalized


def create_polish_card(surface: str) -> CardRecord:
    """Create a Polish surface-card record from observed text."""

    surface_key = normalize_surface(surface)
    return create_card_record("pl", surface_key)
