"""Portuguese WSD surface location.

Follows the Spanish adapter rather than the French one: locating a surface is a
scan for word characters plus the shared normalizer, and needs no tokenizer
module. French requires one because of elision (``l'eau``), which Portuguese
does not have.

Hyphenated clitics (``da-me``, ``ve-lo``) and mesoclisis (``far-me-ia``) are
deliberately NOT joined into one token when locating the *parts*: the frequency
list's tokenizer split on hyphens, so ``Da-me o livro`` still yields the ``da``
and ``me`` cards. Lexical hyphenated cards that the inventory *does* keep
(``bem-vindo``, ``hei-de``) are located as the hyphenated span itself.
"""

from __future__ import annotations

import re

from fluency.languages.portuguese.surfaces import normalize_surface
from fluency.wsd.languages.base import TargetOccurrence, hyphenated_surface_occurrences


class PortugueseWSDAdapter:
    language = "pt"

    # Portuguese uses acute, circumflex, grave, tilde and cedilla. Accents are
    # contrastive at the surface, so they are matched, never folded away.
    _WORD_CHARS = r"0-9A-Za-zÁÂÃÀÉÊÍÓÔÕÚÜÇáâãàéêíóôõúüç"
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
