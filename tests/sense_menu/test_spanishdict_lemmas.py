"""SpanishDict declares a lemma or it is not one.

Every case is a surface from the 105 cards es-speech-v15-10000x10 shipped with
an empty menu (MEND measure, 2026-09-23), and each rule exists because the
previous lemma source got that surface wrong.
"""

import unittest

from fluency.sense_menu.spanishdict_lemmas import (
    CONJUGATION_TABLE,
    ENCLITIC_HOST,
    OVERRIDE,
    PAGE_RELATION,
    PAGE_SELF,
    REFLEXIVE_HEADWORD,
    STATUS_DECLARED,
    STATUS_ENCLITIC,
    STATUS_ENCLITIC_AMBIGUOUS,
    STATUS_NO_LEMMA,
    STATUS_OVERRIDE,
    SpanishDictLemmaRule,
    load_overrides,
)

TABLE = {
    "coge": [{"lemma": "coger", "mood": "imperativo", "person": "2s"},
             {"lemma": "coger", "mood": "indicativo", "person": "3s"}],
    "toma": [{"lemma": "tomar", "mood": "imperativo", "person": "2s"}],
    "queda": [{"lemma": "quedar", "mood": "imperativo", "person": "2s"}],
    "di": [{"lemma": "decir", "mood": "imperativo", "person": "2s"},
           {"lemma": "dar", "mood": "indicativo", "person": "1s"}],
    "decir": [{"lemma": "decir", "mood": "infinitivo"}],
    "vayamos": [{"lemma": "ir", "mood": "imperativo", "person": "1p"}],
    "está": [{"lemma": "estar", "mood": "imperativo", "person": "2s"},
             {"lemma": "estar", "mood": "indicativo", "person": "3s"}],
    "dé": [{"lemma": "dar", "mood": "imperativo", "person": "3s"}],
    "conduces": [{"lemma": "conducir", "mood": "indicativo", "person": "2s"}],
    "chica": [{"lemma": "chicar", "mood": "indicativo", "person": "3s"}],
    "ve": [{"lemma": "ir", "mood": "imperativo", "person": "2s"},
           {"lemma": "ver", "mood": "imperativo", "person": "2s"}],
}
HEADWORDS = frozenset({"quedarse", "tomarse", "decirse", "irse"})


def rule(**kwargs):
    return SpanishDictLemmaRule(TABLE, known_headwords=HEADWORDS, **kwargs)


def page(*headwords, possible=(), lang="es"):
    return {"entry_lang": lang,
            "dictionary_analyses": [{"headword": h} for h in headwords],
            "possible_results": list(possible)}


class PageTests(unittest.TestCase):
    def test_punctuated_and_dotted_headwords_are_the_surface_itself(self) -> None:
        """¡Uy!, ¿Aló? and Ud. were dropped as foreign headwords; they are the word."""
        for surface, head in (("uy", "¡Uy!"), ("aló", "¿Aló?"), ("ud", "Ud."), ("sra", "Sra.")):
            found = rule().resolve(surface, page(head))
            self.assertEqual(found.status, STATUS_DECLARED)
            self.assertEqual([(l.lemma, l.provenance) for l in found.lemmas], [(head, PAGE_SELF)])

    def test_a_different_word_on_the_page_is_rejected_not_a_lemma(self) -> None:
        """tómatelo was answered with *tomate* and no substitution flag."""
        found = rule().resolve("tómatelo", page("tomate"))
        self.assertIn("tomate", found.rejected_headwords)
        self.assertNotIn("tomate", found.lemma_names)
        # ...and the enclitic rule then finds the verb, with its pronominal form.
        self.assertEqual(found.status, STATUS_ENCLITIC)
        self.assertEqual(found.lemma_names, ["tomar", "tomarse"])

    def test_a_declared_relation_is_a_lemma(self) -> None:
        found = rule().resolve("afirma", page(
            "afirmar", "afirmarse",
            possible=[{"headword": "afirmar", "heuristic": "conjugation"}]))
        self.assertEqual(found.lemma_names, ["afirmar"])
        self.assertEqual(found.lemmas[0].provenance, PAGE_RELATION)
        self.assertEqual(found.rejected_headwords, ("afirmarse",))

    def test_a_relation_the_fetch_did_not_keep_is_unknown_and_queued(self) -> None:
        """The refetch stored possible results as bare strings, losing the relation."""
        found = rule().resolve("izan", page("izar", possible=["izar"]))
        self.assertEqual(found.status, STATUS_NO_LEMMA)
        self.assertEqual(found.relation_unknown, ("izar",))
        self.assertTrue(found.needs_refetch)

    def test_every_declared_lemma_of_a_homograph_is_kept(self) -> None:
        found = rule().resolve("condones", page(
            "condones", possible=[{"headword": "condonar", "heuristic": "conjugation"},
                                  {"headword": "condón", "heuristic": "inflection"}]))
        self.assertEqual(found.lemma_names, ["condones", "condonar", "condón"])

    def test_substituted_and_english_pages_are_not_read(self) -> None:
        substituted = rule().resolve("cógelo", page("cómelo"), flags=["spelling_substitution:cómelo"])
        self.assertEqual(substituted.page_state, "substituted")
        self.assertEqual(substituted.lemma_names, ["coger"])  # via the enclitic rule
        english = rule().resolve("bum", page("bum", lang="en"))
        self.assertEqual(english.page_state, "wrong_language")
        self.assertEqual(english.status, STATUS_NO_LEMMA)
        self.assertFalse(english.needs_refetch)


