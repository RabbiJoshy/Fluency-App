import pickle,random,json,re
menus,pools,bank=pickle.load(open('cache.pkl','rb'))
rnd=random.Random(20261012)
cands=sorted(w for w,m in menus.items() if len(m)>=2 and pools.get(w))
words=rnd.sample(cands,160)
out=[]
for w in words:
    sid=rnd.choice(pools[w]); nl,en,src=bank[sid]
    ms=list(re.finditer(r"(?<![\w'])"+re.escape(w)+r"(?![\w'])",nl,re.I))
    out.append(dict(word=w,sid=sid,occ=0,nhits=len(ms)))
json.dump(out,open('sample_r.json','w'),ensure_ascii=False)
print(len(cands))
