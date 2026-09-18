import json
from pathlib import Path
import tempfile
import unittest

from fluency.core.artifacts import artifact_directory, verify_artifact
from fluency.core.workspace import Workspace
from fluency.enrichments.lexical_relations import (
    LexicalRelationsError,
    apply_lexical_relations_to_index,
    build_lexical_relations_layer,
    pin_kaikki_dump,
    pin_spanishdict_fold,
)


class LexicalRelationsLayerTests(unittest.TestCase):
    def test_spanishdict_fold_is_bounded_to_requested_headwords(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            workspace = Workspace.initialize(root / "workspace")
            source = root / "synonyms.json"
            source.write_text(json.dumps({
                "bonito": {
                    "synonyms": [
                        {"word": "lindo", "strength": 2, "context": "beautiful"},
                        {"word": "lindo", "strength": 1},
                    ],
                    "antonyms": [{"word": "feo", "strength": 2}],
                },
                "mesa": {"synonyms": [{"word": "tabla", "strength": 1}]},
            }), encoding="utf-8")
            snapshot = pin_spanishdict_fold(
                workspace,
                source=source,
                snapshot_id="sd-test-v1",
            )
            menu = root / "sense-menu.json"
            menu.write_text(json.dumps({
                "menu_version": "sense-menu/v1",
                "language": "es",
                "snapshot_id": "menu-test-v1",
                "cards": [{
                    "card_id": "card_es_1234567890abcdef",
                    "surface_form": "bonito",
                    "analyses": [
                        {"headword": "bonito", "part_of_speech": "ADJ"},
                    ],
                }],
            }), encoding="utf-8")

            metadata, coverage = build_lexical_relations_layer(
                workspace,
                sense_menu=menu,
                source_snapshot=snapshot,
            )

            self.assertEqual(coverage["requested_headwords"], 1)
            self.assertEqual(coverage["covered_headwords"], 1)
            self.assertEqual(coverage["missing_headwords"], [])
            payload = json.loads(
                (artifact_directory(workspace, metadata.artifact_id) / metadata.filename).read_text()
            )
            self.assertEqual(payload["join_key"], "headword")
            self.assertEqual(payload["source"]["provider"], "spanishdict")
            record = payload["records"][0]
            self.assertEqual(record["headword"], "bonito")
            self.assertEqual([item["word"] for item in record["synonyms"]], ["lindo", "lindo"])
            self.assertEqual(record["antonyms"][0]["word"], "feo")

    def test_kaikki_adapter_folds_sense_lists_and_lists_missing(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            workspace = Workspace.initialize(root / "workspace")
            dump = workspace.root / "raw/wiktionary/kaikki-portuguese.jsonl"
            dump.parent.mkdir(parents=True)
            dump.write_text(
                "\n".join([
                    json.dumps({
                        "word": "livre",
                        "pos": "adj",
                        "senses": [
                            {"glosses": ["free"], "synonyms": [{"word": "liberto"}]},
                            {"glosses": ["gratis"], "synonyms": [{"word": "gratuito"}], "antonyms": [{"word": "preso"}]},
                        ],
                    }),
                    json.dumps({
                        "word": "mesa",
                        "pos": "noun",
                        "senses": [{"synonyms": [{"word": "tábua"}]}],
                    }),
                ]) + "\n",
                encoding="utf-8",
            )
            snapshot = pin_kaikki_dump(
                workspace,
                source=dump,
                language="pt",
                snapshot_id="kaikki-pt-test-v1",
            )
            menu = root / "sense-menu.json"
            menu.write_text(json.dumps({
                "menu_version": "sense-menu/v1",
                "language": "pt",
                "snapshot_id": "menu-pt",
                "cards": [{
                    "surface_form": "livre",
                    "analyses": [
                        {"headword": "livre", "part_of_speech": "ADJ"},
                        {"headword": "ausente", "part_of_speech": "ADJ"},
                    ],
                }],
            }), encoding="utf-8")

            metadata, coverage = build_lexical_relations_layer(
                workspace,
                sense_menu=menu,
                source_snapshot=snapshot,
            )
            self.assertEqual(coverage["requested_headwords"], 2)
            self.assertEqual(coverage["covered_headwords"], 1)
            self.assertEqual(coverage["missing_headwords"], ["ausente"])
            payload = json.loads(
                (artifact_directory(workspace, metadata.artifact_id) / metadata.filename).read_text()
            )
            record = payload["records"][0]
            self.assertEqual(record["headword"], "livre")
            self.assertEqual(
                sorted(item["word"] for item in record["synonyms"]),
                ["gratuito", "liberto"],
            )
            self.assertEqual(record["antonyms"][0]["word"], "preso")
            self.assertNotIn("strength", record["synonyms"][0])
            self.assertEqual(verify_artifact(workspace, metadata.artifact_id), metadata)

    def test_index_join_uses_meaning_headword_not_card_id(self) -> None:
        layer = {
            "layer_version": "lexical-relations/v1",
            "records": [{
                "headword": "hablar",
                "synonyms": [{"word": "platicar", "strength": 1}],
                "antonyms": [],
            }],
        }
        index = [{
            "id": "abcd1234",
            "word": "hablo",
            "surface_card_id": "card_es_ffffffffffffffff",
            "meanings": [{"headword": "hablar", "translation": "to speak"}],
        }]
        stats = apply_lexical_relations_to_index(index, layer)
        self.assertEqual(stats["stamped"], 1)
        self.assertEqual(index[0]["synonyms"][0]["word"], "platicar")
        self.assertNotIn("antonyms", index[0])

    def test_rejects_a_sense_menu_that_is_not_v1(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            workspace = Workspace.initialize(root / "workspace")
            source = root / "synonyms.json"
            source.write_text(json.dumps({"a": {"synonyms": [{"word": "b"}]}}), encoding="utf-8")
            snapshot = pin_spanishdict_fold(workspace, source=source, snapshot_id="bad-menu")
            menu = root / "sense-menu.json"
            menu.write_text(json.dumps({"menu_version": "nope", "language": "es", "cards": []}), encoding="utf-8")
            with self.assertRaises(LexicalRelationsError):
                build_lexical_relations_layer(workspace, sense_menu=menu, source_snapshot=snapshot)


if __name__ == "__main__":
    unittest.main()
