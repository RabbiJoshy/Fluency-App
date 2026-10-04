import json
from pathlib import Path
import tempfile
import unittest

from fluency.core.artifacts import artifact_directory
from fluency.core.io import json_bytes
from fluency.core.workspace import Workspace
from fluency.enrichments.conjugations import (
    ConjugationLayerError,
    build_conjugation_layer,
)
from fluency.enrichments.kaikki_conjugations import pin_kaikki_snapshot


class ConjugationLayerTests(unittest.TestCase):
    def test_kaikki_adapter_requests_wiktionary_verb_pos_and_lists_missing(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            workspace = Workspace.initialize(root / "workspace")
            dump = workspace.root / "raw/wiktionary/kaikki-czech.jsonl"
            dump.parent.mkdir(parents=True)
            dump.write_text(
                json.dumps({
                    "word": "být",
                    "pos": "verb",
                    "senses": [{"glosses": ["to be"]}],
                    "forms": [
                        {"form": "jsem", "tags": ["first-person", "indicative", "present", "singular"], "source": "conjugation"},
                        {"form": "jsi", "tags": ["second-person", "indicative", "present", "singular"], "source": "conjugation"},
                        {"form": "je", "tags": ["third-person", "indicative", "present", "singular"], "source": "conjugation"},
                        {"form": "jsme", "tags": ["first-person", "indicative", "present", "plural"], "source": "conjugation"},
                        {"form": "jste", "tags": ["second-person", "indicative", "present", "plural"], "source": "conjugation"},
                        {"form": "jsou", "tags": ["third-person", "indicative", "present", "plural"], "source": "conjugation"},
                        {"form": "buď", "tags": ["imperative", "present", "second-person", "singular"], "source": "conjugation"},
                        {"form": "byl", "tags": ["masculine", "participle", "past", "singular"], "source": "conjugation"},
                        {"form": "future", "tags": ["table-tags"], "source": "conjugation"},
                    ],
                }, ensure_ascii=False)
                + "\n"
                + json.dumps({"word": "jsem", "pos": "verb", "senses": [{"form_of": [{"word": "být"}]}], "forms": []})
                + "\n",
                encoding="utf-8",
            )
            snapshot = pin_kaikki_snapshot(
                workspace,
                source=dump,
                language="cs",
                snapshot_id="kaikki-test-v1",
            )
            menu = root / "sense-menu.json"
            menu.write_text(json.dumps({
                "menu_version": "sense-menu/v1",
                "language": "cs",
                "snapshot_id": "cs-menu-test",
                "cards": [{
                    "analyses": [
                        {"headword": "být", "part_of_speech": "verb"},
                        {"headword": "jsem", "part_of_speech": "verb"},
                    ],
                }],
            }), encoding="utf-8")

            metadata, coverage = build_conjugation_layer(
                workspace,
                sense_menu=menu,
                source_snapshot=snapshot,
            )

            self.assertEqual(coverage["requested_headwords"], 2)
            self.assertEqual(coverage["covered_headwords"], 1)
            self.assertEqual(coverage["missing_headwords"], ["jsem"])
            payload = json.loads((artifact_directory(workspace, metadata.artifact_id) / metadata.filename).read_text())
            self.assertEqual(payload["language"], "cs")
            self.assertEqual(payload["locale"], "cs-CZ")
            self.assertEqual(payload["source"]["provider"], "kaikki")
            record = payload["records"][0]
            self.assertEqual(record["headword"], "být")
            self.assertEqual(record["nonfinite"]["past_participle"], "byl")
            present = next(item for item in record["paradigms"] if item["mood"] == "indicative")
            self.assertEqual(
                [item["form"] for item in present["forms"]],
                ["jsem", "jsi", "je", "jsme", "jste", "jsou"],
            )

    def test_dutch_has_no_conjugation_locale(self) -> None:
        from fluency.enrichments.conjugations import DEFAULT_LOCALES

        self.assertNotIn("nl", DEFAULT_LOCALES)

    def test_retired_providers_are_refused(self) -> None:
        # Jehle and verbecc were dropped on 2026-10-04; a snapshot pinned from
        # either can no longer build a layer.
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            workspace = Workspace.initialize(root / "workspace")
            snapshot = workspace.root / "raw/conjugations/es/fred-jehle/old-v1"
            snapshot.mkdir(parents=True)
            (snapshot / "artifact.json").write_bytes(json_bytes({
                "schema_version": "retained-source-artifact/v1",
                "artifact_kind": "conjugation_source",
                "language": "es",
                "provider": "fred-jehle",
                "snapshot_id": "old-v1",
            }))
            menu = root / "sense-menu.json"
            menu.write_text(json.dumps({
                "menu_version": "sense-menu/v1", "language": "es", "snapshot_id": "m",
                "cards": [{"analyses": [{"headword": "hablar", "part_of_speech": "VERB"}]}],
            }), encoding="utf-8")
            with self.assertRaisesRegex(ConjugationLayerError, "unsupported conjugation source provider"):
                build_conjugation_layer(workspace, sense_menu=menu, source_snapshot=snapshot)


if __name__ == "__main__":
    unittest.main()
