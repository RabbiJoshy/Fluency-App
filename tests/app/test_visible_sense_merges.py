"""Study grouping uses displayed source senses without changing headwords/IDs."""
import shutil
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


@unittest.skipUnless(shutil.which("node"), "Node is required")
class VisibleSenseMergeTests(unittest.TestCase):
    def test_study_groups_hydration_progress_and_pooling(self):
        script = r'''
const assert = require('node:assert/strict');
const {createHarness} = require('./tests/app/estimation_harness.cjs');
const h = createHarness();
const sense = (ref, frequency, translation=ref) => ({headword:'haver',pos:'verb',
    source_reference:ref, sense_id:`surface:${ref}`, translation, frequency,
    assignment_method:'assigned'});
const card = (word, meanings) => ({word,id:word,rank:1,meanings});
const a = card('havia',[sense('exist',.8),sense('de',.2)]);
const b = card('haveria',[sense('exist',.79,'there would be'),sense('de',.2),sense('rare-error',.01)]);
const c = card('houve',[sense('exist',.5),sense('occur',.5)]);
assert.equal(h.lemmaGroupKey(a),'haver');
assert.equal(h.lemmaStudyGroupKey(a),h.lemmaStudyGroupKey(b),'one-off rare use should not split a matching back');
assert.notEqual(h.lemmaStudyGroupKey(a),h.lemmaStudyGroupKey(c),'additional visible meaning must split');
assert.equal(h.selectLemmaModeRepresentatives([a,b,c]).length,2);
assert.deepEqual(Array.from(a._lemmaModeCompanions,entry=>entry.surface),['havia','houve'],
    'distinct visible backs of a merged lemma must link to one another');
assert.equal(c._lemmaModeCompanions,a._lemmaModeCompanions);
assert.equal(b._lemmaModeCompanions,undefined,'a non-representative is not another card');
assert.equal(h.buildCardFormModel(a,a.meanings,{mergedLemma:true}).lemmaModeCompanions.length,2);
assert.equal(h.buildCardFormModel(a,a.meanings,{mergedLemma:false}).lemmaModeCompanions,null);
h.selectLemmaModeRepresentatives([a]);
assert.equal(a._lemmaModeCompanions,undefined,'changing filters clears stale companion links');
assert.equal(h.lemmaSeenKey(a),h.lemmaSeenKey(b));
assert.notEqual(h.lemmaSeenKey(a),h.lemmaSeenKey(c),'studying a different back cannot clear this form');
assert.equal(a.id,'havia');
assert.equal(h.buildCardFormModel(a,a.meanings,{mergedLemma:true}).displaySurface,'haver','internal signature must never appear in the title');
// Same full repertoire, different visible backs: preserve both teaching items.
const dominant=card('dom',[sense('exist',.97),sense('de',.03)]);
assert.notEqual(h.lemmaStudyGroupKey(a),h.lemmaStudyGroupKey(dominant));
// Duplicate rows, order, surface-specific IDs and English inflections do not split.
const reordered=card('reordered',[sense('de',.1),sense('exist',.8,'he existed'),sense('de',.1)]);
assert.equal(h.lemmaStudyGroupKey(a),h.lemmaStudyGroupKey(reordered));
// Source eligibility still vetoes identical visible signatures.
const contraction={...a,word:'no',is_contraction:true};
assert.equal(h.lemmaStudyGroupKey(contraction),'');
const frozen=card('há',[sense('exist',1),{pos:'PHRASE',headword:'há quanto tempo',translation:'how long'}]);
assert.equal(h.lemmaStudyGroupKey(frozen),'');
assert.equal(h.lemmaStudyGroupKey(card('empty',[])),'');
const explicitlySeparate={...a,merge_key:''};
assert.equal(h.lemmaStudyGroupKey(explicitlySeparate),'','a stamped exclusion survives loaded meanings');
assert.equal(h.buildCardFormModel(explicitlySeparate,a.meanings,{mergedLemma:true}).displaySurface,'havia');
const noAssigned=card('unused',[{...sense('exist',1),unassigned:true}]);
assert.equal(h.lemmaStudyGroupKey(noAssigned),'');
// Cold keys require release-bound visible evidence, and survive row hydration.
const signature=h.visibleSenseMergeSignature(a);
const cold={id:'cold',word:'havia',meanings:[],_indexRowsPending:true};
h.stampMergeExceptionValues([cold],null,{havia:'haver'});
assert.equal(h.lemmaStudyGroupKey(cold),'','legacy headword-only keys are insufficient');
h.stampMergeExceptionValues([cold],null,{havia:'haver'},null,{havia:signature});
assert.equal(h.lemmaStudyGroupKey(cold),h.lemmaStudyGroupKey(a));
h._cachedJoinedIndex=[cold];
h.mergeIndexRowPayload({cold:{meanings:JSON.parse(JSON.stringify(a.meanings))}});
assert.equal(cold._indexRowsPending,false);
assert.equal(h.lemmaStudyGroupKey(cold),h.lemmaStudyGroupKey(a));
// Pooling examples must match the original dictionary sense, never first gloss.
const host=card('host',[sense('exist',.8,'there be'),sense('de',.2)]);
const sibling=card('sibling',[{...sense('exist',.79,'there would be'),examples:[{target:'Matching example',english:'Matching example'}]},
    {...sense('de',.2),examples:[]},
    {...sense('rare-error',.01),examples:[{target:'Wrong sense example',english:'Wrong sense example'}]}]);
h.poolLemmaSiblingExamples([host],[host,sibling],{});
assert.equal(host.meanings[0].examples.length,1);
assert.equal(host.meanings[0].examples[0].target,'Matching example');
assert.equal(host.meanings[1].examples?.length || 0,0);
// Mutating examples during a set must not change the established study group.
assert.equal(h.lemmaStudyGroupKey(host),h.lemmaStudyGroupKey(sibling));
console.log('visible sense grouping, eligibility, IDs, progress, hydration and pooling verified');
'''
        result = subprocess.run(["node", "-e", script], cwd=ROOT, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr + result.stdout)

    def test_cached_visible_evidence_clears_when_release_changes(self):
        script = r'''
const assert=require('node:assert/strict');
const {createHarness}=require('./tests/app/estimation_harness.cjs');
const payload={release_id:'r1',noun_merge_rule:'noun-merge/v2',keys:{havia:'haver'},
 visible_sense_rule:'visible-senses/v1',visible_sense_keys:{havia:'["ref:exist"]'}};
const h=createHarness({fetch:async()=>({ok:true,json:async()=>payload})});
(async()=>{
 const card={word:'havia',meanings:[]};
 const cfg={mergeExceptionsPath:'same-url',indexPath:'releases/r1/app/index.json'};
 await h.stampContractions([card],cfg);
 assert.notEqual(h.lemmaStudyGroupKey(card),'');
 await h.stampContractions([card],{...cfg,indexPath:'releases/r2/app/index.json'});
 assert.equal(h.lemmaStudyGroupKey(card),'');
 assert.equal(card._visibleSenseMergeOverlay,undefined);
 await h.stampContractions([card],cfg,{detached:true});
 assert.notEqual(h.lemmaStudyGroupKey(card),'');
 await h.stampContractions([card],{...cfg,indexPath:'releases/r2/app/index.json'},{detached:true});
 assert.equal(h.lemmaStudyGroupKey(card),'');
})().catch(e=>{console.error(e);process.exitCode=1});
'''
        result = subprocess.run(["node", "-e", script], cwd=ROOT, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
