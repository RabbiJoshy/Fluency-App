"""Cached translation measurements are metadata, never selection inputs."""
from datetime import UTC, datetime
import copy
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from fluency.core.hashing import file_content_id
from fluency.release.run_candidate import build_inactive_run_candidate
from fluency.release.translation_alignment import load_translation_alignment, translation_alignment_metadata
from scripts.build_example_alignment import build_companion
from tests.wsd import test_importer as fixtures


class TranslationAlignmentTests(unittest.TestCase):
    def test_native_release_carries_measurement_without_changing_selection(self):
        with tempfile.TemporaryDirectory() as directory:
            ws, run, _, bundle = fixtures.WSDImporterTests()._fixture(Path(directory))
            menu_path = run / 'stages/02_sense_menu/output/sense-menu.json'
            menu = json.loads(menu_path.read_text())
            menu['cards'][0]['analyses'][0]['senses'][0].update(translation='want', source_reference='fixture:want')
            menu_path.write_text(json.dumps(menu))
            sid = bundle['assignments'][0]['sentence_id']
            bank_path = run / 'stages/03_sentence_harvest/output/sentence-bank.jsonl'
            bank_path.write_text(json.dumps({'sentence_id': sid,
                'source': {'type': 'fixture', 'name': 'fixture'}, 'target': {'text': 'Je veux apprendre.'},
                'translation': {'text': 'I want to learn.'}}) + '\n')
            with patch('fluency.release.run_candidate.compose_release') as compose:
                args = dict(run_id=run.name, release_id='fixture', language='fr', created_at=datetime(2026,10,10,tzinfo=UTC))
                build_inactive_run_candidate(ws, **args)
                before = copy.deepcopy(compose.call_args.args[2])
                selection_path = run / 'stages/05_example_selection/output/selection.json'
                selected = selection_path.read_bytes()
                cache_path = ws.root / 'embeddings/alignment/fr.json'
                cache_path.parent.mkdir(parents=True)
                cache_path.write_text(json.dumps({'model':'sentence-transformers/LaBSE',
                    'alignment_version':'labse-cosine/v1','scores':{sid:.97}}))
                build_inactive_run_candidate(ws, **args)
                after = copy.deepcopy(compose.call_args.args[2])
                composition = compose.call_args.args[1]
                self.assertEqual(selection_path.read_bytes(), selected)
                layer = composition['layers']['translation_alignment']
                self.assertEqual(layer['artifact_id'], file_content_id(cache_path))
                for card in after['cards']:
                    for example in card['examples']:
                        alignment = example['metadata']['translation_alignment']
                        self.assertEqual(alignment['score'],.97)
                        example['metadata']['translation_alignment'] = None
                self.assertEqual(after, before, 'Only display metadata may change')

    def test_companion_joins_by_sentence_id_without_modifying_release(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);source=root/'releases/test/app';source.mkdir(parents=True)
            manifest={'example_format':'slim-example/v1','shards':[{'path':'set1.json'}]}
            (source/'vocabulary.examples.manifest.json').write_text(json.dumps(manifest))
            examples={'card':{'m':[[{'t':'a','e':'b','i':'abc'},{'t':'x','e':'y','i':'missing'}]],
                'u':[{'target':'a','metadata':{'sentence_id':'sentence_abc'}}]}}
            source_file=source/'set1.json';source_file.write_text(json.dumps(examples));before=source_file.read_bytes()
            cache=root/'cache.json';cache.write_text(json.dumps({'model':'LaBSE','alignment_version':'v1',
                'scores':{'sentence_abc':0,'unselected':.99}}))
            output=root/'companion';result=build_companion(root,'releases/test/app/examples.json',cache,output)
            self.assertEqual(json.loads((output/'set1.json').read_text()),{'sentence_abc':0})
            self.assertEqual(result['card_shards'],{'card':'set1.json'})
            self.assertEqual((result['example_count'],result['scored_example_count']),(3,2))
            self.assertEqual(source_file.read_bytes(),before)
            self.assertEqual(translation_alignment_metadata(load_translation_alignment(cache),'absent'),None)
            self.assertEqual(translation_alignment_metadata(load_translation_alignment(root/'absent'),'absent'),None)

    def test_invalid_measurements_are_rejected_instead_of_claimed(self):
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'cache.json'
            for score in [True, '0.9', 2, float('nan')]:
                path.write_text(json.dumps({'model':'LaBSE','alignment_version':'v1','scores':{'s':score}}))
                with self.subTest(score=score),self.assertRaises(ValueError):load_translation_alignment(path)
