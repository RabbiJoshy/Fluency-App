import copy
import json
import tempfile
import unittest
from pathlib import Path

from fluency.core.identity import create_card_record
from fluency.core.hashing import file_content_id
from fluency.sense_menu.config import load_sense_menu_language_policy
from fluency.sense_menu.kaikki import KaikkiSenseMenuAdapter
from fluency.sense_menu.noun_merge import stamp_noun_merge
from fluency.sense_menu.spanishdict import SpanishDictSenseMenuAdapter

ROOT = Path(__file__).resolve().parents[2]


def menu(surface, extra=False, restriction=False, declared=True):
    senses = [{"source_reference": "dictionary:gato:cat", "translation": "cat",
               "definition": "animal", "provider_metadata": {}, "specialist_features": []}]
    if extra:
        senses.append({"source_reference": "dictionary:gato:jack", "translation": "jack",
                       "definition": "tool"})
    if restriction:
        senses[0]["specialist_features"] = [
            {"family": "grammar", "kind": "sense_mark", "value": "number=plural-only"}]
    if surface != "gato":
        senses[0]["specialist_features"].append(
            {"family": "grammar", "kind": "surface_mark", "value": "number=plural"})
    return {"surface_form": surface, "analyses": [{
        "headword": "gato", "part_of_speech": "noun", "source_adapter": "dictionary",
        "senses": senses, "provider_metadata": {"resolution": "structured_form_of",
            "surface_grammar": ["plural"] if declared else []}}]}


