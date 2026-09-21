"""Learner-visible regressions from shipped Portuguese, Czech and Spanish cards."""
from pathlib import Path
import shutil
import subprocess
import unittest

ROOT = Path(__file__).resolve().parents[2]

@unittest.skipUnless(shutil.which('node'), 'Node.js required')
class SenseMetadataBehaviorTests(unittest.TestCase):
    def test_shipped_meaning_distinctions_and_provider_parity(self):
        result = subprocess.run(['node', '--input-type=module', '-'], cwd=ROOT, text=True,
            input=r'''
import assert from 'node:assert/strict';
import fs from 'node:fs';
import * as ui from './app/js/card-metadata-pills.js';
const fixture = JSON.parse(fs.readFileSync('tests/app/fixtures/sense_metadata.json'));
const card = (lang, word) => fixture[lang].find(c => c.word === word);
const project = (c, m) => {
 const gloss = ui.projectWiktionaryGloss(m, m.translation).display;
 const options = {gloss, peerMeanings: ui.senseMetadataPeers(m, c.meanings, gloss), allowInactivePrimary: true, senseCount: c.meanings.length};
 const items = ui.compactLearnerSenseMetadata(ui.senseMetadataItems(m), m, options);
 return {gloss, context: ui.contextWithoutSenseMetadata(m, false, options),
  labels: items.map(i => ui.senseMetadataDisplay(i, options).short),
  html: ui.senseMetadataHTML(m, false, options), options};
};
for(const word of ['um','uma']) {
 const c=card('pt',word), m=c.meanings.find(m=>m.context==='a bit of');
 assert.equal(project(c,m).context,'a bit of');
}
for(const word of ['se','si']) {
 const c=card('cs',word);
 for(const m of c.meanings.filter(m=>m.translation==='oneself')) {
  assert.equal(project(c,m).context,m.context);
  assert.deepEqual(project(c,m).labels,[]);
 }
}
const en=card('es','en');
for(const [context,label] of [['indicating place','place'],['indicating time','time'],['indicating mode','manner']]) {
 const m=en.meanings.find(m=>m.translation==='in' && m.context===context),p=project(en,m);
 assert(p.labels.includes(label));assert(p.html.includes(label));assert.equal(p.context,'');
}
const gosto=card('pt','gosto');assert.deepEqual(project(gosto,gosto.meanings[0]).labels,['with de']);
assert.equal(project(gosto,gosto.meanings[0]).context,'');
const s=card('cs','s'),sp=project(s,s.meanings[0]);
assert(sp.labels.includes('takes instrumental case'));assert(!sp.html.includes('sense-pill--companion'));
const cekat=card('cs','čekat'),wait=cekat.meanings.find(m=>m.translation==='to wait');
assert(project(cekat,wait).labels.includes('with na'));
const su=card('es','su'),your=su.meanings.find(m=>m.translation==='your');
assert(project(su,your).labels.includes('addressing several people'));
assert.equal(project(su,your).context,'');
const ven=card('es','ven'),command=ven.meanings.find(m=>m.context?.includes('imperative'));
assert.deepEqual(project(ven,command).labels,['command']);assert.equal(project(ven,command).context,'');
const article=card('pt','a'),the=article.meanings.find(m=>m.pos==='article');
assert.equal(project(article,the).gloss,'the');assert(project(article,the).context.includes('already been mentioned'));
const v=card('cs','v'),space=v.meanings.find(m=>m.translation.includes('enclosed space'));
assert(project(v,space).gloss.includes('enclosed space'));
const para=card('pt','para'),purpose=para.meanings.find(m=>m.translation.includes('in order to'));
assert.deepEqual(project(para,purpose).labels,[]);
// Shared restrictions must not disappear, even when several other cues exist.
const restricted={translation:'to speak',pos:'verb',metadata:{sense_metadata:{contract_version:'sense-metadata/v1',features:[
 {family:'register',kind:'region',value:'Brazil'}, {family:'register',kind:'usage_tag',value:'vulgar'},
 {family:'companion',kind:'required_word',value:'de'}, {family:'domain',kind:'topic',value:'music'}
]}}};
const restrictions=ui.compactLearnerSenseMetadata(ui.senseMetadataItems(restricted),restricted,{peerMeanings:[structuredClone(restricted)]});
assert(restrictions.some(i=>i.value==='Brazil'));assert(restrictions.some(i=>i.value==='vulgar'));
// Provider prose is escaped; long notes remain visible without character truncation.
const long={translation:'test',context:'A genuinely distinguishing explanation '.repeat(8)+'<script>',metadata:{sense_metadata:{contract_version:'sense-metadata/v1',features:[]}}};
assert.equal(ui.contextWithoutSenseMetadata(long,false),long.context);
assert(ui.escapeCardText(long.context).includes('&lt;script&gt;'));
// Low-level aspect stays accessible on selection, not in every navigation row.
const asp=ui.senseMetadataHTML(wait,true,{...project(cekat,wait).options,peerMeanings:[]});
assert(asp.includes('imperfective'));assert(asp.includes(' hidden'));
console.log('20 shipped cards: meaning preservation, restrictions, grammar, cases and provider parity passed');
''', capture_output=True)
        self.assertEqual(result.returncode, 0, result.stderr)
