"""Sample unseen harvest sentences, excluding ALL previously selected sentences.
Never reads HINGE gold/holdout/census review data. Keeps full attribution.
"""
import hashlib,json,re
from pathlib import Path
from check import ROOT
OUT=ROOT/'docs/audits/function-word-independent'
WS=ROOT.parent/'Fluency-Workspace'
WORDS={'pt':['de','que','se','o','nos','naquele'],'es':['de','que','se','lo','nos','al']}

def normalized(text):return ' '.join(text.casefold().split())
def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def main(output=OUT, words_by_lang=WORDS, additional_exclusions=(), per_word=4):
    OUT=output
    WORDS=words_by_lang
    if (OUT/'sample.json').exists():raise SystemExit('Frozen sample already exists; refusing to resample.')
    pins={};sample=[];counts={}
    existing=set()
    # Also exclude every example ever used in these suites or editorial source pools.
    def texts(x):
        if isinstance(x,dict):
            for k,v in x.items():
                if k in ('sentence','targetHTML','text','target') and isinstance(v,str):existing.add(normalized(re.sub('<[^>]+>','',v)))
                else:texts(v)
        elif isinstance(x,list):
            for v in x:texts(v)
    paths=[ROOT/'docs/audits/function-word-labels/findings.json',ROOT/'docs/audits/function-word-pilot/source-candidates.json',ROOT/'docs/audits/function-word-pilot/source-gap-candidates.json']+[ROOT/f'app/data/grammar-words/{l}.json' for l in WORDS]
    paths += list(additional_exclusions)
    for p in paths:pins[str(p)]=digest(p);texts(json.loads(p.read_text()))
    for lang,words in WORDS.items():
        frozen=WS/'audits/hinge-20261014/inputs/Fluency-Workspace/runs'/lang/'speech'
        run=next(frozen.iterdir());selection=run/'stages/05_example_selection/output/selection.json'
        selected={e['sentence_id'] for c in json.loads(selection.read_text())['cards'] for e in c['selected']}
        bank=WS/'runs'/lang/'speech'/run.name/'stages/03_sentence_harvest/output/sentence-bank.jsonl'
        pins[str(selection)]=digest(selection)
        excluded=set(existing);h=hashlib.sha256()
        for line in bank.open('rb'):
            h.update(line);r=json.loads(line)
            if r['sentence_id'] in selected:excluded.add(normalized(r['target']['text']))
        pins[str(bank)]=h.hexdigest()
        patterns={w:re.compile(r"(?<![\w'’])"+w+r"(?![\w'’])",re.I) for w in words}
        pools={w:[] for w in words};eligible={w:0 for w in words}
        for line in bank.open():
            r=json.loads(line);text=r['target']['text'];english=(r.get('translation') or {}).get('text','')
            if r['sentence_id'] in selected or normalized(text) in excluded or not english or not 4<=len(text.split())<=18:continue
            for w,pattern in patterns.items():
                matches=list(pattern.finditer(text))
                if len(matches)!=1:continue
                eligible[w]+=1
                rank=hashlib.sha256(('independent-20261018|'+lang+'|'+w+'|'+normalized(text)).encode()).hexdigest()
                row=dict(language=lang,word=w,example_id='fresh_'+r['sentence_id'],sentence_id=r['sentence_id'],sentence=text,translation=english,source=r['source'],spans=[[matches[0].start(),matches[0].end()]],sampling_rank=rank)
                pool=pools[w]
                if not any(normalized(q['sentence'])==normalized(text) for q in pool):pool.append(row)
                pool.sort(key=lambda q:q['sampling_rank']);del pool[20:]
        used=set()
        for w in words:
            chosen=[]
            for row in pools[w]:
                if normalized(row['sentence']) in used:continue
                chosen.append(row);used.add(normalized(row['sentence']))
                if len(chosen)==per_word:break
            assert len(chosen)==per_word,(lang,w)
            sample+=chosen
        counts[lang]=eligible
    for p in [ROOT/'research/function_word_audit'/f'syntax_bridge{v}.py' for v in ('_v2','_v3')]:pins[str(p)]=digest(p)
    for p in (ROOT/'research/cascade/trouble-words').glob('*.py'):pins[str(p)]=digest(p)
    OUT.mkdir(exist_ok=True)
    (OUT/'sample.json').write_text(json.dumps(dict(policy=f'{per_word} unique sentences per word; seeded text-hash ranking; 4–18 whitespace tokens; exactly one focus occurrence; all selected sentence IDs/texts and prior suite/pool text excluded.',eligible=counts,input_hashes=pins,rows=sample),ensure_ascii=False,indent=2)+'\n')
    for lang in WORDS:
        suite=json.loads((ROOT/f'app/data/grammar-words/{lang}.json').read_text())
        (OUT/f'{lang}-blind.json').write_text(json.dumps(dict(patterns={w:[{k:r[k] for k in ('tag','formulaHTML','rule','slotTypes')} for r in suite[w]['relations']] for w in WORDS[lang]},rows=[r for r in sample if r['language']==lang]),ensure_ascii=False,indent=2)+'\n')
    print('Frozen',len(sample),'sentences; prior selected/holdout pool excluded without opening holdout.')
if __name__=='__main__':main()
