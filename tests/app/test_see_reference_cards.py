import json
from pathlib import Path
import runpy
import unittest

ROOT = Path(__file__).resolve().parents[2]
BUILDER = runpy.run_path(str(ROOT / "scripts/build_see_reference_cards.py"))


class SeeReferenceCardsTests(unittest.TestCase):
    def test_only_explicit_multiword_see_targets_are_extracted(self):
        rows = [{"meanings": [
            {"translation": "See haver de."},
            {"translation": "See ter de, ter que."},
            {"translation": "See haver."},
            {"translation": "ordinary gloss", "metadata": {"cross_references": [
                {"relation": "after_prepositions", "target": "not a see target"},
                {"relation": "see", "target": "acabar de"}]}},
        ]}]
        self.assertEqual(BUILDER["see_targets"](rows), {"haver de", "ter de", "ter que", "acabar de"})

    def test_quotations_redirects_and_misparsed_examples_are_not_definitions(self):
        senses = BUILDER["dictionary_senses"]({"pos": "verb", "senses": [
            {"glosses": ["ought to; shall", "indicates duty"], "examples": [
                {"type": "quotation", "text": "Quoted text", "translation": "Quoted translation"}]},
            {"glosses": ["A sentence. ― Its translation."]},
            {"glosses": ["See something else."]},
            {"glosses": ["to have to"], "examples": [
                {"type": "example", "text": "Tenho que preparar o café.", "translation": "I have to prepare coffee."}]},
        ]})
        self.assertEqual(len(senses), 2)
        self.assertNotIn("canonical_example", senses[0])
        self.assertEqual(senses[1]["canonical_example"]["evidence"], "dictionary")

    def test_shipped_portuguese_targets_resolve_without_becoming_occurrences(self):
        cfg = json.loads((ROOT / "app/config/config.json").read_text())["languages"]["portuguese"]
        payload = json.loads((ROOT / "app" / cfg["seeReferencesPath"]).read_text())
        self.assertEqual(payload["scope"], "see_links_only")
        self.assertEqual(payload["unresolved"], [])
        self.assertEqual(set(payload["entries"]), {"haver de", "ter de", "ter que", "acabar de"})
        for entry in payload["entries"].values():
            self.assertTrue(entry["reference_only"])
            self.assertNotIn("frequency", entry)
            self.assertNotIn("card_id", entry)
            self.assertTrue(entry["senses"])
