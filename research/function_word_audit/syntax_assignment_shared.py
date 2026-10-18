"""Shared syntactic matchers across Portuguese and Spanish function-word suites.

Prioritises reliable assignments and correct highlighting over recognizing every use.
Uses dependency parse structure, grammatical features, and explicit semantic/lexical
licences. Reusable across both languages wherever grammatical structures align.
"""
from __future__ import annotations

import re
from typing import Any

# Lexical licences shared or language-keyed
THOUGHT_VERBS = {
    'pt': {'achar', 'pensar', 'saber', 'dizer', 'esperar', 'crer', 'supor',
           'lembrar', 'esquecer', 'acreditar', 'afirmar', 'contar', 'sentir', 'notar'},
    'es': {'creer', 'pensar', 'saber', 'decir', 'esperar', 'suponer',
           'recordar', 'olvidar', 'afirmar', 'contar', 'sentir', 'notar'}
}

MOTION_VERBS = {
    'pt': {'ir', 'vir', 'chegar', 'voltar', 'subir', 'descer', 'entrar', 'sair',
           'passar', 'caminhar', 'correr', 'levar', 'trazer'},
    'es': {'ir', 'venir', 'llegar', 'volver', 'subir', 'bajar', 'entrar', 'salir',
           'pasar', 'caminar', 'correr', 'llevar', 'traer'}
}

TIME_HEADS = {
    'pt': {'tempo', 'momento', 'dia', 'noite', 'tarde', 'manhã', 'ano', 'mês',
           'semana', 'hora', 'época', 'verão', 'inverno', 'século', 'vez', 'minuto'},
    'es': {'tiempo', 'momento', 'día', 'noche', 'tarde', 'mañana', 'año', 'mes',
           'semana', 'hora', 'época', 'verano', 'invierno', 'siglo', 'vez', 'minuto'}
}

DESTINATION_HEADS = {
    'pt': {'casa', 'escola', 'hospital', 'trabalho', 'cidade', 'aeroporto', 'praia',
           'parque', 'cinema', 'quarto', 'hotel', 'restaurante', 'mercado', 'estação',
           'universidade', 'igreja', 'porto', 'banco', 'teatro'},
    'es': {'casa', 'colegio', 'escuela', 'hospital', 'trabajo', 'ciudad', 'aeropuerto',
           'playa', 'parque', 'cine', 'habitación', 'hotel', 'restaurante', 'mercado',
           'estación', 'universidad', 'iglesia', 'puerto', 'banco', 'teatro', 'estadio'}
}

COMPARATIVE_MARKERS = {
    'pt': {'mais', 'menos', 'melhor', 'pior', 'maior', 'menor'},
    'es': {'más', 'menos', 'mejor', 'peor', 'mayor', 'menor'}
}

DE_VERBAL_FRAMES = {
    'pt': {'gostar', 'precisar', 'lembrar', 'depender', 'esquecer', 'tratar',
           'falar', 'desistir', 'parar', 'acabar', 'deixar', 'cuidar'},
    'es': {'dejar', 'acabar', 'tratar', 'parar', 'hablar', 'cuidar',
           'acordar', 'depender', 'olvidar'}
}

DE_ACTION_NOUNS = {
    'pt': {'hora', 'momento', 'jeito', 'maneira', 'forma', 'vontade', 'medo', 'tempo',
           'copo', 'mesa', 'dia', 'carro', 'casa', 'homem'},
    'es': {'hora', 'momento', 'manera', 'forma', 'ganas', 'miedo', 'tiempo',
           'vaso', 'mesa', 'día', 'coche', 'casa', 'hombre'}
}

MODAL_VERBS = {
    'pt': {'poder', 'dever', 'querer', 'ter', 'ir', 'costumar', 'precisar'},
    'es': {'poder', 'deber', 'querer', 'tener', 'ir', 'soler', 'necesitar'}
}

HUMAN_HEADS = {
    'pt': {'alguém', 'amigo', 'amiga', 'homem', 'mulher', 'rapaz', 'moça', 'garoto', 'menino', 'menina',
           'pessoa', 'gente', 'pai', 'mãe', 'filho', 'filha', 'irmão', 'irmã', 'família', 'pais',
           'namorado', 'namorada', 'marido', 'esposa', 'senhor', 'senhora', 'doutor', 'médico',
           'professor', 'polícia', 'chefe', 'colega'},
    'es': {'alguien', 'amigo', 'amiga', 'hombre', 'mujer', 'chico', 'chica', 'muchacho', 'muchacha',
           'niño', 'niña', 'persona', 'gente', 'padre', 'madre', 'hijo', 'hija', 'hermano', 'hermana',
           'familia', 'padres', 'novio', 'novia', 'marido', 'esposa', 'señor', 'señora', 'doctor',
           'médico', 'profesor', 'policía', 'jefe', 'colega'}
}

