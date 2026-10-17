"""Production renderer uses typed colours and source provenance on initial and cycled cards."""
import pathlib
import shutil
import subprocess
import unittest

ROOT=pathlib.Path(__file__).resolve().parents[2]

class FunctionWordPresentationTests(unittest.TestCase):
    @unittest.skipUnless(shutil.which('node'),'Node required')
    def test_render_and_cycle(self):
        script=r'''
const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict');
const ctx={window:{},document:{querySelector:()=>null}};vm.createContext(ctx);
vm.runInContext(fs.readFileSync('app/js/function-word-card.js','utf8').replace(/^export /gm,''),ctx);
vm.runInContext(`
configureFunctionWordPresentation({posRgb:p=>p==='verb'?'0, 212, 170':'74, 158, 255',provenanceHTML:e=>'<b>'+e.metadata.source.name+'</b>'});
`,ctx);
const html=vm.runInContext("functionWordBlockHTML({word:'naquele'},'pt')",ctx);
assert.ok(html.indexOf('fw-heading')<html.indexOf('fw-parts-box'));
assert.ok(html.indexOf('fw-parts-box')<html.indexOf('fw-section-header'));
assert.ok(html.includes('rgb(74, 158, 255)'));
assert.ok(html.includes('<b>tatoeba</b>'));
const que=vm.runInContext("functionWordBlockHTML({word:'que'},'pt')",ctx);
assert.ok(que.includes('color:rgb(0, 212, 170)">think / say / know / hope'));
const nodes={'.fw-sentence-target':{},'.fw-sentence-translation':{},'.fw-credit-start':{},'.fw-sentence-ticks-container':{}};
ctx.document.querySelector=()=>({dataset:{word:'que',lang:'pt'},querySelectorAll:()=>[],querySelector:s=>nodes[s]});
vm.runInContext('_activeExampleIndex=2;refreshFunctionWordCardBack()',ctx);
assert.ok(nodes['.fw-credit-start'].innerHTML.includes('opensubtitles'));
assert.ok(nodes['.fw-sentence-target'].innerHTML.includes('rgb(0, 212, 170)'));
assert.equal(vm.runInContext("fwCreditHTML({source:'Conversation'})",ctx),'Source not verified');
assert.equal(vm.runInContext("functionWordBlockHTML({word:'qué',functionWord:{roles:[{value:'interrogative',gloss:'what'}],patterns:[]}},'es')",ctx),'');
assert.ok(vm.runInContext("functionWordBlockHTML({word:'que'},'es')",ctx).includes('fw-deterministic-card'));

'''
        run=subprocess.run(['node','-e',script],cwd=ROOT,text=True,capture_output=True)
        self.assertEqual(run.returncode,0,run.stderr)

    def test_uncovered_words_keep_standard_rows(self):
        source=(ROOT/'app/js/flashcards.js').read_text()
        self.assertIn('backHTML += functionWordRows || `<div class="meanings-scroll">',source)
        self.assertNotIn('functionWordExampleHTML(currentExample)',source)
        self.assertNotIn('Grammar word',(ROOT/'app/js/function-word-card.js').read_text())

    @unittest.skipUnless(shutil.which('node'),'Node required')
    def test_staging_trial_is_opt_in_and_does_not_mutate_base(self):
        script=r'''
const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict');
const ctx={window:{location:{search:'?fwSyntaxTrial=1'}},URLSearchParams,document:{querySelector:()=>null}};vm.createContext(ctx);
vm.runInContext(fs.readFileSync('app/js/function-word-card.js','utf8').replace(/^export /gm,''),ctx);
const get=()=>vm.runInContext("getGrammarWordDefinition('se','spanish')",ctx);
const base=get(),count=base.relations[0].examples.length;
assert.equal(base.syntaxTrial,undefined); // Production ignores opt-in.
ctx.window.__FLUENCY_ENV__='staging';ctx.window.location.search='';
assert.equal(get(),base); // Staging default stays unchanged.
ctx.window.location.search='?fwSyntaxTrial=1';
const trial=get();assert.equal(trial.syntaxTrial,true);
assert.ok(trial.relations[0].examples.length>count);
assert.equal(base.relations[0].examples.length,count);
assert.equal(trial.uses,trial.relations);
assert.ok(vm.runInContext("functionWordBlockHTML({word:'se'},'es')",ctx).includes('Reviewed example trial'));
const nodes={'.fw-sentence-target':{},'.fw-sentence-translation':{},'.fw-credit-start':{},'.fw-sentence-ticks-container':{}};
ctx.document.querySelector=()=>({dataset:{word:'se',lang:'es'},querySelectorAll:()=>[],querySelector:s=>nodes[s]});
vm.runInContext('_activeExampleIndex=1;refreshFunctionWordCardBack()',ctx);
assert.ok(nodes['.fw-sentence-target'].innerHTML.includes('ha acabado'));
ctx.window.location.search='?fwSyntaxTrial=0';assert.equal(get(),base);
ctx.window.__FLUENCY_ENV__='production';ctx.window.location.search='?fwSyntaxTrial=1';assert.equal(get(),base);
'''
        run=subprocess.run(['node','-e',script],cwd=ROOT,text=True,capture_output=True)
        self.assertEqual(run.returncode,0,run.stderr)