class TableTests(unittest.TestCase):
    def test_table_answers_only_where_the_page_did_not(self) -> None:
        self.assertEqual(rule().resolve("conduces").lemma_names, ["conducir"])
        self.assertEqual(rule().resolve("conduces").lemmas[0].provenance, CONJUGATION_TABLE)
        # chica has its own page: the table must not add chicar (decision 0021).
        self.assertEqual(rule().resolve("chica", page("chica")).lemma_names, ["chica"])

    def test_a_table_only_lemma_for_an_unasked_surface_still_asks(self) -> None:
        """borda is a form of bordar and, in every line, the noun: ask the page."""
        found = rule().resolve("conduces")
        self.assertEqual(found.status, STATUS_DECLARED)
        self.assertTrue(found.needs_refetch)
        self.assertFalse(rule().resolve("chica", page("chica")).needs_refetch)

    def test_never_asked_and_unresolved_is_declared_and_queued(self) -> None:
        found = rule().resolve("atrevo")
        self.assertEqual(found.status, STATUS_NO_LEMMA)
        self.assertEqual(found.page_state, "unfetched")
        self.assertTrue(found.needs_refetch)


class EncliticTests(unittest.TestCase):
    def test_host_must_be_a_verb_form_of_exactly_one_verb(self) -> None:
        self.assertEqual(rule().resolve("cógelo").lemma_names, ["coger"])
        self.assertEqual(rule().resolve("decírtelo").lemmas[0].provenance, ENCLITIC_HOST)
        self.assertEqual(rule().resolve("decírtelo").lemma_names, ["decir"])

    def test_mood_removes_the_preterite_that_made_diselo_ambiguous(self) -> None:
        """di is imperative of decir and preterite of dar; only the imperative hosts."""
        self.assertEqual(rule().resolve("díselo").lemma_names, ["decir"])

    def test_two_verbs_with_a_host_form_abstain(self) -> None:
        found = rule().resolve("vete")
        self.assertEqual(found.status, STATUS_ENCLITIC_AMBIGUOUS)
        self.assertEqual(found.lemmas, ())
        self.assertEqual(found.candidates, ("ir", "ver"))

    def test_nosotros_drops_its_s_before_nos(self) -> None:
        self.assertEqual(rule().resolve("vayámonos").lemma_names, ["ir", "irse"])

    def test_accent_moves_with_the_clitic(self) -> None:
        self.assertEqual(rule().resolve("estate").lemma_names, ["estar"])
        self.assertEqual(rule().resolve("dele").lemma_names, ["dar"])

    def test_reflexive_pronoun_declares_the_pronominal_headword(self) -> None:
        found = rule().resolve("quédatelo")
        self.assertEqual(found.lemma_names, ["quedar", "quedarse"])
        self.assertEqual(found.lemmas[1].provenance, REFLEXIVE_HEADWORD)

    def test_object_pronoun_is_not_reflexive(self) -> None:
        self.assertEqual(rule().resolve("cógelo").lemma_names, ["coger"])


class OverrideTests(unittest.TestCase):
    def test_override_replaces_everything_for_its_surface(self) -> None:
        overrides = load_overrides({"schema": "lemma-overrides/v1", "language": "es", "entries": [
            {"surface": "atrevo", "lemmas": ["atreverse"], "reason": "SpanishDict answered atrezo",
             "author": "joshua", "created_at": "2026-09-23"}]})
        found = rule(overrides=overrides).resolve("atrevo", page("atrezo"))
        self.assertEqual(found.status, STATUS_OVERRIDE)
        self.assertEqual([(l.lemma, l.provenance) for l in found.lemmas], [("atreverse", OVERRIDE)])
        self.assertEqual(found.rejected_headwords, ("atrezo",))

    def test_an_override_without_provenance_or_twice_is_refused(self) -> None:
        base = {"schema": "lemma-overrides/v1", "language": "es"}
        with self.assertRaises(ValueError):
            load_overrides({**base, "entries": [{"surface": "x", "lemmas": ["y"]}]})
        entry = {"surface": "x", "lemmas": ["y"], "reason": "r", "author": "a", "created_at": "d"}
        with self.assertRaises(ValueError):
            load_overrides({**base, "entries": [entry, entry]})


if __name__ == "__main__":
    unittest.main()
