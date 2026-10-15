"""Rule labeller v0 for Portuguese function words: Stanza parse + Wiktionary, no WSD.

label(words, i, surface=None) -> {"kind": unit|role|none, "value", "gloss", "rule"}
`words` is one Stanza sentence's words, `i` the target's first word. Contractions
(do = de + o, no = em + o) are split by Stanza, so `surface` carries the token as
written. Order: fixed multiword entry > verb + governed preposition (gostar de) >
pronominal verb (preocupar-se) > se / que / article roles > preposition >
pronoun or determiner > conjunction > none.
"""
import json, re
KAIKKI = "/Users/joshuathomasamar/PycharmProjects/Fluency-Workspace/raw/wiktionary/enwiktionary-2026-08-20/kaikki.org-dictionary-Portuguese.jsonl"
from gloss_filter import Glosses
from grammar_context import phrase_is_literal, clitic_label, feat
PHRASE_POS = {"phrase", "prep_phrase", "adv", "adj", "particle", "conj", "intj", "prep", "pron", "contraction"}
PREPS = ("de", "a", "que", "em", "com", "por", "para")


_G = Glosses(KAIKKI)
_clean = _G.clean  # shared: drops entry notes, follows 'spelling of' pointers


PHRASE_KIND = {}
LIGHT_VERBS = {"ir", "ser", "estar", "fazer", "dar", "ficar", "vir", "ver", "haver", "pôr", "levar", "passar"}
TIME_NOUNS = {"dia", "dias", "hora", "horas", "minuto", "minutos", "segundo", "segundos", "semana", "semanas", "mês", "meses",
              "ano", "anos", "momento", "vez", "vezes", "noite", "manhã", "tarde", "altura", "instante"}
OBJECT_FORM = {"eu": "me", "tu": "you", "ele": "him / it", "ela": "her / it", "nós": "us", "eles": "them", "elas": "them",
               "você": "you", "vocês": "you (plural)", "vós": "you (plural)"}


def _load():
    phrases, pronominal, verb_frames, verbs = {}, {}, {}, {}
    global PHRASE_KIND
    for line in open(KAIKKI):
        e = json.loads(line)
        w = e["word"].lower(); pos = e.get("pos")
        senses = e.get("senses", [])
        gl = _G.senses(senses)
        if not gl: continue
        # two-word adjective entries are mostly 'do mundo' (non-religious): keep only longer ones and 'a salvo'-type
        if " " in w and pos in PHRASE_POS and not (pos == "adj" and w.split()[0] not in ("a", "em", "de", "sem")):
            phrases.setdefault(w, gl[0]); PHRASE_KIND.setdefault(w, pos)
        if " " in w and len(w.split()) == 2 and w.split()[-1] in PREPS and pos in ("verb", "phrase"):
            verb_frames.setdefault(w, gl[0])
        if pos == "verb" and " " not in w:
            verbs.setdefault(w, gl[0])
            # governed prepositions are written into the gloss: 'to need [with de ‘something’]'
            for sn in senses:
                for raw in sn.get("raw_glosses") or sn.get("glosses", []):
                    for prep in re.findall(r"\[with (?:[^\]]*?\b)?(de|a|em|com|por|para)\b", raw):
                        clean = re.sub(r"^\([^)]*\)\s*|\s*\[[^\]]*\]", "", raw).strip()
                        if clean: verb_frames.setdefault(f"{w} {prep}", clean)
            for s in senses:
                tags = s.get("tags", [])
                if ("pronominal" in tags or "reflexive" in tags) and _clean(s.get("glosses", [])):
                    pronominal.setdefault(w, _clean(s["glosses"])[0]); break
    return phrases, pronominal, verb_frames, verbs


PHRASES, PRONOMINAL, VERB_FRAMES, VERBS = _load()
# Wiktionary marks these 'used other than figuratively or idiomatically', so gloss_filter drops them;
# in running text the idiom dominates, so they are kept (hand-checked on deck sentences, 2026-10-13).
IDIOMS = {"por que", "do que", "o senhor", "um pouco", "um dia", "uma vez", "por que não", "quem sabe", "muito menos",
          "daqui a", "quanto mais", "a gente", "entre outros", "numa palavra", "cada vez mais"}
PHRASES.update({w: _G.idiom[w] for w in IDIOMS if w in _G.idiom})
# Ambiguous or misleading entries the rules handle themselves.
for p in ("o que", "é que", "do que", "no que", "a que", "de que", "em que", "que nem", "se não", "a minha", "o meu", "a gente que"):
    PHRASES.pop(p, None)
