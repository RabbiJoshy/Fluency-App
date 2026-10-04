import json, sys, collections, spacy, warnings
warnings.filterwarnings('ignore')
import os; HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(HERE, '..', '..', 'src'))
from spacy.tokens import DocBin
from fluency.reflexive import spanish_base as R
from paths import GOLD, RESULTS
P = os.environ.get('REFL_PARSER', 'trf')
from fluency.wsd.languages.spanish import se_reflexive_evidence
nlp = spacy.blank('es')
def load(items_path, docs_path):
    items = json.load(open(items_path))
    docs = {d.text: d for d in DocBin().from_disk(docs_path).get_docs(nlp.vocab)}
    return items, docs
def span_of(i):
    if 'span' in i: return tuple(i['span'])
    k = i['text'].find(i['surface'])
    import re
    m = re.search(r'(?<![\wáéíóúñü])' + re.escape(i['surface']) + r'(?![\wáéíóúñü])', i['text'], re.I)
    return (m.start(), m.end()) if m else (k, k + len(i['surface']))
def current(i):
    ev = se_reflexive_evidence(i['surface'], i['text'])
    return 'R' if ev is True else ('N' if ev is False else '?')
def score(name, items, docs, fn, show=0, filt=None):
    conf = collections.Counter(); errs = []
    for i in items:
        if filt and not filt(i): continue
        g = i['gold']; p, why = fn(i, docs[i['text']])
        gb = g == 'R'; pb = p == 'R'
        conf[(gb, pb)] += 1
        if gb != pb: errs.append((g, p, why, i['surface'], i['text'][:120]))
    tp, fn_, fp, tn = conf[(True, True)], conf[(True, False)], conf[(False, True)], conf[(False, False)]
    n = tp + fn_ + fp + tn
    print(f"{name:28s} n={n:5d} acc={(tp+tn)/n:.4f}  R-prec={tp/max(1,tp+fp):.3f} R-rec={tp/max(1,tp+fn_):.3f}  FP={fp} FN={fn_}")
    for e in errs[:show]: print('    ', e)
    return errs
if __name__ == '__main__':
    which = sys.argv[1]
    show = int(sys.argv[2]) if len(sys.argv) > 2 else 0
    if which == 'held':
        items, docs = load(GOLD / 'held-es.json', RESULTS / f'held-es-{P}.spacy')
    elif which == 'subs':
        items, docs = load(GOLD / 'subs-es.json', RESULTS / f'subs-es-{P}.spacy')
    else:
        items, docs = load(RESULTS / 'gold-ancora.json', RESULTS / f'ancora-{P}.spacy')
    for i in items: i['span'] = span_of(i)
    score('current-gate (?->N)', items, docs, lambda i, d: (current(i).replace('?', 'N'), ''), 0)
    score('spacy-raw', items, docs, lambda i, d: R.predict_spacy_raw(d, i['span']), show if 'raw' in sys.argv else 0)
    score("rules", items, docs, lambda i, d: R.predict_rules(d, i["span"]), 0)
    from fluency.reflexive import spanish as R2
    score("hybrid-v2", items, docs, lambda i, d: R2.predict(d, i["span"]), 0)
    pol = collections.Counter(); errs = []
    for i in items:
        d = docs[i['text']]; p, why = R2.policy(d, i['span']); g = i['gold']
        pol[(p, g)] += 1
        bad = (p == 'NO_SE' and g == 'R') or (p == 'SE_FIRM' and g in ('N', 'Z', 'P'))
        if bad: errs.append((g, p, why, i['surface'], i['text'][:110]))
    n = sum(pol.values()); dec = sum(v for (p, g), v in pol.items() if p in ('NO_SE', 'SE_FIRM'))
    both = sum(v for (p, g), v in pol.items() if p == 'BOTH')
    print(f"POLICY  n={n} decisive={dec} ({dec/n:.1%}) errors={len(errs)} decisive-acc={(dec-len(errs))/dec:.4f}  BOTH={both} ({both/n:.1%})")
    print('   ', sorted(pol.items()))
    for x in errs[:show]: print('    ', x)
