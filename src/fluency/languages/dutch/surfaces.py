"""Dutch surface normalization for stable card identity."""

from __future__ import annotations

import re
import unicodedata

from fluency.core.identity import CardRecord, create_card_record


_WHITESPACE = re.compile(r"\s+")
_TYPOGRAPHIC_TRANSLATION = str.maketrans(
    {
        "’": "'",  # right single quotation mark
        "‘": "'",  # left single quotation mark
        "ʼ": "'",  # modifier letter apostrophe
        "‛": "'",  # single high-reversed-9 quotation mark
        "＇": "'",  # fullwidth apostrophe
        "‐": "-",  # Unicode hyphen
        "‑": "-",  # non-breaking hyphen
    }
)


def canonicalize_typography(text: str) -> str:
    """Normalize Unicode and equivalent Dutch word punctuation without casing.

    Dutch writes an apostrophe *inside* ordinary words -- ``'s morgens``,
    ``auto's``, ``'t`` -- so the apostrophe is a letter-level character here,
    not stray punctuation. Every apostrophe variant folds to the ASCII
    apostrophe, which is what the ``nl-v1`` harvest policy names as canonical,
    so a subtitle's curly apostrophe and Tatoeba's straight one land on the
    same card. Hyphens fold likewise, for compounds such as ``zee-eend``.
    """

    if not isinstance(text, str):
        raise TypeError("text must be a string")
    return unicodedata.normalize("NFC", text).translate(_TYPOGRAPHIC_TRANSLATION)


def normalize_surface(surface: str) -> str:
    """Return the Dutch identity key without lemmatizing or folding diacritics.

    Dutch diaeresis and acute are contrastive (``een``/``een-with-acute``,
    ``voor``/``voor-with-diaeresis`` in ``reunie``-type spellings), so they are
    preserved. The apostrophe and hyphen are kept inside the surface rather
    than stripped: removing them would turn ``auto's`` into ``autos``, which is
    not a Dutch word, and split ``'s`` off as a card of its own.
    """

    if not isinstance(surface, str):
        raise TypeError("surface must be a string")

    normalized = canonicalize_typography(surface)
    normalized = _WHITESPACE.sub(" ", normalized.strip()).lower()
    if not normalized:
        raise ValueError("surface must not be empty after normalization")
    return normalized


def create_dutch_card(surface: str) -> CardRecord:
    """Create a Dutch surface-card record from observed text."""

    surface_key = normalize_surface(surface)
    return create_card_record("nl", surface_key)
