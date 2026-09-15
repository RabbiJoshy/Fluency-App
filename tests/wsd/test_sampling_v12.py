import pytest
from fluency.wsd.sampling import (
    is_admissible_candidate,
    order_candidates_for_wsd,
    select_occurrences,
    OccurrenceSamplingPolicy,
)

def test_is_admissible_candidate():
    # Valid candidate
    good = {
        "sentence_id": "s1",
        "metrics": {"surface_position": 0.5, "translation_length_ratio": 1.0},
    }
    assert is_admissible_candidate(good) is True

    # Missing surface position (loose sub-token match)
    no_pos = {
        "sentence_id": "s2",
        "metrics": {"surface_position": None, "translation_length_ratio": 1.0},
    }
    assert is_admissible_candidate(no_pos) is False

    # Low length ratio (merged subtitle)
    low_ratio = {
        "sentence_id": "s3",
        "metrics": {"surface_position": 0.2, "translation_length_ratio": 0.25},
    }
    assert is_admissible_candidate(low_ratio) is False

    # High length ratio (credits / untranslated on-screen text)
    high_ratio = {
        "sentence_id": "s4",
        "metrics": {"surface_position": 0.2, "translation_length_ratio": 3.5},
    }
    assert is_admissible_candidate(high_ratio) is False


def test_order_candidates_for_wsd():
    candidates = [
        # Band 0.80 (score 2.0 + grammar 1.2 = diff 3.2)
        {
            "sentence_id": "c1",
            "tags": {"alignment": 0.81},
            "metrics": {"score": 2.0, "grammar_penalty": 1.2, "surface_position": 0.1, "translation_length_ratio": 0.9},
        },
        # Band 0.80 (score 1.0 + grammar 0.0 = diff 1.0) -> should beat c1 because diff 1.0 < 3.2
        {
            "sentence_id": "c2",
            "tags": {"alignment": 0.82},
            "metrics": {"score": 1.0, "grammar_penalty": 0.0, "surface_position": 0.3, "translation_length_ratio": 0.9},
        },
        # Band 0.90 (score 3.0 + grammar 0.0 = diff 3.0) -> higher alignment band should beat Band 0.80
        {
            "sentence_id": "c3",
            "tags": {"alignment": 0.91},
            "metrics": {"score": 3.0, "grammar_penalty": 0.0, "surface_position": 0.5, "translation_length_ratio": 1.0},
        },
        # Anomaly with ratio > 2.8 -> should be filtered
        {
            "sentence_id": "c4_bad",
            "tags": {"alignment": 0.95},
            "metrics": {"score": 0.1, "grammar_penalty": 0.0, "surface_position": 0.5, "translation_length_ratio": 4.0},
        },
    ]

    # Provide enough dummy items so floor >= 10 is tested
    dummies = [
        {
            "sentence_id": f"dummy_{i}",
            "tags": {"alignment": 0.70},
            "metrics": {"score": 1.0, "surface_position": 0.2, "translation_length_ratio": 1.0},
        }
        for i in range(10)
    ]
    all_cands = candidates + dummies
    ordered = order_candidates_for_wsd(all_cands)

    # c4_bad should be filtered out
    ordered_ids = [c["sentence_id"] for c in ordered]
    assert "c4_bad" not in ordered_ids

    # c3 (band 0.90) should come first, then c2 (band 0.80, diff 1.0), then c1 (band 0.80, diff 3.2)
    assert ordered_ids[0] == "c3"
    assert ordered_ids[1] == "c2"
    assert ordered_ids[2] == "c1"
