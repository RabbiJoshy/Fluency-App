"""A cached Pages fallback must never restart recursive module preloads."""
from pathlib import Path
import shutil
import subprocess
import unittest

ROOT = Path(__file__).resolve().parents[2]


@unittest.skipUnless(shutil.which('node'), 'Node.js required')
class ServiceWorkerAssetResponsesTests(unittest.TestCase):
    def test_deployed_precache_has_no_duplicate_requests(self):
        import json
        from scripts.build_pages_site import stamp
        worker = stamp((ROOT / 'app/service-worker.js').read_text(), 'regression-build')
        result = subprocess.run(['node', '-'], cwd=ROOT, text=True, capture_output=True, input=r"""
const assert = require('node:assert/strict'), vm = require('node:vm');
const handlers = {};
let installed;
const context = {
  URL, Set, console,
  Request: class { constructor(url) { this.url = new URL(url, 'https://example.test').href; } },
  self: { registration: {scope:'https://example.test/Fluency-App/'},
    location: {hostname:'example.test'}, addEventListener(name, fn) { handlers[name] = fn; } },
  caches: { async open() { return { async addAll(requests) {
    const urls = requests.map(r => r.url);
    assert.equal(new Set(urls).size, urls.length, 'duplicate requests abort browser cache installation');
    assert.ok(urls.includes('https://example.test/Fluency-App/icons/tatoeba.svg'));
    assert.ok(urls.includes('https://example.test/Fluency-App/assets/flags/pt.svg'));
  }}; } },
};
vm.runInNewContext(""" + json.dumps(worker) + r""", context);
handlers.install({waitUntil(p) { installed = p; }});
installed.catch(error => { console.error(error); process.exitCode = 1; });
""")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

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

    def test_worker_update_starts_even_if_page_load_never_finishes(self):
        result = subprocess.run(['node', '-'], cwd=ROOT, text=True, capture_output=True, input=r'''
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const source = fs.readFileSync('app/js/main.js', 'utf8');
const start = source.indexOf("if ('serviceWorker' in navigator)");
const end = source.indexOf('// All available artist configs', start);
let registered = 0;
const context = {
  navigator: {serviceWorker: {register() {registered++; return new Promise(() => {});}}},
  window: {addEventListener() { /* Simulate a load event that never arrives. */ }},
};
vm.runInNewContext(source.slice(start, end), context);
assert.equal(registered, 1, 'worker recovery must not wait for stalled page loading');
''')
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_staging_uses_public_services_without_probing_missing_backend(self):
        result = subprocess.run(['node', '-'], cwd=ROOT, text=True, capture_output=True, input=r'''
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const source = fs.readFileSync('app/js/auth.js', 'utf8');
const start = source.indexOf('async function loadSecrets()');
const end = source.indexOf('// modern Navigation', start);
const bodyEnd = source.indexOf('\n}\n', start) + 3;
let fetched = false;
const context = {config: {publicServices: {spotifyClientId: 'public-client', progressSyncUrl: 'public-sync'}},
  window: {}, IS_STAGING: true, PASSWORDLESS_ENABLED: true, PASSWORDLESS_SYNC_URL: 'staging-sync',
  fetch() {fetched = true; throw new Error('must not request missing backend');}};
vm.createContext(context);
vm.runInContext(source.slice(start, bodyEnd), context);
(async () => {
  await vm.runInContext('loadSecrets()', context);
  assert.equal(fetched, false);
  assert.equal(context.window._spotifyClientId, 'public-client');
  assert.equal(context.GOOGLE_SCRIPT_URL, 'staging-sync');
})().catch(error => {console.error(error); process.exitCode = 1;});
''')
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
