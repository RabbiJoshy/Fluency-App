"""Rule labeller v0 for Spanish function words: Stanza parse + Wiktionary, no WSD.

Same contract and order as labeller_pt: label(words, i, surface=None). Contractions
are only del (de + el) and al (a + el). Pronominal verbs (irse, quedarse) come
from Wiktionary's pronominal/reflexive senses of the base verb.
"""
import json, re
KAIKKI = "/Users/joshuathomasamar/PycharmProjects/Fluency-Workspace/raw/wiktionary/enwiktionary-2026-09-13/kaikki.org-dictionary-Spanish.jsonl"
PHRASE_POS = {"phrase", "prep_phrase", "adv", "adj", "particle", "conj", "intj", "prep", "pron", "contraction"}
PREPS = ("de", "a", "que", "en", "con", "por", "para")


def _clean(glosses):
    return [g for g in glosses if "form of" not in g and "inflection of" not in g and "combined with" not in g
            and "contraction of" not in g.lower() and "misspelling" not in g]


def _load():
    phrases, pronominal, verb_frames, verbs = {}, {}, {}, {}
    for line in open(KAIKKI):
        e = json.loads(line)
        w = e["word"].lower(); pos = e.get("pos")
        senses = e.get("senses", [])
        gl = _clean([g for s in senses for g in s.get("glosses", [])])
        if not gl: continue
        if " " in w and pos in PHRASE_POS and not (pos == "adj" and w.split()[0] not in ("a", "en", "de", "sin")):
            phrases.setdefault(w, gl[0])
        if " " in w and len(w.split()) == 2 and w.split()[-1] in PREPS and pos in ("verb", "phrase"):
            verb_frames.setdefault(w, gl[0])
        if pos == "verb" and " " not in w:
            verbs.setdefault(w, gl[0])
            for sn in senses:
                for raw in sn.get("raw_glosses") or sn.get("glosses", []):
                    for prep in re.findall(r"\[with (?:[^\]]*?\b)?(de|a|en|con|por|para)\b", raw):
                        clean = re.sub(r"^\([^)]*\)\s*|\s*\[[^\]]*\]", "", raw).strip()
                        if clean: verb_frames.setdefault(f"{w} {prep}", clean)
            for s in senses:
                tags = s.get("tags", [])
                if ("pronominal" in tags or "reflexive" in tags) and _clean(s.get("glosses", [])):
                    pronominal.setdefault(w, _clean(s["glosses"])[0]); break
    return phrases, pronominal, verb_frames, verbs


PHRASES, PRONOMINAL, VERB_FRAMES, VERBS = _load()
for p in ("lo que", "el que", "la que", "los que", "las que", "de que", "en que", "a que", "es que", "se lo", "a la", "a lo", "de la", "en el"):
    PHRASES.pop(p, None)
# Common verb + preposition frames Wiktionary glosses do not mark with '[with ...]'.
VERB_FRAMES.update({"volver a": "to do again", "acabar de": "to have just (done)", "dejar de": "to stop (doing)",
                    "empezar a": "to start to", "comenzar a": "to begin to", "tratar de": "to try to",
                    "pensar en": "to think about", "soñar con": "to dream of", "casarse con": "to marry",
                    "enamorarse de": "to fall in love with", "deber de": "must (probably)", "ponerse a": "to start to"})
PHRASES.update({"por la mañana": "in the morning", "por la tarde": "in the afternoon / evening"})
LIGHT_VERBS = {"ser", "estar", "ir", "hacer", "dar", "haber", "poner", "llevar", "ver", "venir", "pasar"}
BY_TOKEN = {}
for p in PHRASES:
    for t in p.split(): BY_TOKEN.setdefault(t, []).append(p)

ARTICLE = {"el": "the", "la": "the", "los": "the", "las": "the", "un": "a / an", "una": "a / an", "unos": "some",
           "unas": "some", "lo": "the (+ adjective: the ... thing)"}
