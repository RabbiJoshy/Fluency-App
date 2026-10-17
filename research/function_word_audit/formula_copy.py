"""Explicit display-only reductions; never remove recognition or example slots."""
import re

# Retain the distinctive verb/noun frame; the example supplies its completion.
DROP_COMPLETION = {l:{('de',0),('de',1),('que',0),('que',1),('que',2),('como',0)} for l in ('pt','es')}
# Here the complement distinguishes the use, while the generic leading context adds little.
DROP_CONTEXT = {
    'pt':{('em',0),('em',1),('para',0),('para',1),('para',2),('com',0),('com',1),('por',0),('por',1),('mas',0),('a',0),('sem',0),('sobre',0),('sobre',1),('até',0),('porque',0)},
    'es':{('a',0),('a',1),('en',0),('en',1),('por',0),('por',1),('para',0),('para',1),('con',0),('con',1),('sin',0),('pero',0),('porque',0)}}


def simplify(lang, word, index, relation):
    key=(word,index);html=relation['formulaHTML']
    if key in DROP_COMPLETION[lang]:
        relation['formulaHTML']=re.sub(r' \+ <span class="fw-token-c">.*?</span>$','',html)
        return 'Keep the distinctive frame; show its completion in the example.'
    if key in DROP_CONTEXT[lang]:
        relation['formulaHTML']=re.sub(r'^<span class="fw-token-v">.*?</span> \+ ','',html)
        return 'Keep the complement that distinguishes the use; omit generic preceding context.'
    return 'Retain: the displayed elements teach the relationship or required form. Contraction decompositions remain explicit.'
