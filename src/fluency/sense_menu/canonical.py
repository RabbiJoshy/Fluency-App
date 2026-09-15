"""Choose the one canonical example a sense shows, if it has one.

A canonical example is the dictionary's own illustration of a sense. It needs
no WSD -- the provider already bound it to the sense -- so it arrives outside
the corpus pipeline entirely and outside whatever cap governs corpus examples.

Exactly one per sense. SpanishDict is effectively one-per-sense already (95.3%
carry a single example), but Wiktionary is not: 28% of Portuguese senses and
29% of Czech ones carry two or more, up to ten. Without a choice here, "show
the canonical example" would mean showing ten of them on one meaning.

Every criterion below is something the provider *stated*. None is inferred from
the text, which is the rule that matters here: a heuristic reading of
`llevatelo` once produced `llegar`, confidently.
"""

from __future__ import annotations

from typing import Any, Mapping

#: Roughly the corpus preferred band, so a canonical example reads like its
#: neighbours on the card rather than announcing itself as dictionary prose.
IDEAL_TOKENS = 8


def _text(example: Mapping[str, Any]) -> str:
    return (example.get("text") or example.get("original") or "").strip()


def _translation(example: Mapping[str, Any]) -> str:
    return (example.get("english") or example.get("translation")
            or example.get("translated") or "").strip()


def is_proper(example: Mapping[str, Any]) -> bool:
    """Whether this is a usable sentence rather than a citation or a pattern.

    Three provider declarations, each rejecting a different thing:

    - ``type: quotation`` is a literary citation carrying a ``ref``. It
      illustrates attested use, not ordinary use.
    - ``tags: [collocation]`` is a pattern, not a sentence -- Czech
      ``setkat se s nekym`` / *to meet someone*. A quarter of Czech canonical
      examples are these.
    - no English at all is unusable on a bilingual card.
    """

    if (example.get("type") or "example") != "example":
        return False
    if "collocation" in (example.get("tags") or ()):
        return False
    return bool(_text(example)) and bool(_translation(example))


def _rank(example: Mapping[str, Any]) -> tuple:
    """Sort key; lower is better. Declared signals first, shape last."""

    tags = tuple(example.get("tags") or ())
    tokens = len(_text(example).split())
    return (
        # The headword's position is marked, so the card can highlight it and
        # the reader's eye lands in the right place.
        0 if example.get("bold_text_offsets") else 1,
        # The English side is aligned too, which is strictly more to work with.
        0 if example.get("bold_translation_offsets") else 1,
        # A regional tag is a claim about one variety; prefer the unmarked one
        # when an unmarked alternative exists.
        1 if any(t in {"Portugal", "Brazil"} for t in tags) else 0,
        abs(tokens - IDEAL_TOKENS),
        _text(example),
    )


def examples_of(sense: Mapping[str, Any]) -> list[Mapping[str, Any]]:
    """Every canonical example a sense carries, whichever provider supplied it."""

    provider = sense.get("provider_metadata") or {}
    spanishdict = (provider.get("spanishdict") or {}).get("examples") or []
    return list(spanishdict) or list(provider.get("examples") or [])


def choose(sense: Mapping[str, Any]) -> dict[str, Any] | None:
    """The single canonical example for this sense, normalised, or None.

    The return shape is provider-neutral so the card does not need to know
    which dictionary answered.
    """

    usable = [e for e in examples_of(sense) if is_proper(e)]
    if not usable:
        return None
    best = min(usable, key=_rank)
    return {
        "text": _text(best),
        "translation": _translation(best),
        "bold_text_offsets": best.get("bold_text_offsets") or [],
        "bold_translation_offsets": best.get("bold_translation_offsets") or [],
        "literal_meaning": best.get("literal_meaning") or "",
        "tags": list(best.get("tags") or ()),
    }