PREP_GLOSS = {"de": "of / from", "en": "in / on / at", "a": "to / at", "por": "by / for / through", "para": "for / to",
              "con": "with", "sin": "without", "sobre": "about / on", "hasta": "until / up to / even", "entre": "between",
              "desde": "since / from", "durante": "during", "tras": "after / behind", "contra": "against",
              "ante": "before (facing)", "bajo": "under", "según": "according to", "hacia": "towards", "mediante": "by means of",
              "excepto": "except", "salvo": "except", "menos": "except", "vía": "via", "incluso": "even / including"}
CONTRACTION = {"del": "of / from the", "al": "to the"}
CONJ_GLOSS = {"y": "and", "e": "and", "pero": "but", "o": "or", "u": "or", "porque": "because", "cuando": "when",
              "como": "as / like / since", "si": "if / whether", "que": "that", "aunque": "although", "mientras": "while",
              "pues": "because / well", "ni": "nor / not even", "sino": "but rather", "entonces": "so / then",
              "luego": "so / then", "conque": "so (then)", "conforme": "as", "según": "as / according to"}
COMPARATIVE = {"más", "menos", "mejor", "peor", "mayor", "menor", "antes", "mismo", "misma", "otro", "otra", "tanto", "tan"}

PRON_GLOSS = {
    "yo": {"*": "I"}, "tú": {"*": "you"}, "vos": {"*": "you"}, "usted": {"*": "you (formal)"}, "él": {"*": "he / him / it"},
    "ella": {"*": "she / her / it"}, "nosotros": {"*": "we / us"}, "nosotras": {"*": "we / us"},
    "vosotros": {"*": "you (plural)"}, "vosotras": {"*": "you (plural)"}, "ustedes": {"*": "you (plural)"},
    "ellos": {"*": "they / them"}, "ellas": {"*": "they / them"},
    "me": {"reflexive": "myself", "*": "me / to me"}, "te": {"reflexive": "yourself", "*": "you / to you"},
    "le": {"*": "(to) him / her / you"}, "les": {"*": "(to) them / you"}, "nos": {"reflexive": "ourselves", "*": "us / to us"},
    "os": {"reflexive": "yourselves", "*": "you / to you (plural)"}, "lo": {"*": "him / it"}, "la": {"*": "her / it"},
    "los": {"*": "them"}, "las": {"*": "them"}, "mí": {"*": "me"}, "ti": {"*": "you"}, "sí": {"*": "himself / herself / oneself"},
    "conmigo": {"*": "with me"}, "contigo": {"*": "with you"}, "consigo": {"*": "with himself / herself"},
    "mi": {"*": "my"}, "mis": {"*": "my"}, "tu": {"*": "your"}, "tus": {"*": "your"}, "su": {"*": "his / her / your / their"},
    "sus": {"*": "his / her / your / their"}, "mío": {"*": "mine"}, "mía": {"*": "mine"}, "míos": {"*": "mine"},
    "mías": {"*": "mine"}, "tuyo": {"*": "yours"}, "tuya": {"*": "yours"}, "tuyos": {"*": "yours"}, "tuyas": {"*": "yours"},
    "suyo": {"*": "his / hers / yours / theirs"}, "suya": {"*": "his / hers / yours / theirs"},
    "suyos": {"*": "his / hers / yours / theirs"}, "suyas": {"*": "his / hers / yours / theirs"},
    "nuestro": {"*": "our / ours"}, "nuestra": {"*": "our / ours"}, "nuestros": {"*": "our / ours"},
    "nuestras": {"*": "our / ours"}, "vuestro": {"*": "your (plural)"}, "vuestra": {"*": "your (plural)"},
    "vuestros": {"*": "your (plural)"}, "vuestras": {"*": "your (plural)"},
    "este": {"*": "this"}, "esta": {"*": "this"}, "estos": {"*": "these"}, "estas": {"*": "these"},
    "ese": {"*": "that"}, "esa": {"*": "that"}, "esos": {"*": "those"}, "esas": {"*": "those"},
    "aquel": {"*": "that (over there)"}, "aquella": {"*": "that (over there)"}, "aquellos": {"*": "those"},
    "aquellas": {"*": "those"}, "esto": {"*": "this"}, "eso": {"*": "that"}, "aquello": {"*": "that"},
    "éste": {"*": "this one"}, "ésta": {"*": "this one"}, "ése": {"*": "that one"}, "ésa": {"*": "that one"},
    "quién": {"*": "who"}, "quiénes": {"*": "who"}, "quien": {"relative": "who / whom", "*": "who"},
    "quienes": {"relative": "who / whom", "*": "who"}, "cuál": {"*": "which / what"}, "cuáles": {"*": "which / what"},
    "cual": {"*": "which"}, "cuales": {"*": "which"}, "qué": {"*": "what / which"}, "cuánto": {"*": "how much"},
    "cuánta": {"*": "how much"}, "cuántos": {"*": "how many"}, "cuántas": {"*": "how many"}, "cuyo": {"*": "whose"},
    "cuya": {"*": "whose"},
    "todo": {"*": "all / everything / whole"}, "toda": {"*": "all / whole"}, "todos": {"*": "all / everyone"},
    "todas": {"*": "all"}, "nada": {"*": "nothing / anything"}, "algo": {"*": "something"}, "alguien": {"*": "someone"},
    "nadie": {"*": "nobody / anyone"}, "cada": {"*": "each / every"}, "cualquier": {"*": "any"},
    "cualquiera": {"*": "any / anyone"}, "ningún": {"*": "no / not any"}, "ninguno": {"*": "none / no one"},
    "ninguna": {"*": "no / none"}, "algún": {"*": "some / any"}, "alguno": {"*": "some / any"}, "alguna": {"*": "some / any"},
    "algunos": {"*": "some"}, "algunas": {"*": "some"}, "otro": {"*": "other / another"}, "otra": {"*": "other / another"},
    "otros": {"*": "others"}, "otras": {"*": "others"}, "mucho": {"*": "much / a lot of"}, "mucha": {"*": "much / a lot of"},
    "muchos": {"*": "many"}, "muchas": {"*": "many"}, "poco": {"*": "little / not much"}, "poca": {"*": "little"},
    "pocos": {"*": "few"}, "pocas": {"*": "few"}, "tanto": {"*": "so much"}, "tanta": {"*": "so much"},
    "tantos": {"*": "so many"}, "tantas": {"*": "so many"}, "ambos": {"*": "both"}, "ambas": {"*": "both"},
    "varios": {"*": "several"}, "varias": {"*": "several"}, "tal": {"*": "such"}, "tales": {"*": "such"},
    "mismo": {"*": "same / -self"}, "misma": {"*": "same / -self"}, "mismos": {"*": "same / -selves"},
    "mismas": {"*": "same / -selves"}, "propio": {"*": "own / -self"}, "propia": {"*": "own / -self"},
    "demasiado": {"*": "too much"}, "demasiada": {"*": "too much"}, "demasiados": {"*": "too many"},
    "demasiadas": {"*": "too many"}, "bastante": {"*": "enough / quite a lot"}, "bastantes": {"*": "enough / quite a few"},
    "demás": {"*": "the rest / others"}, "ello": {"*": "it / that"}, "tí": {"*": "you"},
    "ésto": {"*": "this"}, "éstos": {"*": "these (ones)"}, "éstas": {"*": "these (ones)"}, "ésos": {"*": "those (ones)"},
    "ésas": {"*": "those (ones)"}, "aquél": {"*": "that one"}, "cuantos": {"*": "as many as / however many"},
    "cuantas": {"*": "as many as / however many"}, "cuanto": {"*": "as much as"}, "cuanta": {"*": "as much as"}, "cierto": {"*": "a certain"}, "cierta": {"*": "a certain"},
}
POSSESSIVE = {"mi", "mis", "tu", "tus", "su", "sus"} | {f for f in PRON_GLOSS if re.match(r"^(mí|tuy|suy|nuestr|vuestr)", f) and f not in ("mí",)}
DEMONSTRATIVE = {f for f in PRON_GLOSS if re.match(r"^(est|es[eaoe]|aquel|aquél|éste|ésta|ésto|ése|ésa|ésos|ésas)", f)} | {"ello"}
INTERROGATIVE = {"cuantos", "cuantas", "cuanto", "cuanta", "quién", "quiénes", "quien", "quienes", "cuál", "cuáles", "cual", "cuales", "qué", "cuánto", "cuánta",
                 "cuántos", "cuántas", "cuyo", "cuya"}
