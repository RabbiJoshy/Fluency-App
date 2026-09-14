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
             "human_review": "review", "adjudicated_keep": "review",
             "adjudicated_exclude": "review"}[code]
    return build_event(surface=surface, language=language, phase=phase,
                       reason_code=code, observer="test", evidence=evidence or {})


class VerdictTests(unittest.TestCase):
    def test_a_minimal_pair_is_not_even_a_suspicion(self) -> None:
        """"a" is the unaccented spelling of "a-grave" and also the commonest
        word in Portuguese; que/que-acute, el/el-acute and ne/ne-caron are the
        same. Differing from another surface by accents is ordinary vocabulary
        in all three languages, so it is recorded and nothing more."""
        self.assertEqual(
            verdict([obs("accent_stripped_duplicate")], DEFAULT_POLICY)["verdict"], KEEP)

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


class AdjudicationTests(unittest.TestCase):
    """Reading a case closes it, in whichever direction the reading went."""

    def test_keeping_clears_the_flag_that_raised_the_review(self) -> None:
        """Londres is capitalised because of what it names, not because it is
        foreign. If the adjudication cannot clear the flag, the queue never
        empties and the same surfaces return every time it is regenerated."""
        found = verdict([obs("capitalised_in_corpus"), obs("adjudicated_keep")],
                        DEFAULT_POLICY)
        self.assertEqual(found["verdict"], KEEP)

    def test_keeping_also_beats_a_conjunction(self) -> None:
        """"dele" is de + le; SpanishDict answered in English but the surface
        is Spanish."""
        found = verdict([obs("english_wordlist"), obs("dictionary_entry_language"),
                         obs("adjudicated_keep")], DEFAULT_POLICY)
        self.assertEqual(found["verdict"], KEEP)

    def test_excluding_is_not_undone_by_a_veto(self) -> None:
        found = verdict([obs("lemma_resolved"), obs("adjudicated_exclude")],
                        DEFAULT_POLICY)
        self.assertEqual(found["verdict"], EXCLUDE)

    def test_a_bare_dictionary_hit_is_no_longer_a_suspicion(self) -> None:
        """Webster's Second lists no, a, la, y, es, en, para, bien and dinero."""
        self.assertEqual(verdict([obs("english_wordlist")], DEFAULT_POLICY)["verdict"], KEEP)

    def test_a_conjunction_still_convicts(self) -> None:
        self.assertEqual(
            verdict([obs("english_wordlist"), obs("dictionary_entry_language")],
                    DEFAULT_POLICY)["verdict"], EXCLUDE)
