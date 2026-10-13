import json,pickle,re,sys,os
S=os.environ['NL_SCRATCH']
menus,pools,bank=pickle.load(open(S+'/cache.pkl','rb'))
parses={}
for l in open(S+'/parses.jsonl'):
    r=json.loads(l); parses[(r['word'],r['sid'])]=r
spec,out=sys.argv[1],sys.argv[2]
recs=[]
for line in open(spec):
    if not line.strip() or line.startswith('#'): continue
    head,_,note=line.partition('|')
    sid8,word,occ,gold,verdict,case=head.split()
    sid=[s for s in pools[word] if s[9:17]==sid8]; assert len(sid)==1,(sid8,word)
    sid=sid[0]; nl,en,src=bank[sid]
    ms=[m for m in re.finditer(r"(?<![\w'])"+re.escape(word)+r"(?![\w'])",nl,re.I)]
    m=ms[int(occ)]
    menu=menus[word]
    gi=[] if gold=='-' else [int(x) for x in gold.split(',')]
    p=parses.get((word,sid)); tgt=None
    if p:
        hits=[t for t in p['toks'] if t['text'].lower()==word.lower()]
        if len(hits)>int(occ): t=hits[int(occ)]; tgt={'upos':t['upos'],'deprel':t['deprel']}
    recs.append(dict(benchmark='nl-wsd-benchmark/v0',stratum='hard',word=word,sentence_id=sid,source=src,text=nl,translation=en,
        span=[m.start(),m.end()],gold_sense_ids=[menu[i][2] for i in gi],gold_glosses=[f'{menu[i][0]}: {menu[i][3]}' for i in gi],
        verdict=verdict,case=case,note=note.strip(),menu_size=len(menu),stanza=tgt,labelled_by='Claude',blind=False))
with open(out,'w') as f:
    for r in recs: f.write(json.dumps(r,ensure_ascii=False)+'\n')
import collections
print(len(recs),collections.Counter(r['verdict'] for r in recs))
