"""Audit retained automatic labels against card patterns; never infer accuracy from counts.
Uses pinned release snapshots, not parked gold or holdout data. No parser rerun.
"""
import hashlib,json
from collections import Counter
from copy import deepcopy
from pathlib import Path
from check import ROOT
from traceable import highlighted

PILOT=ROOT/'docs/audits/function-word-pilot'
OUT=ROOT/'docs/audits/function-word-labels'

def candidate(lang,word,label):
    kind,value,rule=(label.get(k) for k in ('kind','value','rule'))
    if not label:return [],'No retained automatic label.'
    if word=='que':
        mapping={'conj_that':0,'relative':1,'than':2}
        if kind=='role' and value in mapping:return [mapping[value]],'Check governing verb, antecedent and comparison span; role alone does not guarantee formula fit.'
    if word=='de':
        if rule in ('verb_frame','pronominal_verb_frame') and str(value).endswith(' de'):return [0],'Check governed verb and exact focus occurrence.'
        if value=='prep':return [0,1],'Too broad: need governor/attachment; may also be an uncovered use.'
    if lang=='pt' and word=='se':
        if value=='conj_if':return [0],'Must separate conditional if from embedded whether.'
        if rule in ('pronominal_verb','se_verb') or value=='reflexive':return [1],'Check reciprocal, passive and reflexive/pronominal distinction.'
    if lang=='es' and word=='se':
        if value in ('impersonal_se','passive_se'):return [1],'Validate passive/impersonal syntax; retained labels contain false positives.'
        if rule in ('pronominal_verb','se_verb') or value=='reflexive':return [0],'Check reciprocal and le-to-se substitution separately.'
    if word=='o' and lang=='pt' and kind=='role':
        if value=='article':return [0],'Confirm following noun; nominalised adjective is not this formula.'
        if value=='object_pron':return [1],'Confirm object and placement.'
    if word=='lo' and lang=='es' and kind=='role':
        if value=='article':return [0],'Confirm adjective construction.'
        if value=='object_pron':return [1],'Confirm object: lo único is a retained-label counterexample.'
    if word=='nos':
        if value=='object_pron':return [0],'Exclude reciprocal/reflexive uses before assigning us/to us.'
        if lang=='pt' and value=='prep':return [1],'Confirm em + os and following masculine plural noun.'
    if word=='naquele' and lang=='pt' and value=='prep':return [0],'Confirm focus occurrence and following noun span.'
    if word=='al' and lang=='es':
        if rule=='temporal_infinitive' or value=='al + infinitive':return [1],'Confirm infinitive and temporal reading.'
        if value=='prep':return [0],'Exclude personal a, rates/per and non-destination uses.'
    return [],'No direct bridge to a displayed pattern; preserve phrase/unit distinction.'

def build():
    data=json.loads((PILOT/'source-candidates.json').read_text())
    chosen=json.loads((PILOT/'source-selections.json').read_text())
    used={x['example_id'] for x in chosen['selections']}
    used_sentences={x['sentence_id'] for x in chosen['selections']}
    review=json.loads((OUT/'sample-review.json').read_text())
    judged={(r['language'],r['word'],r['example_id']):r for r in review}
    rows=[];trial={l:json.loads((PILOT/f'{l}.proposed.json').read_text()) for l in ('pt','es')}
    for lang,words in data['decks'].items():
        for word,card in words.items():
            for ex in card['examples']:
                label=ex.get('metadata',{}).get('function_word') or {}
                patterns,reason=candidate(lang,word,label)
                text=ex.get('target') or ex.get('text') or ex['metadata']['target']['text']
                judgment=judged.get((lang,word,ex['example_id']))
                row=dict(language=lang,word=word,example_id=ex['example_id'],sentence_id=ex['metadata'].get('sentence_id'),sentence=text,translation=ex['english'],automatic_label=label,candidate_patterns=patterns,requirement=reason,already_in_pilot=ex['example_id'] in used,review=judgment,source=ex['metadata'].get('source'))
                rows.append(row)
                if judgment and judgment['decision']=='accept':
                    assert ex['example_id'] not in used and ex['metadata'].get('sentence_id') not in used_sentences
                    assert judgment['pattern'] in patterns
                    html,spans=highlighted(text,judgment['chunks'])
                    entry=trial[lang][word]['relations'][judgment['pattern']]
                    new=dict(targetHTML=html,translation=ex['english'],source=ex['metadata']['source']['name'],metadata=deepcopy(ex['metadata']),example_id=ex['example_id'],source_card_id=card['card_id'],label_bridge_review=judgment['reason'])
                    entry['examples'].insert(0,new);entry['targetHTML']=html;entry['translation']=ex['english']
    assert len(judged)==sum(r['review'] is not None for r in rows)
    return rows,trial