INDEFINITE = {"nada", "algo", "alguien", "nadie", "cualquiera"}
SUBJECT = {"yo", "tú", "vos", "usted", "él", "ella", "nosotros", "nosotras", "vosotros", "vosotras", "ustedes", "ellos", "ellas"}
SUBJ_GLOSS = {"él": "he / it", "ella": "she / it", "ellos": "they", "ellas": "they", "nosotros": "we", "nosotras": "we"}
OBJ_GLOSS = {"él": "him / it", "ella": "her / it", "ellos": "them", "ellas": "them", "nosotros": "us", "nosotras": "us"}
CLITIC = {"me", "te", "le", "les", "nos", "os", "lo", "la", "los", "las", "se"}
ADVERBIAL = {"mucho": "a lot", "poco": "a little / not very", "tanto": "so much", "bastante": "quite / enough",
             "demasiado": "too / too much", "mismo": "right (here, now) / even", "todo": "all / completely", "nada": "not at all"}


def _unit(value, gloss, rule):
    return {"kind": "unit", "value": value, "gloss": gloss, "rule": rule}


def _role(value, gloss, rule="role"):
    return {"kind": "role", "value": value, "gloss": gloss, "rule": rule}


def _tokens(sent):
    out, seen = [], set()
    for k, w in enumerate(sent):
        tok = w.parent
        if id(tok) in seen: continue
        seen.add(id(tok)); out.append((tok.text.lower(), k, w.lemma.lower() if w.lemma else ""))
    return out


