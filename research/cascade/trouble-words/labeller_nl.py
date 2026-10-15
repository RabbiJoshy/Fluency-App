"""Rule labeller v0 for Dutch function words: parser + dictionary, no WSD.

label(sentence, target_span) -> {"kind": unit|role|none, "value": ..., "gloss": ..., "rule": ...}
Order: fixed multiword entry (Wiktionary) > split particle -> joined verb > er rules >
te / aan het / om te > grammar role from Stanza UPOS/deprel > none.
"""
import json, re
KAIKKI = "/Users/joshuathomasamar/PycharmProjects/Fluency-Workspace/raw/wiktionary/enwiktionary-2026-09-09/kaikki.org-dictionary-Dutch.jsonl"
from gloss_filter import Glosses
_G = Glosses(KAIKKI)
_clean = _G.clean  # shared: drops entry notes, follows 'spelling of' pointers
PHRASE_POS = {"phrase", "prep_phrase", "adv", "particle", "conj", "intj", "prep"}

def _load():
    verbs, phrases, forms = {}, {}, {}
    for line in open(KAIKKI):
        e = json.loads(line)
        if e.get("pos") == "verb" and " " not in e["word"]:
            for f in e.get("forms", []):
                forms.setdefault(f.get("form", "").lower(), e["word"].lower())
        gl = _clean(g for s in e.get("senses", []) for g in s.get("glosses", []))
        if not gl: continue
        w = e["word"].lower()
        if e.get("pos") == "verb" and " " not in w: verbs.setdefault(w, gl[0])
        if " " in w and e.get("pos") in PHRASE_POS: phrases.setdefault(w, gl[0])
    # grammatical frames Wiktionary lists without a usable gloss
    phrases.update({"aan het": "be ...-ing (in progress)", "om te": "in order to"})
    return verbs, phrases, forms
VERBS, PHRASES, FORMS = _load()
# Wiktionary marks these 'used other than figuratively or idiomatically', so gloss_filter drops them;
# in running text the idiom dominates, so they are kept (hand-checked on deck sentences, 2026-10-13).
IDIOMS = {"des te meer"}  # "aan het" has a handwritten gloss in _load
PHRASES.update({w: _G.idiom[w] for w in IDIOMS if w in _G.idiom})
BY_TOKEN = {}
for p in PHRASES:
    for t in p.split(): BY_TOKEN.setdefault(t, []).append(p)
MODAL_AUX = {"zijn", "worden", "hebben", "moeten", "kunnen", "willen", "mogen", "zullen", "gaan", "laten"}
INDEF = {"iets", "niets", "niks", "iemand", "niemand", "wat", "veel", "weinig", "genoeg"}
PREP_GLOSS = {"op": "on / at", "aan": "at / on / to", "van": "of / from", "voor": "for / before", "in": "in", "met": "with",
              "bij": "at / near / with", "naar": "to / towards", "tegen": "against / to", "tot": "until / to", "door": "through / by",
              "over": "about / over", "uit": "out of / from", "om": "around / at", "na": "after", "zonder": "without",
              "tussen": "between", "onder": "under / among", "boven": "above", "achter": "behind", "naast": "next to",
              "sinds": "since", "vanaf": "from", "binnen": "inside / within", "buiten": "outside", "langs": "along / past"}
CONJ_GLOSS = {"dat": "that", "als": "if / when / as", "dan": "than", "zoals": "like / as", "omdat": "because",
              "voordat": "before", "tot": "until", "toen": "when", "terwijl": "while", "of": "whether / or", "want": "because",
              "maar": "but", "en": "and", "door": "by (doing)", "voor": "before", "wanneer": "when", "nadat": "after", "zodat": "so that"}

