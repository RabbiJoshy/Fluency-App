"""Portuguese reflexive/pronominal detector. Same label set as Spanish: R / P / N / Z, policy NO_SE / SE_FIRM / BOTH / Z."""
import json, os, re, unicodedata
from fluency.reflexive.paths import PARADIGMS, DATA
FORMS = json.load(open(PARADIGMS / 'forms-pt.json'))
REFL = ('me', 'te', 'se', 'nos', 'vos')
OTHER = ('lhe', 'lhes', 'o', 'a', 'os', 'as', 'lo', 'la', 'los', 'las', 'no', 'na', 'nos', 'mo', 'ma', 'to', 'ta', 'lho', 'lha', 'no-lo')
ALLCL = set(REFL) | set(OTHER)
SKIPCL = ALLCL - {'a', 'o', 'os', 'as'}
CL_PERS = {'me': ('1', 'Sing'), 'te': ('2', 'Sing'), 'nos': ('1', 'Plur'), 'vos': ('2', 'Plur')}
MESO_END = {'ei', 'ás', 'á', 'emos', 'eis', 'ão', 'ia', 'ias', 'íamos', 'íeis', 'iam'}
FIN_MOODS = ('indicativo', 'subjuntivo', 'condicional')
RESTRUCT = {  # lemma -> allowed connectors before the complement ('' none); G = gerund ok; P = participle ok
    'ir': ('', 'G'), 'vir': ('', 'a', 'G'), 'estar': ('a', 'G'), 'andar': ('a', 'G'), 'ficar': ('a', 'G'), 'continuar': ('a', 'G'),
    'começar': ('a',), 'voltar': ('a',), 'acabar': ('de', 'G'), 'deixar': ('de',), 'ter': ('de', 'que', 'P'),
    'haver': ('de', 'P'), 'poder': ('',), 'dever': ('',), 'querer': ('',), 'conseguir': ('',), 'tentar': ('',),
    'saber': ('',), 'costumar': ('',), 'precisar': ('', 'de'), 'parar': ('de',), 'seguir': ('G',), 'pretender': ('',),
    'chegar': ('a',), 'passar': ('a',), 'tornar': ('a',), 'ousar': ('',), 'desejar': ('',), 'esperar': ('',),
}
ATTRACTORS = {'que', 'quem', 'onde', 'quando', 'embora', 'talvez', 'caso', 'não', 'nunca', 'já', 'também', 'só', 'ainda',
              'sempre', 'jamais', 'nem', 'porque', 'enquanto', 'quanto', 'qual', 'quais', 'tudo', 'todos', 'ninguém',
              'alguém', 'cada', 'bem', 'mal', 'logo', 'aqui', 'lá', 'até', 'apenas', 'mesmo', 'assim', 'para', 'de', 'por',
              'sem', 'ao', 'pra', 'eu', 'tu', 'ele', 'ela', 'você', 'nós', 'eles', 'elas', 'vocês', 'gente', 'senhor', 'senhora'}
SE_PRIOR = json.load(open(DATA / 'se-prior-pt.json'))
PRON_CAPABLE = set(json.load(open(DATA / 'pt-pronominal-capable.json')))
ASK_VERBS = {'perguntar', 'saber', 'ver', 'dizer', 'verificar', 'decidir', 'imaginar', 'questionar', 'descobrir', 'checar', 'confirmar'}
def deacc(s):
    return ''.join(c for c in unicodedata.normalize('NFD', s) if unicodedata.category(c) != 'Mn')
def entries(w):
    return FORMS.get(w.lower(), [])
def lemma_entries(t):
    h = host_of(t.text); ents = entries(h); lem = lemma_of(t)
    if any(e[0] == lem for e in ents): ents = [e for e in ents if e[0] == lem]
    return ents
