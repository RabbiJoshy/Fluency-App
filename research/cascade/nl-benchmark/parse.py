import sys, json, pickle, os, stanza
S=os.path.dirname(os.path.abspath(__file__))
menus,pools,bank=pickle.load(open(S+'/cache.pkl','rb'))
out=S+'/parses.jsonl'
done=set()
if os.path.exists(out):
    done={json.loads(l)['word'] for l in open(out)}
nlp=stanza.Pipeline('nl',processors='tokenize,mwt,pos,lemma,depparse',download_method=None,use_gpu=False,verbose=False)
with open(out,'a') as f:
    for w in sys.argv[1:]:
        if w in done: continue
        sids=pools[w]
        docs=nlp.bulk_process([stanza.Document([],text=bank[s][0]) for s in sids])
        for sid,d in zip(sids,docs):
            toks=[]
            for sent in d.sentences:
                for t in sent.words:
                    toks.append(dict(id=t.id,text=t.text,lemma=t.lemma,upos=t.upos,head=t.head,deprel=t.deprel,feats=t.feats))
            f.write(json.dumps(dict(word=w,sid=sid,nl=bank[sid][0],en=bank[sid][1],src=bank[sid][2],toks=toks),ensure_ascii=False)+'\n')
        print(w,len(sids),flush=True)
