import json
from pathlib import Path
import tempfile
import unittest

from fluency.core.artifacts import artifact_directory, verify_artifact
from fluency.core.workspace import Workspace
from fluency.enrichments.conjugations import (
    ConjugationLayerError,
    build_conjugation_layer,
    pin_jehle_snapshot,
)
from fluency.enrichments.kaikki_conjugations import pin_kaikki_snapshot
from fluency.enrichments.verbecc_conjugations import (
    UNSUPPORTED as VERBECC_UNSUPPORTED,
    collapse_person_forms,
    pin_verbecc_snapshot,
)


CSV = """infinitive,infinitive_english,mood,mood_english,tense,tense_english,verb_english,form_1s,form_2s,form_3s,form_1p,form_2p,form_3p,gerund,gerund_english,pastparticiple,pastparticiple_english
hablar,to speak,Indicativo,Indicative,Presente,Present,I speak,hablo,hablas,habla,hablamos,habláis,hablan,hablando,speaking,hablado,spoken
hablar,to speak,Subjuntivo,Subjunctive,Presente,Present,that I speak,hable,hables,hable,hablemos,habléis,hablen,hablando,speaking,hablado,spoken
"""


class ConjugationLayerTests(unittest.TestCase):
    def test_pins_source_and_builds_only_requested_verb_headwords(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            workspace = Workspace.initialize(root / "workspace")
            source = root / "jehle.csv"
            source.write_text(CSV, encoding="utf-8")
            snapshot = pin_jehle_snapshot(
                workspace,
                source=source,
                snapshot_id="jehle-test-v1",
            )
            menu = root / "sense-menu.json"
            menu.write_text(json.dumps({
                "menu_version": "sense-menu/v1",
                "language": "es",
                "snapshot_id": "menu-test-v1",
                "cards": [{
                    "card_id": "card_es_1234567890abcdef",
                    "surface_form": "hablo",
                    "analyses": [
                        {"headword": "hablar", "part_of_speech": "VERB"},
                        {"headword": "hablo", "part_of_speech": "NOUN"},
                    ],
                }],
            }), encoding="utf-8")

            metadata, coverage = build_conjugation_layer(
                workspace,
                sense_menu=menu,
                source_snapshot=snapshot,
            )

            self.assertEqual(coverage, {
                "requested_headwords": 1,
                "covered_headwords": 1,
                "missing_headwords": [],
            })
            self.assertEqual(verify_artifact(workspace, metadata.artifact_id), metadata)
            payload = json.loads((artifact_directory(workspace, metadata.artifact_id) / metadata.filename).read_text())
            self.assertEqual(payload["join_key"], "headword")
            self.assertEqual(payload["records"][0]["headword"], "hablar")
            self.assertEqual(payload["records"][0]["paradigms"][0]["forms"][0], {
                "person": "1s", "form": "hablo",
            })

    def test_rejects_duplicate_paradigms(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            workspace = Workspace.initialize(root / "workspace")
            source = root / "jehle.csv"
            source.write_text(CSV + CSV.splitlines()[1] + "\n", encoding="utf-8")
            snapshot = pin_jehle_snapshot(workspace, source=source, snapshot_id="duplicate-v1")
            menu = root / "sense-menu.json"
            menu.write_text(json.dumps({
                "menu_version": "sense-menu/v1", "language": "es", "snapshot_id": "m",
                "cards": [{"analyses": [{"headword": "hablar", "part_of_speech": "VERB"}]}],
            }), encoding="utf-8")
            with self.assertRaises(ConjugationLayerError):
                build_conjugation_layer(workspace, sense_menu=menu, source_snapshot=snapshot)

    def test_kaikki_adapter_requests_wiktionary_verb_pos_and_lists_missing(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            workspace = Workspace.initialize(root / "workspace")
            dump = workspace.root / "raw/wiktionary/kaikki-czech.jsonl"
            dump.parent.mkdir(parents=True)
            dump.write_text(
                json.dumps({
                    "word": "být",
                    "pos": "verb",
                    "senses": [{"glosses": ["to be"]}],
                    "forms": [
                        {"form": "jsem", "tags": ["first-person", "indicative", "present", "singular"], "source": "conjugation"},
                        {"form": "jsi", "tags": ["second-person", "indicative", "present", "singular"], "source": "conjugation"},
                        {"form": "je", "tags": ["third-person", "indicative", "present", "singular"], "source": "conjugation"},
                        {"form": "jsme", "tags": ["first-person", "indicative", "present", "plural"], "source": "conjugation"},
                        {"form": "jste", "tags": ["second-person", "indicative", "present", "plural"], "source": "conjugation"},
                        {"form": "jsou", "tags": ["third-person", "indicative", "present", "plural"], "source": "conjugation"},
                        {"form": "buď", "tags": ["imperative", "present", "second-person", "singular"], "source": "conjugation"},
                        {"form": "byl", "tags": ["masculine", "participle", "past", "singular"], "source": "conjugation"},
                        {"form": "future", "tags": ["table-tags"], "source": "conjugation"},
                    ],
                }, ensure_ascii=False)
                + "\n"
                + json.dumps({"word": "jsem", "pos": "verb", "senses": [{"form_of": [{"word": "být"}]}], "forms": []})
                + "\n",
                encoding="utf-8",
            )
            snapshot = pin_kaikki_snapshot(
                workspace,
                source=dump,
                language="cs",
                snapshot_id="kaikki-test-v1",
            )
            menu = root / "sense-menu.json"
            menu.write_text(json.dumps({
                "menu_version": "sense-menu/v1",
                "language": "cs",
                "snapshot_id": "cs-menu-test",
                "cards": [{
                    "analyses": [
                        {"headword": "být", "part_of_speech": "verb"},
                        {"headword": "jsem", "part_of_speech": "verb"},
                    ],
                }],
            }), encoding="utf-8")

            metadata, coverage = build_conjugation_layer(
                workspace,
                sense_menu=menu,
                source_snapshot=snapshot,
            )

            self.assertEqual(coverage["requested_headwords"], 2)
            self.assertEqual(coverage["covered_headwords"], 1)
            self.assertEqual(coverage["missing_headwords"], ["jsem"])
            payload = json.loads((artifact_directory(workspace, metadata.artifact_id) / metadata.filename).read_text())
            self.assertEqual(payload["language"], "cs")
            self.assertEqual(payload["locale"], "cs-CZ")
            self.assertEqual(payload["source"]["provider"], "kaikki")
            record = payload["records"][0]
            self.assertEqual(record["headword"], "být")
            self.assertEqual(record["nonfinite"]["past_participle"], "byl")
            present = next(item for item in record["paradigms"] if item["mood"] == "indicative")
            self.assertEqual(
                [item["form"] for item in present["forms"]],
                ["jsem", "jsi", "je", "jsme", "jste", "jsou"],
            )

    def test_dutch_has_no_conjugation_locale_or_verbecc_source(self) -> None:
        from fluency.enrichments.conjugations import DEFAULT_LOCALES

        self.assertNotIn("nl", DEFAULT_LOCALES)
        self.assertEqual(
            VERBECC_UNSUPPORTED["nl"],
            "Dutch has no live speech menu or release, and verbecc has no nl language.",
        )

    def test_verbecc_refuses_czech_and_dutch(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            workspace = Workspace.initialize(root / "workspace")
            dummy = root / "verbs.xml"
            dummy.write_text("<verbs/>", encoding="utf-8")
            for language, message in VERBECC_UNSUPPORTED.items():
                with self.assertRaisesRegex(ConjugationLayerError, "live speech menu|not in verbecc"):
                    pin_verbecc_snapshot(
                        workspace,
                        language=language,
                        verbs_xml=dummy,
                        conjugations_xml=dummy,
                        snapshot_id=f"{language}-should-fail",
                    )
                self.assertTrue(message)

    def test_verbecc_collapses_european_pronouns_to_six_persons(self) -> None:
        cells = [
            {"c": ["eu sou"], "pr": "eu"},
            {"c": ["tu és"], "pr": "tu"},
            {"c": ["ele é"], "pr": "ele"},
            {"c": ["ela é"], "pr": "ela"},
            {"c": ["você é"], "pr": "você"},
            {"c": ["nós somos"], "pr": "nós"},
            {"c": ["vós sois"], "pr": "vós"},
            {"c": ["eles são"], "pr": "eles"},
            {"c": ["elas são"], "pr": "elas"},
            {"c": ["vocês são"], "pr": "vocês"},
        ]
        forms = collapse_person_forms(cells, "pt")
        self.assertEqual(
            [(item["person"], item["form"]) for item in forms],
            [("1s", "sou"), ("2s", "és"), ("3s", "é"), ("1p", "somos"), ("2p", "sois"), ("3p", "são")],
        )

    def test_verbecc_pin_and_conjugate_known_portuguese_infinitive(self) -> None:
        from fluency.enrichments.verbecc_conjugations import installed_verbecc_xml

        verbs_xml, conjugations_xml = installed_verbecc_xml("pt")
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            workspace = Workspace.initialize(root / "workspace")
            snapshot = pin_verbecc_snapshot(
                workspace,
                language="pt",
                verbs_xml=verbs_xml,
                conjugations_xml=conjugations_xml,
                snapshot_id="verbecc-pt-test-v1",
            )
            menu = root / "sense-menu.json"
            menu.write_text(json.dumps({
                "menu_version": "sense-menu/v1",
                "language": "pt",
                "snapshot_id": "pt-menu-test",
                "cards": [{"analyses": [
                    {"headword": "ser", "part_of_speech": "verb"},
                    {"headword": "acabaram", "part_of_speech": "verb"},
                ]}],
            }), encoding="utf-8")
            metadata, coverage = build_conjugation_layer(
                workspace,
                sense_menu=menu,
                source_snapshot=snapshot,
            )
            self.assertEqual(coverage["requested_headwords"], 2)
            self.assertEqual(coverage["covered_headwords"], 1)
            self.assertEqual(coverage["missing_headwords"], ["acabaram"])
            payload = json.loads((artifact_directory(workspace, metadata.artifact_id) / metadata.filename).read_text())
            record = payload["records"][0]
            self.assertEqual(record["headword"], "ser")
            present = next(item for item in record["paradigms"] if item["mood"] == "indicativo" and item["tense"] == "presente")
            self.assertEqual(present["forms"][0], {"person": "1s", "form": "sou"})


if __name__ == "__main__":
    unittest.main()
