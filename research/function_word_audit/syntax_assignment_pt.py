"""Portuguese syntax recovery for the research bridge; no editorial inputs.

Return None outside the bounded recovery scope, allowing frozen v3 fallback.
Offsets always refer to the original surface, including shared-token MWT parses.
"""


PT_CONTRACTIONS = {
    'naquele': ('em', 'aquele', 'Masc', 'Sing', 0),
    'nos': ('em', 'o', 'Masc', 'Plur', 1),
    'no': ('em', 'o', 'Masc', 'Sing', 0),
    'na': ('em', 'o', 'Fem', 'Sing', 0),
    'num': ('em', 'um', 'Masc', 'Sing', 0),
    'numa': ('em', 'um', 'Fem', 'Sing', 0),
    'do': ('de', 'o', 'Masc', 'Sing', 0),
    'da': ('de', 'o', 'Fem', 'Sing', 0),
    'ao': ('a', 'o', 'Masc', 'Sing', 0),
    'à': ('a', 'o', 'Fem', 'Sing', 0),
    'pelo': ('por', 'o', 'Masc', 'Sing', 0),
    'pela': ('por', 'o', 'Fem', 'Sing', 0),
}


def decide_pt(row, obs):
    if row.get('language') != 'pt' or (row.get('word') not in {'nos', 'naquele', 'se'} and row.get('word') not in PT_CONTRACTIONS):
        return None
    if not obs:
        return None
    text, word = row['sentence'], row['word']
    spans = obs.get('spans', [])
    evidence = {'parser': obs.get('parser'), 'recovery': 'pt-dependency-v1'}

    def stop(reason):
        return dict(status='abstain', pattern=None, chunks=[], reason=reason, evidence=evidence)

    if len(spans) != 1:
        return stop('A unique focus occurrence is required.')
    start, end = spans[0]
    if not 0 <= start < end <= len(text) or text[start:end].casefold() != word:
        return stop('Focus offsets do not match the requested surface.')

    def bounds(n):
        return n['token']['start_char'], n['token']['end_char']

    matches = [(s, [n for n in s if bounds(n)[0] < end and bounds(n)[1] > start])
               for s in obs.get('sentences', [])]
    matches = [(s, ns) for s, ns in matches if ns]
    if len(matches) != 1:
        return stop('Focus is not uniquely aligned to one parsed sentence.')
    sent, focus = matches[0]
    nodes = {n['id']: n for n in sent}
    evidence['focus_nodes'] = focus
    if any(a < start or b > end for a, b in map(bounds, focus)):
        # Enclitic MWTs may cover both the verb and focus; do not manufacture
        # disjoint verb offsets when this card only displays a preposed clitic.
        return stop('Merged verb/clitic token does not establish the displayed before-verb order.')
    coverage = sorted(set(bounds(n) for n in focus))
    cursor = start
    for a, b in coverage:
        if a > cursor:
            return stop('Focus token alignment has an uncovered gap.')
        cursor = max(cursor, b)
    if cursor != end:
        return stop('Focus token alignment is incomplete.')

    def kids(n):
        return [x for x in sent if x['head'] == n['id']]

    def subtree(n):
        ids = {n['id']}
        while True:
            more = {x['id'] for x in sent if x['head'] in ids}
            if more <= ids:
                return [x for x in sent if x['id'] in ids]
            ids |= more

    def constituent(group):
        group = [n for n in group if n['upos'] != 'PUNCT']
        if not group:
            return None
        a = min(bounds(n)[0] for n in group)
        b = max(bounds(n)[1] for n in group)
        ids = {n['id'] for n in group}
        if a < end and b > start:
            return None
        if any(n['upos'] != 'PUNCT' and a <= bounds(n)[0] < b and n['id'] not in ids for n in sent):
            return None
        return a, b

    def emit(pattern, parts, reason):
        if any(r is None for _, r in parts):
            return stop('No complete contiguous constituent is established.')
        chunks = [('connector', (start, end))] + parts
        chunks.sort(key=lambda item: item[1][0])
        if any(a[1][1] > b[1][0] for a, b in zip(chunks, chunks[1:])):
            return stop('Constituent offsets overlap.')
        return dict(status='candidate', pattern=pattern,
                    chunks=[dict(slot=slot, start=a, end=b, text=text[a:b]) for slot, (a, b) in chunks],
                    reason=reason, evidence=evidence)

    # Both split em+determiner and merged ADP representations are accepted,
    # but the nominal dependency, agreement and surface order must agree.
    # Both split em/de/por/a+determiner and merged ADP representations are accepted,
    # but the nominal dependency, agreement and surface order must agree.
    if word in PT_CONTRACTIONS:
        prep_base, det_base, expected_gender, expected_number, pat_idx = PT_CONTRACTIONS[word]
        cases = [n for n in focus if n['upos'] == 'ADP' and n['deprel'] == 'case'
                 and n['lemma'].casefold() in {prep_base, word}]
        if cases:
            if len(cases) != 1:
                return stop('Conflicting contraction case markers.')
            case = cases[0]
            noun = nodes.get(case['head'])
            evidence['head'] = noun
            if not noun or noun['upos'] not in ('NOUN', 'PROPN') or bounds(noun)[0] < end:
                return stop('Contraction must attach to a following noun, never a finite verb.')
            feats = noun.get('feats') or ''
            if expected_gender and f'Gender={expected_gender}' not in feats:
                return stop(f'Contraction lacks {expected_gender.lower()} noun agreement evidence.')
            if expected_number and f'Number={expected_number}' not in feats:
                return stop(f'Contraction lacks {expected_number.lower()} noun agreement evidence.')
            others = [n for n in focus if n['id'] != case['id']]
            if others and (len(others) != 1 or others[0]['upos'] != 'DET'
                           or others[0]['deprel'] != 'det' or others[0]['head'] != noun['id']
                           or others[0]['lemma'].casefold() != det_base):
                return stop('Split contraction components disagree about their nominal head.')
            if not others and case['text'].casefold() != word:
                return stop('Missing determiner component in the contraction parse.')
            group = [noun]
            allowed = {'amod', 'nummod', 'det', 'compound', 'flat', 'flat:name'}
            ids = {noun['id']}
            while True:
                added = [n for n in sent if n['head'] in ids and n['deprel'] in allowed
                         and bounds(n)[0] >= end and n['id'] not in ids]
                if not added:
                    break
                group.extend(added)
                ids.update(n['id'] for n in added)
            if any('VerbForm=Fin' in (n.get('feats') or '')
                   and end <= bounds(n)[0] <= bounds(noun)[0] for n in sent):
                return stop('Finite verb intervenes before the contraction nominal head.')
            phrase = constituent(group)
            if not phrase or text[end:phrase[0]].strip():
                return stop('Contraction is not adjacent to a safe nominal constituent.')
            return emit(pat_idx, [('c', phrase)],
                        'Contraction components, nominal attachment and agreement agree.')
        if word in {'naquele', 'no', 'na', 'do', 'da', 'num', 'numa', 'pelo', 'pela', 'ao', 'à'}:
            return stop(f'No {prep_base} plus determiner contraction structure is established.')
        if len(focus) != 1:
            return stop('Nos has no unique pronoun dependency.')
        pron = focus[0]
        verb = nodes.get(pron['head'])
        evidence['head'] = verb
        if pron['upos'] != 'PRON' or pron['deprel'] not in {'obj', 'iobj'} or not verb or verb['upos'] != 'VERB':
            return stop('Nos is not an established object pronoun.')
        complex_nodes = [verb] + [n for n in kids(verb) if n['deprel'] in {'aux', 'aux:pass'}]
        for n in complex_nodes:
            f = n.get('feats') or ''
            if 'Person=1' in f and 'Number=Plur' in f:
                return stop('First-plural subject permits reciprocal/reflexive nos, outside ordinary us.')
        if any(n['lemma'].casefold() in {'nós', 'nos'} and n['deprel'] == 'nsubj' for n in kids(verb)):
            return stop('First-plural subject permits reciprocal/reflexive nos.')
        phrase = constituent(complex_nodes)
        if not phrase or phrase[0] < end or text[end:phrase[0]].strip():
            return stop('The displayed nos pattern requires an adjacent following verb complex.')
        if not any('Person=' in (n.get('feats') or '') for n in complex_nodes):
            return stop('Verb person evidence is missing; reciprocal nos cannot be excluded.')
        return emit(0, [('v', phrase)], 'Object nos precedes a non-first-plural verb complex.')

    if len(focus) != 1:
        return stop('Se requires a unique syntactic focus.')
    marker = focus[0]
    if marker['upos'] != 'SCONJ' or marker['deprel'] != 'mark':
        return None  # Reflexive/pronominal analysis remains frozen v3's remit.
    condition = nodes.get(marker['head'])
    evidence['head'] = condition
    if not condition or condition['deprel'] != 'advcl':
        return stop('Embedded whether or other non-adverbial se is not a condition/result pattern.')
    main = nodes.get(condition['head'])
    seen = set()
    while main and main['deprel'] == 'xcomp' and main['id'] not in seen:
        seen.add(main['id'])
        parent = nodes.get(main['head'])
        if not parent or parent['upos'] not in {'VERB', 'AUX'} or parent['lemma'].casefold() not in {'poder', 'dever', 'ir'}:
            return stop('Conditional attachment has an unlicensed intervening clause.')
        main = parent
    evidence['governor'] = main
    if not main or main['deprel'] != 'root' or main['upos'] not in {'VERB', 'AUX', 'ADJ'}:
        return stop('No matrix result clause is established.')
    cond_nodes = subtree(condition)
    cond_ids = {n['id'] for n in cond_nodes}
    cond = constituent([n for n in cond_nodes if n['id'] != marker['id']])
    result = constituent([n for n in subtree(main) if n['id'] not in cond_ids])
    if not cond or not result or cond[0] < end or cond[1] > result[0]:
        return stop('Displayed se pattern requires a fronted condition followed by its result.')
    if text[end:cond[0]].strip() or any(c.isalnum() for c in text[cond[1]:result[0]]):
        return stop('Condition/result spans omit intervening content.')
    return emit(0, [('v', cond), ('c', result)],
                'Adverbial se condition attaches to a matrix result, retaining its modal chain.')
