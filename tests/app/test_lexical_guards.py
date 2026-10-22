"""Whole-name entity matching and shared standalone-word corrections."""
from pathlib import Path
import shutil
import subprocess
import unittest

ROOT = Path(__file__).resolve().parents[2]


@unittest.skipUnless(shutil.which('node'), 'Node.js required')
class LexicalGuardTests(unittest.TestCase):
    def test_turbo_and_offline_reject_phrase_contamination(self):
        helper = (ROOT / 'app/js/lexical-guards.js').read_text().replace('export ', '')
        engine = (ROOT / 'app/turbo/turbo-engine.js').read_text()
        engine = '\n'.join(line for line in engine.splitlines() if not line.startswith('import ')).replace('export ', '').replace('import.meta.url', repr('https://app.test/turbo/turbo-engine.js'))
        script = "const assert=require('node:assert/strict');\n" + helper + '\n' + engine + r"""
assert.equal(entityTitleMatchesQuery('Berlín','Muro de Berlín'),false);
assert.equal(entityTitleMatchesQuery('Berlin','Berlín (personaje)'),true);
assert.equal(entityTitleMatchesQuery('Prada','Beanie Prada'),false);
assert.equal(entityTitleMatchesQuery('Puerto Rico','Puerto Rico'),true);
const original=[{pos:'PHRASE',translation:'Berlin Wall',headword:'muro de berlín'}];
assert.equal(standaloneWordMeanings('berlín',original)[0].translation,'Berlin');
assert.equal(standaloneWordMeanings('muro de berlín',original),original);
assert.equal(original[0].translation,'Berlin Wall');
const turbo=new TurboEngine({dictionary:{'berlín':{meanings:original,top_translation:'Berlin Wall'}}});
assert.equal(turbo.resolveWordInfo('berlín').translation,'Berlin');
const urls=[];
globalThis.fetch=async url=>{
 urls.push(url);
 let data={};
 if(url.includes('list=search')) data={query:{search:[{title:'Muro de Berlín'},{title:'Berlín'}]}};
 else if(url.includes('/summary/')) data={title:'Berlín',description:'capital de Alemania',extract:'Berlín es una ciudad.'};
 else if(url.includes('prop=langlinks')) data={query:{pages:{1:{title:'Berlín',langlinks:[{'*':'Berlin'}]}}}};
 else if(url.includes('prop=description')) data={query:{pages:{1:{title:'Berlin',description:'capital of Germany'}}}};
 return {ok:true,json:async()=>data};
};
(async()=>{
 const resolved=await turbo.resolveEntitiesBatch(['Berlín']);
 assert.equal(resolved.get('berlín').canonicalTitle,'Berlín');
 assert.equal(urls.some(u=>u.includes('/summary/Muro')),false);
})().catch(e=>{console.error(e);process.exitCode=1});
"""
        result = subprocess.run(['node','-'], input=script, cwd=ROOT, text=True, capture_output=True)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
