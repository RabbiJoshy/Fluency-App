"""Spanish reflexive/pronominal detector experiments. Labels: R (pronominal -> Xse), P (passive/impersonal se -> X),
N (no coreferent clitic -> X), Z (not a verb)."""
import json, unicodedata, re, os
from fluency.reflexive.paths import PARADIGMS
def deacc(s):
    return ''.join(c for c in unicodedata.normalize('NFD', s) if unicodedata.category(c) != 'Mn').replace('ñ','ñ')
def deacc_keep_n(s):
    s = s.replace('ñ', '\x00').replace('Ñ', '\x01')
    s = deacc(s)
    return s.replace('\x00', 'ñ').replace('\x01', 'Ñ')
FORMS = json.load(open(PARADIGMS / 'forms-es.json'))
DFORMS = {}
for f, entries in FORMS.items():
    DFORMS.setdefault(deacc_keep_n(f), []).extend(entries)
REFL = ('me', 'te', 'se', 'nos', 'os')
OBJ = ('lo', 'la', 'los', 'las', 'le', 'les')
ALLCL = REFL + OBJ
CL_PERS = {'me': ('1', 'Sing'), 'te': ('2', 'Sing'), 'nos': ('1', 'Plur'), 'os': ('2', 'Plur')}
NONFIN_MOODS = {'infinitivo', 'gerundio', 'imperativo', 'inf'}
def host_entries(host, cls):
    cands = [host]
    if cls and cls[0] == 'nos': cands.append(host + 's')   # vámonos, sentémonos
    if cls and cls[0] == 'os': cands.append(host + 'd')    # sentaos, idos
    out = []
    for h in cands:
        for e in DFORMS.get(deacc_keep_n(h), []):
            lemma, mood, tense, p, n = e
            if mood in NONFIN_MOODS or (mood == 'subjuntivo' and tense == 'presente' and p in ('1', '3')):
                out.append(e)
    return out
def is_finite_form(w):
    return any(e[1] in ('indicativo', 'subjuntivo', 'condicional') for e in FORMS.get(w, []))
def split_enclitics(word):
    """Return (host, [clitics], host_entries) for the longest valid enclitic parse, else None."""
    w = word.lower()
    if w in FORMS and is_finite_form(w):
        return None
    best = None
    def rec(host, cls):
        nonlocal best
        if cls:
            ents = host_entries(host, cls)
            if ents and (best is None or len(cls) > len(best[1])):
                best = (host, cls, ents)
        if len(cls) == 3: return
        for c in ALLCL:
            if host.endswith(c) and len(host) > len(c) + 1:
                rec(host[:-len(c)], [c] + cls)
    rec(w, [])
    return best
# restructuring (clitic-climbing) governors: lemma -> required connector ('' = none)
RESTRUCT_INF = {'poder': '', 'querer': '', 'deber': '', 'soler': '', 'saber': '', 'necesitar': '', 'intentar': '',
    'pensar': '', 'esperar': '', 'preferir': '', 'desear': '', 'lograr': '', 'conseguir': '', 'ir': 'a', 'tener': 'que',
    'haber': 'de|que', 'acabar': 'de', 'empezar': 'a', 'comenzar': 'a', 'volver': 'a', 'dejar': 'de', 'tratar': 'de',
    'terminar': 'de', 'parar': 'de', 'llegar': 'a', 'venir': 'a'}
RESTRUCT_GER = {'estar', 'seguir', 'andar', 'venir', 'llevar', 'ir', 'continuar', 'quedar'}
HABER_AUX = {'haber'}
def tok_lemma(t):
    return t.lemma_.split()[0].lower() if t.lemma_ else t.lower_
def verbform(t, ent_host=None):
    vf = t.morph.get('VerbForm')
    if vf: return vf[0]
    w = t.lower_
    if w.endswith(('ar', 'er', 'ir', 'ír')): return 'Inf'
    if deacc(w).endswith(('ando', 'iendo', 'yendo')): return 'Ger'
    return None
