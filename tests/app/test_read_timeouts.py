"""Stalled connections/bodies settle; a partial refresh remains retryable."""
from pathlib import Path
import shutil
import subprocess
import unittest

ROOT = Path(__file__).resolve().parents[2]


@unittest.skipUnless(shutil.which('node'), 'Node.js required')
class ReadTimeoutTests(unittest.TestCase):
    def run_node(self, source):
        result = subprocess.run(['node', '--input-type=module', '-'], cwd=ROOT,
                                input=source, text=True, capture_output=True, timeout=10)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_stalled_headers_and_body_abort_and_allow_retry(self):
        self.run_node(r'''
import assert from 'node:assert/strict';
import { readJsonWithTimeout } from './app/js/read-request.js';
for (const stallBody of [false, true]) {
    let signal;
    globalThis.fetch = async (_, options) => {
        signal = options.signal;
        if (!stallBody) return new Promise(() => {});
        return { ok: true, json: () => new Promise(() => {}) };
    };
    await assert.rejects(readJsonWithTimeout('/test', {}, 10), { name: 'TimeoutError' });
    assert.equal(signal.aborted, true);
}
let signal;
globalThis.fetch = async (_, options) => {
    signal = options.signal;
    return { ok: true, json: async () => ({ saved: 42 }) };
};
assert.deepEqual((await readJsonWithTimeout('/test', {}, 10)).data, { saved: 42 });
await new Promise(resolve => setTimeout(resolve, 20));
assert.equal(signal.aborted, false, 'successful reads clear their timers');
globalThis.fetch = async () => ({ ok: false, status: 404 });
const missing = await readJsonWithTimeout('/missing');
assert.equal(missing.response.status, 404);
assert.equal(missing.data, null);
''')

    def test_failed_and_partial_progress_reads_preserve_cache_and_watermark(self):
        self.run_node(r'''
import assert from 'node:assert/strict';
import fs from 'node:fs';
import vm from 'node:vm';
const auth = fs.readFileSync('app/js/auth.js', 'utf8');
const source = auth.slice(auth.indexOf('async function loadUserProgressFromSheetNow()'),
                          auth.indexOf('// Save the level estimate'));
const cached = { progress: { old: { correct: 3 } }, itemProgress: { detail: { correct: 2 } },
    estimates: {}, backendSchema: 4, syncVersion: 'v1', lastFullSyncAt: Date.now() };
let failedAction = 'load';
const context = {
    console: { log() {}, error() {}, warn() {} }, Date, JSON,
    currentUser: { initials: 'JOSHUA' }, GOOGLE_SCRIPT_URL: '/api',
    progressData: {}, itemProgressData: {}, levelEstimates: {},
    progressSyncVersion: '', progressLastFullSyncAt: 0, progressBackendSchemaVersion: 4,
    FULL_SYNC_INTERVAL_MS: 259200000,
    getIsolatedSyncUser: x => x, localStorage: { getItem: () => JSON.stringify(cached) },
    dbGet: async () => null, detectProgressBackendSchema: async () => 4,
    readJsonWithTimeout: async (_, options) => {
        const action = JSON.parse(options.body).action;
        if (action === failedAction) throw new Error('timed out');
        return { data: { success: true, data: { delta: true, version: 'v2',
            progress: [{ wordId: 'new', correct: 1 }], items: [{ itemId: 'newDetail', correct: 1 }] } } };
    },
    setProgressReadFailed: value => { context.failed = value; },
    applyPendingProgressOverlay: data => { data.pending = { correct: 1 }; },
    applyPendingItemProgressOverlay() {}, applyPendingMetaProgressOverlay() {},
    updateIncorrectButtonVisibility() {}, updateTotalStatsButtonVisibility() {},
    applyRemoteFastTrack() {}, cacheProgressLocally() {},
    getProgressUiFingerprint: () => JSON.stringify(context.progressData),
    bumpProgressEpoch() {}, markProgressLoaded() {},
};
context.window = context;
vm.createContext(context);
vm.runInContext(source, context);
await context.loadUserProgressFromSheetNow();
assert.equal(context.progressData.old.correct, 3);
assert.equal(context.progressData.pending.correct, 1);
assert.equal(context.failed, true);
assert.equal(context.progressSyncVersion, 'v1');
failedAction = 'loadItems';
await context.loadUserProgressFromSheetNow();
assert.equal(context.itemProgressData.detail.correct, 2);
assert.equal(context.progressSyncVersion, 'v1', 'partial replies cannot skip missing rows');
assert.equal(context.failed, true);
failedAction = null;
await context.loadUserProgressFromSheetNow();
assert.equal(context.itemProgressData.newDetail.correct, 1);
assert.equal(context.progressSyncVersion, 'v2');
assert.equal(context.failed, false);
''')
