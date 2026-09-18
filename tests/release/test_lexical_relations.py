from copy import deepcopy
import json
from pathlib import Path
import tempfile
import unittest

from fluency.core.artifacts import store_artifact_bytes
from fluency.core.hashing import file_content_id
from fluency.core.io import json_bytes
from fluency.core.workspace import Workspace
from fluency.release.lexical_relations import attach_lexical_relations
from fluency.release.pilot import build_pilot_release


class LexicalRelationsAttachTests(unittest.TestCase):
    def test_successor_release_stamps_index_and_leaves_source_untouched(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            workspace = Workspace.initialize(Path(temporary) / "workspace")
            source = build_pilot_release(workspace)
            composition = json.loads((source / "composition.json").read_text(encoding="utf-8"))
            source_index = json.loads((source / "app" / "vocabulary.index.json").read_text(encoding="utf-8"))
            self.assertFalse(any(card.get("synonyms") for card in source_index))

            layer = {
                "layer_version": "lexical-relations/v1",
                "language": "fr",
                "locale": "fr-FR",
                "layer_kind": "lexical_relations",
                "join_key": "headword",
                "source": {"provider": "kaikki", "snapshot_id": "test", "provenance_status": "observed"},
                "inputs": {
                    "sense_menu_content_id": composition["layers"]["sense_menu"]["artifact_id"],
                },
                "coverage": {"requested_headwords": 1, "covered_headwords": 1, "missing_headwords": []},
                "records": [{
                    "headword": "bonjour",
                    "synonyms": [{"word": "salut"}],
                    "antonyms": [],
                }],
            }
            metadata = store_artifact_bytes(
                workspace,
                json_bytes(layer),
                filename="lexical-relations.json",
                media_type="application/json",
                schema="lexical-relations/v1",
                created_by_stage="test",
                row_count=1,
            )

            directory, _stats = attach_lexical_relations(
                workspace,
                language="fr",
                mode="speech",
                source_release_id=composition["release_id"],
                target_release_id="fr-speech-pilot-relations",
                artifact_id=metadata.artifact_id,
            )

            successor = json.loads((directory / "app" / "vocabulary.index.json").read_text(encoding="utf-8"))
            stamped = [card for card in successor if card.get("word") == "bonjour"]
            self.assertEqual(len(stamped), 1)
            self.assertEqual(stamped[0]["synonyms"][0]["word"], "salut")
            source_after = json.loads((source / "app" / "vocabulary.index.json").read_text(encoding="utf-8"))
            self.assertEqual(source_after, source_index)
            self.assertEqual(
                json.loads((directory / "composition.json").read_text(encoding="utf-8"))["layers"]["lexical_relations"]["artifact_id"],
                metadata.artifact_id,
            )
            self.assertEqual(file_content_id(source / "deck.json"), file_content_id(source / "deck.json"))
            successor_deck = json.loads((directory / "deck.json").read_text(encoding="utf-8"))
            source_deck = json.loads((source / "deck.json").read_text(encoding="utf-8"))
            expected = deepcopy(source_deck)
            expected["release_id"] = "fr-speech-pilot-relations"
            self.assertEqual(successor_deck, expected)


if __name__ == "__main__":
    unittest.main()
