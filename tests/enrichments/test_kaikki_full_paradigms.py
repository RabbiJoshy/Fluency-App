"""Full Spanish/Portuguese tables from a Kaikki dump: tenses, compounds, derived -se verbs."""

import json
from pathlib import Path
import tempfile
import unittest

from fluency.enrichments.kaikki_conjugations import kaikki_records

P = ("first-person", "second-person", "third-person")


def cells(tags, forms):
    persons = [(p, "singular") for p in P] + [(p, "plural") for p in P]
    return [{"form": f, "tags": list(tags) + list(pn)} for f, pn in zip(forms, persons) if f]


def verb(word, forms, senses=None):
    return {"word": word, "pos": "verb", "forms": forms,
            "senses": senses or [{"glosses": [f"to {word}"]}]}


HABER = verb("haber", cells(["indicative", "present"], ["he", "has", "ha", "hemos", "habéis", "han"]))
ACOSTAR = verb("acostar", [
    {"form": "acostando", "tags": ["gerund"]},
    {"form": "acostado", "tags": ["masculine", "participle", "past", "singular"]},
    *cells(["indicative", "present"], ["acuesto", None, "acuesta", "acostamos", "acostáis", "acuestan"]),
    {"form": "acuestas", "tags": ["indicative", "informal", "present", "second-person", "singular"]},
    {"form": "acostás", "tags": ["indicative", "informal", "present", "second-person", "singular", "vos-form"]},
    *cells(["imperative", "negative"], [None, "acuestes", "acueste", "acostemos", "acostéis", "acuesten"]),
    {"form": "acuéstate", "tags": ["combined-form", "imperative", "informal", "with-tú",
                                   "object-second-person", "object-singular", "accusative"]},
    {"form": "acuéstese", "tags": ["combined-form", "imperative", "formal",
                                   "object-third-person", "object-singular", "accusative"]},
    {"form": "acostándose", "tags": ["combined-form", "gerund", "object-third-person", "object-singular"]},
], senses=[{"glosses": ["to put to bed"]}, {"glosses": ["to go to bed"], "tags": ["reflexive"]}])


class KaikkiFullParadigmTests(unittest.TestCase):
    def records(self, rows, requested, language):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "dump.jsonl"
            path.write_text("\n".join(json.dumps(r, ensure_ascii=False) for r in rows), encoding="utf-8")
            return kaikki_records(path, requested, language)

    def table(self, record, mood, tense):
        return next({f["person"]: f["form"] for f in p["forms"]}
                    for p in record["paradigms"] if (p["mood"], p["tense"]) == (mood, tense))

    def test_standard_form_beats_vos_and_negative_takes_no(self):
        acostar = self.records([ACOSTAR, HABER], {"acostar"}, "es")["acostar"]
        present = self.table(acostar, "indicativo", "presente")
        self.assertEqual(present["2s"], "acuestas")
        self.assertEqual(self.table(acostar, "imperativo", "negativo")["2s"], "no acuestes")

    def test_compound_tense_is_haber_plus_participle_and_labelled(self):
        acostar = self.records([ACOSTAR, HABER], {"acostar"}, "es")["acostar"]
        perfect = next(p for p in acostar["paradigms"] if p["tense"] == "pretérito perfecto")
        self.assertEqual(perfect["forms"][0]["form"], "he acostado")
        self.assertIn("haber", perfect["derived"])

    def test_pronominal_verb_is_derived_from_its_base(self):
        acostarse = self.records([ACOSTAR, HABER], {"acostarse"}, "es")["acostarse"]
        self.assertIn("reflexive of acostar", acostarse["derived"])
        self.assertEqual(acostarse["translation"], "to go to bed")
        self.assertEqual(self.table(acostarse, "indicativo", "presente")["1s"], "me acuesto")
        self.assertEqual(self.table(acostarse, "imperativo", "afirmativo"), {"2s": "acuéstate", "3s": "acuéstese"})
        self.assertEqual(self.table(acostarse, "imperativo", "negativo")["2s"], "no te acuestes")
        self.assertEqual(self.table(acostarse, "indicativo", "pretérito perfecto")["2s"], "te has acostado")
        self.assertEqual(acostarse["nonfinite"]["gerund"], "acostándose")

    def test_portuguese_regional_variant_loses_to_the_plain_form(self):
        ajudar = verb("ajudar", [
            *cells(["indicative", "preterite"], ["ajudei", "ajudaste", "ajudou", "ajudámos", "ajudastes", "ajudaram"]),
            {"form": "ajudamos", "tags": ["Brazil", "indicative", "preterite", "first-person", "plural"]},
        ])
        record = self.records([ajudar], {"ajudar"}, "pt")["ajudar"]
        self.assertEqual(self.table(record, "indicativo", "pretérito-perfeito")["1p"], "ajudámos")

    def test_other_languages_keep_present_and_imperative_only(self):
        record = self.records([verb("dělat", cells(["indicative", "present"], ["dělám"] * 6)
                                    + cells(["indicative", "future"], ["budu dělat"] * 6))], {"dělat"}, "cs")
        self.assertEqual([(p["mood"], p["tense"]) for p in record["dělat"]["paradigms"]],
                         [("indicative", "present")])


if __name__ == "__main__":
    unittest.main()
