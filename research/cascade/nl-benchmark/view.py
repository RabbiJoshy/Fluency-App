import pickle,json,sys
menus,pools,bank=pickle.load(open('cache.pkl','rb'))
s=json.load(open('sample_r.json'))
a,b=int(sys.argv[1]),int(sys.argv[2])
for i,x in enumerate(s[a:b],a):
    nl,en,_=bank[x['sid']]
    print(f"#{i} {x['word']} ({x['sid'][9:17]}, hits={x['nhits']}) {nl} || {en}")
    for j,(pos,hw,sid,tr,tags) in enumerate(menus[x['word']]):
        print(f"   [{j}] {pos} {hw}: {tr[:110]}")
