"""Conservative Spanish research overrides for frozen syntax bridge v3.

No labels, translations, review decisions or example identifiers drive assignment.
None delegates to v3; an explicit abstention also blocks an unsafe v3 candidate.
"""

PRONOMINAL = {'equivocar', 'arrepentir', 'quejar', 'atrever', 'enterar',
              'acordar', 'referir', 'sentir', 'ir'}
MODALS = {'poder', 'deber', 'querer'}
DESTINATIONS = {'autobús', 'tren', 'avión', 'colegio', 'cine', 'parque',
                'mercado', 'hospital', 'aeropuerto', 'puerto', 'hotel',
                'restaurante', 'supermercado', 'estadio'}
MOTION = {'ir', 'venir', 'llegar', 'volver', 'subir', 'bajar', 'entrar'}


def decide_es(row, obs):
    if row.get('language') != 'es' or row.get('word') not in {'se', 'lo', 'que', 'al', 'del'}:
        return None
    text, word = row['sentence'], row['word']
    evidence = {'parser': obs.get('parser') if obs else None}

    def stop(reason):
        return dict(status='abstain', reason=reason, evidence=evidence.copy())

    if not obs or len(obs.get('spans', [])) != 1:
        return stop('Exactly one parsed focus occurrence is required.')
    start, end = obs['spans'][0]
    if not 0 <= start < end <= len(text) or text[start:end].casefold() != word:
        return stop('Focus offsets do not match the Spanish surface.')
    hits = [(s, n) for s in obs.get('sentences', []) for n in s
            if (n['token']['start_char'], n['token']['end_char']) == (start, end)]
    if len(hits) != 1:
        return stop('Focus must be one unsplit dependency token.')
    sent, focus = hits[0]
    nodes = {n['id']: n for n in sent}
    head = nodes.get(focus['head'])
    evidence.update(focus=focus, head=head)
    if not head and word != 'lo':
        return stop('Focus has no dependency head.')

    def bounds(n):
        return n['token']['start_char'], n['token']['end_char']

    def kids(n):
        return [x for x in sent if x['head'] == n['id']]

    def descendants(n):
        ids = {n['id']}
        while True:
            more = {x['id'] for x in sent if x['head'] in ids}
            if more <= ids:
                return [x for x in sent if x['id'] in ids]
            ids |= more

    def constituent(items):
        items = [n for n in items if n['upos'] != 'PUNCT' and n['id'] != focus['id']]
        if not items:
            return None
        a, b = min(bounds(n)[0] for n in items), max(bounds(n)[1] for n in items)
        ids = {n['id'] for n in items}
        if a < end and b > start:
            return None
        if any(a <= bounds(n)[0] < b and n['id'] not in ids for n in sent):
            return None
        return a, b

    def emit(pattern, parts, reason):
        if any(span is None for _, span in parts):
            return stop('No complete contiguous constituent matches the formula.')
        chunks = [dict(slot='connector', start=start, end=end)]
        chunks += [dict(slot=slot, start=span[0], end=span[1]) for slot, span in parts]
        chunks.sort(key=lambda c: c['start'])
        if any(c['start'] < 0 or c['start'] >= c['end'] or c['end'] > len(text) for c in chunks):
            return stop('Constituent offsets are invalid.')
        if any(a['end'] > b['start'] for a, b in zip(chunks, chunks[1:])):
            return stop('Constituent spans overlap.')
        expected = ['v', 'connector', 'c'] if word == 'que' else ['connector', 'c' if ((word in {'al', 'del'}) and pattern == 0) else 'v']
        if [c['slot'] for c in chunks] != expected:
            return stop('Constituent order does not match the displayed formula.')
        for c in chunks:
            c['text'] = text[c['start']:c['end']]
        return dict(status='candidate', pattern=pattern, chunks=chunks,
                    reason=reason, evidence=evidence.copy())

    def verb_complex(verb):
        selected = [verb] + [x for x in kids(verb) if x['deprel'] in {'aux', 'aux:pass'}]
        parent = nodes.get(verb['head'])
        if parent and verb['deprel'] == 'xcomp' and parent['lemma'] in MODALS:
            selected += [parent] + [x for x in kids(parent) if x['deprel'] == 'aux']
        # Spanish parser can attach tener que + infinitive as conj rather than xcomp.
        if parent and parent['lemma'] == 'tener' and verb['deprel'] in {'xcomp', 'conj'} and 'VerbForm=Inf' in (verb.get('feats') or ''):
            marker = [x for x in kids(verb) if x['text'].casefold() == 'que' and x['deprel'] in {'mark', 'cc'}]
            if len(marker) == 1 and bounds(parent)[1] <= bounds(marker[0])[0] < bounds(verb)[0]:
                selected += [parent, marker[0]]
        result = constituent(selected)
        if result and (result[0] < end or text[end:result[0]].strip()):
            return None
        return result

    if word == 'se':
        if head['upos'] != 'VERB' or focus['deprel'] not in {'expl:pv', 'expl'}:
            return stop('No licensed pronominal dependency; passive/reflexive ambiguity remains.')
        if any(x['deprel'] in {'aux:pass', 'nsubj:pass'} for x in kids(head)):
            return stop('Passive dependencies conflict with the pronominal reading.')
        lemma = head['lemma'].casefold().removesuffix('se')
        selected = None
        if lemma in PRONOMINAL:
            # These transitive lemmas need their pronominal prepositional frame.
            required_case = {'referir': {'a', 'al'}, 'acordar': {'de'}, 'enterar': {'de'}}.get(lemma)
            frame_ok = not required_case or any(
                marker['text'].casefold() in required_case and marker['deprel'] == 'case'
                for child in kids(head) for marker in kids(child))
            if frame_ok:
                selected = verb_complex(head)
        elif lemma == 'llevar':
            manner = [x for x in kids(head) if x['lemma'] in {'bien', 'mal'} and x['deprel'] == 'advmod']
            company = [x for x in kids(head) if x['deprel'] == 'obl' and any(y['lemma'] == 'con' and y['deprel'] == 'case' for y in kids(x))]
            if len(manner) == len(company) == 1:
                selected = constituent([head, manner[0]] + descendants(company[0]) + [x for x in kids(head) if x['deprel'] == 'aux'])
                if selected and text[end:selected[0]].strip():
                    selected = None
        if selected:
            return emit(0, [('v', selected)], 'Licensed pronominal lemma/construction and dependency agree.')
        return stop('Pronominal parser tag alone cannot resolve reflexive, middle or passive semantics.')

    if word == 'lo':
        if head and focus['deprel'] == 'det' and head['upos'] == 'ADJ':
            return None  # Frozen v3 owns the adjective rule.
        if head and head['upos'] == 'VERB' and focus['deprel'] == 'obj':
            return emit(1, [('v', verb_complex(head))], 'Accusative lo precedes a complete parsed verb complex.')
        # Anaphoric predicate lo is itself the copular head in UD.
        copulas = [x for x in kids(focus) if x['deprel'] == 'cop' and x['lemma'] == 'ser']
        if focus['upos'] == 'PRON' and 'Case=Acc' in (focus.get('feats') or '') and len(copulas) == 1:
            return emit(1, [('v', constituent(copulas))], 'Anaphoric predicate lo with a parsed ser copula.')
        return stop('Lo lacks object or anaphoric copular evidence; nominal lo que is unsupported.')

    if word == 'que':
        if focus['upos'] != 'PRON' or 'Rel' not in (focus.get('feats') or ''):
            return None
        if focus['deprel'] not in {'nsubj', 'obj', 'iobj', 'obl'} or any(x['deprel'] == 'case' for x in kids(focus)):
            return stop('Preposition-bearing relative does not fit noun + que formula.')
        rel = head
        visited = set()
        while rel and rel['id'] not in visited:
            visited.add(rel['id'])
            if rel['deprel'] in {'acl', 'acl:relcl'}:
                break
            rel = nodes.get(rel['head'])
        noun = nodes.get(rel['head']) if rel else None
        if not rel or rel['deprel'] not in {'acl', 'acl:relcl'} or not noun or noun['upos'] not in {'NOUN', 'PROPN'}:
            return stop('Relative pronoun lacks a confirmed noun antecedent.')
        clause = descendants(rel)
        if any(bounds(n)[0] < start for n in clause if n['upos'] != 'PUNCT'):
            return stop('Relative clause is not fully after the noun + que boundary.')
        return emit(1, [('v', bounds(noun)), ('c', constituent(clause))], 'Relative pronoun and acl attachment identify a noun-modifying clause.')

    if word == 'al':
        if head['upos'] == 'VERB' and 'VerbForm=Inf' in (head.get('feats') or '') and head['deprel'] == 'advcl':
            return emit(1, [('v', bounds(head))], 'Temporal al plus adverbial infinitive.')
        gov = nodes.get(head['head'])
        evidence['governor'] = gov
        if focus['deprel'] == 'case' and head['deprel'] == 'obl' and gov and gov['lemma'] in MOTION and head['lemma'] in DESTINATIONS:
            return emit(0, [('c', constituent(descendants(head)))], 'Motion predicate and licensed destination fit al + destination.')
        return stop('Personal-a, recipient and rate uses do not establish the displayed destination slot.')

    if word == 'del':
        if head and head['upos'] in {'NOUN', 'PROPN'} and bounds(head)[0] >= end:
            hf = head.get('feats') or ''
            if 'Gender=Masc' not in hf and 'Gender=' in hf:
                return stop('Del requires masculine noun agreement.')
            phrase = constituent(descendants(head))
            if phrase and not text[end:phrase[0]].strip():
                return emit(0, [('c', phrase)], 'Del contraction attached to masculine noun.')
        return stop('Del lacks valid nominal attachment.')
    return None
