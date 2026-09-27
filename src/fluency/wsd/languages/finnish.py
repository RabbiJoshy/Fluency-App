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

    def contextual_headwords(self, sentence: str, surface_form: str) -> frozenset[str]:
        """Resolve measured Finnish homographic inflections before WSD.

        ``tapaan`` is either the illative of ``tapa`` (manner) or first-person
        singular of ``tavata`` (meet). Its noun modifiers are genitive or
        illative forms ending in ``-n`` (``samaan tapaan``, ``tappajan
        tapaan``); otherwise the observed form is the verb. This rule matched
        all 30 manually audited release candidates, while Stanza missed six
        verb uses and unconstrained semantic scoring missed three displayed
        examples.
        """

        if surface_form.casefold() != "tapaan":
            return frozenset()
        noun_phrase = re.search(
            rf"\b(?P<modifier>[{self._WORD_CHARS}]+n)\s+tapaan\b",
            sentence,
            re.IGNORECASE,
        )
        # ``ennen kuin tapaan`` is the one measured non-modifier sequence that
        # has the same spelling shape. These function/adverb words cannot be a
        # noun modifier here; keeping them explicit avoids pretending that a
        # suffix alone is a complete Finnish parser.
        non_modifiers = frozenset(
            {"kuin", "kun", "uudelleen", "jälleen", "harvoin", "pian"}
        )
        is_noun = bool(
            noun_phrase
            and noun_phrase.group("modifier").casefold() not in non_modifiers
        )
        return frozenset({"tapa" if is_noun else "tavata"})

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
