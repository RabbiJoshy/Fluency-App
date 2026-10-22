"""Prose-only finite forms must resolve to meanings, not grammar descriptions."""
import json
from pathlib import Path
import tempfile
import unittest

from fluency.core.identity import create_card_record
from fluency.sense_menu.config import load_sense_menu_language_policy
from fluency.sense_menu.kaikki import KaikkiSenseMenuAdapter, _normalize_linked_finite_forms


def form_row():
    return {"word": "foram", "lang": "Portuguese", "lang_code": "pt", "pos": "verb",
            "senses": [{"id": f"form-{lemma}",
                        "glosses": [f"third-person plural preterite/pluperfect indicative of {lemma}"],
                        "links": [[lemma, f"{lemma}#Portuguese"]]}
                       for lemma in ("ir", "ser")]}


class LinkedFiniteFormTests(unittest.TestCase):
    def test_both_lemmas_resolve_to_real_meanings(self):
        rows = [form_row(), *[
            {"word": lemma, "lang_code": "pt", "pos": "verb", "senses": [
                {"id": f"meaning-{lemma}", "glosses": [gloss]}]}
            for lemma, gloss in (("ir", "to go"), ("ser", "to be"))]]
        root = Path(__file__).resolve().parents[2]
        policy = load_sense_menu_language_policy(root, policy_id="pt-v1", language="pt")
        card = create_card_record("pt", "foram").to_dict()
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "source.jsonl"
            source.write_text("".join(json.dumps(row) + "\n" for row in rows))
            menu, _ = KaikkiSenseMenuAdapter(
                source, language_code="pt", language_policy=policy,
            ).build([card], snapshot_id="linked-finite-test")
        result = menu["cards"][0]
        self.assertEqual(result["surface_form"], "foram")
        self.assertEqual({(a["headword"], s["translation"])
                          for a in result["analyses"] for s in a["senses"]},
                         {("ir", "to go"), ("ser", "to be")})

    def test_requires_matching_language_link(self):
        row = form_row()
        for sense in row["senses"]:
            sense["links"] = [["other", "other#Portuguese"]]
        self.assertEqual(_normalize_linked_finite_forms(row), row)

    def test_keeps_lexical_senses_and_source_evidence(self):
        row = form_row()
        lexical = {"glosses": ["to go away"], "links": [["ir", "ir#Portuguese"]]}
        row["senses"].append(lexical)
        result = _normalize_linked_finite_forms(row)
        self.assertEqual(result["senses"][-1], lexical)
        self.assertEqual(result["senses"][0]["id"], "form-ir")
        self.assertEqual(result["senses"][0]["glosses"], row["senses"][0]["glosses"])
        self.assertIn("pluperfect", result["senses"][0]["tags"])
        self.assertNotIn("form_of", row["senses"][0])