class NounMergeTests(unittest.TestCase):
    def test_identical_complete_menus_ignore_surface_grammar_order_and_duplicates(self):
        cards = [menu("gato", extra=True), menu("gatos", extra=True)]
        cards[1]["analyses"][0]["senses"].reverse()
        cards[1]["analyses"][0]["senses"].append(copy.deepcopy(cards[1]["analyses"][0]["senses"][0]))
        stamp_noun_merge(cards)
        self.assertTrue(all(c["noun_merge"]["allowed"] for c in cards))
        self.assertEqual(cards[0]["noun_merge"]["sense_set"], cards[1]["noun_merge"]["sense_set"])

    def test_extra_sense_on_either_side_blocks_both(self):
        for side in (0, 1):
            with self.subTest(side=side):
                cards = [menu("gato", extra=side == 0), menu("gatos", extra=side == 1)]
                stamp_noun_merge(cards)
                self.assertTrue(all(not c["noun_merge"]["allowed"] for c in cards))
                self.assertEqual(cards[0]["noun_merge"]["reason"], "different_sense_sets")

    def test_number_restricted_shared_menu_blocks_both(self):
        cards = [menu("gato", restriction=True), menu("gatos", restriction=True)]
        stamp_noun_merge(cards)
        self.assertTrue(all(not c["noun_merge"]["allowed"] for c in cards))

    def test_missing_base_or_missing_relationship_is_not_approval(self):
        for cards in ([menu("gatos")], [menu("gato"), menu("gatos", declared=False)]):
            stamp_noun_merge(cards)
            self.assertTrue(all(not c["noun_merge"]["allowed"] for c in cards))

    def test_gender_form_is_not_a_number_pair(self):
        cards = [menu("gato"), menu("gatos"), menu("gata")]
        cards[2]["analyses"][0]["provider_metadata"]["surface_grammar"] = ["feminine", "singular"]
        stamp_noun_merge(cards)
        self.assertTrue(cards[0]["noun_merge"]["allowed"])
        self.assertTrue(cards[1]["noun_merge"]["allowed"])
        self.assertFalse(cards[2]["noun_merge"]["allowed"])

    def test_reference_collision_does_not_hide_different_definition(self):
        cards = [menu("gato"), menu("gatos")]
        cards[1]["analyses"][0]["senses"][0]["definition"] = "different meaning"
        stamp_noun_merge(cards)
        self.assertFalse(cards[0]["noun_merge"]["allowed"])

    def test_unassigned_dictionary_phrase_also_participates(self):
        cards = [menu("gato"), menu("gatos")]
        phrase = {"headword": "phrase with gato", "part_of_speech": "PHRASE",
                  "source_adapter": "dictionary", "senses": [{
                      "source_reference": "dictionary:phrase", "translation": "special phrase",
                      "frequency": 0}]}
        cards[0]["analyses"].append(phrase)
        stamp_noun_merge(cards)
        self.assertTrue(all(not c["noun_merge"]["allowed"] for c in cards))
        cards[1]["analyses"].append(copy.deepcopy(phrase))
        stamp_noun_merge(cards)
        self.assertTrue(all(c["noun_merge"]["allowed"] for c in cards))

    def test_ambiguous_plural_blocks_the_singular_group(self):
        cards = [menu("gato"), menu("gatos")]
        other = copy.deepcopy(cards[1]["analyses"][0])
        other["headword"] = "other"
        cards[1]["analyses"].append(other)
        stamp_noun_merge(cards)
        self.assertTrue(all(not c["noun_merge"]["allowed"] for c in cards))

    def test_same_spelling_noun_and_verb_entries_block_whole_word_merge(self):
        for sides in ((0,), (1,), (0, 1)):
            with self.subTest(sides=sides):
                cards = [menu("gato"), menu("gatos")]
                for side in sides:
                    verb = copy.deepcopy(cards[side]["analyses"][0])
                    verb["part_of_speech"] = "verb"
                    verb["senses"] = [{"source_reference": "dictionary:gato:verb",
                                       "translation": "a verb meaning"}]
                    cards[side]["analyses"].append(verb)
                stamp_noun_merge(cards)
                self.assertTrue(all(not c["noun_merge"]["allowed"] for c in cards))
                self.assertEqual({c["noun_merge"]["reason"] for c in cards},
                                 {"multiple_dictionary_entries"})

    def test_multiple_provider_analyses_of_one_noun_entry_are_not_a_clash(self):
        cards = [menu("gato"), menu("gatos")]
        for card in cards:
            other_provider = copy.deepcopy(card["analyses"][0])
            other_provider["source_adapter"] = "second-dictionary"
            other_provider["part_of_speech"] = "NOUN"
            card["analyses"].append(other_provider)
        stamp_noun_merge(cards)
        self.assertTrue(all(c["noun_merge"]["allowed"] for c in cards))

    def test_wiktionary_ser_seres_noun_and_personal_infinitive_do_not_merge(self):
        with tempfile.TemporaryDirectory() as tmp:
            rows = [
                {"word": "ser", "lang_code": "pt", "pos": "noun",
                 "senses": [{"id": "being", "glosses": ["being (a living creature)"]}]},
                {"word": "ser", "lang_code": "pt", "pos": "verb",
                 "senses": [{"id": "be", "glosses": ["to be"]}]},
                {"word": "seres", "lang_code": "pt", "pos": "noun",
                 "senses": [{"tags": ["form-of", "plural"], "form_of": [{"word": "ser"}],
                             "glosses": ["plural of ser"]}]},
                {"word": "seres", "lang_code": "pt", "pos": "verb",
                 "senses": [{"tags": ["form-of", "infinitive", "personal", "second-person", "singular"],
                             "form_of": [{"word": "ser"}],
                             "glosses": ["second-person singular personal infinitive of ser"]}]},
            ]
            path = Path(tmp) / "dictionary.jsonl"
            path.write_text("\n".join(json.dumps(row) for row in rows))
            policy = load_sense_menu_language_policy(ROOT, policy_id="pt-lyrics-polyglot-v2", language="pt")
            adapter = KaikkiSenseMenuAdapter(path, language_code="pt", language_policy=policy)
            cards = [create_card_record("pt", surface).to_dict() for surface in ("ser", "seres")]
            payload, _ = adapter.build(cards, snapshot_id="test")
            self.assertTrue(all(not c["noun_merge"]["allowed"] for c in payload["cards"]))
            self.assertEqual({c["noun_merge"]["reason"] for c in payload["cards"]},
                             {"multiple_dictionary_entries"})

    def test_wiktionary_real_form_of_rows_in_spanish_and_portuguese(self):
        for language in ("es", "pt"):
            for plural_only in (False, True):
                with self.subTest(language=language, plural_only=plural_only), tempfile.TemporaryDirectory() as tmp:
                    rows = [
                        {"word": "gato", "lang_code": language, "pos": "noun",
                         "tags": ["plural-only"] if plural_only else [],
                         "senses": [{"id": "cat", "glosses": ["cat"]}]},
                        {"word": "gatos", "lang_code": language, "pos": "noun",
                         "senses": [{"tags": ["form-of", "plural"], "form_of": [{"word": "gato"}],
                                     "glosses": ["plural of gato"]}]},
                    ]
                    path = Path(tmp) / "dictionary.jsonl"
                    path.write_text("\n".join(json.dumps(r) for r in rows))
                    policy = load_sense_menu_language_policy(ROOT,
                        policy_id="es-wiktionary-v1" if language == "es" else "pt-lyrics-polyglot-v2",
                        language=language)
                    adapter = KaikkiSenseMenuAdapter(path, language_code=language, language_policy=policy)
                    cards = [{**create_card_record(language, s).to_dict(), "rank": i}
                             for i, s in enumerate(("gato", "gatos"), 1)]
                    payload, _ = adapter.build(cards, snapshot_id="test")
                    self.assertEqual([not plural_only] * 2,
                                     [c["noun_merge"]["allowed"] for c in payload["cards"]])

    def test_spanishdict_declared_plural_and_separately_defined_plural(self):
        for special in (False, True):
            with self.subTest(special=special), tempfile.TemporaryDirectory() as tmp:
                path = Path(tmp)
                noun = {"pos": "NOUN", "part_of_speech_label": "masculine noun",
                        "translation": "cat", "context": "animal"}
                entry = {"entry_lang": "es", "dictionary_analyses": [
                    {"headword": "gato", "senses": [noun]}]}
                plural = {**entry, "query": "gatos", "possible_results": [
                    {"headword": "gato", "heuristic": "inflection", "inflection_type": "plural"}]}
                if special:
                    plural = copy.deepcopy(plural)
                    plural["dictionary_analyses"].append({"headword": "gatos", "senses": [
                        {"pos": "plural noun", "translation": "special meaning", "context": ""}]})
                files = {"surface_cache.json": {"gato": {**entry, "query": "gato"}, "gatos": plural},
                         "headword_cache.json": {"gato": entry}, "spanish_forms.json": {},
                         "conjugation_reverse.json": {}}
                manifest = []
                for name, data in files.items():
                    dest = path / name
                    dest.write_text(json.dumps(data))
                    manifest.append({"path": name, "sha256": file_content_id(dest).removeprefix("sha256:"),
                                     "bytes": dest.stat().st_size})
                (path / "artifact.json").write_text(json.dumps({
                    "schema_version": "spanishdict-snapshot/v1", "artifact_kind": "dictionary_menu_source",
                    "language": "es", "provider": "spanishdict", "snapshot_id": "test", "content_files": manifest}))
                adapter = SpanishDictSenseMenuAdapter(path, language_policy=load_sense_menu_language_policy(
                    ROOT, policy_id="es-spanishdict-v1", language="es"))
                cards = [{**create_card_record("es", s).to_dict(), "rank": i}
                         for i, s in enumerate(("gato", "gatos"), 1)]
                payload, _ = adapter.build(cards, snapshot_id="test")
                self.assertEqual([not special] * 2, [c["noun_merge"]["allowed"] for c in payload["cards"]])


if __name__ == "__main__":
    unittest.main()
