import json, sys, collections, spacy, warnings; warnings.filterwarnings('ignore')
import os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'src'))
from paths import RESULTS
from spacy.tokens import DocBin
from fluency.reflexive import portuguese as P
nlp = spacy.blank('pt')
items = json.load(open(RESULTS / 'gold-ud-pt.json')); docs = {d.text: d for d in DocBin().from_disk(RESULTS / 'gold-ud-pt-sp.spacy').get_docs(nlp.vocab)}
def gold(i):
    labs = set()
    for f, rel in i['clitics']:
        if f == 'se' and (rel in ('expl:pass', 'expl:impers') or rel.startswith('nsubj')): labs.add('P')
        elif rel.startswith('expl') or (f == 'se' and rel in ('obj', 'iobj')): labs.add('R')
        else: labs.add('O')          # me/te/nos as obj/iobj: reflexive or not is not annotated
    if 'R' in labs: return 'R'
    if 'P' in labs: return 'P'
    if 'O' in labs: return 'O'
    return 'N'
conf = collections.defaultdict(collections.Counter); errs = collections.defaultdict(list); seconj = collections.Counter(); seerr = []
for i in items:
    d = docs[i['text']]; p, why = P.policy(d, tuple(i['span'])); g = gold(i)
    conf[i['tb']][(p, g)] += 1
    if (p == 'NO_SE' and g == 'R') or (p == 'SE_FIRM' and g in ('N', 'P')):
        errs[i['tb']].append((g, p, why, i['surface'], i['text'][:100]))
    if i['prev_se_conj'] is not None:
        t = P.target_token(d, tuple(i['span']))
        cl, _ = P.clitics_of(d, t) if t is not None else ([], None)
        pred_conj = 'se' not in cl
        seconj[(i['prev_se_conj'], pred_conj)] += 1
        if pred_conj != i['prev_se_conj']: seerr.append(('gold-conj' if i['prev_se_conj'] else 'gold-pron', i['surface'], i['text'][:100]))
tot = collections.Counter()
for tb, c in conf.items():
    n = sum(c.values()); dec = sum(v for (p, g), v in c.items() if p in ('NO_SE', 'SE_FIRM'))
    e = len(errs[tb]); both = sum(v for (p, g), v in c.items() if p == 'BOTH')
    sef = {g: v for (p, g), v in c.items() if p == 'SE_FIRM'}; bo = {g: v for (p, g), v in c.items() if p == 'BOTH'}
    print(f"{tb:26s} n={n:5d} decisive={dec/n:.1%} errors={e} prec={(dec-e)/dec:.4f} BOTH={both}  SE_FIRM by gold {sef}  BOTH by gold {bo}")
    tot['n'] += n; tot['dec'] += dec; tot['e'] += e
print(f"ALL n={tot['n']} decisive={tot['dec']/tot['n']:.1%} errors={tot['e']} prec={(tot['dec']-tot['e'])/tot['dec']:.4f}")
ok = seconj[(True, True)] + seconj[(False, False)]
print('se directly before verb — conj/pron decision:', dict(seconj), f'acc={ok/sum(seconj.values()):.4f}')
if len(sys.argv) > 1:
    for tb in errs:
        for x in errs[tb][:int(sys.argv[1])]: print('  ', tb[14:], x)
    for x in seerr[:int(sys.argv[1])]: print('   SE', x)
