"""v2 hybrid detector."""
import json, os
from fluency.reflexive.spanish_base import (deacc, deacc_keep_n, FORMS, DFORMS, REFL, OBJ, ALLCL, CL_PERS, RESTRUCT_INF, RESTRUCT_GER,
                     target_token)
NONFIN = {'infinitivo', 'gerundio', 'inf'}
def tok_lemma(t):
    sp = t.lemma_.split()[0].lower() if t.lemma_ else t.lower_
    lemmas = {e[0] for e in FORMS.get(t.lower_, [])}
    if not lemmas or sp in lemmas: return sp
    # prefer a restructuring/aux lemma if the form can be one (fue: ir/ser)
    for l in ('haber', 'estar', 'ir', 'poder', 'querer', 'deber', 'tener', 'ser'):
        if l in lemmas: return l
    return sorted(lemmas)[0]
OBJ_CONTROL = {'dejar', 'hacer', 'ver', 'oír', 'oir', 'mandar', 'permitir', 'ayudar', 'enseñar', 'obligar', 'invitar',
               'impedir', 'prohibir', 'ordenar', 'animar', 'forzar', 'escuchar', 'mirar', 'llevar', 'acompañar', 'recordar', 'pedir'}
CAUSATIVE = {'hacer', 'dejar', 'ver', 'oír', 'oir', 'mandar', 'escuchar', 'sentir', 'mirar'}
CL3 = {'le', 'les', 'lo', 'la', 'los', 'las', 'se'}
def host_entries(host, cls):
    out = []
    if cls[0] == 'os':
        cands = [(host, ('infinitivo', 'gerundio', 'inf')), (host + 'd', ('imperativo',))]
        if host == 'i': cands.append(('id', ('imperativo',)))
    elif cls[0] == 'nos':
        cands = [(host, None), (host + 's', ('subjuntivo', 'imperativo'))]
    else:
        cands = [(host, None)]
    for h, allowed in cands:
        for e in DFORMS.get(deacc_keep_n(h), []):
            lemma, mood, tense, p, n = e
            ok = mood in NONFIN or mood == 'imperativo' or (mood == 'subjuntivo' and tense == 'presente' and (p == '3' or (p == '1' and n == 'p')))
            if ok and (allowed is None or mood in allowed):
                out.append(e)
    if not out:
        d = deacc(host)
        if len(d) >= 4 and d.endswith(('ar', 'er', 'ir')) and cls[0] != 'os' or (cls[0] == 'os' and d.endswith(('ar', 'er', 'ir'))):
            out.append((host, 'infinitivo', 'generic', '', ''))
        elif len(d) >= 6 and d.endswith(('ando', 'iendo', 'yendo')) and any(ch in host for ch in 'áéí'):
            out.append((host, 'gerundio', 'generic', '', ''))
    return out
def is_finite_form(w):
    return any(e[1] in ('indicativo', 'subjuntivo', 'condicional') for e in FORMS.get(w, []))
def split_enclitics(word):
    w = word.lower()
    if w in FORMS and is_finite_form(w): return None
    best = None
    def rec(host, cls):
        nonlocal best
        if cls:
            ents = host_entries(host, cls)
            if ents and (best is None or len(cls) > len(best[1])): best = (host, cls, ents)
        if len(cls) == 3: return
        for c in ALLCL:
            if host.endswith(c) and len(host) > len(c) + 1: rec(host[:-len(c)], [c] + cls)
    rec(w, [])
    return best
def verbform(t):
    enc = split_enclitics(t.text)
    if enc:
        moods = {e[1] for e in enc[2]}
        if moods & {'infinitivo', 'inf'}: return 'Inf'
        if 'gerundio' in moods: return 'Ger'
        return 'Imp'
    vf = t.morph.get('VerbForm')
    if vf: return vf[0]
    w = deacc(t.lower_)
    if w.endswith(('ar', 'er', 'ir')): return 'Inf'
    if w.endswith(('ando', 'iendo', 'yendo')): return 'Ger'
    return None
