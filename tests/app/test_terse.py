"""Source-preserving presentation regressions for TERSE-2."""
from pathlib import Path
import shutil
import subprocess
import unittest

ROOT = Path(__file__).resolve().parents[2]


@unittest.skipUnless(shutil.which('node'), 'Node.js required')
class TerseTests(unittest.TestCase):
    def test_dictionary_trimming_preserves_complete_meanings_and_originals(self):
        result = subprocess.run(['node', '--input-type=module', '-'], cwd=ROOT, text=True,
            capture_output=True, input=r'''
import assert from 'node:assert/strict';
import fs from 'node:fs';
import * as ui from './app/js/card-metadata-pills.js';
const view = (meaning, peers = [meaning], active = true, gloss) => ui.learnerSensePresentation(meaning, active, {
 ignoreBudget: true, allowInactivePrimary: true, cardMeanings: peers, gloss,
 peerMeanings: peers.filter(peer => peer !== meaning),
});
const examples = [
 ['galaxy (set of many stars, with a spiral shape, which constitutes an astral system)', 'galaxy'],
 ['certificate (copy extracted from a document, issued by the service, which proves the acts)', 'certificate'],
 ['plant (an organism of Plantae (land plants), including green algae)', 'plant'],
 ['pre-reform spelling (used until 1943 in Brazil and 1990 in Portugal) of eletricidade; still used where the agreement hasn’t come into effect', 'pre-reform spelling of eletricidade'],
 ['to end one’s connection, affiliation or relationship with', 'to end one’s connection, affiliation or relationship with'],
 ['to speak (with someone)', 'to speak (with someone)'],
 ['to go (only when the speaker has permission to leave)', 'to go (only when the speaker has permission to leave)'],
 ['no; not; never', 'no; not; never'],
 ['to decline, rather than to accept', 'to decline, rather than to accept'],
 ['alternative form of foo; bar', 'alternative form of foo; bar'],
 ["Used for explanations: it's just that, because; it's not that", "it's just that, because; it's not that"],
 ['the past form of que seja: modifies a quantity to express sufficiency: even; only', 'even; only'],
];
for (const [translation, expected] of examples) {
 const meaning = { translation, context: '', pos: 'noun' };
 const source = JSON.stringify(meaning);
 const p = view(meaning);
 assert.equal(p.gloss, expected, translation);
 assert.equal(JSON.stringify(meaning), source);
 assert.deepEqual(view(meaning), p);
 assert.equal(view(meaning, [meaning], false).gloss, p.gloss);
 if (expected !== translation) {
  assert.equal(p.transformation.policy, 'learner-card-trimming/v1');
  assert.equal(p.note.original.originalGloss, translation);
  assert(!ui.senseNoteHTML(p).includes('Original dictionary text'));
  assert(ui.senseNoteHTML(p).includes('sense-note-trigger'));
 }
}
const siblings = [
 { translation: 'bank (a financial institution serving local people and businesses)', pos: 'noun' },
 { translation: 'bank (the sloping land bordering a body of water in the countryside)', pos: 'noun' },
];
const pair = siblings.map(m => view(m, siblings));
assert.notEqual(pair[0].gloss + pair[0].key.text, pair[1].gloss + pair[1].key.text);
const nao = {translation: "not; don't; haven't (negates the meaning of the verb or adverb)",
 context: "isn't (used to ask whether a person agrees with the proposition, rather than to ask for an unknown fact)", pos:'adv'};
const p = view(nao);
assert.equal(p.gloss, "not; don't; haven't");
assert.equal(p.note.original.originalContext, nao.context);
assert(!ui.senseNoteHTML(p).includes(ui.escapeCardText(nao.context)));
assert(ui.senseNoteHTML(p).includes('Negates the meaning of the verb or adverb'));
assert(!ui.senseNoteHTML(p).includes('Original dictionary text'));
// An already projected/inflected input must still expose original dictionary text.
assert.equal(view(nao, [nao], true, p.gloss).note.original.originalGloss, nao.translation);
// Unbalanced source text is retained, rather than completed by invention.
const malformed = {translation: 'Puerto Rico (an island in the Caribbean', pos: 'noun'};
assert.equal(view(malformed).gloss, malformed.translation);
// The full longest-case corpus also stays immutable and recoverable.
const audit = JSON.parse(fs.readFileSync('research/terse/audit.json'));
for (const deck of Object.values(audit.releases)) for (const row of [...deck.longestGlosses, ...deck.longestContexts]) {
 const meaning = {translation:row.gloss, context:row.context, pos:'noun'};
 const original = JSON.stringify(meaning);
 const p = view(meaning);
 assert.equal(JSON.stringify(meaning), original);
 if(p.transformation) {
  assert.equal(p.note.original.originalGloss, row.gloss);
  assert.equal(p.note.original.originalContext, row.context);
 }
}
''')
        self.assertEqual(result.returncode, 0, result.stderr)
