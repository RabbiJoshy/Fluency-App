"""Deck switches must carry the release-bound assets used before rows load."""
import json
import unittest
from pathlib import Path

APP = Path(__file__).resolve().parents[2] / 'app'


class SpeechAssetBindingsTests(unittest.TestCase):
    def test_spanish_portuguese_default_assets_belong_to_the_same_release(self):
        config = json.loads((APP / 'config/config.json').read_text())
        for language in config['languages'].values():
            if language.get('routeCode') not in {'es', 'pt'}:
                continue
            with self.subTest(language=language['routeCode']):
                index = language['indexPath']
                base = index.removesuffix('/app/vocabulary.index.json')
                release = base.rsplit('/', 1)[1]
                for field in ('examplesPath', 'studyStructurePath', 'releaseManifestPath',
                              'releaseCompositionPath', 'conjugationsPath'):
                    self.assertTrue(language[field].startswith(base + '/'), field)
                for field, binding, expected in (
                    ('frequencyPath', 'indexPath', index),
                    ('estimationPoolPath', 'release', index),
                    ('cognatesPath', 'built_from_release_id', release),
                    ('mergeExceptionsPath', 'release_id', release),
                ):
                    payload = json.loads((APP / language[field]).read_text())
                    self.assertEqual(payload[binding], expected, field)
                if language.get('coveragePath'):
                    self.assertTrue((APP / language['coveragePath']).is_file())
