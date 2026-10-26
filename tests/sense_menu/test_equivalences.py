from __future__ import annotations

from fluency.sense_menu.equivalences import (
    are_senses_equivalent,
    find_card_equivalences,
    stamp_sense_equivalences,
)


def test_are_senses_equivalent_geographic_sheriff():
    s1 = {
        "sense_id": "sid-1",
        "translation": "sheriff (England)",
        "part_of_speech": "noun",
    }
    s2 = {
        "sense_id": "sid-2",
        "translation": "sheriff (US)",
        "part_of_speech": "noun",
    }
    assert are_senses_equivalent(s1, s2)


def test_are_senses_equivalent_singular_plural():
    s1 = {
        "sense_id": "sid-1",
        "translation": "million",
        "part_of_speech": "noun",
    }
    s2 = {
        "sense_id": "sid-2",
        "translation": "millions",
        "part_of_speech": "noun",
    }
    assert are_senses_equivalent(s1, s2)


def test_are_senses_equivalent_unelaborated_base():
    s1 = {
        "sense_id": "sid-1",
        "translation": "piece",
        "part_of_speech": "noun",
    }
    s2 = {
        "sense_id": "sid-2",
        "translation": "piece (part of a larger whole)",
        "part_of_speech": "noun",
    }
    assert are_senses_equivalent(s1, s2)


def test_are_senses_equivalent_distinct_pos_rejected():
    s1 = {
        "sense_id": "sid-1",
        "translation": "sheriff",
        "part_of_speech": "noun",
    }
    s2 = {
        "sense_id": "sid-2",
        "translation": "sheriff",
        "part_of_speech": "verb",
    }
    assert not are_senses_equivalent(s1, s2)


def test_are_senses_equivalent_disjoint_topics_rejected():
    s1 = {
        "sense_id": "sid-1",
        "translation": "king",
        "part_of_speech": "noun",
        "provider_metadata": {"topics": ["chess"]},
    }
    s2 = {
        "sense_id": "sid-2",
        "translation": "king",
        "part_of_speech": "noun",
        "provider_metadata": {"topics": ["monarchy"]},
    }
    assert not are_senses_equivalent(s1, s2)


def test_find_and_stamp_card_equivalences():
    card = {
        "surface_form": "xerife",
        "analyses": [
            {
                "part_of_speech": "noun",
                "senses": [
                    {"sense_id": "s-sharif-1", "translation": "sharif (Moorish title)"},
                    {"sense_id": "s-sheriff-uk", "translation": "sheriff (England)"},
                    {"sense_id": "s-sharif-2", "translation": "sharif (Muslim title)"},
                    {"sense_id": "s-sheriff-us", "translation": "sheriff (US)"},
                ],
            }
        ],
    }

    stamp_sense_equivalences([card])

    assert "equivalences" in card
    groups = card["equivalences"]
    assert sorted(groups) == [
        ["s-sharif-1", "s-sharif-2"],
        ["s-sheriff-uk", "s-sheriff-us"],
    ]

    senses = card["analyses"][0]["senses"]
    assert senses[0]["provider_metadata"]["equivalent_sense_ids"] == ["s-sharif-2"]
    assert senses[1]["provider_metadata"]["equivalent_sense_ids"] == ["s-sheriff-us"]
    assert senses[2]["provider_metadata"]["equivalent_sense_ids"] == ["s-sharif-1"]
    assert senses[3]["provider_metadata"]["equivalent_sense_ids"] == ["s-sheriff-uk"]
