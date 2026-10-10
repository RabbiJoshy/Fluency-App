import copy
import importlib.util
import unittest
from pathlib import Path

from fluency.sense_menu.noun_merge import stamp_noun_merge

spec = importlib.util.spec_from_file_location("noun_merge_refresh", Path(__file__).resolve().parents[2] /
                                            "scripts/refresh_noun_merge_metadata.py")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
refresh = module.refresh


def fixtures(adapter="spanishdict-sense-menu/v1"):
    cards, rows = [], []
    for surface in ("gato", "gatos"):
        sense = {"translation": "cat", "definition": "animal", "source_reference": "cat-id",
                 "provider_metadata": {"context": "animal", "tags": [], "spanishdict": {}},
                 "specialist_features": []}
        analysis = {"headword": "gato", "part_of_speech": "noun", "source_adapter": adapter,
                    "provider_metadata": ({"resolution": "structured_form_of", "surface_grammar": ["plural"]}
                                          if adapter == "wiktionary-sense-menu/v1" else {"spanishdict": {}}),
                    "senses": [sense]}
        cards.append({"card_id": surface, "surface_form": surface, "analyses": [analysis]})
        rows.append({"surface_card_id": surface, "word": surface, "meanings": [
            {"source_reference": "cat-id", "translation": "cat" if surface == "gato" else "cats"}]})
    source = {"language": "es", "cards": cards}
    responses = {surface: {"word": surface, "entry_lang": "es", "flags": [], "analyses": [
        {"headword": "gato", "translation": "cat", "context": "animal", "regions": [],
         "part_of_speech_label": "noun"}], "possible_results": [
        {"headword": "gato", "heuristic": "inflection", "inflection_type": "masculine plural"}]
        if surface == "gatos" else []} for surface in ("gato", "gatos")}
    return source, rows, responses


class NounMergeRefreshTests(unittest.TestCase):
    def test_complete_spanishdict_evidence_preserves_original_menu_and_release(self):
        source, rows, responses = fixtures()
        original, original_rows = copy.deepcopy(source), copy.deepcopy(rows)
        result, report = refresh(source, rows, responses=responses)
        self.assertEqual(source, original)
        self.assertEqual(rows, original_rows)
        self.assertFalse(report["surface_failures"])
        for card in result["cards"]:
            self.assertTrue(card["noun_merge"]["allowed"])
            sense = card["analyses"][0]["senses"][0]
            self.assertEqual((sense["translation"], sense["definition"], sense["source_reference"]),
                             ("cat", "animal", "cat-id"))

    def test_extra_fresh_sense_on_either_side_blocks_both_even_after_restamping(self):
        for surface in ("gato", "gatos"):
            with self.subTest(surface=surface):
                source, rows, responses = fixtures()
                responses[surface]["analyses"].append({"headword": "gato", "translation": "jack",
                    "context": "tool", "regions": [], "part_of_speech_label": "noun"})
                result, _ = refresh(source, rows, responses=responses)
                stamp_noun_merge(result["cards"])
                self.assertTrue(all(not c["noun_merge"]["allowed"] for c in result["cards"]))

    def test_plural_only_label_blocks_pair_despite_equal_glosses(self):
        source, rows, responses = fixtures()
        responses["gatos"]["analyses"][0]["part_of_speech_label"] = "plural noun"
        result, _ = refresh(source, rows, responses=responses)
        self.assertTrue(all(not c["noun_merge"]["allowed"] for c in result["cards"]))

    def test_missing_relationship_or_flagged_response_cannot_approve(self):
        for change in ("relation", "flag"):
            with self.subTest(change=change):
                source, rows, responses = fixtures()
                if change == "relation":
                    responses["gatos"]["possible_results"] = []
                else:
                    responses["gatos"]["flags"] = ["spelling_substitution"]
                result, _ = refresh(source, rows, responses=responses)
                self.assertTrue(all(not c["noun_merge"]["allowed"] for c in result["cards"]))

    def test_mismatched_release_references_block_entire_group(self):
        source, rows, responses = fixtures()
        rows[1]["meanings"][0]["source_reference"] = "other-release-sense"
        result, _ = refresh(source, rows, responses=responses)
        stamp_noun_merge(result["cards"])
        self.assertTrue(all(not c["noun_merge"]["allowed"] for c in result["cards"]))
        self.assertEqual(result["cards"][0]["noun_merge"]["reason"], "release_menu_mismatch")

    def test_wiktionary_entry_tags_are_recovered_only_from_matching_complete_menu(self):
        source, rows, _ = fixtures("wiktionary-sense-menu/v1")
        source["language"] = "pt"
        fresh = copy.deepcopy(source)
        for card in fresh["cards"]:
            card["analyses"][0]["senses"][0]["provider_metadata"]["entry_tags"] = []
        result, _ = refresh(source, rows, fresh=fresh)
        self.assertTrue(all(c["noun_merge"]["allowed"] for c in result["cards"]))
        fresh["cards"][1]["analyses"][0]["senses"][0]["provider_metadata"]["entry_tags"] = ["plural-only"]
        result, _ = refresh(source, rows, fresh=fresh)
        self.assertTrue(all(not c["noun_merge"]["allowed"] for c in result["cards"]))
        fresh["cards"][1]["analyses"][0]["senses"][0]["translation"] = "different sense"
        result, _ = refresh(source, rows, fresh=fresh)
        stamp_noun_merge(result["cards"])
        self.assertTrue(all(not c["noun_merge"]["allowed"] for c in result["cards"]))


if __name__ == "__main__":
    unittest.main()
