import json,pickle,re,sys,os,collections
S=os.environ['NL_SCRATCH']
menus,pools,bank=pickle.load(open(S+'/cache.pkl','rb'))
sample=json.load(open(S+'/sample_r.json'))
spec,out=sys.argv[1],sys.argv[2]
recs=[]
for line in open(spec):
    if not line.strip() or line.startswith('#'): continue
    head,_,note=line.partition('|')
    idx,gold,verdict=head.split()
    x=sample[int(idx)]; word,sid=x['word'],x['sid']; nl,en,src=bank[sid]
    m=list(re.finditer(r"(?<![\w'])"+re.escape(word)+r"(?![\w'])",nl,re.I))[0]
    menu=menus[word]; gi=[] if gold=='-' else [int(g) for g in gold.split(',')]
    recs.append(dict(benchmark='nl-wsd-benchmark/v0',stratum='random',word=word,sentence_id=sid,source=src,text=nl,translation=en,
        span=[m.start(),m.end()],gold_sense_ids=[menu[i][2] for i in gi],gold_glosses=[f'{menu[i][0]}: {menu[i][3]}' for i in gi],
        verdict=verdict,case=None,note=note.strip(),menu_size=len(menu),labelled_by='Claude',blind=True))
with open(out,'w') as f:
    for r in recs: f.write(json.dumps(r,ensure_ascii=False)+'\n')
print(len(recs),collections.Counter(r['verdict'] for r in recs))