TENSE_RANK = {'presente': 0, 'afirmativo': 0, 'pretérito-perfeito': 1, 'pretérito-imperfeito': 1, 'infinitivo': 1, 'inf': 1,
              'gerúndio': 1, 'particípio': 1, 'futuro-do-presente': 2, 'futuro-do-pretérito': 2, 'futuro': 2,
              'infinitivo-pessoal-presente': 2, 'pretérito-mais-que-perfeito': 5}
def lemma_of(t):
    ents = entries(host_of(t.text))
    ls = {e[0] for e in ents}
    sp = (t.lemma_ or '').lower()
    if not ls or sp in ls: return sp or host_of(t.text)
    for l in ('haver', 'ter', 'estar', 'ir', 'poder', 'querer', 'dever', 'ser'):
        if l in ls: return l
    # prefer the lemma with the most everyday reading (vira: virar present, not ver pluperfect)
    return min(ls, key=lambda l: (min(TENSE_RANK.get(e[2], 3) for e in ents if e[0] == l), l))
def split_token(text):
    """virou-se -> ('virou', ['se']); far-se-á -> ('fará', ['se']); dá-me -> ('dá', ['me'])"""
    parts = text.lower().split('-')
    if len(parts) == 1: return parts[0], []
    host = parts[0]; cls = []
    rest = parts[1:]
    if len(rest) >= 2 and rest[-1] in MESO_END and all(p in ALLCL for p in rest[:-1]):
        return host + rest[-1], rest[:-1]   # mesoclisis: far-se-á -> far + á ; manter-me-ia -> manteria
    if all(p in ALLCL or p in ('lo', 'la', 'los', 'las', 'no', 'na') for p in rest):
        return host, rest
    return text.lower(), []
def host_of(text):
    return split_token(text)[0]
def is_verb(t):
    h, enc = split_token(t.text)
    ents = entries(h)
    if t.pos_ in ('VERB', 'AUX'): return True
    if not ents: return False
    finite = any(e[1] in FIN_MOODS or e[1] in ('imperativo', 'infinitivo', 'inf') for e in ents)
    if finite and any(c in REFL for c in enc): return True
    doc = t.doc
    if finite and t.i > 0 and doc[t.i - 1].lower_ in REFL and '-' not in doc[t.i - 1].text: return True
    return t.pos_ not in ('NOUN', 'ADJ', 'DET', 'PROPN', 'ADP')
def vform(t):
    h = host_of(t.text)
    moods = {(e[1], e[2]) for e in entries(h)}
    vf = t.morph.get('VerbForm')
    if not moods and deacc(h).endswith(('ar', 'er', 'ir', 'ôr', 'or')) and len(h) > 3: return 'Inf'
    if '-' in t.text and any(m[0] in ('inf', 'infinitivo') and m[1] in ('inf', 'infinitivo') for m in moods): return 'Inf'
    if any(m[0] == 'gerúndio' for m in moods) or deacc(h).endswith(('ando', 'endo', 'indo', 'ondo')): return 'Ger'
    if any(m[0] == 'particípio' for m in moods) or (vf and vf[0] == 'Part'): return 'Part'
    fin = any(m[0] in FIN_MOODS for m in moods)
    inf = any(m[0] in ('inf', 'infinitivo') and m[1] in ('inf', 'infinitivo') for m in moods)
    if inf and not fin: return 'Inf'
    if inf and fin:  # chegar: infinitive or future subjunctive
        return 'Inf' if (vf and vf[0] == 'Inf') or not vf else 'Fin'
    if fin: return 'Fin'
    if vf: return {'Fin': 'Fin', 'Inf': 'Inf', 'Ger': 'Ger', 'Part': 'Part'}.get(vf[0], 'Fin')
    if deacc(h).endswith(('ar', 'er', 'ir')): return 'Inf'
    return 'Fin'
QUOTES = ('"', '“', '”', '«', '»', "'", '‘', '’')
def proclitic_seq(doc, i):
    out = []; j = i - 1
    while j >= 0 and doc[j].text in QUOTES: j -= 1
    while j >= 0 and doc[j].lower_ in SKIPCL and '-' not in doc[j].text:
        out.insert(0, (doc[j].lower_, j)); j -= 1
    return out
