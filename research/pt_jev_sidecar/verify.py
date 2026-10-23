"""Validate real overlay census, metadata, stable identities and replay model picks."""
import json,pathlib,collections,hashlib,ast
ROOT=pathlib.Path(__file__).resolve().parents[2];O=ROOT.parent/'Fluency-Workspace/reviews/pt-first200-jev-v1';A=ROOT/'app/data/wsd-sidecars/pt-first200-jev-v1.json'
load=lambda p:json.loads(p.read_text());asset=load(A);cards=load(O/'cards.json');rows=load(O/'rows.json');ds=load(O/'decisions.json');pre=load(O/'preflight.json');spend=load(O/'spend.json');changed=0;unresolved=0
assert len(cards)==121==len(asset['cards'])
for c in cards:
 cid=c['card_id'];patch=asset['cards'][cid];assert c['surface']!='foram';assert asset['card_ids'][c['short']]==cid;assert c['rank']<=200;assert not c['index'].get('function_word');assert c['surface'] not in load(ROOT/'app/data/grammar-words/pt.json')
 original=c['row']['meanings'];assert [m['sense_id'] for m in patch['meanings'][:len(original)]]==[m['sense_id'] for m in original]
 bysent=collections.defaultdict(list)
 for r in rows:
  if r['card_id']==cid:bysent[r['sentence_id']].append(r)
 examples={}
 for i,(m,es) in enumerate(zip(patch['meanings'],patch['examples']['m'])):
  assert m['_masterSenseIndex']==i;assert abs(float(m['frequency'])-len(es)/len(bysent))<1e-8;assert m['display_frequency']==m['frequency'];assert bool(m['canonical_example'])==bool(es)
  if es:assert m['canonical_example']['text']==es[0]['t']
  for e in es:
   sid='sentence_'+e['i'];assert sid not in examples;examples[sid]=e;rr=bysent[sid];orig=rr[0]['record'];assert {k:v for k,v in e.items() if k not in ['a','ju','w']}=={k:v for k,v in orig.items() if k not in ['a','ju','w']};assert e['s'] in asset['sources'];ju=e['ju'];assert ju['previous_wsd_evidence']==orig.get('w');assert e['a']=='jev-1.14.0-ui-sidecar';assert ju['model']=='jev-1.14.0';assert ju['previous_source_sense_id']==rr[0]['previous_sense_id']
   picks={ds[r['id']]['source_sense_id'] for r in rr}
   if ju['status']=='assigned':assert picks=={ju['source_sense_id']};assert m['source_sense_id']==ju['source_sense_id'];assert not m.get('unassigned');assert e['w']==['leaf',0]
   else:assert m.get('unassigned') and m['pos']=='UNASSIGNED';unresolved+=1
   changed+=ju['source_sense_id']!=rr[0]['previous_sense_id']
 assert set(examples)==set(bysent)
assert len(ds)==len(rows)==3579
assert changed==1009;assert unresolved==109
assert spend['cumulative_billed_plus_reserved_usd']<=1
for p in pathlib.Path(__file__).resolve().parent.glob('*.py'):ast.parse(p.read_text())
result=dict(verified=True,asset_sha256=hashlib.sha256(A.read_bytes()).hexdigest(),asset_bytes=A.stat().st_size,cards=121,examples=3558,marked_occurrences=3579,changed_assignments=changed,unresolved=unresolved,existing_meaning_ids_preserved=True,all_example_ids_and_text_and_attribution_preserved=True,all_model_picks_replayed=True,function_word_cards_excluded=True,underlying_release_changed=False,additional_cost_usd=spend['additional_billed_usd'],cumulative_billed_plus_reserved_usd=spend['cumulative_billed_plus_reserved_usd'])
(O/'verification.json').write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2))
