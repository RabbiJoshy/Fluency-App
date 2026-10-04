"""Token-level gold from UD Portuguese. For every surface token holding a verb: which clitics hang on it and how.
Also every 'se' token directly before/attached to a verb, labelled conj vs pronoun."""
import json, sys, glob, collections
def sents(path):
    buf = []
    for line in open(path, encoding='utf8'):
        line = line.rstrip('\n')
        if not line:
            if buf: yield buf
            buf = []
        else: buf.append(line)
    if buf: yield buf
RESTR = {'ir','vir','estar','andar','ficar','continuar','começar','voltar','acabar','deixar','ter','haver','poder','dever','querer','conseguir','tentar','saber','costumar','precisar','parar','seguir','chegar','passar'}
items = []
for path in sys.argv[2:]:
    tb = path.split('/')[-2]
    for s in sents(path):
        text = [l[9:] for l in s if l.startswith('# text = ')]
        if not text: continue
        text = text[0]
        rows = [l.split('\t') for l in s if not l.startswith('#')]
        words = {r[0]: r for r in rows if r[0].isdigit()}
        surf = []; skip = set()
        for r in rows:
            if '-' in r[0] and r[0].split('-')[0].isdigit():
                a, b = map(int, r[0].split('-')); ids = [str(i) for i in range(a, b + 1)]
                surf.append((r[1], ids)); skip.update(ids)
            elif r[0].isdigit() and r[0] not in skip:
                surf.append((r[1], [r[0]]))
        pos = 0; spans = []
        for form, ids in surf:
            i = text.find(form, pos)
            spans.append(None if i < 0 else (i, i + len(form)))
            if i >= 0: pos = i + len(form)
        def lexical(h):
            for _ in range(4):
                w = words.get(h)
                if not w or w[2] not in RESTR: return h
                xs = [c for c in words.values() if c[6] == h and c[7] in ('xcomp',) and ('VerbForm=Inf' in c[5] or 'VerbForm=Ger' in c[5] or 'VerbForm=Part' in c[5])]
                if not xs: return h
                h = xs[0][0]
            return h
        kids = collections.defaultdict(list)
        for w in words.values():
            h = w[6]
            if w[3] == 'PRON' and w[1].lower().strip('-') in ('se', 'me', 'te', 'nos', 'vos'): h = lexical(h)
            kids[h].append(w)
        for (form, ids), span in zip(surf, spans):
            if span is None: continue
            verbs = [words[i] for i in ids if words[i][3] in ('VERB', 'AUX')]
            if not verbs: continue
            det = []
            for v in verbs:
                for c in kids.get(v[0], []):
                    f = c[1].lower().strip('-')
                    if c[3] == 'PRON' and f in ('se', 'me', 'te', 'nos', 'vos'): det.append((f, c[7]))
            # conj 'se' immediately before this token
            k = text.rfind(' se ', 0, span[0] + 1)
            prev_se = text[max(0, span[0] - 3):span[0]].lower() == 'se '
            se_conj = None
            if prev_se:
                se_rows = [w for w in words.values() if w[1].lower() == 'se']
                # find the se word whose surface precedes this token
                idx_word = int(ids[0]) - 1
                pw = words.get(str(idx_word))
                if pw and pw[1].lower() == 'se': se_conj = pw[3] == 'SCONJ'
            items.append({'tb': tb, 'text': text, 'span': span, 'surface': form, 'lemma': verbs[-1][2], 'clitics': det, 'prev_se_conj': se_conj})
json.dump(items, open(sys.argv[1], 'w'), ensure_ascii=False)
c = collections.Counter((i['tb'], bool(i['clitics'])) for i in items); print(len(items), c)
print('se before verb:', collections.Counter((i['tb'], i['prev_se_conj']) for i in items if i['prev_se_conj'] is not None))
