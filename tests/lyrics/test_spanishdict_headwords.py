"""Lyric cards keep the headwords SpanishDict's page declares, and only those."""

from fluency.lyrics.spanishdict_headwords import headword_analyses, page_declared_forms
from fluency.sense_menu.spanishdict_lemmas import SpanishDictLemmaRule

CONJ = {
    "muerdo": [{"lemma": "morder", "mood": "indicativo", "tense": "presente", "person": "1s"}],
    "chica": [{"lemma": "chicar", "mood": "indicativo", "tense": "presente", "person": "3s"}],
}
# As the 2026-09-23 snapshot records muerdo.
MUERDO = {
    "possible_results": [
        {"headword": "muerdo", "result": "muerdo", "heuristic": "dictionary", "translation": "bite", "pos": "X"},
        {"headword": "morder", "result": "muerdo", "heuristic": "conjugation", "translation": "I bite", "pos": "VERB"},
    ],
    "dictionary_analyses": [{"headword": "muerdo", "senses": [{"translation": "bite"}]}],
}
CHICA = {
    "possible_results": [{"headword": "chica", "result": "chica", "heuristic": "dictionary"}],
    "dictionary_analyses": [{"headword": "chica", "senses": [{"translation": "girl"}]}],
}


def test_a_stated_conjugation_is_kept_beside_the_page_word() -> None:
    assert page_declared_forms(SpanishDictLemmaRule(CONJ), "muerdo", MUERDO) == ["morder"]


def test_the_conjugation_table_adds_nothing_to_a_page_that_answered() -> None:
    # chica is a form of chicar in the table, but its page states no relation.
    assert page_declared_forms(SpanishDictLemmaRule(CONJ), "chica", CHICA) == []


def test_no_page_declares_nothing() -> None:
    assert page_declared_forms(SpanishDictLemmaRule(CONJ), "muerdo", None) == []


def test_analyses_come_from_spanishdict_entries_only() -> None:
    menu = {"morder": [{"headword": "morder", "pos": "VERB"}]}
    assert headword_analyses("morder", MUERDO, menu, {}) == menu["morder"]
    cache = {"morder": {"dictionary_analyses": [{"headword": "morder"}]}}
    assert headword_analyses("morder", MUERDO, {}, cache) == [{"headword": "morder"}]
    assert headword_analyses("morder", MUERDO, {}, {}) == []
