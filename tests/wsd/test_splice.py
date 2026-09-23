"""Carried, fresh and declared rows make one bundle the importer's contract accepts."""

import unittest

from fluency.wsd.contracts import WSDAssignment
from fluency.wsd.importer import WSDAssignmentImportError, _is_declared_default
from fluency.wsd.splice import carried_row, declared_row, sampling_from_rows, splice_bundle

CARD = "card_es_" + "a" * 32
SENTENCE = "sentence_" + "b" * 32
ANALYSIS = "analysis_" + "c" * 32
MENU = "sha256:" + "d" * 64
MENU_CARD = {
    "card_id": CARD, "surface_form": "bum",
    "analyses": [{"menu_analysis_id": ANALYSIS, "headword": "bum", "part_of_speech": "interjection",
                  "senses": [{"sense_id": "es-gloss-bum#1", "translation": "boom"}]}],
    "resolution": {"strategy": "declared_gloss", "entry": {"entry_id": "es-gloss-bum"}},
}


class SpliceTests(unittest.TestCase):
    def test_a_declared_row_is_a_valid_deterministic_assignment(self):
        row = declared_row(card_id=CARD, surface_form="bum", sentence_id=SENTENCE,
                           menu_card=MENU_CARD, sense_menu_content_id=MENU)
        assignment = WSDAssignment.from_dict(row)
        self.assertEqual((assignment.status, assignment.decision_kind), ("assigned", "deterministic_default"))
        self.assertEqual(dict(assignment.model_revisions), {})
        menu = {CARD: {ANALYSIS: ("bum", "interjection", {"es-gloss-bum#1"})}}
        self.assertTrue(_is_declared_default(assignment, menu[CARD]))

    def test_a_declared_row_is_refused_on_a_menu_with_a_choice(self):
        row = declared_row(card_id=CARD, surface_form="bum", sentence_id=SENTENCE,
                           menu_card=MENU_CARD, sense_menu_content_id=MENU)
        two = {ANALYSIS: ("bum", "interjection", {"es-gloss-bum#1", "other"})}
        with self.assertRaises(WSDAssignmentImportError):
            _is_declared_default(WSDAssignment.from_dict(row), two)
        with self.assertRaises(ValueError):
            declared_row(card_id=CARD, surface_form="bum", sentence_id=SENTENCE,
                         menu_card={**MENU_CARD, "analyses": []}, sense_menu_content_id=MENU)

    def test_a_carried_row_names_its_source_and_takes_the_new_menu(self):
        source = {"card_id": CARD, "sentence_id": SENTENCE, "status": "assigned",
                  "sense_menu_content_id": "sha256:" + "e" * 64, "evidence": {"x": 1}}
        row = carried_row(source, source_run_id="20260914T223348Z-c35194bc",
                          source_method={"profile_id": "es-v15-1"}, sense_menu_content_id=MENU)
        self.assertEqual(row["sense_menu_content_id"], MENU)
        self.assertEqual(row["evidence"]["carried"]["source_sense_menu_content_id"], "sha256:" + "e" * 64)
        self.assertEqual(row["evidence"]["x"], 1)
        self.assertEqual(source["sense_menu_content_id"], "sha256:" + "e" * 64)  # source untouched

    def test_the_bundle_accounts_for_every_occurrence_once(self):
        a = {"card_id": CARD, "sentence_id": SENTENCE, "status": "assigned"}
        b = {"card_id": CARD, "sentence_id": "sentence_" + "f" * 32, "status": "not_evaluated_example_cap"}
        bundle, report = splice_bundle(run_id="r", language="es", mode="speech", inputs={}, method={},
                                       sampling_policy={"cap": 30}, carried=[a], fresh=[b], declared=[])
        self.assertEqual(bundle["sampling"]["occurrences_considered"], 2)
        self.assertEqual(bundle["sampling"]["occurrences_not_evaluated"], 1)
        self.assertEqual(report["rows_by_origin"], {"carried": 1, "fresh": 1})
        with self.assertRaises(ValueError):
            splice_bundle(run_id="r", language="es", mode="speech", inputs={}, method={},
                          sampling_policy={}, carried=[a], fresh=[a], declared=[])
        self.assertEqual(sampling_from_rows([], {})["occurrences_considered"], 0)


if __name__ == "__main__":
    unittest.main()
