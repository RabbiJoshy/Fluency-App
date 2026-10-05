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
const card = REPLICA_CARDS.ptBancoSpeech;
const selected = card.defaultMeaningIndex;
const bank = renderBack(card, selected, 0);
const rowIndices = [...bank.matchAll(/data-meaning-index="(\d+)"/g)].map(m => +m[1]);
assert.deepEqual(rowIndices.map(i => card.meanings[i].translation), ['bank', 'bench']);
assert.equal(rowIndices[0], selected);
assert(bank.includes('Nem sequer sabia'));
assert(bank.includes('The Last Heist (2016)'));
assert(bank.includes('Information about this meaning'));
assert(!bank.includes('replica-dictionary-source'));
assert(!bank.includes('example-source-favicon--wikipedia'));
assert(!bank.includes('meaning-row-check'));
for (const [index, meaning] of card.meanings.entries()) {
  for (let example = 0; example < meaning.examples.length; example++) {
    const html = renderBack(card, index, example);
    assert(!html.includes('Speech example'));
    assert(html.includes('example-source-chip'));
    assert(html.includes(meaning.examples[example].english.replace(/&/g, '&amp;').replace(/"/g, '&quot;')));
  }
}
const benchIndex = rowIndices[1];
assert(renderBack(card, benchIndex, 1).includes('Por que você pintou'));
assert.equal(card.meanings[benchIndex].translation, 'bench');
''', capture_output=True,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
