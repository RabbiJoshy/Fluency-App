"""Locate the observed surface or its attached clitic at a declared offset."""
import re


def locate(doc, text, form, span=None):
    if span is None:
        match = re.search(r"(?<![\w'’])" + re.escape(form).replace("'", "['’]") + r"(?![\w'’])", text, re.I)
        if not match:
            return None
        span = (match.start(), match.end())
    if text[span[0]:span[1]].casefold() != form.casefold():
        return None
    for sentence in doc.sentences:
        hits = [(i, w) for i, w in enumerate(sentence.words)
                if w.parent.start_char <= span[0] < w.parent.end_char]
        if hits:
            component = next(((i, w) for i, w in hits if w.text.casefold() == form.casefold()), hits[0])
            i, word = component
            # A contraction keeps its observed token; an attached pronoun keeps
            # its grammatical component (ouvi-a -> a, never ouvi-a as an article).
            return sentence.words, i, form
    return None
