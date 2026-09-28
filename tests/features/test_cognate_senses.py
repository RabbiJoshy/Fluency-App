"""The per-sense cognate map (cognate-score/v3)."""

import tempfile
import unittest
from pathlib import Path

from fluency.enrichments.cognates import build_app_cognates_by_sense

CONFIG_ROOT = Path(__file__).resolve().parents[2] / "config"


def row(word, *senses):
    return {"word": word, "meanings": [{"headword": h, "translation": t} for h, t in senses]}


class SenseMapTests(unittest.TestCase):
    def build(self, rows, pairs, **kwargs):
        with tempfile.TemporaryDirectory() as directory:
            raw = Path(directory)
            (raw / "cognet" / "pairs").mkdir(parents=True)
            # Named alphabetically by the extractor, so Spanish is column 1.
            (raw / "cognet" / "pairs" / "eng-spa.tsv").write_text(
                "".join(f"{known}\t{target}\tn\n" for target, known in pairs), encoding="utf-8"
            )
            return build_app_cognates_by_sense(
                language="es", config_root=CONFIG_ROOT, raw_root=raw, release_rows=rows, **kwargs
            )

    def test_cognet_decides_cognateness_and_the_scorer_closeness(self) -> None:
        payload = self.build(
            [
                row("problemas", ("problema", "problems")),
                row("banco", ("banco", "bank"), ("banco", "bench"), ("banco", "school")),
            ],
            [("problema", "problem"), ("problema", "problems"), ("banco", "bank"), ("banco", "bench")],
        )
        self.assertEqual(payload["schema"], "cognate-score/v3")
        self.assertEqual(payload["surface_scorer"], "edit-distance/v1")
        self.assertGreaterEqual(payload["scores"]["problemas"]["problema"]["problems"], 0.85)
        banco = payload["scores"]["banco"]["banco"]
        self.assertIn("bank", banco)
        # "school" is a translation of banco but CogNet does not pair them.
        self.assertNotIn("school", banco)

    def test_without_cognet_a_close_gloss_is_enough_and_a_far_one_is_not(self) -> None:
        payload = self.build(
            [row("idea", ("idea", "idea")), row("este", ("este", "east"))], []
        )
        self.assertEqual(payload["scores"]["idea"]["idea"]["idea"], 1.0)
        self.assertNotIn("este", payload["scores"])

    def test_the_gloss_route_needs_a_real_english_word_when_a_list_is_given(self) -> None:
        payload = self.build([row("nous", ("nous", "nous"))], [], english_words={"we"})
        self.assertNotIn("nous", payload["scores"])

    def test_non_english_languages_ride_along_from_a_v2_map(self) -> None:
        carried = {
            "schema": "cognate-score/v2.1",
            "known_languages": ["en", "pl"],
            "thresholds": {"en": 0.75, "pl": 0.8},
            "scores": {"idea": {"idea": {"en": 1.0, "pl": 0.9}}},
            "matches": {"idea": {"idea": {"en": "idea", "pl": "idea"}}},
        }
        payload = self.build([row("idea", ("idea", "idea"))], [], carried=carried)
        self.assertEqual(payload["known_languages"], ["en", "pl"])
        self.assertEqual(payload["carried"]["scores"], {"idea": {"idea": {"pl": 0.9}}})
        self.assertEqual(payload["carried"]["thresholds"], {"pl": 0.8})


if __name__ == "__main__":
    unittest.main()
