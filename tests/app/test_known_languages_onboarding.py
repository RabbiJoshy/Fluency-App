import unittest
import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

@unittest.skipUnless(shutil.which('node'), 'Node.js required')
class KnownLanguagesOnboardingTests(unittest.TestCase):
    def test_target_language_excluded_and_polish_available(self):
        script = r'''
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');

const config = JSON.parse(fs.readFileSync('app/config/config.json', 'utf8'));

// Minimal DOM simulation
function createElement(tag) {
    const el = {
        tagName: tag.toUpperCase(),
        children: [],
        attributes: {},
        classList: {
            _classes: new Set(),
            add(c) { this._classes.add(c); },
            remove(c) { this._classes.delete(c); },
            contains(c) { return this._classes.has(c); }
        },
        dataset: {},
        innerHTML: '',
        appendChild(child) { this.children.push(child); },
        setAttribute(k, v) { this.attributes[k] = String(v); },
        getAttribute(k) { return this.attributes[k]; },
        addEventListener(event, fn) {}
    };
    Object.defineProperty(el, 'disabled', {
        get() { return el.attributes['disabled'] === 'true' || el.attributes['disabled'] === ''; },
        set(v) { if (v) el.attributes['disabled'] = 'true'; else delete el.attributes['disabled']; }
    });
    return el;
}

const choicesContainer = createElement('div');

const context = {
    console,
    config,
    selectedLanguage: 'czech',
    document: {
        getElementById(id) {
            if (id === 'knownLanguagesModalChoices') return choicesContainer;
            return createElement('div');
        },
        createElement
    },
    window: {
        knownLanguageOptions: () => ['en', 'pl', 'es', 'fr', 'pt', 'de', 'it', 'ru', 'sk', 'uk', 'nl', 'sv', 'cs', 'fi'],
        knownLanguageFlag: () => '🌐',
        knownLanguageLabel: (c) => c.toUpperCase(),
        availableKnownLanguages: () => ['en', 'pl']
    }
};
context.globalThis = context;
context.window.globalThis = context;

// Extract targetRouteCode, getKnownLanguagesForTarget, renderKnownLanguagesModalChoices from main.js
let mainSrc = fs.readFileSync('app/js/main.js', 'utf8');

// Replace top-level import/export
mainSrc = mainSrc.replace(/^import[\s\S]*?;[ \t]*$/mg, '');

// Run with routes helpers defined
const routesSrc = fs.readFileSync('app/js/routes.js', 'utf8').replace(/^export /mg, '');
vm.runInNewContext(routesSrc + '\n' + `
let introSelectedCodes = new Set(['en']);
let introLanguageLabels = {};
let knownLanguagesScoped = false;
` + mainSrc.slice(mainSrc.indexOf('function targetRouteCode')), context);

// Test 1: getKnownLanguagesForTarget excludes target language code
const czechOptions = context.window.getKnownLanguagesForTarget('czech');
assert(!czechOptions.includes('cs'), 'Czech target must exclude "cs" from known choices');
assert(czechOptions.includes('pl'), 'Czech target must include Polish "pl"');
assert(czechOptions.includes('en'), 'Czech target must include English "en"');
assert.equal(czechOptions.length, 13, 'Must have 13 known languages when 1 target is excluded');

const spanishOptions = context.window.getKnownLanguagesForTarget('spanish');
assert(!spanishOptions.includes('es'), 'Spanish target must exclude "es"');
assert(spanishOptions.includes('cs'), 'Spanish target must include "cs"');

// Test 2: renderKnownLanguagesModalChoices in general onboarding (unscoped)
// Polish must NOT be marked "Coming soon" and must NOT be disabled
context.window.renderKnownLanguagesModalChoices(czechOptions);
assert.equal(choicesContainer.children.length, 13);
const plBtn = choicesContainer.children.find(b => b.dataset.code === 'pl');
assert(plBtn, 'Polish button must exist in choices');
assert.equal(plBtn.disabled, false, 'Polish button must be enabled in onboarding');
assert(!plBtn.innerHTML.includes('Coming soon'), 'Polish must not show "Coming soon" in onboarding');

console.log('Known languages onboarding checks passed successfully.');
''';
        result = subprocess.run(['node', '-e', script], cwd=ROOT, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)

if __name__ == '__main__':
    unittest.main()
