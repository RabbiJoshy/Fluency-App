"""Spanish patterns added 2026-10-19: todo "all the", reflexive me/te/nos, lo que.

Runs before every other decider. Returns None to defer, a candidate to assign,
or an abstention to block a weaker rule from misfiling the occurrence.

  es:todo:1   todo + el + noun        "All the"      (todo el día)
  es:me:1     me + verb, 1sg verb     "Myself"       (me levanto)
  es:te:1     te + verb, 2sg verb     "Yourself"     (te relajas)
  es:nos:1    nos + verb, 1pl verb    "Ourselves"    (nos fuimos)
  es:lo:2     lo + que + clause       "What"         (lo que quiero)

Reflexive me/te/nos: the clitic agrees with its verb's subject (me with a
first-person singular verb, and so on). That agreement is what separates
"me levanto" (I get up) from "me compró" (he bought me). Verbs with no person
(infinitives, gerunds) say nothing either way, so they keep the older rule.
"""
from syntax_assignment_shared import (_bounds, _constituent_interval, _emit,
                                      _features, _subtree, _verb_complex)

REFLEXIVE_AGREEMENT = {'me': ('1', 'Sing'), 'te': ('2', 'Sing'), 'nos': ('1', 'Plur')}
# "todo el mundo" is "everybody", not a transparent "all the world".
TODO_EXCLUDED_NOUNS = {'mundo'}


def decide_es_additions(row, obs):
    if row.get('language') != 'es' or row.get('word') not in {'todo', 'lo', *REFLEXIVE_AGREEMENT}:
        return None
    if not obs or len(obs.get('spans', [])) != 1:
        return None
    text, word = row['sentence'], row['word']
    start, end = obs['spans'][0]
    hits = [(s, n) for s in obs.get('sentences', []) for n in s if _bounds(n) == (start, end)]
    if len(hits) != 1:
        return None
    sent, focus = hits[0]
    byid = {n['id']: n for n in sent}
    head = byid.get(focus['head'])
    evidence = {'focus': focus, 'head': head, 'parser': obs.get('parser')}
    following = sorted((n for n in sent if _bounds(n)[0] >= end), key=lambda n: _bounds(n)[0])
    nxt = following[0] if following else None

    if word in REFLEXIVE_AGREEMENT:
        if focus['upos'] != 'PRON' or not head or head['upos'] not in {'VERB', 'AUX'}:
            return None
        verbs = [head] + [n for n in sent if n['head'] == head['id'] and n['deprel'] in {'aux', 'aux:pass'}]
        persons = {(_features(v).get('Person'), _features(v).get('Number')) for v in verbs if _features(v).get('Person')}
        if not persons:
            return None
        if REFLEXIVE_AGREEMENT[word] not in persons:
            return None  # e.g. "me compró": the older "me / to me" rule handles it.
        if _bounds(head)[0] < end:
            return None  # displayed formula is "me + verb"; after-verb forms abstain
        v_span = _verb_complex(sent, head, (start, end), 'es', text)
        if not v_span or text[end:v_span[0]].strip():
            return dict(status='abstain', reason='Reflexive clitic is not directly before its verb.', evidence=evidence)
        return _emit(1, [('v', v_span)], f'{word} agrees with its verb\'s subject: reflexive or pronominal verb.',
                     (start, end), text, evidence)

    if word == 'todo':
        if not nxt or nxt['lemma'] != 'el' or nxt['upos'] != 'DET' or focus['deprel'] not in {'det', 'amod', 'nmod'}:
            return None
        # spaCy hangs todo on the article ("todo → el → día"); others on the noun.
        if head and head['id'] == nxt['id']:
            head = byid.get(nxt['head'])
        if not head or head['upos'] != 'NOUN' or nxt['head'] != head['id']:
            return None
        if head['lemma'] in TODO_EXCLUDED_NOUNS:
            return dict(status='abstain', reason='todo el mundo means everybody, not "all the world".', evidence=evidence)
        phrase = _constituent_interval(sent, [n for n in _subtree(sent, head) if _bounds(n)[0] >= end], (start, end), text)
        if not phrase or text[end:phrase[0]].strip():
            return None
        return _emit(1, [('c', phrase)], 'todo before el + noun: "all the".', (start, end), text, evidence)

    if word == 'lo':
        if not nxt or nxt['text'].casefold() != 'que' or text[end:_bounds(nxt)[0]].strip():
            return None
        rel = byid.get(nxt['head'])
        clause = [n for n in _subtree(sent, rel) if _bounds(n)[0] >= end] if rel else []
        span = _constituent_interval(sent, clause, (start, end), text) if clause else None
        if not span or span[0] != _bounds(nxt)[0]:
            return dict(status='abstain', reason='lo que lacks a complete clause after it.', evidence=evidence)
        return _emit(2, [('c', span)], 'lo + que + clause: "what / the thing that".', (start, end), text, evidence)
    return None
