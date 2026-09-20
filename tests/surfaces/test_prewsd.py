import tempfile
import unittest
from pathlib import Path

from fluency.surfaces.prewsd import (
    PAIRS_VERSION,
    build,
    occurrence_pos_lookup,
    verify,
)


class PrewsdPairsTests(unittest.TestCase):
    def test_occurrence_pos_is_parallel_to_eligible_and_lookup_skips_nulls(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp)
            manifest = build(
                out,
                language="es",
                run_id="test",
                sentences=[
                    {"sentence_id": "sentence_aaa", "target": "Te tomo en serio.",
                     "translation": "I take you seriously."},
                    {"sentence_id": "bbb", "target": "Es muy serio.",
                     "translation": "He is very serious."},
                ],
                surfaces={
                    "serio": {
                        "eligible": [0, 1],
                        "occurrence_pos": ["ADV", None],
                    }
                },
                occurrence_pos_model="es_dep_news_trf@3.8.0",
            )
            self.assertEqual(verify(out), [])
            pairs = (out / "pairs.json").read_text(encoding="utf-8")
            self.assertIn(PAIRS_VERSION, pairs)
            import json
            examples = json.loads((out / "examples.json").read_text(encoding="utf-8"))
            pr = json.loads((out / "pairs.json").read_text(encoding="utf-8"))
            self.assertEqual(pr["occurrence_pos_model"], "es_dep_news_trf@3.8.0")
            self.assertEqual(
                occurrence_pos_lookup(examples, pr),
                {("serio", "sentence_aaa"): "ADV"},
            )
            self.assertEqual(manifest["sentences"], 2)

    def test_missing_occurrence_pos_column_is_all_null(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp)
            build(
                out,
                language="cs",
                run_id="test",
                sentences=[{"sentence_id": "sentence_x", "target": "Ahoj."}],
                surfaces={"ahoj": {"eligible": [0]}},
            )
            import json
            pr = json.loads((out / "pairs.json").read_text(encoding="utf-8"))
            self.assertEqual(pr["surfaces"]["ahoj"]["occurrence_pos"], [None])
            self.assertIsNone(pr["occurrence_pos_model"])


if __name__ == "__main__":
    unittest.main()