BY_TOKEN = {}
for p in PHRASES:
    for t in p.split(): BY_TOKEN.setdefault(t, []).append(p)

ARTICLE = {"o": "the", "a": "the", "os": "the", "as": "the", "um": "a / an", "uma": "a / an", "uns": "some", "umas": "some"}
PREP_GLOSS = {"de": "of / from", "em": "in / on / at", "a": "to / at", "por": "by / for / through", "para": "for / to",
              "com": "with", "sem": "without", "sobre": "about / on", "até": "until / up to", "entre": "between",
              "desde": "since / from", "durante": "during", "após": "after", "perante": "before (facing)", "contra": "against",
              "ante": "before", "segundo": "according to", "conforme": "according to", "salvo": "except", "via": "via",
              "trás": "behind", "fora": "outside / except", "menos": "except"}
# Contractions: preposition + article/demonstrative/pronoun, glossed whole.
CONTRACTION = {
    "do": "of / from the", "da": "of / from the", "dos": "of / from the", "das": "of / from the",
    "no": "in / on the", "na": "in / on the", "nos": "in / on the", "nas": "in / on the",
    "ao": "to the", "à": "to the", "aos": "to the", "às": "to the", "pelo": "by / through the", "pela": "by / through the",
    "pelos": "by / through the", "pelas": "by / through the", "num": "in a", "numa": "in a", "dum": "of a", "duma": "of a",
    "dele": "his / of him", "dela": "her / of her", "deles": "their / of them", "delas": "their / of them",
    "nele": "in him / in it", "nela": "in her / in it", "neles": "in them", "nelas": "in them",
    "disso": "of that", "disto": "of this", "daquilo": "of that", "nisso": "in that", "nisto": "in this", "naquilo": "in that",
    "deste": "of this", "desta": "of this", "destes": "of these", "destas": "of these", "desse": "of that", "dessa": "of that",
    "desses": "of those", "dessas": "of those", "daquele": "of that", "daquela": "of that", "daqueles": "of those",
    "daquelas": "of those", "neste": "in this", "nesta": "in this", "nestes": "in these", "nestas": "in these",
    "nesse": "in that", "nessa": "in that", "nesses": "in those", "nessas": "in those", "naquele": "in that",
    "naquela": "in that", "naqueles": "in those", "naquelas": "in those", "àquele": "to that", "àquela": "to that",
    "àqueles": "to those", "noutro": "in another", "noutra": "in another", "noutras": "in other", "nalgum": "in some",
    "nalguma": "in some", "daqui": "from here", "daí": "from there / so", "dali": "from there", "donde": "from where",
}
CONJ_GLOSS = {"e": "and", "mas": "but", "ou": "or", "porque": "because", "quando": "when", "como": "as / like / since",
              "se": "if / whether", "que": "that", "embora": "although", "enquanto": "while", "pois": "because / since",
              "nem": "nor / not even", "caso": "in case / if", "porém": "however", "entretanto": "meanwhile / however",
              "senão": "otherwise / but", "conforme": "as / according to", "logo": "so / therefore", "ora": "well / now",
              "quer": "whether", "então": "so / then", "mal": "as soon as", "segundo": "according to"}
COMPARATIVE = {"mais", "menos", "melhor", "pior", "maior", "menor", "antes", "mesmo", "tanto", "tão", "outro", "outra"}

