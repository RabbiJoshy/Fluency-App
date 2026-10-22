from copy import deepcopy
import unittest

from fluency.release.linked_finite_forms import correction_plan, repair_meaning


class LinkedFiniteReleaseTests(unittest.TestCase):
    def fixture(self):
        row = {"word": "foram", "pos": "verb", "lang": "Portuguese", "senses": [
            {"id": "source-ir", "glosses": ["third-person plural preterite/pluperfect indicative of ir"],
             "links": [["ir", "ir#Portuguese"]]}]}
        meaning = {"sense_id": "old-learning-id", "source_sense_id": "source-ir",
                   "headword": "foram", "translation": row["senses"][0]["glosses"][0],
                   "canonical_example": {"text": "Eles foram.", "translation": "They went."},
                   "frequency": "0.15", "metadata": {"original_evidence": "preserve"}}
        return row, meaning

    def test_preserves_identity_examples_frequency_and_evidence(self):
        row, meaning = self.fixture()
        original = deepcopy(meaning)
        plan = correction_plan([{"word": "foram", "meanings": [meaning]}], [row],
                               {"ir": "to go"}, {"ir": {"tenses": {"Pretérito": ["foram"]}}})
        result = repair_meaning(meaning, plan)
        self.assertEqual(meaning, original)
        for key in ("sense_id", "source_sense_id", "canonical_example", "frequency"):
            self.assertEqual(result[key], original[key])
        self.assertEqual(result["headword"], "ir")
        self.assertEqual(result["translation"], "to go")
        self.assertEqual(result["metadata"]["learner_cue_correction"]["scope"],
                         "verb-level-grammatical-reading")
        self.assertEqual(result["metadata"]["original_evidence"], "preserve")

    def test_rejects_form_not_verified_in_target_table(self):
        row, meaning = self.fixture()
        with self.assertRaisesRegex(ValueError, "absent"):
            correction_plan([{"word": "foram", "meanings": [meaning]}], [row],
                            {"ir": "to go"}, {"ir": {"tenses": {"Presente": ["vou"]}}})

    def test_unrelated_meaning_is_unchanged(self):
        meaning = {"translation": "ordinary lexical meaning", "sense_id": "other"}
        self.assertIs(repair_meaning(meaning, {}), meaning)
