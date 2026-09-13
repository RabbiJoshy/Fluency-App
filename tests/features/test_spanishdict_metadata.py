import unittest

from fluency.features.spanishdict_metadata import metadata_accounting


class SpanishDictMetadataAccountingTests(unittest.TestCase):
    def test_known_fields_are_covered_and_unknown_fields_are_retained(self) -> None:
        accounting = metadata_accounting({
            "context": "used with de",
            "regions": ["Mexico"],
            "examples": [],
            "provider_only_note": {"label": "something new"},
        })
        self.assertEqual(accounting.coverage["context"], "parsed")
        self.assertEqual(
            accounting.coverage["context_semantic_remainder"], "preserved"
        )
        self.assertEqual(accounting.unclassified, ({
            "source_field": "spanishdict.provider_only_note",
            "value": {"label": "something new"},
            "reason": "no canonical SpanishDict mapping",
        },))

    def test_absent_language_specific_fields_need_no_fake_equivalent(self) -> None:
        accounting = metadata_accounting({"context": ""})
        self.assertEqual(accounting.unclassified, ())
        self.assertEqual(accounting.coverage["regions"], "parsed")

    def test_english_gloss_region_is_explicitly_ignored_not_lost(self) -> None:
        accounting = metadata_accounting({"regions": ["United Kingdom", "Spain"]})
        self.assertEqual(accounting.ignored, ({
            "source_field": "spanishdict.regions",
            "value": "United Kingdom",
            "reason": "English gloss locale, not target-language usage",
        },))


if __name__ == "__main__":
    unittest.main()
