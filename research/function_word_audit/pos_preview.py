"""Preview-only whole-chunk colours derived from formula slots."""
import re
from check import ROOT


def payload():
    source=(ROOT/'app/js/flashcards.js').read_text()
    block=source.split('function getPosAccentRgb(pos) {',1)[1].split('};',1)[0]
    palette=dict(re.findall(r"'pos-([^']+)': '([\d, ]+)'",block))
    assert all(k in palette for k in ('noun','verb','pron','prep','det','conj'))
    return dict(palette=palette)


SCRIPT = r'''
function chunkColour(label,side,slotType){
 const text=label.trim().toLowerCase();
 let pos=null;
 if(slotType){
  const rgb=POS_PREVIEW.palette[slotType];
  return rgb ? `rgb(${rgb})` : (side==='v'?'#8fb8d8':'#c3a6df');
 }
 if(/^(?:a )?(?:(?:masculine|feminine|singular|plural) )*noun$/.test(text))pos='noun';
 else if(/^(?:a )?verb$/.test(text)||/^infinitive(?: \(dictionary form\))?$/.test(text))pos='verb';
 else if(text==='adjective')pos='adj';
 else if(text==='pronoun')pos='pron';
 if(!pos)return side==='v'?'#8fb8d8':'#c3a6df';
 const rgb=POS_PREVIEW.palette[pos].split(',').map(Number);
 return `rgb(${rgb.join(',')})`;
}
function paintPreviewPOS(){
 const lang=previewElement('language').value,word=previewElement('word').value;
 const entry=getGrammarWordDefinition(word,lang),relations=entry.relations;
 const enabled=previewElement('colours').value==='pos';document.querySelector('.preview-card').classList.toggle('preview-pos',enabled);
 const colours=[];
 document.querySelectorAll('.fw-relation-box').forEach((box,i)=>{
  const formula=box.querySelector('.fw-relation-formula');formula.innerHTML=relations[i].formulaHTML;colours[i]={};
  for(const side of ['v','c']){
   const slot=formula.querySelector('.fw-token-'+side);
   if(slot){colours[i][side]=chunkColour(slot.textContent,side,relations[i].slotTypes?.[side]);if(enabled)slot.style.color=colours[i][side];}
  }
 });
 const relation=relations[_activeRelIndex],example=relation.examples[_activeExampleIndex];
 const sentence=document.querySelector('.fw-sentence-target');sentence.innerHTML=example.targetHTML;
 if(enabled)for(const side of ['v','c'])sentence.querySelectorAll('.fw-token-'+side).forEach(el=>{el.style.color=colours[_activeRelIndex][side]||chunkColour('',side);});
 const section=document.querySelector('.fw-section-header');
 document.querySelectorAll('.fw-parts-box').forEach(parts=>section.before(parts));
 const heading=document.querySelector('.fw-heading');heading.removeAttribute('style');heading.removeAttribute('title');heading.removeAttribute('data-pos');
 document.querySelector('.fw-section-header').textContent='Function Word · Example Patterns';
 document.querySelectorAll('.fw-part-pill').forEach(el=>{el.removeAttribute('style');el.removeAttribute('title');});
}
const originalPreviewRefresh=refreshFunctionWordCardBack;
refreshFunctionWordCardBack=function(){originalPreviewRefresh();paintPreviewPOS();paintPreviewProvenance();};
'''
