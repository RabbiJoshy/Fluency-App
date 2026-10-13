"""Stanza-shaped view of a spaCy parse, so the rule labellers run on either parser.

Spanish uses the repo's pinned parser, es_dep_news_trf@3.8.0 (fluency.nlp.pos), rather
than a second Stanza model. Each sentence exposes `.words` whose items carry text, lemma,
upos, feats, deprel, 1-based id/head and `.parent` (the token as written). spaCy does not
split del/al, so a word is its own token.
"""
import spacy


class Word:
    __slots__ = ("text", "lemma", "upos", "feats", "deprel", "id", "head", "parent", "start_char", "end_char", "words")

    def __init__(self, tok, sent_start):
        self.text, self.lemma, self.upos = tok.text, tok.lemma_, tok.pos_
        self.feats = str(tok.morph) or None
        self.deprel = "root" if tok.dep_ == "ROOT" else tok.dep_.lower()
        self.id = tok.i - sent_start + 1
        self.head = 0 if tok.head.i == tok.i else tok.head.i - sent_start + 1
        self.start_char, self.end_char = tok.idx, tok.idx + len(tok.text)
        self.parent, self.words = self, [self]


class Sentence:
    def __init__(self, span):
        self.words = [Word(t, span.start) for t in span]


class Doc:
    def __init__(self, doc):
        self.sentences = [Sentence(s) for s in doc.sents]


class Pipeline:
    def __init__(self, model="es_dep_news_trf"):
        self.nlp = spacy.load(model)
        self.version = f"{model}@{self.nlp.meta['version']}"

    def __call__(self, text):
        return Doc(self.nlp(text))

    def bulk(self, texts):
        return [Doc(d) for d in self.nlp.pipe(texts, batch_size=64)]
