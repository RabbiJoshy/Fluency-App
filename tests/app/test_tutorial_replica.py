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
const cardSteps = () => tutorialSteps().filter(step => step.kind === 'card');
assert.equal(cardSteps().length, 2);
assert(cardSteps().every(step => step.deck === 'speech'));
assert.deepEqual(tutorialSteps().map(step => step.chapter), ['card', 'card', 'smartSkip', 'modes']);
`, context);
speechChosen = true;
assert.equal(window.getCardTutorialMode(), 'speech');
window.activeArtist = {language: 'spanish'};
assert.equal(window.getCardTutorialMode(), 'lyrics');
vm.runInContext(`
state.mode = 'lyrics';
assert.equal(cardSteps().length, 2);
assert(cardSteps().every(step => step.deck === 'lyrics'));
const deck = deckById('lyrics');
assert.equal(deck.card, 'cielo');
assert(deck.faces.front.notes.some(note => note.title === 'Kind of word'));
assert(deck.faces.front.notes.find(note => note.title === 'How common the word is').text.includes('your chosen songs'));
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
import { REPLICA_CARDS, esc } from './app/js/card-replica.js';
const source = fs.readFileSync('./app/js/tutorial.js', 'utf8').replace(/import \{[\s\S]*?\} from '[^']+';/, '');
const context = vm.createContext({assert, REPLICA_CARDS, esc,
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
// Progress counts the chapter on show: the card's two faces.
assert.equal(tutorialStepPosition().total, 9);
const front = stepNotes(tutorialSteps()[0]);
assert.deepEqual(front.map(note => note.title), ['The word', 'How common the word is', 'Kind of word', 'The dictionary form']);
const back = stepNotes(tutorialSteps()[1]);
assert.deepEqual(back.map(note => note.title), ['The meanings at a glance', 'The selected meaning', 'How common this meaning is', 'A real example', 'Grade your answer']);
// Notes explain; none sets a task that holds Next back.
for (const step of tutorialSteps()) for (const note of stepNotes(step)) {
  assert.equal(note.practice, undefined);
  assert.equal(note.actionHint, undefined);
}
// Smart Skip and the vocabulary source are pages, each in the language taught.
const skip = stepNotes(tutorialSteps()[2]);
assert.deepEqual(skip.map(note => note.title), ['Turn it on', 'Word forms share a card', 'Look-alikes are skipped']);
assert(tutorialText(skip[1].text).startsWith('“falo”, “falou” and “falar”'));
assert(TUTORIAL_PAGES.smartSkip.html(tutorialAdapter()).includes('falou'));
assert.equal(stepNotes(tutorialSteps()[3]).length, 2);
assert(TUTORIAL_PAGES.modes.html(tutorialAdapter()).includes('Your music'));
state.stepIndex = 2;
assert.deepEqual(tutorialStepPosition(0), {current: 1, total: 3});
state.stepIndex = 0;
tutorialLanguageOverride = 'spanish';
state.mode = 'lyrics';
assert.equal(tutorialStepPosition().total, 12);
const lyricsBack = stepNotes(tutorialSteps()[1]);
assert(lyricsBack.some(note => note.title === 'Play the line'));
// Grading closes the face even after the song details are added.
assert.equal(lyricsBack[lyricsBack.length - 1].title, 'Grade your answer');
assert.equal(stepNotes(tutorialSteps()[0]).length, 4);
`, context);
''', capture_output=True,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
