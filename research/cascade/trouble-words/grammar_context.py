"""Context checks shared by the audited Spanish and Portuguese labellers.

Dictionary membership proposes a construction; it never establishes its use.
These checks use syntax and token boundaries, rather than sentence exceptions.
"""
import re


def feat(word, key):
    for item in (word.feats or "").split("|"):
        if item.startswith(key + "="):
            return set(item.split("=", 1)[1].split(","))
    return set()


def children(words, word):
    return [x for x in words if x.head == word.id and x.id != word.id]


def phrase_is_literal(words, tokens, target_pos, phrase, kinds):
    parts = phrase.split()
    starts = [target_pos - k for k, part in enumerate(parts) if part == tokens[target_pos][0]]
    start = next((s for s in starts if s >= 0 and s + len(parts) <= len(tokens)
                  and all(p in (tokens[s + j][0], tokens[s + j][2]) for j, p in enumerate(parts))), None)
    if start is None:
        return True
    selected = [words[tokens[start + j][1]] for j in range(len(parts))]
    before = tokens[start - 1][0] if start else ""
    after = tokens[start + len(parts)][0] if start + len(parts) < len(tokens) else ""
    # An interjection does not absorb the subject or complement of a real clause.
    if kinds.get(phrase) == "intj":
        boundary = lambda text: not text or bool(re.fullmatch(r"\W+", text))
        if not (boundary(before) and boundary(after)):
            return True
    # A quoted dictionary question is not a fixed phrase when its verb has
    # additional arguments (qué tienes en la boca, qué va a pasar).
    if any(w.upos == "VERB" for w in selected) and any(w.text.lower() in ("qué", "que") for w in selected):
        members = {w.id for w in selected}
        if any(x.head in members and x.id not in members and x.upos != "PUNCT" for x in words):
            return True
    if any(w.text.lower() == "qué" for w in selected):
        if any(w.upos == "PRON" and w.deprel in ("obj", "nsubj") and w.head not in {x.id for x in selected} for w in selected):
            return True
    # Dictionary command/discourse phrases cannot consume a negated verb clause.
    if any(w.upos in ("VERB", "AUX") for w in selected):
        members = {w.id for w in selected}
        if any(x.head in members and x.id not in members and (x.text.lower() in ("no", "não") or x.deprel.startswith("nsubj")) for x in words):
            return True
        if any(w.deprel in ("xcomp", "ccomp", "csubj", "advcl", "acl") and w.head not in members for w in selected):
            return True
    last = selected[-1]
    if last.deprel in ("det", "amod", "nummod") and last.head > last.id:
        return True
    first = selected[0]
    # Preposition + demonstrative is an ordinary complement when inside a clause.
    # A detached initial connector can retain its discourse reading.
    if first.upos == "ADP" and last.upos == "PRON" and feat(last, "PronType") & {"Dem"}:
        if start > 0 and any(words[t[1]].upos in ("VERB", "AUX") for t in tokens[:start]):
            return True
    # A noun modifier such as amor de mi vida cannot become the vocative my dear.
    if first.upos == "ADP":
        complement = words[first.head - 1] if first.head else None
        if complement is not None and complement.deprel == "nmod" and complement.head:
            if words[complement.head - 1].upos in ("NOUN", "PROPN"):
                return True
    # More than once is a quantity comparison, not the impatience expression
    # de una vez. This applies to numerical bounds before any dictionary phrase.
    if before in ("más", "menos", "mais") and parts[0] in ("de", "do"):
        return True
    # Motion/auxiliary clauses retain the infinitive, rather than an a ver interjection.
    if any(w.upos == "VERB" for w in selected):
        if before and words[tokens[start - 1][1]].lemma in ("ir", "venir", "volver"):
            return True
    return False


def governing_verb(words, word):
    head = words[word.head - 1] if word.head else None
    if head is None:
        return None
    if head.upos in ("VERB", "AUX"):
        return head
    return words[head.head - 1] if head.head else None


def resolve_clitic_head(words, word):
    """Follow a climbing auxiliary to the lexical infinitive it controls."""
    head = governing_verb(words, word)
    seen = set()
    while head is not None and head.id not in seen:
        seen.add(head.id)
        restructuring = {"ir", "vir", "estar", "poder", "dever", "querer", "conseguir", "ter", "haver", "começar", "voltar", "acabar", "deixar", "parar", "continuar", "seguir", "tener", "haber", "deber", "querer", "empezar", "volver", "acabar", "dejar"}
        complements = [x for x in children(words, head) if head.lemma in restructuring and x.deprel == "xcomp" and x.upos == "VERB"]
        if not complements:
            break
        head = complements[0]
    return head


