"""The per-sense cognate map (cognate-score/v4), for English and for a known
language read through its own dictionary."""

import json
import tempfile
import unittest
from pathlib import Path

from fluency.enrichments.cognates import build_app_cognates_by_sense

CONFIG_ROOT = Path(__file__).resolve().parents[2] / "config"


def row(word, *senses):
    return {"word": word, "meanings": [{"headword": h, "translation": t} for h, t in senses]}


def entry(word, *glosses, tags=()):
    return {"word": word, "pos": "noun", "senses": [{"glosses": [g], "tags": list(tags)} for g in glosses]}


class SenseMapTests(unittest.TestCase):
    def build(self, language, rows, pairs, files, known=None, **kwargs):
        with tempfile.TemporaryDirectory() as directory:
            raw = Path(directory)
            (raw / "cognet" / "pairs").mkdir(parents=True)
            for name, lines in files.items():
                (raw / "cognet" / "pairs" / name).write_text(
                    "".join(f"{a}\t{b}\tn\n" for a, b in lines), encoding="utf-8"
                )
            extracts = {}
            for code, entries in (known or {"en": None}).items():
                if entries is None:
                    extracts[code] = None
                    continue
                path = raw / f"{code}.jsonl"
                path.write_text("".join(json.dumps(e) + "\n" for e in entries), encoding="utf-8")
                extracts[code] = path
            return build_app_cognates_by_sense(
                language=language, config_root=CONFIG_ROOT, raw_root=raw,
                release_rows=rows, known_extracts=extracts, **kwargs
            )

    def test_cognet_decides_cognateness_and_the_scorer_closeness(self) -> None:
        # Named alphabetically by the extractor, so Spanish is column 1.
        payload = self.build(
            "es",
            [row("problemas", ("problema", "problems")),
             row("banco", ("banco", "bank"), ("banco", "bench"), ("banco", "school"))],
            None,
            {"eng-spa.tsv": [("problems", "problema"), ("bank", "banco"), ("bench", "banco")]},
        )
        self.assertEqual(payload["schema"], "cognate-score/v4")
        self.assertEqual(payload["surface_scorers"], {"en": "learner-align/v1"})
        self.assertGreaterEqual(payload["scores"]["problemas"]["problema"]["problems"]["en"], 0.85)
        banco = payload["scores"]["banco"]["banco"]
        self.assertIn("bank", banco)
        # "school" is a translation of banco but CogNet does not pair them.
        self.assertNotIn("school", banco)
        self.assertEqual(payload["cards"]["problemas"]["en"][1], "problems")

    def test_without_cognet_a_close_gloss_is_enough_and_a_far_one_is_not(self) -> None:
        payload = self.build("es", [row("idea", ("idea", "idea")), row("este", ("este", "east"))], None, {"eng-spa.tsv": []})
        self.assertEqual(payload["scores"]["idea"]["idea"]["idea"]["en"], 1.0)
        self.assertNotIn("este", payload["scores"])

    def test_the_gloss_route_needs_a_real_english_word_when_a_list_is_given(self) -> None:
        payload = self.build("es", [row("nous", ("nous", "nous"))], None, {"eng-spa.tsv": []}, english_words={"we"})
        self.assertNotIn("nous", payload["scores"])

    def test_a_known_language_is_reached_through_the_english_gloss(self) -> None:
        polish = [
            entry("problem", "problem"),
            entry("sklep", "shop"),
            # Polish chyba is the particle "probably"; "mistake" is obsolete.
            {"word": "chyba", "pos": "particle", "senses": [
                {"glosses": ["probably"]}, {"glosses": ["mistake"], "tags": ["obsolete"]}]},
            entry("pivnica", "cellar"),
        ]
        rows = [
            row("problém", ("problém", "problem")),
            # sklep is a cellar in Czech, a shop in Polish: no shared sense.
            row("sklep", ("sklep", "cellar")),
            row("chyba", ("chyba", "mistake")),
        ]
        payload = self.build(
            "cs", rows, None,
            {"ces-eng.tsv": [], "ces-pol.tsv": [("problém", "problem")]},
            known={"en": None, "pl": polish},
        )
        self.assertEqual(payload["known_languages"], ["en", "pl"])
        self.assertEqual(payload["scores"]["problém"]["problém"]["problem"]["pl"], 1.0)
        self.assertNotIn("pl", payload["scores"].get("sklep", {}).get("sklep", {}).get("cellar", {}))
        self.assertNotIn("chyba", payload["scores"])
        self.assertEqual(payload["cards"]["problém"]["pl"], [1.0, "problem"])

    def test_portuguese_for_spanish_speakers_preserves_false_friends_and_mixed_cards(self) -> None:
        payload = self.build(
            "pt", [row("informação", ("informação", "information")),
                   row("família", ("família", "family")),
                   row("cidade", ("cidade", "city")),
                   row("oficina", ("oficina", "workshop")),
                   row("famílias", ("família", "family"), ("família", "household"))],
            None,
            {"por-spa.tsv": [("informação", "información"), ("família", "familia"),
                             ("cidade", "ciudad"), ("oficina", "oficina")]},
            known={"es": [entry("información", "information"), entry("familia", "family"),
                          entry("ciudad", "city"), entry("oficina", "office", "workshop")]},
        )
        self.assertEqual(payload["known_languages"], ["es"])
        for surface, match in [("informação", "información"), ("família", "familia"),
                               ("cidade", "ciudad")]:
            with self.subTest(surface=surface):
                score, word = payload["cards"][surface]["es"]
                self.assertGreaterEqual(score, payload["thresholds"]["es"])
                self.assertEqual(word, match)
        self.assertNotIn("oficina", payload["scores"])
        self.assertNotIn("famílias", payload["cards"])

    def test_only_a_primary_sense_of_the_known_word_counts(self) -> None:
        # Polish czerstwy is "stale" first; "fresh" is a minor sense. A Polish
        # reader takes Czech čerstvý (fresh) for its opposite, so it is not free.
        polish = [{"word": "czerstwy", "pos": "adj", "senses": [
            {"glosses": ["stale"]}, {"glosses": ["fresh"]}]}]
        payload = self.build(
            "cs", [row("čerstvý", ("čerstvý", "fresh"))], None,
            {"ces-eng.tsv": [], "ces-pol.tsv": [("čerstvý", "czerstwy")]},
            known={"en": None, "pl": polish},
        )
        self.assertNotIn("čerstvý", payload["scores"])

    def test_cognet_narrows_a_known_language_where_it_knows_the_headword(self) -> None:
        polish = [entry("kot", "cat"), entry("kotek", "cat")]
        payload = self.build(
            "cs", [row("kotě", ("kotě", "cat"))], None,
            {"ces-eng.tsv": [], "ces-pol.tsv": [("kotě", "kotek")]},
            known={"en": None, "pl": polish},
        )
        cell = payload["scores"]["kotě"]["kotě"]["cat"]
        self.assertIn("pl", cell)
        self.assertEqual(payload["matches"]["kotě"]["kotě"]["cat"]["pl"], "kotek")


if __name__ == "__main__":
    unittest.main()