QUOTES = ('"', '“', '”', '«', '»', "'", '‘', '’')
def proclitics(doc, i):
    out = []; j = i - 1
    while j >= 0 and doc[j].text in QUOTES: j -= 1
    while j >= 0 and doc[j].lower_ in ALLCL and doc[j].pos_ in ('PRON', 'DET'):
        out.insert(0, doc[j].lower_); j -= 1
    return out
def own_clitics(doc, t):
    enc = split_enclitics(t.text)
    return (enc[1] if enc else []) + proclitics(doc, t.i)
def find_governor(doc, i, form):
    j = i - 1
    while j >= 0 and (doc[j].text in QUOTES or doc[j].lower_ in ('no', 'ya', 'nunca', 'también', 'siempre', 'aún', 'todavía', 'solo', 'sólo', 'casi', 'más')):
        j -= 1
    if j < 0: return None
    conn = ''
    if form == 'Inf' and doc[j].lower_ in ('a', 'de', 'que'):
        conn = doc[j].lower_; j -= 1
    if j < 0: return None
    g = doc[j]; gl = tok_lemma(g)
    if g.pos_ not in ('VERB', 'AUX'): return None
    ok = (form == 'Inf' and gl in RESTRUCT_INF and conn in (RESTRUCT_INF[gl].split('|') if RESTRUCT_INF[gl] else [''])) \
        or (form == 'Ger' and gl in RESTRUCT_GER and conn == '') or (form == 'Part' and gl == 'haber' and conn == '')
    if not ok: return None
    gf = verbform(g)
    if gf in ('Inf', 'Ger', 'Part'):
        up = find_governor(doc, j, gf)
        return up if up is not None else j
    return j
def pn_set(t):
    """possible (person, number) of a finite token. The paradigm table is authoritative; spaCy only picks among its options."""
    p = t.morph.get('Person'); n = t.morph.get('Number')
    sp = (p[0], n[0] if n else None) if p else None
    table = set()
    lem = tok_lemma(t)
    ents = FORMS.get(t.lower_, [])
    if any(e[0] == lem for e in ents): ents = [e for e in ents if e[0] == lem]
    for lemma, mood, tense, pp, nn in ents:
        if mood in ('indicativo', 'subjuntivo', 'condicional') and pp:
            table.add((pp, 'Sing' if nn == 's' else 'Plur'))
    if table: return table, sp
    return ({sp} if sp else set()), sp

def obj_person(doc, v):
    """person of the object of an object-control verb, or None"""
    cl = own_clitics(doc, v)
    for c in cl:
        if c in CL_PERS: return {CL_PERS[c]}
        if c in ('le', 'lo', 'la'): return {('3', 'Sing')}
        if c in ('les', 'los', 'las'): return {('3', 'Plur')}
    for c in v.children:
        if c.dep_ in ('obj', 'iobj') and c.pos_ in ('NOUN', 'PROPN', 'PRON') and c.lower_ not in ALLCL:
            return {('3', 'Plur' if 'Number=Plur' in str(c.morph) else 'Sing')}
    return None
