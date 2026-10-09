"""Deterministic construction and periphrasis gating for closed-menu WSD.

Covers grammar verbs (Causes 8-11), pronoun function gating (Cause 12), and
governed prepositions (Cause 19).

Discrete and relational: when a syntactic periphrasis or structural construction
is unambiguously present in the context, candidate senses are partitioned into
those matching the grammatical function versus rare/lexical misinterpretations.
"""

from __future__ import annotations

import re
import unicodedata
from typing import Any, Mapping, Sequence

from fluency.wsd.menus import MenuAnalysis, SenseLeaf


# Progressive auxiliary verbs and patterns
_ES_GERUND = re.compile(r"\b\w+(?:ando|iendo|yendo)\b", re.I)
_PT_GERUND = re.compile(r"\b\w+ndo\b", re.I)
_PT_EU_PROGRESSIVE = re.compile(r"\ba\s+\w+[aei]r\b", re.I)

_ES_ESTAR_FORMS = frozenset({
    "estoy", "estas", "estás", "esta", "está", "estamos", "estais", "estáis", "estan", "están",
    "estuve", "estuviste", "estuvo", "estuvimos", "estuvisteis", "estuvieron",
    "estaba", "estabas", "estabamos", "estábamos", "estabais", "estaban",
    "este", "esté", "estes", "estés", "estemos", "esteis", "estéis", "esten", "estén",
    "estuviera", "estuvieras", "estuvieramos", "estuviéramos", "estuvieran",
    "estar", "estando",
})

_PT_ESTAR_ANDAR_FORMS = frozenset({
    "estou", "estas", "estás", "esta", "está", "estamos", "estais", "estao", "estão",
    "estive", "estiveste", "esteve", "estivemos", "estivestes", "estiveram",
    "estava", "estavas", "estavamos", "estávamos", "estavam",
    "esteja", "estejas", "estejamos", "estejam",
    "estiver", "estiveres", "estivermos", "estiverem",
    "estar", "estando", "to", "tô", "ta", "tá", "tamos", "tão",
    "ando", "andas", "anda", "andamos", "andam", "andava", "andavam", "andar", "andando",
})

# Modal obligation verbs
_ES_TENER_FORMS = frozenset({
    "tengo", "tienes", "tiene", "tenemos", "teneis", "tenéis", "tienen",
    "tuve", "tuviste", "tuvo", "tuvimos", "tuvisteis", "tuvieron",
    "tenia", "tenía", "tenias", "tenías", "teniamos", "teníamos", "tenian", "tenían",
    "tenga", "tengas", "tengamos", "tengan", "tener", "teniendo",
})

_PT_TER_FORMS = frozenset({
    "tenho", "tens", "tem", "temos", "tendes", "tem", "têm",
    "tive", "tiveste", "teve", "tivemos", "tivestes", "tiveram",
    "tinha", "tinhas", "tinhamos", "tínhamos", "tinham",
    "tenha", "tenhas", "tenhamos", "tenham",
    "tiver", "tiveres", "tivermos", "tiverem",
    "ter", "tendo",
})

# Future auxiliary verbs
_ES_IR_FORMS = frozenset({
    "voy", "vas", "va", "vamos", "vais", "van",
    "iba", "ibas", "ibamos", "íbamos", "ibais", "iban",
    "fui", "fuiste", "fue", "fuimos", "fuisteis", "fueron",
    "vaya", "vayas", "vayamos", "vayan", "ir", "yendo",
})

_PT_IR_FORMS = frozenset({
    "vou", "vais", "vai", "vamos", "vades", "vao", "vão",
    "ia", "ias", "iamos", "íamos", "iam",
    "fui", "foste", "foi", "fomos", "foram",
    "va", "vá", "vas", "vás", "vamos", "vao", "vão",
    "ir", "indo",
})

# Perfect auxiliary verbs
_ES_HABER_FORMS = frozenset({
    "he", "has", "ha", "hemos", "habeis", "habéis", "han",
    "habia", "había", "habias", "habías", "habiamos", "habíamos", "habian", "habían",
    "hube", "hubiste", "hubo", "hubimos", "hubieron",
    "haya", "hayas", "hayamos", "hayan", "haber", "habiendo",
})

_PT_TER_HAVER_AUX_FORMS = frozenset({
    "tenho", "tens", "tem", "temos", "têm", "tinha", "tinhas", "tínhamos", "tinham",
    "tive", "teve", "tivemos", "tiveram", "tenha", "tenham", "tiver", "ter",
    "hei", "hás", "há", "havemos", "hão", "havia", "haviam", "houve", "houveram", "haver",
})

