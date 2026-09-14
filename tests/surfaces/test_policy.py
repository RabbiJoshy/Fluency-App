"""Evidence accumulates; verdicts are computed from it, never stored.

Every case here is one the backfill got wrong before the policy grew the rule
that fixes it. They are regression tests for real deletions that nearly
shipped, not illustrations.
"""

import unittest

from fluency.surfaces.events import build_event
from fluency.surfaces.policy import DEFAULT_POLICY, EXCLUDE, KEEP, REVIEW, verdict


def obs(code, language="pt", surface="x", evidence=None):
    phase = {"english_wordlist": "list", "accent_stripped_duplicate": "list",
             "abbreviation_form": "list", "capitalised_in_corpus": "harvest",
             "dictionary_absent": "menu", "dictionary_entry_language": "menu",
             "dictionary_pos_gloss_mismatch": "menu", "lemma_resolved": "lemma",
             "human_review": "review"}[code]
    return build_event(surface=surface, language=language, phase=phase,
                       reason_code=code, observer="test", evidence=evidence or {})


class VerdictTests(unittest.TestCase):
    def test_a_minimal_pair_is_not_a_misspelling(self) -> None:
        """"a" is the unaccented spelling of "a-grave" and also the commonest
        word in Portuguese. Treating the coincidence as grounds to exclude
        removed que, a, de, para, se and tem from the deck."""
        self.assertEqual(
            verdict([obs("accent_stripped_duplicate")], DEFAULT_POLICY)["verdict"], REVIEW)

    def test_a_sparse_dictionary_does_not_convict(self) -> None:
        """Czech Wiktionary is absent for 43% of surfaces, so "no entry" adds
        almost nothing. Combined with accent stripping it convicted policii,
        filmu and stalo -- all ordinary Czech."""
        found = verdict([obs("accent_stripped_duplicate"), obs("dictionary_absent")],
                        DEFAULT_POLICY)
        self.assertNotEqual(found["verdict"], EXCLUDE)

    def test_two_independent_reasons_convict(self) -> None:
        """An English word that SpanishDict also answers as English."""
        found = verdict([obs("english_wordlist"), obs("dictionary_entry_language")],
                        DEFAULT_POLICY)
        self.assertEqual(found["verdict"], EXCLUDE)

    def test_a_resolved_lemma_vetoes_an_exclusion(self) -> None:
        """Whatever else is suspected, a surface a morphology source resolved
        to a lemma is a word."""
        found = verdict([obs("english_wordlist"), obs("dictionary_entry_language"),
                         obs("lemma_resolved")], DEFAULT_POLICY)
        self.assertEqual(found["verdict"], REVIEW)

    def test_a_person_outranks_the_veto(self) -> None:
        found = verdict([obs("lemma_resolved"), obs("human_review")], DEFAULT_POLICY)
        self.assertEqual(found["verdict"], EXCLUDE)

    def test_silence_is_not_evidence(self) -> None:
        self.assertEqual(verdict([], DEFAULT_POLICY)["verdict"], KEEP)

    def test_the_same_observation_twice_is_one_fact(self) -> None:
        """Event ids hash the body, so re-running an observer adds nothing."""
        self.assertEqual(obs("english_wordlist")["event_id"],
                         obs("english_wordlist")["event_id"])


if __name__ == "__main__":
    unittest.main()
