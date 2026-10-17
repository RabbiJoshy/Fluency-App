"""Build preview only from reviewed structural candidates, using generated spans verbatim."""
import json
from copy import deepcopy
from check import ROOT
from syntax_bridge import OUT

def build():
    rows=json.loads((OUT/'syntax-findings.json').read_text())['rows']
    reviews=json.loads((OUT/'syntax-review.json').read_text())
    byid={r['example_id']:r for r in rows}
    trial={l:json.loads((ROOT/f'docs/audits/function-word-pilot/{l}.proposed.json').read_text()) for l in ('pt','es')}
    raw=json.loads((ROOT/'docs/audits/function-word-pilot/source-candidates.json').read_text())['decks']
    added=0
    for review in reviews:
        row=byid[review['example_id']]
        assert row['status']=='candidate'
        if review['decision']!='accept':continue
        lang,word,p=row['language'],row['word'],row['pattern']
        card=raw[lang][word];ex=next(e for e in card['examples'] if e['example_id']==row['example_id'])
        new=dict(targetHTML=row['targetHTML'],translation=row['translation'],source=ex['metadata']['source']['name'],metadata=deepcopy(ex['metadata']),example_id=ex['example_id'],source_card_id=card['card_id'],syntax_bridge_review=review['reason'])
        rel=trial[lang][word]['relations'][p]
        assert all(e.get('example_id')!=ex['example_id'] for e in rel['examples'])
        rel['examples'].insert(0,new);rel['targetHTML']=new['targetHTML'];rel['translation']=new['translation'];added+=1
    (OUT/'syntax-trial.json').write_text(json.dumps(trial,ensure_ascii=False,indent=2)+'\n')
    lines=['# Additional structural-candidate review','', 'Assistant editorial review, not a blinded accuracy evaluation. Examples are outside the previous 24-example review. No hand-written highlight spans are used for accepted examples.','']
    for review in reviews:
        r=byid[review['example_id']]
        lines += [f"## {r['language']} / {r['word']} — {review['decision']}",r['sentence'],r['translation'],str([(c['slot'],c['text']) for c in r['chunks']]),review['reason'],'']
    (OUT/'syntax-sample-report.md').write_text('\n\n'.join(lines));print(f'{added} reviewed automatic-span additions.')
    return trial
if __name__=='__main__':build()
