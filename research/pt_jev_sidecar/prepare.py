"""Freeze first-200 ordinary-card scope; reuse exact-menu previously paid Jev decisions."""
import json,pathlib,re,hashlib,collections
ROOT=pathlib.Path(__file__).resolve().parents[2];WS=ROOT.parent/'Fluency-Workspace';OUT=WS/'reviews/pt-first200-jev-v1';OLD=WS/'reviews/portuguese-verbs-jev-20261023';REL=ROOT/'dist/pt-finite-staging/pt/speech/pt-speech-v25-literal-ground-r4-10000x30-fw1-deepseek-v25-finite-v1-slim';RUN=WS/'runs/pt/speech/20261013T133630Z-12746d8c'
def load(p):return json.loads(p.read_text())
def save(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=1))
def sha(x):return hashlib.sha256(json.dumps(x,ensure_ascii=False,sort_keys=True).encode()).hexdigest()
allidx=sorted(load(REL/'app/vocabulary.index.json'),key=lambda c:c['rank'])[:200];grammar=load(ROOT/'app/data/grammar-words/pt.json');idx=[c for c in allidx if not c.get('function_word') and c['word'].lower() not in grammar];source={c['card_id']:c for c in load(RUN/'stages/02_sense_menu/output/sense-menu.json')['cards']};byshort={c['id']:c for c in idx};cards={};rows=[]
oldcards={c['card_id']:c for c in load(OLD/'cards.json')};oldrows=load(OLD/'rows.json');oldanswers={};oldroles={};oldrefs={}
for f in sorted((OLD/'responses').glob('*.json')):
 x=load(f)
 if x['status']!='ok':continue
 if x['condition']=='role_guided14':
  oldanswers.update(x['response']['answers'])
  for k in x['response']['answers']:oldrefs[k]=dict(audit='portuguese-verbs-jev-2026-10-23',request_index=x['request_index'],payload_sha256=x['payload_sha256'])
 if x['condition']=='screen':oldroles.update(x['response']['answers'])
oldby={(x['card_id'],x['sentence_id'],tuple(x['span'])):x for x in oldrows};reused={}
for mf in load(REL/'app/vocabulary.examples.manifest.json')['shards']:
 if mf['start_rank']>200:continue
 examples=load(REL/'app/vocabulary.examples.shards'/pathlib.Path(mf['path']).name);fat=load(REL/'app/vocabulary.index.rows'/pathlib.Path(mf['path']).name)
 for short,c in byshort.items():
  if short not in examples:continue
  cid=c['surface_card_id'];menu=[]
  for a in source[cid]['analyses']:
   for s in a['senses']:menu.append(dict(id=s['sense_id'],headword=a['headword'],pos=a['part_of_speech'],gloss=s['translation'],usage=s.get('definition','')))
  for m in c['meanings']:
   sid=m.get('source_sense_id')
   if sid and sid not in {x['id'] for x in menu}:menu.append(dict(id=sid,headword=m['headword'],pos=m['pos'],gloss=m['translation'],usage=m.get('context','')))
  cards[cid]=dict(card_id=cid,short=short,rank=c['rank'],surface=c['word'],menu=menu,index=c,row=fat[short],shard=pathlib.Path(mf['path']).name,menu_sha256=sha(menu))
  for mi,es in enumerate(examples[short]['m']):
   m=fat[short]['meanings'][mi];previous=c['meanings'][mi].get('source_sense_id') or m.get('source_sense_id') or m['source_reference'].removeprefix('kaikki-senseid:').removeprefix('kaikki:')
   for e in es:
    spans=[z.span() for z in re.finditer(r'(?<!\w)'+re.escape(c['word'])+r'(?!\w)',e['t'],re.I)]
    for oi,span in enumerate(spans or [None]):
     marked=e['t'] if span is None else e['t'][:span[0]]+'<<'+e['t'][span[0]:span[1]]+'>>'+e['t'][span[1]:]
     x=dict(card_id=cid,sentence_id='sentence_'+e['i'],surface=c['word'],rank=c['rank'],span=list(span) if span else None,occurrence=oi,text=e['t'],marked=marked,record=e,previous_sense_id=previous,previous_meaning_index=mi);rows.append(x)
