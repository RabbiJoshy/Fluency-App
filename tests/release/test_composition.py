from copy import deepcopy
import json
from pathlib import Path
import tempfile
import unittest

from fluency.core.workspace import Workspace
from fluency.release.activation import activate_release
from fluency.release.catalog import build_catalog
from fluency.release.pilot import build_pilot_release
from fluency.release.composition import compose_release
from fluency.release.validation import ReleaseValidationError, validate_composition


class CompositionTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.workspace = Workspace.initialize(Path(self.temporary.name) / "workspace")
        self.release = build_pilot_release(self.workspace)
        self.composition = json.loads((self.release / "composition.json").read_text(encoding="utf-8"))

    def tearDown(self):
        self.temporary.cleanup()

    def test_catalog_contains_only_composed_candidates(self):
        legacy = self.release.parent / "legacy-release"
        legacy.mkdir()
        (legacy / "manifest.json").write_text("{}\n", encoding="utf-8")
        catalog = build_catalog(self.workspace, "fr", "speech")
        self.assertEqual([item["release_id"] for item in catalog["candidates"]], ["fr-speech-pilot-0005"])
        self.assertTrue(catalog["candidates"][0]["active"])
        self.assertEqual(catalog["candidates"][0]["fallback_layers"], 0)

    def test_catalog_excludes_invalid_historical_candidates(self):
        historical = self.release.parent / "historical-release"
        historical.mkdir()
        (historical / "composition.json").write_text("{}\n", encoding="utf-8")
        (historical / "manifest.json").write_text("{}\n", encoding="utf-8")
        catalog = build_catalog(self.workspace, "fr", "speech")
        self.assertEqual(
            [item["release_id"] for item in catalog["candidates"]],
            ["fr-speech-pilot-0005"],
        )

    def test_dependency_drift_fails_closed(self):
        broken = deepcopy(self.composition)
        broken["layers"]["example_selection"]["requires"]["inventory"] = "sha256:" + "0" * 64
        with self.assertRaisesRegex(ReleaseValidationError, "different inventory"):
            validate_composition(broken)

    def test_fallback_cannot_be_implicit(self):
        broken = deepcopy(self.composition)
        broken["layers"]["sentences"]["fallback"] = {
            "policy": "missing_only",
            "source_type": "run",
            "source_id": "old-run",
            "artifact_id": "sha256:" + "1" * 64,
            "record_count": 2,
        }
        with self.assertRaisesRegex(ReleaseValidationError, "fallback policy is none"):
            validate_composition(broken)

    def test_failed_activation_preserves_pointer(self):
        active = self.release.parent / "active.json"
        before = active.read_bytes()
        with self.assertRaises(ReleaseValidationError):
            activate_release(self.workspace, "fr", "speech", "missing-release")
        self.assertEqual(active.read_bytes(), before)

    def test_streamed_composition_matches_every_existing_payload_byte(self):
        deck = json.loads((self.release / 'deck.json').read_text())
        before = {p.relative_to(self.release): p.read_bytes() for p in self.release.rglob('*') if p.is_file()}
        result = compose_release(self.workspace, self.composition, deck, memory_bounded=True)
        self.assertEqual(result, self.release)
        self.assertEqual(before, {p.relative_to(result): p.read_bytes() for p in result.rglob('*') if p.is_file()})
        # Exercise publication to a new directory too, not just validation of
        # an existing immutable bundle.
        import shutil
        shutil.rmtree(self.release)
        result = compose_release(self.workspace, self.composition, deck, memory_bounded=True)
        self.assertEqual(before, {p.relative_to(result): p.read_bytes() for p in result.rglob('*') if p.is_file()})
        self.assertFalse(list((self.workspace.root / '.fluency/temporary').glob('serialized-release-*')))


if __name__ == "__main__":
    unittest.main()