def controller(doc, t, depth=0):
    """Return (set of (p,n), how) for the subject of verb token t."""
    if depth > 4: return None, 'deep'
    vf = verbform(t)
    if vf == 'Imp':
        enc = split_enclitics(t.text)
        out = set()
        for lemma, mood, tense, p, n in enc[2]:
            if p: out.add((p, 'Sing' if n == 's' else 'Plur'))
        return out, 'imp'
    if vf not in ('Inf', 'Ger', 'Part', None):
        s, spacy_pn = pn_set(t)
        # explicit subject disambiguates 1sg/3sg
        for c in t.children:
            if c.dep_ == 'nsubj':
                if c.lower_ == 'yo': return {('1', 'Sing')}, 'subj-yo'
                if c.lower_ in ('tú', 'vos'): return {('2', 'Sing')}, 'subj-tu'
                if c.lower_ == 'nosotros' or c.lower_ == 'nosotras': return {('1', 'Plur')}, 'subj'
                if c.pos_ in ('NOUN', 'PROPN') or c.lower_ in ('él', 'ella', 'usted', 'ellos', 'ellas', 'ustedes', 'nadie', 'alguien', 'esto', 'eso', 'quien', 'quién'):
                    return {x for x in s if x[0] == '3'} or s, 'subj-3'
        if len({x[0] for x in s}) > 1: return s, 'ambiguous'
        return s, 'fin'
    # nonfinite: aux children first
    for c in t.children:
        if c.dep_.startswith('aux') and verbform(c) not in ('Inf', 'Ger', 'Part'):
            return controller(doc, c, depth + 1)
    # restructuring governor to the left
    gov = find_governor(doc, t.i, vf) if vf in ('Inf', 'Ger', 'Part') else None
    if gov is not None and gov != t.i:
        return controller(doc, doc[gov], depth + 1)
    h = t.head
    if h is t or h.pos_ not in ('VERB', 'AUX'):
        # copula/noun/preposition heads: try one more hop for advcl ('para relajarme')
        if t.dep_ in ('advcl', 'xcomp', 'ccomp', 'obl', 'acl') and h is not t and h.head is not h and h.head.pos_ in ('VERB', 'AUX') and h.pos_ not in ('NOUN',):
            return controller(doc, h.head, depth + 1)
        return None, 'uncontrolled'
    if t.dep_ in ('csubj',) or any(c.dep_ == 'cop' for c in t.children) or tok_lemma(h) == 'ser': return None, 'uncontrolled'
    hl = tok_lemma(h)
    if hl in OBJ_CONTROL:
        op = obj_person(doc, h)
        if op: return op, 'objctl'
    return controller(doc, h, depth + 1)
def se_type(doc, t, setok, lemma_prior=None):
    if setok is not None and setok.dep_ in ('expl:pass', 'expl:impers'): return 'P'
    return 'R'
from fluency.reflexive.paths import DATA
PRIOR = json.load(open(DATA / 'se-prior-es.json'))
ASPECTUAL_SE_LO = {'llevar', 'comer', 'beber', 'tomar', 'quedar', 'guardar', 'creer', 'saber', 'ganar', 'merecer', 'fumar',
                   'gastar', 'pensar', 'imaginar', 'tragar', 'jugar', 'aprender', 'leer', 'callar', 'buscar', 'perder', 'olvidar'}
def policy(doc, span):
    """NO_SE / SE_FIRM / BOTH / Z"""
    lab, why = predict(doc, span)
    if lab == 'Z': return 'Z', why
    if why.startswith('uncontrolled'): return 'BOTH', why
    if lab == 'N':
        if why == 'dative-se':
            t = target_token(doc, span)
            if tok_lemma(t) in ASPECTUAL_SE_LO or (split_enclitics(t.text) and deacc(split_enclitics(t.text)[0])[:-2] in {deacc(x)[:-2] for x in ASPECTUAL_SE_LO}):
                return 'BOTH', 'se-lo-aspectual'
        return 'NO_SE', why
    if why.startswith('uncontrolled'): return 'BOTH', why
    if why != 'se': return 'SE_FIRM', why     # agreeing me/te/nos/os, imperative
    t = target_token(doc, span)
    enc = split_enclitics(t.text)
    if enc and verbform(t) == 'Imp': return 'SE_FIRM', 'imp-se'
    lem = tok_lemma(t) if not enc else None
    if enc:
        h = deacc(enc[0]); lem = next((e[0] for e in enc[2] if e[0]), h)
    # promotions: evidence that rules out passive/impersonal se
    v = t
    if not enc and verbform(t) in ('Inf', 'Ger', 'Part'):
        gov = find_governor(doc, t.i, verbform(t))
        if gov is not None: v = doc[gov]
    def subj_of(x):
        for c in x.children:
            if c.dep_ in ('nsubj', 'nsubj:pass'): return c
        return None
    subj = subj_of(t) or (subj_of(v) if v is not t else None)
    ANIM_PRON = {'él', 'ella', 'ellos', 'ellas', 'usted', 'ustedes', 'nadie', 'alguien', 'quienes', 'uno', 'una'}
    if subj is not None and subj.i < t.i and (subj.lower_ in ANIM_PRON or
            (subj.pos_ == 'PROPN' and not any(c.dep_ == 'det' for c in subj.children) and subj.text[:1].isupper()
             and not any(c.dep_ in ('nmod', 'amod', 'appos', 'flat') for c in subj.children))):
        return 'SE_FIRM', 'animate-subj'
    pr = PRIOR.get(lem, {})
    r, pp = pr.get('R', 0), pr.get('P', 0)
    if r + pp >= 5 and r / (r + pp) >= 0.95: return 'SE_FIRM', 'prior'
    if lab == 'P': return 'BOTH', 'spacy-pass'
    return 'BOTH', 'se-3p'