def main():
    rows,trial=build();OUT.mkdir(parents=True,exist_ok=True)
    counts=Counter('ambiguous' if len(r['candidate_patterns'])>1 else 'candidate' if r['candidate_patterns'] else 'unmapped' for r in rows)
    pins={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in [PILOT/'source-candidates.json',PILOT/'source-selections.json',OUT/'sample-review.json',Path(__file__)]}
    (OUT/'findings.json').write_text(json.dumps(dict(input_hashes=pins,counts=counts,rows=rows),ensure_ascii=False,indent=2)+'\n')
    (OUT/'trial.json').write_text(json.dumps(trial,ensure_ascii=False,indent=2)+'\n')
    lines=['# Automatic-label bridge: twelve-word first pass','',f'{len(rows)} retained release examples: '+', '.join(f'{n} {k}' for k,n in counts.items())+'.','',
      'These are adapter routing counts, not accuracy, coverage of the language, or dominance. Releases cap/select examples. The retained labels were not recomputed with today’s draft labeller. No parked HINGE gold/holdout was read or changed.','',
      'The trial adds only explicitly accepted examples absent from the original 71-example selection. Existing examples remain available. Sampling is editorial and deliberately includes counterexamples, not a blinded or representative evaluation. Chunk spans are editorially reviewed by the assistant; the automatic labels alone do not supply them.','',
      '## Pattern mapping and gaps','']
    for lang in ('pt','es'):
        for word in sorted({r['word'] for r in rows if r['language']==lang}):
            for i,p in enumerate(trial[lang][word]['relations']):
                candidates=[r for r in rows if r['language']==lang and r['word']==word and i in r['candidate_patterns']]
                accepted=[r for r in candidates if r['review'] and r['review']['decision']=='accept' and r['review']['pattern']==i]
                lines.append(f'- {lang} / {word} / {i} ({p["tag"]}): {len(candidates)} candidate routes; {len(accepted)} accepted fresh examples. '+('No retained example reaches this pattern; expand the input pool before judging the matcher.' if not candidates else 'Not approved for automatic assignment.'))
    lines += ['','## Reviewed fresh examples','']
    for r in rows:
        if not r['review']:continue
        j=r['review'];lines += [f'### {r["language"]} / {r["word"]}: {j["decision"]}',r['sentence'],r['translation'],f'Label: {r["automatic_label"]}',f'Candidates: {r["candidate_patterns"]}. {j["reason"]}','']
    lines += ['## Recommended next implementation','',
      '1. Recover occurrence-level parse evidence (focus offsets, governor, dependency relation and complement type) rather than guessing from the label or English gloss.',
      '2. Resolve conditional/whether se, reciprocal nos, nominalised lo/o, and destination/personal/rate al before broad automatic assignment.',
      '3. Map classifier outputs to stable pattern identities; keep unmapped and ambiguous outcomes visible. Expand beyond capped release examples for missing patterns.',
      '4. Validate mapping and automatic chunk extraction on a separately sampled development set; keep the existing holdout untouched. Do not promote the trial as an accuracy result.']
    (OUT/'report.md').write_text('\n\n'.join(lines)+'\n')
    print(dict(examples=len(rows),routing=dict(counts),reviewed=sum(bool(r['review']) for r in rows),accepted=sum(bool(r['review'] and r['review']['decision']=='accept') for r in rows)))
if __name__=='__main__':main()