def se_is_conjunction(doc, k, verb_tok):
    """doc[k] is 'se' directly before verb_tok. Decide 'if' vs pronoun."""
    kk = k - 1
    while kk >= 0 and doc[kk].text in QUOTES: kk -= 1
    prev = doc[kk].lower_ if kk >= 0 else ''
    k_prev = kk
    h = host_of(verb_tok.text)
    es = lemma_entries(verb_tok)
    tenses = {(e[1], e[2]) for e in es}
    if prev == 'se': return False                      # 'se se': second is the pronoun
    if vform(verb_tok) == 'Part' and not (k_prev >= 0 and lemma_of(doc[k_prev]) in ('ter', 'haver')):
        return True                                    # se condenado, se comparados: 'if'
    # a subordinator already opened this clause (Se esse cenário se confirmar; para que o escoamento se tornasse)
    j = k - 1
    while j >= 0 and not doc[j].is_punct and k - j <= 6 and not is_verb(doc[j]):
        if j < k - 1 and doc[j].lower_ in ('se', 'que', 'quando', 'caso', 'embora', 'enquanto', 'porque', 'onde') \
                and any(doc[x].pos_ in ('NOUN', 'PROPN', 'PRON') for x in range(j + 1, k)): return False
        j -= 1
    pers = {e[3] for e in es if e[1] in FIN_MOODS or (e[1] == 'infinitivo' and 'pessoal' in e[2] and h != e[0])}
    if pers and '3' not in pers: return True           # se + perdermos / sentires: only 'if' agrees
    if prev == 'como':                                 # como se + imperfect subjunctive = as if
        return ('subjuntivo', 'pretérito-imperfeito') in tenses
    if ('subjuntivo', 'presente') in tenses and not any(m in tenses for m in (('subjuntivo', 'futuro'), ('subjuntivo', 'pretérito-imperfeito'), ('indicativo', 'presente'))):
        return False                                   # conjunction se never takes the present subjunctive
    prev_lemma = lemma_of(doc[k_prev]) if k_prev >= 0 else ''
    if (k_prev >= 0 and doc[k_prev].pos_ in ('VERB', 'AUX') and prev_lemma in ASK_VERBS) or prev in ('ver', 'saber', 'perguntar'): return True
    subjish = any(m in tenses for m in (('subjuntivo', 'futuro'), ('subjuntivo', 'pretérito-imperfeito')))
    inf_too = any(e[1] in ('inf', 'infinitivo') for e in es)
    if inf_too and k_prev >= 0 and (is_verb(doc[k_prev]) or doc[k_prev].pos_ == 'ADP' or prev in ('para', 'de', 'a', 'sem', 'por', 'ao', 'pra', 'até', 'em', 'com', 'após', 'antes', 'depois', 'pelo', 'pela', 'no', 'na')):
        return False
    if inf_too and subjish and prev not in ATTRACTORS:
        has_obj = any(ch.dep_ == 'obj' and ch.pos_ in ('NOUN', 'PROPN') and ch.i > verb_tok.i for ch in verb_tok.children)
        if not has_obj and lemma_of(verb_tok) in PRON_CAPABLE and lemma_of(verb_tok) not in ('ser', 'estar', 'ter', 'haver', 'poder', 'querer', 'ir', 'dar', 'fazer', 'vir'):
            return False
    SUBORD = {'que', 'quem', 'onde', 'quando', 'embora', 'caso', 'enquanto', 'porque', 'qual', 'quais', 'quanto', 'talvez', 'não', 'nunca', 'jamais', 'nem', 'se', 'como'}
    if subjish and not inf_too and prev not in SUBORD: return True
    if subjish and prev not in ATTRACTORS: return True
    if lemma_of(verb_tok) in ('ser', 'estar', 'ter', 'haver', 'poder', 'querer') and prev not in ATTRACTORS:
        return True
    # spaCy as tie-breaker
    return doc[k].pos_ == 'SCONJ' and doc[k].dep_ == 'mark' and prev not in ATTRACTORS and subjish
