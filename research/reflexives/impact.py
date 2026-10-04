"""Apply the policy to live v22 pair-card assignments and count what a hard filter would change."""
import json, sys, random, re, collections, spacy, warnings
warnings.filterwarnings('ignore')
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'src'))
from paths import RESULTS
# usage: impact.py <es|pt> <sample size, 0 = all>; needs results/<lang>-pair-assignments.json and <lang>-sent.json
lang, n_sample = sys.argv[1], int(sys.argv[2]); S = RESULTS
if lang == 'es':
    from fluency.reflexive import spanish as M
    rows = json.load(open(f'{S}/es-pair-assignments.json')); sent = json.load(open(f'{S}/es-sent.json'))
    for r in rows: r['sel'] = 'pron' if r['hw'].endswith('se') else 'nonpron'
    model = 'es_dep_news_trf'; W = 'A-Za-záéíóúüñÁÉÍÓÚÜÑ'
else:
    from fluency.reflexive import portuguese as M
    rows = [r for r in json.load(open(f'{S}/pt-pair-assignments.json')) if r['sel'] != 'other']; sent = json.load(open(f'{S}/pt-sent.json'))
    model = 'pt_core_news_lg'; W = 'A-Za-zÁÂÃÀÉÊÍÓÔÕÚÜÇáâãàéêíóôõúüç'
random.seed(5)
if n_sample and n_sample < len(rows): rows = random.sample(rows, n_sample)
nlp = spacy.load(model)
texts = sorted({sent[r['sid']][0] for r in rows})
docs = {d.text: d for d in nlp.pipe(texts, batch_size=64)}
c = collections.Counter(); changes = []
for r in rows:
    t = sent[r['sid']][0]
    m = re.search(rf'(?<![{W}]){re.escape(r["surface"])}(?![{W}])', t, re.I)
    if not m: c['unlocated'] += 1; continue
    p, why = M.policy(docs[t], (m.start(), m.end()))
    c[(r['sel'], p)] += 1
    if (p == 'NO_SE' and r['sel'] == 'pron') or (p == 'SE_FIRM' and r['sel'] == 'nonpron'):
        changes.append({'surface': r['surface'], 'v22': r['sel'], 'policy': p, 'why': why, 'text': t, 'tr': sent[r['sid']][1]})
json.dump({'counts': {str(k): v for k, v in c.items()}, 'changes': changes}, open(f'{S}/impact-{lang}.json', 'w'), ensure_ascii=False, indent=0)
tot = sum(v for k, v in c.items() if k != 'unlocated')
print(lang, 'rows', tot, 'would change', len(changes), f'({len(changes)/tot:.1%})')
for k, v in sorted(c.items(), key=str): print('  ', k, v)
