from __future__ import annotations

from fluency.wsd.sampling import is_hyphenated_compound_occurrence


def test_hyphenated_compound_guarda():
    # guarda-chuva should be skipped for card guarda
    assert is_hyphenated_compound_occurrence("Eu esqueci o guarda-chuva.", "guarda") is True
    assert is_hyphenated_compound_occurrence("Ela comprou um guarda-roupa novo.", "guarda") is True

    # Standalone guarda should be kept
    assert is_hyphenated_compound_occurrence("O guarda estava na entrada da estação.", "guarda") is False

    # Sentence with both compound and standalone should be kept
    assert is_hyphenated_compound_occurrence("O guarda esqueceu o guarda-chuva em casa.", "guarda") is False


def test_hyphenated_compound_norte():
    # norte-americanos / norte-coreano should be skipped for card norte
    assert is_hyphenated_compound_occurrence("Ele não é norte-americano.", "norte") is True
    assert is_hyphenated_compound_occurrence("Os norte-coreanos chegaram ontem.", "norte") is True

    # Standalone norte should be kept
    assert is_hyphenated_compound_occurrence("Eles viajaram para o norte de Portugal.", "norte") is False


def test_verbal_enclitics_not_treated_as_compounds():
    # Verbs followed by clitic pronouns should NOT be treated as compounds
    assert is_hyphenated_compound_occurrence("Diz-me o que aconteceu.", "diz") is False
    assert is_hyphenated_compound_occurrence("Ajuda-nos com a mudança.", "ajuda") is False
    assert is_hyphenated_compound_occurrence("Não quero preocupar-me com isso.", "preocupar") is False
    assert is_hyphenated_compound_occurrence("Eles foram-se embora cedo.", "foram") is False

    # Enclitic pronoun target itself should not be treated as compound
    assert is_hyphenated_compound_occurrence("Não digas que não, porque eu ouvi-a.", "a") is False
    assert is_hyphenated_compound_occurrence("Ele disse-me que viria.", "me") is False


def test_hyphenated_compound_second_element():
    # meia-noite should be skipped for card noite
    assert is_hyphenated_compound_occurrence("Chegamos depois da meia-noite.", "noite") is True
    assert is_hyphenated_compound_occurrence("A noite estava muito fria.", "noite") is False

    # vice-presidente should be skipped for card presidente
    assert is_hyphenated_compound_occurrence("Ele foi eleito vice-presidente.", "presidente") is True
    assert is_hyphenated_compound_occurrence("O presidente fez um pronunciamento.", "presidente") is False
