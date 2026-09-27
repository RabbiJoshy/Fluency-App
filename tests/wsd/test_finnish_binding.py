from __future__ import annotations

import unittest

from fluency.wsd.bindings import binding_for, pos_gate_for
from fluency.wsd.languages.finnish import FinnishWSDAdapter


class FinnishBindingTests(unittest.TestCase):
    def test_binding_uses_wiktionary_without_an_unpinned_pos_model(self) -> None:
        binding = binding_for("fi")
        self.assertEqual(binding.menu_provider, "wiktionary")
        self.assertIsNone(binding.pos_model_role)

    def test_exact_surface_location_preserves_diacritics(self) -> None:
        adapter = FinnishWSDAdapter()
        found = adapter.locate("Hän näki tämän täällä.", "tämän")
        self.assertEqual(
            [(item.observed_text, item.start, item.end) for item in found],
            [("tämän", 9, 14)],
        )
        self.assertEqual(adapter.locate("Han on täällä.", "hän"), ())

    def test_absent_pos_model_never_removes_menu_senses(self) -> None:
        compatible, orthogonal = pos_gate_for("fi")
        self.assertTrue(compatible("verb", "NOUN"))
        self.assertFalse(orthogonal("verb"))


if __name__ == "__main__":
    unittest.main()