# Pronouns and determiners: role from Stanza features, gloss from this table (role -> gloss, "*" any role).
PRON_GLOSS = {
    "eu": {"*": "I"}, "tu": {"*": "you"}, "você": {"*": "you"}, "ele": {"*": "he / it"}, "ela": {"*": "she / it"},
    "nós": {"*": "we / us"}, "vocês": {"*": "you (plural)"}, "eles": {"*": "they / them"}, "elas": {"*": "they / them"},
    "vós": {"*": "you (plural, formal)"}, "a gente": {"*": "we"},
    "me": {"reflexive": "myself", "*": "me / to me"}, "te": {"reflexive": "yourself", "*": "you / to you"},
    "lhe": {"*": "(to) him / her / you"}, "lhes": {"*": "(to) them"}, "nos": {"reflexive": "ourselves", "*": "us / to us"},
    "vos": {"*": "you / to you (plural)"}, "mim": {"*": "me"}, "ti": {"*": "you"}, "si": {"*": "yourself / himself / oneself"},
    "o": {"*": "him / it"}, "a": {"*": "her / it"}, "os": {"*": "them"}, "as": {"*": "them"},
    "meu": {"*": "my / mine"}, "minha": {"*": "my / mine"}, "meus": {"*": "my / mine"}, "minhas": {"*": "my / mine"},
    "teu": {"*": "your / yours"}, "tua": {"*": "your / yours"}, "teus": {"*": "your / yours"}, "tuas": {"*": "your / yours"},
    "seu": {"*": "his / her / your / their"}, "sua": {"*": "his / her / your / their"}, "seus": {"*": "his / her / your / their"},
    "suas": {"*": "his / her / your / their"}, "nosso": {"*": "our / ours"}, "nossa": {"*": "our / ours"},
    "nossos": {"*": "our / ours"}, "nossas": {"*": "our / ours"}, "vosso": {"*": "your (plural)"}, "vossa": {"*": "your (plural)"},
    "vossos": {"*": "your (plural)"}, "vossas": {"*": "your (plural)"},
    "este": {"*": "this"}, "esta": {"*": "this"}, "estes": {"*": "these"}, "estas": {"*": "these"},
    "esse": {"*": "that"}, "essa": {"*": "that"}, "esses": {"*": "those"}, "essas": {"*": "those"},
    "aquele": {"*": "that (over there)"}, "aquela": {"*": "that (over there)"}, "aqueles": {"*": "those"}, "aquelas": {"*": "those"},
    "isto": {"*": "this"}, "isso": {"*": "that"}, "aquilo": {"*": "that"},
    "quem": {"relative": "who / whom", "*": "who"}, "qual": {"relative": "which", "*": "which / what"},
    "quais": {"relative": "which", "*": "which / what"}, "quê": {"*": "what"},
    "quanto": {"*": "how much"}, "quanta": {"*": "how much"}, "quantos": {"*": "how many"}, "quantas": {"*": "how many"},
    "tudo": {"*": "everything"}, "nada": {"*": "nothing / anything"}, "algo": {"*": "something"}, "alguém": {"*": "someone"},
    "ninguém": {"*": "nobody / anyone"}, "todo": {"*": "all / every / whole"}, "toda": {"*": "all / every / whole"},
    "todos": {"*": "all / everyone"}, "todas": {"*": "all"}, "cada": {"*": "each / every"}, "qualquer": {"*": "any"},
    "quaisquer": {"*": "any"}, "nenhum": {"*": "no / none"}, "nenhuma": {"*": "no / none"}, "nenhuns": {"*": "no / none"},
    "nenhumas": {"*": "no / none"}, "algum": {"*": "some / any"}, "alguma": {"*": "some / any"}, "alguns": {"*": "some"},
    "algumas": {"*": "some"}, "outro": {"*": "other / another"}, "outra": {"*": "other / another"}, "outros": {"*": "others"},
    "outras": {"*": "others"}, "muito": {"*": "much / a lot of"}, "muita": {"*": "much / a lot of"}, "muitos": {"*": "many"},
    "muitas": {"*": "many"}, "pouco": {"*": "little / not much"}, "pouca": {"*": "little"}, "poucos": {"*": "few"},
    "poucas": {"*": "few"}, "tanto": {"*": "so much"}, "tanta": {"*": "so much"}, "tantos": {"*": "so many"},
    "tantas": {"*": "so many"}, "ambos": {"*": "both"}, "ambas": {"*": "both"}, "vários": {"*": "several"},
    "várias": {"*": "several"}, "tal": {"*": "such"}, "tais": {"*": "such"}, "próprio": {"*": "own / -self"},
    "própria": {"*": "own / -self"}, "bastante": {"*": "enough / quite a lot"}, "demais": {"*": "too much / the others"},
    "certo": {"*": "a certain"}, "certa": {"*": "a certain"}, "determinado": {"*": "a certain"},
    "determinada": {"*": "a certain"}, "mesmo": {"*": "same / -self"}, "mesma": {"*": "same / -self"},
}
POSSESSIVE = {f for f in PRON_GLOSS if re.match(r"^(meu|minha|teu|tua|seu|sua|nosso|nossa|vosso|vossa)s?$", f)}
DEMONSTRATIVE = {"este", "esta", "estes", "estas", "esse", "essa", "esses", "essas", "aquele", "aquela", "aqueles", "aquelas",
                 "isto", "isso", "aquilo"}
