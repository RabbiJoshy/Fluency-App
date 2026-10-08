"""Selection and source regressions in the Portuguese learner tutorial."""
from pathlib import Path
import shutil
import subprocess
import unittest

ROOT = Path(__file__).resolve().parents[2]


@unittest.skipUnless(shutil.which('node'), 'Node.js required')
class TutorialReplicaTests(unittest.TestCase):
    def test_commonness_order_keeps_selection_and_example_indices(self):
        result = subprocess.run(
            ['node', '--input-type=module', '-'], cwd=ROOT, text=True,
            input=r'''
import assert from 'node:assert/strict';
import { REPLICA_CARDS, renderBack } from './app/js/card-replica.js';
globalThis.window = {};
const card = REPLICA_CARDS.ptProvarSpeech;
const selected = card.defaultMeaningIndex;
const back = renderBack(card, selected, 0);
const rowIndices = [...back.matchAll(/data-meaning-index="(\d+)"/g)].map(m => +m[1]);
assert.deepEqual(rowIndices.map(i => card.meanings[i].translation), ['to prove', 'to taste; to try', 'to try on']);
assert.equal(rowIndices[0], selected);
const shuffled = {...card, meanings: [card.meanings[1], card.meanings[0], card.meanings[2]]};
assert.deepEqual([...renderBack(shuffled, 1, 0).matchAll(/data-meaning-index="(\d+)"/g)].map(m => +m[1]), [1, 0, 2]);
assert(back.includes('Tens de me ajudar'));
assert(back.includes('Power · S3 E7'));
assert.equal(card.meanings.reduce((n, m) => n + m.examples.length, 0), 14);
assert(card.meanings[0].pct > 75);
assert(card.meanings.slice(1).every(m => m.examples.length >= 2));
assert(back.includes('Information about this meaning'));
assert(!back.includes('replica-dictionary-source'));
assert(!back.includes('example-source-favicon--wikipedia'));
assert(!back.includes('meaning-row-check'));
assert(!back.includes('>tr.</span>'));
assert(back.includes('meaning-row-sub sense-cue-area'));
assert(!back.includes('· show that something is true'));
for (const [index, meaning] of card.meanings.entries()) {
  for (let example = 0; example < meaning.examples.length; example++) {
    const html = renderBack(card, index, example);
    assert(!html.includes('Speech example'));
    assert(html.includes('example-source-chip'));
    assert(html.includes(meaning.examples[example].english.replace(/&/g, '&amp;').replace(/"/g, '&quot;')));
  }
}
const tasteIndex = rowIndices[1];
assert(renderBack(card, tasteIndex, 0).includes('How about trying some sushi?'));
assert.equal(card.meanings[tasteIndex].translation, 'to taste; to try');
const clothesIndex = rowIndices[2];
assert(renderBack(card, clothesIndex, 0).includes('this dress'));
assert(renderBack(card, selected, 8).includes('Tens de me ajudar'));
''', capture_output=True,
        )
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_tutorial_uses_one_selected_mode_and_waits_for_source_choice(self):
        result = subprocess.run(
            ['node', '--input-type=module', '-'], cwd=ROOT, text=True,
            input=r'''
import assert from 'node:assert/strict';
import fs from 'node:fs';
import vm from 'node:vm';
let speechChosen = false;
const window = {};
const document = {
  readyState: 'loading', addEventListener() {}, querySelector() { return null; },
  getElementById(id) { return id === 'step1' ? {classList: {contains: () => speechChosen}} : null; },
};
const source = fs.readFileSync('./app/js/tutorial.js', 'utf8').replace(/import \{[\s\S]*?\} from '[^']+';/, '');
const context = vm.createContext({window, document, localStorage: {getItem() {return null;}}, assert});
vm.runInContext(source + `
assert.equal(selectedTutorialMode(), null);
assert.equal(openFirstRunCardTutorial(), false);
state.mode = 'speech';
assert.equal(tutorialSteps().length, 2);
assert(tutorialSteps().every(step => step.deck === 'speech'));
`, context);
speechChosen = true;
assert.equal(window.getCardTutorialMode(), 'speech');
window.activeArtist = {language: 'spanish'};
assert.equal(window.getCardTutorialMode(), 'lyrics');
vm.runInContext(`
state.mode = 'lyrics';
assert.equal(tutorialSteps().length, 2);
assert(tutorialSteps().every(step => step.deck === 'lyrics'));
const deck = deckById('lyrics');
assert.equal(deck.card, 'cielo');
assert(deck.faces.front.notes.some(note => note.title === 'Kind of word'));
assert(deck.faces.front.notes.some(note => note.title === 'Song line count'));
assert(deck.faces.back.notes.some(note => note.title === 'The meanings at a glance'));
assert(deck.faces.back.notes.some(note => note.title === 'Which song it is from'));
assert(deck.faces.back.notes.some(note => note.title === 'Play the line'));
assert(!deck.faces.back.notes.some(note => note.title === 'Where the example is from'));
`, context);
''', capture_output=True,
        )
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_full_tutorial_includes_metadata_and_practice(self):
        result = subprocess.run(
            ['node', '--input-type=module', '-'], cwd=ROOT, text=True,
            input=r'''import assert from 'node:assert/strict';
import fs from 'node:fs';
import vm from 'node:vm';
import { REPLICA_CARDS } from './app/js/card-replica.js';
const source = fs.readFileSync('./app/js/tutorial.js', 'utf8').replace(/import \{[\s\S]*?\} from '[^']+';/, '');
const context = vm.createContext({assert, REPLICA_CARDS,
  window: {}, document: {readyState: 'loading', addEventListener() {}, querySelector() {return null;}, getElementById() {return null;}},
  localStorage: {getItem() {return null;}}});
vm.runInContext(source + `
tutorialLanguageOverride = 'portuguese';
state.mode = 'speech';
window.innerHeight = 900;
window.matchMedia = () => ({matches: false});
assert.equal(tutorialCardHeight(), 740);
state.meaningIndex = 2;
state.exampleIndex = 1;
assert.equal(tutorialCardHeight(), 740);
window.innerHeight = 680;
assert.equal(tutorialCardHeight(), 520);
// The actual tutorial area can be shorter than the window (text zoom,
// browser chrome, or a wrapped header). Its measured budget wins.
window.innerWidth = 1440;
const pane = {clientHeight: 590};
const column = {};
document.querySelector = selector => selector.includes('stage-col') ? column : pane;
document.getElementById = () => ({offsetHeight: 46});
this.getComputedStyle = element => element === pane
    ? {paddingTop: '0', paddingBottom: '0'} : {gap: '14'};
assert.equal(tutorialCardHeight(), 522);
state.meaningIndex = 1;
assert.equal(tutorialCardHeight(), 522);
pane.clientHeight = 410;
state.cardHeight = null;
assert.equal(tutorialCardHeight(), 342);
window.innerWidth = 913;
state.cardHeight = null;
window.matchMedia = () => ({matches: true});
assert.equal(tutorialCardHeight(), 402);
window.innerWidth = 375;
state.cardHeight = null;
document.querySelector = () => null;
document.getElementById = () => null;
window.matchMedia = () => ({matches: true});
assert.equal(tutorialCardHeight(), 440);
document.querySelector = () => ({clientHeight: 360});
assert.equal(tutorialCardHeight(), 342);
state.meaningIndex = 0;
assert.equal(tutorialCardHeight(), 342);
document.querySelector = () => null;
assert.equal(tutorialStepPosition().total, 15);
const front = stepNotes(tutorialSteps()[0]);
for (const title of ['How common the word is', 'Kind of word', 'The dictionary form', 'How often it is said']) assert(front.some(note => note.title === title));
const back = stepNotes(tutorialSteps()[1]);
for (const title of ['Useful extras', 'How common this meaning is', 'Where the example is from', 'Smart Skip saves time', 'Switch modes anytime', 'You’re ready to study']) assert(back.some(note => note.title === title));
state.stepIndex = 1;
state.activeNote = back.findIndex(note => note.practice === 'meaning');
assert.equal(practicePending(), true);
renderNotes = () => {};
markAnchors = () => {};
completePractice('example');
assert.equal(practicePending(), true);
completePractice('meaning');
assert.equal(practicePending(), false);
state.activeNote = back.findIndex(note => note.practice === 'example');
assert.equal(practicePending(), true);
completePractice('example');
assert.equal(practicePending(), false);
tutorialLanguageOverride = 'spanish';
state.mode = 'lyrics';
assert(tutorialStepPosition().total > 15);
assert(stepNotes(tutorialSteps()[1]).some(note => note.title === 'Play the line'));
assert.equal(stepNotes(tutorialSteps()[0]).length, 5);
`, context);
''', capture_output=True,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
