"""A form-of chain reaches its lemma whatever else is in the inventory.

Found building lyrics v20 (2026-09-27): ``estan`` -> ``están`` -> ``estar``
stopped at ``están`` when ``están`` was also a card, because its rows were read
in an earlier pass and only rows read in the current pass were followed. And
Spanish Wiktionary tags apocopes (``algún`` -> ``alguno``) ``abbreviation``,
which the redirect policy rejects unless ``apocopic`` allows it.
"""

import json
from pathlib import Path
import tempfile
import unittest

from fluency.core.identity import create_card_record
from fluency.sense_menu.config import load_sense_menu_language_policy
from fluency.sense_menu.kaikki import KaikkiSenseMenuAdapter

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]


def form(word, pos, target, *tags):
    return {"word": word, "lang_code": "es", "pos": pos, "senses": [{
        "glosses": [f"form of {target}"], "tags": ["form-of", *tags], "form_of": [{"word": target}]}]}


ROWS = [
    {"word": "estar", "lang_code": "es", "pos": "verb", "senses": [{"id": "es-estar-be", "glosses": ["to be"]}]},
    form("están", "verb", "estar", "third-person", "plural"),
    {"word": "estan", "lang_code": "es", "pos": "verb", "senses": [{
        "glosses": ["misspelling of están"], "tags": ["alt-of", "misspelling"], "alt_of": [{"word": "están"}]}]},
    {"word": "alguno", "lang_code": "es", "pos": "det", "senses": [{"id": "es-alguno-some", "glosses": ["some, any"]}]},
    {"word": "algún", "lang_code": "es", "pos": "det", "senses": [{
        "glosses": ["apocopic form of alguno"], "tags": ["abbreviation", "alt-of", "apocopic", "masculine"],
        "alt_of": [{"word": "alguno"}]}]},
]


class RedirectPassTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.snapshot = Path(self.temporary.name) / "kaikki-spanish.jsonl"
        self.snapshot.write_text("\n".join(json.dumps(r, ensure_ascii=False) for r in ROWS) + "\n", encoding="utf-8")
        self.adapter = KaikkiSenseMenuAdapter(
            self.snapshot, language_code="es",
            language_policy=load_sense_menu_language_policy(
                REPOSITORY_ROOT, policy_id="es-wiktionary-v1", language="es"))

    def tearDown(self):
        self.temporary.cleanup()

    def headwords(self, *surfaces):
        cards = [create_card_record("es", s).to_dict() for s in surfaces]
        menu, _ = self.adapter.build(cards, snapshot_id="fixture")
        return {card["surface_form"]: {a["headword"] for a in card["analyses"]} for card in menu["cards"]}

    def test_a_two_hop_chain_is_followed_when_the_middle_form_is_also_a_card(self):
        self.assertEqual(self.headwords("estan", "están")["estan"], {"estar"})

    def test_the_same_chain_alone(self):
        self.assertEqual(self.headwords("estan")["estan"], {"estar"})

    def test_an_apocope_reaches_its_full_form(self):
        self.assertEqual(self.headwords("algún")["algún"], {"alguno"})


if __name__ == "__main__":
    unittest.main()
