"""Assemble release-pinned UI overlay, preserving source/DeepSeek artifacts and IDs."""
import json,pathlib,collections,copy,hashlib,datetime,re
ROOT=pathlib.Path(__file__).resolve().parents[2];OUT=ROOT.parent/'Fluency-Workspace/reviews/pt-first200-jev-v1';REL=ROOT/'dist/pt-finite-staging/pt/speech/pt-speech-v25-literal-ground-r4-10000x30-fw1-deepseek-v25-finite-v1-slim';DEST=ROOT/'app/data/wsd-sidecars/pt-first200-jev-v1.json'
load=lambda p:json.loads(p.read_text());cards=load(OUT/'cards.json');rows=load(OUT/'rows.json');decisions=load(OUT/'decisions.json');pre=load(OUT/'preflight.json');spend=load(OUT/'spend.json');manifest=load(REL/'app/vocabulary.examples.manifest.json')
def sid(m):return m.get('source_sense_id') or m.get('source_reference','').removeprefix('kaikki-senseid:').removeprefix('kaikki:')
asset=dict(schema='wsd-ui-sidecar/v1',sidecar_id='pt-first200-jev-v1',release_id=pre['release_id'],language='pt',rank_limit=200,method='full-menu-occurrence-grammar-guide-with-advisory-role/v1',frequency_basis='exported-example-share',example_format=manifest['example_format'],sources=manifest['sources'],provenance=dict(model='jev-1.14.0',method='full-menu-occurrence-grammar-guide-with-advisory-role/v1',precedence='Jev UI sidecar > published DeepSeek > original WSD',frequency_basis='exported-example-share',frequency_note='These shares describe the existing selected examples only, not an independently estimated corpus sense distribution.',function_word_policy=pre['function_word_policy'],reused_decisions=pre['reused_occurrences'],new_decisions=pre['new_occurrences'],source_hashes=pre['hashes'],spend=spend,underlying_release_changed=False,unresolved_policy='Explicit unassigned bucket; no forced dictionary sense. Multiple marked occurrences disagreeing are unresolved.'),cards={},card_ids={})
stats=collections.Counter();cardstats=[]
for c in sorted(cards,key=lambda c:c['rank']):
 assert c['surface']!='foram'
 rr=[r for r in rows if r['card_id']==c['card_id']];groups=collections.defaultdict(list)
 for r in rr:groups[r['sentence_id']].append(r)
 meanings=copy.deepcopy(c['row']['meanings']);before_ids=[m['sense_id'] for m in meanings];mapping={sid(m):i for i,m in enumerate(meanings)};unused={sid(m):m for m in c['row'].get('unused_menu_senses',[])};menumap={s['id']:s for s in c['menu']};buckets=[[] for m in meanings];unresolved=None;counts=collections.Counter();nchanged=0
 for sentence_id,occur in groups.items():
  ds=[decisions[r['id']] for r in occur];picks={d['source_sense_id'] for d in ds};statuses={'NONE':'missing_sense','AMBIGUOUS':'ambiguous'}
  if any(r['span'] is None for r in occur):status='target_missing';choice=None
  elif len(picks)!=1:status='multiple_occurrences_disagree';choice=None
  else:
   choice=next(iter(picks));status=statuses.get(choice,'assigned')
   if status!='assigned':choice=None
  previous=occur[0]['previous_sense_id'];e=copy.deepcopy(occur[0]['record']);e['a']='jev-1.14.0-ui-sidecar';e['ju']=dict(sidecar_id='pt-first200-jev-v1',status=status,model='jev-1.14.0',source_sense_id=choice,previous_source_sense_id=previous,confidence=min(d['answer'].get('confidence',0) for d in ds),decision_ids=[r['id'] for r in occur],provenance=[d['provenance'] for d in ds])
  e['ju']['previous_wsd_evidence']=e.get('w')
  e['w']=['leaf',0] if status=='assigned' else []
  if status=='assigned':
   assert choice in menumap
   if choice not in mapping:
    if choice in unused:m=copy.deepcopy(unused[choice])
    else:
     s=menumap[choice];m=dict(sense_id='sense_'+hashlib.md5((c['card_id']+'\0'+choice).encode()).hexdigest(),source_sense_id=choice,source_reference='kaikki:'+choice if not choice.startswith('mwe:') else choice,source='wiktionary',headword=s['headword'],pos=s['pos'],translation=s['gloss'],context=s['usage'],metadata={'wsd_ui':{'appended_source_sense':True}})
    m.pop('unassigned',None);m['assignment_method']='jev-1.14.0-ui-sidecar';m['source_sense_id']=choice;mapping[choice]=len(meanings);meanings.append(m);buckets.append([]);stats['appended_senses']+=1
   mi=mapping[choice]
  else:
   if unresolved is None:
    unresolved=len(meanings);meanings.append(dict(sense_id='ui_jev_unresolved_'+c['short'],source_sense_id='ui:jev-unresolved:'+c['card_id'],source='jev-ui-sidecar',source_reference='ui:jev-unresolved:'+c['card_id'],pos='UNASSIGNED',translation='Meaning unresolved',headword=c['surface'],unassigned=True,assignment_method='unassigned'));buckets.append([])
   mi=unresolved
  buckets[mi].append(e);counts[status]+=1;stats[status]+=1
  if choice!=previous:nchanged+=1
 for i,m in enumerate(meanings):
  m['_masterSenseIndex']=i;m.setdefault('source_sense_id',sid(m));m['frequency']=f'{len(buckets[i])/len(groups):.9f}';m['display_frequency']=m['frequency'];m['assignment_method']='unassigned' if m.get('unassigned') else 'jev-1.14.0-ui-sidecar'
  if buckets[i]:
   e=buckets[i][0];spans=[[z.start(),z.end()] for z in re.finditer(r'(?<!\w)'+re.escape(c['surface'])+r'(?!\w)',e['t'],re.I)];m['canonical_example']=dict(text=e['t'],translation=e['e'],bold_text_offsets=spans,bold_translation_offsets=[],literal_meaning='',tags=[],source=e.get('s'),metadata={'sentence_id':'sentence_'+e['i'],'wsd_ui':e['ju']})
  else:m['canonical_example']=None
 assert [m['sense_id'] for m in meanings[:len(before_ids)]]==before_ids
 assert collections.Counter(e['i'] for b in buckets for e in b)==collections.Counter(r['record']['i'] for r in {r['sentence_id']:r for r in rr}.values())
 distribution=dict(considered=len(groups),assigned=counts['assigned'],unassigned=len(groups)-counts['assigned'],frequency_basis='exported-example-share',method='jev-ui-sidecar/v1')
 asset['card_ids'][c['short']]=c['card_id']
 asset['cards'][c['card_id']]=dict(short_id=c['short'],word=c['surface'],rank=c['rank'],meanings=meanings,examples={'m':buckets},wsd_distribution=distribution,counts=dict(counts),frequency_basis='exported-example-share',previous_example_count=len(groups),changed_example_count=nchanged)
 stats['examples']+=len(groups);stats['changed_vs_published']+=nchanged;cardstats.append(dict(card_id=c['card_id'],word=c['surface'],rank=c['rank'],examples=len(groups),changed=nchanged,**counts))
asset['provenance']['coverage']=dict(cards=len(cards),occurrences=len(rows),**stats);DEST.write_text(json.dumps(asset,ensure_ascii=False,separators=(',',':')));summary=dict(path=str(DEST),bytes=DEST.stat().st_size,sha256=hashlib.sha256(DEST.read_bytes()).hexdigest(),cards=len(cards),**stats)
(OUT/'build-summary.json').write_text(json.dumps(summary,indent=2));(OUT/'card-summary.json').write_text(json.dumps(cardstats,ensure_ascii=False,indent=1));print(json.dumps(summary,indent=2))
