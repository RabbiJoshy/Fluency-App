import pytest
from fluency.lyrics.inflector import (
    inflect_verb_translation,
    pluralize_english_noun,
    split_attached_clitics,
    inflect_single_verb_gloss,
    inflect_card_senses,
)

def test_verb_gloss_infinitive_inflection():
    assert inflect_single_verb_gloss("to lose", "indicativo", "presente", 0) == "I lose"
    assert inflect_single_verb_gloss("to play", "indicativo", "pretérito perfecto simple", 0) == "I played"
    assert inflect_single_verb_gloss("to leave", "imperativo", "presente", 1, clitics=["te"]) == "leave!"

def test_verb_translation_with_leading_to():
    morph = [{"mood": "imperativo", "tense": "presente", "person": "2s"}]
    assert inflect_verb_translation("to go away; to leave", morph, clitics=["te"]) == "go away!; leave!"

def test_noun_pluralization():
    assert pluralize_english_noun("altar boy") == "altar boys"
    assert pluralize_english_noun("cat") == "cats"
    assert pluralize_english_noun("box") == "boxes"
    assert pluralize_english_noun("city") == "cities"

def test_split_attached_clitics():
    stem, clitics = split_attached_clitics("guíllate")
    assert stem == "guílla"
    assert clitics == ["te"]

    stem, clitics = split_attached_clitics("dímelo")
    assert stem == "dí"
    assert clitics == ["me", "lo"]

    stem, clitics = split_attached_clitics("hablar")
    assert stem == "hablar"
    assert clitics == []

def test_inflect_card_senses():
    senses = [
        {"gloss": "to lose; to misplace", "pos": "verb"},
    ]
    conj_rev = {
        "pierdo": [{"lemma": "perder", "mood": "indicativo", "tense": "presente", "person": "1s"}]
    }
    inflected = inflect_card_senses("pierdo", "perder", senses, conj_rev)
    assert "I lose" in inflected[0]["gloss"]