def proclitics(doc, i):
    out = []; j = i - 1
    while j >= 0 and doc[j].lower_ in ALLCL and doc[j].pos_ in ('PRON', 'DET') :
        out.insert(0, doc[j].lower_); j -= 1
    return out, j + 1
def find_governor(doc, i, form):
    """Walk left from a nonfinite target to the restructuring/aux governor chain. Returns index of top governor or None."""
    j = i - 1
    while j >= 0 and doc[j].pos_ == 'ADV' and doc[j].lower_ in ('no', 'ya', 'nunca', 'también', 'siempre', 'aún', 'todavía', 'solo', 'sólo'):
        j -= 1
    if j < 0: return None
    conn = ''
    if form == 'Inf' and doc[j].lower_ in ('a', 'de', 'que'):
        conn = doc[j].lower_; j -= 1
    if j < 0: return None
    g = doc[j]; gl = tok_lemma(g)
    if g.pos_ not in ('VERB', 'AUX'): return None
    ok = False
    if form == 'Inf' and gl in RESTRUCT_INF and conn in RESTRUCT_INF[gl].split('|') + ([''] if RESTRUCT_INF[gl] == '' else []):
        ok = True
    if form == 'Ger' and gl in RESTRUCT_GER and conn == '':
        ok = True
    if form == 'Part' and gl in HABER_AUX and conn == '':
        ok = True
    if not ok: return None
    gform = verbform(g)
    if gform in ('Inf', 'Ger', 'Part'):
        up = find_governor(doc, j, gform)
        return up if up is not None else j
    return j
def person_number(t):
    p = t.morph.get('Person'); n = t.morph.get('Number')
    return (p[0] if p else None, n[0] if n else None)
def host_person(ents):
    """For imperative hosts: set of (person, number)"""
    out = set()
    for lemma, mood, tense, p, n in ents:
        if mood in ('imperativo', 'subjuntivo') and p:
            out.add((p, 'Sing' if n == 's' else 'Plur'))
    return out
def target_token(doc, span):
    for t in doc:
        if t.idx <= span[0] < t.idx + len(t.text): return t
    return None
