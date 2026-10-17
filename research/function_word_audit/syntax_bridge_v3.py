"""Bounded recovery of de + infinitive; preserve frozen v1/v2 evidence.
Display formulas are not used as recognition rules.
"""
import json
from collections import Counter
from syntax_bridge_v2 import decide as previous, render, OUT, ROOT, sha

# Explicit construction licences, not guesses from a shortened teaching formula.
FRAMES={'pt':{'impedir','precisar','gostar','deixar','parar','acabar'},
        'es':{'dejar','acabar','tratar','parar'}}
ACTION_NOUNS={'pt':{'hora','momento','jeito','maneira','forma'},
              'es':{'hora','momento','manera','forma'}}


def decide(row, obs):
    result=previous(row,obs)
    if result['status']=='candidate' or not obs or row['word']!='de':return result
    if len(obs['spans'])!=1:return result
    start,end=obs['spans'][0];text=row['sentence']
    if text[start:end].casefold()!='de':return result
    hits=[(s,w) for s in obs['sentences'] for w in s if (w['token']['start_char'],w['token']['end_char'])==(start,end)]
    if len(hits)!=1:return result
    sent,focus=hits[0];nodes={w['id']:w for w in sent};verb=nodes.get(focus['head'])
    if not verb or verb['upos']!='VERB' or 'VerbForm=Inf' not in (verb.get('feats') or '') or focus['deprel']!='mark':return result
    governor=nodes.get(verb['head'])
    if not governor or governor['token']['end_char']>start:return result
    lang=row['language'];pattern=None
    if governor['upos']=='VERB' and governor['lemma'].lower() in FRAMES.get(lang,set()) and verb['deprel']=='xcomp':pattern=0
    if governor['upos']=='NOUN' and governor['lemma'].lower() in ACTION_NOUNS.get(lang,set()) and verb['deprel']=='acl':pattern=1
    if pattern is None:return result
    ids={verb['id']}
    while True:
        more={w['id'] for w in sent if w['head'] in ids}
        if more<=ids:break
        ids|=more
    content=[w for w in sent if w['id'] in ids and w['id']!=focus['id'] and w['upos']!='PUNCT']
    if not content:return result
    a=min(w['token']['start_char'] for w in content);b=max(w['token']['end_char'] for w in content)
    if a<end or text[end:a].strip():return result
    if any(w['upos']!='PUNCT' and a<=w['token']['start_char']<b and w['id'] not in ids for w in sent):return result
    chunks=[dict(slot='v',start=governor['token']['start_char'],end=governor['token']['end_char']),dict(slot='connector',start=start,end=end),dict(slot='c',start=a,end=b)]
    for c in chunks:c['text']=text[c['start']:c['end']]
    return dict(status='candidate',pattern=pattern,chunks=chunks,
                reason='Licensed governor plus de-marked infinitive; full action subtree retained.',
                evidence=dict(focus=focus,head=verb,governor=governor,parser=obs['parser']))


def main():
    rows=json.loads((OUT/'findings.json').read_text())['rows'];cache=json.loads((OUT/'parse-evidence.json').read_text())['rows']
    results=[];changes=[]
    for row in rows:
        obs=cache.get(row['language']+'|'+row['word']+'|'+row['example_id'])
        result=decide(row,obs)
        result.update(language=row['language'],word=row['word'],example_id=row['example_id'],sentence=row['sentence'],translation=row['translation'])
        if result['status']=='candidate':result['targetHTML']=render(row['sentence'],result['chunks'])
        if previous(row,obs)['status']!=result['status']:changes.append(result)
        results.append(result)
    output=dict(counts=dict(Counter(r['status'] for r in results)),changes=changes,rows=results,
                input_hashes={str(p.relative_to(ROOT)):sha(p) for p in [OUT/'findings.json',OUT/'parse-evidence.json',ROOT/'research/function_word_audit/syntax_bridge_v2.py',ROOT/'research/function_word_audit/syntax_bridge_v3.py']})
    (OUT/'syntax-v3-findings.json').write_text(json.dumps(output,ensure_ascii=False,indent=2)+'\n')
    print(output['counts'])
    for r in changes:print(r['example_id'],r['language'],r['pattern'],r['sentence'],[(c['slot'],c['text']) for c in r['chunks']])

if __name__=='__main__':main()
