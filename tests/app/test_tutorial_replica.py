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
for (const key of ['ptDeviaSpeech', 'quieroSpeech']) {
  const card = REPLICA_CARDS[key];
  // A form whose dictionary form differs, with more than one meaning, early
  // in its deck, and glosses short enough for a narrow phone.
  assert.notEqual(card.word, card.lemma);
  assert(card.meanings.length >= 2);
  assert(card.rank <= 350);
  assert(card.meanings.every(m => m.translation.length <= 14));
  const back = renderBack(card, card.defaultMeaningIndex, 0);
  const rowIndices = [...back.matchAll(/data-meaning-index="(\d+)"/g)].map(m => +m[1]);
  assert.equal(rowIndices.length, card.meanings.length);
  // Rows are drawn most common first.
  const shares = rowIndices.map(i => card.meanings[i].pct);
  assert.deepEqual(shares, [...shares].sort((a, b) => b - a));
  for (const [index, meaning] of card.meanings.entries()) {
    assert(meaning.examples.length >= 1);
    for (let example = 0; example < meaning.examples.length; example++) {
      const html = renderBack(card, index, example);
      assert(html.includes('example-source-chip'));
      assert(html.includes(meaning.examples[example].english.replace(/&/g, '&amp;').replace(/"/g, '&quot;')));
    }
  }
}
assert.equal(REPLICA_CARDS.quieroSpeech.lemma, 'querer');
assert.equal(REPLICA_CARDS.ptDeviaSpeech.lemma, 'dever');
assert(renderBack(REPLICA_CARDS.quieroSpeech, 0, 0).includes('Information about this meaning'));
assert(!renderBack(REPLICA_CARDS.quieroSpeech, 0, 0).includes('meaning-row-check'));
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
assert(deck.faces.front.notes.find(note => note.title === 'Song lines').text.includes('your chosen songs'));
assert(deck.faces.back.notes.some(note => note.title === 'The kind of word'));
assert(deck.faces.back.notes.some(note => note.title === 'Which song it is from'));
assert(deck.faces.back.notes.some(note => note.title === 'The line in English'));
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
assert.equal(tutorialStepPosition().total, 19);
const front = stepNotes(tutorialSteps()[0]);
assert.deepEqual(front.map(note => note.title), ['The word', 'Vocabulary rank', 'How often it is said', 'Kind of word', 'The dictionary form']);
const back = stepNotes(tutorialSteps()[1]);
// One note per meaning row (parece has two), then the card's other parts.
// parece's opening meaning has no usage line or grammar, so no "More about a meaning" note.
assert.deepEqual(back.map(note => note.title), ['The kind of word', 'The most common meaning', 'The next meaning', 'How common each meaning is', 'A real example', 'The sentence in English', 'Where it comes from', 'Change the meaning', 'Cycle through the examples', 'Rare uses', 'Flag a meaning', 'Look up', 'Open a dictionary', 'Grade your answer']);
// Notes explain; none sets a task that holds Next back.
for (const step of tutorialSteps()) for (const note of stepNotes(step)) {
  assert.equal(note.practice, undefined);
  assert.equal(note.actionHint, undefined);
}
// Smart Skip and the vocabulary source are pages, each in the language taught.
const skip = stepNotes(tutorialSteps()[2]);
assert.deepEqual(skip.map(note => note.title), ['Turn it on', 'Look-alikes are skipped', 'Word forms share a card', 'Singular and plural share a card']);
assert(tutorialText(skip[2].text).startsWith('“falo”, “falou” and “falar”'));
assert(TUTORIAL_PAGES.smartSkip.html(tutorialAdapter()).includes('falou'));
// Portuguese has no music catalogue, so the artist/playlist note is absent.
assert.equal(stepNotes(tutorialSteps()[3]).length, 3);
assert(TUTORIAL_PAGES.modes.html(tutorialAdapter()).includes('Music'));
state.stepIndex = 2;
assert.deepEqual(tutorialStepPosition(0), {current: 1, total: 4});
state.stepIndex = 0;
tutorialLanguageOverride = 'spanish';
state.mode = 'lyrics';
assert.equal(tutorialStepPosition().total, 20);
const lyricsBack = stepNotes(tutorialSteps()[1]);
assert(lyricsBack.some(note => note.title === 'Play the line'));
// Grading closes the face even after the song details are added.
assert.equal(lyricsBack[lyricsBack.length - 1].title, 'Grade your answer');
assert.equal(stepNotes(tutorialSteps()[0]).length, 5);
`, context);
''', capture_output=True,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