def predict(doc, span, prior=None):
    t = target_token(doc, span)
    if t is None: return 'Z', 'notok'
    enc = split_enclitics(t.text)
    if t.pos_ not in ('VERB', 'AUX') and not enc:
        # spaCy sometimes mis-tags a verb; rescue when the paradigm knows the form and a clitic or governor is adjacent
        known = t.lower_ in FORMS
        prev = doc[t.i - 1].lower_ if t.i > 0 else ''
        if not (known and (prev in REFL or (verbform(t) in ('Inf', 'Ger') and find_governor(doc, t.i, verbform(t)) is not None))):
            return 'Z', 'pos'
    vf = verbform(t)
    tl = tok_lemma(t)
    # haber with enclitics (habérmelo dicho) or auxiliary with a complement: clitics belong elsewhere
    if enc and deacc(enc[0]) in ('haber', 'habiendo'): return 'N', 'haber-enc'
    if not enc and (t.pos_ == 'AUX' or tl in RESTRUCT_INF or tl in RESTRUCT_GER or tl == 'haber'):
        k = t.i + 1
        while k < len(doc) and doc[k].lower_ in ('no', 'a', 'de', 'que', 'ya'): k += 1
        if k < len(doc) and doc[k].pos_ in ('VERB', 'AUX') and verbform(doc[k]) in ('Inf', 'Ger', 'Part'):
            gov = find_governor(doc, k, verbform(doc[k]))
            if gov is not None and gov <= t.i and not split_enclitics(doc[k].text):
                return 'N', 'climbed-to-complement'
    setok = None
    if enc:
        clitics = enc[1]
    elif vf in ('Inf', 'Ger', 'Part'):
        gov = find_governor(doc, t.i, vf)
        if gov is not None:
            g = doc[gov]; clitics = own_clitics(doc, g)
            pc = [doc[k] for k in range(max(0, gov - 3), gov) if doc[k].lower_ == 'se']
            setok = pc[-1] if pc else None
        else:
            clitics = proclitics(doc, t.i) if vf != 'Part' else []
    else:
        clitics = proclitics(doc, t.i)
        pc = [doc[k] for k in range(max(0, t.i - 3), t.i) if doc[k].lower_ == 'se']
        setok = pc[-1] if pc else None
    refl = [c for c in clitics if c in REFL]
    if not refl: return 'N', 'no-refl-clitic'
    # causative/perception verb with enclitic followed by an infinitive: clitic is its object
    if enc and tl in CAUSATIVE and 'se' not in refl:
        k = t.i + 1
        if k < len(doc) and verbform(doc[k]) == 'Inf': return 'N', 'causative'
    if 'se' in refl:
        idx = clitics.index('se')
        if idx + 1 < len(clitics) and clitics[idx + 1] in ('lo', 'la', 'los', 'las'): return 'N', 'dative-se'
        return se_type(doc, t, setok, prior), 'se'
    ctrl, how = controller(doc, t)
    c = refl[0]; want = CL_PERS[c]
    if not ctrl:
        # uncontrolled nonfinite: defer to spaCy's Reflex mark
        return ('R' if 'Reflex=Yes' in str(t.morph) else 'N'), 'uncontrolled-spacy'
    match = any(p == want[0] and (n is None or n == want[1]) for p, n in ctrl)
    if match and how == 'ambiguous':
        # 1sg/3sg-ambiguous finite form: trust spaCy's reading of the clitic itself
        cl = [d for d in doc[max(0, t.i - 3):t.i] if d.lower_ == c]
        if cl and (cl[-1].dep_ == 'expl:pv' or 'Reflex=Yes' in str(cl[-1].morph)): return 'R', 'amb-spacy-R'
        return 'N', 'amb-spacy-N'
    return ('R' if match else 'N'), how
