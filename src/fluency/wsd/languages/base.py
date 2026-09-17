"""Language adapter protocol for locating an exact surface occurrence."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
import re
from typing import Protocol


@dataclass(frozen=True, slots=True)
class TargetOccurrence:
    observed_text: str
    surface_key: str
    start: int
    end: int


class LanguageAdapter(Protocol):
    language: str

    def locate(
        self,
        sentence: str,
        surface_form: str,
    ) -> tuple[TargetOccurrence, ...]: ...


def hyphenated_surface_occurrences(
    sentence: str,
    surface_form: str,
    *,
    normalize: Callable[[str], str],
    word_chars: str,
) -> tuple[TargetOccurrence, ...]:
    """Match a hyphenated card against the hyphenated span in the sentence.

    Word-run locators split on hyphens so clitic *parts* stay findable
    (``me`` in ``Dá-me``). That is correct for those cards. A card whose own
    surface contains a hyphen (``bem-vindo``, ``hei-de``) is a different
    identity and will never match a word run. This looks only at those cards.
    SpanishDict and Czech inventories currently have none; the helper still
    lives here so a hyphenated card in any word-scan language locates the
    same way.
    """

    if "-" not in surface_form:
        return ()
    surface_key = normalize(surface_form)
    run = re.compile(rf"[{word_chars}]+(?:-[{word_chars}]+)+")
    found: list[TargetOccurrence] = []
    for match in run.finditer(sentence or ""):
        observed = match.group(0)
        if normalize(observed) != surface_key:
            continue
        found.append(
            TargetOccurrence(
                observed_text=observed,
                surface_key=surface_key,
                start=match.start(),
                end=match.end(),
            )
        )
    return tuple(found)
