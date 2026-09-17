"""Czech WSD surface location.

Follows the Portuguese adapter: locating a surface is a scan for word characters
plus the shared normalizer, and needs no tokenizer module. Czech has no elision,
so nothing like French ``l'eau`` has to be split.

Czech diacritics are contrastive at the surface -- ``byt``/``být``,
``mate``/``máte``, ``dela``/``dělá`` -- so they are matched, never folded.
"""

from __future__ import annotations

import re

from fluency.languages.czech.surfaces import normalize_surface
from fluency.wsd.languages.base import TargetOccurrence, hyphenated_surface_occurrences


class CzechWSDAdapter:
    language = "cs"

    # Czech uses the caron (háček), the acute (čárka) and the ring (kroužek).
    _WORD_CHARS = r"0-9A-Za-zÁÄÉĚÍÓÖÚŮÜÝČĎŇŘŠŤŽáäéěíóöúůüýčďňřšťž"
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
