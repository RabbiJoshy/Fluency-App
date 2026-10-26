from __future__ import annotations

from fluency.sense_menu.equivalences import (
    are_senses_equivalent,
    find_card_equivalences,
)


def test_phrase_equivalences_frente():
    # frente: two "in front of"
    s1 = {
        "sense_id": "mwe:na frente de",
        "translation": "in front of",
        "part_of_speech": "PHRASE",
    }
    s2 = {
        "sense_id": "mwe:em frente a",
        "translation": "in front of",
        "part_of_speech": "PHRASE",
    }
    assert are_senses_equivalent(s1, s2)

    groups = find_card_equivalences(flat_senses=[s1, s2])
    assert groups == [["mwe:em frente a", "mwe:na frente de"]]


def test_phrase_equivalences_vez():
    # vez: two "once"
    s_once1 = {
        "sense_id": "mwe:uma vez",
        "translation": "once",
        "part_of_speech": "PHRASE",
    }
    s_once2 = {
        "sense_id": "mwe:uma vez que",
        "translation": "once",
        "part_of_speech": "PHRASE",
    }
    assert are_senses_equivalent(s_once1, s_once2)

    # vez: two "more and more"
    s_more1 = {
        "sense_id": "mwe:cada vez",
        "translation": "increasingly; more and more",
        "part_of_speech": "PHRASE",
    }
    s_more2 = {
        "sense_id": "mwe:cada vez mais",
        "translation": "more and more; increasingly",
        "part_of_speech": "PHRASE",
    }
    assert are_senses_equivalent(s_more1, s_more2)

    groups = find_card_equivalences(flat_senses=[s_once1, s_once2, s_more1, s_more2])
    assert len(groups) == 2
    assert sorted(groups[0]) == ["mwe:cada vez", "mwe:cada vez mais"]
    assert sorted(groups[1]) == ["mwe:uma vez", "mwe:uma vez que"]
