"""Portuguese lyrics preserve contractions and clitic bundles as surface cards.

Restored enclitic hosts are lookup candidates only. The dictionary must license
one before it becomes a menu; ambiguous deleted consonants are not guessed.
"""
import re
from fluency.core.text_units import TokenUnit, TokenizationResult
from fluency.languages.portuguese.surfaces import canonicalize_typography, normalize_surface
from fluency.lyrics.languages.base import NormalizedUnit

_WORD = re.compile(r"[^\W\d_]+(?:[’'\-][^\W\d_]+)*", re.UNICODE)
_CLITICS = frozenset({'me','te','se','nos','vos','lhe','lhes','o','a','os','as','lo','la','los','las','no','na','nas','mo','ma','mos','mas','to','ta','tos','tas','lho','lha','lhos','lhas'})


class PortugueseLyricsAdapter:
    language = 'pt'
    method_id = 'portuguese-lyrics-normalizer/v1'

    def tokenize(self, text):
        canonical = canonicalize_typography(text)
        return TokenizationResult(canonical, tuple(
            TokenUnit(m.group(), normalize_surface(m.group()), m.start(), m.end(), 'word', 'ordinary_token', True)
            for m in _WORD.finditer(canonical)))

    def normalize(self, surface, *, previous=None, following=None):
        return (NormalizedUnit(normalize_surface(surface), 'preserve', 'surface_preserved'),)

    def lookup_forms(self, surface):
        parts = normalize_surface(surface).split('-')
        if len(parts) < 2 or not all(p in _CLITICS for p in parts[1:]):
            return ()  # lexical compounds and mesoclisis need dictionary evidence
        host = parts[0]
        if parts[1] in {'lo','la','los','las'}:
            # Productive infinitives with a deleted r. pô-lo has a unique
            # accented infinitive; fi-lo/di-lo may have lost z/s: abstain.
            if host.endswith(('á','ê','í')):
                host = host[:-1] + {'á':'ar','ê':'er','í':'ir'}[host[-1]]
            elif host == 'pô':
                host = 'pôr'
            else:
                return ()
        return (host,)


    @staticmethod
    def occurrence_grammar(surface, sentence, span, token):
        if surface in {'você', 'vocês'} and token is not None and token.pos_ == 'PRON':
            # Semantic addressee person differs from third-person agreement.
            return {'person': '2'}
        if surface == 'se' and token is not None and token.pos_ == 'PRON':
            morphology = token.morph.to_dict()
            head = getattr(token, 'head', None)
            if not morphology.get('Person') and head is not None and head.pos_ in {'VERB', 'AUX'}:
                person = head.morph.to_dict().get('Person')
                if person in {'1', '2', '3'}:
                    return {'person': person}
        return {}

    @staticmethod
    def clitic_evidence(surface, sentence, grammar=None):
        # Portuguese se may be passive/impersonal and French se may be
        # lexical: mere spelling does not certify reflexivity.
        return True if (grammar or {}).get('reflexive') == 'true' else None

    @staticmethod
    def pronominal_base(headword):
        return headword[:-3] if headword.endswith('-se') else headword

    def has_clitic(self, sentence):
        return any(part in {'me', 'te', 'se', 'nos', 'vos', 'lhe', 'lhes'}
                   for u in self.tokenize(sentence).units for part in u.surface_key.split('-'))


ADAPTER_CLASS = PortugueseLyricsAdapter
