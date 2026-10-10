import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


class NounMergeBuilderTests(unittest.TestCase):
    def test_full_menu_overlay_matches_source_references_without_undoing_inflection(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            app = root / "release-a" / "app"
            app.mkdir(parents=True)
            rows, cards = [], []
            for word, translation in (("gato", "cat"), ("gatos", "cats")):
                card_id = "card_es_" + word
                rows.append({"word": word, "surface_card_id": card_id, "meanings": [
                    {"headword": "gato", "pos": "NOUN", "translation": translation,
                     "source_reference": "dictionary:gato:cat"}]})
                cards.append({"card_id": card_id, "surface_form": word, "analyses": [{
                    "headword": "gato", "part_of_speech": "noun", "source_adapter": "dictionary",
                    "provider_metadata": {"resolution": "structured_form_of", "surface_grammar": ["plural"]},
                    "senses": [{"source_reference": "dictionary:gato:cat", "translation": "cat"}]}]})
            index = app / "vocabulary.index.json"
            index.write_text(json.dumps(rows))
            menu = root / "sense-menu.json"
            menu.write_text(json.dumps({"language": "es", "cards": cards}))
            out = root / "merge.json"
            command = [sys.executable, str(ROOT / "scripts/build_merge_exceptions.py"),
                       "--language", "es", "--release-index", str(index),
                       "--sense-menu", str(menu), "--out", str(out)]
            env = {**os.environ, "PYTHONPATH": str(ROOT / "src")}
            result = subprocess.run(command, capture_output=True, text=True, env=env)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            payload = json.loads(out.read_text())
            self.assertEqual(payload["keys"], {"gato": "gato", "gatos": "gato"})
            self.assertTrue(payload["noun_verdicts"]["gatos"]["allowed"])
            self.assertEqual(payload["release_id"], "release-a")
            rows[1]["meanings"][0]["source_reference"] = "different-snapshot-sense"
            index.write_text(json.dumps(rows))
            rejected = subprocess.run(command, capture_output=True, text=True, env=env)
            self.assertNotEqual(rejected.returncode, 0)
            self.assertIn("complete source senses", rejected.stderr)
            self.assertEqual(json.loads(out.read_text()), payload)
