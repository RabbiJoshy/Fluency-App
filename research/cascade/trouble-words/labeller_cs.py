"""Rule labeller v0 for Czech function words: Stanza parse + Wiktionary, no WSD.

Same contract as labeller_pt: label(words, i, surface=None). Czech has no articles;
its function words are prepositions (whose meaning follows the case they govern:
'na stole' on, 'na stůl' onto), conjunctions, the reflexive se/si (pronominal verbs:
bát se, dát si) and case-inflected pronouns (mi = to me, mnou = with me). Glosses
for pronouns come from the lemma and the case Stanza reads.
"""
import json, re
KAIKKI = "/Users/joshuathomasamar/PycharmProjects/Fluency-Workspace/raw/wiktionary/enwiktionary-2026-09-06/kaikki.org-dictionary-Czech.jsonl"
from gloss_filter import Glosses
PREPS = ("na", "o", "v", "ve", "s", "se", "z", "ze", "do", "k", "ke", "po", "za", "od", "pro", "u", "před", "přede",
         "mezi", "pod", "při", "přes", "proti", "bez", "beze")
PHRASE_POS = {"phrase", "prep_phrase", "adv", "conj", "intj", "prep", "pron"}


_G = Glosses(KAIKKI)
_clean = _G.clean  # shared: drops entry notes, follows 'spelling of' pointers


VERBS = {}


def _load():
    phrases, pronominal, frames = {}, {}, {}
    global VERBS
    for line in open(KAIKKI):
        e = json.loads(line)
        w = e["word"].lower(); pos = e.get("pos"); senses = e.get("senses", [])
        gl = _clean([g for s in senses for g in s.get("glosses", [])])
        if not gl: continue
        if " " in w and pos in PHRASE_POS: phrases.setdefault(w, gl[0])
        if pos == "verb" and " " not in w:
            VERBS.setdefault(w, re.sub(r"^\([^)]*\)\s*|\s*\[[^\]]*\]", "", gl[0]).strip())
            for sn in senses:
                tags = sn.get("tags", [])
                for raw in sn.get("raw_glosses") or sn.get("glosses", []):
                    clean = re.sub(r"^\([^)]*\)\s*|\s*\[[^\]]*\]", "", raw).strip()
                    for prep in re.findall(r"\[with (?:[^\]]*?\b)?(na|o|v|s|z|do|k|po|za|od|pro|u|před|mezi|pod|při|přes)\b", raw):
                        if clean: frames.setdefault(f"{w} {prep}", clean)
                    if ("reflexive" in tags or "pronominal" in tags) and clean:
                        refl = "si" if re.search(r"\bsi\b", raw) else "se"
                        pronominal.setdefault((w, refl), clean)
    return phrases, pronominal, frames


PHRASES, PRONOMINAL, FRAMES = _load()
# Wiktionary marks these 'used other than figuratively or idiomatically', so gloss_filter drops them;
# in running text the idiom dominates, so they are kept (hand-checked on deck sentences, 2026-10-13).
IDIOMS = set()
PHRASES.update({w: _G.idiom[w] for w in IDIOMS if w in _G.idiom})
BY_TOKEN = {}
for p in PHRASES:
    for t in p.split(): BY_TOKEN.setdefault(t, []).append(p)

