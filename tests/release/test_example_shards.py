import json
from pathlib import Path
import tempfile
import unittest

from fluency.release.example_shards import shard_app_examples


class ExampleShardTests(unittest.TestCase):
    def test_splits_the_monolith_along_study_sets(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            app = Path(directory)
            (app / "vocabulary.index.json").write_text(
                json.dumps(
                    [
                        {"id": "aaaa0001", "word": "um", "rank": 1, "surface_card_id": "card_pt_aaaa0001deadbeef", "meanings": []},
                        {"id": "bbbb0002", "word": "dois", "rank": 2, "surface_card_id": "card_pt_bbbb0002deadbeef", "meanings": []},
                    ]
                ),
                encoding="utf-8",
            )
            (app / "vocabulary.examples.json").write_text(
                json.dumps(
                    {
                        "aaaa0001": {"m": [[{"target": "um", "source": "tatoeba"}]]},
                        "bbbb0002": {"m": [[{"target": "dois", "source": "opensubtitles"}]]},
                    }
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

            manifest = shard_app_examples(app)
            first = json.loads(
                (app / "vocabulary.examples.shards/level-001-set-01.json").read_text(encoding="utf-8")
            )
            self.assertEqual(manifest["shard_count"], 2)
            self.assertEqual(manifest["missing_cards"], 0)
            self.assertEqual(list(first), ["aaaa0001"])
            self.assertTrue((app / "vocabulary.examples.json").is_file())


if __name__ == "__main__":
    unittest.main()
