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
