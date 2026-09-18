import json
from pathlib import Path
import tempfile
import unittest

from fluency.release.index_shards import shard_app_index


class IndexShardTests(unittest.TestCase):
    def test_writes_columns_and_fat_rows_per_study_set(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            app = Path(directory)
            (app / "vocabulary.index.json").write_text(
                json.dumps(
                    [
                        {
                            "id": "aaaa0001",
                            "word": "um",
                            "rank": 1,
                            "surface_card_id": "card_pt_aaaa0001deadbeef",
                            "wsd_distribution": {"denominator": 1},
                            "unused_menu_senses": [{"sense_id": "leave"}],
                            "meanings": [
                                {
                                    "headword": "um",
                                    "translation": "one",
                                    "frequency": "1.0",
                                    "metadata": {"heavy": True},
                                }
                            ],
                            "synonyms": [{"word": "um só"}],
                        },
                        {
                            "id": "bbbb0002",
                            "word": "dois",
                            "rank": 2,
                            "surface_card_id": "card_pt_bbbb0002deadbeef",
                            "meanings": [{"headword": "dois", "frequency": "1.0"}],
                        },
                    ]
                ),
                encoding="utf-8",
            )
            (app / "study-structure.json").write_text(
                json.dumps(
                    {
                        "structure_version": "study-structure/v1",
                        "levels": [
                            {
                                "level_id": "level-001",
                                "sets": [
                                    {
                                        "set_id": "level-001-set-01",
                                        "start_rank": 1,
                                        "end_rank": 1,
                                        "card_ids": ["card_pt_aaaa0001deadbeef"],
                                    },
                                    {
                                        "set_id": "level-001-set-02",
                                        "start_rank": 2,
                                        "end_rank": 2,
                                        "card_ids": ["card_pt_bbbb0002deadbeef"],
                                    },
                                ],
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )

            manifest = shard_app_index(app)
            columns = json.loads((app / "vocabulary.index.columns.json").read_text(encoding="utf-8"))
            first = json.loads(
                (app / "vocabulary.index.rows/level-001-set-01.json").read_text(encoding="utf-8")
            )

            self.assertEqual(manifest["shard_count"], 2)
            self.assertEqual(manifest["missing_cards"], 0)
            self.assertEqual(columns["n"], 2)
            self.assertEqual(columns["id"], ["aaaa0001", "bbbb0002"])
            self.assertEqual(columns["lemma"], ["um", "dois"])
            self.assertNotIn("meanings", columns)
            self.assertNotIn("synonyms", columns)
            self.assertIn("meanings", first["aaaa0001"])
            self.assertEqual(first["aaaa0001"]["synonyms"][0]["word"], "um só")
            self.assertTrue(first["aaaa0001"]["meanings"][0]["metadata"]["heavy"])
            self.assertNotIn("word", first["aaaa0001"])
            self.assertTrue((app / "vocabulary.index.json").is_file())


if __name__ == "__main__":
    unittest.main()