def _phrase(sent, i):
    toks = _tokens(sent); pos = next(n for n, t in enumerate(toks) if t[1] == i)
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


def label(sent, i, surface=None):
    w = sent[i]; t = (surface or w.parent.text or w.text).lower()
    head = sent[w.head - 1] if w.head else None
    kids = lambda h: [x for x in sent if x.head == h.id]
    toks = _tokens(sent); tpos = next(n for n, x in enumerate(toks) if x[1] == i)
    nxt_tok = toks[tpos + 1][0] if tpos + 1 < len(toks) else ""
    prev_tok = toks[tpos - 1][0] if tpos > 0 else ""

    # 1. 'lo que' / 'del que' before the dictionary; fixed multiword entries, longest first
    if t == "lo" and nxt_tok == "que": return _unit("lo que", "what / that which", "lo_que")
    if t == "lo" and w.upos == "DET" and nxt_tok and toks[tpos + 1][2] and sent[toks[tpos + 1][1]].upos == "ADJ":
        return _role("article", "the (+ adjective: the ... thing)")
    ph = _phrase(sent, i) if t != "se" else None
    if ph:
        s0 = tpos - ph[0].split().index(t) if t in ph[0].split() else tpos
        # 'fui a ver si', 'los vas a matar': after ir, 'a' is the motion / going-to 'a', not an idiom
        if ph[0].startswith("a ") and s0 > 0 and toks[s0 - 1][2] == "ir": ph = None
    if ph:
        # 'con todo este ruido': the phrase's last word modifies a noun after it, so it is literal
        last = sent[toks[s0 + ph[1] - 1][1]] if s0 + ph[1] - 1 < len(toks) else None
        if last is not None and last.deprel in ("det", "amod", "nummod") and last.head > last.id: ph = None
    if ph and ph[1] == 2 and ph[0].split()[0] == t and tpos + 1 < len(toks):
        # 'significado da vida' is literal (vida modifies a noun); the idiom 'da vida' (extremely) is not
        nxt_word = sent[toks[tpos + 1][1]]
        if nxt_word.deprel == "nmod" and nxt_word.head and sent[nxt_word.head - 1].upos == "NOUN": ph = None
    if ph and ph[1] >= 2: return _unit(ph[0], PHRASES[ph[0]], "phrase")
    # 2. que
    if t == "que":
        if prev_tok == "lo": return _unit("lo que", "what / that which", "lo_que")
        # spaCy attaches 'tengo que esperar' as cc + conj, so read the frame from the surface
        if tpos > 0 and nxt_tok and "VerbForm=Inf" in (sent[toks[tpos + 1][1]].feats or ""):
            if prev_tok == "hay": return _unit("hay que", "one has to / you have to", "tener_que")
            if toks[tpos - 1][2] == "tener": return _unit("tener que", "have to", "tener_que")
        if prev_tok == "mejor" and tpos >= 2 and toks[tpos - 2][2] == "ser":
            return _unit("mejor que", "(it's) better that / you'd better", "mejor_que")
        if any(x[0] in COMPARATIVE or x[2] in COMPARATIVE for x in toks[max(0, tpos - 4):tpos]) and w.upos in ("SCONJ", "CCONJ", "ADP"):
            return _role("than", "than", "comparative")
        if head is not None and w.deprel == "mark":
            near = ([sent[head.head - 1]] if head.head else []) + kids(head)
            have = next((x for x in near if x.lemma in ("tener", "haber") and x.id < w.id), None)
            if have is not None:
                return _unit("hay que" if have.text.lower() == "hay" else "tener que",
                             "one has to / you have to" if have.text.lower() == "hay" else "have to", "tener_que")
        if "PronType=Rel" in (w.feats or "") or (w.upos == "PRON" and w.deprel != "obj"):
            return _role("relative", "that / which / who", "role")
        if w.upos == "PRON": return _role("relative", "that / which / who", "role")
        return _role("conj_that", "that", "role")
    # 3. verb + governed preposition (tratar de, acordarse de, volver a)
    if t == "de" and prev_tok in ("algo", "nada", "poco", "un poco") : return _unit(prev_tok + " de", "some / a bit of", "quantity_de")
    if (w.upos == "ADP" or w.deprel == "mark") and head is not None and t in PREPS + ("del", "al"):
        p = {"del": "de", "al": "a"}.get(t, t)
        gov = sent[head.head - 1] if head.head else None
        if gov is not None and gov.upos in ("VERB", "AUX", "ADJ"):
            lem = gov.lemma.lower()
            if lem == "ir" and p == "a" and head.upos == "VERB" and "Mood=Imp" not in (gov.feats or ""):  # 've a ver' = go and see
                return _unit("ir a", "going to (+ verb)", "ir_a")
            if lem in LIGHT_VERBS or w.id < gov.id: lem = None  # 'estuvo ... por la mañana'; fronted 'A este libro le faltan'
        if gov is not None and gov.upos in ("VERB", "AUX", "ADJ") and lem:
            if any(k.text.lower() in ("se", "me", "te", "nos", "os") for k in kids(gov)) and lem in PRONOMINAL:
                return _unit(f"{lem}se {p}", PRONOMINAL[lem], "pronominal_verb_frame")
            if f"{lem} {p}" in VERB_FRAMES: return _unit(f"{lem} {p}", VERB_FRAMES[f"{lem} {p}"], "verb_frame")
        if w.deprel == "mark" and t in PREP_GLOSS: return _role("prep", PREP_GLOSS[t] + " (+ verb)")
    # 4. se: pronominal verb, impersonal/passive, indirect 'se lo', reflexive
    if t == "se" and head is not None:
        lem = head.lemma.lower()
        if nxt_tok in ("lo", "la", "los", "las"): return _role("object_pron", "(to) him / her / them (se lo = le lo)")
        if lem in PRONOMINAL: return _unit(lem + "se", PRONOMINAL[lem], "pronominal_verb")
        subj = [k for k in kids(head) if k.deprel.startswith("nsubj")]
        if not subj and "Person=3" in (head.feats or "") and not any(k.deprel == "aux" for k in kids(head)):
            return _role("impersonal_se", "one / (it) is done", "role")
        if head.upos == "VERB" and lem in VERBS:
            return _unit(lem + "se", VERBS[lem] + " (oneself)", "se_verb")
        return _role("reflexive", "himself / herself / themselves", "role")
    if t in ("me", "te", "nos", "os") and head is not None and head.upos == "VERB" and head.lemma.lower() in PRONOMINAL \
            and ("Reflex=Yes" in (w.feats or "") or w.deprel in ("expl", "expl:pv")):
        return _unit(head.lemma.lower() + "se", PRONOMINAL[head.lemma.lower()], "pronominal_verb")
    # si: conjunction 'if' vs 'yes' / 'himself'
    if t == "si" and (w.upos in ("SCONJ", "CCONJ") or w.deprel == "mark"): return _role("conj_if", "if / whether")
    # 5. articles vs object pronouns
    if t in ARTICLE and w.upos == "DET": return _role("article", ARTICLE[t])
    if t in ("lo", "la", "los", "las") and w.upos == "PRON": return _role("object_pron", PRON_GLOSS[t]["*"])
    # 6. prepositions
    if t in CONTRACTION: return _role("prep", CONTRACTION[t])
    if w.upos == "ADP" and t in PREP_GLOSS:
        if t == "a" and head is not None and head.upos in ("PRON", "PROPN", "NOUN") and head.deprel in ("obj", "iobj"):
            return _role("personal_a", "(marks a person as object)")
        return _role("prep", PREP_GLOSS[t])
    # 7. pronouns and determiners
    pd = pron_det(sent, i, t)
    if pd: return pd
    # 8. conjunctions
    if w.upos in ("SCONJ", "CCONJ") or (w.deprel == "mark" and t in CONJ_GLOSS):
        return _role("conj", CONJ_GLOSS.get(t, t))
    return {"kind": "none", "value": None, "gloss": None, "rule": "none"}


