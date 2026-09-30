"""Learner-visible regressions from shipped Portuguese, Czech and Spanish cards."""
from pathlib import Path
import shutil
import subprocess
import unittest

ROOT = Path(__file__).resolve().parents[2]

@unittest.skipUnless(shutil.which('node'), 'Node.js required')
class SenseMetadataBehaviorTests(unittest.TestCase):
    def test_unbudgeted_cues_are_stable_across_selection_and_density(self):
        result = subprocess.run(['node', '--input-type=module', '-'], cwd=ROOT, text=True,
            input=r'''import assert from 'node:assert/strict';
import fs from 'node:fs';
import * as ui from './app/js/card-metadata-pills.js';
const fixture=JSON.parse(fs.readFileSync('tests/app/fixtures/sense_metadata_presentation.json'));
for(const cards of Object.values(fixture)) for(const card of cards) for(const meaning of card.meanings) {
 const options={ignoreBudget:true,allowInactivePrimary:true,gloss:ui.projectWiktionaryGloss(meaning,meaning.translation).display,cardMeanings:card.meanings,peerMeanings:ui.senseMetadataPeers(meaning,card.meanings)};
 const active=ui.learnerSensePresentation(meaning,true,{...options,senseCount:20});
 const inactive=ui.learnerSensePresentation(meaning,false,{...options,senseCount:20});
 assert.deepEqual(active.key,inactive.key,card.word);
 assert.equal(active.gloss,inactive.gloss,card.word);
 assert.equal(active.gloss,options.gloss,card.word);
 for(const item of active.grammar.items) assert(['form','construction','function'].includes(ui.grammarCueCategory(item)));
}
const long={translation:'meaning',context:'A useful sense distinction '.repeat(20),pos:'noun'};
for(const senseCount of [1,6,20]) {
 const p=ui.learnerSensePresentation(long,false,{ignoreBudget:true,senseCount,allowInactivePrimary:true});
 assert.equal(p.key.text,long.context.trim());
}
const providers=JSON.parse(fs.readFileSync('tests/app/fixtures/sense_metadata.json'));
for(const [language,word] of [['es','tener'],['pt','gosto'],['cs','čekat']]) {
 const card=providers[language].find(c=>c.word===word);
 assert(card.meanings.some(m=>ui.senseMetadataHTML(m,false,{ignoreBudget:true,allowInactivePrimary:true}).includes('sense-grammar-cue')),word);
}
''', capture_output=True)
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_adaptive_presentation_budget_for_portuguese_czech_and_spanish(self):
        result = subprocess.run(['node', '--input-type=module', '-'], cwd=ROOT, text=True,
            input=r'''
import assert from 'node:assert/strict';
import fs from 'node:fs';
import * as ui from './app/js/card-metadata-pills.js';
const fixture=JSON.parse(fs.readFileSync('tests/app/fixtures/sense_metadata_presentation.json'));
const card=(lang,word)=>fixture[lang].find(c=>c.word===word);
const show=(c,index=0,active=false)=>{
 const meaning=c.meanings[index];
 const gloss=ui.projectWiktionaryGloss(meaning,meaning.translation).display;
 const options={gloss,peerMeanings:ui.senseMetadataPeers(meaning,c.meanings,gloss),cardMeanings:c.meanings,senseCount:c.meanings.length,allowInactivePrimary:true};
 const presentation=ui.learnerSensePresentation(meaning,active,options);
 return {gloss,visibleGloss:presentation.visibleGloss,noteGloss:presentation.noteGloss,hasSenseNote:presentation.hasSenseNote,
  context:presentation.residualContext,visibleContext:presentation.visibleContext,detailContext:presentation.detailContext,
  visible:presentation.visibleItems.map(item=>ui.senseMetadataDisplay(item,options).short),
  details:presentation.detailItems.map(item=>ui.senseMetadataDisplay(item,options).short)};
};

const voces=show(card('pt','vocês'),0,true);
assert.deepEqual(voces.visible,['addressing several people']);
assert(!voces.details.some(label=>/gender|feminine|masculine/.test(label)));
const pra=show(card('pt','pra'));
assert.equal(pra.gloss,'informal form of para');assert.equal(pra.context,'');assert.deepEqual(pra.visible,[]);
const parece=card('pt','parece');
assert.deepEqual(show(parece,0).visible,[]);assert.equal(show(parece,0).context,'');
assert.deepEqual(show(parece,0,true).details,['copulative or auxiliary']);
assert.deepEqual(show(parece,1,true).visible,['with com']);
const uma=card('pt','uma');
assert.equal(show(uma,0).visibleContext,'');assert.equal(show(uma,1).visibleContext,'a bit of');
assert.equal(show(uma,2).visibleContext,'quite a; quite the');assert(show(uma,2).detailContext.includes('quite a'));
assert.equal(show(uma,2).hasSenseNote,false);
const talvez=show(card('pt','talvez'),0,true);
assert.deepEqual(talvez.visible,[]);assert.deepEqual(talvez.details,[]);

const vas=card('cs','vás');
assert.deepEqual(show(vas,0).visible,['plural']);assert.deepEqual(show(vas,1).visible,['formal singular']);
for(const meaning of card('cs','na').meanings){
 const c=card('cs','na'),index=c.meanings.indexOf(meaning),view=show(c,index);
 assert.equal(view.visible.length,1);assert.match(view.visible[0],/^takes (?:accusative|locative) case$/);
}
const podivej=show(card('cs','podívej'),0,true);
assert.deepEqual(podivej.visible,['podívat se na…']);assert(podivej.details.includes('perfective'));assert(!podivej.details.includes('reflexive'));
assert.deepEqual(show(card('cs','to')).visible,['neuter · singular · nom./acc.']);

const longSer={translation:'to be (to have the given quality), especially a quality that is intrinsic or not expected to change, contrasting with estar which denotes a temporary quality',pos:'verb'};
const serView=ui.learnerSensePresentation(longSer,true,{gloss:longSer.translation,senseCount:4,cardMeanings:[longSer],peerMeanings:[]});
// No sibling shares 'to be', so the bracketed definition moves to the note.
assert.equal(serView.visibleGloss,'to be');assert.equal(serView.noteGloss,longSer.translation);assert.equal(serView.hasSenseNote,true);

const porqueGlosses=[
 'because (introduces an explanation to a claim in the previous clause)',
 'because (introduces a reason for that described in the previous clause)',
];
const porqueMeanings=porqueGlosses.map(translation=>({translation,pos:'conj'}));
const porqueViews=porqueMeanings.map((meaning,index)=>ui.learnerSensePresentation(
 meaning,false,{gloss:meaning.translation,senseCount:2,cardMeanings:porqueMeanings,
  peerMeanings:porqueMeanings.filter((_,peerIndex)=>peerIndex!==index),preservePeerGlossDistinction:false}
));
assert.deepEqual(porqueViews.map(view=>view.visibleGloss),['because','because']);
assert.deepEqual(porqueViews.map(view=>view.visibleKey),['introduces an explanation','introduces a reason']);
assert.deepEqual(porqueViews.map(view=>view.noteGloss),porqueGlosses);
for(const view of porqueViews){
 assert.equal(view.gloss,view.visibleGloss);
 assert.equal(view.key.text,view.visibleKey);
 assert.deepEqual(view.key.items,view.visibleItems);
 assert.equal(view.note.gloss,view.noteGloss);
 assert.equal(view.note.available,view.hasSenseNote);
}

const su=card('es','su');assert.deepEqual(show(su,1).visible,['addressing several people']);
assert.deepEqual(show(card('es','ven')).visible,['command']);
console.log('Adaptive metadata presentation examples passed');
''', capture_output=True)
        self.assertEqual(result.returncode, 0, result.stderr)

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
 const options = {ignoreBudget:false, gloss, peerMeanings: ui.senseMetadataPeers(m, c.meanings, gloss), cardMeanings:c.meanings, allowInactivePrimary: true, senseCount: c.meanings.length};
 const presentation = ui.learnerSensePresentation(m, false, options);
 return {gloss, context: presentation.residualContext,
  labels: presentation.visibleItems.map(i => ui.senseMetadataDisplay(i, options).short),
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
assert(ui.senseMetadataHTML(wait,true,project(cekat,wait).options).includes('with na'));
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
// Restrictions compete for the same learner-facing budget rather than all
// appearing just because the release contains them.
const restricted={translation:'to speak',pos:'verb',metadata:{sense_metadata:{contract_version:'sense-metadata/v1',features:[
 {family:'register',kind:'region',value:'Brazil'}, {family:'register',kind:'usage_tag',value:'vulgar'},
 {family:'companion',kind:'required_word',value:'de'}, {family:'domain',kind:'topic',value:'music'}
]}}};
const restrictionOptions={gloss:'to speak',peerMeanings:[],cardMeanings:[restricted],senseCount:1,allowInactivePrimary:true};
const restrictions=ui.learnerSensePresentation(restricted,true,restrictionOptions);
assert.equal(restrictions.visibleItems.length,2);
assert(restrictions.detailItems.length>=1);
// Provider prose is escaped; long notes remain visible without character truncation.
const long={translation:'test',context:'A genuinely distinguishing explanation '.repeat(8)+'<script>',metadata:{sense_metadata:{contract_version:'sense-metadata/v1',features:[]}}};
assert.equal(ui.contextWithoutSenseMetadata(long,false),long.context);
assert(ui.escapeCardText(long.context).includes('&lt;script&gt;'));
const longPresentation=ui.learnerSensePresentation(long,true,{gloss:'test',senseCount:3,cardMeanings:[long],peerMeanings:[]});
assert.equal(longPresentation.visibleContext,'');assert.equal(longPresentation.detailContext,long.context);
// Low-level aspect stays accessible on selection, not in every navigation row.
const asp=ui.senseMetadataHTML(wait,true,{...project(cekat,wait).options,peerMeanings:[]});
assert(asp.includes('imperfective'));assert(asp.includes('sense-note-template'));
// One shared prose rule for dictionary notes, retaining constraints.
assert.equal(ui.readableSenseNote('used to talk about characteristics'),'about characteristics');
assert.equal(ui.readableSenseNote('used in forming the perfect aspect'),'forms the perfect aspect');
assert.equal(ui.readableSenseNote('ending a question; a standalone sentence; ending a question; a standalone sentence'),'ending a question; a standalone sentence');
assert.equal(ui.readableSenseNote('[transitive with a or para or indirect object pronoun] | to provide a service'),'to provide a service (transitive with a or para or indirect object pronoun)');
assert.equal(ui.readableSenseNote('not used with de'),'not used with de');
assert.equal(ui.readableSenseNote('sometimes used with de'),'sometimes used with de');
const dar=card('pt','dar');
for(const m of dar.meanings){
 const p=project(dar,m);
 assert(!p.labels.includes('ditransitive'));
assert(ui.senseMetadataHTML(m,true,p.options).includes('ditransitive'));
}
// Secondary information opens in a dialog instead of expanding the row.
assert(asp.includes('aria-haspopup="dialog"'));
assert(asp.includes('onclick="openSenseNote(event, this)"'));
assert(asp.includes('class="sense-note-template"'));
assert(asp.includes('How it is used'));
assert(!asp.includes('aria-expanded'));
assert(!asp.includes('Collapse notes'));
// Empty space above the bottom toolbar is available for expanded meanings.
const source=fs.readFileSync('app/js/flashcards.js','utf8');
const start=source.indexOf('function availableHeightForMeaningScroll');
const end=source.indexOf('// Disclosures change row height',start);
const available=new Function('getComputedStyle',source.slice(start,end)+'; return availableHeightForMeaningScroll;')(el=>el.css);
const scroll={};
const child=(height,margin,links=false,display='block')=>({offsetHeight:height,classList:{contains:k=>links&&k==='links-section'},css:{position:'static',display,marginTop:String(margin),marginBottom:'0'}});
const back={clientHeight:600,children:[scroll,child(100,0),child(120,0),child(40,200,true),child(99,0,false,'none')],css:{rowGap:'10',paddingTop:'0',paddingBottom:'0'}};
assert.equal(available(back,scroll),310);
assert(asp.includes('aria-hidden="true">i</span>'));assert(asp.includes('class="sense-note-trigger"'));
assert(!asp.includes('•••'));
console.log('40 shipped cards: meaning preservation, restrictions, grammar, cases and provider parity passed');
''', capture_output=True)
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_sense_row_target_collocation_and_unified_example_highlighting(self):
        result = subprocess.run(['node', '--input-type=module', '-'], cwd=ROOT, text=True,
            input=r'''
import assert from 'node:assert/strict';
import fs from 'node:fs';
import * as ui from './app/js/card-metadata-pills.js';

const fixture = JSON.parse(fs.readFileSync('tests/app/fixtures/sense_metadata.json'));
const card = (lang, word) => fixture[lang].find(c => c.word === word);

// 1. extractSenseCompanion: Spanish, Portuguese, Czech
const tener = card('es', 'tener');
const tenerQue = tener.meanings.find(m => m.translation === 'to have to');
const compTener = ui.extractSenseCompanion(tenerQue);
assert.deepEqual(compTener, { terms: ['que'], qualifier: null, isOptional: false });

const gosto = card('pt', 'gosto');
const compGosto = ui.extractSenseCompanion(gosto.meanings[0]);
assert.deepEqual(compGosto, { terms: ['de'], qualifier: null, isOptional: false });

const cekat = card('cs', 'čekat');
const cekatNa = cekat.meanings.find(m => m.translation === 'to wait');
const compCekat = ui.extractSenseCompanion(cekatNa);
assert.deepEqual(compCekat, { terms: ['na'], qualifier: null, isOptional: false });

// Optional companion extraction from context
const optMeaning = { translation: 'to come', context: 'often used with "a"' };
const compOpt = ui.extractSenseCompanion(optMeaning);
assert.deepEqual(compOpt, { terms: ['a'], qualifier: 'often', isOptional: true });

// 2. senseCollocationHTML: physically links the target surface to the companion
const htmlTener = ui.senseCollocationHTML(tenerQue, tener);
assert(htmlTener.includes('class="sense-target-collocation"'));
assert(htmlTener.includes('<span class="sense-collocation-target">tener</span>'));
assert(htmlTener.includes('<span class="sense-collocation-particle">que</span>'));

const htmlGosto = ui.senseCollocationHTML(gosto.meanings[0], gosto);
assert(htmlGosto.includes('<span class="sense-collocation-target">gostar</span>'));
assert(htmlGosto.includes('<span class="sense-collocation-particle">de</span>'));

const htmlOpt = ui.senseCollocationHTML(optMeaning, { targetWord: 'venir' });
assert(htmlOpt.includes('is-optional'));
assert(htmlOpt.includes('<span class="sense-collocation-target">venir</span>'));
assert(htmlOpt.includes('<span class="sense-collocation-particle">+ a</span>'));
assert(htmlOpt.includes('<span class="sense-collocation-qualifier">(often)</span>'));

// 3. excludeCompanion: ensures companion is promoted to sense row and excluded from subsense tier
const metaOptionsExcluded = { gloss: 'to have to', excludeCompanion: true, allowInactivePrimary: true };
const itemsExcluded = ui.compactLearnerSenseMetadata(ui.senseMetadataItems(tenerQue), tenerQue, metaOptionsExcluded);
assert(!itemsExcluded.some(i => i.family === 'companion'));
const pillsHtml = ui.senseMetadataHTML(tenerQue, false, metaOptionsExcluded);
assert(!pillsHtml.includes('sense-pill--companion'));

// 4. Unified example sentence highlighting from flashcards.js
const flashcardsSource = fs.readFileSync('app/js/flashcards.js', 'utf8');
assert(flashcardsSource.includes('function highlightUnifiedCompanionInSentence'));
assert(flashcardsSource.includes('senseCollocationHTML(m, card)'));
assert(flashcardsSource.includes('senseCollocationHTML(mm, card)'));

// Extract highlightUnifiedCompanionInSentence from flashcards.js to test directly
const fnStart = flashcardsSource.indexOf('function highlightUnifiedCompanionInSentence');
const fnEnd = flashcardsSource.indexOf('// Choose a type scale', fnStart);
const fnCode = flashcardsSource.slice(fnStart, fnEnd);
const variantsStart = flashcardsSource.indexOf('const COMPANION_SURFACE_VARIANTS');
const variantsCode = flashcardsSource.slice(variantsStart, fnStart);

const _cachedRegex = (pattern, flags) => new RegExp(pattern, flags);
const highlightFn = new Function(
    'extractSenseCompanion', 'parseSpanishDictUsageContext', '_cachedRegex',
    variantsCode + '\n' + fnCode + '\nreturn highlightUnifiedCompanionInSentence;'
)(ui.extractSenseCompanion, () => null, _cachedRegex);

// Adjacent active phrase is merged into a single example-word-highlight
const sentence1 = 'No sé qué hacer, pero <span class="example-word-highlight">tengo</span> que salir.';
const res1 = highlightFn(sentence1, tenerQue, tener, 'spanish');
assert.equal(res1.html, 'No sé qué hacer, pero <span class="example-word-highlight">tengo que</span> salir.');

// Contiguous in Portuguese: "gosto de"
const sentence2 = 'Eu <span class="example-word-highlight">gosto</span> de você.';
const res2 = highlightFn(sentence2, gosto.meanings[0], gosto, 'portuguese');
assert.equal(res2.html, 'Eu <span class="example-word-highlight">gosto de</span> você.');

// Separated: companion receives unified active styling
const sentence3 = '<span class="example-word-highlight">Tengo</span> mucho que aprender.';
const res3 = highlightFn(sentence3, tenerQue, tener, 'spanish');
assert(res3.html.includes('<span class="example-word-highlight">Tengo</span>'));
assert(res3.html.includes('<span class="example-word-highlight example-companion-highlight" title="Collocation with this sense">que</span>'));

console.log('Sense row collocation and unified example highlighting tests passed');
''', capture_output=True)
        self.assertEqual(result.returncode, 0, result.stderr)
