import json, sys
from collections import Counter
from fluency.sense_menu.noun_merge import stamp_noun_merge
from fluency.enrichments.card_rules import normal_token
S=sys.argv[1]
cfg=json.load(open('app/config/config.json'))['languages']
src={'portuguese':'../Fluency-Workspace/runs/pt/speech/20261026T150251Z-eb0e1fce/stages/02_sense_menu/output/sense-menu.json',
     'spanish':'../Fluency-Workspace/audits/seam/es-enriched-menu.json'}
for lang,path in src.items():
    cards=json.load(open(path))['cards']; stamp_noun_merge(cards); by={c['card_id']:c for c in cards}
    rows=json.load(open('../Fluency-Workspace/'+cfg[lang]['indexPath']))
    payload=json.load(open('app/'+cfg[lang]['mergeExceptionsPath'])); old=payload['noun_verdicts']
    v={normal_token(r['word']):by[r['surface_card_id']]['noun_merge'] for r in rows if r.get('surface_card_id') in by and 'noun_merge' in by[r['surface_card_id']]}
    for w,o in old.items():
        if o.get('reason') in ('missing_or_rejected_response','fresh_menu_mismatch','fresh_other_entry_or_missing_label'): v[w]=o
    payload['noun_verdicts']=v; payload['noun_merge_rule']='noun-merge/v3'
    json.dump(payload,open(f'{S}/{lang}-nounv3.json','w'),ensure_ascii=False)
