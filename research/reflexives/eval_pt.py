import json, sys, re, collections, spacy, warnings
warnings.filterwarnings('ignore')
import os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'src'))
from paths import GOLD, RESULTS
from spacy.tokens import DocBin
from fluency.reflexive import portuguese as P
nlp = spacy.blank('pt')
W = 'A-Za-zÁÂÃÀÉÊÍÓÔÕÚÜÇáâãàéêíóôõúüç'
def span_of(i):
    if 'span' in i: return tuple(i['span'])
    m = re.search(rf'(?<![{W}]){re.escape(i["surface"])}(?![{W}])', i['text'], re.I)
    return (m.start(), m.end()) if m else (0, 0)
def run(items_path, docs_path, show):
    items = json.load(open(items_path)); docs = {d.text: d for d in DocBin().from_disk(docs_path).get_docs(nlp.vocab)}
    pol = collections.Counter(); errs = []; paths = collections.defaultdict(collections.Counter)
    for i in items:
        d = docs[i['text']]; p, why = P.policy(d, span_of(i)); g = i['gold']
        pol[(p, g)] += 1
        bad = (p == 'NO_SE' and g == 'R') or (p == 'SE_FIRM' and g in ('N', 'Z', 'P'))
        paths[(p, why)]['ERR' if bad else 'ok'] += 1
        if bad: errs.append((g, p, why, i['surface'], i['text'][:110]))
    n = sum(pol.values()); dec = sum(v for (p, g), v in pol.items() if p in ('NO_SE', 'SE_FIRM'))
    both = sum(v for (p, g), v in pol.items() if p == 'BOTH')
    # binary accuracy treating BOTH as 'R' guess
    acc = sum(v for (p, g), v in pol.items() if (p in ('SE_FIRM', 'BOTH')) == (g == 'R')) / n
    print(f"POLICY n={n} decisive={dec} ({dec/n:.1%}) errors={len(errs)} decisive-acc={(dec-len(errs))/max(1,dec):.4f} BOTH={both} ({both/n:.1%})  binary(BOTH->R)={acc:.4f}")
    print('   ', sorted(pol.items()))
    if show:
        for k, v in sorted(paths.items(), key=lambda x: -sum(x[1].values())): print('     ', k, dict(v))
        for e in errs: print('    ', e)
if __name__ == '__main__':
    # usage: eval_pt.py <dev|held|blind2|blind3> [show]
    run(GOLD / f'{sys.argv[1]}-pt.json', RESULTS / f'{sys.argv[1]}-pt-sp.spacy', len(sys.argv) > 2)