# Pronouns and determiners: role from Stanza features, gloss from this table (role -> gloss, "*" = any role).
PRON_GLOSS = {
    "ik": {"*": "I"}, "jij": {"*": "you"}, "je": {"possessive": "your", "reflexive": "yourself", "*": "you"},
    "jou": {"*": "you"}, "jouw": {"*": "your"}, "u": {"reflexive": "yourself", "*": "you (formal)"}, "uw": {"*": "your (formal)"},
    "hij": {"*": "he"}, "ie": {"*": "he"}, "hem": {"*": "him / it"}, "'m": {"*": "him / it"},
    "zij": {"subject_pron": "she / they", "*": "her / them"}, "ze": {"subject_pron": "she / they", "*": "her / them"},
    "haar": {"possessive": "her", "*": "her"}, "hun": {"possessive": "their", "*": "them"}, "hen": {"*": "them"},
    "me": {"possessive": "my", "reflexive": "myself", "*": "me"}, "mij": {"reflexive": "myself", "*": "me"}, "mijn": {"*": "my"},
    "ons": {"possessive": "our", "reflexive": "ourselves", "*": "us"}, "onze": {"*": "our"}, "jullie": {"possessive": "your (plural)", "*": "you (plural)"},
    "z'n": {"*": "his / its"}, "zich": {"*": "himself / herself / themselves"}, "zichzelf": {"*": "himself / herself / themselves"},
    "men": {"*": "one / people"}, "d'r": {"possessive": "her", "*": "her / there"}, "gij": {"*": "you (archaic)"},
    "zijne": {"*": "his"}, "hare": {"*": "hers"}, "haren": {"*": "hers"}, "mijnen": {"*": "mine"},
    "die": {"relative": "who / that", "demonstrative": "that / those", "*": "that one / he / she"},
    "deze": {"*": "this / these"}, "dit": {"*": "this"}, "dien": {"*": "that"}, "gene": {"*": "that (one)"},
    "wat": {"interrogative": "what", "relative": "what / which", "quantifier": "some / a bit of", "indefinite": "something", "*": "what"},
    "wie": {"relative": "who / whom", "*": "who"}, "welke": {"*": "which"}, "welk": {"*": "which"}, "hoeveel": {"*": "how much / how many"},
    "wiens": {"*": "whose"}, "dier": {"*": "of those"},
    "iets": {"*": "something"}, "niets": {"*": "nothing"}, "niks": {"*": "nothing"}, "iemand": {"*": "someone"},
    "zoiets": {"*": "something like that"}, "geen": {"*": "no / not a"}, "alle": {"*": "all"}, "allen": {"*": "all (of them)"},
    "allemaal": {"*": "all (of them)"}, "elk": {"*": "each / every"}, "ieder": {"*": "each / every"}, "iedere": {"*": "each / every"},
    "veel": {"*": "much / many / a lot"}, "vele": {"*": "many"}, "weinig": {"*": "little / few"}, "meer": {"*": "more"},
    "minder": {"*": "less / fewer"}, "meest": {"*": "most"}, "meeste": {"*": "most"}, "meesten": {"*": "most (people)"},
    "genoeg": {"*": "enough"}, "voldoende": {"*": "enough"}, "zoveel": {"*": "so much / so many"}, "evenveel": {"*": "as much / as many"},
    "sommige": {"*": "some"}, "sommigen": {"*": "some (people)"}, "enkele": {"*": "a few / some"}, "meerdere": {"*": "several"},
    "beide": {"*": "both"}, "beiden": {"*": "both"}, "allebei": {"*": "both"}, "ander": {"*": "other"}, "anderen": {"*": "others"},
    "hetzelfde": {"*": "the same"}, "dezelfde": {"*": "the same"}, "zelfde": {"*": "same"}, "zo'n": {"*": "such a"},
    "dergelijke": {"*": "such"}, "allerlei": {"*": "all kinds of"}, "eén": {"*": "one"}, "èèn": {"*": "one"}, "ene": {"*": "the one / one"},
    "enige": {"only": "only", "*": "some / any"}, "enig": {"only": "only", "*": "some / any"}, "enigen": {"only": "the only ones", "*": "some (people)"},
    "der": {"*": "of the"}, "des": {"*": "of the"}, "den": {"*": "the"},
}
QUANT = {"geen", "alle", "allen", "allemaal", "elk", "ieder", "iedere", "veel", "vele", "weinig", "meer", "minder", "meest", "meeste",
         "meesten", "genoeg", "voldoende", "zoveel", "evenveel", "sommige", "sommigen", "enkele", "meerdere", "beide", "beiden",
         "allebei", "ander", "anderen", "hetzelfde", "dezelfde", "zelfde", "zo'n", "dergelijke", "allerlei", "eén", "èèn", "ene",
         "enige", "enig", "enigen"}
