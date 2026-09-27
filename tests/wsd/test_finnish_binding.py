from __future__ import annotations

import unittest

from fluency.core.identity import create_card_record
from fluency.wsd.bindings import binding_for, pos_gate_for
from fluency.wsd.languages.finnish import FinnishWSDAdapter
from fluency.wsd.languages.spanish import SpanishV5CandidatePolicy
from fluency.wsd.menus import MenuAnalysis, SenseLeaf, build_analysis_id


class FinnishBindingTests(unittest.TestCase):
    def test_binding_uses_wiktionary_with_pinned_finnish_pos_model(self) -> None:
        binding = binding_for("fi")
        self.assertEqual(binding.menu_provider, "wiktionary")
        self.assertEqual(binding.pos_model_role, "occurrence-pos-fi")

    def test_exact_surface_location_preserves_diacritics(self) -> None:
        adapter = FinnishWSDAdapter()
        found = adapter.locate("Hän näki tämän täällä.", "tämän")
        self.assertEqual(
            [(item.observed_text, item.start, item.end) for item in found],
            [("tämän", 9, 14)],
        )
        self.assertEqual(adapter.locate("Han on täällä.", "hän"), ())

    def test_finnish_pos_gate_uses_wiktionary_bridge(self) -> None:
        compatible, orthogonal = pos_gate_for("fi")
        self.assertFalse(compatible("verb", "NOUN"))
        self.assertTrue(compatible("verb", "VERB"))
        self.assertFalse(orthogonal("verb"))

    def test_tapaan_rule_overrides_unreliable_contextual_pos_and_lemma(self) -> None:
        card = create_card_record("fi", "tapaan")

        def analysis(key: str, headword: str, pos: str, translation: str) -> MenuAnalysis:
            adapter = "kaikki-sense-menu/v1"
            return MenuAnalysis(
                menu_analysis_id=build_analysis_id(
                    card_id=card.card_id,
                    source_adapter=adapter,
                    source_analysis_key=key,
                ),
                card_id=card.card_id,
                surface_form="tapaan",
                headword=headword,
                part_of_speech=pos,
                source_adapter=adapter,
                source_analysis_key=key,
                senses=(SenseLeaf(key, translation, "", f"wikt:{key}", {}),),
                provider_metadata={},
            )

        noun = analysis("tapa:noun", "tapa", "NOUN", "manner")
        verb = analysis("tavata:verb", "tavata", "VERB", "meet")
        adapter = FinnishWSDAdapter()
        compatible, orthogonal = pos_gate_for("fi")
        policy = SpanishV5CandidatePolicy(
            language="fi",
            constraint_mode="filter",
            sense_compatible=compatible,
            pos_is_orthogonal=orthogonal,
            contextual_headword_selector=adapter.contextual_headwords,
        )
        prepared = policy.prepare(
            sentence="En pääse ennen kuin tapaan Andyn.",
            surface_form="tapaan",
            observed_pos="NOUN",
            observed_grammar={"lemma": "tapa"},
            analyses=(noun, verb),
        )

        self.assertEqual(prepared.analyses, (verb,))
        self.assertTrue(prepared.evidence["contextual_constraint_bypass"])
        self.assertEqual(
            prepared.evidence["contextual_headword_override"], ["tavata"]
        )
        self.assertEqual(prepared.evidence["pos_removed_analysis_ids"], [])
        self.assertEqual(prepared.evidence["lemma_removed_analysis_ids"], [])

        noun_prepared = policy.prepare(
            sentence="Hän teki sen samaan tapaan.",
            surface_form="tapaan",
            observed_pos="VERB",
            observed_grammar={"lemma": "tavata"},
            analyses=(noun, verb),
        )
        self.assertEqual(noun_prepared.analyses, (noun,))
        self.assertEqual(
            noun_prepared.evidence["contextual_headword_override"], ["tapa"]
        )


if __name__ == "__main__":
    unittest.main()