# Preposition glosses by the case of the noun they govern; "*" when the case does not decide.
PREP_GLOSS = {
    "v": {"Loc": "in / at", "Acc": "on (a day) / in", "*": "in"}, "na": {"Loc": "on / at", "Acc": "onto / for / to", "*": "on / to"},
    "s": {"Ins": "with", "Gen": "off / down from", "*": "with"}, "z": {"*": "from / out of / of"},
    "do": {"*": "into / to / until"}, "k": {"*": "to / towards"}, "o": {"Loc": "about", "Acc": "about / for / by", "*": "about"},
    "po": {"Loc": "after / around / along", "Acc": "up to / for", "*": "after"}, "za": {"Ins": "behind / to (see)", "Acc": "for / in (time)",
    "Gen": "during", "*": "for / behind"}, "od": {"*": "from / since"}, "pro": {"*": "for"}, "u": {"*": "at / by / near"},
    "před": {"Ins": "in front of / before / ago", "Acc": "in front of (motion)", "*": "before"},
    "mezi": {"*": "between / among"}, "pod": {"*": "under"}, "při": {"*": "during / at / by"}, "přes": {"*": "across / over / via"},
    "proti": {"*": "against / opposite"}, "bez": {"*": "without"}, "díky": {"*": "thanks to"}, "kvůli": {"*": "because of"},
    "místo": {"*": "instead of"}, "podle": {"*": "according to / by"}, "během": {"*": "during"}, "kolem": {"*": "around / past"},
    "okolo": {"*": "around"}, "mimo": {"*": "except / outside"}, "uprostřed": {"*": "in the middle of"}, "blízko": {"*": "near"},
    "poblíž": {"*": "near"}, "pomocí": {"*": "by means of"}, "vůči": {"*": "towards / with respect to"}, "jménem": {"*": "on behalf of"},
    "nad": {"*": "above / over"}, "skrz": {"*": "through"}, "ku": {"*": "to / towards"}, "vo": {"*": "about (colloquial o)"},
    "stran": {"*": "concerning"}, "zač": {"*": "for what"},
}
PREP_ALIAS = {"ve": "v", "se": "s", "ze": "z", "ke": "k", "přede": "před", "beze": "bez", "ode": "od", "ku": "k"}
CONJ_GLOSS = {
    "a": "and", "že": "that", "ale": "but", "nebo": "or", "anebo": "or", "když": "when / if", "jestli": "if / whether",
    "jestliže": "if", "pokud": "if / as long as", "protože": "because", "aby": "so that / to", "abych": "so that I / to",
    "abys": "so that you", "abychom": "so that we", "abysme": "so that we", "abyste": "so that you (plural)",
    "kdyby": "if (would)", "kdybych": "if I (were / did)", "kdybys": "if you (were / did)", "kdybychom": "if we (were / did)",
    "kdybysme": "if we (were / did)", "kdybyste": "if you (were / did)", "než": "than / before", "až": "until / when / as late as",
    "ani": "not even / nor", "i": "and / even / also", "však": "however", "ať": "let / may / whether", "buď": "either",
    "zda": "whether", "či": "or", "totiž": "you see / namely", "ovšem": "of course / however", "zatímco": "while",
    "ačkoliv": "although", "vždyť": "after all", "dyť": "after all", "jakoby": "as if", "leda": "unless / only",
    "jak": "how / as", "kde": "where", "kdy": "when", "plus": "plus", "an": "while / since", "nikoliv": "not (rather)",
}
# Pronoun lemmas: (subject gloss, object gloss); the case adds 'to' (dative) or 'with' (instrumental).
PERSONAL = {"já": ("I", "me"), "ty": ("you", "you"), "on": ("he / it", "him / it"), "ona": ("she / it", "her / it"),
            "ono": ("it", "it"), "my": ("we", "us"), "vy": ("you (plural / formal)", "you (plural / formal)"),
            "oni": ("they", "them"), "ony": ("they", "them"), "se": ("oneself", "oneself"), "sebe": ("oneself", "oneself")}
POSSESSIVE = {"můj": "my / mine", "tvůj": "your / yours", "svůj": "one's own (my, your, his...)", "náš": "our / ours",
              "váš": "your / yours (plural / formal)", "jeho": "his / its", "její": "her / hers", "jejich": "their / theirs",
              "jehož": "whose", "jejíž": "whose", "jejichž": "whose"}
DEMONSTRATIVE = {"ten": "that / this / the", "tento": "this", "tenhle": "this", "tamten": "that (over there)", "onen": "that"}
RELATIVE = {"který": "which / who / that", "jaký": "what (kind of)", "čí": "whose", "jenž": "who / which", "co": "what / that",
            "kdo": "who", "kolik": "how many / how much", "cože": "what?!", "kdokoliv": "anyone / whoever", "jakýkoliv": "any"}
QUANT = {"všechen": "all / everything / everyone", "vše": "everything", "všechno": "everything", "všecko": "everything",
         "každý": "each / every / everyone", "žádný": "no / none / not any", "nic": "nothing", "něco": "something",
         "nějaký": "some / any", "někdo": "someone", "nikdo": "nobody", "sám": "alone / (one)self / by oneself",
         "samotný": "alone / itself", "mnoho": "many / much", "moc": "a lot", "více": "more", "víc": "more", "nejvíce": "most",
         "tolik": "so much / so many", "oba": "both", "jeden": "one / a", "ničí": "nobody's"}
SUBJ_FORMS = {"já": "I", "ty": "you", "on": "he / it", "ona": "she / it", "ono": "it", "my": "we",
              "vy": "you (plural / formal)", "oni": "they", "ony": "they"}
