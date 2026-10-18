"""Conservative structural assignment for the suite's articles and personal subjects.

The registry is explicit: adding a surface requires checking its teaching pattern.
No automatic label, translation, example text or editorial decision is consulted.
Unsupported surfaces return None so the caller may use its other rules.
"""
import re

# (pattern index, gender, number). These indices come from the PT/ES suites.
ARTICLE_PATTERNS = {
    'pt': {'o': (0, 'Masc', 'Sing'), 'a': (1, 'Fem', 'Sing'),
           'um': (0, 'Masc', 'Sing'), 'uma': (0, 'Fem', 'Sing'),
           'os': (0, 'Masc', 'Plur'), 'as': (0, 'Fem', 'Plur')},
    'es': {'el': (0, 'Masc', 'Sing'), 'la': (0, 'Fem', 'Sing'),
           'los': (0, 'Masc', 'Plur'), 'las': (0, 'Fem', 'Plur'),
           'un': (0, 'Masc', 'Sing'), 'una': (0, 'Fem', 'Sing')},
}
POSSESSIVE_PATTERNS = {'es': {'mi': 0, 'su': 0, 'tu': 0}}
# (pattern index, person, number); demonstrative/indefinite subjects are excluded.
SUBJECT_PATTERNS = {
    'pt': {'eu': (0, '1', 'Sing'), 'ele': (0, '3', 'Sing'),
           'ela': (0, '3', 'Sing')},
    'es': {'yo': (0, '1', 'Sing'), 'tú': (0, '2', 'Sing')},
}
SUPPORTED_PATTERNS = {
    (lang, word): spec[0]
    for registry in (ARTICLE_PATTERNS, SUBJECT_PATTERNS)
    for lang, words in registry.items() for word, spec in words.items()
}
SUPPORTED_PATTERNS.update({(lang, word): index
                           for lang, words in POSSESSIVE_PATTERNS.items()
                           for word, index in words.items()})


def _features(node):
    feats = node.get('feats') or ''
    if isinstance(feats, dict):
        return feats
    return dict(part.split('=', 1) for part in feats.split('|') if '=' in part)


