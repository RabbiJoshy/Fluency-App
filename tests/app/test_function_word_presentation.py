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
// Contraction parts share the heading line; no eyebrow above the patterns.
assert.ok(html.includes('<span class="fw-heading-word">naquele</span><span class="fw-heading-parts">(em + aquele)</span>'));
assert.ok(!html.includes('Example Patterns'));
assert.ok(html.includes('class="fw-relation-meaning">In / on / at that<'));
assert.ok(html.includes('data-pos="contraction"'));
const nos=vm.runInContext("functionWordBlockHTML({word:'nos'},'pt')",ctx);
assert.ok(nos.includes('<span class="fw-heading-parts is-dynamic" hidden></span>'));
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
const artistHtml = vm.runInContext("functionWordBlockHTML({word:'como', channel:'artist', artist:'Portuguese Playlist'},'pt')", ctx);
assert.ok(artistHtml.includes('data-deck="artist"'));
assert.ok(artistHtml.includes('data-artist="Portuguese Playlist"'));
assert.ok(artistHtml.includes('Portuguese Playlist'));
const speechHtml = vm.runInContext("functionWordBlockHTML({word:'como', channel:'speech'},'pt')", ctx);
assert.ok(speechHtml.includes('data-deck="speech"'));
const artistShortageHtml = vm.runInContext("functionWordBlockHTML({word:'como', channel:'artist', artist:'Artist A With Shortage'},'pt')", ctx);
assert.ok(!artistShortageHtml.includes('Portuguese Playlist'), 'Shortage for Artist A must not return Portuguese Playlist lyrics');
const fixtureNoSpeech = {
    tag: 'Like / in the same way',
    speech_examples: [],
    artist_examples: [{sentence:'s', targetHTML:'Song by Artist B', source:'Artist B · Song', channel:'artist', metadata:{source:{artist:'Artist B'}}}],
    examples: [{sentence:'s', targetHTML:'Song by Artist B', source:'Artist B · Song', channel:'artist', metadata:{source:{artist:'Artist B'}}}]
};
const resNoSpeech = vm.runInContext("getRelationExamples(" + JSON.stringify(fixtureNoSpeech) + ", {channel:'artist', artist:'Artist A'})", ctx);
assert.equal(resNoSpeech.length, 0, 'Must exclude Artist B lyrics when speech_examples is empty');

// Regression test: Rendered card and DOM refresh when relation only has Artist B lyrics (no safe speech/curriculum examples)
vm.runInContext(`
PORTUGUESE_GRAMMAR_WORDS['test_shortage'] = {
    word: 'test_shortage',
    relations: [{
        tag: 'Like / in the same way',
        targetHTML: 'Song by Artist B',
        translation: 'Artist B lyric translation',
        source: 'Artist B · Song',
        speech_examples: [],
        artist_examples: [{sentence:'s', targetHTML:'Song by Artist B', source:'Artist B · Song', channel:'artist', metadata:{source:{artist:'Artist B'}}}],
        examples: [{sentence:'s', targetHTML:'Song by Artist B', source:'Artist B · Song', channel:'artist', metadata:{source:{artist:'Artist B'}}}]
    }]
};
PORTUGUESE_GRAMMAR_WORDS['test_shortage'].uses = PORTUGUESE_GRAMMAR_WORDS['test_shortage'].relations;

PORTUGUESE_GRAMMAR_WORDS['test_curriculum_fallback'] = {
    word: 'test_curriculum_fallback',
    relations: [{
        tag: 'Like / in the same way',
        targetHTML: 'Ela precisa de dinheiro.',
        translation: 'She needs money.',
        source: 'Everyday speech',
        speech_examples: [],
        artist_examples: [{sentence:'s', targetHTML:'Song by Artist B', source:'Artist B · Song', channel:'artist', metadata:{source:{artist:'Artist B'}}}],
        examples: [{targetHTML: 'Ela precisa de dinheiro.', translation: 'She needs money.', source: 'Everyday speech'}]
    }]
};
PORTUGUESE_GRAMMAR_WORDS['test_curriculum_fallback'].uses = PORTUGUESE_GRAMMAR_WORDS['test_curriculum_fallback'].relations;
`, ctx);

