"""A cached Pages fallback must never restart recursive module preloads."""
from pathlib import Path
import shutil
import subprocess
import unittest

ROOT = Path(__file__).resolve().parents[2]


@unittest.skipUnless(shutil.which('node'), 'Node.js required')
class ServiceWorkerAssetResponsesTests(unittest.TestCase):
    def test_html_assets_are_evicted_and_replaced_without_preload_headers(self):
        result = subprocess.run(['node', '-'], cwd=ROOT, text=True, capture_output=True, input=r'''
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const listeners = {};
const entries = new Map();
const deleted = [];
const writes = [];
let network;
const cache = {
  match: async request => entries.get(request.url || request),
  delete: async request => { deleted.push(request.url); return entries.delete(request.url); },
  put: async (request, response) => { writes.push(request.url || request); },
};
const context = {URL, Request, Response, Map, Set, Promise, console,
  self: {location: {origin: 'https://staging.test', hostname: 'staging.test'},
    registration: {scope: 'https://staging.test/'},
    addEventListener: (name, handler) => {listeners[name] = handler;}},
  caches: {keys: async () => [], open: async () => cache},
  fetch: async () => network.clone(),
};
vm.createContext(context);
vm.runInContext(fs.readFileSync('app/service-worker.js', 'utf8'), context);
const html = () => new Response('<html>fallback</html>', {headers: {
  'Content-Type': 'text/html; charset=utf-8',
  Link: '<js/main.js>; rel="modulepreload"',
}});
async function request(path, mode = 'cors') {
  let response;
  listeners.fetch({request: {url: 'https://staging.test' + path, method: 'GET', mode},
    respondWith: value => {response = value;}});
  return await response;
}
(async () => {
  entries.set('https://staging.test/backend/secrets.json', html());
  network = new Response('{}', {headers: {'Content-Type': 'application/json'}});
  const repaired = await request('/backend/secrets.json');
  assert.equal(await repaired.text(), '{}');
  assert.deepEqual(deleted, ['https://staging.test/backend/secrets.json']);
  assert.equal(repaired.headers.get('Link'), null);

  network = html();
  const missing = await request('/backend/js/main.js');
  assert.equal(missing.status, 404);
  assert.equal(missing.headers.get('Link'), null);
  assert.equal(missing.headers.get('Content-Type'), 'text/plain');
  assert.ok(!writes.includes('https://staging.test/backend/js/main.js'));

  entries.set('https://staging.test/js/main.js', new Response('cached code', {
    headers: {'Content-Type': 'application/javascript'},
  }));
  assert.equal(await (await request('/js/main.js')).text(), 'cached code');
  network = html();
  assert.equal(await (await request('/', 'navigate')).text(), '<html>fallback</html>');
})().catch(error => {console.error(error); process.exitCode = 1;});
''')
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
