import json, sys, pickle, os
R='/Users/joshuathomasamar/PycharmProjects/Fluency-Workspace/runs/nl/speech/20261012T175838Z-76d34ee3/stages'
S=os.path.dirname(__file__)
cache=S+'/cache.pkl'
if os.path.exists(cache):
    menus,pools,bank=pickle.load(open(cache,'rb'))
else:
    m=json.load(open(R+'/02_sense_menu/output/sense-menu.json'))
    menus={c['surface_form']:[(a['part_of_speech'],a['headword'],s['sense_id'],s['translation'],s['metadata']['source_metadata'].get('tags',[])) for a in c['analyses'] for s in a['senses']] for c in m['cards']}
    p=json.load(open(R+'/04_pools/output/pools.json'))
    pools={c['display_form']:[x['sentence_id'] for x in c['candidates'] if x['eligible']] for c in p['cards']}
    need={s for v in pools.values() for s in v}
    bank={}
    for line in open(R+'/03_sentence_harvest/output/sentence-bank.jsonl'):
        r=json.loads(line)
        if r['sentence_id'] in need: bank[r['sentence_id']]=(r['target']['text'],r['translation']['text'],r['source']['name'])
    pickle.dump((menus,pools,bank),open(cache,'wb'))
for w in sys.argv[1:]:
    print('=== ',w)
    for i,(pos,hw,sid,tr,tags) in enumerate(menus[w]):
        print(f'  [{i}] {pos} {hw}: {tr}  {",".join(t for t in tags if t not in ("not-comparable",))}')
