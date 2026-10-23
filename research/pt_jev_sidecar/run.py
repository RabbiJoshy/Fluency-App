"""Authorised two-stage Jev; cumulative previous audit + this pass <= $1."""
import json,pathlib,hashlib,urllib.request,urllib.error,concurrent.futures,time,threading,datetime,os
ROOT=pathlib.Path(__file__).resolve().parents[2];OUT=ROOT.parent/'Fluency-Workspace/reviews/pt-first200-jev-v1';RAW=OUT/'responses';RAW.mkdir(exist_ok=True);RATE=.042/1e6
load=lambda p:json.loads(p.read_text());pre=load(OUT/'preflight.json');batches=load(OUT/'batches.json');prompt=load(OUT/'prompt.json');reused=load(OUT/'reused.json');cards={c['card_id']:c for c in load(OUT/'cards.json')};rows={r['id']:r for r in load(OUT/'rows.json')}
for f,h in pre['hashes'].items():assert hashlib.sha256((OUT/f).read_bytes()).hexdigest()==h
key=os.environ.get('TYPESAFE_API_KEY')
if not key:
 for line in (ROOT/'.env').read_text().splitlines():
  k,sep,v=line.partition('=')
  if sep and k.strip().removeprefix('export ').strip()=='TYPESAFE_API_KEY':key=v.strip().strip('"').strip("'")
assert key,'TYPESAFE_API_KEY missing'
lock=threading.Lock();charged=pre['prior_audit_billed_plus_reserved_usd']
for f in RAW.glob('*.json'):
 r=load(f);charged+=r.get('cost_usd',r.get('reservation_usd',0))
print('Preflight:',pre['new_occurrences'],'new occurrences;',pre['estimated_additional_usd'],'estimated additional USD; cumulative ceiling $1',flush=True)
def call(name,body):
 global charged
 digest=hashlib.sha256(json.dumps(body,ensure_ascii=False).encode()).hexdigest()
 for attempt in range(2):
  path=RAW/f'{name}-{attempt}.json'
  if path.exists():
   rec=load(path);assert rec['payload_sha256']==digest
   if rec['status']=='ok':return rec
   continue
  encoded=json.dumps(body,ensure_ascii=False).encode();reservation=len(encoded)*RATE
  with lock:
   assert charged+reservation<=1,('Cumulative budget exhausted',charged,reservation)
   charged+=reservation
  rec=dict(name=name,attempt=attempt,payload_sha256=digest,reservation_usd=reservation,model=body['model'],utc=datetime.datetime.now(datetime.timezone.utc).isoformat());start=time.perf_counter()
  try:
   req=urllib.request.Request('https://api.typesafe.ai/v1/systemone',data=encoded,headers={'Authorization':'Bearer '+key,'Content-Type':'application/json'})
   with urllib.request.urlopen(req,timeout=45) as f:res=json.load(f)
   assert set(res['answers'])==set(body['questions'])
   assert res['model']==body['model']
   for k,a in res['answers'].items():assert a['choice'] in body['questions'][k]['criteria']
   rec.update(status='ok',response=res,cost_usd=res['usage']['input_tokens']*RATE)
   with lock:charged+=rec['cost_usd']-reservation
  except urllib.error.HTTPError as e:rec.update(status='error',http_status=e.code)
  except Exception as e:rec.update(status='error',error_type=type(e).__name__)
  rec['elapsed_s']=time.perf_counter()-start;path.write_text(json.dumps(rec,ensure_ascii=False,indent=1))
  if rec['status']=='ok':return rec
 raise RuntimeError('Jev request failed twice: '+name)
def work(pair):
 ix,b=pair;role=call(f'{ix:03}-role',b['role_body']);state=json.loads(json.dumps(b['role_body']['state']));state['grammar_guide']=prompt['guide'];state['first_pass_role']={i:role['response']['answers'][i+'_role'] for i in b['ids']};criteria={str(i+1):'Sense '+str(i+1)+' in the shared menu.' for i in range(len(cards[b['card_id']]['menu']))};criteria.update(NONE='No supplied sense fits this marked occurrence.',AMBIGUOUS='Several substantially different readings fit and the sentence does not distinguish them.');qs={i:dict(type='choice',instructions='Evaluate only sentences.'+i+'. '+prompt['question'],criteria=criteria) for i in b['ids']};body=dict(model='jev-1.14.0',state=state,questions=qs);(OUT/f'request-{ix:03}-sense.json').write_text(json.dumps(body,ensure_ascii=False,indent=1));rec=call(f'{ix:03}-sense',body);result={}
 for i in b['ids']:
  a=rec['response']['answers'][i];k=a['choice'];sid=cards[b['card_id']]['menu'][int(k)-1]['id'] if k.isdigit() else k;result[i]=dict(source_sense_id=sid,answer=a,model=rec['response']['model'],role=state['first_pass_role'][i],provenance=dict(reused=False,request=rec['name'],payload_sha256=rec['payload_sha256']))
 return result
results=dict(reused)
with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
 for n,res in enumerate(pool.map(work,enumerate(batches)),1):
  results.update(res)
  if n%15==0:print('completed batches',n,'/',len(batches),flush=True)
assert set(results)==set(rows)
(OUT/'decisions.json').write_text(json.dumps(results,ensure_ascii=False,indent=1));calls=[load(f) for f in RAW.glob('*.json')];tokens=sum(x.get('response',{}).get('usage',{}).get('input_tokens',0) for x in calls);failed=sum(x['reservation_usd'] for x in calls if x['status']!='ok');summary=dict(new_requests=len(calls),new_input_tokens=tokens,additional_billed_usd=tokens*RATE,additional_failed_reserved_usd=failed,cumulative_billed_plus_reserved_usd=pre['prior_audit_billed_plus_reserved_usd']+tokens*RATE+failed,previous_decisions_reused=len(reused),occurrences_covered=len(results),limit_usd=1);assert summary['cumulative_billed_plus_reserved_usd']<=1;(OUT/'spend.json').write_text(json.dumps(summary,indent=2));print(json.dumps(summary,indent=2),flush=True)
