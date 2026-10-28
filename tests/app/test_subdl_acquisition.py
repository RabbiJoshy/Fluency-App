"""Guard provider metadata and series-specific episode validation."""
import importlib.util
from pathlib import Path
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]


def load(name):
    spec = importlib.util.spec_from_file_location(name, ROOT / 'scripts' / f'{name}.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


acquisition = load('refresh_series_from_subdl')
builder = load('build_casa_de_papel')
probe = load('probe_subdl_series')


class SubdlAcquisitionTests(unittest.TestCase):
    def test_broader_search_fallback_cannot_silently_change_identity(self):
        params = {'sd_id': '123', 'languages': 'ES', 'season_number': 1}
        payload = {'results': [{'sd_id': 123}], 'subtitles': [{'language': 'ES', 'season': 1}]}
        probe.validate_catalogue(payload, params)
        for bad in [dict(payload, results=[{'sd_id': 456}]),
                    dict(payload, subtitles=[{'language': 'EN', 'season': 1}]),
                    dict(payload, subtitles=[{'language': 'ES', 'season': 2}])]:
            with self.assertRaises(RuntimeError):
                probe.validate_catalogue(bad, params)

    def test_legacy_accent_decoding_uses_unique_archive_filename(self):
        actual = ['Élite - 01x01 - Bienvenidos.srt', 'Élite - 01x02 - Deseo.srt']
        self.assertEqual(acquisition.resolve_members(['�lite - 01x02 - Deseo.srt'], actual), [actual[1]])
        with self.assertRaisesRegex(ValueError, 'ambiguous'):
            acquisition.resolve_members(['�lite.srt'], ['Élite.srt', 'Álite.srt'])
        with self.assertRaisesRegex(ValueError, 'absent'):
            acquisition.resolve_members(['�lite - 01x03.srt'], actual)

    def test_elite_episode_validation_uses_its_own_numbering(self):
        cues = [{'spanish': 'Hola.', 'start_ms': i * 10000, 'end_ms': i * 10000 + 1000}
                for i in range(200)]
        manifest = {'episodes': [{'season': 2, 'episode': 8}], 'expectedEpisodeCounts': [8] * 8}
        with patch.object(builder, 'read_source', return_value=b''), patch.object(builder, 'parse_srt', return_value=cues):
            self.assertEqual(builder.load_episodes(manifest, ROOT, True)[0]['episode'], 'S02E08')
            with self.assertRaisesRegex(ValueError, 'unexpected'):
                builder.load_episodes({'episodes': manifest['episodes']}, ROOT, True)
            with self.assertRaisesRegex(ValueError, 'Missing episodes'):
                builder.load_episodes(manifest, ROOT, False)


if __name__ == '__main__':
    unittest.main()