def find_governor(doc, i, form, chain=None):
    """walk left from a nonfinite complement to its restructuring governor chain; returns top index (chain appended)"""
    j = i - 1
    while j >= 0 and (doc[j].text in QUOTES or (doc[j].lower_ in SKIPCL and '-' not in doc[j].text)): j -= 1
    while j >= 0 and (doc[j].pos_ == 'ADV' or doc[j].lower_ in ('não', 'já', 'nunca', 'mais', 'sempre', 'também', 'só', 'sequer')): j -= 1
    if j < 0: return None
    conn = ''
    if doc[j].lower_ in ('a', 'de', 'que'): conn = doc[j].lower_; j -= 1
    while j >= 0 and (doc[j].text in QUOTES or (doc[j].lower_ in SKIPCL and '-' not in doc[j].text) or doc[j].pos_ == 'ADV' or doc[j].lower_ in ('já', 'ainda', 'sempre', 'não', 'sequer')): j -= 1
    if j < 0: return None
    g = doc[j]; gl = lemma_of(g)
    if gl not in RESTRUCT: return None
    allowed = RESTRUCT[gl]
    ok = (form == 'Inf' and conn in allowed) or (form == 'Ger' and conn == '' and 'G' in allowed) or (form == 'Part' and conn == '' and 'P' in allowed)
    if not ok: return None
    if chain is not None: chain.append(j)
    gf = vform(g)
    if gf in ('Inf', 'Ger', 'Part'):
        up = find_governor(doc, j, gf, chain)
        return up if up is not None else j
    return j
def clitics_of(doc, t):
    """reflexive-relevant clitics for verb token t -> (clitics, controller token index or None)"""
    host, enc = split_token(t.text)
    if enc: return enc, t.i
    seq = proclitic_seq(doc, t.i)
    if seq and seq[-1][0] == 'se' and se_is_conjunction(doc, seq[-1][1], t): seq = seq[:-1]
    elif seq and seq[0][0] == 'se' and len(seq) > 1 and se_is_conjunction(doc, seq[0][1], t): seq = seq[1:]
    vf = vform(t)
    chain = []
    gov = find_governor(doc, t.i, vf, chain) if vf in ('Inf', 'Ger', 'Part') else None
    if seq:
        return [c for c, j in seq], (gov if gov is not None else t.i)
    if gov is not None:
        cls = []
        for x in chain:                      # enclitics on any link: devia ter-me matado, vai-se aproximando
            cls += split_token(doc[x].text)[1]
            cls += [doc[y].lower_ for y in range(x + 1, t.i) if doc[y].lower_ in SKIPCL and '-' not in doc[y].text and y not in chain]
        top = proclitic_seq(doc, gov)
        if top and top[-1][0] == 'se' and se_is_conjunction(doc, top[-1][1], doc[gov]): top = top[:-1]
        cls = [c for c, j in top] + cls
        return cls, gov
    return [], None
def target_token(doc, span):
    for t in doc:
        if t.idx <= span[0] < t.idx + len(t.text): return t
    return None
def pn_options(t):
    h = host_of(t.text); out = set()
    ents = entries(h); lem = lemma_of(t)
    if any(e[0] == lem for e in ents): ents = [e for e in ents if e[0] == lem]
    for lemma, mood, tense, p, n in ents:
        if mood in FIN_MOODS or (mood == 'infinitivo' and 'pessoal' in tense):
            if p: out.add((p, 'Sing' if n == 's' else 'Plur'))
    if not out:
        p = t.morph.get('Person'); n = t.morph.get('Number')
        if p: out.add((p[0], n[0] if n else None))
    return out
