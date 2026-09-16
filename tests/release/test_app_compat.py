import json
from copy import deepcopy
from pathlib import Path
import unittest

from fluency.release.app_compat import build_app_compatibility_assets, build_app_conjugations
from fluency.release.pilot import build_pilot_deck, default_seed_path


class AppCompatibilityTests(unittest.TestCase):
    def test_clean_deck_maps_to_existing_app_contract_without_lemmas(self) -> None:
        seed = json.loads(default_seed_path().read_text(encoding="utf-8"))
        deck = build_pilot_deck(seed)
        index, examples = build_app_compatibility_assets(deck)

        self.assertEqual(len(index), 25)
        self.assertEqual(len(examples), 25)
        self.assertNotIn("lemma", index[0])
        self.assertEqual(index[0]["surface_card_id"], deck["cards"][0]["card_id"])
        self.assertEqual(index[0]["meanings"][0]["sense_id"], deck["cards"][0]["meanings"][0]["sense_id"])
        self.assertEqual(len(examples[index[0]["id"]]["m"][0]), 3)

    def test_unassigned_examples_use_the_apps_existing_sense_cycle(self) -> None:
        seed = json.loads(default_seed_path().read_text(encoding="utf-8"))
        deck = build_pilot_deck(seed)
        card = deck["cards"][0]
        card["meanings"][0]["assignment_status"] = "unassigned"
        for example in card["examples"]:
            example["assignment_status"] = "unassigned"
            example["sense_id"] = None

        index, examples = build_app_compatibility_assets(deck)
        app_card = index[0]
        app_examples = examples[app_card["id"]]

        self.assertEqual(len(app_card["meanings"]), 1)
        self.assertTrue(app_card["meanings"][0]["unassigned"])
        self.assertEqual(
            app_card["meanings"][0]["allSenses"][0]["sense_id"],
            card["meanings"][0]["sense_id"],
        )
        self.assertEqual(len(app_examples["m"][0]), 3)
        self.assertNotIn("assignment_method", app_examples["m"][0][0])

    def test_meaning_provider_metadata_reaches_the_app_contract(self) -> None:
        seed = json.loads(default_seed_path().read_text(encoding="utf-8"))
        deck = build_pilot_deck(seed)
        deck["cards"][0]["meanings"][0]["metadata"] = {
            "source_adapter": "spanishdict-sense-menu/v1",
            "sense_provider_metadata": {"translation_status": "present"},
        }
        index, _ = build_app_compatibility_assets(deck)
        self.assertEqual(
            index[0]["meanings"][0]["metadata"]["source_adapter"],
            "spanishdict-sense-menu/v1",
        )

    def test_canonical_sense_metadata_reaches_the_app_contract(self) -> None:
        seed = json.loads(default_seed_path().read_text(encoding="utf-8"))
        deck = build_pilot_deck(seed)
        envelope = {
            "contract_version": "sense-metadata/v1",
            "features": [],
            "source_metadata": {},
            "coverage": {"tags": "parsed"},
            "unclassified": [],
            "ignored": [],
        }
        deck["cards"][0]["meanings"][0]["metadata"] = {
            "source_adapter": "wiktionary-sense-menu/v1",
            "sense_metadata": envelope,
        }
        index, _ = build_app_compatibility_assets(deck)
        self.assertEqual(
            index[0]["meanings"][0]["metadata"]["sense_metadata"], envelope
        )

    def test_typed_source_document_restores_app_provenance_and_human_title(self) -> None:
        seed = json.loads(default_seed_path().read_text(encoding="utf-8"))
        deck = build_pilot_deck(seed)
        example = deck["cards"][0]["examples"][0]
        example["source"] = "opensubtitles"
        example["provenance"] = "opensubtitles"
        example["metadata"] = {
            "source": {
                "name": "opensubtitles",
                "document": {
                    "title_id": "1256443",
                    "subtitle_id": "12345",
                    "line": "77",
                },
            },
            "source_title": {
                "title": "Friends and Neighbors",
                "series": "Without a Trace",
                "year": "2009",
                "type": "tvEpisode",
            },
        }

        index, examples = build_app_compatibility_assets(deck)
        record = examples[index[0]["id"]]["m"][0][0]
        self.assertEqual(record["provenance"]["title_id"], "1256443")
        self.assertEqual(record["provenance"]["line"], "77")
        self.assertEqual(record["source_title"]["series"], "Without a Trace")

    def test_tatoeba_source_fields_reach_the_app_example_record(self) -> None:
        seed = json.loads(default_seed_path().read_text(encoding="utf-8"))
        deck = build_pilot_deck(seed)
        example = deck["cards"][0]["examples"][0]
        example["source"] = "tatoeba"
        example["provenance"] = "tatoeba"
        example["metadata"] = {
            "source": {
                "name": "tatoeba",
                "adapter": "tatoeba/v1",
                "source_record_id": "202:101",
                "url": "https://tatoeba.org/en/sentences/show/202",
                "attribution": "Tatoeba sentence #202 by Émile",
                "license": "CC BY 2.0 FR",
            },
            "target": {
                "contributor": "Émile",
                "url": "https://tatoeba.org/en/sentences/show/202",
            },
        }

        index, examples = build_app_compatibility_assets(deck)
        record = examples[index[0]["id"]]["m"][0][0]
        self.assertEqual(record["source_record_id"], "202:101")
        self.assertEqual(record["source_url"], "https://tatoeba.org/en/sentences/show/202")
        self.assertEqual(record["contributor"], "Émile")
        self.assertIn("source_record_id", record["metadata"]["source"])

    def test_partially_assigned_card_keeps_unused_menu_out_of_learner_meanings(self) -> None:
        seed = json.loads(default_seed_path().read_text(encoding="utf-8"))
        deck = build_pilot_deck(seed)
        card = deck["cards"][0]
        unused = deepcopy(card["meanings"][0])
        unused["sense_id"] = "sense_unused_menu_leaf"
        unused["translation"] = "unused alternative"
        unused["assignment_status"] = "unassigned"
        card["meanings"].append(unused)

        index, _ = build_app_compatibility_assets(deck)
        app_card = index[0]
        self.assertEqual(len(app_card["meanings"]), 1)
        self.assertEqual(app_card["meanings"][0]["frequency"], "1.000000")
        self.assertEqual(
            app_card["unused_menu_senses"][0]["sense_id"],
            "sense_unused_menu_leaf",
        )

    def test_canonical_example_reaches_assigned_and_unused_app_meanings(self) -> None:
        seed = json.loads(default_seed_path().read_text(encoding="utf-8"))
        deck = build_pilot_deck(seed)
        card = deck["cards"][0]
        chosen = {
            "text": "La vi en la calle.",
            "translation": "I saw her in the street.",
            "bold_text_offsets": [[0, 2]],
        }
        card["meanings"][0]["canonical_example"] = chosen
        unused = deepcopy(card["meanings"][0])
        unused["sense_id"] = "sense_unused_canonical"
        unused["translation"] = "unused alternative"
        unused["assignment_status"] = "unassigned"
        unused["canonical_example"] = {
            "text": "Otra frase.",
            "translation": "Another sentence.",
        }
        card["meanings"].append(unused)

        index, _ = build_app_compatibility_assets(deck)
        app_card = index[0]
        self.assertEqual(app_card["meanings"][0]["canonical_example"]["text"], chosen["text"])
        self.assertEqual(
            app_card["unused_menu_senses"][0]["canonical_example"]["text"],
            "Otra frase.",
        )

    def test_wsd_distribution_keeps_unresolved_mass_in_the_denominator(self) -> None:
        seed = json.loads(default_seed_path().read_text(encoding="utf-8"))
        deck = build_pilot_deck(seed)
        card = deck["cards"][0]
        sense_id = card["meanings"][0]["sense_id"]
        card["wsd_distribution"] = {
            "distribution_version": "wsd-distribution/v1",
            "selection_projection": "provider_only",
            "publication_projection": "supported_specificity",
            "denominator": 10,
            "published_leaf_counts": {sense_id: 2},
            "unresolved_mass": 8,
            "supported_unavailable_mass": 0,
        }

        index, _ = build_app_compatibility_assets(deck)
        self.assertEqual(index[0]["meanings"][0]["frequency"], "0.200000")
        self.assertEqual(index[0]["wsd_distribution"]["unresolved_mass"], 8)

    def test_typed_conjugations_map_to_the_existing_optional_app_shape(self) -> None:
        result = build_app_conjugations({
            "layer_version": "conjugation-layer/v1",
            "records": [{
                "headword": "hablar",
                "translation": "to speak",
                "nonfinite": {"gerund": "hablando", "past_participle": "hablado"},
                "paradigms": [{
                    "mood": "Indicativo",
                    "tense": "Presente",
                    "forms": [
                        {"person": "1s", "form": "hablo"},
                        {"person": "2s", "form": "hablas"},
                        {"person": "3s", "form": "habla"},
                        {"person": "1p", "form": "hablamos"},
                        {"person": "2p", "form": "habláis"},
                        {"person": "3p", "form": "hablan"},
                    ],
                }],
            }],
        })
        self.assertEqual(result["hablar"]["tenses"]["Presente"], [
            "hablo", "hablas", "habla", "hablamos", "habláis", "hablan",
        ])
        self.assertEqual(result["hablar"]["gerund"], "hablando")

    def test_conjugation_tense_labels_are_language_specific(self) -> None:
        portuguese = build_app_conjugations({
            "layer_version": "conjugation-layer/v1",
            "language": "pt",
            "records": [{
                "headword": "ser",
                "translation": None,
                "nonfinite": {"gerund": "sendo", "past_participle": "sido"},
                "paradigms": [
                    {"mood": "indicativo", "tense": "presente", "forms": [{"person": "1s", "form": "sou"}]},
                    {"mood": "indicativo", "tense": "pretérito-perfeito", "forms": [{"person": "1s", "form": "fui"}]},
                ],
            }],
        })
        self.assertEqual(portuguese["ser"]["tenses"]["Presente"][0], "sou")
        self.assertEqual(portuguese["ser"]["tenses"]["Pretérito"][0], "fui")

        french = build_app_conjugations({
            "layer_version": "conjugation-layer/v1",
            "language": "fr",
            "records": [{
                "headword": "être",
                "translation": None,
                "nonfinite": {"gerund": None, "past_participle": "été"},
                "paradigms": [
                    {"mood": "indicatif", "tense": "présent", "forms": [{"person": "1s", "form": "suis"}]},
                ],
            }],
        })
        self.assertEqual(french["être"]["tenses"]["Présent"][0], "suis")

        czech = build_app_conjugations({
            "layer_version": "conjugation-layer/v1",
            "language": "cs",
            "records": [{
                "headword": "být",
                "translation": "to be",
                "nonfinite": {"gerund": None, "past_participle": "byl"},
                "paradigms": [
                    {"mood": "indicative", "tense": "present", "forms": [{"person": "1s", "form": "jsem"}]},
                ],
            }],
        })
        self.assertEqual(czech["být"]["tenses"]["Present"][0], "jsem")


if __name__ == "__main__":
    unittest.main()