PERSONAL_A_VERBS = {
    'conocer', 'ver', 'mirar', 'escuchar', 'oír', 'amar', 'querer', 'odiar', 'respetar',
    'buscar', 'encontrar', 'esperar', 'llamar', 'invitar', 'saludar', 'ayudar', 'acompañar',
    'entender', 'comprender', 'visitar', 'proteger', 'cuidar'
}

A_IDIOM_HEADS = {
    'pt': {'propósito', 'favor', 'pé', 'tempo', 'vezes', 'sério', 'solas', 'fundo', 'bordo', 'toa', 'vontade'},
    'es': {'propósito', 'favor', 'pie', 'tiempo', 'veces', 'menudo', 'serio', 'solas', 'fondo', 'bordo', 'cabo', 'pesar'}
}

POR_IDIOM_HEADS = {
    'pt': {'favor', 'exemplo', 'fim', 'acaso', 'sorte', 'suposto', 'vezes'},
    'es': {'favor', 'ejemplo', 'fin', 'acaso', 'suerte', 'supuesto', 'veces'}
}

CON_IDIOM_HEADS = {
    'pt': {'cuidado', 'calma', 'certeza', 'frequência', 'facilidade', 'medo', 'pressa'},
    'es': {'cuidado', 'calma', 'certeza', 'frecuencia', 'facilidad', 'miedo', 'prisa'}
}

PATH_HEADS = {
    'pt': {'rua', 'estrada', 'caminho', 'cidade', 'porta', 'janela', 'mar', 'ar', 'terra', 'floresta', 'bosque', 'ponte', 'corredor'},
    'es': {'calle', 'carretera', 'camino', 'ciudad', 'puerta', 'ventana', 'mar', 'aire', 'tierra', 'bosque', 'puente', 'pasillo'}
}

CAUSE_HEADS = {
    'pt': {'culpa', 'motivo', 'razão', 'causa', 'medo', 'acidente', 'erro', 'isso', 'aquilo'},
    'es': {'culpa', 'motivo', 'razón', 'causa', 'miedo', 'accidente', 'error', 'eso', 'aquello'}
}

INSTRUMENT_HEADS = {
    'pt': {'caneta', 'faca', 'colher', 'garfo', 'chave', 'carro', 'martelo', 'arma', 'telefone', 'computador', 'livro', 'dinheiro', 'água', 'mão'},
    'es': {'bolígrafo', 'pluma', 'cuchillo', 'cuchara', 'tenedor', 'llave', 'coche', 'martillo', 'arma', 'pistola', 'teléfono', 'ordenador', 'computadora', 'libro', 'dinero', 'agua', 'mano'}
}

LOCATIVE_HEADS = {
    'pt': {'casa', 'quarto', 'cidade', 'país', 'rua', 'estrada', 'escola', 'hospital',
           'trabalho', 'escritório', 'parque', 'praça', 'praia', 'mar', 'floresta', 'bosque',
           'hotel', 'restaurante', 'bar', 'loja', 'sala', 'cozinha', 'jardim', 'prédio',
           'edifício', 'igreja', 'banco', 'cinema', 'teatro', 'aeroporto', 'estação',
           'porto', 'ilha', 'rio', 'montanha', 'mundo', 'terra', 'chão', 'mesa', 'cama',
           'prisão', 'manicômio', 'tribunal', 'universidade', 'apartamento', 'quarto',
           'banheiro', 'estádio', 'campo', 'vila', 'aldeia', 'carro', 'ônibus', 'trem',
           'avião', 'barco', 'navio', 'gaveta', 'bolsa', 'bolso', 'caixa', 'parede', 'lado', 'lugar'},
    'es': {'casa', 'habitación', 'cuarto', 'ciudad', 'país', 'calle', 'carretera', 'camino',
           'escuela', 'colegio', 'hospital', 'trabajo', 'oficina', 'parque', 'plaza', 'playa',
           'mar', 'bosque', 'hotel', 'restaurante', 'bar', 'tienda', 'sala', 'cocina',
           'jardín', 'edificio', 'iglesia', 'banco', 'cine', 'teatro', 'aeropuerto',
           'estación', 'puerto', 'isla', 'río', 'montaña', 'mundo', 'tierra', 'suelo',
           'mesa', 'cama', 'prisión', 'cárcel', 'manicomio', 'tribunal', 'universidad',
           'apartamento', 'departamento', 'piso', 'baño', 'estadio', 'campo', 'pueblo',
           'aldea', 'coche', 'auto', 'autobús', 'tren', 'avión', 'barco', 'cajón', 'bolso',
           'bolsillo', 'caja', 'pared', 'lado', 'lugar', 'sitio'}
}

LOCATIVE_VERBS = {
    'pt': {'estar', 'viver', 'morar', 'ficar', 'trabalhar', 'nascer', 'morrer', 'dormir',
           'entrar', 'cair', 'sentar', 'deitar', 'passar', 'colocar', 'pôr', 'guardar'},
    'es': {'estar', 'vivir', 'morar', 'quedar', 'quedarse', 'trabajar', 'nacer', 'morir',
           'dormir', 'entrar', 'caer', 'sentar', 'sentarse', 'acostar', 'pasar', 'poner', 'guardar'}
}