INTERROGATIVE = {"quem", "qual", "quais", "quê", "quanto", "quanta", "quantos", "quantas"}
INDEFINITE = {"tudo", "nada", "algo", "alguém", "ninguém"}
SUBJECT = {"eu", "tu", "você", "ele", "ela", "nós", "vocês", "eles", "elas", "vós"}
CLITIC = {"me", "te", "lhe", "lhes", "nos", "vos", "o", "a", "os", "as", "se"}


def _unit(value, gloss, rule):
    return {"kind": "unit", "value": value, "gloss": gloss, "rule": rule}


def _role(value, gloss, rule="role"):
    return {"kind": "role", "value": value, "gloss": gloss, "rule": rule}


def _tokens(sent):
    """Surface tokens of the sentence as (text, first word index, lemma of first word)."""
    out, seen = [], set()
    for k, w in enumerate(sent):
        tok = w.parent
        if id(tok) in seen: continue
        seen.add(id(tok)); out.append((tok.text.lower(), k, w.lemma.lower() if w.lemma else ""))
    return out


def _phrase(sent, i):
    toks = _tokens(sent); pos = next(n for n, t in enumerate(toks) if sent[t[1]].parent is sent[i].parent)
    best = None
    for p in BY_TOKEN.get(toks[pos][0], []):
        parts = p.split(); n = len(parts)
        for k, part in enumerate(parts):
            if part != toks[pos][0]: continue
            s = pos - k
            if s < 0 or s + n > len(toks): continue
            if all(parts[j] in (toks[s + j][0], toks[s + j][2]) for j in range(n)):
                if best is None or n > best[1]: best = (p, n)
    return best


