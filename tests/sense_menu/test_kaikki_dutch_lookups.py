"""Two ways the Dutch Wiktionary menu lost entries it held (2026-10-12).

Dutch capitalises nationality words and country names, so Wiktionary has
``Amerikaanse`` and no ``amerikaanse``; exact matching found nothing. Matching
stays exact by default -- case-blind matching once read Spanish ``no`` as the
abbreviation ``NO`` -- and the surface ledger licenses a title-case row per word.

And pronominal adverbs (``ermee`` "with it") are filed as "pronominal adverb
form of met + het": read as form-of, the gloss was discarded and the card
pointed at the preposition ``met``.
"""

import json
from pathlib import Path
import tempfile
import unittest

from fluency.core.identity import create_card_record
from fluency.sense_menu.config import load_sense_menu_language_policy
from fluency.sense_menu.kaikki import KaikkiSenseMenuAdapter

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]

ROWS = [
    {"word": "Amerikaans", "lang_code": "nl", "pos": "adj", "senses": [
        {"id": "nl-amerikaans-adj", "glosses": ["American"]}]},
    {"word": "Amerikaanse", "lang_code": "nl", "pos": "adj", "senses": [{
        "glosses": ["inflection of Amerikaans:"], "tags": ["form-of", "inflection"],
        "form_of": [{"word": "Amerikaans"}]}]},
    {"word": "Amerikaanse", "lang_code": "nl", "pos": "noun", "senses": [
        {"id": "nl-amerikaanse-noun", "glosses": ["a female American"]}]},
    {"word": "NO", "lang_code": "nl", "pos": "noun", "senses": [
        {"id": "nl-NO-noun", "glosses": ["northeast"], "tags": ["abbreviation"]}]},
    {"word": "no", "lang_code": "nl", "pos": "intj", "senses": [{"id": "nl-no-intj", "glosses": ["no"]}]},
    {"word": "mijn", "lang_code": "nl", "pos": "det", "senses": [{"id": "nl-mijn-det", "glosses": ["my"]}]},
    {"word": "m'n", "lang_code": "nl", "pos": "pron", "senses": [{
        "glosses": ["contraction of mijn"], "tags": ["abbreviation", "alt-of", "contraction"],
        "alt_of": [{"word": "mijn"}]}]},
    {"word": "met", "lang_code": "nl", "pos": "prep", "senses": [{"id": "nl-met-prep", "glosses": ["with"]}]},
    {"word": "ermee", "lang_code": "nl", "pos": "adv", "senses": [{
        "glosses": ["pronominal adverb form of met + het (“with it”)"],
        "tags": ["adverb", "form-of", "pronominal"], "form_of": [{"word": "met", "extra": "+ het (“with it”)"}]}]},
    {"word": "daarna", "lang_code": "nl", "pos": "adv", "senses": [{
        "glosses": ["pronominal adverb form of na + dat; thereafter, afterwards"],
        "tags": ["adverb", "form-of", "pronominal"], "form_of": [{"word": "na", "extra": "+ dat"}]}]},
    {"word": "ervoor", "lang_code": "nl", "pos": "adv", "senses": [{
        "glosses": ["pronominal adverb form of voor + het"],
        "tags": ["adverb", "form-of", "pronominal"], "form_of": [{"word": "voor", "extra": "+ het"}]}]},
]


class DutchLookupTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.snapshot = Path(self.temporary.name) / "kaikki-dutch.jsonl"
        self.snapshot.write_text(
            "\n".join(json.dumps(r, ensure_ascii=False) for r in ROWS) + "\n", encoding="utf-8")
        self.policy = load_sense_menu_language_policy(REPOSITORY_ROOT, policy_id="nl-v1", language="nl")

    def tearDown(self):
        self.temporary.cleanup()

    def menus(self, *surfaces, external=None, title_case=()):
        adapter = KaikkiSenseMenuAdapter(
            self.snapshot, language_code="nl", language_policy=self.policy,
            external_lemmas=external, title_case_headwords=frozenset(title_case))
        cards = [create_card_record("nl", s).to_dict() for s in surfaces]
        menu, _ = adapter.build(cards, snapshot_id="fixture")
        return {
            card["surface_form"]: sorted(
                (a["headword"], a["part_of_speech"], leaf["translation"])
                for a in card["analyses"] for leaf in a["senses"])
            for card in menu["cards"]
        }

    def test_a_capitalised_entry_is_not_read_without_a_ledger_licence(self):
        self.assertEqual(self.menus("amerikaanse")["amerikaanse"], [])

    def test_the_ledger_licence_reads_the_title_case_entry_and_its_lemma(self):
        menu = self.menus(
            "amerikaanse",
            external={"amerikaanse": ["amerikaans"]},
            title_case={"amerikaanse", "amerikaans"},
        )["amerikaanse"]
        self.assertEqual(menu, [
            ("amerikaans", "adj", "American"),
            ("amerikaanse", "noun", "a female American"),
        ])

    def test_all_capital_abbreviations_stay_out_even_when_licensed(self):
        self.assertEqual(self.menus("no", title_case={"no"})["no"], [("no", "intj", "no")])

    def test_a_pronominal_adverb_keeps_its_own_meaning(self):
        menus = self.menus("ermee", "daarna", "ervoor")
        self.assertEqual(menus["ermee"], [("ermee", "adv", "with it")])
        self.assertEqual(menus["daarna"], [("daarna", "adv", "thereafter, afterwards")])
        self.assertEqual(menus["ervoor"], [("ervoor", "adv", "voor + het (pronominal adverb)")])

    def test_a_pronominal_adverb_does_not_take_the_preposition_menu(self):
        headwords = {h for h, _, _ in self.menus("ermee")["ermee"]}
        self.assertNotIn("met", headwords)

    def test_m_n_reaches_the_determiner_mijn_under_nl_v2(self):
        self.policy = load_sense_menu_language_policy(REPOSITORY_ROOT, policy_id="nl-v2", language="nl")
        self.assertEqual(self.menus("m'n")["m'n"], [("mijn", "det", "my")])

    def test_nl_v1_still_stops_m_n_at_the_part_of_speech_mismatch(self):
        self.assertEqual(self.menus("m'n")["m'n"], [])


if __name__ == "__main__":
    unittest.main()
