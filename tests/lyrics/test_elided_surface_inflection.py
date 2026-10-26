"""An elided lyric spelling (seguimo') is inflected for its restored word."""
import importlib.util
import unittest
from pathlib import Path

from fluency.lyrics.inflector import inflect_card_senses

ROOT = Path(__file__).resolve().parents[2]


def plant_module():
    spec = importlib.util.spec_from_file_location("plant_artist_v20", ROOT / "scripts/plant_artist_v20.py")
    module = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(module)
    except ImportError as error:  # optional heavy dependencies of the full build
        raise unittest.SkipTest(str(error))
    return module


CONJ = {
    "seguimos": [{"lemma": "seguir", "mood": "indicativo", "tense": "presente", "person": "1p"}],
    "quedas": [{"lemma": "quedar", "mood": "indicativo", "tense": "presente", "person": "2s"}],
}


class ElidedSurfaceInflectionTests(unittest.TestCase):
    def test_elided_display_inflects_as_the_restored_word(self):
        plant = plant_module()
        for word, display, lemma, gloss, expected in [
            ("seguimos", "seguimo'", "seguir", "to follow", "we follow"),
            ("quedas", "queda'", "quedar", "to be", "you are"),
        ]:
            surface, inflect_as = plant.card_surfaces({"word": word, "display_form": display})
            self.assertEqual((surface, inflect_as), (word, word))
            sense = inflect_card_senses(inflect_as, lemma, [{"pos": "VERB", "translation": gloss, "headword": lemma}], CONJ)
            self.assertEqual(sense[0]["translation"], expected)

    def test_other_display_forms_are_kept(self):
        plant = plant_module()
        self.assertEqual(plant.card_surfaces({"word": "pa", "display_form": "Pa"}), ("pa", "Pa"))


if __name__ == "__main__":
    unittest.main()