CASE_PREFIX = {"Dat": "(to) ", "Ins": "(with / by) "}
# Unambiguous pronoun forms, read from the surface: the parser tags 'tebou' and 'tobě' as nouns.
FORMS = {
    "mě": ("object_pron", "me"), "mne": ("object_pron", "me"), "mi": ("object_pron", "(to) me"), "mně": ("object_pron", "(to) me"),
    "mnou": ("object_pron", "(with) me"), "tě": ("object_pron", "you"), "tebe": ("object_pron", "you"),
    "tobě": ("object_pron", "(to) you"), "tebou": ("object_pron", "(with) you"), "ho": ("object_pron", "him / it"),
    "mu": ("object_pron", "(to) him"), "něj": ("object_pron", "him / it"), "něho": ("object_pron", "him / it"),
    "jemu": ("object_pron", "(to) him"), "němu": ("object_pron", "(to) him"), "jej": ("object_pron", "him / it"),
    "ním": ("object_pron", "(with) him / it"), "ji": ("object_pron", "her"), "ni": ("object_pron", "her"),
    "ní": ("object_pron", "her"), "nás": ("object_pron", "us"), "nám": ("object_pron", "(to) us"),
    "námi": ("object_pron", "(with) us"), "vás": ("object_pron", "you (plural / formal)"),
    "vám": ("object_pron", "(to) you (plural / formal)"), "vámi": ("object_pron", "(with) you (plural / formal)"),
    "váma": ("object_pron", "(with) you (plural, colloquial)"), "jim": ("object_pron", "(to) them"),
    "nim": ("object_pron", "(to) them"), "jich": ("object_pron", "them / of them"), "nich": ("object_pron", "them / of them"),
    "jimi": ("object_pron", "(with) them"), "nimi": ("object_pron", "(with) them"), "jima": ("object_pron", "(with) them"),
    "nima": ("object_pron", "(with) them"), "ně": ("object_pron", "them"), "sebe": ("reflexive", "oneself"),
    "sobě": ("reflexive", "(to) oneself"), "sebou": ("reflexive", "(with) oneself"),
    "sám": ("quantifier", "alone / by oneself / -self"), "sama": ("quantifier", "alone / by oneself / -self"),
    "sami": ("quantifier", "alone / by themselves"), "samo": ("quantifier", "by itself"), "samy": ("quantifier", "alone / by themselves"),
    "všema": ("quantifier", "(with) all"), "všecko": ("quantifier", "everything"), "cože": ("interrogative", "what?!"),
    "tys": ("subject_pron", "you (are / did) (ty + jsi)"), "žes": ("conj", "that you (že + jsi)"),
    "cos": ("relative", "what you (co + jsi)"), "jaks": ("interrogative", "how you (jak + jsi)"),
    "vo": ("prep", "about (colloquial o)"), "dyť": ("conj", "after all (vždyť)"), "ničí": ("possessive", "nobody's"),
    "tamto": ("demonstrative", "that (over there)"),
}


def _unit(value, gloss, rule):
    return {"kind": "unit", "value": value, "gloss": gloss, "rule": rule}


def _role(value, gloss, rule="role"):
    return {"kind": "role", "value": value, "gloss": gloss, "rule": rule}


def _feat(w, name):
    m = re.search(name + r"=(\w+)", w.feats or "")
    return m.group(1) if m else None


def _phrase(sent, i):
    toks = [x.text.lower() for x in sent]
    best = None
    for p in BY_TOKEN.get(toks[i], []):
        parts = p.split(); n = len(parts)
        for k, part in enumerate(parts):
            if part != toks[i]: continue
            s = i - k
            if s < 0 or s + n > len(toks): continue
            if all(parts[j] in (toks[s + j], sent[s + j].lemma.lower()) for j in range(n)):
                if best is None or n > best[1]: best = (p, n)
    return best