def label(sent, i, surface=None, reflexive_decisions=None):
    w = sent[i]; t = (surface or w.parent.text or w.text).lower()
    head = sent[w.head - 1] if w.head else None
    kids = lambda h: [x for x in sent if x.head == h.id]
    prev = sent[i - 1].text.lower() if i > 0 else ""
    toks = _tokens(sent); tpos = next(n for n, x in enumerate(toks) if sent[x[1]].parent is w.parent)
    nxt_tok = toks[tpos + 1][0] if tpos + 1 < len(toks) else ""
    prev_tok = toks[tpos - 1][0] if tpos > 0 else ""

    if t in ("se", "me", "te", "nos", "vos"):
        clitic = clitic_label(sent, i, t, "pt", PRONOMINAL, reflexive_decisions, VERBS)
        if clitic is not None:
            return clitic
    if t in ("um", "uma", "uns", "umas") and w.upos == "NUM":
        return _role("quantifier", {"um": "one", "uma": "one", "uns": "some", "umas": "some"}[t], "partitive_number")
    if t == "que" and prev_tok in ("", "-", "¿") and nxt_tok in ("é", "foi"):
        return _role("interrogative", "what", "question_cleft")
    # Productive degree/time constructions survive dictionary-note filtering.
    if t in ("cada", "vez"):
        start = tpos if t == "cada" else tpos - 1
        if start >= 0 and start + 1 < len(toks) and [x[0] for x in toks[start:start + 2]] == ["cada", "vez"]:
            modifier = toks[start + 2][0] if start + 2 < len(toks) else ""
            if modifier in ("mais", "menos", "maior", "menor", "melhor", "pior"):
                return _unit("cada vez", "progressively / increasingly", "progressive_degree")
            if start and toks[start - 1][0] == "de":
                return _unit("de cada vez", "at a time", "distributive_time")

    # 1. fixed multiword entries, longest first ('se' goes to its verb instead: não se preocupe -> preocupar-se)
    if t in ("o", "no", "do") and nxt_tok == "que":
        if t == "do" and any(x[0] in COMPARATIVE for x in toks[:tpos]): return _unit("do que", "than", "comparative")
        if t == "o": return _unit("o que", "what / which", "o_que")
    ph = _phrase(sent, i) if t != "se" else None
    if ph and phrase_is_literal(sent, toks, tpos, ph[0], PHRASE_KIND):
        ph = None
    if ph and ph[1] == 2 and ph[0].split()[0] == t and tpos + 1 < len(toks):
        # 'significado da vida' is literal (vida modifies a noun); the idiom 'da vida' (extremely) is not
        nxt_word = sent[toks[tpos + 1][1]]
        if nxt_word.deprel == "nmod" and nxt_word.head and sent[nxt_word.head - 1].upos == "NOUN": ph = None
    if ph and PHRASE_KIND.get(ph[0]) == "intj":
        # an interjection ('que isso!') only when it stands alone between punctuation marks
        s0 = tpos - ph[0].split().index(t) if t in ph[0].split() else tpos
        before = toks[s0 - 1][0] if s0 > 0 else "."
        after = toks[s0 + ph[1]][0] if s0 + ph[1] < len(toks) else "."
        if not (re.fullmatch(r"\W+", before) and re.fullmatch(r"\W+", after)): ph = None
    if ph and ph[0] == "isto é" and nxt_tok != "," and prev_tok != ",": ph = None  # 'isto é' (that is) vs 'isto é contra a lei'
    if ph and ph[1] >= 2: return _unit(ph[0], PHRASES[ph[0]], "phrase")
    # 2. que: cleft 'é que' after a question word, 'o que', comparison 'do que' / 'que'
    if t == "que":
        if prev_tok in ("é", "foi") and tpos >= 2 and toks[tpos - 2][0] in ("porque", "onde", "quando", "como", "quem", "que", "quê", "o", "qual"):
            return _unit("é que", "(question emphasis, not translated)", "cleft")
        if prev_tok in ("o", "no", "do", "ao", "pelo"):
            if prev_tok == "do" and any(x[0] in COMPARATIVE for x in toks[:tpos]): return _unit("do que", "than", "comparative")
            return _unit("o que", "what / which", "o_que")
        if prev_tok == "do" and any(x[0] in COMPARATIVE for x in toks[:tpos]): return _unit("do que", "than", "comparative")
        if any(x[0] in COMPARATIVE for x in toks[max(0, tpos - 4):tpos]) and w.upos in ("SCONJ", "CCONJ", "ADP"):
            return _role("than", "than", "comparative")
        if head is not None and w.deprel == "mark":
            near = ([sent[head.head - 1]] if head.head else []) + kids(head)
            have = next((x for x in near if x.lemma in ("ter", "haver") and x.id < w.id), None)
            if have is not None: return _unit(have.lemma + " que", "have to", "ter_que")
        if "PronType=Rel" in (w.feats or "") or (w.upos == "PRON" and w.deprel != "obj"):
            if "PronType=Int" in (w.feats or "") and prev_tok in ("", "e", "mas", "porque", "-"): return _role("interrogative", "what", "role")
            return _role("relative", "that / which / who", "role")
        if w.upos == "PRON": return _role("interrogative", "what", "role")
        return _role("conj_that", "that", "role")
    # 3. verb + governed preposition (gostar de, precisar de, ter de)
    if (w.upos == "ADP" or w.deprel == "mark") and head is not None and t in PREPS:
        gov = sent[head.head - 1] if head.head else None
        # the preposition hangs on its complement (fazer, mim); the verb that governs it is one up
        for v in (gov,):
            if v is None or v.upos not in ("VERB", "AUX", "ADJ"): continue
            if v.lemma.lower() in LIGHT_VERBS: continue  # 'com quem você vai' is not 'ir com' (to match)
            # 'encontraremos em três horas': a time or number phrase is not the verb's governed object
            if head.upos == "NUM" or any(k.deprel == "nummod" for k in kids(head)) or head.text.lower() in TIME_NOUNS: continue
            lem = v.lemma.lower()
            if f"{lem} {t}" in VERB_FRAMES: return _unit(f"{lem} {t}", VERB_FRAMES[f"{lem} {t}"], "verb_frame")
        if w.deprel == "mark" and t in PREP_GLOSS: return _role("prep", PREP_GLOSS[t])  # same meaning before a verb; one row on the card
    # 4. se: conjunction 'if' or a clitic on a (pronominal) verb
    if t == "se":
        if w.upos in ("SCONJ", "CCONJ") or w.deprel == "mark": return _role("conj_if", "if / whether")
        if head is not None:
            lem = head.lemma.lower()
            if lem in PRONOMINAL: return _unit(lem + "-se", PRONOMINAL[lem], "pronominal_verb")
            subj = [k for k in kids(head) if k.deprel.startswith("nsubj")]
            if not subj and "Person=3" in (head.feats or "") and not any(k.deprel == "aux" for k in kids(head)) \
                    and not re.search(r"Mood=(Imp|Sub)", head.feats or ""):  # 'não se esqueça' is a command, not 'one forgets'
                return _role("impersonal_se", "one / (it) is done", "role")
            if head.upos == "VERB" and lem in VERBS:  # 'vão se juntar' -> juntar-se
                return _role("pronominal", "", "uncertain_pronominal_sense")
            return _role("reflexive", "himself / herself / themselves", "role")
    # clitic me/te/nos on a pronominal verb (preocupo-me, lembras-te)
    if t in ("me", "te", "nos", "vos") and head is not None and head.upos == "VERB" and head.lemma.lower() in PRONOMINAL \
            and ("Reflex=Yes" in (w.feats or "") or w.deprel in ("expl", "expl:pv")):
        return _unit(head.lemma.lower() + "-se", PRONOMINAL[head.lemma.lower()], "pronominal_verb")
    # 5. articles vs object pronouns
    if t in ARTICLE and w.upos == "DET": return _role("article", ARTICLE[t])
    if t in ("o", "a", "os", "as") and w.upos == "PRON":
        if nxt_tok == "senhor" or nxt_tok == "senhora": return _unit(f"{t} {nxt_tok}", "you (formal)", "phrase")
        return _role("object_pron", PRON_GLOSS[t]["*"])
    # 6. prepositions and contractions ('conseguem nos rastrear': 'nos' before a verb is 'us', not em + os)
    if t == "nos" and tpos + 1 < len(toks) and sent[toks[tpos + 1][1]].upos in ("VERB", "AUX"):
        return _role("object_pron", "us / to us")
    if t in CONTRACTION and (w.upos == "ADP" or len(w.parent.words) > 1):
        return _role("prep", CONTRACTION[t])
    if w.upos == "ADP" and t in PREP_GLOSS:
        if t == "a" and head is not None and head.upos in ("PRON", "PROPN") and head.deprel in ("obj",):
            return _role("personal_a", "(marks a person as object)")
        return _role("prep", PREP_GLOSS[t])
    # 7. pronouns and determiners
    pd = pron_det(sent, i, t)
    if pd: return pd
    # 8. conjunctions ('Porque devo confiar em si?' is European Portuguese 'why')
    first = next((x[0] for x in toks if not re.fullmatch(r"\W+", x[0])), "")
    if t == "porque" and (nxt_tok == "é" and tpos + 2 < len(toks) and toks[tpos + 2][0] == "que"
                          or (first == "porque" and sent[-1].text in ("?", '?"', "?»"))):
        return _role("interrogative", "why")
    if w.upos in ("SCONJ", "CCONJ") or (w.deprel == "mark" and t in CONJ_GLOSS):
        return _role("conj", CONJ_GLOSS.get(t, t))
    return {"kind": "none", "value": None, "gloss": None, "rule": "none"}


