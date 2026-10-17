"""Second revision of the diagnostic bridge; v1 remains frozen for replay.
Only the explicitly named development cache is read. No gold or holdout inputs.
"""
import argparse,hashlib,json,re
from collections import Counter
from html import escape
from pathlib import Path
from check import ROOT
OUT=ROOT/'docs/audits/function-word-labels'

def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()

def collect(workspace):
    base=workspace/'audits/hinge-20261014'
    paths=[base/'blind-development.jsonl']+[base/f'parsed-development-{l}.json' for l in ('pt','es')]
    dev=[json.loads(x) for x in paths[0].read_text().splitlines()]
    index={}
    for r in dev:index.setdefault((r['language'],r['word'],r['text']),[]).append(r)
    parsed={l:json.loads((base/f'parsed-development-{l}.json').read_text()) for l in ('pt','es')}
    rows=json.loads((OUT/'findings.json').read_text())['rows'];observations={}
    for row in rows:
        key=row['language']+'|'+row['word']+'|'+row['example_id']
        matches=index.get((row['language'],row['word'],row['sentence']),[])
        if len(matches)!=1:continue
        d=matches[0];p=parsed[row['language']]
        if str(d['review_id']) not in p['rows']:continue
        observations[key]=dict(parser=p['parser'],development_id=d['review_id'],sentence=row['sentence'],spans=d['spans'],sentences=p['rows'][str(d['review_id'])])
    result=dict(input_hashes={str(p):sha(p) for p in paths},rows=observations)
    (OUT/'parse-evidence.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    return result

def decide(row,obs):
    # Never consult editorial decisions, expected patterns, or manually supplied chunks.
    def stop(reason,evidence=None):return dict(status='abstain',reason=reason,evidence=evidence or {})
    if not obs:return stop('No matching development parse; not fetched from another split.')
    text=row['sentence'];word=row['word'];lang=row['language'];label=row['automatic_label']
    spans=obs['spans']
    if len(spans)!=1:return stop('Multiple focus occurrences: occurrence selection is not established.')
    start,end=spans[0]
    if text[start:end].casefold()!=word:return stop('Focus span does not match the card surface.')
    hits=[(sent,w) for sent in obs['sentences'] for w in sent if (w['token']['start_char'],w['token']['end_char'])==(start,end)]
    if len(hits)!=1:return stop('Parser split or merged the focus token; do not guess the contraction/pronoun reading.')
    sent,w=hits[0];byid={x['id']:x for x in sent};head=byid.get(w['head']);gov=byid.get(head['head']) if head else None
    evidence=dict(focus=w,head=head,governor=gov,parser=obs['parser'])
    def span(node):return [node['token']['start_char'],node['token']['end_char']]
    def kids(node):return [x for x in sent if x['head']==node['id']]
    def subtree(node):
        ids={node['id']}
        while True:
            more={x['id'] for x in sent if x['head'] in ids}
            if more<=ids:break
            ids |= more
        return [x for x in sent if x['id'] in ids]
    def chunk_nodes(nodes):
        ranges=sorted(set(tuple(span(n)) for n in nodes if n['upos']!='PUNCT' and n['id']!=w['id']))
        if not ranges:return None
        a,b=ranges[0][0],ranges[-1][1]
        # A contiguous chunk must not swallow unrelated words.
        if any(x['upos']!='PUNCT' and span(x)[0]>=a and span(x)[1]<=b and tuple(span(x)) not in ranges for x in sent):return None
        if a<end and b>start:return None
        return [a,b]
    def noun_chunk(node):
        nodes=subtree(node)
        result=chunk_nodes(nodes)
        # A following comparison may have been attached to the verb instead.
        # Abstain rather than silently truncate the noun phrase.
        if result:
            following=next((n for n in sent if span(n)[0]>=result[1] and n['upos']!='PUNCT'),None)
            if following and following['lemma'].lower() in ('como','que'):
                return None
        return result
    def verb_chunk(node):
        nodes=[node]+[n for n in kids(node) if n['deprel'] in ('aux','aux:pass','compound:prt')]
        # Include an intervening modal governing an infinitive.
        parent=byid.get(node['head'])
        if node['deprel']=='xcomp' and parent and parent['lemma'].lower() in ('poder','deber','dever','querer') and end<=span(parent)[0]<span(node)[0]:
            nodes.append(parent)
        # Lexical direction particles belong to the verbal construction.
        for child in kids(node):
            if child['deprel']=='advmod' and child['lemma'].lower() in ('atrás','adelante','fora','embora'):
                nodes.extend(subtree(child))
        nodes=[n for n in nodes if span(n)[0]>=end]
        result=chunk_nodes(nodes)
        if result and text[end:result[0]].strip():return None
        return result
    def emit(pattern,parts,reason):
        chunks=[dict(slot='connector',start=start,end=end)]+[dict(slot=slot,start=r[0],end=r[1]) for slot,r in parts if r]
        if any(r is None for _,r in parts):return stop('No safe contiguous constituent span.',evidence)
        chunks.sort(key=lambda c:c['start'])
        if word=='de' and [c['slot'] for c in chunks]!=['v','connector','c']:return stop('Word order does not match the displayed de formula.',evidence)
        for c in chunks:c['text']=text[c['start']:c['end']]
        if any(a['end']>b['start'] for a,b in zip(chunks,chunks[1:])):return stop('Overlapping constituent spans.',evidence)
        return dict(status='candidate',pattern=pattern,chunks=chunks,reason=reason,evidence=evidence)
    role=label.get('value');rule=label.get('rule')
    if not head:return stop('No syntactic head available.',evidence)
    if word=='que' and role=='conj_that':
        if w['deprel']=='mark' and (head['deprel']=='ccomp' or (head['deprel']=='xcomp' and any(n['deprel']=='aux' and 'VerbForm=Fin' in (n.get('feats') or '') for n in kids(head)))) and gov and gov['upos']=='VERB':
            # Explicit semantic whitelist for the teaching row, not a surface-form guess.
            thought={'achar','pensar','saber','dizer','esperar','crer','supor','creer','decir','suponer','pensar','saber','esperar'}
            if gov['lemma'].lower() not in thought:return stop('Clause governor is outside the thought/speech pattern scope.',evidence)
            comp=chunk_nodes([n for n in subtree(head) if span(n)[0]>=end])
            return emit(0,[('v',span(gov)),('c',comp)],'Complement clause attached to a licensed thought/speech verb.')
        return stop('Conjunction label lacks a matching complement-clause attachment.',evidence)
    if word=='que' and role=='relative':
        ancestors=[head];cursor=head
        while cursor and cursor['head'] and len(ancestors)<len(sent):
            cursor=byid.get(cursor['head']);ancestors.append(cursor)
            if cursor is None:break
        rel=next((n for n in ancestors if n and n['deprel']=='acl:relcl'),None)
        noun=byid.get(rel['head']) if rel else None
        if noun and noun['upos'] in ('NOUN','PROPN'):
            return emit(1,[('v',span(noun)),('c',chunk_nodes([n for n in subtree(rel) if span(n)[0]>=end]))],'Relative clause attached to a noun antecedent.')
        return stop('Relative label has no confirmed noun antecedent.',evidence)
    if word=='de':
        if rule in ('verb_frame','pronominal_verb_frame') and gov and gov['upos']=='VERB' and head['upos'] in ('VERB','NOUN','PROPN','PRON') and w['deprel'] in ('mark','case'):
            # Compare retained frame to parsed governor to avoid stale frame labels.
            frame=str(label.get('value','')).removesuffix(' de').removesuffix('-se')
            if gov['lemma'].lower().removesuffix('se')!=frame:return stop('Frame label and parsed governor disagree.',evidence)
            return emit(0,[('v',span(gov)),('c',span(head) if head['upos']=='VERB' else noun_chunk(head))],'Governed de frame and dependency agree.')
        if role=='prep' and w['deprel']=='case' and head['deprel']=='nmod' and gov and gov['upos'] in ('NOUN','PROPN'):
            return stop('Noun attachment alone cannot establish the ownership/contents/material/purpose scope of this card.',evidence)
        return stop('Generic de label does not establish either displayed attachment.',evidence)
    if word in ('o','lo'):
        nextword=next((n for n in sent if span(n)[0]>=end and n['upos']!='PUNCT'),None)
        if word=='lo' and w['deprel']=='det' and nextword and nextword['upos']=='ADJ':
            return emit(0,[('c',span(nextword))],'Determiner plus adjective; overrides stale object label.')
        if word=='o' and w['deprel']=='det' and head['upos'] in ('NOUN','PROPN'):
            return emit(0,[('c',noun_chunk(head))],'Article attached to noun.')
        if role=='object_pron' and w['deprel'] in ('obj','iobj') and head['upos']=='VERB' and span(head)[0]>=end:
            if text[end:span(head)[0]].strip():return stop('Intervening verb-complex material requires a complete verb-phrase span.',evidence)
            return emit(1,[('v',verb_chunk(head))],'Object dependency and before-verb placement agree.')
        return stop('Article/object evidence does not fit the displayed formula.',evidence)
    if word=='nos':
        if role=='object_pron' and w['text'].lower()=='nos' and w['deprel'] in ('obj','iobj') and head['upos']=='VERB' and span(head)[0]>=end:
            # First-person plural subjects can signal reflexive/reciprocal use.
            if 'Person=1' in (head.get('feats') or '') and 'Number=Plur' in (head.get('feats') or ''):return stop('First-person plural verb: reflexive/reciprocal interpretation needs a separate check.',evidence)
            return emit(0,[('v',verb_chunk(head))],'Unsplit nos object attached to a non-first-plural verb.')
        return stop('Nos contraction/object interpretation not established.',evidence)
    if word=='se':
        if lang=='pt' and role=='conj_if':
            if head['deprel']=='ccomp':return stop('Embedded whether clause, not the displayed condition/result.',evidence)
            if head['deprel']=='advcl' and gov and gov['deprel']=='root' and start<span(gov)[0]:
                condition=chunk_nodes([n for n in subtree(head) if span(n)[0]>=end])
                condition_ids={n['id'] for n in subtree(head)}
                result=chunk_nodes([n for n in subtree(gov) if n['id'] not in condition_ids and span(n)[0]>end])
                return emit(0,[('v',condition),('c',result)],'Fronted adverbial condition attached to a result clause.')
            return stop('Conditional clause structure is not established.',evidence)
        if head['upos']=='VERB' and span(head)[0]>=end:
            if (w['deprel'] in ('expl:pv','expl') or (w['deprel']=='nsubj' and head['deprel']=='xcomp' and gov and gov['lemma'].lower() in ('poder','dever') and str(role).removesuffix('-se')==head['lemma'].lower())) and rule in ('pronominal_verb','se_verb'):
                return emit(1 if lang=='pt' else 0,[('v',verb_chunk(head))],'Pronominal label and dependency agree.')
            if w['deprel']=='expl:pv' and role=='impersonal_se':
                return emit(0 if lang=='es' else 1,[('v',verb_chunk(head))],'Pronominal dependency contradicts retained impersonal label; diagnostic correction requires review.')
        return stop('Se needs agreement, valency and reflexive/passive checks; parser-label conflict is unresolved.',evidence)
    if word=='al':
        if w['deprel']=='case' and head['deprel']=='obl' and gov and gov['lemma'].lower() in ('ir','venir','llegar','volver','subir','bajar','entrar') and head['lemma'].lower() in ('autobús','tren','avión','colegio','cine','parque','mercado','hospital','aeropuerto','puerto','hotel','restaurante','supermercado','estadio'):
            return emit(0,[('c',noun_chunk(head))],'Motion verb plus explicitly licensed destination noun.')
        if head['lemma'].lower() in ('año','mes','semana','día','hora'):
            return stop('Time/rate noun: generic al label is not destination evidence.',evidence)
        if head['upos']=='VERB' and 'VerbForm=Inf' in (head.get('feats') or '') and head['deprel']=='advcl':
            return emit(1,[('v',span(head))],'Temporal infinitive in an adverbial clause.')
        return stop('Need destination versus personal-a/recipient evidence; no forced assignment.',evidence)
    if word=='naquele' and w['deprel'] in ('case','det') and head['upos']=='NOUN':
        return emit(0,[('c',noun_chunk(head))],'Contraction attached to a noun.')
    return stop('No supported structural rule in this first pass.',evidence)

def render(text,chunks):
    cursor=0;out=[]
    for c in chunks:
        assert cursor<=c['start']<c['end']<=len(text)
        out += [escape(text[cursor:c['start']]),f'<span class="fw-token-{c["slot"]}">{escape(text[c["start"]:c["end"]])}</span>'];cursor=c['end']
    return ''.join(out)+escape(text[cursor:])

def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--collect',action='store_true');ap.add_argument('--workspace',type=Path,default=ROOT.parent/'Fluency-Workspace');args=ap.parse_args()
    cache=collect(args.workspace) if args.collect else json.loads((OUT/'parse-evidence.json').read_text())
    original=json.loads((OUT/'findings.json').read_text())['rows'];out=[]
    for row in original:
        obs=cache['rows'].get(row['language']+'|'+row['word']+'|'+row['example_id'])
        result=decide(row,obs)
        result.update(language=row['language'],word=row['word'],example_id=row['example_id'],sentence=row['sentence'],translation=row['translation'],source=row['source'],prior_review=row['review'],parser_available=bool(obs))
        if result['status']=='candidate':result['targetHTML']=render(row['sentence'],result['chunks'])
        out.append(result)
    counts=Counter(r['status'] for r in out);reasons=Counter(r['reason'] for r in out if r['status']=='abstain')
    (OUT/'syntax-v2-findings.json').write_text(json.dumps(dict(input_hashes={str(p.relative_to(ROOT)):sha(p) for p in [OUT/'parse-evidence.json',OUT/'findings.json',Path(__file__)]},counts=counts,rows=out),ensure_ascii=False,indent=2)+'\n')
    lines=['# Occurrence-level syntax trial','',f'{len(out)} examples; {sum(r["parser_available"] for r in out)} cached development parses; {counts["candidate"]} structural candidates; {counts["abstain"]} abstentions.','',
      'No gold/holdout input was read. This reuses cached development parses, not a new parser run. Candidate rules were developed after inspecting the previous 24-example editorial sample, so agreement on that sample is a regression check, not independent accuracy. All outputs remain diagnostic; no production classifier or data is changed.','',
      'Each candidate includes focus offsets, head/governor, parser identity and automatically extracted spans. Candidates are not automatically approved teaching examples. Existing editorial chunk strings are never used to generate spans.','', '## Abstentions','']
    lines += [f'- {n}: {reason}' for reason,n in reasons.most_common()]
    lines += ['','## Previous reviewed cases (development regression only)','']
    for r in out:
        if r['prior_review']:lines += [f'### {r["language"]} {r["word"]}: {r["sentence"]}',f'Prior review: {r["prior_review"]["decision"]}. Syntax result: {r["status"]}; pattern {r.get("pattern","—")}.',r['reason'],str(r.get('chunks',[])),'']
    lines += ['## Next validation','', 'Inspect fresh structural candidates for semantic fit and chunk boundaries before enabling them in the learner preview. Parser coverage and abstention are not precision. In particular, first-plural filtering alone does not prove non-reciprocal nos; al destination inference and passive se remain deliberately unsupported.']
    (OUT/'syntax-v2-report.md').write_text('\n\n'.join(lines)+'\n');print(dict(counts,parsed=sum(r['parser_available'] for r in out)))
if __name__=='__main__':main()