ABSTRACT_STATE_HEADS = {
    'pt': {'necesidade', 'necessidade', 'dúvida', 'perigo', 'paz', 'calma', 'segredo', 'realidade',
           'geral', 'efeito', 'teoria', 'vão', 'prática', 'silêncio', 'choque', 'pânico',
           'tentativa', 'vida', 'caso', 'ordem', 'modo', 'forma', 'jeito', 'mudança', 'situação',
           'amor', 'risco', 'verdade', 'conta', 'graça'},
    'es': {'necesidad', 'duda', 'peligro', 'paz', 'calma', 'secreto', 'realidad',
           'general', 'efecto', 'teoría', 'vano', 'práctica', 'silencio', 'shock', 'pánico',
           'intento', 'vida', 'caso', 'orden', 'modo', 'forma', 'cambio', 'situación',
           'amor', 'riesgo', 'verdad', 'cuenta', 'gracia'}
}



def _features(node: dict[str, Any]) -> dict[str, str]:
    feats = node.get('feats') or ''
    if isinstance(feats, dict):
        return feats
    return dict(part.split('=', 1) for part in feats.split('|') if '=' in part)


def _bounds(node: dict[str, Any]) -> tuple[int, int]:
    return node['token']['start_char'], node['token']['end_char']


def _kids(sent: list[dict[str, Any]], node: dict[str, Any]) -> list[dict[str, Any]]:
    return [n for n in sent if n['head'] == node['id']]


def _subtree(sent: list[dict[str, Any]], node: dict[str, Any]) -> list[dict[str, Any]]:
    ids = {node['id']}
    while True:
        more = {n['id'] for n in sent if n['head'] in ids}
        if more <= ids:
            break
        ids |= more
    return [n for n in sent if n['id'] in ids]


def _constituent_interval(sent: list[dict[str, Any]],
                          nodes: list[dict[str, Any]],
                          focus: tuple[int, int],
                          text: str) -> tuple[int, int] | None:
    nodes = [n for n in nodes if n['upos'] != 'PUNCT' and _bounds(n) != focus]
    if not nodes:
        return None
    spans = {_bounds(n) for n in nodes}
    a = min(x[0] for x in spans)
    b = max(x[1] for x in spans)
    # Must not engulf the focus token
    if a < focus[1] and b > focus[0]:
        return None
    # Must not contain foreign tokens within the range
    node_ids = {n['id'] for n in nodes}
    for n in sent:
        if n['upos'] != 'PUNCT':
            nb = _bounds(n)
            if a <= nb[0] and nb[1] <= b and n['id'] not in node_ids:
                return None
    # Strip trailing punctuation from text range
    while b > a and text[b - 1] in ' \t\r\n.,;:!?"\'»«—-)':
        b -= 1
    while a < b and text[a] in ' \t\r\n.,;:!?"\'»«—(-':
        a += 1
    if a >= b:
        return None
    return a, b


def _verb_complex(sent: list[dict[str, Any]],
                  verb: dict[str, Any],
                  focus: tuple[int, int],
                  lang: str,
                  text: str) -> tuple[int, int] | None:
    modals = MODAL_VERBS.get(lang, set())
    selected = [verb] + [n for n in _kids(sent, verb) if n['deprel'] in {'aux', 'aux:pass', 'compound:prt'}]
    byid = {n['id']: n for n in sent}
    parent = byid.get(verb['head'])
    if parent and verb['deprel'] == 'xcomp' and parent['lemma'].lower() in modals:
        selected += [parent] + [n for n in _kids(sent, parent) if n['deprel'] in {'aux', 'aux:pass'}]
    return _constituent_interval(sent, selected, focus, text)


def _noun_phrase(sent: list[dict[str, Any]],
                 noun: dict[str, Any],
                 focus: tuple[int, int],
                 text: str) -> tuple[int, int] | None:
    # Noun plus determiners, adjectives, numerals, compounds
    ids = {noun['id']}
    while True:
        more = {n['id'] for n in sent if n['head'] in ids
                and n['deprel'] in {'det', 'det:poss', 'amod', 'nummod', 'compound',
                                   'flat', 'flat:name', 'nmod:poss'}
                and _bounds(n) != focus}
        if more <= ids:
            break
        ids |= more
    nodes = [n for n in sent if n['id'] in ids]
    return _constituent_interval(sent, nodes, focus, text)


def _emit(pattern: int,
          parts: list[tuple[str, tuple[int, int] | None]],
          reason: str,
          focus: tuple[int, int],
          text: str,
          evidence: dict[str, Any]) -> dict[str, Any]:
    if any(span is None for _, span in parts):
        return dict(status='abstain', reason='No complete contiguous constituent span.', evidence=evidence)
    chunks = [dict(slot='connector', start=focus[0], end=focus[1])]
    for slot, span in parts:
        assert span is not None
        chunks.append(dict(slot=slot, start=span[0], end=span[1]))
    chunks.sort(key=lambda c: c['start'])
    # Validate chunks
    if any(c['start'] < 0 or c['start'] >= c['end'] or c['end'] > len(text) for c in chunks):
        return dict(status='abstain', reason='Invalid constituent boundaries.', evidence=evidence)
    if any(a['end'] > b['start'] for a, b in zip(chunks, chunks[1:])):
        return dict(status='abstain', reason='Overlapping constituent chunks.', evidence=evidence)
    for c in chunks:
        c['text'] = text[c['start']:c['end']]
    return dict(status='candidate', pattern=pattern, chunks=chunks, reason=reason, evidence=evidence)