INDEF_PRON = {"iets", "niets", "niks", "iemand", "zoiets", "men"}
ARCHAIC_ART = {"der", "des", "den"}

def pron_det(sent, i):
    """Role + gloss for a pronoun or determiner; None when the form is not in the table."""
    w = sent[i]; t = w.text.lower().replace("\u2019", "'"); g = PRON_GLOSS.get(t)
    # homographs: 'dier' animal, 'haren' hair, 'mijnen' mines, 'Gene' a name
    if g is None or w.upos in ("NOUN", "PROPN", "VERB"): return None
    f = w.feats or ""; head = sent[w.head - 1] if w.head else None
    def out(role, gl=None):
        return {"kind": "role", "value": role, "gloss": gl or g.get(role) or g["*"], "rule": "pron_det"}
    if t in ARCHAIC_ART: return out("article")
    if t == "d'r" and "Poss=Yes" not in f and w.deprel != "nmod:poss": return out("locative_er", "there (= er)")
    if t in ("enige", "enig", "enigen") and i > 0 and sent[i - 1].text.lower() in ("de", "het", "mijn", "zijn", "onze", "hun"):
        return out("quantifier", g["only"])
    if t == "meer" and any(x.text.lower() in ("geen", "niet", "nooit", "niemand", "niets", "niks") for x in sent[:i]) \
            and not (i + 1 < len(sent) and sent[i + 1].upos in ("NOUN", "ADJ", "ADV")):
        return out("adverb", "anymore / no longer")
    if t in ("enkele", "enkel") and i > 0 and sent[i - 1].text.lower() == "geen": return out("quantifier", "single (not a single)")
    if t in QUANT: return out("quantifier")
    if t in INDEF_PRON: return out("indefinite")
    if t == "wat":
        if w.upos == "DET": return out("quantifier")
        if "PronType=Ind" in f: return out("indefinite")
        if "PronType=Rel" in f or (i > 0 and sent[i - 1].text.lower() in ("alles", "niets", "iets", "dat", "niet", "het")): return out("relative")
        return out("interrogative")
    if t in ("wie", "welke", "welk", "hoeveel", "wiens"):
        if "PronType=Rel" in f or (i > 0 and sent[i - 1].upos == "ADP" and i > 1 and sent[i - 2].upos in ("NOUN", "PRON")): return out("relative")
        return out("interrogative")
    if t in ("die", "deze", "dit", "dien", "gene", "dier"):
        if "PronType=Rel" in f: return out("relative")
        return out("demonstrative")
    if "Poss=Yes" in f or w.deprel == "nmod:poss" or t in ("mijn", "jouw", "uw", "onze", "z'n", "zijne", "hare", "haren", "mijnen"):
        return out("possessive")
    if t in ("zich", "zichzelf"): return out("reflexive")
    if ("Reflex=Yes" in f or w.deprel == "expl:pv") and head is not None:
        # 'me' is only 'myself' when the clause's subject is the same person ('ik schaam me', not 'jullie geloofden me')
        person = re.search(r"Person=(\d)", f)
        subj = [k for k in sent if k.head == head.id and k.deprel.startswith("nsubj")]
        if not subj and head.head:  # 'je moet je haasten': the subject hangs on the modal
            subj = [k for k in sent if k.head == head.head and k.deprel.startswith("nsubj")]
        if person and subj and re.search(r"Person=(\d)", subj[0].feats or "") and \
                re.search(r"Person=(\d)", subj[0].feats).group(1) == person.group(1):
            return out("reflexive")
    if w.deprel.startswith("nsubj") or w.deprel == "expl":
        if t in ("ze", "zij") and head is not None:
            verb = next((k for k in sent if k.head == head.id and k.upos == "AUX" and "Number=" in (k.feats or "")), head)
            num = re.search(r"Number=(\w+)", verb.feats or "")
            if num: return out("subject_pron", "she" if num.group(1) == "Sing" else "they")
        return out("subject_pron")
    return out("object_pron")