def decide_basic(row, obs):
    """Return a structural candidate, an abstention, or None for irrelevant cards."""
    lang, word = row.get('language'), row.get('word')
    if (lang, word) not in SUPPORTED_PATTERNS:
        return None
    evidence = {'parser': (obs or {}).get('parser')}

    def stop(reason):
        return dict(status='abstain', reason=reason, evidence=evidence)

    text = row.get('sentence')
    if not isinstance(text, str) or not obs:
        return stop('No source sentence or matching parse available.')
    if obs.get('sentence', text) != text:
        return stop('Parse and source sentence disagree.')
    spans = obs.get('spans') or []
    if len(spans) != 1 or len(spans[0]) != 2:
        return stop('Exactly one focus occurrence is required.')
    start, end = spans[0]
    if (not isinstance(start, int) or not isinstance(end, int)
            or not 0 <= start < end <= len(text)
            or text[start:end].casefold() != word):
        return stop('Focus span does not match the card surface.')
    occurrences = list(re.finditer(r'(?<!\w)' + re.escape(word) + r'(?!\w)', text, re.IGNORECASE))
    if len(occurrences) != 1 and not obs.get('occurrence_selected'):
        return stop('Multiple focus occurrences require occurrence selection.')
    sentences = obs.get('sentences') or []
    try:
        hits = [(sent, node) for sent in sentences for node in sent
                if (node['token']['start_char'], node['token']['end_char']) == (start, end)]
        if len(hits) != 1:
            return stop('Parser split or merged the focus token.')
        sent, focus = hits[0]
        ids = [node['id'] for node in sent]
        if len(set(ids)) != len(ids):
            return stop('Parser word identifiers are not unique.')
        byid = {node['id']: node for node in sent}
        for node in sent:
            token = node['token']
            a, b = token['start_char'], token['end_char']
            if not 0 <= a < b <= len(text) or token['text'] != text[a:b]:
                return stop('Parser token offsets do not preserve the source.')
            node['head'], node['upos'], node['deprel']
        if any(node is not focus and node['token']['start_char'] < end
               and node['token']['end_char'] > start for node in sent):
            return stop('Focus token has overlapping parser words or a token split.')
        head = byid.get(focus['head'])
    except (KeyError, TypeError, ValueError):
        return stop('Incomplete parser word structure.')
    evidence.update(focus=focus, head=head)
    if head is None:
        return stop('No syntactic head available.')

    def bounds(node):
        return node['token']['start_char'], node['token']['end_char']

    def chunk(nodes):
        nodes = [n for n in nodes if n['id'] != focus['id'] and n['upos'] != 'PUNCT']
        if not nodes:
            return None
        ranges = {bounds(n) for n in nodes}
        # Shared ranges represent unsafely merged multiword tokens.
        if len(ranges) != len(nodes):
            return None
        a, b = min(x[0] for x in ranges), max(x[1] for x in ranges)
        if a < end and b > start:
            return None
        if any(n['upos'] != 'PUNCT' and bounds(n)[0] < b and bounds(n)[1] > a
               and n not in nodes for n in sent):
            return None
        return a, b

    def emit(slot, interval, reason):
        if interval is None or interval[0] < end or text[end:interval[0]].strip():
            return stop('No safe adjacent constituent matching the displayed formula.')
        chunks = [dict(slot='connector', start=start, end=end),
                  dict(slot=slot, start=interval[0], end=interval[1])]
        for c in chunks:
            c['text'] = text[c['start']:c['end']]
        return dict(status='candidate', pattern=SUPPORTED_PATTERNS[lang, word],
                    chunks=chunks, reason=reason, evidence=evidence)

    articles = ARTICLE_PATTERNS.get(lang, {})
    possessives = POSSESSIVE_PATTERNS.get(lang, {})
    ff, hf = _features(focus), _features(head)
    if word in articles or word in possessives:
        # These suites also teach other readings of the same surface. Clear
        # evidence for those readings belongs to the caller's other adapters;
        # abstention here would incorrectly block their routing.
        object_surfaces = {'pt': {'o', 'a', 'os'}, 'es': {'la', 'los'}}
        if (word in object_surfaces.get(lang, set())
                and focus['upos'] == 'PRON'
                and focus['deprel'] in ('obj', 'iobj') and head['upos'] == 'VERB'):
            return None
        if (lang == 'pt' and word == 'a' and focus['upos'] == 'ADP'
                and focus['deprel'] == 'case' and head['upos'] in ('NOUN', 'PROPN', 'PRON')):
            return None
        if (focus['upos'] != 'DET' or focus['deprel'] not in ('det', 'det:poss')
                or head['upos'] not in ('NOUN', 'PROPN')):
            return stop('Determiner must attach directly to a lexical noun; objects and nominalised adjectives are excluded.')
        if word in articles:
            _, gender, number = articles[word]
            expected_definite = 'Ind' if word in ('um', 'uma', 'un', 'una') else 'Def'
            if (ff.get('PronType') != 'Art' or ff.get('Definite') != expected_definite or ff.get('Gender') != gender
                    or hf.get('Gender') != gender or ff.get('Number') != number
                    or hf.get('Number') != number):
                return stop('Article type and noun gender/number are not confirmed.')
        elif (ff.get('Poss') != 'Yes' or hf.get('Number') != 'Sing'
              or ff.get('Number') not in (None, 'Sing')):
            return stop('Possessive determiner and singular noun are not confirmed.')
        subtree_ids = {head['id']}
        while True:
            more = {n['id'] for n in sent if n['head'] in subtree_ids
                    and n['deprel'] not in ('appos','vocative','discourse','parataxis','cop')
                    and not (n['head']==head['id'] and n['deprel'] in ('nsubj','csubj','advmod'))}
            if more <= subtree_ids:
                break
            subtree_ids |= more
        return emit('c', chunk([n for n in sent if n['id'] in subtree_ids and bounds(n)[0] >= end]),
                    'Registered determiner surface and noun attachment agree.')

    _, person, number = SUBJECT_PATTERNS[lang][word]
    if (focus['upos'] != 'PRON' or focus['deprel'] != 'nsubj'
            or ff.get('PronType') != 'Prs' or ff.get('Person') != person
            or ff.get('Number') != number or head['upos'] != 'VERB'):
        return stop('Personal subject and verbal head are not confirmed.')
    verbs = [head] + [n for n in sent if n['head'] == head['id']
                     and n['deprel'] in ('aux', 'aux:pass')]
    finite = [n for n in verbs if _features(n).get('VerbForm') == 'Fin']
    if not finite or any(person not in _features(n).get('Person', person).split(',')
                         or _features(n).get('Number', number) != number for n in finite):
        return stop('Finite subject/verb agreement is not established.')
    right=max(bounds(n)[1] for n in verbs)
    verbs += [n for n in sent if n['head']==head['id'] and bounds(n)[0]>=end and bounds(n)[1]<=right and (n['upos']=='ADV' and n['deprel']=='advmod' or n['upos']=='PRON' and n['deprel'] in ('obj','iobj','expl:pv','expl'))]
    return emit('v', chunk(verbs), 'Registered personal pronoun is the subject of an agreeing verb.')