_PAST_PARTICIPLE = re.compile(
    r"\b(?:\w+(?:ado|ido)|sido|visto|hecho|dicho|puesto|escrito|abierto|muerto|feito|dito|posto)\b",
    re.I,
)

# Governed prepositions trigger verbs
_GOVERNING_VERBS_DE = frozenset({
    "precisar", "preciso", "precisa", "precisamos", "precisam", "precisei", "precisava",
    "gostar", "gosto", "gosta", "gostamos", "gostam", "gostei", "gostava",
    "depender", "dependo", "depende", "dependemos", "dependem", "dependeu",
    "cuidar", "cuido", "cuida", "cuidamos", "cuidam", "cuidei",
    "falar", "falo", "fala", "falamos", "falam", "falei", "falava",
    "lembrar", "lembro", "lembra", "lembrei", "lembrava",
    "esquecer", "esqueço", "esquece", "esqueci", "esquecia",
    "acordar", "acordo", "acorda", "acordarse", "acuerda", "acuerdo",
    "tratar", "trato", "trata", "tratamos", "tratam",
    "deixar", "deixo", "deixa", "deixamos", "deixei",
    "parar", "paro", "para", "parei",
})

_PREPOSITIONS_BEFORE_PRONOUNS = frozenset({
    "a", "com", "de", "em", "para", "por", "sem", "sob", "sobre", "ate", "até", "contra",
    "entre", "desde", "hacia", "hasta", "segun", "según",
})


def _clean_word(token: str) -> str:
    return unicodedata.normalize("NFC", token or "").casefold().strip(".,!?:;\"'()[]{}«»—–")


