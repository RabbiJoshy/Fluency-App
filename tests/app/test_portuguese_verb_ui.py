"""Construction and redirect regressions from Portuguese pre-ship review."""
import shutil
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


@unittest.skipUnless(shutil.which('node'), 'Node.js required')
class PortugueseVerbUITests(unittest.TestCase):
    def test_source_frames_remain_optional_and_share_the_companion_renderer(self):
        script = r'''
import assert from 'node:assert/strict';
import fs from 'node:fs';
import * as ui from './app/js/card-metadata-pills.js';
const rows=JSON.parse(fs.readFileSync('./tests/app/fixtures/portuguese_verb_ui.json'));
const original=JSON.stringify(rows);
for(const word of ['tratar','procurar','começar','ir']) {
 const row=rows.find(r=>r.word===word);
 for(const meaning of row.meanings) {
  const frame=ui.senseMetadataItems(meaning).find(item=>item.kind==='companion_form' && ui.frameCue(item.value));
  const companion=ui.extractSenseCompanion(meaning);
  if(!frame && !companion) continue;
  const html=ui.senseCollocationHTML(meaning,row);
  assert.match(html,/sense-target-collocation/);
  assert.match(html,new RegExp(`Used with: ${word}`));
  const remaining=ui.compactLearnerSenseMetadata(ui.senseMetadataItems(meaning),meaning,{excludeCompanion:true});
  assert(!remaining.some(item=>item.family==='companion'||item.kind==='companion_form'));
  if(frame?.value.includes('direct object')) assert.match(companion.frame,/\((de|por)\)/,'optional preposition must remain optional');
 }
}
const manner=rows.find(r=>r.word==='tratar').meanings.find(m=>m.translation.includes('specific way'));
assert.equal(ui.extractSenseCompanion(manner).frame,'+ (de) + adverb (bem / mal)');
const existential=rows.find(r=>r.word==='tem').meanings.find(m=>m.translation.startsWith('there be'));
assert.match(ui.projectWiktionaryGloss(existential,existential.translation).display,/^to exist/);
for(const [word,slot] of [['saber','infinitive'],['estamos','adjective']]) {
 const card=rows.find(r=>r.word===word);
 const sense=card.meanings.find(m=>ui.extractSenseCompanion(m)?.frame===`+ ${slot}`);
 assert(sense,`${word}: grammar slot is extracted`);
 const html=ui.senseCollocationHTML(sense,card);
 assert.match(html,new RegExp(`data-frame-phrase="${word} \\+ ${slot}"`));
 assert.match(ui.senseCollocationHTML(sense,{...card,mergedLemma:true}),new RegExp(`data-frame-phrase="${sense.headword} \\+ ${slot}"`));
 const metadata=ui.senseMetadataHTML(sense,true,{excludeCompanion:true,ignoreBudget:true,gloss:sense.translation,cardMeanings:card.meanings});
 assert(!metadata.includes(`+ ${slot}`),'the slot already in the phrase pill is not repeated');
}
const literal=rows.find(r=>r.word==='querer').meanings.find(m=>ui.extractSenseCompanion(m)?.terms.includes('que'));
assert.match(ui.senseCollocationHTML(literal,{word:'querer'}),/data-frame-phrase="querer que"/);
assert.equal(JSON.stringify(rows),original,'rendering never rewrites source senses');
'''
        result = subprocess.run(['node', '--input-type=module', '-'], input=script,
                                cwd=ROOT, text=True, capture_output=True)
        self.assertEqual(result.returncode, 0, result.stderr)
