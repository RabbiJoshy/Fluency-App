"""Guard real subtitle ingestion and full-series coverage."""
import importlib.util
import json
from pathlib import Path
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location("casa_build", ROOT / "scripts/build_casa_de_papel.py")
casa = importlib.util.module_from_spec(spec)
spec.loader.exec_module(casa)


class CasaSubtitleBuildTests(unittest.TestCase):
    def test_wrapped_dialogue_repetitions_and_captions(self):
        data = ("1\n00:00:01,000 --> 00:00:03,000\n<i>Hola,</i>\nprofesor.\n\n"
                "2\n00:00:04,000 --> 00:00:05,000\nHola, profesor.\n\n"
                "3\n00:00:06,000 --> 00:00:07,000\n[disparos]\n\n"
                "4\n00:00:08,000 --> 00:00:09,000\n♪ Song ♪\n")
        cues = casa.parse_srt(data.encode())
        self.assertEqual([c["spanish"] for c in cues], ["Hola, profesor."] * 2)
        self.assertEqual(cues[0]["start_ms"], 1000)
        dialogue, deck = casa.build([{"episode": "S01E01", "lines": cues}], {"hola", "profesor"},
                                    {"numbering": "original", "retrievedAt": "2026-10-21"})
        self.assertEqual(deck["surfaces"]["profesor"]["count"], 2)
        self.assertEqual(len(deck["surfaces"]["profesor"]["lines"]), 1)
        self.assertNotIn("english", deck["surfaces"]["profesor"]["lines"][0])

    def test_missing_episodes_cannot_publish_full_show(self):
        with self.assertRaisesRegex(ValueError, "Missing episodes: S01E01"):
            casa.load_episodes({"episodes": []}, ROOT)

    def test_forced_only_subtitles_rejected(self):
        with patch.object(casa, "read_source", return_value=b"1\n00:00:01,000 --> 00:00:02,000\nHola"):
            with self.assertRaisesRegex(ValueError, "Incomplete dialogue"):
                casa.load_episodes({"episodes": [{"season": 1, "episode": 1}]}, ROOT)

    def test_published_sample_has_real_coverage_and_season_examples(self):
        dialogue = json.loads((ROOT / "app/data/series/casa-de-papel.json").read_text())
        deck = json.loads((ROOT / "app/data/series/casa-de-papel-deck.json").read_text())
        sources = json.loads((ROOT / "app/data/series/casa-de-papel-sources.json").read_text())
        self.assertEqual(len(sources["episodes"]), 30)
        self.assertEqual(dialogue["episodes_count"], 30)
        self.assertEqual(dialogue["total_lines_count"], 22755)
        self.assertEqual(sum(len(ep["lines"]) for ep in dialogue["episodes"]), 22755)
        self.assertEqual(deck["matchedCount"], len(deck["surfaces"]))
        self.assertEqual(deck["matchedCount"], 6102)
        self.assertEqual(deck["coverage"], dialogue["coverage"])
        self.assertFalse(deck["coverage"]["complete"])
        self.assertEqual(len(deck["coverage"]["missing"]), 11)
        self.assertEqual(deck["coverage"]["exampleTranslations"], "unavailable")
        self.assertEqual(deck["surfaces"]["profesor"]["count"], 299)
        self.assertEqual(deck["intake"]["mode"], "no-wsd")
        self.assertEqual(deck["intake"]["grouping"], "original-surface")
        self.assertEqual(deck["intake"]["summary"]["frequencyRecognized"], 10335)
        self.assertEqual(deck["intake"]["summary"]["additionalFrequencySurfaces"], 4233)
        self.assertEqual(deck["intake"]["summary"]["entityCandidates"], 13)
        self.assertEqual({e["song"][:3] for e in deck["surfaces"]["profesor"]["lines"]},
                         {"S01", "S02", "S03", "S04"})
