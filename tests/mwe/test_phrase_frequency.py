from __future__ import annotations

from fluency.mwe.builder import count_mwe_occurrences


def test_phrase_frequency_counts_inflected_verbal_matches():
    raw_candidates = {
        "ter que": {
            "translations": ["to have to"],
            "pos": "verb",
            "attach_words": ["ter", "que"],
        },
        "acabar de": {
            "translations": ["to have just"],
            "pos": "verb",
            "attach_words": ["acabar", "de"],
        },
        "por favor": {
            "translations": ["please"],
            "pos": "phrase",
            "attach_words": ["por", "favor"],
        },
    }

    # Sentences with inflected matches "temos que" and "acabei de", plus contiguous "por favor"
    targets = [
        "Nós temos que partir imediatamente.",
        "Eu acabei de comer.",
        "Um café, por favor.",
        "Não temos que nos preocupar com isso.",
    ]
    translations = [
        "We have to leave immediately.",
        "I just ate.",
        "A coffee, please.",
        "We don't have to worry about that.",
    ]

    counts, examples = count_mwe_occurrences(
        raw_candidates,
        targets,
        translations,
        lang="pt",
    )

    # Inflected matches must count toward the verbal phrase's corpus frequency
    assert counts["ter que"] == 2, f"Expected 2 matches for 'ter que' (temos que), got {counts['ter que']}"
    assert counts["acabar de"] == 1, f"Expected 1 match for 'acabar de' (acabei de), got {counts['acabar de']}"
    assert counts["por favor"] == 1, f"Expected 1 match for 'por favor', got {counts['por favor']}"

    assert len(examples["ter que"]) == 2
    assert len(examples["acabar de"]) == 1
    assert examples["ter que"][0]["pt"] == "Nós temos que partir imediatamente."
    assert examples["acabar de"][0]["pt"] == "Eu acabei de comer."
