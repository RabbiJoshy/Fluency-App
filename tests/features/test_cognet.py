"""The CogNet route: an asserted pair list read at surface level."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from fluency.features.cognates import CognatePolicy, read_relations
from fluency.features.cognet import (
    CognetPair,
    CognetSourceError,
    LemmaAnalysis,
    best_match,
    candidate_lemmas,
    read_pairs,
    read_surface_lemmas,
    score_surfaces,
)


def policy(**overrides) -> CognatePolicy:
    defaults = dict(
        target_language="cs",
        known_language="pl",
        minimum_length=3,
        length_guard=0.70,
        default_threshold=0.80,
    )
    defaults.update(overrides)
    return CognatePolicy(**defaults)


def surface_view(surfaces: dict) -> Path:
    handle = tempfile.NamedTemporaryFile("w", suffix=".json", delete=False, encoding="utf-8")
    json.dump({"language": "cs", "surfaces": surfaces}, handle, ensure_ascii=False)
    handle.close()
    return Path(handle.name)


def pair_file(rows: list[tuple[str, str, str]]) -> Path:
    handle = tempfile.NamedTemporaryFile("w", suffix=".tsv", delete=False, encoding="utf-8")
    for target, known, part in rows:
        handle.write(f"{target}\t{known}\t{part}\n")
    handle.close()
    return Path(handle.name)


class SurfaceLemmaTests(unittest.TestCase):
    def test_share_is_the_readings_frequency_over_the_total(self):
        path = surface_view(
            {
                "je": {
                    "evidence": {
                        "lemma_resolved": {
                            "analyses": [
                                {"lemma": "být", "ipm": 900.0, "pos": ["verb"]},
                                {"lemma": "oni", "ipm": 100.0, "pos": ["pronoun"]},
                            ]
                        }
                    }
                }
            }
        )
        analyses = read_surface_lemmas(path)["je"]
        self.assertEqual([a.lemma for a in analyses], ["být", "oni"])
        self.assertAlmostEqual(analyses[0].share, 0.9)
        self.assertAlmostEqual(analyses[1].share, 0.1)

    def test_repeated_lemma_rows_are_summed_not_counted_twice(self):
        path = surface_view(
            {
                "stat": {
                    "evidence": {
                        "lemma_resolved": {
                            "analyses": [
                                {"lemma": "stat", "ipm": 60.0, "pos": []},
                                {"lemma": "stat", "ipm": 30.0, "pos": ["noun"]},
                                {"lemma": "stavat", "ipm": 10.0, "pos": ["verb"]},
                            ]
                        }
                    }
                }
            }
        )
        analyses = {a.lemma: a for a in read_surface_lemmas(path)["stat"]}
        self.assertAlmostEqual(analyses["stat"].share, 0.9)
        self.assertEqual(analyses["stat"].parts_of_speech, frozenset({"noun"}))

    def test_case_differing_lemmas_are_one_lemma(self):
        path = surface_view(
            {
                "a": {
                    "evidence": {
                        "lemma_resolved": {
                            "analyses": [
                                {"lemma": "a", "ipm": 90.0, "pos": ["conjunction"]},
                                {"lemma": "A", "ipm": 10.0, "pos": ["noun"]},
                            ]
                        }
                    }
                }
            }
        )
        analyses = read_surface_lemmas(path)["a"]
        self.assertEqual(len(analyses), 1)
        self.assertAlmostEqual(analyses[0].share, 1.0)

    def test_a_provider_that_states_only_lemmas_is_still_read(self):
        """The Wiktionary form-of provider carries no frequency; that is not absence."""

        path = surface_view(
            {
                "abych": {
                    "evidence": {
                        "lemma_resolved": {
                            "lemmas": ["aby"],
                            "provider": "enwiktionary-form-of",
                        }
                    }
                }
            }
        )
        analyses = read_surface_lemmas(path)["abych"]
        self.assertEqual([a.lemma for a in analyses], ["aby"])
        self.assertAlmostEqual(analyses[0].share, 1.0)

    def test_absent_frequency_splits_evenly_rather_than_guessing(self):
        path = surface_view(
            {
                "x": {
                    "evidence": {
                        "lemma_resolved": {
                            "analyses": [{"lemma": "p"}, {"lemma": "q"}],
                        }
                    }
                }
            }
        )
        analyses = read_surface_lemmas(path)["x"]
        self.assertEqual({round(a.share, 3) for a in analyses}, {0.5})

    def test_a_surface_with_no_resolution_is_absent_not_empty(self):
        path = surface_view({"x": {"tags": ["english_wordlist"]}})
        self.assertEqual(read_surface_lemmas(path), {})

    def test_a_missing_file_says_so(self):
        with self.assertRaises(CognetSourceError):
            read_surface_lemmas(Path("/nonexistent/surfaces.json"))


class PairFileTests(unittest.TestCase):
    def test_concept_prefix_becomes_a_part_of_speech(self):
        pairs = read_pairs(pair_file([("bratr", "brat", "n"), ("brát", "brać", "v")]))
        self.assertEqual(pairs["bratr"][0].parts_of_speech, frozenset({"noun"}))
        self.assertEqual(pairs["brát"][0].parts_of_speech, frozenset({"verb"}))

    def test_one_lemma_may_be_cognate_with_several(self):
        pairs = read_pairs(pair_file([("den", "dzien", "n"), ("den", "dno", "n")]))
        self.assertEqual({p.known_lemma for p in pairs["den"]}, {"dzien", "dno"})

    def test_the_same_pair_under_two_concepts_keeps_both_parts(self):
        pairs = read_pairs(pair_file([("stav", "staw", "n"), ("stav", "staw", "v")]))
        self.assertEqual(len(pairs["stav"]), 1)
        self.assertEqual(pairs["stav"][0].parts_of_speech, frozenset({"noun", "verb"}))


class CandidateLemmaTests(unittest.TestCase):
    """The one-to-many gate: which readings may speak for a surface."""

    def test_a_minority_reading_is_refused(self):
        analyses = [LemmaAnalysis("být", 0.94, frozenset()), LemmaAnalysis("oni", 0.06, frozenset())]
        kept = candidate_lemmas("je", analyses, policy(lemma_share_floor=0.9))
        self.assertEqual([a.lemma for a in kept], ["být"])

    def test_a_surface_always_speaks_for_itself(self):
        # ``den`` is a minority reading of ``den`` only because the surface is
        # also an inflection of something else; it is still the word itself.
        analyses = [LemmaAnalysis("dno", 0.7, frozenset()), LemmaAnalysis("den", 0.3, frozenset())]
        kept = {a.lemma for a in candidate_lemmas("den", analyses, policy(lemma_share_floor=0.9))}
        self.assertEqual(kept, {"den"})

    def test_a_lower_floor_admits_more(self):
        analyses = [LemmaAnalysis("a", 0.6, frozenset()), LemmaAnalysis("b", 0.4, frozenset())]
        self.assertEqual(len(candidate_lemmas("x", analyses, policy(lemma_share_floor=0.3))), 2)


class MatchTests(unittest.TestCase):
    def test_meaning_is_asserted_so_the_score_is_the_form(self):
        match = best_match(
            "bratr",
            [LemmaAnalysis("bratr", 1.0, frozenset({"noun"}))],
            {"bratr": (CognetPair("brat", frozenset({"noun"})),)},
            {},
            policy(),
        )
        assert match is not None
        self.assertEqual(match.known_surface, "brat")
        # combine() with meaning 1.0 is form x (floor + weight) = form x 1.0
        self.assertAlmostEqual(match.score, match.form)

    def test_the_known_side_is_expanded_so_forms_meet_forms(self):
        """``bratra`` vs ``brat`` fails the length guard; vs ``brata`` it does not."""

        bare = best_match(
            "bratra",
            [LemmaAnalysis("bratr", 1.0, frozenset())],
            {"bratr": (CognetPair("brat", frozenset()),)},
            {},
            policy(),
        )
        self.assertIsNone(bare)

        expanded = best_match(
            "bratra",
            [LemmaAnalysis("bratr", 1.0, frozenset())],
            {"bratr": (CognetPair("brat", frozenset()),)},
            {"brat": frozenset({"brat", "brata", "bratu"})},
            policy(),
        )
        assert expanded is not None
        self.assertEqual(expanded.known_surface, "brata")

    def test_a_minority_lemma_cannot_carry_a_surface(self):
        match = best_match(
            "je",
            [LemmaAnalysis("být", 0.94, frozenset()), LemmaAnalysis("oni", 0.06, frozenset())],
            {"oni": (CognetPair("oni", frozenset()),)},
            {},
            policy(minimum_length=2),
        )
        self.assertIsNone(match)

    def test_part_of_speech_disagreement_is_refused_when_asked(self):
        arguments = (
            "stavu",
            [LemmaAnalysis("stav", 1.0, frozenset({"noun"}))],
            {"stav": (CognetPair("stawiac", frozenset({"verb"})),)},
            {},
            policy(),
        )
        self.assertIsNotNone(best_match(*arguments))
        self.assertIsNone(best_match(*arguments, require_pos_agreement=True))

    def test_unknown_part_of_speech_is_not_disagreement(self):
        match = best_match(
            "bratr",
            [LemmaAnalysis("bratr", 1.0, frozenset())],
            {"bratr": (CognetPair("brat", frozenset({"noun"})),)},
            {},
            policy(),
            require_pos_agreement=True,
        )
        self.assertIsNotNone(match)

    def test_a_surface_shorter_than_the_minimum_is_never_scored(self):
        match = best_match(
            "on",
            [LemmaAnalysis("on", 1.0, frozenset())],
            {"on": (CognetPair("on", frozenset()),)},
            {},
            policy(minimum_length=3),
        )
        self.assertIsNone(match)

    def test_the_best_of_several_known_forms_wins(self):
        match = best_match(
            "hlavni",
            [LemmaAnalysis("hlavni", 1.0, frozenset())],
            {"hlavni": (CognetPair("glowny", frozenset()),)},
            {"glowny": frozenset({"glowny", "hlavni", "glownego"})},
            policy(),
        )
        assert match is not None
        self.assertEqual(match.known_surface, "hlavni")
        self.assertAlmostEqual(match.score, 1.0)


class ScoreSurfacesTests(unittest.TestCase):
    def test_only_surfaces_with_an_asserted_pair_are_scored(self):
        scored = score_surfaces(
            {
                "bratr": (LemmaAnalysis("bratr", 1.0, frozenset()),),
                "stul": (LemmaAnalysis("stul", 1.0, frozenset()),),
            },
            {"bratr": (CognetPair("brat", frozenset()),)},
            {},
            policy(),
        )
        self.assertEqual(set(scored), {"bratr"})

    def test_provenance_survives_into_the_record(self):
        scored = score_surfaces(
            {"bratr": (LemmaAnalysis("bratr", 1.0, frozenset()),)},
            {"bratr": (CognetPair("brat", frozenset()),)},
            {},
            policy(),
        )
        record = scored["bratr"].to_dict()
        self.assertEqual(record["meaning_source"], "cognet")
        self.assertEqual(record["meaning"], 1.0)
        self.assertEqual(record["target_lemma"], "bratr")


class RelationReuseTests(unittest.TestCase):
    """The known-side expansion is the same walk ``expand_surfaces`` makes."""

    def test_forms_by_lemma_inverts_both_recorded_directions(self):
        entries = [
            {
                "word": "brat",
                "pos": "noun",
                "senses": [{"glosses": ["brother"]}],
                "forms": [{"form": "brata"}],
            },
            {
                "word": "bratu",
                "pos": "noun",
                "senses": [{"glosses": ["dative of brat"], "form_of": [{"word": "brat"}]}],
            },
        ]
        forms = read_relations(entries, policy()).forms_by_lemma()
        self.assertEqual(forms["brat"], frozenset({"brat", "brata", "bratu"}))


if __name__ == "__main__":
    unittest.main()


class MergeTests(unittest.TestCase):
    """Folding CogNet into a scored layer keeps the better of the two routes."""

    def layer(self) -> dict:
        return {
            "language": "cs",
            "known_languages": ["pl"],
            "policies": {"pl": {"default_threshold": 0.8}},
            "coverage": {"pl": {"deck_surfaces": 3}},
            "scores": {
                "sklep": {"pl": {"known_word": "sklep", "score": 0.18}},
                "stopa": {"pl": {"known_word": "stopa", "score": 0.92}},
            },
        }

    def test_a_better_cognet_score_replaces_a_weaker_gloss_score(self):
        from fluency.enrichments.cognates import merge_cognet_scores

        merged = merge_cognet_scores(
            self.layer(),
            {"pl": {"sklep": {"known_surface": "sklep", "score": 0.95, "meaning_source": "cognet"}}},
        )
        self.assertEqual(merged["scores"]["sklep"]["pl"]["score"], 0.95)
        self.assertEqual(merged["scores"]["sklep"]["pl"]["meaning_source"], "cognet")

    def test_a_weaker_cognet_score_does_not_displace_a_stronger_one(self):
        from fluency.enrichments.cognates import merge_cognet_scores

        merged = merge_cognet_scores(
            self.layer(),
            {"pl": {"stopa": {"known_surface": "stopą", "score": 0.5, "meaning_source": "cognet"}}},
        )
        self.assertEqual(merged["scores"]["stopa"]["pl"]["score"], 0.92)
        self.assertEqual(merged["scores"]["stopa"]["pl"]["meaning_source"], "glosses")

    def test_a_surface_the_gloss_route_never_saw_is_added(self):
        from fluency.enrichments.cognates import merge_cognet_scores

        merged = merge_cognet_scores(
            self.layer(),
            {"pl": {"owoce": {"known_surface": "owoce", "score": 1.0, "meaning_source": "cognet"}}},
        )
        self.assertIn("owoce", merged["scores"])
        self.assertEqual(merged["coverage"]["pl"]["cognet_adopted_surfaces"], 1)

    def test_the_original_layer_is_not_mutated(self):
        from fluency.enrichments.cognates import merge_cognet_scores

        original = self.layer()
        merge_cognet_scores(
            original,
            {"pl": {"sklep": {"known_surface": "sklep", "score": 0.95, "meaning_source": "cognet"}}},
        )
        self.assertEqual(original["scores"]["sklep"]["pl"]["score"], 0.18)
        self.assertNotIn("meaning_source", original["scores"]["sklep"]["pl"])

    def test_a_new_known_language_is_declared(self):
        from fluency.enrichments.cognates import merge_cognet_scores

        merged = merge_cognet_scores(
            self.layer(),
            {"sk": {"stopa": {"known_surface": "stopa", "score": 0.9, "meaning_source": "cognet"}}},
        )
        self.assertEqual(merged["known_languages"], ["pl", "sk"])


class LedgerTests(unittest.TestCase):
    """A ledger has already elected the lemma; this route honours the election."""

    def ledger(self, surfaces: dict) -> Path:
        handle = tempfile.NamedTemporaryFile("w", suffix=".json", delete=False, encoding="utf-8")
        json.dump({"language": "cs", "surfaces": surfaces}, handle, ensure_ascii=False)
        handle.close()
        return Path(handle.name)

    def test_the_elected_lemma_speaks_for_the_surface(self):
        from fluency.features.cognet import read_ledger

        path = self.ledger({"je": {"lemma": "být", "verdict": "keep"}})
        analyses = read_ledger(path)["je"]
        self.assertEqual(analyses[0].lemma, "být")
        self.assertEqual(analyses[0].share, 1.0)

    def test_alternates_are_carried_but_do_not_speak_alone(self):
        from fluency.features.cognet import read_ledger

        path = self.ledger(
            {
                "je": {
                    "lemma": "být",
                    "verdict": "keep",
                    "lemma_alternates": [{"lemma": "oni", "provenance": "CNK"}],
                }
            }
        )
        analyses = {a.lemma: a.share for a in read_ledger(path)["je"]}
        self.assertEqual(analyses["být"], 1.0)
        self.assertEqual(analyses["oni"], 0.0)

    def test_a_surface_the_ledger_excluded_is_never_scored(self):
        from fluency.features.cognet import read_ledger

        path = self.ledger({"fscx100": {"lemma": "fscx100", "verdict": "exclude"}})
        self.assertEqual(read_ledger(path), {})

    def test_a_surface_with_no_elected_lemma_is_absent(self):
        from fluency.features.cognet import read_ledger

        path = self.ledger({"x": {"verdict": "keep"}})
        self.assertEqual(read_ledger(path), {})

    def test_part_of_speech_rides_along_with_the_election(self):
        from fluency.features.cognet import read_ledger

        path = self.ledger({"pes": {"lemma": "pes", "verdict": "keep", "part_of_speech": ["noun"]}})
        self.assertEqual(read_ledger(path)["pes"][0].parts_of_speech, frozenset({"noun"}))

    def test_a_missing_ledger_says_so(self):
        from fluency.features.cognet import CognetSourceError, read_ledger

        with self.assertRaises(CognetSourceError):
            read_ledger(Path("/nonexistent/ledger.json"))


class PerLemmaTests(unittest.TestCase):
    """Form at the surface, cognateness at the lemma, keyed on both."""

    def rows(self, **overrides):
        from fluency.features.cognet import score_pairs

        # ``stavu`` is both a case of ``stav`` and a form of ``stavit``. The
        # shares are lopsided; under (surface, lemma) keying neither has to win.
        settings = dict(
            surface_lemmas={
                "stavu": (
                    LemmaAnalysis("stav", 1.0, frozenset()),
                    LemmaAnalysis("stavit", 0.0, frozenset()),
                ),
            },
            pairs={"stavit": (CognetPair("stawic", frozenset()),)},
            known_forms={},
            policy=policy(),
        )
        settings.update(overrides)
        return score_pairs(**settings)

    def test_a_minority_lemma_no_longer_has_to_be_discarded(self):
        """Its share is 0.0 and it still gets a row; nothing is elected away."""

        rows = self.rows()
        self.assertEqual(set(rows["stavu"]), {"stavit"})
        self.assertEqual(rows["stavu"]["stavit"].lemma_share, 0.0)

    def test_each_lemma_gets_its_own_verdict(self):
        rows = self.rows(
            pairs={
                "stavit": (CognetPair("stawic", frozenset()),),
                "stav": (CognetPair("stawu", frozenset()),),
            }
        )
        self.assertEqual(set(rows["stavu"]), {"stavit", "stav"})
        self.assertNotEqual(
            rows["stavu"]["stav"].score, rows["stavu"]["stavit"].score
        )

    def test_a_surface_no_lemma_can_speak_for_is_absent(self):
        self.assertEqual(self.rows(pairs={}), {})

    def test_the_length_guard_still_applies_per_row(self):
        """``je``/``oni`` is 0.667 on min/max and is refused, as it should be."""

        self.assertEqual(
            self.rows(
                surface_lemmas={"je": (LemmaAnalysis("oni", 0.0, frozenset()),)},
                pairs={"oni": (CognetPair("oni", frozenset()),)},
                policy=policy(minimum_length=2),
            ),
            {},
        )

    def test_form_is_measured_at_the_surface_not_the_lemma(self):
        """``hoteles`` is scored against ``hotels``, never ``hotel``/``hotel``."""

        from fluency.features.cognet import score_pairs

        rows = score_pairs(
            {"hoteles": (LemmaAnalysis("hotel", 1.0, frozenset()),)},
            {"hotel": (CognetPair("hotel", frozenset()),)},
            {"hotel": frozenset({"hotel", "hotels"})},
            policy(known_language="en"),
        )
        match = rows["hoteles"]["hotel"]
        self.assertEqual(match.known_surface, "hotels")
        self.assertLess(match.score, 1.0)


class AppPayloadTests(unittest.TestCase):
    def payload(self):
        from fluency.enrichments.cognates import build_app_cognet

        return build_app_cognet(
            language="cs",
            rows={
                "en": {"doktor": {"doktor": {"score": 0.917}}},
                "pl": {"doktor": {"doktor": {"score": 0.95}}, "ale": {"ale": {"score": 0.917}}},
            },
            thresholds={"en": 0.75, "pl": 0.8},
        )

    def test_the_outer_key_is_still_the_surface(self):
        """Card identity is the surface; the lemma is a dimension of the verdict."""

        self.assertEqual(set(self.payload()["scores"]), {"doktor", "ale"})

    def test_a_surface_carries_its_lemmas_and_each_lemma_its_languages(self):
        scores = self.payload()["scores"]
        self.assertEqual(scores["doktor"]["doktor"], {"en": 0.917, "pl": 0.95})

    def test_known_languages_are_declared_not_inferred(self):
        payload = self.payload()
        self.assertEqual(payload["known_languages"], ["en", "pl"])
        # v2.1 is v2 plus the matched word; the route is unchanged, so readers
        # test the prefix rather than the exact string.
        self.assertEqual(payload["schema"], "cognate-score/v2.1")
        self.assertTrue(payload["schema"].startswith("cognate-score/v2"))

    def test_the_matched_word_travels_with_the_lemma_that_scored_it(self):
        from fluency.enrichments.cognates import build_app_cognet

        payload = build_app_cognet(
            language="cs",
            rows={
                "en": {"doktor": {"doktor": {"score": 0.917, "known_word": "doctor"}}},
                # No known_word here: the file must not invent one.
                "pl": {"doktor": {"doktor": {"score": 0.95}}},
            },
            thresholds={"en": 0.75, "pl": 0.8},
        )
        self.assertEqual(payload["matches"]["doktor"]["doktor"], {"en": "doctor"})
        self.assertEqual(payload["scores"]["doktor"]["doktor"], {"en": 0.917, "pl": 0.95})

    def test_a_language_that_scored_nothing_for_a_surface_is_simply_absent(self):
        self.assertEqual(self.payload()["scores"]["ale"]["ale"], {"pl": 0.917})