def _phrase(words, i):
    best = None
    for p in BY_TOKEN.get(words[i].text.lower(), []):
        toks = p.split(); n = len(toks)
        for k, t in enumerate(toks):
            if t != words[i].text.lower(): continue
            s = i - k
            if s < 0 or s + n > len(words): continue
            if all(toks[j] in (words[s + j].text.lower(), words[s + j].lemma.lower()) for j in range(n)):
                if best is None or n > best[1]: best = (p, n)
    return best

def label(sent, i):
    """sent: list of stanza words for one sentence; i: index of the target word."""
    w = sent[i]; t = w.text.lower(); head = sent[w.head - 1] if w.head else None
    kids = lambda h: [x for x in sent if x.head == h.id]
    # 1. fixed multiword entries (longest)
    ph = _phrase(sent, i)
    if ph and ph[1] >= 2:
        if ph[0] == "aan het" and not (i + 2 < len(sent) and sent[i + 2].upos in ("VERB", "AUX")): ph = None
        elif ph[0] == "om te": ph = None  # handled with te below
        if ph: return {"kind": "unit", "value": ph[0], "gloss": PHRASES[ph[0]], "rule": "phrase"}
    # 2. split particle -> joined verb
    nxt = sent[i + 1] if i + 1 < len(sent) else None
    if w.deprel == "compound:prt" and nxt is not None and nxt.upos in ("DET", "NOUN", "PROPN", "PRON") and nxt.head != w.head:
        w_is_prep = True  # 'ging schaatsen op het meer': a particle is not followed by its own noun phrase
    else:
        w_is_prep = False
    if w_is_prep:
        return {"kind": "role", "value": "prep", "gloss": PREP_GLOSS.get(t, t), "rule": "particle_reread_as_prep"}
    if w.deprel == "compound:prt" and head is not None and not w_is_prep:
        lemma = head.lemma.replace("_", "").lower()
        if (lemma if lemma.startswith(t) else t + lemma) not in VERBS:
            lemma = FORMS.get(head.text.lower(), lemma)
        if any(k.text.lower() == "er" for k in kids(head)) and ("er" + t + lemma) in VERBS:
            return {"kind": "unit", "value": "er" + t + lemma, "gloss": VERBS["er" + t + lemma], "rule": "er_particle_verb"}
        comp = lemma if lemma.startswith(t) else t + lemma
        if comp in VERBS: return {"kind": "unit", "value": comp, "gloss": VERBS[comp], "rule": "particle_verb"}
        if lemma in MODAL_AUX: return {"kind": "role", "value": "adverb", "gloss": t, "rule": "particle_on_aux"}
        return {"kind": "unit", "value": comp, "gloss": None, "rule": "particle_verb_unglossed"}
    # 3. er
    if t == "er":
        own = [k for k in kids(w) if k.upos == "ADP"]
        if own and head is not None:
            for lem in (head.lemma.replace("_", "").lower(), FORMS.get(head.text.lower(), "")):
                v = "er" + own[0].text.lower() + lem
                if v in VERBS: return {"kind": "unit", "value": v, "gloss": VERBS[v], "rule": "er_prep_verb"}
            return {"kind": "role", "value": "pronominal_adverb", "gloss": f"{own[0].text.lower()} it", "rule": "er_own_prep"}
        if head is not None:
            prt = [k for k in sent if k.deprel == "compound:prt"]
            for p in prt:
                ph = sent[p.head - 1]
                for lem in (ph.lemma.replace("_", "").lower(), FORMS.get(ph.text.lower(), "")):
                    v = "er" + p.text.lower() + lem
                    if v in VERBS: return {"kind": "unit", "value": v, "gloss": VERBS[v], "rule": "er_particle_verb"}
            stranded = [k for k in kids(head) if k.upos == "ADP" and k.deprel != "case" and k.id > w.id and not kids(k)]
            objs = [k for k in kids(head) if k.deprel == "obj" and (k.upos == "NUM" or k.lemma.lower() in ("een", "geen", "veel", "meer", "twee", "drie"))]
            if objs and not stranded:
                return {"kind": "role", "value": "partitive_er", "gloss": "of them", "rule": "er_partitive"}
            if stranded:
                return {"kind": "role", "value": "pronominal_adverb", "gloss": f"{stranded[0].text.lower()} it", "rule": "er_stranded_prep"}
            subj = [k for k in kids(head) if k.deprel.startswith("nsubj")]
            pas = any(k.deprel == "aux:pass" for k in kids(head))
            if pas or not subj or any(s.upos == "NOUN" and not any(d.lemma == "de" or d.lemma == "het" for d in kids(s)) or s.lemma.lower() in INDEF for s in subj):
                return {"kind": "role", "value": "existential_er", "gloss": "there (is/are)", "rule": "er_existential"}
        return {"kind": "role", "value": "locative_er", "gloss": "there", "rule": "er_locative"}
    # 4. te
    if t == "te":
        if w.deprel == "mark": return {"kind": "role", "value": "infinitive_to", "gloss": "to (+ verb)", "rule": "te_infinitive"}
        if head is not None and head.upos in ("ADJ", "ADV"): return {"kind": "role", "value": "degree_too", "gloss": "too", "rule": "te_degree"}
    # 5. grammar roles
    if t == "zijn":
        if w.upos in ("PRON", "DET"): return {"kind": "role", "value": "possessive", "gloss": "his / its", "rule": "role"}
        if w.deprel == "aux:pass": return {"kind": "role", "value": "aux_passive", "gloss": "been (passive)", "rule": "role"}
        if w.deprel == "aux": return {"kind": "role", "value": "aux_perfect", "gloss": "have (perfect)", "rule": "role"}
        if w.deprel == "cop": return {"kind": "role", "value": "copula", "gloss": "be", "rule": "role"}
        return {"kind": "role", "value": "be", "gloss": "be / exist", "rule": "role"}
    pd = pron_det(sent, i)
    if pd: return pd
    if w.upos == "DET" and t in ("de", "het", "een", "'t", "'n"): return {"kind": "role", "value": "article", "gloss": "the" if t != "een" else "a", "rule": "role"}
    if t in ("het", "'t") and w.upos == "PRON":
        return {"kind": "role", "value": "subject_pron" if w.deprel.startswith("nsubj") or w.deprel == "expl" else "object_pron", "gloss": "it", "rule": "role"}
    if t == "dat":
        if w.upos == "SCONJ" or w.deprel == "mark": return {"kind": "role", "value": "conj_that", "gloss": "that", "rule": "role"}
        if head is not None and head.deprel == "acl:relcl" and (w.feats or "").find("PronType=Rel") >= 0:
            return {"kind": "role", "value": "relative", "gloss": "that / which", "rule": "role"}
        return {"kind": "role", "value": "demonstrative", "gloss": "that", "rule": "role"}
    if w.upos == "ADP" and (w.deprel != "case" or (head is not None and head.text.lower() in ("er", "daar", "hier", "waar"))) and not kids(w) and any(x.text.lower() in ("er", "daar", "hier", "waar") and x.id < w.id for x in sent):
        return {"kind": "role", "value": "pronominal_adverb", "gloss": f"{t} it", "rule": "stranded_prep"}
    if t == "om" and any(x.text.lower() == "te" and x.id > w.id and x.deprel == "mark" for x in sent):
        return {"kind": "unit", "value": "om te", "gloss": "in order to", "rule": "om_te"}
    if w.upos in ("SCONJ", "CCONJ") or w.deprel == "mark":
        value = {"dat": "conj_that", "voor": "conj_before", "als": "conj_if", "of": "conj_if"}.get(t, "conj")
        return {"kind": "role", "value": value, "gloss": CONJ_GLOSS.get(t, t), "rule": "role"}
    if w.upos == "ADP" and w.deprel in ("case", "obl", "nmod", "root", "xcomp", "fixed"):
        return {"kind": "role", "value": "prep", "gloss": PREP_GLOSS.get(t, t), "rule": "role"}
    return {"kind": "none", "value": None, "gloss": None, "rule": "none"}