def pron_det(sent, i, t):
    w = sent[i]; g = PRON_GLOSS.get(t)
    if g is None or w.upos in ("NOUN", "PROPN", "VERB", "ADJ" if t not in ("próprio", "própria", "mesmo", "mesma") else "_"):
        return None
    if w.upos == "ADV" and t not in ("muito", "pouco", "tanto", "bastante", "demais", "tudo", "nada"): return None
    f = w.feats or ""; head = sent[w.head - 1] if w.head else None
    out = lambda role, gl=None: {"kind": "role", "value": role, "gloss": gl or g.get(role) or g["*"], "rule": "pron_det"}
    if t in ("mesmo", "mesma") and w.upos == "ADV": return out("adverb", "even / really")
    if t in ("muito", "pouco", "tanto", "bastante", "demais") and w.upos == "ADV":
        return out("adverb", {"muito": "very / a lot", "pouco": "a little / not very", "tanto": "so much",
                              "bastante": "quite / enough", "demais": "too much"}[t])
    if t in INDEFINITE: return out("indefinite")
    if t in POSSESSIVE: return out("possessive")
    if t in DEMONSTRATIVE: return out("demonstrative")
    if t in INTERROGATIVE:
        if "PronType=Rel" in f: return out("relative")
        return out("interrogative")
    if t in SUBJECT:
        if w.deprel.startswith("nsubj"): return out("subject_pron")
        if w.deprel in ("cop", "root") or (head is not None and head.upos == "AUX"): return out("subject_pron")
        return out("object_pron", OBJECT_FORM[t])
    if t in ("mim", "ti", "si"): return out("object_pron")
    if t in CLITIC:
        if "Reflex=Yes" in f or w.deprel in ("expl", "expl:pv"):
            return out("reflexive")
        if w.deprel == "iobj": return out("object_pron", {"me": "(to) me", "te": "(to) you", "nos": "(to) us"}.get(t))
        return out("object_pron")
    return out("quantifier")

