"""Occurrence-level automatic assignment. Translation/curation never gate syntax.
Language adapters use explicit syntactic evidence; frozen bridges remain regressions.
"""
from copy import deepcopy
from syntax_bridge_v3 import decide as legacy, render
VERSION='syntax-assignment/v1.1'
THOUGHT={'pt':{'achar','pensar','saber','dizer','esperar','crer','supor','lembrar','esquecer','acreditar','afirmar','contar'},
         'es':{'creer','pensar','saber','decir','esperar','suponer','recordar','olvidar','afirmar','contar'}}


def context(row,obs):
    if not obs or len(obs.get('spans',[]))!=1:return None
    a,b=obs['spans'][0]
    if row['sentence'][a:b].casefold()!=row['word'].casefold():return None
    hits=[(sent,w) for sent in obs['sentences'] for w in sent if bounds(w)==(a,b)]
    if len(hits)!=1:return None
    sent,w=hits[0];byid={n['id']:n for n in sent}
    return sent,w,byid,a,b

def bounds(node):return node['token']['start_char'],node['token']['end_char']
def subtree(sent,node):
    ids={node['id']}
    while True:
        children={n['id'] for n in sent if n['head'] in ids}
        if children<=ids:break
        ids|=children
    return [n for n in sent if n['id'] in ids]

def interval(sent,nodes,focus):
    spans={bounds(n) for n in nodes if n['upos']!='PUNCT' and bounds(n)!=focus}
    if not spans:return None
    a=min(x[0] for x in spans);b=max(x[1] for x in spans)
    if a<focus[1] and b>focus[0]:return None
    if any(n['upos']!='PUNCT' and a<=bounds(n)[0]<b and bounds(n) not in spans for n in sent):return None
    return a,b

def emit(row,obs,pattern,parts,reason,evidence):
    focus=tuple(obs['spans'][0]);pieces=[('connector',focus)]+parts
    if any(span is None for _,span in pieces):return dict(status='abstain',reason='No complete contiguous constituent span.',evidence=evidence)
    chunks=[dict(slot=k,start=a,end=b,text=row['sentence'][a:b]) for k,(a,b) in pieces]
    chunks.sort(key=lambda c:c['start'])
    if any(a['end']>b['start'] for a,b in zip(chunks,chunks[1:])):return dict(status='abstain',reason='Overlapping syntax chunks.',evidence=evidence)
    return dict(status='candidate',pattern=pattern,chunks=chunks,reason=reason,evidence=evidence)

def common(row,obs):
    ctx=context(row,obs)
    if not ctx or row['word'] not in ('que','nos'):return None
    sent,w,byid,start,end=ctx;head=byid.get(w['head']);gov=byid.get(head['head']) if head else None
    if row['word']=='nos' and row['language']=='es':
        if not head or w['upos']!='PRON' or w['deprel'] not in ('obj','iobj') or head['upos']!='VERB':return None
        verbs=[head]+[n for n in sent if n['head']==head['id'] and n['deprel'] in ('aux','aux:pass')]
        if any('Person=1' in (n.get('feats') or '') and 'Number=Plur' in (n.get('feats') or '') for n in verbs):return None
        if not any('VerbForm=Fin' in (n.get('feats') or '') for n in verbs):return None
        verbs += [n for n in sent if n['head']==head['id'] and n['deprel']=='mark' and n['text'].lower()=='a' and any(v['lemma']=='ir' for v in verbs)]
        phrase=interval(sent,verbs,(start,end))
        if phrase and phrase[0]>=end and not row['sentence'][end:phrase[0]].strip():
            return emit(row,obs,0,[('v',phrase)],'Object nos plus complete non-first-plural verb complex.',dict(focus=w,head=head,parser=obs['parser']))
        return None
    if not head or not gov:return None
    if w['deprel']=='mark' and head['deprel'] in ('ccomp','csubj') and gov['upos']=='VERB' and gov['lemma'].lower() in THOUGHT[row['language']]:
        comp=interval(sent,[n for n in subtree(sent,head) if bounds(n)[0]>=end],(start,end))
        if bounds(gov)[1]>start:return None
        return emit(row,obs,0,[('v',bounds(gov)),('c',comp)],'Licensed thought/speech governor and complement attachment.',dict(focus=w,head=head,governor=gov,parser=obs['parser']))
    return None

def complete_chunks(row,obs,result):
    if result['status']!='candidate':return result
    ctx=context(row,obs)
    if not ctx:return result
    sent,w,byid,start,end=ctx;head=byid.get(w['head'])
    revised=deepcopy(result)
    if row['word']=='de' and head and head['upos']=='VERB':
        span=interval(sent,[n for n in subtree(sent,head) if bounds(n)[0]>=end],(start,end))
        if not span:return dict(status='abstain',reason='Cannot retain the full de complement without overlap.',evidence=result.get('evidence',{}))
        for c in revised['chunks']:
            if c['slot']=='c':c.update(start=span[0],end=span[1],text=row['sentence'][span[0]:span[1]])
    if row['word']=='que':
        for c in revised['chunks']:
            if c['slot']!='v':continue
            node=next((n for n in sent if bounds(n)==(c['start'],c['end'])),None)
            if not node:continue
            nodes=[node]
            if revised['pattern']==1 and node['upos'] in ('NOUN','PROPN'):
                nodes += [n for n in sent if n['head']==node['id'] and n['deprel'] in ('det','amod','nummod','compound','flat','flat:name') and bounds(n)[1]<=start]
            if revised['pattern']==0:
                nodes += [n for n in sent if n['head']==node['id'] and n['deprel'] in ('aux','aux:pass')]
                parent=byid.get(node['head'])
                if node['deprel']=='xcomp' and parent and parent['lemma'].lower() in ('ouvir','oír','escuchar') and bounds(parent)[1]<bounds(node)[0]:nodes.append(parent)
            span=interval(sent,nodes,(start,end))
            if span and span[1]<=start:c.update(start=span[0],end=span[1],text=row['sentence'][span[0]:span[1]])
    return revised

def assign(row,obs):
    row=dict(row);row.setdefault('automatic_label',{})
    from syntax_assignment_pt import decide_pt
    from syntax_assignment_es import decide_es
    from syntax_assignment_basic import decide_basic
    from syntax_assignment_shared import decide_shared
    result=decide_basic(row,obs)
    if result is None:result=(decide_pt if row['language']=='pt' else decide_es)(row,obs)
    if result is None:result=common(row,obs)
    if result is None:result=decide_shared(row,obs)
    if result is None:result=legacy(row,obs)
    result=complete_chunks(row,obs,result)
    if result['status']=='candidate':
        chunks=result['chunks'];text=row['sentence']
        assert all(0<=c['start']<c['end']<=len(text) and text[c['start']:c['end']]==c['text'] for c in chunks)
        assert sum(c['slot']=='connector' for c in chunks)==1
        assert all(a['end']<=b['start'] for a,b in zip(chunks,chunks[1:]))
        result=dict(result,pattern_id=f"{row['language']}:{row['word']}:{result['pattern']}",targetHTML=render(text,chunks))
    return dict(result,matcher_version=VERSION)

def assign_occurrences(row,obs):
    """Assign each declared focus occurrence independently; labels must be occurrence-local.
    Discard any sentence-wide retained label when there is more than one occurrence.
    """
    if not obs:return [assign(row,None)]
    multiple=len(obs.get('spans',[]))>1
    return [dict(assign(dict(row,automatic_label={} if multiple else row.get('automatic_label',{})),dict(obs,spans=[span],occurrence_selected=True)),focus_span=span) for span in obs.get('spans',[])]
