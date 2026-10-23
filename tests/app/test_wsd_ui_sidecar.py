"""The Jev overlay wins over published buckets without changing source IDs."""
import json
import shutil
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


@unittest.skipUnless(shutil.which('node'), 'Node.js required')
class WsdUiSidecarTests(unittest.TestCase):
    def run_js(self, script):
        source = (ROOT / 'app/js/wsd-ui-sidecar.js').read_text()
        source = '\n'.join(line for line in source.splitlines() if not line.startswith('import '))
        source = source.replace('export ', '')
        result = subprocess.run(['node', '-e', source + '\n' + script], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_precedence_release_isolation_and_restore_template(self):
        self.run_js(r'''
const config = {indexPath:'https://host/pt/speech/release-one/app/vocabulary.index.json',
 wsdSidecarPath:'sidecar.json',wsdSidecarRelease:'release-one'};
const payload = {schema:'wsd-ui-sidecar/v1',release_id:'release-one',cards:{a:{
 meanings:[{translation:'right',frequency:'1',_masterSenseIndex:0}],
 examples:{m:[[{t:'sentence',i:'abc',ju:{status:'assigned'}}]]}}}};
validateWsdUiSidecar(payload,config);
const row={id:'a',word:'target',rank:8,meanings:[{translation:'wrong'}]};
const other={id:'b',meanings:[{translation:'unchanged'}]};
applyWsdUiIndex([row,other],payload);
if(row.id!=='a'||row.rank!==8||row.meanings[0].translation!=='right')throw Error('override');
if(other.meanings[0].translation!=='unchanged')throw Error('outside scope');
row.meanings[0].translation='mutated';
if(row._base_meanings[0].translation!=='right'||payload.cards.a.meanings[0].translation!=='right')throw Error('mutation leak');
if(Object.keys(wsdUiExamplePayload({a:{m:[]},b:{m:[]}},payload)).join()!=='a')throw Error('examples scope');
let reads=0;
async function readJsonWithTimeout(){reads++;return {response:{ok:true},data:payload};}
(async()=>{
 await loadWsdUiSidecar(config);await loadWsdUiSidecar(config);
 if(reads!==1)throw Error('cache');
 const wrong=await loadWsdUiSidecar({...config,indexPath:'releases/other/app/vocabulary.index.json'});
 if(wrong!==null||reads!==1)throw Error('cross release');
 let rejected=false;try{validateWsdUiSidecar(payload,{indexPath:'/other/'})}catch(_){rejected=true}
 if(!rejected)throw Error('release validation');
})().catch(e=>{console.error(e);process.exitCode=1});
''')

    def test_slim_expansion_keeps_jev_provenance_and_license(self):
        source = (ROOT / 'app/js/vocab.js').read_text()
        pure = source[source.index('// slim-example-pure'):source.index('// /slim-example-pure')]
        result = subprocess.run(['node', '-e', pure + r'''
const payload=expandSlimExamplePayload({a:{m:[[{t:'Olá',e:'Hello',s:'tatoeba',i:'123',
 ju:{status:'ambiguous',model:'jev'}}]]}}, {example_format:'slim-example/v1',sources:{tatoeba:{license:'CC BY',attribution:'Tatoeba'}}});
const ex=payload.a.m[0][0];
if(ex.metadata.sentence_id!=='sentence_123'||ex.license!=='CC BY'||ex.metadata.wsd_ui.status!=='ambiguous')throw Error('provenance lost');
'''], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_zero_evidence_rows_move_to_unused_and_indices_do_not_shift(self):
        self.run_js(r'''
const original={sense_id:'old',translation:'wrong',frequency:'0',_masterSenseIndex:0};
const fixed={sense_id:'new',source_sense_id:'en-new',translation:'right',frequency:'0.9',_masterSenseIndex:1};
const unresolved={sense_id:'unresolved',translation:'Meaning unresolved',unassigned:true,frequency:'0.1',_masterSenseIndex:2};
const row={id:'a',unused_menu_senses:[{sense_id:'new',source_reference:'kaikki:en-new'}]};
applyWsdUiIndex([row],{release_id:'x',cards:{a:{meanings:[original,fixed,unresolved],wsd_distribution:{denominator:30}}}});
if(row.meanings.length!==2||row.meanings[0]._masterSenseIndex!==1)throw Error('bucket drift');
if(row.unused_menu_senses.length!==1||row.unused_menu_senses[0].sense_id!=='old')throw Error('unused duplicate');
if(!row.meanings[1].unassigned||row.wsd_distribution.denominator!==30)throw Error('unresolved/distribution');
''')

    def test_config_pins_overlay_and_hydration_reapplies_it(self):
        cfg = json.loads((ROOT / 'app/config/config.json').read_text())['languages']['portuguese']
        self.assertIn('/' + cfg['wsdSidecarRelease'] + '/', cfg['indexPath'])
        source = (ROOT / 'app/js/vocab.js').read_text()
        start = source.index('async function fetchIndexRowShard(')
        finish = source.index('async function ensureIndexRowsForRange(', start)
        hydration = source[start:finish]
        self.assertLess(hydration.index('mergeIndexRowPayload('), hydration.index('applyWsdUiIndex('))
        self.assertIn('wsdUiExamplePayload(responseData, sidecar)', source)

    def test_published_release_short_ids_receive_real_sidecar_buckets(self):
        self.run_js(r'''
const fs=require('node:fs'),path=require('node:path');
const sidecar=JSON.parse(fs.readFileSync('app/data/wsd-sidecars/pt-first200-jev-v1.json','utf8'));
const release=path.join('dist/pt-finite-staging/pt/speech',sidecar.release_id,'app');
const indexFile=path.join(release,'vocabulary.index.json');
const rows=fs.existsSync(indexFile)?JSON.parse(fs.readFileSync(indexFile,'utf8')):
 Object.entries(sidecar.card_ids).map(([id,surface_card_id])=>({id,surface_card_id,word:sidecar.cards[surface_card_id].word}));
validateWsdUiSidecar(sidecar,{indexPath:`releases/pt/speech/${sidecar.release_id}/app/vocabulary.index.json`});
let applied=0,examples=0;
for(const row of rows){
 const patch=wsdUiCard(sidecar,row.id,row.surface_card_id);if(!patch)continue;
 const oldId=row.id,oldSurface=row.surface_card_id;
 applyWsdUiIndex([row],sidecar);
 if(!row.wsd_ui_sidecar||row.id!==oldId||row.surface_card_id!==oldSurface)throw Error('identity/precedence');
 const overlay=wsdUiExamplePayload({[row.id]:{m:[]}},sidecar);
 if(!overlay[row.id]||overlay[row.id].m.length!==patch.meanings.length)throw Error('short example key');
 examples+=overlay[row.id].m.reduce((n,b)=>n+b.length,0);applied++;
}
if(applied!==121||examples!==3558)throw Error(`real coverage ${applied}/${examples}`);
// When local release artifacts exist, exercise the actual async loading seam:
// skinny columns -> fat row hydration -> slim example shards -> Jev override.
if(fs.existsSync(indexFile)){
 const {createHarness}=require('./tests/app/estimation_harness.cjs');
 const h=createHarness();
 h.loadModule('sense-gloss.js');
 const cfg={indexPath:`releases/pt/speech/${sidecar.release_id}/app/vocabulary.index.json`,
 examplesPath:`releases/pt/speech/${sidecar.release_id}/app/vocabulary.examples.json`,
 wsdSidecarPath:'data/wsd-sidecars/pt-first200-jev-v1.json',wsdSidecarRelease:sidecar.release_id};
 h.fetch=async url=>{
  const file=url===cfg.wsdSidecarPath?'app/'+url:url.replace(`releases/pt/speech/${sidecar.release_id}/app`,release);
  if(!fs.existsSync(file))return {ok:false,status:404};
  return {ok:true,status:200,json:async()=>JSON.parse(fs.readFileSync(file,'utf8'))};
 };
 (async()=>{
  await h.fetchAndJoinIndex(cfg);await h.ensureIndexRowsForRange(cfg,1,200);await h.ensureExamplesForRange(cfg,1,200);
  let attached=0;
  for(const row of h._cachedJoinedIndex){
   const patch=wsdUiCard(sidecar,row.id,row.surface_card_id);if(!patch)continue;
   const ex=h._cachedExamplesData[row.id];
   if(!row.wsd_ui_sidecar||!ex)throw Error('real loader failed to overlay');
   for(const meaning of row.meanings){
    const bucket=meaning._masterSenseIndex;
    if(ex.m[bucket].length!==patch.examples.m[bucket].length)throw Error('hydration bucket drift');
   }
   attached+=ex.m.reduce((n,b)=>n+b.length,0);
  }
  if(attached!==3558)throw Error('real loader coverage '+attached);
 })().catch(e=>{console.error(e);process.exitCode=1});
}
''')
