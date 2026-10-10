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
                            "noun_merge": {"rule_version": "noun-merge/v2", "allowed": False},
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
            self.assertEqual(columns["noun_merge"], [{"rule_version": "noun-merge/v2", "allowed": False}, None])
            self.assertNotIn("meanings", columns)
            self.assertNotIn("synonyms", columns)
            self.assertIn("meanings", first["aaaa0001"])
            self.assertEqual(first["aaaa0001"]["synonyms"][0]["word"], "um só")
            self.assertTrue(first["aaaa0001"]["meanings"][0]["metadata"]["heavy"])
            self.assertNotIn("word", first["aaaa0001"])
            self.assertTrue((app / "vocabulary.index.json").is_file())

    def test_lemma_column_skips_expressions_the_word_occurs_in(self) -> None:
        # Shapes from pt-speech-v23: é shipped lemma "não é" because the phrase
        # was its single most frequent meaning, though ser outweighs it.
        cards = {
            "é": [
                {"headword": "ser", "pos": "verb", "frequency": "0.2"},
                {"headword": "ser", "pos": "verb", "frequency": "0.2"},
                {"headword": "não é", "pos": "PHRASE", "frequency": "0.3"},
            ],
            # Wiktionary tags some multiword headwords with an ordinary part of speech.
            "cinto": [
                {"headword": "cinto", "pos": "noun", "frequency": "0.28"},
                {"headword": "cinto de segurança", "pos": "noun", "frequency": "0.42"},
            ],
            "repente": [{"headword": "de repente", "pos": "adv", "frequency": "1.0"}],
            "porfavor": [{"headword": "por favor", "pos": "PHRASE", "frequency": "1.0"}],
            "casa-de-banho": [{"headword": "casa de banho", "pos": "noun", "frequency": "1.0"}],
            "por favor": [{"headword": "por favor", "pos": "MWE", "frequency": "1.0"}],
        }
        index = [
            {
                "id": f"{rank:08x}",
                "word": word,
                "rank": rank,
                "surface_card_id": f"card_pt_{rank:08x}",
                "meanings": meanings,
            }
            for rank, (word, meanings) in enumerate(cards.items(), start=1)
        ]
        structure = {
            "structure_version": "study-structure/v1",
            "levels": [
                {
                    "level_id": "level-001",
                    "sets": [
                        {
                            "set_id": "level-001-set-01",
                            "start_rank": 1,
                            "end_rank": len(index),
                            "card_ids": [card["surface_card_id"] for card in index],
                        }
                    ],
                }
            ],
        }
        with tempfile.TemporaryDirectory() as directory:
            app = Path(directory)
            (app / "vocabulary.index.json").write_text(json.dumps(index), encoding="utf-8")
            (app / "study-structure.json").write_text(json.dumps(structure), encoding="utf-8")

            shard_app_index(app)
            columns = json.loads((app / "vocabulary.index.columns.json").read_text(encoding="utf-8"))

        self.assertEqual(
            dict(zip(columns["word"], columns["lemma"])),
            {
                "é": "ser",
                "cinto": "cinto",
                "repente": None,
                "porfavor": "por favor",
                "casa-de-banho": "casa de banho",
                "por favor": "por favor",
            },
        )


if __name__ == "__main__":
    unittest.main()
