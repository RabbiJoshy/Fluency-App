"""Flag images use app-relative URLs and are available before offline use."""
from pathlib import Path
import re
import shutil
import subprocess
import unittest
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[2]


class FlagAssetTests(unittest.TestCase):
    def test_every_supported_flag_is_valid_and_precached(self):
        source = (ROOT / 'app/js/flags.js').read_text()
        available = source.split('const AVAILABLE = new Set([')[1].split(']);')[0]
        worker = (ROOT / 'app/service-worker.js').read_text()
        for code in re.findall(r"'([a-z]{2})'", available):
            with self.subTest(code=code):
                asset = ROOT / f'app/assets/flags/{code}.svg'
                self.assertEqual(ET.parse(asset).getroot().tag, '{http://www.w3.org/2000/svg}svg')
                self.assertIn(f"'/assets/flags/{code}.svg'", worker)

    @unittest.skipUnless(shutil.which('node'), 'Node.js required')
    def test_local_source_icons_follow_module_location(self):
        result = subprocess.run(['node', '-'], cwd=ROOT, capture_output=True, text=True, input=r"""
const fs = require('node:fs'), vm = require('node:vm'), assert = require('node:assert/strict');
const raw = fs.readFileSync('app/js/flashcards.js', 'utf8');
const start = raw.indexOf('function exampleFaviconHTML(');
const end = raw.indexOf('\n}', start) + 2;
const source = raw.slice(start, end).replace('import.meta.url', "'https://example.test/Fluency-App/js/flashcards.js?v=build'");
const context = {URL};
vm.createContext(context);
vm.runInContext(source, context);
assert.ok(context.exampleFaviconHTML('tatoeba.org').includes('https://example.test/Fluency-App/icons/tatoeba.svg'));
assert.ok(context.exampleFaviconHTML('wiktionary.org').includes('https://example.test/Fluency-App/icons/wikipedia-w.svg'));
""")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    @unittest.skipUnless(shutil.which('node'), 'Node.js required')
    def test_flag_urls_follow_module_location_not_page_location(self):
        result = subprocess.run(['node', '-'], cwd=ROOT, capture_output=True, text=True, input=r'''
const fs = require('node:fs'), vm = require('node:vm'), assert = require('node:assert/strict');
const raw = fs.readFileSync('app/js/flags.js', 'utf8');
for (const base of ['https://example.test/', 'https://example.test/Fluency-App/', 'https://example.test/Fluency-App/app/']) {
    const source = raw.replace(/export /g, '').replace('import.meta.url', JSON.stringify(base + 'js/flags.js?v=build'));
    const context = { URL, document: {createElement() { return { dataset: {} }; }} };
    vm.createContext(context);
    vm.runInContext(source, context);
    const image = context.flagImgElement('pt');
    assert.equal(image.src, base + 'assets/flags/pt.svg');
    assert.ok(context.flagImgHTML('pt', 'Portugal').includes(`src="${image.src}"`));
    assert.equal(context.flagImgHTML('unknown'), '');
    assert.equal(context.flagCodeFromEmoji('🇵🇹'), 'pt');
    assert.equal(context.restoreFlagEmoji, undefined, 'never substitute emoji for an image failure');
}
''')
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
