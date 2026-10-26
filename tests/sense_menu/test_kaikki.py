import json
from pathlib import Path
import tempfile
import unittest

from fluency.core.identity import create_card_record
from fluency.sense_menu.config import load_sense_menu_language_policy
from fluency.sense_menu.kaikki import (
    ADAPTER_ID,
    KaikkiSenseMenuAdapter,
    _cross_references,
    _display_gloss,
    _metadata,
)


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]


def form_sense(base, sense_id):
    return {
        "id": sense_id,
        "glosses": [f"inflection of {base}"],
        "tags": ["form-of", "indicative", "present"],
        "form_of": [{"word": base}],
    }


class KaikkiSenseMenuTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.snapshot = Path(self.temporary.name) / "kaikki-french.jsonl"
        self.policy = load_sense_menu_language_policy(
            REPOSITORY_ROOT, policy_id="fr-v1", language="fr"
        )
        rows = [
            {
                "word": "être",
                "lang_code": "fr",
                "pos": "noun",
                "senses": [{"id": "en-etre-fr-noun-being", "glosses": ["a being"]}],
            },
            {
                "word": "être",
                "lang_code": "fr",
                "pos": "verb",
                "senses": [
                    {
                        "id": "en-etre-fr-verb-be",
                        "glosses": ["to be", "exist or have identity"],
                        "raw_glosses": ["to be"],
                        "tags": [],
                    }
                ],
            },
            {
                "word": "suivre",
                "lang_code": "fr",
                "pos": "verb",
                "senses": [
                    {
                        "id": "en-suivre-fr-verb-follow",
                        "glosses": ["to follow"],
                        "topics": ["movement", "transport"],
                        "tags": ["masculine", "slang", "transitive"],
                    }
                ],
            },
            {
                "word": "est",
                "lang_code": "fr",
                "pos": "noun",
                "senses": [
                    {
                        "id": "en-est-fr-noun-east",
                        "glosses": ["east"],
                        "tags": ["masculine"],
                    }
                ],
            },
            {
                "word": "est",
                "lang_code": "fr",
                "pos": "verb",
                "senses": [form_sense("être", "en-est-fr-verb-form")],
            },
            {
                "word": "suis",
                "lang_code": "fr",
                "pos": "verb",
                "senses": [
                    form_sense("être", "en-suis-fr-etre-form"),
                    form_sense("suivre", "en-suis-fr-suivre-form"),
                ],
            },
            {
                "word": "suis",
                "lang_code": "es",
                "pos": "noun",
                "senses": [{"id": "wrong-language", "glosses": ["noise"]}],
            },
            {
                "word": "de",
                "lang_code": "fr",
                "pos": "prep",
                "senses": [{"id": "en-de-fr-prep-of", "glosses": ["of"]}],
            },
            {
                "word": "de",
                "lang_code": "fr",
                "pos": "noun",
                "senses": [
                    {
                        "id": "en-de-fr-abbreviation-dame",
                        "glosses": ["abbreviation of dame"],
                        "tags": ["abbreviation", "alt-of"],
                        "alt_of": [{"word": "dame"}],
                    }
                ],
            },
            {
                "word": "dame",
                "lang_code": "fr",
                "pos": "noun",
                "senses": [{"id": "en-dame-fr-noun-lady", "glosses": ["lady"]}],
            },
            {
                "word": "cette",
                "lang_code": "fr",
                "pos": "det",
                "senses": [{"id": "en-cette-fr-det-this", "glosses": ["this"]}],
            },
            {
                "word": "Cette",
                "lang_code": "fr",
                "pos": "name",
                "senses": [
                    {
                        "id": "en-cette-fr-name-sete",
                        "glosses": ["former spelling of Sète"],
                        "tags": ["alt-of"],
                        "alt_of": [{"word": "Sète"}],
                    }
                ],
            },
            {
                "word": "Sète",
                "lang_code": "fr",
                "pos": "name",
                "senses": [{"id": "en-sete-fr-name-city", "glosses": ["a city in France"]}],
            },
        ]
        with self.snapshot.open("w", encoding="utf-8") as stream:
            for row in rows:
                stream.write(json.dumps(row, ensure_ascii=False) + "\n")

    def tearDown(self):
        self.temporary.cleanup()

    def test_only_explicit_see_glosses_become_cross_references(self):
        self.assertEqual(
            _cross_references({"glosses": ["See ter de, ter que."]}),
            [
                {"relation": "see", "target": "ter de"},
                {"relation": "see", "target": "ter que"},
            ],
        )
        self.assertEqual(
            _cross_references({"glosses": ["to see you tomorrow"]}),
            [],
        )
        self.assertEqual(
            _metadata({}, {"glosses": ["See haver de."]})["cross_references"],
            [{"relation": "see", "target": "haver de"}],
        )

    def test_pointer_glosses_resolve_to_target_entry_meaning(self):
        from fluency.sense_menu.kaikki import _resolve_pointer_gloss
        rows_by_word = {
            "ter de": [{"pos": "verb", "senses": [{"glosses": ["to have to (indicates obligation)"]}]}],
            "acabar de": [{"pos": "verb", "senses": [{"glosses": ["to have just (indicates recency)"]}]}],
            "embaixo": [{"pos": "adv", "senses": [{"glosses": ["below, down"]}]}],
        }
        self.assertEqual(
            _resolve_pointer_gloss({"glosses": ["See ter de, ter que."]}, rows_by_word),
            "to have to",
        )
        self.assertEqual(
            _resolve_pointer_gloss({"glosses": ["See acabar de."]}, rows_by_word),
            "to have just",
        )
        self.assertEqual(
            _resolve_pointer_gloss({"glosses": ["European Portuguese standard spelling of embaixo"]}, rows_by_word),
            "below, down",
        )
        self.assertIsNone(
            _resolve_pointer_gloss({"glosses": ["synonym of perfectum"]}, rows_by_word),
        )

    def test_object_pronoun_gloss_exposes_typed_card_references(self):
        sense = {
            "glosses": [
                "him, it (as a direct object; as an indirect object, see lhe; "
                "after prepositions, see ele)"
            ]
        }
        self.assertEqual(_display_gloss(sense), "him, it")
        self.assertEqual(_cross_references(sense), [
            {"relation": "indirect_object", "target": "lhe"},
            {"relation": "after_prepositions", "target": "ele"},
        ])

    def test_form_of_targets_become_explicit_headword_pos_tuples(self):
        cards = [
            {**create_card_record("fr", "suis").to_dict(), "rank": 1},
            {**create_card_record("fr", "est").to_dict(), "rank": 2},
        ]
        menu, report = KaikkiSenseMenuAdapter(
            self.snapshot, language_policy=self.policy
        ).build(
            cards, snapshot_id="fixture-2026-08"
        )
        by_surface = {card["surface_form"]: card for card in menu["cards"]}
        suis = by_surface["suis"]["analyses"]
        self.assertEqual(
            {(item["headword"], item["part_of_speech"]) for item in suis},
            {("être", "verb"), ("suivre", "verb")},
        )

        self.assertEqual(
            {item["senses"][0]["translation"] for item in suis},
            {"to be", "to follow"},
        )
        self.assertTrue(
            all(item["provider_metadata"]["resolution"] == "structured_form_of" for item in suis)
        )
        etre = next(item for item in suis if item["headword"] == "être")
        surface_features = {
            (feature["family"], feature["kind"], feature["value"])
            for feature in etre["senses"][0]["specialist_features"]
        }
        self.assertIn(("grammar", "surface_mark", "mood=indicative"), surface_features)
        self.assertEqual(report["fallbacks"], [])
        self.assertEqual(report["cards_without_menu"], 0)

    def test_external_lemma_does_not_broaden_a_declared_verb_form_to_noun(self):
        adapter = KaikkiSenseMenuAdapter(self.snapshot, language_policy=self.policy,
                                        external_lemmas={'suis': ['être', 'suivre']})
        cards = [{**create_card_record('fr', 'suis').to_dict(), 'rank': 1}]
        menu, _ = adapter.build(cards, snapshot_id='fixture')
        self.assertEqual({(a['headword'], a['part_of_speech']) for a in menu['cards'][0]['analyses']},
                         {('être', 'verb'), ('suivre', 'verb')})
        self.assertEqual(adapter.direct_form_positions({'suis'})['suis']['être'], {'verb'})

    def test_external_missing_first_hop_is_not_given_an_invented_pos(self):
        adapter = KaikkiSenseMenuAdapter(self.snapshot, language_policy=self.policy,
                                        external_lemmas={'unknown': ['être']})
        cards = [{**create_card_record('fr', 'unknown').to_dict(), 'rank': 1}]
        menu, _ = adapter.build(cards, snapshot_id='fixture')
        self.assertEqual({a['part_of_speech'] for a in menu['cards'][0]['analyses']}, {'noun', 'verb'})

    def test_multiple_explicit_pos_relations_to_same_lemma_are_preserved(self):
        with self.snapshot.open('a') as f:
            f.write(json.dumps({'word':'suis','lang_code':'fr','pos':'noun',
                                'senses':[form_sense('être','noun-form')]})+'\n')
        adapter = KaikkiSenseMenuAdapter(self.snapshot, language_policy=self.policy,
                                        external_lemmas={'suis': ['être']})
        cards = [{**create_card_record('fr', 'suis').to_dict(), 'rank': 1}]
        menu, _ = adapter.build(cards, snapshot_id='fixture')
        self.assertEqual({a['part_of_speech'] for a in menu['cards'][0]['analyses'] if a['headword']=='être'},
                         {'noun', 'verb'})

    def test_separate_indirect_noun_path_survives_direct_verb_constraint(self):
        with self.snapshot.open('a') as f:
            for row in [
                {'word':'suis','lang_code':'fr','pos':'noun','senses':[form_sense('variant','noun-variant')]},
                {'word':'variant','lang_code':'fr','pos':'noun','senses':[form_sense('être','noun-base')]},
            ]:
                f.write(json.dumps(row)+'\n')
        adapter = KaikkiSenseMenuAdapter(self.snapshot, language_policy=self.policy,
                                        external_lemmas={'suis':['être','suivre']})
        cards = [{**create_card_record('fr','suis').to_dict(),'rank':1}]
        menu,_ = adapter.build(cards,snapshot_id='fixture')
        self.assertEqual({a['part_of_speech'] for a in menu['cards'][0]['analyses'] if a['headword']=='être'},
                         {'noun','verb'})

    def test_direct_homograph_and_form_of_headword_both_survive(self):
        cards = [{**create_card_record("fr", "est").to_dict(), "rank": 1}]
        menu, _ = KaikkiSenseMenuAdapter(
            self.snapshot, language_policy=self.policy
        ).build(
            cards, snapshot_id="fixture-2026-08"
        )
        analyses = menu["cards"][0]["analyses"]
        self.assertEqual(
            {(item["headword"], item["part_of_speech"]) for item in analyses},
            {("est", "noun"), ("être", "verb")},
        )
        translations = {
            sense["translation"]
            for analysis in analyses
            for sense in analysis["senses"]
        }
        self.assertEqual(translations, {"east", "to be"})
        self.assertNotIn("inflection of être", translations)

    def test_output_exposes_provider_ids_metadata_and_snapshot_hash(self):
        cards = [{**create_card_record("fr", "est").to_dict(), "rank": 1}]
        menu, _ = KaikkiSenseMenuAdapter(
            self.snapshot, language_policy=self.policy
        ).build(
            cards, snapshot_id="fixture-2026-08"
        )
        self.assertEqual(menu["source_adapter"], ADAPTER_ID)
        self.assertEqual(menu["metadata_contract"], "sense-metadata/v1")
        self.assertEqual(menu["language_policy_id"], "fr-v1")
        self.assertTrue(menu["language_policy_content_id"].startswith("sha256:"))
        self.assertTrue(menu["snapshot_content_id"].startswith("sha256:"))
        leaf = next(
            sense
            for analysis in menu["cards"][0]["analyses"]
            if analysis["headword"] == "est"
            for sense in analysis["senses"]
        )
        self.assertEqual(leaf["sense_id"], "en-est-fr-noun-east")
        self.assertEqual(leaf["source_reference"], "kaikki:en-est-fr-noun-east")
        self.assertEqual(leaf["provider_metadata"]["tags"], ["masculine"])
        self.assertEqual(leaf["provider_metadata"]["part_of_speech"], "noun")
        self.assertEqual(leaf["metadata"]["contract_version"], "sense-metadata/v1")
        self.assertEqual(leaf["metadata"]["features"], leaf.get("specialist_features", []))
        self.assertEqual(leaf["metadata"]["coverage"]["tags"], "parsed")
        self.assertEqual(leaf["provider_metadata"]["examples"], [])
        self.assertEqual(leaf["provider_metadata"]["cross_references"], [])
        self.assertEqual(leaf["provider_metadata"]["info_templates"], [])

    def test_topics_and_semantic_tags_become_normalized_specialist_features(self):
        cards = [{**create_card_record("fr", "suis").to_dict(), "rank": 1}]
        menu, _ = KaikkiSenseMenuAdapter(
            self.snapshot, language_policy=self.policy
        ).build(cards, snapshot_id="fixture-2026-08")
        leaf = next(
            sense
            for analysis in menu["cards"][0]["analyses"]
            if analysis["headword"] == "suivre"
            for sense in analysis["senses"]
        )
        features = {
            (item["family"], item["kind"], item["value"])
            for item in leaf["specialist_features"]
        }
        self.assertIn(("domain", "topic", "movement"), features)
        self.assertIn(("domain", "topic", "transport"), features)
        self.assertIn(("register", "usage_tag", "slang"), features)
        self.assertIn(("construction", "grammar_tag", "transitive"), features)
        self.assertFalse(any(value == "masculine" for _, _, value in features))

    def test_abbreviation_redirect_does_not_expand_an_unrelated_headword(self):
        cards = [{**create_card_record("fr", "de").to_dict(), "rank": 1}]
        menu, _ = KaikkiSenseMenuAdapter(
            self.snapshot, language_policy=self.policy
        ).build(cards, snapshot_id="fixture-2026-08")
        analyses = menu["cards"][0]["analyses"]
        self.assertEqual(
            {(item["headword"], item["part_of_speech"]) for item in analyses},
            {("de", "prep")},
        )

    def test_case_distinct_redirect_does_not_expand_a_proper_name(self):
        cards = [{**create_card_record("fr", "cette").to_dict(), "rank": 1}]
        menu, _ = KaikkiSenseMenuAdapter(
            self.snapshot, language_policy=self.policy
        ).build(cards, snapshot_id="fixture-2026-08")
        analyses = menu["cards"][0]["analyses"]
        self.assertEqual(
            {(item["headword"], item["part_of_speech"]) for item in analyses},
            {("cette", "det")},
        )

    def test_complete_dump_declares_absence_for_a_missing_surface(self):
        cards = [{**create_card_record("fr", "inconnu").to_dict(), "rank": 1}]
        menu, report = KaikkiSenseMenuAdapter(
            self.snapshot, language_policy=self.policy
        ).build(cards, snapshot_id="fixture-2026-08")

        card = menu["cards"][0]
        self.assertEqual(card["analyses"], [])
        self.assertEqual(
            card["resolution"],
            {
                "resolver_version": "surface-resolver/v1",
                "strategy": "no_menu",
                "provider": "wiktionary",
                "coverage": "absent",
                "entry_id": None,
                "expanded_to": None,
                "word_class": "unresolved",
                "surface": "inconnu",
                "reason": "absent",
                "headwords": [],
                "entry": None,
                "notes": {},
            },
        )
        self.assertEqual(report["per_surface"][0]["strategy"], "no_menu")
        self.assertEqual(report["per_surface"][0]["reason"], "absent")

    def test_semantic_form_of_senses_are_retained_and_do_not_redirect(self):
        row_base = {
            "word": "mau", "lang_code": "pt", "pos": "adj",
            "senses": [{"id": "en-mau-pt-adj-bad", "glosses": ["bad"]}],
        }
        row_form = {
            "word": "pior", "lang_code": "pt", "pos": "adj",
            "senses": [
                {
                    "id": "en-pior-pt-adj-worse",
                    "glosses": ["comparative degree of mau: worse"],
                    "tags": ["comparative", "form-of"],
                    "form_of": [{"word": "mau"}],
                },
                {
                    "id": "en-pior-pt-adj-worst",
                    "glosses": ["superlative degree of mau: worst"],
                    "tags": ["superlative", "form-of"],
                    "form_of": [{"word": "mau"}],
                },
            ],
        }
        snap = Path(self.temporary.name) / "kaikki-pt-form.jsonl"
        snap.write_text(
            json.dumps(row_base) + "\n" + json.dumps(row_form) + "\n",
            encoding="utf-8",
        )
        pt_policy = load_sense_menu_language_policy(REPOSITORY_ROOT, policy_id="pt-v1", language="pt")
        adapter = KaikkiSenseMenuAdapter(snap, language_code="pt", language_policy=pt_policy)
        cards = [create_card_record("pt", "pior").to_dict()]
        menu, _ = adapter.build(cards, snapshot_id="fixture-form-of")
        analyses = menu["cards"][0]["analyses"]
        self.assertEqual([(a["headword"], a["part_of_speech"]) for a in analyses], [("pior", "adj")])
        senses = analyses[0]["senses"]
        self.assertEqual([s["sense_id"] for s in senses], ["en-pior-pt-adj-worse", "en-pior-pt-adj-worst"])
        self.assertEqual(
            [(s["translation"], s["definition"]) for s in senses],
            [("worse", "comparative degree of mau"), ("worst", "superlative degree of mau")],
        )

    def test_inflected_card_sub_senses_and_form_restrictions(self):
        row_verb = {
            "word": "dar", "lang_code": "pt", "pos": "verb",
            "senses": [
                {
                    "id": "s-dar-give-1",
                    "glosses": ["to give", "to transfer possession"],
                    "tags": ["ditransitive"],
                },
                {
                    "id": "s-dar-give-2",
                    "glosses": ["to give", "to hand over"],
                    "tags": ["ditransitive"],
                },
                {
                    "id": "s-dar-impersonal",
                    "glosses": ["to be possible, can"],
                    "tags": ["impersonal"],
                },
            ],
        }
        row_form = {
            "word": "dão", "lang_code": "pt", "pos": "verb",
            "senses": [
                {
                    "id": "s-dao-form",
                    "glosses": ["third-person plural present indicative of dar"],
                    "tags": ["form-of", "indicative", "plural", "present", "third-person"],
                    "form_of": [{"word": "dar"}],
                }
            ],
        }
        snap = Path(self.temporary.name) / "kaikki-pt-dar.jsonl"
        snap.write_text(
            json.dumps(row_verb) + "\n" + json.dumps(row_form) + "\n",
            encoding="utf-8",
        )
        pt_policy = load_sense_menu_language_policy(REPOSITORY_ROOT, policy_id="pt-v1", language="pt")
        adapter = KaikkiSenseMenuAdapter(snap, language_code="pt", language_policy=pt_policy)
        cards = [create_card_record("pt", "dão").to_dict()]
        menu, _ = adapter.build(cards, snapshot_id="fixture-dão")
        analysis = menu["cards"][0]["analyses"][0]
        self.assertEqual(analysis["headword"], "dar")
        senses = analysis["senses"]
        # Both "to give" senses preserved with their distinguishing definitions
        self.assertEqual([s["sense_id"] for s in senses], ["s-dar-give-1", "s-dar-give-2"])
        self.assertEqual(
            [(s["translation"], s["definition"]) for s in senses],
            [("to give", "to transfer possession"), ("to give", "to hand over")],
        )
        # Impersonal sense dropped because form is 3pl
        dropped = analysis["provider_metadata"]["dropped_form_restrictions"]
        self.assertEqual(len(dropped), 1)
        self.assertEqual(dropped[0]["sense_id"], "s-dar-impersonal")
        self.assertIn("not 3sg", dropped[0]["reason"])


if __name__ == "__main__":
    unittest.main()
