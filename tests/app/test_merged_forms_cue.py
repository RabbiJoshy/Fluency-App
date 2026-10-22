"""Merged titles and the disclosure use the actual study group's membership."""
import shutil
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


@unittest.skipUnless(shutil.which('node'), 'Node is required')
class MergedFormsCueTests(unittest.TestCase):
    def test_representative_and_membership(self):
        result = subprocess.run(['node', '-e', r'''
const assert = require('node:assert/strict');
const {createHarness} = require('./tests/app/estimation_harness.cjs');
const h = createHarness();
h.loadModule('merged-forms-cue.js');
const row = (word, rank, ref='know') => ({word, id:word, rank, stableRank:rank,
 meanings:[{headword:'saber',pos:'verb',translation:'to know',frequency:1,source_reference:ref}]});
const sabe = row('sabe',106), sabes = row('sabes',115), saber = row('saber',200,'can');
const groups = h.selectLemmaModeRepresentatives([sabes,saber,sabe]);
assert.equal(groups.length,2,'different visible senses remain separate');
assert.equal(groups[1],sabe,'highest-frequency actual member wins');
sabe._dictionaryMergedSurfaces=['saber','sabes','sabe','sabia'];
const model = h.buildCardFormModel(sabe,sabe.meanings,{mergedLemma:true});
assert.equal(model.displaySurface,'sabe','dictionary-wide members cannot supply an absent infinitive');
assert.deepEqual(Array.from(model.mergedGroupSurfaces).sort(),['sabe','sabes']);
assert.equal(sabe.id,'sabe','progress identity is unchanged');
assert.deepEqual(Array.from(h.mergedCardForms(model)).sort(),['sabe','sabes']);
const included = row('saber',300);
const host = h.selectLemmaModeRepresentatives([sabe,sabes,included])[0];
assert.equal(host,included,'infinitive in this exact group still fronts it');
assert.equal(h.buildCardFormModel(host,host.meanings,{mergedLemma:true}).displaySurface,'saber');
const unmerged = h.buildCardFormModel(sabe,sabe.meanings,{mergedLemma:false});
assert.equal(unmerged.displaySurface,'sabe');
assert.equal(h.mergedCardForms(unmerged).length,0);
assert.equal(h.mergedCardForms({...model,isChainChild:true}).length,0);
assert.deepEqual(Array.from(h.mergedCardForms({mergedLemma:true,mergedGroupSurfaces:['é','e\u0301','É','são','são']})),['É','são']);
'''], cwd=ROOT, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