def imperative_persons(t):
    """tu-imperative = 3sg pres ind form; você = 3sg pres subj; vocês = 3pl pres subj; nós = 1pl pres subj"""
    h = host_of(t.text); out = set()
    for lemma, mood, tense, p, n in lemma_entries(t):
        if mood == 'indicativo' and tense == 'presente' and p == '3' and n == 's': out.add(('2', 'Sing'))
        if mood == 'subjuntivo' and tense == 'presente' and p == '3': out.add(('3', 'Sing' if n == 's' else 'Plur'))
        if mood == 'subjuntivo' and tense == 'presente' and p == '1' and n == 'p': out.add(('1', 'Plur'))
    return out
SUBJ_P = {'eu': ('1', 'Sing'), 'tu': ('2', 'Sing'), 'nós': ('1', 'Plur'), 'vós': ('2', 'Plur'), 'você': ('3', 'Sing'),
          'ele': ('3', 'Sing'), 'ela': ('3', 'Sing'), 'eles': ('3', 'Plur'), 'elas': ('3', 'Plur'), 'vocês': ('3', 'Plur')}
def controller(doc, t, carrier, depth=0):
    if depth > 4: return None, 'deep'
    c = doc[carrier] if carrier is not None else t
    vf = vform(c)
    if vf == 'Fin' or (vf == 'Inf' and c.lower_ != host_of(c.text) and False):
        opts = pn_options(c)
        # explicit subject pronoun to the left
        for k in range(c.i - 1, max(-1, c.i - 5), -1):
            if doc[k].lower_ in SUBJ_P and doc[k].dep_ in ('nsubj', 'nsubj:pass', ''):
                want = SUBJ_P[doc[k].lower_]
                if want in opts or not opts: return {want}, 'subj'
        if 'gente' in [doc[k].lower_ for k in range(max(0, c.i - 3), c.i)]: return {('1', 'Plur'), ('3', 'Sing')}, 'a-gente'
        imp = imperative_persons(c)
        sent_start = clause_start(doc, c.i)
        if imp and sent_start and not any(d.dep_ == 'nsubj' and d.i < c.i and d.pos_ in ('NOUN', 'PROPN', 'PRON') for d in c.children):
            opts = opts | imp
        return opts or None, 'fin'
    # small clause with its own subject: 'pessoas me tocando', 'vi o João levantar-se'
    seq = proclitic_seq(doc, c.i)
    first = seq[0][1] if seq else c.i
    if seq and first > 0 and doc[first - 1].lower_ in SUBJ_P:    # para você me tratar / antes de eu me ir
        return {SUBJ_P[doc[first - 1].lower_]}, 'inf-subj'
    if seq and first > 0 and doc[first - 1].pos_ in ('NOUN', 'PROPN') and doc[first - 1].dep_ in ('obj', 'nsubj', 'iobj') \
            and not any(e[1] in FIN_MOODS for e in entries(doc[first - 1].lower_)):
        return {('3', 'Plur' if 'Number=Plur' in str(doc[first - 1].morph) else 'Sing')}, 'small-clause'
    # personal infinitive (para te sentires) / future-subj-like forms
    h = host_of(c.text)
    pers = {(e[3], 'Sing' if e[4] == 's' else 'Plur') for e in entries(h) if e[1] == 'infinitivo' and 'pessoal' in e[2] and e[3] and h != lemma_of(c)}
    if pers: return pers, 'pers-inf'
    for ch in c.children:
        if ch.dep_.startswith('aux') and vform(ch) == 'Fin':
            return controller(doc, ch, ch.i, depth + 1)
    hd = c.head
    if hd is c or not is_verb(hd): return None, 'uncontrolled'
    # por/para/sem + infinitive adjunct while the matrix verb has its own object clitic: controller is ambiguous
    if c.dep_ in ('advcl', 'obl', 'acl') and any(x in CL_PERS or x in ('o', 'a', 'lhe', 'lo', 'la') for x in split_token(hd.text)[1] + [y for y, _ in proclitic_seq(doc, hd.i)]):
        return None, 'uncontrolled'
    if lemma_of(hd) in ('deixar', 'fazer', 'mandar', 'ver', 'ouvir', 'ajudar', 'ensinar', 'obrigar', 'convidar', 'permitir', 'impedir', 'pedir'):
        hcl, _ = clitics_of(doc, hd)
        for x in hcl:
            if x in CL_PERS: return {CL_PERS[x]}, 'objctl'
            if x in ('lhe', 'o', 'a', 'lo', 'la', 'no', 'na'): return {('3', 'Sing')}, 'objctl'
        for ch in hd.children:
            if ch.dep_ in ('obj', 'iobj') and ch.pos_ in ('NOUN', 'PROPN'): return {('3', 'Sing')}, 'objctl'
            if ch.dep_ in ('obj', 'nsubj') and ch.lower_ in SUBJ_P and ch.i > hd.i: return {SUBJ_P[ch.lower_]}, 'objctl'
    if any(ch.dep_ == 'cop' for ch in c.children) or lemma_of(hd) == 'ser': return None, 'uncontrolled'
    return controller(doc, hd, hd.i, depth + 1)
