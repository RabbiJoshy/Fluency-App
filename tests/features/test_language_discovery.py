"""Languages are discovered, not registered.

Adding a language used to mean editing eight shared files -- two if-chains, the
CLI asset table, the deployment key map, two JS order lists, a TTS map and the
app config. Two sessions adding two languages collided in all of them.
"""

import unittest

from fluency.core.languages import app_data_routes, language_directories, language_keys
from fluency.languages.surfaces import (
    LanguageSupportError,
    normalizer_for_language,
    registered_languages,
    typography_canonicalizer_for_language,
)


class DiscoveryTests(unittest.TestCase):
    def test_languages_are_found_from_their_packages(self) -> None:
        self.assertEqual(set(registered_languages()) & {"es", "fr", "pt"}, {"es", "fr", "pt"})

    def test_normalizer_resolves_per_language(self) -> None:
        self.assertEqual(normalizer_for_language("pt")("  Você  "), "você")
        self.assertEqual(normalizer_for_language("fi")("  YÖPÖYTÄ  "), "yöpöytä")

    def test_unknown_language_names_what_is_available(self) -> None:
        with self.assertRaises(LanguageSupportError) as caught:
            normalizer_for_language("zz")
        self.assertIn("available:", str(caught.exception))

    def test_missing_optional_helper_is_explicit(self) -> None:
        """A language without a typography canonicalizer must not silently
        fall back to another language's rules. (Spanish was the real example
        until lyrics v20 gave it one; every package now has one, so a stand-in
        module plays the part.)"""

        from types import ModuleType
        from unittest import mock

        bare = ModuleType("fluency.languages.bare.surfaces")
        with mock.patch("fluency.languages.surfaces._surfaces_module", return_value=bare), \
                self.assertRaises(LanguageSupportError) as caught:
            typography_canonicalizer_for_language("es")
        self.assertIn("canonicalize_typography", str(caught.exception))


class DerivedRegistryTests(unittest.TestCase):
    def test_keys_include_discovered_and_app_only_languages(self) -> None:
        keys = language_keys()
        self.assertEqual(keys["pt"], "portuguese")
        self.assertEqual(keys["nl"], "dutch")
        self.assertEqual(keys["fi"], "finnish")

    def test_data_directories_are_capitalised(self) -> None:
        self.assertEqual(language_directories()["pt"], "Portuguese")

    def test_asset_routes_are_generated_for_every_language(self) -> None:
        routes = app_data_routes()
        self.assertEqual(
            routes["/Data/Portuguese/vocabulary.index.json"], ("pt", "index_path")
        )
        self.assertEqual(len(routes), len(language_keys()) * 6)

    def test_cli_uses_the_derived_routes(self) -> None:
        from fluency.cli import APP_DATA_ROUTES

        self.assertEqual(APP_DATA_ROUTES, app_data_routes())


if __name__ == "__main__":
    unittest.main()
