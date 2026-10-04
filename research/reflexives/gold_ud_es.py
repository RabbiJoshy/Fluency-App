"""Extract token-level reflexive gold from UD conllu.
Each item: text, target surface span (char offsets), gold label R/P/N, lemma, detail."""
import json, sys, re
CL = {'me','te','se','nos','os','vos','lhe','lhes','-me','-te','-se','-nos'}
def sents(path):
    buf=[]
    for line in open(path, encoding='utf8'):
        line=line.rstrip('\n')
        if not line:
            if buf: yield buf
            buf=[]
        else: buf.append(line)
    if buf: yield buf
def extract(path, lang, reflex_feature=True):
    out=[]
    for s in sents(path):
        text=[l[9:] for l in s if l.startswith('# text = ')][0]
        sid=[l.split('= ',1)[1] for l in s if l.startswith('# sent_id')][0]
        rows=[l.split('\t') for l in s if not l.startswith('#')]
        words={r[0]:r for r in rows if r[0].isdigit()}
        # surface tokens
        surf=[]; skip=set()
        for r in rows:
            if '-' in r[0]:
                a,b=map(int,r[0].split('-')); ids=[str(i) for i in range(a,b+1)]
                surf.append((r[1],ids)); skip.update(ids)
            elif r[0].isdigit() and r[0] not in skip:
                surf.append((r[1],[r[0]]))
        # char offsets
        pos=0; spans=[]
        for form,ids in surf:
            i=text.find(form,pos)
            if i<0: spans.append(None); continue
            spans.append((i,i+len(form))); pos=i+len(form)
        RESTR={'poder','querer','deber','soler','saber','necesitar','intentar','pensar','esperar','preferir','desear','lograr','conseguir','ir','tener','haber','acabar','empezar','comenzar','volver','dejar','tratar','terminar','parar','llegar','venir','estar','seguir','andar','llevar','continuar','quedar'}
        def lexical(h):
            # descend restructuring governors to their nonfinite xcomp
            for _ in range(4):
                w=words.get(h)
                if not w or w[2] not in RESTR: return h
                xs=[c for c in words.values() if c[6]==h and c[7]=='xcomp' and ('VerbForm=Inf' in c[5] or 'VerbForm=Ger' in c[5])]
                if not xs: return h
                h=xs[0][0]
            return h
        children={}
        for w in words.values():
            head=w[6]
            if w[1].lower().lstrip('-') in ('me','te','se','nos','os') and w[3]=='PRON':
                head=lexical(head)
            children.setdefault(head,[]).append(w)
        for (form,ids),span in zip(surf,spans):
            if span is None: continue
            verbs=[words[i] for i in ids if words[i][3] in ('VERB','AUX')]
            if not verbs: continue
            label='N'; det=[]
            for v in verbs:
                for c in children.get(v[0],[]):
                    f=c[1].lower().lstrip('-')
                    if c[3]!='PRON' or f not in {'me','te','se','nos','os','vos'}: continue
                    rel=c[7]
                    if rel in ('expl:pass','expl:impers'):
                        lab='P'
                    elif rel.startswith('expl') or (reflex_feature and 'Reflex=Yes' in c[5]):
                        lab='R'
                    else: lab='N'
                    det.append(f'{f}:{rel}:{lab}')
                    if lab=='R' or (lab=='P' and label=='N'): label=lab
            out.append({'id':f'{sid}:{span[0]}','text':text,'span':span,'surface':text[span[0]:span[1]],'lemma':verbs[-1][2],'upos':verbs[-1][3],'gold':label,'detail':det})
    return out
if __name__=='__main__':
    lang, outp = sys.argv[1], sys.argv[2]
    items=[]
    for p in sys.argv[3:]: items+=extract(p, lang)
    json.dump(items, open(outp,'w'), ensure_ascii=False)
    import collections; print(len(items), collections.Counter(i['gold'] for i in items))
