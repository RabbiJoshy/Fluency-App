"""Placement regressions for zoom, setup gutters, and resizing open sheets."""
import shutil
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


@unittest.skipUnless(shutil.which('node'), 'Node.js required')
class SideDockLayoutTests(unittest.TestCase):
    def test_zoom_and_resize_preserve_clear_gutters_and_stacked_sheets(self):
        result = subprocess.run(['node', '-'], cwd=ROOT, text=True, capture_output=True, input=r'''
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const nodes = new Map();
function element(id, hidden = false) {
    const classes = new Set(hidden ? ['hidden'] : []);
    const el = {id, dataset: {}, style: {setProperty() {}}, hidden: false,
        classList: {contains: x => classes.has(x), add: x => classes.add(x),
            remove: x => classes.delete(x), toggle(x, on) {on ? classes.add(x) : classes.delete(x);}},
        getBoundingClientRect() {return this.rect;}};
    nodes.set(id, el);
    return el;
}
const app = element('appContent');
const card = element('flashcard'); card.offsetWidth = 513;
const centre = element('centre');
const setup = element('setupPanel');
const help = element('helpModal');
const settings = element('settingsModal', true);
settings.classList.add('settings-study-only');
const explanation = element('spacedRepetitionInfoModal', true);
const callbacks = {};
let zoom = 1;
const body = element('body');
const context = {window: {innerWidth: 1600, addEventListener(type, fn) {callbacks[type] = fn;}},
    document: {body, documentElement: {}, readyState: 'complete', getElementById: id => nodes.get(id),
        querySelector: s => s === '.card-container' ? centre : setup,
        querySelectorAll: () => [centre, setup]},
    getComputedStyle: () => ({zoom}),
    MutationObserver: class {observe() {}}, ResizeObserver: class {observe() {}},
    requestAnimationFrame(fn) {fn(); return 1;}, cancelAnimationFrame() {}};
function geometry(width, scale = 1) {
    context.window.innerWidth = width; zoom = scale;
    centre.rect = {left: 20, right: width - 20, width: width - 40};
    setup.rect = {left: (width - 1140 * scale) / 2, right: (width + 1140 * scale) / 2, width: 1140 * scale};
}
geometry(1600);
vm.createContext(context);
vm.runInContext(fs.readFileSync('app/js/side-dock.js', 'utf8'), context);
const dock = context.window.sideDock;
assert.equal(dock.placeById('helpModal'), 'left');
geometry(1280, 1.15); callbacks.resize();
assert.equal(help.dataset.dock, undefined, 'zoom must not push a docked sheet over the card');
geometry(1360, 1.15); callbacks.resize();
assert.equal(help.dataset.dock, 'left', 'a sheet docks again when a readable gutter is available');
app.classList.add('hidden');
assert.equal(dock.canDockSheet(), false, 'setup sheets must not overlap the centre column');
geometry(1800); callbacks.resize();
assert.equal(dock.canDockSheet(), true, 'setup sheets can shrink into a sufficient gutter');
app.classList.remove('hidden');
help.classList.add('hidden');
settings.classList.remove('hidden');
assert.equal(dock.placeById('settingsModal'), 'left');
explanation.classList.remove('hidden');
assert.equal(dock.placeById('spacedRepetitionInfoModal'), 'left');
assert.equal(explanation.dataset.dockStack, '');
geometry(1700); callbacks.resize();
assert.equal(explanation.classList.contains('hidden'), false);
assert.equal(explanation.dataset.dockStack, '', 'resize must preserve a sheet stacked over settings');
''')
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
