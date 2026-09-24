import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock

from fluency.surfaces.entities import (
    WikipediaEntity,
    WikipediaEntityResolver,
    infer_entity_type,
)
from fluency.surfaces import trust


class TestEntityInference(unittest.TestCase):
    def test_infer_place(self):
        self.assertEqual(infer_entity_type("municipio de Puerto Rico"), "place")
        self.assertEqual(infer_entity_type("capital de Antioquia, Colombia"), "place")
        self.assertEqual(infer_entity_type("estadio cubierto en San Juan"), "place")

    def test_infer_person(self):
        self.assertEqual(infer_entity_type("rapero y cantante puertorriqueño"), "person")
        self.assertEqual(infer_entity_type("futbolista profesional argentino"), "person")

    def test_infer_brand(self):
        self.assertEqual(infer_entity_type("fabricante italiano de automóviles"), "brand")
        self.assertEqual(infer_entity_type("marca de ropa de lujo"), "brand")

    def test_infer_work(self):
        self.assertEqual(infer_entity_type("álbum de estudio de Bad Bunny"), "work")
        self.assertEqual(infer_entity_type("canción del año 2022"), "work")

    def test_infer_other(self):
        self.assertEqual(infer_entity_type("concepto filosófico"), "other")


class TestWikipediaEntityDeclaredEntry(unittest.TestCase):
    def test_to_declared_entry_matches_schema(self):
        entity = WikipediaEntity(
            query="Choliseo",
            canonical_title="Coliseo de Puerto Rico José Miguel Agrelot",
            description="estadio cubierto en San Juan",
            extract="El Coliseo de Puerto Rico...",
            entity_type="place",
            language="es",
        )
        declared = entity.to_declared_entry(author="unit_test")
        self.assertEqual(declared.kind, "entity")
        self.assertEqual(declared.surface, "Choliseo")
        self.assertEqual(declared.language, "es")
        self.assertEqual(declared.payload["entity_type"], "place")
        self.assertEqual(declared.payload["description"], "estadio cubierto en San Juan")
        self.assertEqual(declared.trust, trust.DERIVED)


class TestWikipediaResolverMocked(unittest.TestCase):
    @patch("urllib.request.urlopen")
    def test_resolver_successful_fetch(self, mock_urlopen):
        search_resp = MagicMock()
        search_resp.read.return_value = b'{"query": {"search": [{"title": "Bayam\xc3\xb3n"}]}}'
        search_resp.__enter__.return_value = search_resp

        sum_resp = MagicMock()
        sum_resp.read.return_value = b'{"title": "Bayam\xc3\xb3n", "description": "municipio en Puerto Rico", "extract": "Bayam\xc3\xb3n es..."}'
        sum_resp.__enter__.return_value = sum_resp

        mock_urlopen.side_effect = [search_resp, sum_resp]

        resolver = WikipediaEntityResolver()
        result = resolver.resolve("Bayamón", language="es")

        self.assertIsNotNone(result)
        self.assertEqual(result.canonical_title, "Bayamón")
        self.assertEqual(result.entity_type, "place")

        # Second call hits memory cache
        cached = resolver.resolve("Bayamón", language="es")
        self.assertIs(cached, result)
        self.assertEqual(mock_urlopen.call_count, 2)

    @patch("urllib.request.urlopen")
    def test_resolver_handles_not_found(self, mock_urlopen):
        search_resp = MagicMock()
        search_resp.read.return_value = b'{"query": {"search": []}}'
        search_resp.__enter__.return_value = search_resp
        mock_urlopen.return_value = search_resp

        resolver = WikipediaEntityResolver()
        result = resolver.resolve("asdkfjhasdf98234", language="es")
        self.assertIsNone(result)


if __name__ == "__main__":
    unittest.main()
