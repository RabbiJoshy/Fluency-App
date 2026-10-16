"""Embed the app's existing provenance components in the isolated file preview."""
import base64
import re
from check import ROOT


def function_source(source, name):
    match=re.search(r'^(?:export )?function '+re.escape(name)+r'\([^\n]*\) \{.*?^\}',source,re.M|re.S)
    if not match:raise ValueError(f'App provenance helper not found: {name}')
    return re.sub(r'^export ','',match.group())


def script():
    source=(ROOT/'app/js/flashcards.js').read_text()
    names=['normalizedExampleProvenance','sourceTitleRecord','sourceTitleLabel','outboundLeaveButton',
           'outboundChipHTML','outboundChipKeydown','disarmOutboundLinks','armOutboundLink','confirmOutboundLink',
           'exampleFaviconHTML','exampleSourceChipHTML','dictionaryProviderCredit','exampleProvenanceHTML']
    icon=re.search(r'^const OUTBOUND_LEAVE_ICON = .*?;$',source,re.M).group()
    html_escape=function_source((ROOT/'app/js/card-metadata-pills.js').read_text(),'escapeCardText')
    result='\n'.join([html_escape,icon,'let _sourceTitles = null;']+[function_source(source,n) for n in names])
    # Same app assets, embedded so both file:// and the limited localhost server work.
    for asset in ('tatoeba.svg','wikipedia-w.svg'):
        data=base64.b64encode((ROOT/'app/icons'/asset).read_bytes()).decode()
        result=result.replace(f"'icons/{asset}'",f"'data:image/svg+xml;base64,{data}'")
    return result+r'''
function paintPreviewProvenance(){
 const lang=previewElement('language').value,word=previewElement('word').value;
 const ex=getGrammarWordDefinition(word,lang).relations[_activeRelIndex].examples[_activeExampleIndex];
 const credit=document.querySelector('.fw-credit-start');
 if(ex.metadata?.source?.source_record_id){credit.innerHTML=exampleProvenanceHTML(ex)||'';}
 else {credit.textContent=String(ex.source||'').startsWith('Original teaching example')?'Teaching example':'Source not verified';}
}
'''