def predict(doc, span):
    t = target_token(doc, span)
    if t is None: return 'Z', 'notok'
    if not is_verb(t): return 'Z', 'pos'
    host, enc = split_token(t.text)
    tl = lemma_of(t)
    # auxiliary/restructuring target with a complement: its clitics belong to the complement
    if tl in RESTRUCT or tl in ('haver', 'ter'):
        k = t.i + 1
        while k < len(doc) and (doc[k].lower_ in ('não', 'a', 'de', 'que', 'já') or (doc[k].lower_ in SKIPCL and '-' not in doc[k].text)): k += 1
        if k < len(doc) and is_verb(doc[k]) and vform(doc[k]) in ('Inf', 'Ger', 'Part'):
            gov = find_governor(doc, k, vform(doc[k]))
            if gov == t.i or (gov is not None and gov < t.i):
                return 'N', 'climbed-to-complement'
    cls, carrier = clitics_of(doc, t)
    refl = [c for c in cls if c in REFL]
    if not refl: return 'N', 'no-refl-clitic'
    if 'se' in refl: return 'SE', 'se'
    ctrl, how = controller(doc, t, carrier)
    c = refl[0]; want = CL_PERS[c]
    if not ctrl: return 'U', 'uncontrolled'
    match = any(p == want[0] and (n is None or n == want[1]) for p, n in ctrl)
    if match and len({p for p, n in ctrl}) > 1 and how == 'fin':
        return 'A', 'ambiguous-person'
    return ('R' if match else 'N'), how
ANIM = ('ele', 'ela', 'eles', 'elas', 'você', 'vocês', 'gente', 'ninguém', 'alguém', 'senhor', 'senhora', 'outros', 'outras', 'todos', 'todo')
def clause_start(doc, i):
    return i == 0 or doc[i - 1].is_punct or doc[i - 1].lower_ in ('e', 'não', 'nunca', 'favor', 'mas', 'agora', 'vá', 'vamos', 'só', 'apenas', 'então', 'oh', 'ok', 'bem', 'sim', 'ei', 'agora')
def explicit_subject(doc, t, c):
    """nsubj of the carrier verb that precedes it (not a relative 'que')"""
    for x in (c, t):
        for ch in x.children:
            if ch.dep_ in ('nsubj', 'nsubj:pass') and ch.i < x.i and ch.lower_ not in ALLCL and ch.pos_ in ('NOUN', 'PROPN', 'PRON', 'DET') \
                    and ch.i != c.i and not (ch.pos_ not in ('NOUN', 'PROPN') and ch.lower_ not in SUBJ_P and any(e[1] in FIN_MOODS for e in entries(ch.lower_))) \
                    and not any(g.dep_ == 'case' for g in ch.children): return ch
    return None