def predict_rules(doc, span, use_spacy_fallback=True, se_rule='spacy'):
    t = target_token(doc, span)
    if t is None: return 'Z', 'notok'
    if t.pos_ not in ('VERB', 'AUX'):
        enc = split_enclitics(t.text)
        if not enc: return 'Z', 'pos'
    i = t.i
    enc = split_enclitics(t.text)
    form = verbform(t)
    clitics = []; ctrl = None; ctrl_tok = None; why = []
    if enc:
        host, cls, ents = enc
        clitics = cls
        moods = {e[1] for e in ents}
        if 'imperativo' in moods or ('subjuntivo' in moods and not moods & {'infinitivo', 'gerundio', 'inf'}):
            ctrl = host_person(ents); why.append('imp')
        else:
            form = 'Inf' if moods & {'infinitivo', 'inf'} else 'Ger'
    else:
        # AUX/restructuring target followed by its complement: clitics climbed to it belong to the complement
        if t.pos_ == 'AUX' or tok_lemma(t) in RESTRUCT_INF or tok_lemma(t) in RESTRUCT_GER:
            k = i + 1
            while k < len(doc) and doc[k].lower_ in ('no', 'a', 'de', 'que', 'ya'): k += 1
            if k < len(doc) and doc[k].pos_ in ('VERB', 'AUX') and verbform(doc[k]) in ('Inf', 'Ger', 'Part'):
                comp = doc[k]; gov = find_governor(doc, k, verbform(comp))
                if gov is not None and gov <= i and not split_enclitics(comp.text):
                    return 'N', 'climbed-to-complement'
        if form in ('Inf', 'Ger', 'Part'):
            gov = find_governor(doc, i, form)
            if gov is not None:
                clitics, _ = proclitics(doc, gov); ctrl_tok = doc[gov]
                genc = split_enclitics(doc[gov].text)
                if genc: clitics = genc[1]
                why.append('climb')
            else:
                clitics, _ = proclitics(doc, i)
                if form == 'Part': clitics = []  # participle without haber: adjectival/passive
        else:
            clitics, _ = proclitics(doc, i)
            ctrl_tok = t
    refl = [c for c in clitics if c in REFL]
    if not refl: return 'N', 'no-refl-clitic'
    # controller person/number
    if ctrl is None:
        if ctrl_tok is not None and verbform(ctrl_tok) not in ('Inf', 'Ger', 'Part'):
            pn = person_number(ctrl_tok)
            ctrl = {pn} if pn[0] else None
        elif enc or form in ('Inf', 'Ger'):
            # nonfinite with enclitic and no restructuring governor: find a finite controller up the tree or among aux children
            base = ctrl_tok if ctrl_tok is not None else t
            auxes = [c for c in base.children if c.dep_.startswith('aux') and verbform(c) not in ('Inf', 'Ger', 'Part')]
            if auxes:
                ctrl = {person_number(auxes[0])}
            else:
                h = base; hops = 0
                while h.head is not h and hops < 3 and h.dep_ in ('xcomp', 'ccomp', 'advcl', 'conj', 'obj', 'csubj'):
                    h = h.head; hops += 1
                    if h.pos_ in ('VERB', 'AUX') and verbform(h) not in ('Inf', 'Ger', 'Part'):
                        ctrl = {person_number(h)}
                        # object control: matrix verb carries a clitic of the same person
                        mcl, _ = proclitics(doc, h.i)
                        menc = split_enclitics(h.text)
                        if menc: mcl = mcl + menc[1]
                        for c in refl:
                            if c in mcl and c != 'se': ctrl = ctrl | {CL_PERS[c]}; why.append('objctl')
                        break
    for c in refl:
        if c == 'se':
            idx = clitics.index('se')
            if idx + 1 < len(clitics) and clitics[idx + 1] in ('lo', 'la', 'los', 'las'):
                return 'N', 'dative-se'
            # passive / impersonal?
            setok = None
            if not enc:
                start = (ctrl_tok.i if ctrl_tok is not None else i)
                for k in range(start - 1, max(-1, start - 4), -1):
                    if doc[k].lower_ == 'se': setok = doc[k]; break
            if se_rule == 'spacy' and setok is not None and setok.dep_ in ('expl:pass', 'expl:impers'):
                return 'P', 'se-pass'
            return 'R', 'se'
    for c in refl:
        want = CL_PERS[c]
        if ctrl is None:
            if use_spacy_fallback:
                return ('R' if 'Reflex=Yes' in str(t.morph) or any(ch.lower_ == c and 'Reflex=Yes' in str(ch.morph) for ch in t.children) else 'N'), 'fallback-spacy'
            return 'N', 'no-ctrl'
        for p, n in ctrl:
            if p == want[0] and (n is None or n == want[1]):
                return 'R', 'agree:' + ','.join(why)
            if c == 'te' and p == '2' and n is None: return 'R', 'agree'
    return 'N', 'disagree'
def predict_spacy_raw(doc, span):
    t = target_token(doc, span)
    if t is None: return 'Z', ''
    if t.pos_ not in ('VERB', 'AUX'): return 'Z', 'pos'
    if 'Reflex=Yes' in str(t.morph): return 'R', 'merged'
    lab = 'N'
    for c in t.children:
        if c.lower_ in REFL and c.pos_ == 'PRON':
            if c.dep_ in ('expl:pass', 'expl:impers'): lab = 'P' if lab == 'N' else lab
            elif c.dep_ == 'expl:pv' or 'Reflex=Yes' in str(c.morph): return 'R', c.dep_
    return lab, ''
