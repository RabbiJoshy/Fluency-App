"""The headwords a SpanishDict page declares for a lyric surface, beyond its own.

SpanishDict files a verb's senses under the infinitive, never on a conjugated
form's page. When a form is also a word in its own right, its page holds that
word's entry *and* states the relation: the page for *muerdo* carries the noun
(*bite*) and the result "muerdo: conjugation of morder". Reading only the
page's dictionary entries kept the noun and dropped the verb, so the card had
one sense and WSD never ran.

Which headwords count is decided once, by the shared declared-lemma rule
(``fluency.sense_menu.spanishdict_lemmas``): the page's own headword and the
relations it states. The conjugation table is not consulted for a page that
answered, so a noun that merely shares a verb form's spelling (*chica*) gains
no infinitive. Nothing here builds a menu; it names SpanishDict's own entries.
"""

from __future__ import annotations

from typing import Any, Mapping

from fluency.sense_menu.spanishdict_lemmas import (
    PAGE_RELATION,
    SpanishDictLemmaRule,
    headword_key,
)


def page_declared_forms(rule: SpanishDictLemmaRule, surface: str, page: Mapping[str, Any] | None) -> list[str]:
    """Headwords the exact page states this surface is a conjugation or inflection of."""
    if not isinstance(page, Mapping):
        return []
    found = rule.resolve(surface, page)
    key = headword_key(surface)
    return [item.lemma for item in found.lemmas
            if item.provenance == PAGE_RELATION and headword_key(item.lemma) != key]


def headword_analyses(
    headword: str,
    surface_page: Mapping[str, Any] | None,
    normalized_menu: Mapping[str, Any],
    headword_cache: Mapping[str, Any],
) -> list[dict[str, Any]]:
    """SpanishDict's own entry for ``headword``: its menu, its cached page, or the surface page's analyses under it."""
    menu = normalized_menu.get(headword)
    if menu:
        return list(menu)
    cached = headword_cache.get(headword)
    if isinstance(cached, Mapping) and cached.get("dictionary_analyses"):
        return list(cached["dictionary_analyses"])
    page = surface_page if isinstance(surface_page, Mapping) else {}
    return [a for a in page.get("dictionary_analyses") or []
            if isinstance(a, Mapping) and str(a.get("headword") or "").strip() == headword]
