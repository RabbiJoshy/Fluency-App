"""Rule labeller v0 for Dutch function words: parser + dictionary, no WSD.

label(sentence, target_span) -> {"kind": unit|role|none, "value": ..., "gloss": ..., "rule": ...}
Order: fixed multiword entry (Wiktionary) > split particle -> joined verb > er rules >
te / aan het / om te > grammar role from Stanza UPOS/deprel > none.
"""
import json, re
KAIKKI = "/Users/joshuathomasamar/PycharmProjects/Fluency-Workspace/raw/wiktionary/enwiktionary-2026-09-09/kaikki.org-dictionary-Dutch.jsonl"
PHRASE_POS = {"phrase", "prep_phrase", "adv", "particle", "conj", "intj", "prep"}

def _load():
    verbs, phrases, forms = {}, {}, {}
    for line in open(KAIKKI):
        e = json.loads(line)
        if e.get("pos") == "verb" and " " not in e["word"]:
            for f in e.get("forms", []):
                forms.setdefault(f.get("form", "").lower(), e["word"].lower())
        gl = [g for s in e.get("senses", []) for g in s.get("glosses", [])
              if "form of" not in g and "inflection of" not in g and "Used other than" not in g]
        if not gl: continue
        w = e["word"].lower()
        if e.get("pos") == "verb" and " " not in w: verbs.setdefault(w, gl[0])
        if " " in w and e.get("pos") in PHRASE_POS: phrases.setdefault(w, gl[0])
    # grammatical frames Wiktionary lists without a usable gloss
    phrases.update({"aan het": "be ...-ing (in progress)", "om te": "in order to"})
    return verbs, phrases, forms
VERBS, PHRASES, FORMS = _load()
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
