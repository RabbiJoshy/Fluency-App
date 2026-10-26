"""Regressions for grammar-word follow-ups, row fitting and example ordering."""
from pathlib import Path
import shutil
import subprocess
import unittest

ROOT = Path(__file__).resolve().parents[2]


@unittest.skipUnless(shutil.which('node'), 'Node required')
class MobileCardRegressionTests(unittest.TestCase):
    def run_js(self, script):
        result = subprocess.run(['node', '--input-type=module', '-'], input=script,
                                cwd=ROOT, text=True, capture_output=True)
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_function_word_children_and_independent_row_fitting(self):
        self.run_js(r'''
import fs from 'node:fs';
import assert from 'node:assert/strict';
const fw = await import('data:text/javascript;base64,' + Buffer.from(
 fs.readFileSync('app/js/function-word-card.js','utf8')).toString('base64'));
for (const word of ['que','de','se']) {
 for (const lang of ['es','pt']) {
  const parent={targetWord:word};
  assert(fw.getGrammarWordDefinition(parent,lang));
  const child={...parent,isChainChild:true,chainChildKind:'expressions'};
  assert.equal(fw.getGrammarWordDefinition(child,lang),null);
  assert.equal(fw.isFunctionWordCard(child,lang),false);
  assert.equal(fw.functionWordBlockHTML(child,lang),'');
 }
}
const ate=fw.functionWordBlockHTML({targetWord:'até'},'pt');
const patterns=[...ate.matchAll(/class="fw-relation-formula">(.*?)<\/div>/g)]
 .map(match=>match[1].replace(/<[^>]*>/g,''));
assert.deepEqual(patterns,['até + endpoint','até']);
function box(wrapped) {
 const classes=new Set(['is-stacked']);
 return {classes,classList:{remove:k=>classes.delete(k),toggle(k,v){v?classes.add(k):classes.delete(k)}},
 querySelector:s=>s.includes('formula')?{offsetTop:0,offsetHeight:25}:{offsetTop:wrapped?30:0}};
}
const short=box(false),long=box(true);
const list={querySelectorAll:()=>[short,long]};
const root={querySelectorAll:()=>[list]};
fw.fitFunctionWordRows(root);
assert.equal(short.classes.has('is-stacked'),false);
assert.equal(long.classes.has('is-stacked'),true);
// Resize/refit can unstack the long row again.
long.querySelector=short.querySelector;
fw.fitFunctionWordRows(root);
assert.equal(long.classes.has('is-stacked'),false);
''')

    def test_expression_followup_renders_its_saved_indicator(self):
        self.run_js(r'''
import fs from 'node:fs';
import vm from 'node:vm';
import assert from 'node:assert/strict';
const source=fs.readFileSync('app/js/flashcards.js','utf8');
const start=source.indexOf('function renderPhraseRow(');
const end=source.indexOf('\n}\n',start)+3;
const ctx={savedPhraseEntry:()=>({}),isItemSaved:()=>false,
 phraseSourcePillHTML:()=>'',exampleTargetText:()=>'',selectedLanguage:'spanish',
 escapeCardText:s=>String(s).replaceAll('"','&quot;'),SAVE_STAR_ICON:'star',saveItemButtonHTML:()=>''};
vm.createContext(ctx);vm.runInContext(source.slice(start,end),ctx);
const html=ctx.renderPhraseRow({expression:'tener "que"',translation:'have to'},0);
assert(html.includes('data-saved-indicator="tener &quot;que&quot;"'));
assert(html.includes('have to'));
''')

    def test_rarer_pager_renders_the_open_sheet_not_the_underlying_card(self):
        self.run_js(r'''
import fs from 'node:fs';
import vm from 'node:vm';
import assert from 'node:assert/strict';
const source=fs.readFileSync('app/js/flashcards.js','utf8');
const start=source.indexOf('function cycleRarerShade(');
const end=source.indexOf('\n}\n',start)+3;
let sheetRenders=0,cardRenders=0,stopped=0;
const card={},body={scrollTop:123};
const ctx={flashcards:[card],currentIndex:0,document:{
 getElementById:id=>id==='rareUsesModal'?{hidden:false}:body,
 querySelector:()=>{throw Error('must use the visible sheet');}},
 renderRareUsesBody:opts=>{assert.equal(opts.preserveExamples,true);sheetRenders++;body.scrollTop=0;},
 updateCard:()=>cardRenders++,requestAnimationFrame:fn=>fn()};
vm.createContext(ctx);vm.runInContext(source.slice(start,end),ctx);
ctx.cycleRarerShade({stopPropagation:()=>stopped++},'NOUN-0',2,1);
assert.equal(card._rarerShade['NOUN-0'],1);
assert.equal(sheetRenders,1);assert.equal(cardRenders,0);assert.equal(body.scrollTop,123);
ctx.cycleRarerShade(null,'NOUN-0',2,1);assert.equal(card._rarerShade['NOUN-0'],0);
ctx.cycleRarerShade(null,'NOUN-0',2,-1);assert.equal(card._rarerShade['NOUN-0'],1);
assert.equal(stopped,1);
''')

    def test_ordering_preserves_examples_and_lyrics_precedence(self):
        self.run_js(r'''
import fs from 'node:fs';
import vm from 'node:vm';
import assert from 'node:assert/strict';
const mod=await import('data:text/javascript;base64,'+Buffer.from(
 fs.readFileSync('app/js/example-personalisation.js','utf8')).toString('base64'));
const source=fs.readFileSync('app/js/flashcards.js','utf8');
const start=source.indexOf('function sortExamplesByRelevance(');
const end=source.indexOf('\n}\n',start)+3;
const poor={target:'Um exemplo.',english:'An example.',frequency:13,
 metadata:{translation_alignment:{score:0.45,model:'LaBSE',version:'v1'}}};
const good={target:'Uma frase.',english:'A sentence.',frequency:7,
 metadata:{translation_alignment:{score:0.95,model:'LaBSE',version:'v1'}}};
const {exampleTranslationAlignment}=await import('data:text/javascript;base64,'+Buffer.from(
 fs.readFileSync('app/js/example-alignment.js','utf8')).toString('base64'));
const ctx={...mod,exampleTranslationAlignment,getReinforcementWords:()=>new Set(),activeArtist:null,
 exampleIsSingleSentence:()=>true,exampleConfidenceTier:()=>1,
 exampleReinforcementScore:()=>0,exampleSungByActiveArtist:ex=>ex===poor};
vm.createContext(ctx);vm.runInContext(source.slice(start,end),ctx);
const selected=[poor,good],snapshot=JSON.stringify(selected);
const ordered=ctx.sortExamplesByRelevance(selected);
assert.equal(ordered[0],good);assert.equal(ordered[1],poor);
assert.equal(JSON.stringify(selected),snapshot);assert.equal(ordered.length,selected.length);
assert.equal(exampleTranslationAlignment({metadata:{translation_alignment:{score:0}}}),0);
assert.equal(exampleTranslationAlignment({metadata:{translation_alignment:{score:null}}}),null);
assert.equal(exampleTranslationAlignment({}),null);
const unknown={target:'Unknown.',english:'Unknown.',frequency:3};
assert.equal(ctx.sortExamplesByRelevance([unknown,good])[0],good);
assert.equal(ctx.sortExamplesByRelevance([unknown,{...unknown}])[0],unknown);
// Normal pairs tie stably, and the established artist priority is retained.
assert.equal(ctx.sortExamplesByRelevance([good,{...good}])[0],good);
ctx.activeArtist={};assert.equal(ctx.sortExamplesByRelevance(selected)[0],poor);
''')
