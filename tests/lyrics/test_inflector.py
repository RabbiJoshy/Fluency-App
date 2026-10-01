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
    # Wiktionary glosses: a note stays after the plural; a definition is left alone.
    assert pluralize_english_noun("flower (structure in angiosperms)") == "flowers (structure in angiosperms)"
    assert pluralize_english_noun("hit (success)") == "hits (success)"
    assert pluralize_english_noun("A globular buildup of carbon on the end of a wick") == "A globular buildup of carbon on the end of a wick"
    assert pluralize_english_noun("The name of the Latin-script letter Y/y.") == "The name of the Latin-script letter Y/y."


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


def test_uncountable_nouns_not_pluralized():
    """Mass/uncountable nouns like 'dark' stay singular even on plural cards."""
    assert pluralize_english_noun("dark") == "dark"
    assert pluralize_english_noun("darkness") == "darkness"
    assert pluralize_english_noun("nightfall") == "nightfall"
    assert pluralize_english_noun("sadness") == "sadness"
    assert pluralize_english_noun("information") == "information"
    assert pluralize_english_noun("furniture") == "furniture"
    assert pluralize_english_noun("music") == "music"
    assert pluralize_english_noun("weather") == "weather"
    # Countable nouns must still pluralize normally
    assert pluralize_english_noun("night") == "nights"
    assert pluralize_english_noun("evening") == "evenings"
    assert pluralize_english_noun("reason") == "reasons"


def test_inflect_card_senses_uncountable_noun():
    """A plural surface must not pluralize an uncountable English gloss."""
    senses = [
        {"headword": "noche", "pos": "NOUN", "translation": "night"},
        {"headword": "noche", "pos": "NOUN", "translation": "dark"},
        {"headword": "noche", "pos": "NOUN", "translation": "sadness"},
    ]
    res = inflect_card_senses("noches", "noche", senses, {})
    assert res[0]["translation"] == "nights"    # countable: pluralised
    assert res[1]["translation"] == "dark"       # uncountable: unchanged
    assert res[2]["translation"] == "sadness"    # uncountable: unchanged


def test_inflect_verb_with_embedded_punctuation():
    """Verb glosses with semicolons, commas, or notes must not corrupt into ';s' or ',s'."""
    assert inflect_single_verb_gloss("to be; forms the progressive aspect", "indicativo", "presente", 2) == "he/she is"
    assert inflect_single_verb_gloss("to be, to exist", "indicativo", "presente", 2) == "he/she is"
    assert inflect_single_verb_gloss("to matter; to mind", "indicativo", "presente", 2) == "he/she matters"
    assert inflect_single_verb_gloss("to mind, why don't", "indicativo", "presente", 2) == "he/she minds"

