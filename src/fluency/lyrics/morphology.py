"""Contextual UD evidence for lyrics, without changing legacy speech profiles."""
from fluency.speech.wsd_execute import _canonical_grammar

_VALUES = {
    'VerbForm': {'Ger': ('form', 'gerund'), 'Inf': ('form', 'infinitive'),
                 'Part': ('form', 'participle')},
    'Case': {v: ('case', k) for v, k in [('Nom', 'nominative'), ('Acc', 'accusative'),
             ('Dat', 'dative'), ('Gen', 'genitive'), ('Loc', 'locative')]},
    'Gender': {'Masc': ('gender', 'masculine'), 'Fem': ('gender', 'feminine')},
}


def canonical_grammar(token):
    result = _canonical_grammar(token)
    for axis, mapping in _VALUES.items():
        pair = mapping.get(token.morph.to_dict().get(axis))
        if pair:
            result[pair[0]] = pair[1]
    if getattr(token, 'dep_', '') in {'nsubj', 'nsubj:pass', 'csubj'}:
        result['pronoun_role'] = 'subject'
    elif token.pos_ == 'PRON' and getattr(token, 'dep_', '') in {'obj', 'iobj'}:
        result['pronoun_role'] = 'object'
    if hasattr(token, 'doc') and token.i + 1 < len(token.doc):
        result['following_pos'] = token.doc[token.i + 1].pos_
    result['lemma'] = token.lemma_.casefold()
    return result


def parsing_text(text, units, resolver):
    """Expand scoped declarations for tagging only; map back to observed spans.

    A declared single-token expansion is evidence. Ambiguous and multiword
    expansions remain untouched; no generic normalizer guesses their meaning.
    """
    pieces = []; spans = {}; source_end = 0; output_end = 0
    for unit in units:
        prefix = text[source_end:unit.start]
        replacement = resolver.expansion_target(unit.surface_key) if unit.eligible else ''
        replacement = replacement if replacement and not any(c.isspace() for c in replacement) else unit.observed_text
        pieces.extend((prefix, replacement))
        start = output_end + len(prefix)
        spans[(unit.start, unit.end)] = (start, start + len(replacement))
        output_end = start + len(replacement); source_end = unit.end
    pieces.append(text[source_end:])
    return ''.join(pieces), spans