def resolve_ambiguous(doc, t, carrier, clitic):
    c = doc[carrier] if carrier is not None else t
    subj = explicit_subject(doc, t, c)
    want = CL_PERS[clitic]
    if subj is not None:
        sp = SUBJ_P.get(subj.lower_)
        if sp is None: sp = ('3', 'Sing')          # NP, relative 'que' with a noun antecedent, isto/isso
        return 'SE_FIRM' if sp[0] == want[0] else 'NO_SE', 'amb-subj'
    host, enc = split_token(c.text)
    imp = imperative_persons(c)
    if clause_start(doc, c.i if not proclitic_seq(doc, c.i) else proclitic_seq(doc, c.i)[0][1]) and imp:
        # imperative position: tu-imperative takes te; você-imperative (3sg subj) cannot take me/te reflexively
        if clitic == 'te' and ('2', 'Sing') in imp: return 'SE_FIRM', 'amb-imp-tu'
        if clitic == 'me' and ('3', 'Sing') in imp and any(e[1] == 'subjuntivo' and e[2] == 'presente' for e in entries(host)): return 'NO_SE', 'amb-imp-voce'
    return 'BOTH', 'ambiguous-person'
def policy(doc, span):
    lab, why = predict(doc, span)
    if lab == 'Z': return 'Z', why
    if lab == 'N': return 'NO_SE', why
    if lab == 'R': return 'SE_FIRM', why
    t = target_token(doc, span)
    cls, carrier = clitics_of(doc, t)
    if lab == 'A':
        c = [x for x in cls if x in CL_PERS][0]
        return resolve_ambiguous(doc, t, carrier, c)
    if lab == 'U': return 'BOTH', why
    # 3rd-person se
    c = doc[carrier] if carrier is not None else t
    host, enc = split_token(c.text)
    imp = imperative_persons(c)
    first = proclitic_seq(doc, c.i)[0][1] if proclitic_seq(doc, c.i) else c.i
    IMPERSONAL_FORMULA = {'acrescentar', 'registrar', 'registar', 'notar', 'observar', 'destacar', 'ressaltar', 'salientar', 'sublinhar',
                          'frisar', 'assinalar', 'considerar', 'ver', 'dizer', 'referir', 'recordar', 'admitir', 'reconhecer', 'poder', 'dever'}
    que_before = any(doc[x].lower_ in ('que', 'se', 'quando', 'caso', 'embora', 'talvez') for x in range(max(0, first - 8), first))
    sent_initial = first == 0 or doc[first - 1].text in ('.', '!', '?', '-', '—', '"', '“') or \
        (doc[first - 1].lower_ in ('não', 'nunca', 'favor', 'vá', 'vamos') and (first - 1 == 0 or doc[first - 2].is_punct or doc[first - 2].lower_ == 'por'))
    if imp and any(p == '3' for p, n in imp) and not que_before and not explicit_subject(doc, t, c) and lemma_of(c) not in IMPERSONAL_FORMULA \
            and ((enc and clause_start(doc, first)) or sent_initial):
        if any(e[1] == 'subjuntivo' and e[2] == 'presente' for e in lemma_entries(c)): return 'SE_FIRM', 'imp-se'
    subj = explicit_subject(doc, t, c)
    in_relative = c.dep_ == 'acl:relcl' or any(ch.lower_ in ('que', 'onde', 'qual', 'quais', 'cujo') and ch.i < c.i for ch in c.children)
    if subj is not None and not in_relative and vform(c) == 'Fin' and subj.lower_ not in ('que', 'o', 'a', 'isto', 'isso', 'aquilo', 'quem'):
        return 'SE_FIRM', 'preverbal-subj'
    for k in range(max(0, first - 4), first):
        if doc[k].lower_ in ANIM: return 'SE_FIRM', 'animate-subj'
    pr = SE_PRIOR.get(lemma_of(t), {})
    modal_impersonal = lemma_of(c) in ('poder', 'dever') and c is not t
    if not in_relative and not modal_impersonal and sum(pr.values()) >= 5 and pr.get('R', 0) / sum(pr.values()) >= 0.95:
        return 'SE_FIRM', 'prior'
    return 'BOTH', 'se-3p'