rows.sort(key=lambda x:(x['rank'],x['sentence_id'],x['occurrence']))
for i,x in enumerate(rows,1):
 x['id']=f'J{i:04}';cid=x['card_id'];old=oldby.get((cid,x['sentence_id'],tuple(x['span'] or [])))
 if old and old['id'] in oldanswers and cid in oldcards and sha(cards[cid]['menu'])==sha(oldcards[cid]['menu']) and old['text']==x['text']:
  a=oldanswers[old['id']];choice=a['choice'];sid=cards[cid]['menu'][int(choice)-1]['id'] if choice.isdigit() else choice
  reused[x['id']]=dict(source_sense_id=sid,answer=a,model='jev-1.14.0',role=oldroles.get(old['id']+'_role'),provenance=dict(reused=True,old_occurrence_id=old['id'],**oldrefs[old['id']]))
save(OUT/'cards.json',list(cards.values()));save(OUT/'rows.json',rows);save(OUT/'reused.json',reused)
oldrequests=load(OLD/'requests.json');reference=next(x['body'] for x in oldrequests if x['condition']=='role_guided14');guide=reference['state']['grammar_guide'];question=next(iter(reference['questions'].values()))['instructions'];generic=question[question.index('Which menu sense'):];screen=next(x['body'] for x in oldrequests if x['condition']=='screen');rq=next(q for k,q in screen['questions'].items() if k.endswith('_role'));roleprompt=rq['instructions'][rq['instructions'].index('What grammatical use'):];rolecriteria=rq['criteria'];batches=[]
for c in cards.values():
 rr=[x for x in rows if x['card_id']==c['card_id'] and x['id'] not in reused]
 for start in range(0,len(rr),15):
  batch=rr[start:start+15];menu={str(i+1):dict(headword=s['headword'],pos=s['pos'],meaning=s['gloss'],usage=s['usage']) for i,s in enumerate(c['menu'])};state=dict(language='Portuguese',surface=c['surface'],menu=menu,sentences={r['id']:r['marked'] for r in batch});questions={}
  for r in batch:questions[r['id']+'_role']=dict(type='choice',instructions='Evaluate only sentences.'+r['id']+'. '+roleprompt,criteria=rolecriteria)
  body=dict(model='jev-1.13.0',state=state,questions=questions);batches.append(dict(card_id=c['card_id'],ids=[r['id'] for r in batch],role_body=body))
save(OUT/'batches.json',batches);save(OUT/'prompt.json',dict(guide=guide,question=generic))
# Two requests per new batch. Reserve UTF8 bytes for both + two total attempts.
nb=sum(len(json.dumps(x['role_body'],ensure_ascii=False).encode()) for x in batches);newocc=sum(len(x['ids']) for x in batches);planning=nb*4*.042/1e6
oldcost=load(ROOT/'docs/audits/portuguese-verbs-jev-2026-10-23/spend.json');spent=oldcost['estimated_billed_usd']+oldcost['failed_call_reservations_usd'];pre=dict(release_id=REL.name,rank_limit=200,cards=len(cards),excluded_function_cards=[dict(rank=c['rank'],word=c['word'],card_id=c['surface_card_id']) for c in allidx if c not in idx],function_word_policy='same as UI isFunctionWordCard: release function_word or curated pt grammar suite; no linguistic POS-only guess',occurrences=len(rows),distinct_examples=len({(r['card_id'],r['sentence_id']) for r in rows}),reused_occurrences=len(reused),new_occurrences=newocc,new_batches=len(batches),new_role_requests=len(batches),new_sense_requests=len(batches),prior_audit_billed_plus_reserved_usd=spent,estimated_additional_usd=nb/3*2*.042/1e6,planning_additional_reservation_usd=planning,cumulative_limit_usd=1,price_per_million_input=.042,hashes={f:hashlib.sha256((OUT/f).read_bytes()).hexdigest() for f in ['cards.json','rows.json','reused.json','batches.json','prompt.json']})
# Broad planning bound; runner computes exact body reservation at each dependent stage.
assert spent+planning<1,pre
save(OUT/'preflight.json',pre);print(json.dumps({k:v for k,v in pre.items() if k not in ['excluded_function_cards','hashes']},indent=2))