def decide_shared(row: dict[str, Any], obs: dict[str, Any] | None) -> dict[str, Any] | None:
    """Unified syntactic matcher for function words across Portuguese and Spanish."""
    if not obs:
        return None
    lang, word = row.get('language'), row.get('word')
    if not lang or not word:
        return None
    text = row.get('sentence', '')
    spans = obs.get('spans') or []
    if len(spans) != 1 or len(spans[0]) != 2:
        return None
    start, end = spans[0]
    if not (0 <= start < end <= len(text)) or text[start:end].casefold() != word.casefold():
        return None

    sentences = obs.get('sentences') or []
    hits = [(s, n) for s in sentences for n in s
            if (n['token']['start_char'], n['token']['end_char']) == (start, end)]
    if len(hits) != 1:
        return None
    sent, focus = hits[0]
    byid = {n['id']: n for n in sent}
    head = byid.get(focus['head'])
    focus_bounds = (start, end)
    evidence = {'focus': focus, 'head': head, 'parser': obs.get('parser')}

    def stop(reason: str) -> dict[str, Any]:
        return dict(status='abstain', reason=reason, evidence=evidence)

    # -------------------------------------------------------------
    # 1. Demonstrative & Indefinite Pronouns as Subjects: eso, esto, todo, algo / isso, isto, tudo
    # Formula: [connector] + [v: verb]
    # -------------------------------------------------------------
    subject_pron_patterns = {
        ('es', 'eso'): 0, ('es', 'esto'): 0, ('es', 'todo'): 0, ('es', 'algo'): 0,
        ('pt', 'isso'): 0, ('pt', 'isto'): 0, ('pt', 'tudo'): 0
    }
    if (lang, word) in subject_pron_patterns:
        pat = subject_pron_patterns[(lang, word)]
        if focus['deprel'] in {'nsubj', 'nsubj:pass'} and head and head['upos'] in {'VERB', 'AUX'}:
            v_span = _verb_complex(sent, head, focus_bounds, lang, text)
            if v_span:
                return _emit(pat, [('v', v_span)], f'Demonstrative/indefinite subject {word} attached to verb.',
                             focus_bounds, text, evidence)
        if word == 'algo' and focus['deprel'] in {'obj', 'iobj'} and head and head['upos'] in {'VERB', 'AUX'}:
            # algo can also be object (formula: verb + algo)
            v_span = _verb_complex(sent, head, focus_bounds, lang, text)
            if v_span and v_span[1] <= start:
                return _emit(0, [('v', v_span)], 'Indefinite object algo following verb.',
                             focus_bounds, text, evidence)

    # -------------------------------------------------------------
    # 2. Clitic Object Pronouns: me, te, nos, le/lhe, la, lo, los, o, a, os, as
    # Formula: [connector] + [v: verb] (or verb + connector)
    # -------------------------------------------------------------
    clitic_patterns = {
        ('es', 'me'): 0, ('es', 'te'): 0, ('es', 'nos'): 0, ('es', 'le'): 0,
        ('es', 'la'): 1, ('es', 'lo'): 1, ('es', 'los'): 1,
        ('pt', 'me'): 0, ('pt', 'te'): 0, ('pt', 'nos'): 0, ('pt', 'lhe'): 0,
        ('pt', 'o'): 1, ('pt', 'a'): 2, ('pt', 'os'): 1
    }
    if (lang, word) in clitic_patterns and focus['upos'] == 'PRON' and focus['deprel'] in {'obj', 'iobj', 'expl', 'expl:pv'}:
        pat = clitic_patterns[(lang, word)]
        if head and head['upos'] in {'VERB', 'AUX'}:
            # Check for reflexive me in pt (me:1 is verb + -me)
            if lang == 'pt' and word == 'me' and _features(head).get('Person') == '1':
                if _bounds(head)[1] <= start:
                    pat = 1  # Myself / part of a verb
            v_span = _verb_complex(sent, head, focus_bounds, lang, text)
            if v_span:
                return _emit(pat, [('v', v_span)], f'Clitic pronoun {word} governed by verb.',
                             focus_bounds, text, evidence)

    # -------------------------------------------------------------
    # 3. Preposition + Infinitive: para, al / ao
    # -------------------------------------------------------------
    # es: para:0 is verb + para + infinitive, pt: para:1 is verb + para + infinitive
    if (lang, word) in {('es', 'para'), ('pt', 'para')} and head and head['upos'] in {'VERB', 'AUX'}:
        hf = _features(head)
        if hf.get('VerbForm') == 'Inf' and focus['deprel'] == 'mark':
            pat = 0 if lang == 'es' else 1
            # c is the infinitive subtree
            inf_span = _constituent_interval(sent, _subtree(sent, head), focus_bounds, text)
            gov = byid.get(head['head'])
            v_span = _verb_complex(sent, gov, focus_bounds, lang, text) if (gov and gov['upos'] in {'VERB', 'AUX'}) else None
            parts = [('c', inf_span)]
            if v_span and v_span[1] <= start:
                parts.insert(0, ('v', v_span))
            if inf_span:
                return _emit(pat, parts, f'{word} introducing infinitive purpose clause.',
                             focus_bounds, text, evidence)

    # es: al:1 / pt: ao:1 is al/ao + infinitive (when doing something)
    if (lang, word) in {('es', 'al'), ('pt', 'ao')} and head and head['upos'] in {'VERB', 'AUX'}:
        hf = _features(head)
        if hf.get('VerbForm') == 'Inf' and focus['deprel'] in {'mark', 'case'}:
            v_span = _verb_complex(sent, head, focus_bounds, lang, text)
            if v_span and v_span[0] >= end:
                return _emit(1, [('v', v_span)], f'{word} with infinitive temporal reading.',
                             focus_bounds, text, evidence)

    # -------------------------------------------------------------
    # 4. Prepositional Phrases: en/em, a, para, con/com, por, sin/sem, sobre, até
    # -------------------------------------------------------------
    # en/em:0 (place) vs en/em:1 (time)
    if (lang, word) in {('es', 'en'), ('pt', 'em')} and head and focus['deprel'] == 'case':
        hl = head['lemma'].lower()
        pat = None
        if hl in TIME_HEADS[lang]:
            pat = 1
        else:
            gov = byid.get(head['head'])
            gl = gov['lemma'].lower() if gov else ''
            is_place = hl in LOCATIVE_HEADS.get(lang, set()) or hl in DESTINATION_HEADS.get(lang, set())
            is_loc_verb = gov and gl in LOCATIVE_VERBS.get(lang, set())
            if (is_place or is_loc_verb) and hl not in ABSTRACT_STATE_HEADS.get(lang, set()) and head['upos'] in {'NOUN', 'PROPN'}:
                pat = 0

        # Strict abstention if neither time nor place is positively licensed
        if pat is None:
            return None

        gov = byid.get(head['head'])
        v_span = _verb_complex(sent, gov, focus_bounds, lang, text) if (gov and gov['upos'] in {'VERB', 'AUX'}) else None
        c_span = _noun_phrase(sent, head, focus_bounds, text) or _constituent_interval(sent, _subtree(sent, head), focus_bounds, text)
        parts = [('c', c_span)]
        if v_span and v_span[1] <= start:
            parts.insert(0, ('v', v_span))
        if c_span:
            return _emit(pat, parts, f'Preposition {word} governing {"temporal" if pat==1 else "locative"} nominal.',
                         focus_bounds, text, evidence)

    # a:0 (where to: destination) vs a:1 (es: before a person)
    if (lang, word) in {('es', 'a'), ('pt', 'a')} and focus['upos'] == 'ADP' and focus['deprel'] == 'case' and head:
        gov = byid.get(head['head'])
        hl = head['lemma'].lower()
        gl = gov['lemma'].lower() if gov else ''
        if hl in A_IDIOM_HEADS.get(lang, set()):
            return None

        pat = None
        # Spanish personal a (a:1): requires human nominal, personal pronoun, or animacy feature governed by transitive verb / obj deprel
        if lang == 'es':
            is_person = (head['upos'] == 'PRON' or _features(head).get('Animacy') == 'Anim' or hl in HUMAN_HEADS['es'])
            is_transitive_contact = (head['deprel'] in {'obj', 'iobj'} or gl in PERSONAL_A_VERBS)
            if is_person and (is_transitive_contact or gl not in MOTION_VERBS['es']):
                pat = 1

        # Where to: destination (a:0 in both ES and PT): requires motion verb governor OR destination noun head
        if pat is None:
            is_motion = gl in MOTION_VERBS.get(lang, set())
            is_dest_head = hl in DESTINATION_HEADS.get(lang, set())
            if is_dest_head or (is_motion and head['upos'] in {'NOUN', 'PROPN'} and hl not in HUMAN_HEADS.get(lang, set())):
                pat = 0

        # Strict abstention if neither pattern is positively licensed
        if pat is None:
            return None

        v_span = _verb_complex(sent, gov, focus_bounds, lang, text) if (gov and gov['upos'] in {'VERB', 'AUX'}) else None
        c_span = _noun_phrase(sent, head, focus_bounds, text) or _constituent_interval(sent, _subtree(sent, head), focus_bounds, text)
        parts = [('c', c_span)]
        if v_span and v_span[1] <= start:
            parts.insert(0, ('v', v_span))
        if c_span:
            return _emit(pat, parts, f'Preposition a pattern {pat}.', focus_bounds, text, evidence)

    # con/com:0 (who with: person) vs con/com:1 (how/with what: instrument/tool)
    if (lang, word) in {('es', 'con'), ('pt', 'com')} and focus['deprel'] == 'case' and head:
        gov = byid.get(head['head'])
        hl = head['lemma'].lower()
        if hl in CON_IDIOM_HEADS.get(lang, set()):
            return None

        pat = None
        # Person / Accompaniment (pat = 0)
        if head['upos'] == 'PRON' or _features(head).get('Animacy') == 'Anim' or hl in HUMAN_HEADS.get(lang, set()):
            pat = 0
        # Instrument / Tool (pat = 1)
        elif hl in INSTRUMENT_HEADS.get(lang, set()) or (head['upos'] == 'NOUN' and hl not in {'amor', 'cuidado', 'calma', 'paz', 'alegria', 'certeza'} and gov and gov['upos'] == 'VERB' and hl in {'faca', 'cuchillo', 'mano', 'mão', 'arma', 'carro', 'coche', 'caneta', 'lápiz'}):
            pat = 1

        # Strict abstention if neither accompaniment nor instrument is positively licensed
        if pat is None:
            return None

        v_span = _verb_complex(sent, gov, focus_bounds, lang, text) if (gov and gov['upos'] in {'VERB', 'AUX'}) else None
        c_span = _noun_phrase(sent, head, focus_bounds, text) or _constituent_interval(sent, _subtree(sent, head), focus_bounds, text)
        parts = [('c', c_span)]
        if v_span and v_span[1] <= start:
            parts.insert(0, ('v', v_span))
        if c_span:
            return _emit(pat, parts, f'Preposition {word} pattern {pat}.', focus_bounds, text, evidence)

    # por:0 (why/cause) vs por:1 (through/along/motion)
    if (lang, word) in {('es', 'por'), ('pt', 'por')} and focus['deprel'] == 'case' and head:
        gov = byid.get(head['head'])
        gl = gov['lemma'].lower() if gov else ''
        hl = head['lemma'].lower()
        if hl in POR_IDIOM_HEADS.get(lang, set()):
            return None

        pat = None
        # Motion / Path (pat = 1): nominal head MUST be a path or physical passage
        if hl in PATH_HEADS.get(lang, set()) and hl not in {'vida', 'amor', 'dinheiro', 'deus', 'medo', 'culpa'}:
            pat = 1
        elif gl in MOTION_VERBS.get(lang, set()) and hl in {'porta', 'janela', 'rua', 'estrada', 'ponte', 'caminho', 'corredor', 'túnel'}:
            pat = 1
        # Cause / Reason / Motive (pat = 0): reason, purpose, reaction, emotional motive (e.g. por suas vidas)
        elif hl in CAUSE_HEADS.get(lang, set()) or hl in {'vida', 'vidas', 'razão', 'motivo', 'culpa', 'causa', 'medo', 'dinheiro', 'amor', 'segurança', 'sobrevivência'} or (gov and gl in {'preocupar', 'disculpar', 'pedir', 'agradecer', 'llorar', 'chorar', 'odiar', 'culpar', 'brigar', 'pelear', 'lutar', 'luchar'}):
            pat = 0

        # Strict abstention if neither path nor cause is positively licensed
        if pat is None:
            return None

        v_span = _verb_complex(sent, gov, focus_bounds, lang, text) if (gov and gov['upos'] in {'VERB', 'AUX'}) else None
        c_span = _noun_phrase(sent, head, focus_bounds, text) or _constituent_interval(sent, _subtree(sent, head), focus_bounds, text)
        parts = [('c', c_span)]
        if v_span and v_span[1] <= start:
            parts.insert(0, ('v', v_span))
        if c_span:
            return _emit(pat, parts, f'Preposition {word} pattern {pat}.', focus_bounds, text, evidence)

    # sin/sem:0 (without)
    if (lang, word) in {('es', 'sin'), ('pt', 'sem')} and head and focus['deprel'] in {'case', 'mark'}:
        gov = byid.get(head['head'])
        v_span = _verb_complex(sent, gov, focus_bounds, lang, text) if (gov and gov['upos'] in {'VERB', 'AUX'}) else None
        c_span = _constituent_interval(sent, _subtree(sent, head), focus_bounds, text)
        parts = [('c', c_span)]
        if v_span and v_span[1] <= start:
            parts.insert(0, ('v', v_span))
        if c_span:
            return _emit(0, parts, f'Preposition {word} privation pattern.', focus_bounds, text, evidence)

    # sobre:0 (about: topic) vs sobre:1 (on/above: place)
    if lang == 'pt' and word == 'sobre' and head and focus['deprel'] == 'case':
        hl = head['lemma'].lower()
        gov = byid.get(head['head'])
        gl = gov['lemma'].lower() if gov else ''
        pat = None

        # Topic (pat = 0): governed by media/information noun or communication/thought verb
        topic_governors = {'revista', 'livro', 'artigo', 'filme', 'notícia', 'história', 'documentário',
                           'falar', 'conversar', 'discutir', 'escrever', 'pensar', 'saber', 'ler', 'perguntar',
                           'dizer', 'contar', 'ensinar', 'aprender', 'debater', 'estudar'}
        if gl in topic_governors or hl in {'assunto', 'tema', 'história', 'vida', 'cidade', 'país', 'futuro',
                                           'passado', 'amor', 'mundo', 'política', 'música', 'trabalho', 'isso', 'aquilo'}:
            pat = 0
        # On/Above (pat = 1): physical surface (mesa, chão, cama, balcão, telhado)
        elif hl in {'mesa', 'chão', 'cama', 'balcão', 'terra', 'superfície', 'telhado', 'prato', 'estrada', 'muro', 'teto', 'parede'}:
            pat = 1

        if pat is None:
            return None

        v_span = _verb_complex(sent, gov, focus_bounds, lang, text) if (gov and gov['upos'] in {'VERB', 'AUX'}) else None
        c_span = _noun_phrase(sent, head, focus_bounds, text) or _constituent_interval(sent, _subtree(sent, head), focus_bounds, text)
        parts = [('c', c_span)]
        if v_span and v_span[1] <= start:
            parts.insert(0, ('v', v_span))
        if c_span:
            return _emit(pat, parts, f'Preposition sobre pattern {pat}.', focus_bounds, text, evidence)

    # até:0 (until/endpoint) vs até:1 (even: focus particle)
    if lang == 'pt' and word == 'até' and head:
        pat = None
        if focus['deprel'] in {'advmod', 'discourse'} and head['upos'] in {'NOUN', 'PRON', 'PROPN'}:
            pat = 1
        elif focus['deprel'] == 'case' and (head['lemma'].lower() in DESTINATION_HEADS.get(lang, set()) or head['lemma'].lower() in TIME_HEADS.get(lang, set())):
            pat = 0

        if pat is None:
            return None

        gov = byid.get(head['head'])
        v_span = _verb_complex(sent, gov, focus_bounds, lang, text) if (gov and gov['upos'] in {'VERB', 'AUX'}) else None
        c_span = _constituent_interval(sent, _subtree(sent, head), focus_bounds, text)
        parts = [('c', c_span)]
        if pat == 0 and v_span and v_span[1] <= start:
            parts.insert(0, ('v', v_span))
        if c_span:
            return _emit(pat, parts, f'Até pattern {pat}.', focus_bounds, text, evidence)

    # -------------------------------------------------------------
    # 5. Clausal & Sentential Connectors: pero/mas, si/se, porque, cuando/quando, y/e, como
    # -------------------------------------------------------------
    # pero:0 (es) / mas:0 (pt) - Adversative coordination
    if (lang, word) in {('es', 'pero'), ('pt', 'mas')} and focus['deprel'] in {'cc', 'advmod'} and head:
        c_span = _constituent_interval(sent, [n for n in _subtree(sent, head) if _bounds(n)[0] >= end], focus_bounds, text)
        gov = byid.get(head['head']) or head
        # Left clause
        left_nodes = [n for n in sent if _bounds(n)[1] <= start and n['upos'] != 'PUNCT']
        v_span = _constituent_interval(sent, left_nodes, focus_bounds, text)
        parts = [('c', c_span)]
        if v_span:
            parts.insert(0, ('v', v_span))
        if c_span:
            return _emit(0, parts, f'Adversative conjunction {word}.', focus_bounds, text, evidence)

    # si:0 (es) / se:0 (pt) - Conditional clause (if situation, then result; NOT indirect question whether)
    if ((lang == 'es' and word == 'si') or (lang == 'pt' and word == 'se' and focus['deprel'] == 'mark')) and head:
        gov = byid.get(head['head'])
        gl = gov['lemma'].lower() if gov else ''
        # Block indirect questions ("whether") governed by verbs of asking/wondering/doubting or functioning as ccomp/obj
        if head.get('deprel') in {'ccomp', 'obj'} or gl in {'preguntar', 'dudar', 'averiguar', 'perguntar', 'duvidar'}:
            return None

        c_span = _constituent_interval(sent, [n for n in _subtree(sent, head) if _bounds(n)[0] >= end], focus_bounds, text)
        v_span = _verb_complex(sent, gov, focus_bounds, lang, text) if (gov and gov['upos'] in {'VERB', 'AUX'}) else None
        parts = [('c', c_span)]
        if v_span:
            parts.append(('v', v_span)) if v_span[0] >= end else parts.insert(0, ('v', v_span))
        if c_span:
            return _emit(0, parts, f'Conditional conjunction {word}.', focus_bounds, text, evidence)

    # porque:0 - Causal clause
    if word == 'porque' and head and focus['deprel'] == 'mark':
        c_span = _constituent_interval(sent, [n for n in _subtree(sent, head) if _bounds(n)[0] >= end], focus_bounds, text)
        gov = byid.get(head['head'])
        v_span = _verb_complex(sent, gov, focus_bounds, lang, text) if (gov and gov['upos'] in {'VERB', 'AUX'}) else None
        parts = [('c', c_span)]
        if v_span and v_span[1] <= start:
            parts.insert(0, ('v', v_span))
        if c_span:
            return _emit(0, parts, 'Causal conjunction porque.', focus_bounds, text, evidence)

    # cuando/quando:0 - Temporal clause
    if (lang, word) in {('es', 'cuando'), ('pt', 'quando')} and head and focus['deprel'] == 'mark':
        c_span = _constituent_interval(sent, [n for n in _subtree(sent, head) if _bounds(n)[0] >= end], focus_bounds, text)
        gov = byid.get(head['head'])
        v_span = _verb_complex(sent, gov, focus_bounds, lang, text) if (gov and gov['upos'] in {'VERB', 'AUX'}) else None
        parts = [('c', c_span)]
        if v_span and v_span[1] <= start:
            parts.insert(0, ('v', v_span))
        if c_span:
            return _emit(0, parts, f'Temporal conjunction {word}.', focus_bounds, text, evidence)

    # y:0 (es) / e:0 (pt) - Coordinating conjunction
    if (lang, word) in {('es', 'y'), ('pt', 'e')} and focus['deprel'] == 'cc' and head:
        c_span = _constituent_interval(sent, [n for n in _subtree(sent, head) if _bounds(n)[0] >= end], focus_bounds, text)
        left_nodes = [n for n in sent if _bounds(n)[1] <= start and n['head'] == head['head'] or n['id'] == head['head']]
        v_span = _constituent_interval(sent, left_nodes, focus_bounds, text)
        parts = [('c', c_span)]
        if v_span:
            parts.insert(0, ('v', v_span))
        if c_span:
            return _emit(0, parts, f'Coordinating conjunction {word}.', focus_bounds, text, evidence)

    # como:0 (comparison) vs como:1 (role/as)
    if word == 'como' and head:
        # Block interrogative/manner "how" ("¿Cómo estás?", "Como é suposto...", etc.)
        if text.rstrip().endswith('?') or start == 0:
            return None
        if focus.get('deprel') in {'advmod'} or _features(focus).get('PronType') == 'Int':
            return None

        gov = byid.get(head['head'])
        gl = gov['lemma'].lower() if gov else ''
        hl = head['lemma'].lower()
        v_span = _verb_complex(sent, gov, focus_bounds, lang, text) if (gov and gov['upos'] in {'VERB', 'AUX'}) else None

        pat = None
        # Pattern 1: Role / Job / Capacity (como + role/job)
        if focus['deprel'] == 'case' and head['upos'] in {'NOUN', 'PROPN'}:
            if hl in HUMAN_HEADS.get(lang, set()) or hl in {'ejemplo', 'exemplo', 'modelo', 'base', 'guía', 'guia', 'prueba', 'prova'}:
                pat = 1

        # Pattern 0: Comparison (verb + como: "Like / in the same way")
        # Formula strictly requires preceding verb: verb + como
        if pat is None:
            if v_span and v_span[1] <= start:
                pat = 0

        # Strict abstention if neither pattern applies
        if pat is None:
            return None

        c_span = _constituent_interval(sent, [n for n in _subtree(sent, head) if _bounds(n)[0] >= end], focus_bounds, text)
        parts = [('c', c_span)]
        if pat == 0 and v_span and v_span[1] <= start:
            parts.insert(0, ('v', v_span))
        if c_span:
            return _emit(pat, parts, f'Conjunction/preposition como pattern {pat}.', focus_bounds, text, evidence)

    # que:2 (comparative)
    if word == 'que' and head:
        prev_words = [n for n in sent if _bounds(n)[1] <= start and n['lemma'].lower() in COMPARATIVE_MARKERS.get(lang, set())]
        if prev_words:
            v_span = _bounds(prev_words[-1])
            c_span = _constituent_interval(sent, [n for n in _subtree(sent, head) if _bounds(n)[0] >= end], focus_bounds, text)
            if v_span and c_span:
                return _emit(2, [('v', v_span), ('c', c_span)], 'Comparative marker plus que.', focus_bounds, text, evidence)

    # Portuguese contractions: dele:0, dela:0 (noun + dele/dela)
    if lang == 'pt' and word in {'dele', 'dela'} and head and focus['deprel'] in {'nmod', 'nmod:poss'}:
        noun_span = _noun_phrase(sent, head, focus_bounds, text)
        if noun_span and noun_span[1] <= start:
            return _emit(0, [('v', noun_span)], f'Possessive contraction {word} modifying noun.', focus_bounds, text, evidence)

    # Portuguese ele:1 (after preposition)
    if lang == 'pt' and word == 'ele' and focus['deprel'] in {'obl', 'nmod', 'obl:arg'}:
        case_nodes = [n for n in _kids(sent, focus) if n['deprel'] == 'case' and _bounds(n)[1] <= start]
        if case_nodes:
            prep_span = _bounds(case_nodes[0])
            return _emit(1, [('v', prep_span)], 'Pronoun ele governed by preceding preposition.', focus_bounds, text, evidence)

    return None