def label(sent, i, surface=None):
    w = sent[i]; t = (surface or w.text).lower(); lem = (w.lemma or t).lower()
    head = sent[w.head - 1] if w.head else None
    kids = lambda h: [x for x in sent if x.head == h.id]
    # 1. fixed multiword entries (not for se/si, which go to their verb)
    ph = _phrase(sent, i) if t not in ("se", "si", "ses", "sis") else None
    if ph and ph[1] >= 2: return _unit(ph[0], PHRASES[ph[0]], "phrase")
    # ses / sis = se / si + jsi ('proč ses smál' = why did you laugh): take the pronominal verb if there is one
    if t in ("ses", "sis"):
        refl = t[:2]
        for v in sent:
            if v.upos == "VERB" and (v.lemma.lower(), refl) in PRONOMINAL:
                return _unit(f"{v.lemma.lower()} {refl}", PRONOMINAL[(v.lemma.lower(), refl)], "pronominal_verb")
        return _role("reflexive", "yourself (" + refl + " + jsi)")
    if t in FORMS and w.upos not in ("VERB", "AUX"):
        role, gloss = FORMS[t]
        return {"kind": "role", "value": role, "gloss": gloss, "rule": "form"}
    # 2. reflexive se / si: pronominal verb, else reflexive or passive
    if t in ("se", "si", "ses", "sis") and w.upos in ("PRON", "PART") and head is not None:
        refl = "si" if t.startswith("si") else "se"
        v = head.lemma.lower() if head.upos in ("VERB", "AUX") else None
        if v and (v, refl) in PRONOMINAL: return _unit(f"{v} {refl}", PRONOMINAL[(v, refl)], "pronominal_verb")
        if w.deprel == "expl:pass": return _role("impersonal_se", "(is done) / one", "role")
        # Czech se/si mostly belongs to the verb (vrátit se, promluvit si): teach the pair
        if v and v in VERBS: return _unit(f"{v} {refl}", VERBS[v], "se_verb")
        if refl == "si": return _role("reflexive", "(for) oneself", "role")
        return _role("reflexive", "oneself / each other", "role")
    # 3. je: 'is' or 'them / it'
    if t == "je":
        if w.upos == "AUX" or lem == "být": return _role("copula", "is")
        return _role("object_pron", "them / it")
    if t == "by" and (w.upos == "AUX" or lem == "být"): return _role("conditional", "would")
    if t == "ne" and w.upos in ("PART", "INTJ", "ADV"): return _role("negation", "no / not")
    # 4. prepositions, glossed by the case they govern; verb + preposition frames (čekat na)
    base = PREP_ALIAS.get(t, t)
    if w.upos == "ADP" and base in PREP_GLOSS:
        if head is not None and head.head:
            gov = sent[head.head - 1]
            if gov.upos == "VERB" and f"{gov.lemma.lower()} {base}" in FRAMES:
                return _unit(f"{gov.lemma.lower()} {base}", FRAMES[f"{gov.lemma.lower()} {base}"], "verb_frame")
        case = _feat(head, "Case") if head is not None else None
        g = PREP_GLOSS[base]
        return _role("prep", g.get(case) or g["*"])
    # 5. pronouns and determiners
    pd = pron_det(sent, i, t, lem)
    if pd: return pd
    # 6. conjunctions and question/relative adverbs
    if t in CONJ_GLOSS and w.upos in ("SCONJ", "CCONJ", "ADV", "PART", "AUX", "ADP"):
        if t in ("jak", "kde", "kdy") and sent[-1].text == "?" and i == 0: return _role("interrogative", CONJ_GLOSS[t])
        return _role("conj", CONJ_GLOSS[t])
    return {"kind": "none", "value": None, "gloss": None, "rule": "none"}


def pron_det(sent, i, t, lem):
    w = sent[i]
    if w.upos not in ("PRON", "DET", "NUM", "ADJ", "ADV"): return None
    case = _feat(w, "Case"); has_prep = any(x.head == w.id and x.upos == "ADP" for x in sent)
    prefix = "" if has_prep else CASE_PREFIX.get(case, "")
    out = lambda role, gloss: {"kind": "role", "value": role, "gloss": gloss, "rule": "pron_det"}
    if _feat(w, "Poss") == "Yes" or lem in POSSESSIVE:
        if lem in POSSESSIVE: return out("possessive", POSSESSIVE[lem])
    if lem in PERSONAL and w.upos == "PRON":
        if lem in ("se", "sebe"): return out("reflexive", prefix + "oneself")
        if t in SUBJ_FORMS and case in ("Nom", None): return out("subject_pron", SUBJ_FORMS[t])
        if lem == "on" and _feat(w, "Gender") == "Fem": lem = "ona"   # Stanza lemmatises jí, ní to 'on'
        if lem == "on" and _feat(w, "Number") == "Plur": lem = "oni"
        subj, obj = PERSONAL[lem]
        if w.deprel.startswith("nsubj") or case == "Nom": return out("subject_pron", subj)
        return out("object_pron", prefix + obj)
    if lem in DEMONSTRATIVE:
        if t in ("tu",) and w.upos == "ADV": return None
        return out("demonstrative", DEMONSTRATIVE[lem])
    if lem in RELATIVE:
        # a question word opens its sentence (after any preposition); elsewhere it introduces a clause
        first = next((x for x in sent if x.upos not in ("PUNCT", "ADP")), None)
        if first is w or _feat(w, "PronType") == "Int" and first is not None and first.id > w.id: return out("interrogative", RELATIVE[lem])
        return out("relative", RELATIVE[lem])
    if lem in QUANT: return out("quantifier", QUANT[lem])
    return None
