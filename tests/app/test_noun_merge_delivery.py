import os
import shutil
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


class NounMergeDeliveryTests(unittest.TestCase):
    @unittest.skipUnless(shutil.which("node"), "Node is required")
    def test_old_rules_and_cached_other_release_keys_cannot_approve(self):
        script = r"""
const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict');
const source=fs.readFileSync(process.env.VOCAB,'utf8');
const pure=source.slice(source.indexOf('// lemma-merge-pure'),source.indexOf('// /lemma-merge-pure'));
const loading=source.slice(source.indexOf('let _mergeExceptionsFor'),source.indexOf('async function fetchActiveVocabularyIndex'));
let payload={release_id:'release-a',keys:{gatos:'gato'},contractions:[]};
const context={console,fetch:async()=>({ok:true,json:async()=>payload})};
vm.runInNewContext(pure+loading,context);
(async()=>{
 const item={word:'gatos',lemma:'gato',meanings:[]};
 const config={mergeExceptionsPath:'old.json',indexPath:'/release-a/app/index.json'};
 await context.stampContractions([item],config);
 assert.equal(item.merge_key,undefined);
 payload={...payload,noun_merge_rule:'noun-merge/v1',noun_verdicts:{gatos:{rule_version:'noun-merge/v1',allowed:true,lemma:'gato'}}};
 config.mergeExceptionsPath='previous-rule.json';
 await context.stampContractions([item],config);
 assert.equal(item.merge_key,undefined);
 assert.equal(item.noun_merge,undefined);
 payload={...payload,noun_merge_rule:'noun-merge/v2',noun_verdicts:{gatos:{rule_version:'noun-merge/v2',allowed:true,lemma:'gato'}}};
 config.mergeExceptionsPath='current.json';
 await context.stampContractions([item],config);
 assert.equal(context.lemmaSeenKey(item),'gato');
 await context.stampContractions([item],{...config,indexPath:'/release-b/app/index.json'});
 assert.equal(item.merge_key,undefined);
 assert.equal(item.noun_merge,undefined);
 assert.equal(context.lemmaSeenKey(item),'');
})().catch(error=>{console.error(error);process.exitCode=1;});
"""
        result = subprocess.run(["node", "-e", script], capture_output=True, text=True,
                                env={**os.environ, "VOCAB": str(ROOT / "app/js/vocab.js")})
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    @unittest.skipUnless(shutil.which("node"), "Node is required")
    def test_verdict_overlay_is_cleared_and_smart_skip_uses_the_same_decision(self):
        script = r"""
const fs=require('node:fs'), vm=require('node:vm'), assert=require('node:assert/strict');
const source=fs.readFileSync(process.env.VOCAB,'utf8');
const pure=source.slice(source.indexOf('// lemma-merge-pure'),source.indexOf('// /lemma-merge-pure'));
const start=source.indexOf('function stampMergeExceptionValues');
const stamping=source.slice(start,source.indexOf('\n}\n',start)+3);
const context={};vm.runInNewContext(pure+stamping,context);
const proof={rule_version:'noun-merge/v2',lemma:'gato',allowed:true,sense_set:'complete-source-menu'};
const item={word:'gatos',lemma:'gato',meanings:[]};
context.stampMergeExceptionValues([item],null,{gatos:'gato'},{gatos:proof});
assert.equal(context.lemmaGroupKey(item),'gato');
// Noun approval cannot pull another dictionary entry into the same card.
const mixed={word:'seres',noun_merge:{...proof,lemma:'ser'},meanings:[
 {headword:'ser',pos:'noun',translation:'beings'},
 {headword:'ser',pos:'verb',translation:'to be'}]};
assert.equal(context.lemmaSeenKey(mixed),'');
mixed.unused_menu_senses=[mixed.meanings.pop()];
assert.equal(context.lemmaGroupKey(mixed),'');
mixed.meanings=[{pos:'SENSE_CYCLE',allSenses:[...mixed.meanings,...mixed.unused_menu_senses]}];
mixed.unused_menu_senses=[];
mixed.merge_key='ser';
assert.equal(context.lemmaGroupKey(mixed),'');
assert.equal(context.lemmaSeenKey(item),'gato');
item.meanings=[{headword:'gato',pos:'NOUN',translation:'cats'}];
assert.equal(context.lemmaGroupKey(item),'gato');
context.stampMergeExceptionValues([item],null,{gatos:'gato'},{gatos:{...proof,allowed:false}});
assert.equal(context.lemmaGroupKey(item),'');
assert.equal(context.lemmaSeenKey(item),'');
context.stampMergeExceptionValues([item],null,null);
assert.equal(item.noun_merge,undefined);
assert.equal(context.lemmaGroupKey(item),'');
// A source verdict from an index survives removal of a supplemental overlay.
item.noun_merge=proof;
context.stampMergeExceptionValues([item],null,null,{gatos:{...proof,allowed:false}});
context.stampMergeExceptionValues([item],null,null);
assert.equal(item.noun_merge,proof);
assert.equal(context.lemmaGroupKey(item),'gato');
"""
        result = subprocess.run(["node", "-e", script], capture_output=True, text=True,
                                env={**os.environ, "VOCAB": str(ROOT / "app/js/vocab.js")})
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)


if __name__ == "__main__":
    unittest.main()
