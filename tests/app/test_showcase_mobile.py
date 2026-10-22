"""Regression tests for mobile layout and showcase polish in Tutorial, Walkthrough, and About."""
from pathlib import Path
import shutil
import subprocess
import unittest

ROOT = Path(__file__).resolve().parents[2]


@unittest.skipUnless(shutil.which('node'), 'Node.js required')
class ShowcaseMobileTests(unittest.TestCase):
    def test_tutorial_notes_concise_and_placeholder_free_across_languages(self):
        """Every tutorial note text across all 4 languages must be <= 180 characters with no leftover {placeholders}."""
        result = subprocess.run(
            ['node', '--input-type=module', '-'], cwd=ROOT, text=True,
            input=r'''
import assert from 'node:assert/strict';
import fs from 'node:fs';
import vm from 'node:vm';
import { REPLICA_CARDS, esc, hasConjugateTile, hasDistinctLemma } from './app/js/card-replica.js';

const source = fs.readFileSync('./app/js/tutorial.js', 'utf8').replace(/import \{[\s\S]*?\} from '[^']+';/, '');
const context = vm.createContext({
  assert, REPLICA_CARDS, esc, hasConjugateTile, hasDistinctLemma,
  window: {}, document: {
    readyState: 'loading', addEventListener() {}, querySelector() { return null; }, getElementById() { return null; }
  },
  localStorage: { getItem() { return null; } }
});

vm.runInContext(source + `
const languages = ['spanish', 'portuguese', 'czech', 'french'];
for (const lang of languages) {
  tutorialLanguageOverride = lang;
  state.mode = 'speech';
  const steps = tutorialSteps();
  for (const step of steps) {
    const notes = stepNotes(step);
    for (const note of notes) {
      const text = tutorialText(note.text);
      const title = tutorialText(note.title);
      assert(!/\{[a-zA-Z0-9_]+\}/.test(text), \`Leftover placeholder in \${lang} note "\${title}": \${text}\`);
      assert(!/\{[a-zA-Z0-9_]+\}/.test(title), \`Leftover placeholder in \${lang} title: \${title}\`);
      assert(text.length <= 180, \`Note "\${title}" in \${lang} exceeds 180 chars (\${text.length}): "\${text}"\`);
    }
  }
}
`, context);
''', capture_output=True,
        )
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_about_modal_walkthrough_hint(self):
        """About project walkthrough button hint accurately reflects both phone and desktop views."""
        auth_js = (ROOT / 'app' / 'js' / 'auth.js').read_text(encoding='utf-8')
        self.assertIn('A quick look at a card · about 30 seconds', auth_js)
        self.assertNotIn('Two screens · about 30 seconds', auth_js)

    def test_css_contracts_for_tutorial_and_about_demos(self):
        """Verify CSS invariants for full-bleed mobile stages and demo grid stability."""
        css = (ROOT / 'app' / 'css' / 'style.css').read_text(encoding='utf-8')
        # Tutorial flow-root prevents margin collapse bug
        self.assertIn('#cardTutorialStage { display: flow-root; }', css)
        # Full-bleed mobile modal
        self.assertIn('#cardTutorialModal.modal { padding: 0 !important; }', css)
        # About demo card 3-column grid override against global meaning-row rule
        self.assertIn('.about-demo-card-inner .meaning-row-regular {', css)
        self.assertIn('grid-template-columns: 22px minmax(0, 1fr) 30px !important;', css)

    def test_walkthrough_mobile_pin_positioning_contracts(self):
        """Walkthrough supports pinTitle and pinAnchor to avoid covering critical card text."""
        wt_js = (ROOT / 'app' / 'js' / 'walkthrough.js').read_text(encoding='utf-8')
        self.assertIn("pinTitle || label.title", wt_js)
        self.assertIn("pinAnchor", wt_js)
        self.assertIn("pinTitle: 'How common'", wt_js)
        self.assertIn("pinAnchor: '.breakdown-trigger'", wt_js)

    def test_replica_and_tutorial_smart_skip_alignment(self):
        """Replica front POS pills, ambient glow, and Tutorial Smart Skip page match live app controls."""
        result = subprocess.run(
            ['node', '--input-type=module', '-'], cwd=ROOT, text=True,
            input=r'''
import assert from 'node:assert/strict';
import fs from 'node:fs';
import vm from 'node:vm';
import { REPLICA_CARDS, esc, hasConjugateTile, hasDistinctLemma, renderFront, replicaCardHTML } from './app/js/card-replica.js';
globalThis.window = {};

const quieroFront = renderFront(REPLICA_CARDS.quieroSpeech);
assert(quieroFront.includes('style="--front-pos-rgb: 0, 212, 170;"'));
assert(quieroFront.includes('<span class="front-lemma-from">from </span>querer'));

const cieloFront = renderFront(REPLICA_CARDS.cielo);
assert(cieloFront.includes('style="--front-pos-rgb: 74, 158, 255;"'));
assert(!cieloFront.includes('front-lemma-from'));

const cardHtml = replicaCardHTML(REPLICA_CARDS.quieroSpeech);
assert(cardHtml.includes('--card-pos-rgb: 0, 212, 170;'));
assert(cardHtml.includes('--card-ambient-glow: radial-gradient('));

const source = fs.readFileSync('./app/js/tutorial.js', 'utf8').replace(/import \{[\s\S]*?\} from '[^']+';/, '');
const context = vm.createContext({
  assert, REPLICA_CARDS, esc, hasConjugateTile, hasDistinctLemma,
  window: {}, document: {
    readyState: 'loading', addEventListener() {}, querySelector() { return null; }, getElementById() { return null; }
  },
  localStorage: { getItem() { return null; } }
});
vm.runInContext(source + `
const skipHtml = TUTORIAL_PAGES.smartSkip.html(tutorialAdapter('spanish'));
// The home screen's row: name, summary and a switch (no Off/On pills).
assert(skipHtml.includes('home-smart-skip'));
assert(skipHtml.includes('home-switch'));
assert(!skipHtml.includes('smart-skip-choice-btn'));
assert(!skipHtml.includes('streamline-rec-badge'));
`, context);
''', capture_output=True,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        auth_js = (ROOT / 'app' / 'js' / 'auth.js').read_text(encoding='utf-8')
        self.assertNotIn('<div class="about-demo-pos-legend">', auth_js)
        self.assertIn("posEl.style.setProperty('--front-pos-rgb'", auth_js)

