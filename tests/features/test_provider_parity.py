"""Both dictionary adapters must emit the same concept families."""

import unittest

from fluency.features.spanishdict import extract as spanishdict_extract
from fluency.features.wiktionary import extract as wiktionary_extract


def values(features, family):
    return {feature.value for feature in features if feature.family == family}


class ProviderParityTests(unittest.TestCase):
    def test_functional_notes_share_one_family(self) -> None:
        spanish = spanishdict_extract({"context": "used to indicate direction"})
        wiki = wiktionary_extract({"glosses": ["used to indicate direction"]})
        self.assertEqual(values(spanish, "functional"), values(wiki, "functional"))

    def test_grammar_marks_share_canonical_values(self) -> None:
        spanish = spanishdict_extract(
            {"context": "imperative; second person singular"}
        )
        wiki = wiktionary_extract(
            {}, tags=["imperative", "second-person", "singular"]
        )
        self.assertEqual(values(spanish, "grammar"), values(wiki, "grammar"))

    def test_plain_paraphrase_is_not_sent_to_the_domain_channel(self) -> None:
        features = spanishdict_extract({"context": "to be available"})
        self.assertFalse(any(feature.family == "domain" for feature in features))

    def test_spanishdict_context_is_partitioned_clause_by_clause(self) -> None:
        features = spanishdict_extract({
            "context": 'to reach a place; often used with "a"; second person singular'
        })
        projected = {(item.family, item.kind, item.value) for item in features}
        self.assertIn(
            ("construction", "optional_companion", 'often used with "a"'),
            projected,
        )
        self.assertIn(("grammar", "sense_mark", "person=2"), projected)
        self.assertIn(("grammar", "sense_mark", "number=singular"), projected)
        self.assertFalse(any(item.value == "to reach a place" for item in features))

    def test_quoted_a_is_a_spanish_companion_not_an_english_article(self) -> None:
        features = spanishdict_extract({
            "context": 'road or route; used with "a" or "hasta"'
        })
        companions = {
            item.value for item in features if item.family == "companion"
        }
        self.assertEqual(companions, {"a", "hasta"})
        self.assertTrue(all(
            item.embedding_text == 'used with "a" or "hasta"'
            for item in features if item.family == "companion"
        ))

    def test_provider_domain_and_region_shapes_share_canonical_families(self) -> None:
        features = spanishdict_extract({
            "context": "aviation",
            "regions": [{"name": "Mexico"}],
        })
        self.assertEqual(
            {(item.family, item.kind, item.value) for item in features},
            {
                ("domain", "domain_label", "aviation"),
                ("register", "region", "Mexico"),
            },
        )

    def test_functional_future_note_is_not_mistaken_for_verb_tense(self) -> None:
        features = spanishdict_extract({"context": "used to indicate the future"})
        self.assertEqual({item.family for item in features}, {"functional"})

    def test_family_relative_is_not_mistaken_for_relative_pronoun_grammar(self) -> None:
        noun = spanishdict_extract({"pos": "NOUN", "context": "relative"})
        pronoun = spanishdict_extract({"pos": "PRON", "context": "relative"})
        self.assertEqual(values(noun, "grammar"), set())
        self.assertEqual(values(pronoun, "grammar"), {"function=relative"})

    def test_multiword_quoted_companions_remain_complete(self) -> None:
        features = spanishdict_extract({"context": 'used with "por" or "a por"'})
        self.assertEqual(values(features, "companion"), {"por", "a por"})
        self.assertNotIn('por"', values(features, "companion"))

    def test_soft_trailing_companion_is_not_marked_required(self) -> None:
        features = spanishdict_extract({
            "context": 'used with "a" or "de" and sometimes preceded by "con"'
        })
        self.assertEqual(values(features, "companion"), {"a", "de"})
        self.assertEqual(
            values(features, "construction"), {"sometimes preceded by con"}
        )

    def test_english_gloss_locales_are_not_spanish_regions(self) -> None:
        features = spanishdict_extract({
            "context": "dwelling",
            "regions": ["Australia", "United Kingdom", "Spain"],
        })
        self.assertEqual(values(features, "register"), {"Spain"})

    def test_unknown_regions_are_not_silently_promoted_to_registers(self) -> None:
        features = spanishdict_extract({"regions": ["Future provider label"]})
        self.assertEqual(values(features, "register"), set())

    def test_domain_aliases_match_wiktionary_topic_vocabulary(self) -> None:
        legal = spanishdict_extract({"context": "legal"})
        religious = spanishdict_extract({"context": "religious"})
        self.assertEqual(values(legal, "domain"), {"law"})
        self.assertEqual(values(religious, "domain"), {"religion"})

    def test_spanishdict_object_roles_use_wiktionarys_construction_shape(self) -> None:
        spanish = spanishdict_extract({"context": "direct object"})
        wiki = wiktionary_extract({
            "raw_glosses": ["(direct object) him"],
        })
        self.assertEqual(
            {(item.family, item.kind, item.value) for item in spanish},
            {("construction", "object_role", "direct object")},
        )
        self.assertEqual(
            {(item.family, item.kind, item.value) for item in spanish},
            {(item.family, item.kind, item.value) for item in wiki},
        )
        self.assertEqual(values(spanish, "grammar"), set())

    def test_spanishdict_prose_frames_become_atomic_constructions(self) -> None:
        features = spanishdict_extract({
            "context": "before adjective; used with an infinitive; with participle"
        })
        self.assertEqual(
            {(item.kind, item.value) for item in features if item.family == "construction"},
            {
                ("position", "before adjective"),
                ("complement_form", "infinitive"),
                ("complement_form", "participle"),
            },
        )

    def test_clear_functional_participles_are_not_left_as_semantic_prose(self) -> None:
        features = spanishdict_extract({"context": "indicating time; expressing surprise"})
        self.assertEqual(
            values(features, "functional"),
            {"indicating time", "expressing surprise"},
        )

    def test_semantic_uses_of_express_and_used_remain_meaning_text(self) -> None:
        for context in ("to express", "to express a thought to oneself", "to be used up"):
            self.assertEqual(spanishdict_extract({"context": context}), ())


if __name__ == "__main__":
    unittest.main()
