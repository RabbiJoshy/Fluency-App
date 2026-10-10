"""Streaming preserves import validation, assignments and release projections."""
import json
from pathlib import Path
import tempfile
import unittest
from datetime import UTC, datetime
from unittest.mock import patch

from tests.wsd import test_importer as fixtures
from fluency.wsd.importer import import_wsd_assignments, WSDAssignmentImportError
from fluency.wsd.splice import write_spliced_bundle
from fluency.wsd.streaming import load_streamed_bundle
from fluency.release.run_candidate import _load_assignments, display_pool_for_card, build_inactive_run_candidate
from fluency.core.hashing import file_content_id


class StreamingTests(unittest.TestCase):
    def write_bundle(self, path, bundle):
        write_spliced_bundle(path, run_id=bundle['run_id'], language=bundle['language'],
            mode=bundle['mode'], inputs=bundle['inputs'], method=bundle['method'],
            sampling_policy=bundle['sampling']['policy'], carried=bundle['assignments'],
            fresh=(), declared=())

    def test_identical_import_and_release_projection(self):
        with tempfile.TemporaryDirectory() as directory:
            ws, run, path, bundle = fixtures.WSDImporterTests()._fixture(Path(directory))
            self.write_bundle(path, bundle)
            args = dict(run_id=run.name, language='fr', mode='speech', bundle_path=path)
            output = import_wsd_assignments(ws, **args)
            before = {name: (output / name).read_bytes() for name in
                      ('assignments.jsonl', 'method.json', 'report.json')}
            import_wsd_assignments(ws, **args, streaming=True, overwrite=True)
            for name, raw in before.items():
                self.assertEqual(raw, (output / name).read_bytes(), name)
            normal = _load_assignments(run, selection_projection='provider_only')
            bounded = _load_assignments(run, selection_projection='provider_only', memory_bounded=True)
            for pair, row in normal.items():
                self.assertEqual(row, bounded.get(pair))
                self.assertEqual(row, bounded.get(pair[0])[pair[1]])
                pool = [{'sentence_id': pair[1]}, {'sentence_id': 'missing'}]
                self.assertEqual(display_pool_for_card(pool, normal, pair[0], wsd_ran=True),
                                 display_pool_for_card(pool, bounded, pair[0], wsd_ran=True))
            self.assertEqual(bounded.counts['assigned'], 1)
            self.assertIsNone(bounded.get(('missing', 'missing')))

    def test_streaming_still_rejects_stale_model_duplicate_and_missing_rows(self):
        for failure in ('stale', 'model', 'duplicate', 'missing'):
            with self.subTest(failure=failure), tempfile.TemporaryDirectory() as directory:
                ws, run, path, bundle = fixtures.WSDImporterTests()._fixture(Path(directory))
                if failure == 'stale':
                    bundle['assignments'][0]['sense_menu_content_id'] = 'sha256:' + '0' * 64
                elif failure == 'model':
                    bundle['assignments'][0]['model_revisions'] = {'gloss': 'wrong@1'}
                elif failure == 'missing':
                    bundle['assignments'] = []
                self.write_bundle(path, bundle)
                if failure == 'duplicate':
                    lines = path.read_text().splitlines()
                    lines.insert(2, lines[1])
                    lines[1] += ','
                    path.write_text('\n'.join(lines) + '\n')
                with self.assertRaises(WSDAssignmentImportError):
                    import_wsd_assignments(ws, run_id=run.name, language='fr', mode='speech',
                                           bundle_path=path, streaming=True)
                self.assertFalse((run / 'stages/04_wsd_assignments/output').exists())

    def test_malformed_arrays_are_rejected(self):
        for rows in ('{}\n{}', '{},', '{}\n], "sampling": {}\n{}'):
            with self.subTest(rows=rows), tempfile.TemporaryDirectory() as directory:
                path = Path(directory) / 'bundle.json'
                path.write_text('{"version": 1, "assignments": [\n' + rows + '\n], "sampling": {}}\n')
                with self.assertRaises(ValueError):
                    list(load_streamed_bundle(path)['assignments'])

    def test_assignment_cache_moves_between_cards(self):
        from fluency.release.assignment_store import AssignmentFile
        with tempfile.TemporaryDirectory() as directory:
            _, _, _, bundle = fixtures.WSDImporterTests()._fixture(Path(directory))
            row = bundle['assignments'][0]
            second = {**row, 'card_id': 'second-card'}
            path = Path(directory) / 'assignments.jsonl'
            path.write_text(json.dumps(row) + '\n' + json.dumps(second) + '\n')
            store = AssignmentFile(path, 'provider_only')
            store.get(row['card_id'])
            store.get(second['card_id'])
            self.assertEqual(store.cached_card, second['card_id'])
            self.assertEqual(len(store.cached_rows), 1)
            self.assertEqual(store.get((row['card_id'], row['sentence_id']))['card_id'], row['card_id'])

    def test_complete_deck_selection_is_identical(self):
        with tempfile.TemporaryDirectory() as directory:
            ws, run, path, bundle = fixtures.WSDImporterTests()._fixture(Path(directory))
            menu_path = run / 'stages/02_sense_menu/output/sense-menu.json'
            menu = json.loads(menu_path.read_text())
            menu['cards'][0]['analyses'][0]['senses'][0].update(
                translation='want', source_reference='fixture:want')
            menu_path.write_text(json.dumps(menu))
            bank_path = run / 'stages/03_sentence_harvest/output/sentence-bank.jsonl'
            bank_path.write_text(json.dumps({'sentence_id': bundle['assignments'][0]['sentence_id'],
                'source': {'type': 'fixture', 'name': 'fixture'}, 'target': {'text': 'Je veux apprendre.'},
                'translation': {'text': 'I want to learn.'}}) + '\n')
            bundle['inputs']['sense_menu'] = file_content_id(menu_path)
            bundle['inputs']['sentence_bank'] = file_content_id(bank_path)
            bundle['assignments'][0]['sense_menu_content_id'] = file_content_id(menu_path)
            self.write_bundle(path, bundle)
            import_wsd_assignments(ws, run_id=run.name, language='fr', mode='speech',
                                   bundle_path=path, streaming=True)
            with patch('fluency.release.run_candidate.compose_release') as compose:
                args = dict(run_id=run.name, release_id='fixture', language='fr',
                            created_at=datetime(2026, 10, 10, tzinfo=UTC))
                build_inactive_run_candidate(ws, **args)
                normal = compose.call_args.args[1:]
                build_inactive_run_candidate(ws, **args, memory_bounded=True)
                self.assertEqual(normal, compose.call_args.args[1:])

    def test_multiword_and_provider_projections_remain_identical(self):
        with tempfile.TemporaryDirectory() as directory:
            fixture = fixtures.WSDImporterTests()
            ws, run, path, bundle = fixture._fixture(Path(directory))
            fixture._add_mwe_alternate(bundle, pin_inventory=True)
            self.write_bundle(path, bundle)
            import_wsd_assignments(ws, run_id=run.name, language='fr', mode='speech',
                                   bundle_path=path, streaming=True)
            for projection in ('provider_only', 'mwe_augmented'):
                normal = _load_assignments(run, selection_projection=projection)
                bounded = _load_assignments(run, selection_projection=projection, memory_bounded=True)
                for pair, row in normal.items():
                    self.assertEqual(row, bounded.get(pair))

    def test_sentence_file_keeps_unicode_lines_and_rejects_duplicates(self):
        from fluency.release.assignment_store import SentenceFile
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'sentences.jsonl'
            row = {'sentence_id': 'sentence', 'target': {'text': 'a\u0085b\u2028c'}}
            path.write_text(json.dumps(row, ensure_ascii=False) + '\n')
            store = SentenceFile(path)
            self.assertEqual(store.get('sentence'), row)
            self.assertEqual(len(store), 1)
            self.assertIsNone(store.get('missing'))
            path.write_text(path.read_text() * 2)
            with self.assertRaises(ValueError):
                SentenceFile(path)
