# Second random draw: 240 more cards (>=2 senses) not in the first 160, one random eligible sentence each.
import pickle,random,json,re
menus,pools,bank=pickle.load(open('cache.pkl','rb'))
first=json.load(open('sample_r.json'))
seen={x['word'] for x in first}
rnd=random.Random(20261013)
cands=sorted(w for w,m in menus.items() if len(m)>=2 and pools.get(w) and w not in seen)
words=rnd.sample(cands,240)
out=[]
for w in words:
    sid=rnd.choice(pools[w]); nl,en,src=bank[sid]
    ms=list(re.finditer(r"(?<![\w'])"+re.escape(w)+r"(?![\w'])",nl,re.I))
    out.append(dict(word=w,sid=sid,occ=0,nhits=len(ms)))
json.dump(first+out,open('sample_r.json','w'),ensure_ascii=False)
print(len(first+out))
