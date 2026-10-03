"""French lyrics use the shared, offset-preserving French tokenizer.

Elided clitics remain surface cards (l’ is not arbitrarily changed to le).
Expansion alternatives are dictionary lookup metadata, never extra occurrences.
"""
from fluency.languages.french.tokenization import tokenize_french, load_tokenization_config
from fluency.languages.french.surfaces import normalize_surface
from fluency.lyrics.languages.base import NormalizedUnit


class FrenchLyricsAdapter:
    language = 'fr'
    method_id = 'french-lyrics-normalizer/v1'

    def tokenize(self, text):
        return tokenize_french(text)

    def normalize(self, surface, *, previous=None, following=None):
        result = self.tokenize(surface)
        return tuple(NormalizedUnit(u.surface_key, 'split' if len(result.units) > 1 else 'preserve', u.decision)
                     for u in result.units if u.eligible)

    def lookup_forms(self, surface):
        key = normalize_surface(surface)
        return load_tokenization_config().elision_expansions.get(key, ())


    @staticmethod
    def occurrence_grammar(surface, sentence, span, token):
        # Closed-class lexical person is independent of noisy agreement tags.
        pronouns = {'tu': ('2','singular'), 'je': ('1','singular'), 'j’': ('1','singular'),
                    'nous': ('1','plural'), 'vous': ('2','plural'),
                    'il': ('3','singular'), 'elle': ('3','singular'),
                    'ils': ('3','plural'), 'elles': ('3','plural')}
        if surface in pronouns and token is not None and token.pos_ in {'PRON', 'PROPN'}:
            person, number = pronouns[surface]
            return {'person': person, 'number': number, '_pos': 'PRON'}
        if surface == 'on' and token is not None and token.pos_ == 'PRON':
            # On takes singular verbs but can mean one or we. Agreement
            # number cannot decide the semantic pronoun reading.
            return {'number': None}
        if surface == 'est' and sentence[span[1]:].startswith('-ce'):
            return {'person': '3', 'number': 'singular', '_pos': 'AUX', '_lemma': 'être'}
        if surface == 'pas' and token is not None and token.pos_ == 'ADV':
            # The intensifying pas reading needs the voilà construction.
            # Ordinary sung negative pas often lacks UD Polarity marking.
            import re
            return {'function': 'rhetorical' if re.search(r"\bvoilà\b", sentence, re.I) else 'negative'}
        return {}

    @staticmethod
    def clitic_evidence(surface, sentence, grammar=None):
        # Portuguese se may be passive/impersonal and French se may be
        # lexical: mere spelling does not certify reflexivity.
        return True if (grammar or {}).get('reflexive') == 'true' else None

    @staticmethod
    def pronominal_base(headword):
        form = headword.replace("'", '’')
        return form[3:] if form.startswith('se ') else form[2:] if form.startswith('s’') else form

    def has_clitic(self, sentence):
        return any(u.surface_key in {'me', 'te', 'se', 'nous', 'vous', 'm’', 't’', 's’'}
                   for u in self.tokenize(sentence).units)


ADAPTER_CLASS = FrenchLyricsAdapter
