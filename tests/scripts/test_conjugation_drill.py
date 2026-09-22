import importlib.util
from pathlib import Path
import unittest


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]


def _load_builder():
    path = REPOSITORY_ROOT / "scripts" / "build_conjugation_drill.py"
    spec = importlib.util.spec_from_file_location("build_conjugation_drill", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


builder = _load_builder()


def _persons(*forms):
    return [
        {"person": person, "form": form}
        for person, form in zip(("1s", "2s", "3s", "1p", "2p", "3p"), forms)
    ]


def _layer(language, locale, records):
    return {
        "layer_version": "conjugation-layer/v1",
        "language": language,
        "locale": locale,
        "source": {"provider": "stub", "snapshot_id": "test"},
        "inputs": {"sense_menu_snapshot_id": "menu-test"},
        "records": records,
    }


class ConjugationDrillBuilderTests(unittest.TestCase):
    def test_portuguese_stub_maps_indicative_present_and_pronouns(self) -> None:
        records = [
            {
                "headword": "falar",
                "gloss": "to speak",
                "nonfinite": {"past_participle": "falado"},
                "paradigms": [{
                    "mood": "indicativo",
                    "tense": "presente",
                    "forms": _persons("falo", "falas", "fala", "falamos", "falais", "falam"),
                }],
            },
            {
                "headword": "nadar",
                "gloss": "to swim",
                "nonfinite": {"past_participle": "nadado"},
                "paradigms": [{
                    "mood": "indicativo",
                    "tense": "presente",
                    "forms": _persons("nado", "nadas", "nada", "nadamos", "nadais", "nadam"),
                }],
            },
            {
                "headword": "amar",
                "gloss": "to love",
                "nonfinite": {"past_participle": "amado"},
                "paradigms": [{
                    "mood": "indicativo",
                    "tense": "presente",
                    "forms": _persons("amo", "amas", "ama", "amamos", "amais", "amam"),
                }],
            },
        ]
        deck = builder.build_deck(_layer("pt", "pt-PT", records), {"falar": 12}, "pt")
        self.assertEqual(deck["language"], "pt")
        self.assertEqual(deck["pronouns"]["1s"], "eu")
        self.assertEqual(len(deck["verbs"]), 3)
        present = [tense for tense in deck["tenses"] if tense["tense"] == "Present"]
        self.assertEqual(len(present), 1)
        self.assertEqual(present[0]["mood"], "Indicative")
        falar = next(verb for verb in deck["verbs"] if verb["h"] == "falar")
        self.assertEqual(falar["n"], 12)

    def test_czech_stub_maps_present_and_imperative(self) -> None:
        records = [
            {
                "headword": "dělat",
                "gloss": "to do",
                "nonfinite": {"past_participle": "dělal"},
                "paradigms": [
                    {
                        "mood": "indicative",
                        "tense": "present",
                        "forms": _persons("dělám", "děláš", "dělá", "děláme", "děláte", "dělají"),
                    },
                    {
                        "mood": "imperative",
                        "tense": "present",
                        "forms": [{"person": "2s", "form": "dělej"}, {"person": "2p", "form": "dělejte"}],
                    },
                ],
            },
            {
                "headword": "čekat",
                "gloss": "to wait",
                "nonfinite": {"past_participle": "čekal"},
                "paradigms": [{
                    "mood": "indicative",
                    "tense": "present",
                    "forms": _persons("čekám", "čekáš", "čeká", "čekáme", "čekáte", "čekají"),
                }],
            },
            {
                "headword": "volat",
                "gloss": "to call",
                "nonfinite": {"past_participle": "volal"},
                "paradigms": [{
                    "mood": "indicative",
                    "tense": "present",
                    "forms": _persons("volám", "voláš", "volá", "voláme", "voláte", "volají"),
                }],
            },
        ]
        deck = builder.build_deck(_layer("cs", "cs-CZ", records), {}, "cs")
        self.assertEqual(deck["language"], "cs")
        self.assertEqual(deck["pronouns"]["1s"], "já")
        labels = {(tense["mood"], tense["tense"]) for tense in deck["tenses"]}
        self.assertEqual(labels, {("Indicative", "Present"), ("Imperative", "Imperative")})
        self.assertEqual(len(deck["verbs"]), 3)
        self.assertGreater(deck["total_forms"], 0)


class ConjugationModeWiringTests(unittest.TestCase):
    def test_portuguese_and_czech_decks_are_shipped_and_linked(self) -> None:
        app = REPOSITORY_ROOT / "app"
        html = (app / "conjugation" / "index.html").read_text(encoding="utf-8")
        conj = (app / "js" / "flashcards-conj.js").read_text(encoding="utf-8")
        boot = (app / "conjugation" / "app.js").read_text(encoding="utf-8")
        self.assertTrue((app / "conjugation" / "data" / "pt.js").is_file())
        self.assertTrue((app / "conjugation" / "data" / "cs.js").is_file())
        self.assertIn("data/pt.js", html)
        self.assertIn("data/cs.js", html)
        self.assertIn("id=\"back-to-study\"", html)
        self.assertIn("portuguese: 'pt'", conj)
        self.assertIn("czech: 'cs'", conj)
        self.assertIn("params.get('lang')", boot)
        self.assertIn("leaveConjugationMode", boot)