const renderedShortageCard = vm.runInContext("functionWordBlockHTML({word:'test_shortage', channel:'artist', artist:'Artist A'}, 'pt')", ctx);
assert.ok(!renderedShortageCard.includes('Song by Artist B'), 'Rendered card must NOT show Artist B lyrics when Artist A is selected');
assert.ok(!renderedShortageCard.includes('Artist B lyric translation'), 'Rendered card must NOT show Artist B translation');
assert.ok(renderedShortageCard.includes('No matching examples found'), 'Rendered card must show shortage message');
assert.ok(renderedShortageCard.includes('Shortage'), 'Rendered card must show shortage badge');

const shortageNodes = {'.fw-sentence-target':{}, '.fw-sentence-translation':{}, '.fw-credit-start':{}, '.fw-sentence-ticks-container':{}};
ctx.document.querySelector = (sel) => {
    if (sel === '.fw-deterministic-card') {
        return {
            dataset: {word: 'test_shortage', lang: 'pt', deck: 'artist', artist: 'Artist A'},
            querySelectorAll: () => [],
            querySelector: s => shortageNodes[s]
        };
    }
    return null;
};
vm.runInContext('_activeExampleIndex = 0; refreshFunctionWordCardBack()', ctx);
assert.ok(!shortageNodes['.fw-sentence-target'].innerHTML.includes('Song by Artist B'), 'Refresh must NOT display Artist B default sentence');
assert.ok(shortageNodes['.fw-sentence-target'].innerHTML.includes('No matching examples found'), 'Refresh must display shortage message');
assert.ok(shortageNodes['.fw-sentence-translation'].textContent.includes('shortage'), 'Refresh must display shortage translation text');
assert.ok(shortageNodes['.fw-credit-start'].innerHTML.includes('Shortage'), 'Refresh must display shortage credit');

vm.runInContext('cycleFunctionWordExample()', ctx);
assert.ok(!shortageNodes['.fw-sentence-target'].innerHTML.includes('Song by Artist B'), 'Cycle must NOT cycle to Artist B sentence');

const renderedCurriculumCard = vm.runInContext("functionWordBlockHTML({word:'test_curriculum_fallback', channel:'artist', artist:'Artist A'}, 'pt')", ctx);
assert.ok(!renderedCurriculumCard.includes('Song by Artist B'), 'Rendered card must NOT show Artist B lyrics');
assert.ok(renderedCurriculumCard.includes('Ela precisa de dinheiro.'), 'Rendered card must show safe curriculum example');

// Regression test: Missing/empty source metadata must NOT be accepted as curriculum fallback
vm.runInContext(`
PORTUGUESE_GRAMMAR_WORDS['test_missing_metadata'] = {
    word: 'test_missing_metadata',
    relations: [{
        tag: 'Like / in the same way',
        targetHTML: 'Unlabelled song lyric by Artist B',
        translation: 'Artist B lyric translation',
        // NO source, NO channel, NO metadata
        speech_examples: [],
        artist_examples: [],
        examples: [{targetHTML: 'Unlabelled song lyric by Artist B', translation: 'Artist B lyric translation'}]
    }]
};
PORTUGUESE_GRAMMAR_WORDS['test_missing_metadata'].uses = PORTUGUESE_GRAMMAR_WORDS['test_missing_metadata'].relations;
`, ctx);

const renderedMissingMetaCard = vm.runInContext("functionWordBlockHTML({word:'test_missing_metadata', channel:'artist', artist:'Artist A'}, 'pt')", ctx);
assert.ok(!renderedMissingMetaCard.includes('Unlabelled song lyric by Artist B'), 'Missing source metadata must NOT be accepted as curriculum fallback');
assert.ok(renderedMissingMetaCard.includes('No matching examples found'), 'Must preserve shortage when source metadata is missing');
assert.ok(renderedMissingMetaCard.includes('Shortage'), 'Must display shortage badge when source metadata is missing');


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
