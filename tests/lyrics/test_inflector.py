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
    assert pluralize_english_noun("knife") == "knives"
    assert pluralize_english_noun("woman") == "women"
    assert pluralize_english_noun("kisses") == "kisses"
    assert pluralize_english_noun("buttocks") == "buttocks"
    assert pluralize_english_noun("things") == "things"


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


def test_inflect_card_senses_noun_plural():
    senses = [
        {"headword": "razonar", "pos": "VERB", "translation": "to reason"},
        {"headword": "razón", "pos": "NOUN", "translation": "reason"},
    ]
    # Test standard plural with accent loss (razón -> razones)
    res = inflect_card_senses("razones", "razón", senses, {})
    assert res[0]["translation"] == "to reason"  # verb untouched
    assert res[1]["translation"] == "reasons"    # noun pluralized

    # Test Caribbean elision plural (razón -> razone')
    res_elided = inflect_card_senses("razone'", "razón", senses, {})
    assert res_elided[1]["translation"] == "reasons"

    # Test explicit is_plural flag
    res_flagged = inflect_card_senses("razone'", "razón", senses, {}, is_plural=True)
    assert res_flagged[1]["translation"] == "reasons"


def test_inflect_card_senses_participle():
    conj_rev = {
        "metido": [{"lemma": "meter", "mood": "participo", "tense": "participo", "person": ""}]
    }
    senses = [
        {"headword": "metido", "pos": "ADJ", "translation": "involved"},
        {"headword": "meter", "pos": "VERB", "translation": "to put"},
    ]
    # In base participle form (surface == lemma), the verb sense inflects to 'put',
    # while the adjective sense remains unpluralized 'involved'
    res = inflect_card_senses("metido", "metido", senses, conj_rev)
    assert res[0]["translation"] == "involved"
    assert res[1]["translation"] == "put"

    # In plural form (metidos), the adjective must NOT become 'involveds'
    res_pl = inflect_card_senses("metidos", "metido", senses, conj_rev, is_plural=True)
    assert res_pl[0]["translation"] == "involved"


def test_ambiguous_forms_prefer_statement_over_command() -> None:
    from fluency.lyrics.inflector import inflect_card_senses

    # Table order is alphabetical by mood, so the command reading comes first.
    conj_rev = {
        "despeja": [
            {"lemma": "despejar", "mood": "imperativo", "tense": "afirmativo", "person": "2s"},
            {"lemma": "despejar", "mood": "indicativo", "tense": "presente", "person": "3s"},
        ],
        "condene": [
            {"lemma": "condenar", "mood": "imperativo", "tense": "afirmativo", "person": "3s"},
            {"lemma": "condenar", "mood": "subjuntivo", "tense": "presente", "person": "3s"},
        ],
        "despejad": [
            {"lemma": "despejar", "mood": "imperativo", "tense": "afirmativo", "person": "2p"},
        ],
    }
    senses = [{"pos": "VERB", "translation": "to clear", "headword": "despejar"}]
    assert inflect_card_senses("despeja", "despejar", senses, conj_rev)[0]["translation"] == "he/she clears"
    condemn = [{"pos": "VERB", "translation": "to condemn", "headword": "condenar"}]
    assert "!" not in inflect_card_senses("condene", "condenar", condemn, conj_rev)[0]["translation"]
    # A form that is only a command stays a command.
    assert inflect_card_senses("despejad", "despejar", senses, conj_rev)[0]["translation"] == "clear!"