def evaluate_construction(
    *,
    sentence: str,
    surface_form: str,
    analyses: Sequence[MenuAnalysis],
    language: str = "es",
    observed_pos: str | None = None,
    observed_grammar: Mapping[str, str] | None = None,
) -> tuple[set[tuple[str, str]] | None, set[tuple[str, str]], dict[str, Any]]:
    """Evaluate construction rules for the target surface in sentence context.

    Returns:
        (supported_refs, rejected_refs, diagnostics)
        - supported_refs: set of (menu_analysis_id, sense_id) licensed by the construction,
          or None if no specific construction rule fired.
        - rejected_refs: set of (menu_analysis_id, sense_id) disqualified by the construction.
        - diagnostics: metadata record of which rule fired.
    """
    surface_clean = _clean_word(surface_form)
    sentence_clean = unicodedata.normalize("NFC", sentence or "")
    text_lower = sentence_clean.casefold()
    tokens = [_clean_word(tok) for tok in text_lower.split() if _clean_word(tok)]
    try:
        target_idx = tokens.index(surface_clean)
    except ValueError:
        target_idx = -1

    all_leaves = [
        (analysis, leaf)
        for analysis in analyses
        for leaf in analysis.senses
    ]

    def _leaf_ref(analysis: MenuAnalysis, leaf: SenseLeaf) -> tuple[str, str]:
        return (analysis.menu_analysis_id, leaf.sense_id)

    # -------------------------------------------------------------------------
    # Rule 1: Progressive auxiliary (estar/andar + gerund or pt estar a + inf)
    # Causes 10: progressive_as_lexical (e.g. estuve pensando, estás a fazer)
    # -------------------------------------------------------------------------
    is_estar = (
        (language == "es" and surface_clean in _ES_ESTAR_FORMS)
        or (language == "pt" and surface_clean in _PT_ESTAR_ANDAR_FORMS)
    )
    if is_estar:
        has_gerund = False
        if target_idx >= 0 and target_idx + 1 < len(tokens):
            window = " ".join(tokens[target_idx + 1 : target_idx + 4])
            if language == "es":
                has_gerund = bool(_ES_GERUND.search(window))
            else:
                has_gerund = bool(_PT_GERUND.search(window) or _PT_EU_PROGRESSIVE.search(window))
        elif language == "es":
            has_gerund = bool(_ES_GERUND.search(text_lower))
        else:
            has_gerund = bool(_PT_GERUND.search(text_lower) or _PT_EU_PROGRESSIVE.search(text_lower))

        if has_gerund:
            supported = set()
            rejected = set()
            for analysis, leaf in all_leaves:
                defin = (leaf.definition or "").casefold()
                trans = (leaf.translation or "").casefold()
                is_prog = (
                    "progressive" in defin
                    or "gerund" in defin
                    or "forms the progressive" in defin
                    or "progressive" in trans
                    or "to be" in trans
                )
                is_lexical_slip = (
                    "to fit" in trans
                    or "to fit" in defin
                    or "to stand" in trans
                    or "to stand" in defin
                    or "to stay" in trans
                    or "to cost" in trans
                )
                if is_prog and not is_lexical_slip:
                    supported.add(_leaf_ref(analysis, leaf))
                elif is_lexical_slip:
                    rejected.add(_leaf_ref(analysis, leaf))

            if supported:
                return (
                    supported,
                    rejected,
                    {
                        "construction": "progressive_auxiliary",
                        "rule": "estar_gerund_progressive",
                        "language": language,
                    },
                )

    # -------------------------------------------------------------------------
    # Rule 2: Modal obligation (tener que / ter que / ter de + infinitive)
    # Cause 8: construction_misread (e.g. tenemos que, tens de)
    # -------------------------------------------------------------------------
    is_tener = (
        (language == "es" and surface_clean in _ES_TENER_FORMS)
        or (language == "pt" and surface_clean in _PT_TER_FORMS)
    )
    if is_tener:
        has_obligation = False
        if target_idx >= 0 and target_idx + 1 < len(tokens):
            next_words = tokens[target_idx + 1 : target_idx + 4]
            if next_words and next_words[0] in ("que", "de"):
                if len(next_words) > 1 and next_words[1].endswith(("ar", "er", "ir")):
                    has_obligation = True
                elif len(next_words) > 2 and next_words[2].endswith(("ar", "er", "ir")):
                    has_obligation = True
        if not has_obligation:
            has_obligation = bool(
                re.search(r"\b(?:tener|ter)\s+(?:que|de)\s+\w+[aei]r\b", text_lower)
            )

        if has_obligation:
            supported = set()
            rejected = set()
            for analysis, leaf in all_leaves:
                defin = (leaf.definition or "").casefold()
                trans = (leaf.translation or "").casefold()
                is_oblg = (
                    "have to" in trans
                    or "must" in trans
                    or "obligation" in defin
                    or "have to" in defin
                    or "must" in defin
                )
                is_possession = (
                    "to own" in trans
                    or "possess" in trans
                    or "to hold" in trans
                    or "to possess" in defin
                    or "possession" in defin
                )
                if is_oblg:
                    supported.add(_leaf_ref(analysis, leaf))
                elif is_possession:
                    rejected.add(_leaf_ref(analysis, leaf))

            if supported:
                return (
                    supported,
                    rejected,
                    {
                        "construction": "modal_obligation",
                        "rule": "tener_que_obligation",
                        "language": language,
                    },
                )

    # -------------------------------------------------------------------------
    # Rule 3: Future auxiliary (ir + infinitive or ir a + infinitive)
    # Cause 11: auxiliary_as_lexical (e.g. vou fazer, vai chover)
    # -------------------------------------------------------------------------
    is_ir = (
        (language == "es" and surface_clean in _ES_IR_FORMS)
        or (language == "pt" and surface_clean in _PT_IR_FORMS)
    )
    if is_ir:
        has_future = False
        if target_idx >= 0 and target_idx + 1 < len(tokens):
            next_words = tokens[target_idx + 1 : target_idx + 4]
            if next_words and next_words[0] == "a" and len(next_words) > 1 and next_words[1].endswith(("ar", "er", "ir")):
                has_future = True
            elif language == "pt" and next_words and next_words[0].endswith(("ar", "er", "ir")):
                has_future = True
            elif language == "pt" and len(next_words) > 1 and next_words[1].endswith(("ar", "er", "ir")):
                has_future = True

        if has_future:
            supported = set()
            rejected = set()
            for analysis, leaf in all_leaves:
                defin = (leaf.definition or "").casefold()
                trans = (leaf.translation or "").casefold()
                is_fut = (
                    "will" in trans
                    or "going to" in trans
                    or "future" in defin
                    or "will" in defin
                    or "going to" in defin
                )
                is_pure_motion = (
                    "to begin an action" in defin
                    or "to depart" in trans
                    or "to travel" in trans
                )
                if is_fut:
                    supported.add(_leaf_ref(analysis, leaf))
                elif is_pure_motion:
                    rejected.add(_leaf_ref(analysis, leaf))

            if supported:
                return (
                    supported,
                    rejected,
                    {
                        "construction": "future_auxiliary",
                        "rule": "ir_infinitive_future",
                        "language": language,
                    },
                )

    # -------------------------------------------------------------------------
    # Rule 4: Perfect / compound auxiliary (haber / ter / haver + past participle)
    # Cause 11: auxiliary_as_lexical (e.g. ha ido, ter sido)
    # -------------------------------------------------------------------------
    is_haber = (
        (language == "es" and surface_clean in _ES_HABER_FORMS)
        or (language == "pt" and surface_clean in _PT_TER_HAVER_AUX_FORMS)
    )
    if is_haber:
        has_participle = False
        if target_idx >= 0 and target_idx + 1 < len(tokens):
            next_words = tokens[target_idx + 1 : target_idx + 4]
            has_participle = any(_PAST_PARTICIPLE.fullmatch(w) for w in next_words)
        else:
            has_participle = bool(_PAST_PARTICIPLE.search(text_lower))

        if has_participle:
            supported = set()
            rejected = set()
            for analysis, leaf in all_leaves:
                defin = (leaf.definition or "").casefold()
                trans = (leaf.translation or "").casefold()
                is_aux = (
                    "compound" in defin
                    or "auxiliary" in defin
                    or "perfect" in defin
                    or "to have" in trans
                    or "have" in trans
                )
                is_existential = (
                    "there is" in trans
                    or "there are" in trans
                    or "to exist" in trans
                    or "exist" in defin
                )
                is_possession = "to own" in trans or "possess" in trans
                if is_aux:
                    supported.add(_leaf_ref(analysis, leaf))
                elif is_existential or is_possession:
                    rejected.add(_leaf_ref(analysis, leaf))

            if supported:
                return (
                    supported,
                    rejected,
                    {
                        "construction": "perfect_auxiliary",
                        "rule": "haber_participle_compound",
                        "language": language,
                    },
                )

    # -------------------------------------------------------------------------
    # Rule 5: Personal pronoun function / case (Cause 12: ela, nós, etc.)
    # -------------------------------------------------------------------------
    if language == "pt" and surface_clean == "ela":
        is_prepositional = False
        if target_idx > 0 and tokens[target_idx - 1] in _PREPOSITIONS_BEFORE_PRONOUNS:
            is_prepositional = True

        supported = set()
        rejected = set()
        for analysis, leaf in all_leaves:
            defin = (leaf.definition or "").casefold()
            trans = (leaf.translation or "").casefold()
            if is_prepositional:
                if "her" in trans or "prepositional" in defin:
                    supported.add(_leaf_ref(analysis, leaf))
                elif "she" in trans or "subject" in defin or "nominative" in defin:
                    rejected.add(_leaf_ref(analysis, leaf))
            else:
                if "she" in trans or "subject" in defin or "nominative" in defin:
                    supported.add(_leaf_ref(analysis, leaf))
                elif "prepositional" in defin:
                    rejected.add(_leaf_ref(analysis, leaf))

        if supported:
            return (
                supported,
                rejected,
                {
                    "construction": "pronoun_function",
                    "rule": "ela_case_distinction",
                    "prepositional": is_prepositional,
                },
            )

    if language == "pt" and surface_clean == "nós":
        is_prepositional = target_idx > 0 and tokens[target_idx - 1] in _PREPOSITIONS_BEFORE_PRONOUNS
        if not is_prepositional:
            supported = set()
            rejected = set()
            for analysis, leaf in all_leaves:
                trans = (leaf.translation or "").casefold()
                if "we" in trans:
                    supported.add(_leaf_ref(analysis, leaf))
                elif "us" in trans:
                    rejected.add(_leaf_ref(analysis, leaf))
            if supported:
                return (
                    supported,
                    rejected,
                    {"construction": "pronoun_function", "rule": "nos_subject_distinction"},
                )

    # -------------------------------------------------------------------------
    # Rule 6: Governed prepositions (Cause 19: de after precisar, gostar, etc.)
    # -------------------------------------------------------------------------
    if surface_clean in ("de", "do", "da", "dos", "das"):
        is_governed = False
        if target_idx > 0 and tokens[target_idx - 1] in _GOVERNING_VERBS_DE:
            is_governed = True
        elif any(verb in text_lower for verb in _GOVERNING_VERBS_DE):
            is_governed = True

        if is_governed:
            supported = set()
            rejected = set()
            for analysis, leaf in all_leaves:
                defin = (leaf.definition or "").casefold()
                trans = (leaf.translation or "").casefold()
                is_role_or_adverbial = (
                    "in the role of" in defin
                    or "as (in the role" in defin
                    or "in (wearing" in defin
                    or "wearing" in trans
                    or "in the capacity" in defin
                )
                is_relational = (
                    "of" in trans
                    or "from" in trans
                    or "about" in trans
                    or "by" in trans
                )
                if is_relational and not is_role_or_adverbial:
                    supported.add(_leaf_ref(analysis, leaf))
                elif is_role_or_adverbial:
                    rejected.add(_leaf_ref(analysis, leaf))

            if supported:
                return (
                    supported,
                    rejected,
                    {"construction": "governed_preposition", "rule": "governed_de_relational"},
                )

    return None, set(), {}
