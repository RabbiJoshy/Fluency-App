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
assert.ok(que.includes('color:rgb(0, 212, 170)">think, say, know or hope'));
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
