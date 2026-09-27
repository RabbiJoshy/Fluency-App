"""Finnish WSD surface location.

Finnish diacritics are contrastive and the speech inventory contains complete
observed surface forms, so locating an occurrence is an exact normalized word
scan.  Hyphenated lexical cards are retained as one span when present.
"""

from __future__ import annotations

import re

from fluency.languages.finnish.surfaces import normalize_surface
from fluency.wsd.languages.base import TargetOccurrence, hyphenated_surface_occurrences


class FinnishWSDAdapter:
    language = "fi"

    _WORD_CHARS = r"0-9A-Za-zÄÖÅäöåŠŽšž"
    _WORD = re.compile(rf"[{_WORD_CHARS}]+")

    def locate(self, sentence: str, surface_form: str) -> tuple[TargetOccurrence, ...]:
        surface_key = normalize_surface(surface_form)
        found: list[TargetOccurrence] = []
        seen: set[tuple[int, int]] = set()
        for match in self._WORD.finditer(sentence or ""):
            observed = match.group(0)
            if normalize_surface(observed) != surface_key:
                continue
            found.append(
                TargetOccurrence(
                    observed_text=observed,
                    surface_key=surface_key,
                    start=match.start(),
                    end=match.end(),
                )
            )
            seen.add((match.start(), match.end()))
        for item in hyphenated_surface_occurrences(
            sentence,
            surface_form,
            normalize=normalize_surface,
            word_chars=self._WORD_CHARS,
        ):
            span = (item.start, item.end)
            if span not in seen:
                found.append(item)
                seen.add(span)
        return tuple(found)