def policy_for(word, decisions):
    if decisions is None:
        return None
    start = word.parent.start_char
    decision = next((d for d in decisions if d["start"] <= start < d["end"]), None)
    return decision["policy"][0] if decision else "Z"


def clitic_label(words, i, surface, language, pronominal, decisions=None, verbs=None):
    """A grammatical claim without guessing the first dictionary verb sense.

NO_SE is authoritative against a pronominal/reflexive claim. SE_FIRM permits
one; BOTH requires local syntax. No invented verb+'oneself' glosses.
"""
    role = lambda value, gloss: {"kind": "role", "value": value, "gloss": gloss, "rule": "clitic_context"}
    unit = lambda value: {"kind": "unit", "value": value, "gloss": "", "rule": "pronominal_context"}
    w = words[i]
    head = resolve_clitic_head(words, w)
    if head is None or head.upos not in ("VERB", "AUX"):
        return None
    kids = children(words, head)
    if surface == "se" and (w.upos in ("SCONJ", "CCONJ") or w.deprel == "mark"):
        return role("conj_if", "if / whether") if language == "pt" else None
    decision = policy_for(head, decisions)
    if decisions is not None:
        observed = next((d for d in decisions if d["start"] <= head.parent.start_char < d["end"]), None)
        lemma = observed.get("resolved_lemma", head.lemma) if observed else head.lemma
    else:
        lemma = head.lemma
    if decision == "NO_SE":
        # Portuguese se may instead be a conjunction before an auxiliary.
        if language == "pt" and surface == "se":
            return role("conj_if", "if / whether")
        return role("object_pron", {"me": "me / to me", "te": "you / to you", "nos": "us / to us", "os": "you / to you (plural)", "vos": "you / to you (plural)", "se": "to him / her / them"}[surface])
    texts = [x.text.lower() for x in words]
    if surface == "se" and language == "es" and i + 1 < len(words) and words[i + 1].text.lower() in ("lo", "la", "los", "las"):
        return role("object_pron", "to him / her / them")
    if "outros" in texts or "otros" in texts or ("uno" in texts and "otro" in texts):
        if feat(head, "Number") == {"Plur"} or surface == "se":
            return role("reciprocal", "each other")
    if any(x.text.lower() in ("sí", "si") for x in kids) and any(x.text.lower().startswith(("mism", "mesm")) for x in words):
        return role("reflexive", "oneself")
    # Nominal subjects which name the patient cannot license a -self reading.
    subjects = [x for x in kids if x.deprel.startswith("nsubj") and x.text.lower() not in ("se", "me", "te", "nos", "os", "vos")]
    if surface == "se" and lemma in pronominal and any((x.upos == "ADJ" and x.deprel in ("obj", "xcomp")) or (x.upos == "ADV" and "Cmp" in feat(x, "Degree")) for x in kids):
        return unit(lemma + ("-se" if language == "pt" else "se"))
    if decision != "SE_FIRM" and surface == "se":
        if any(x.deprel == "nsubj:pass" for x in subjects) or w.deprel == "expl:pass":
            if lemma in pronominal and not any("Part" in feat(x, "VerbForm") for x in (head,)):
                return {"kind": "none", "value": None, "gloss": None, "rule": "passive_or_pronominal"}
            return role("passive_se", "is / are done")
        if not subjects and lemma not in pronominal and not feat(head, "Mood") & {"Imp", "Sub"}:
            return role("impersonal_se", "one / people")
        if subjects and any(x.upos == "NOUN" for x in subjects) and lemma not in pronominal:
            return role("passive_se", "is / are done")
    agree = {"me": ("1", "Sing"), "te": ("2", "Sing"), "nos": ("1", "Plur"), "os": ("2", "Plur"), "vos": ("2", "Plur")}
    matched = decision == "SE_FIRM" or (decision is None and surface in agree and agree[surface][0] in feat(head, "Person") and agree[surface][1] in feat(head, "Number"))
    if surface != "se" and not matched:
        return None
    if lemma in pronominal:
        return unit(lemma + ("-se" if language == "pt" else "se"))
    if matched:
        if verbs is not None and lemma not in verbs:
            return role("pronominal", "")  # Never teach an invented lemma from a parser error.
        return unit(lemma + ("-se" if language == "pt" else "se"))
    if surface == "se":
        return {"kind": "none", "value": None, "gloss": None, "rule": "uncertain_clitic"}
    return None