def pron_det(sent, i, t):
    w = sent[i]; g = PRON_GLOSS.get(t)
    if g is None or w.upos in ("NOUN", "PROPN", "VERB"): return None
    if w.upos == "ADJ" and t not in ("mismo", "misma", "mismos", "mismas", "propio", "propia", "cierto", "cierta", "tal"):
        return None
    f = w.feats or ""
    out = lambda role, gl=None: {"kind": "role", "value": role, "gloss": gl or g.get(role) or g["*"], "rule": "pron_det"}
    if w.upos == "ADV":
        if t in ADVERBIAL: return out("adverb", ADVERBIAL[t])
        return None
    if t in INDEFINITE: return out("indefinite")
    if t in POSSESSIVE: return out("possessive")
    if t in DEMONSTRATIVE: return out("demonstrative")
    if t in INTERROGATIVE:
        if "PronType=Rel" in f: return out("relative")
        return out("interrogative")
    if t in SUBJECT:
        if w.deprel.startswith("nsubj"): return out("subject_pron", SUBJ_GLOSS.get(t))
        return out("object_pron", OBJ_GLOSS.get(t))
    if t in ("mí", "ti", "tí", "sí", "conmigo", "contigo", "consigo"): return out("object_pron")
    if t in CLITIC:
        if "Reflex=Yes" in f or w.deprel in ("expl", "expl:pv"): return out("reflexive")
        if w.deprel == "iobj": return out("object_pron", {"me": "(to) me", "te": "(to) you", "nos": "(to) us"}.get(t))
        return out("object_pron")
    return out("quantifier")
