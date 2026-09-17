"""Non-decomposition policy for multiword expressions.

A learner needs a multiword expression when its meaning cannot be derived from
its constituent parts.

This module provides the policy classifier to separate true non-compositional
expressions (idioms, locutions, formulaic greetings) from compositional noise
(degree modifiers, transparent verbal clauses, translation drills).

Absence is declared: compositional entries retain their place in the snapshot
with `verdict="exclude"` and `reason="compositional"`, never omitted implicitly.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Sequence


@dataclass(frozen=True, slots=True)
class MWEDisposition:
    verdict: str  # "keep" or "exclude"
    reason: str   # "non_compositional", "compositional", "zero_freq"
    status: str   # "keep" or "compositional"
    non_compositional: bool

    def to_dict(self) -> dict[str, Any]:
        return {
            "verdict": self.verdict,
            "reason": self.reason,
            "status": self.status,
            "non_compositional": self.non_compositional,
        }


# Explicit keepers: expressions that must always be kept across languages
_SPANISH_EXPLICIT_KEEP = frozenset({
    "en serio", "a menos que", "por qué", "por que", "tal vez", "de nuevo",
    "sin embargo", "ni siquiera", "por favor", "de vez en cuando", "a menudo",
    "de pronto", "dar cuenta de", "tener que", "no te des por vencido",
    "no es para tanto", "no hay de qué", "muy bien", "muy señor mío",
    "si dios quiere", "si bien", "si es así", "si tú lo dices", "en fin",
    "por fin", "a través de", "a pesar de", "por lo tanto", "de todas formas",
    "de todos modos", "en cambio", "en lugar de", "en vez de", "al menos",
    "por lo menos", "al fin y al cabo", "sin duda", "en efecto", "de acuerdo",
    "de hecho", "poco a poco", "de repente", "a veces", "por cierto",
    "al parecer", "sobre todo", "en general", "por lo general", "hoy en día",
    "echar de menos", "darse cuenta", "valer la pena",
})

_SPANISH_EXPLICIT_DROP = frozenset({
    "muy serio", "si puedo", "no tiene", "no des", "no le des",
    "no me los des", "quiero que me des un", "yo nací", "yo nací ayer",
    "yo como", "él come", "estoy bien", "estoy cansado", "estoy triste",
    "estoy seguro", "estoy feliz", "estoy aburrido", "estoy trabajando",
    "estoy enfermo", "muy rico", "muy duro", "muy lejos", "muy cerca",
    "muy bueno", "muy mal", "muy conocido", "si quiere", "si quieres",
    "si hubiera", "si porque", "no quiero", "no puedo", "no tengo dinero",
    "no estoy de acuerdo", "no estoy seguro",
})

_PORTUGUESE_EXPLICIT_KEEP = frozenset({
    "de novo", "a partir de", "por isso", "apesar de", "em vez de", "do zero",
    "zero à esquerda", "a peso de ouro", "de peso", "em peso", "com certeza",
    "por favor", "talvez", "de repente", "por enquanto", "ao mesmo tempo",
    "de fato", "na verdade", "com efeito", "ao menos", "pelo menos",
    "em geral", "sem dúvida", "pouco a pouco", "às vezes", "por exemplo",
    "dar certo", "ter a ver", "ter de", "ter que", "ter cuidado",
    "fazer sentido", "dar uma olhada", "estar de acordo", "ao redor de",
    "não me diga", "de jeito nenhum", "pois não", "pelo contrário",
})

_PORTUGUESE_EXPLICIT_DROP = frozenset({
    "muito sério", "se posso", "não tem", "não quero", "não posso",
    "estou cansado", "estou bem", "muito bom", "muito bem obrigado",
    "se quiser", "se puder", "não dá", "não sei",
})

_CZECH_EXPLICIT_KEEP = frozenset({
    "dobrý den", "dobrou noc", "dobrý večer", "na shledanou", "jak se máš",
    "jak se máte", "na zdraví", "není zač", "všechno nejlepší", "i když",
    "právě tehdy, když", "hodně štěstí", "dobrou chuť", "mimochodem",
    "koneckonců", "čas od času", "krok za krokem", "den co den",
    "vůbec ne", "být v obraze", "dát si pozor", "mít pravdu",
    "stát za to", "vzít v úvahu", "udělat radost", "ty vole", "ty brďo",
    "je mi líto", "mít rád", "rád tě vidím",
})

_CZECH_EXPLICIT_DROP = frozenset({
    "velmi vážný", "moc dobrý", "když můžu", "když chce", "nechci",
    "nemám", "jsem unavený", "jsem rád", "velmi dobře",
})


def _is_spanish_compositional(expression: str, translations: Sequence[str]) -> bool:
    tokens = expression.strip().casefold().split()
    if not tokens:
        return True
    first = tokens[0]

    # Degree adverbs + adjective/adverb (muy serio, tan grande, bastante tarde)
    if first in {"muy", "tan", "bastante", "demasiado", "sumamente"}:
        if len(tokens) == 2:
            return True
        if first == "muy" and len(tokens) <= 3:
            return True

    # Copula + adjective/participle (estoy cansado, es fácil)
    if first in {"estoy", "estás", "está", "estamos", "están", "soy", "eres", "es", "somos", "son"}:
        if len(tokens) <= 3:
            trans_lower = " ".join(translations).casefold()
            if any(cop in trans_lower for cop in ("am ", "is ", "are ", "i'm ", "you're ", "he's ", "she's ")):
                return True

    # Negation + verb / pronoun + verb (no quiero, no tiene, no des, no le des)
    if first == "no" and len(tokens) >= 2:
        second = tokens[1]
        if second in {
            "quiero", "puedo", "tiene", "tengo", "des", "sé", "voy", "va",
            "vamos", "van", "está", "estoy", "es", "hay", "creo", "sabes",
            "sabe", "tienes", "puedes", "puede", "hago", "hace", "dice", "digo",
        }:
            return True
        if len(tokens) >= 3 and second in {"me", "te", "se", "le", "nos", "les", "lo", "la", "los", "las"}:
            third = tokens[2]
            if third in {"des", "da", "dan", "gusta", "importa", "parece", "ocurre", "diga", "digo", "dice"}:
                return True

    # Conditional si + verb (si puedo, si quiere, si quieres, si hubiera)
    if first == "si" and len(tokens) >= 2:
        second = tokens[1]
        if second in {
            "puedo", "quiere", "quieres", "hubiera", "porque", "tengo",
            "tiene", "voy", "vas", "va", "puedes", "puede", "gusta", "gustan",
        }:
            return True

    # Subject pronoun + personal verb (yo como, él viene)
    if first in {"yo", "tú", "él", "ella", "usted", "nosotros", "ellos", "ellas"} and len(tokens) <= 3:
        return True

    return False


def _is_portuguese_compositional(expression: str, translations: Sequence[str]) -> bool:
    tokens = expression.strip().casefold().split()
    if not tokens:
        return True
    first = tokens[0]

    if first in {"muito", "tão", "bastante", "demais"} and len(tokens) <= 3:
        return True

    if first in {"estou", "está", "estamos", "estão", "sou", "é", "somos", "são"}:
        if len(tokens) <= 3:
            trans_lower = " ".join(translations).casefold()
            if any(cop in trans_lower for cop in ("am ", "is ", "are ", "i'm ", "you're ", "he's ")):
                return True

    if first == "não" and len(tokens) >= 2:
        second = tokens[1]
        if second in {"quero", "posso", "tem", "tenho", "sei", "vou", "vai", "dá", "é", "está", "faz", "acho"}:
            return True
        if len(tokens) >= 3 and second in {"me", "te", "se", "lhe", "nos", "lhes", "o", "a", "os", "as"}:
            return True

    if first == "se" and len(tokens) >= 2:
        second = tokens[1]
        if second in {"posso", "quiser", "puder", "tiver", "for", "houver", "vai", "tem"}:
            return True

    if first in {"eu", "tu", "ele", "ela", "você", "nós", "eles", "elas", "vocês"} and len(tokens) <= 3:
        return True

    return False


def _is_czech_compositional(expression: str, translations: Sequence[str]) -> bool:
    tokens = expression.strip().casefold().split()
    if not tokens:
        return True
    first = tokens[0]

    if first in {"velmi", "moc", "příliš", "docela"} and len(tokens) <= 3:
        return True

    if first in {"jsem", "jsi", "je", "jsme", "jste", "jsou"} and len(tokens) <= 3:
        return True

    if first == "když" and len(tokens) >= 2:
        return True

    if (first.startswith("ne") and len(first) > 3) and len(tokens) <= 3:
        # Common Czech negated verbs: nechci, nemám, nemohu, nevím
        if first in {"nechci", "nemám", "nemohu", "nevím", "nejsem", "nemá", "nechce", "nemůže"}:
            return True

    if first in {"já", "ty", "on", "ona", "ono", "my", "vy", "oni"} and len(tokens) <= 3:
        return True

    return False


def classify_mwe(
    expression: str,
    translations: Sequence[str],
    language: str,
    *,
    corpus_freq: int = 0,
    sources: Sequence[str] = (),
) -> MWEDisposition:
    """Classify an MWE into keep (non-compositional) or exclude (compositional/zero_freq)."""

    norm_expr = expression.strip().casefold()
    lang = language.lower()

    if lang == "es":
        if norm_expr in _SPANISH_EXPLICIT_KEEP:
            is_comp = False
        elif norm_expr in _SPANISH_EXPLICIT_DROP:
            is_comp = True
        else:
            is_comp = _is_spanish_compositional(norm_expr, translations)
    elif lang == "pt":
        if norm_expr in _PORTUGUESE_EXPLICIT_KEEP:
            is_comp = False
        elif norm_expr in _PORTUGUESE_EXPLICIT_DROP:
            is_comp = True
        else:
            is_comp = _is_portuguese_compositional(norm_expr, translations)
    elif lang == "cs":
        if norm_expr in _CZECH_EXPLICIT_KEEP:
            is_comp = False
        elif norm_expr in _CZECH_EXPLICIT_DROP:
            is_comp = True
        else:
            is_comp = _is_czech_compositional(norm_expr, translations)
    else:
        is_comp = False

    if is_comp:
        return MWEDisposition(
            verdict="exclude",
            reason="compositional",
            status="compositional",
            non_compositional=False,
        )

    # If non-compositional: check tier-1 vs tier-2 (frequency > 0)
    # Tier 2 (corpus_freq == 0) is still non-compositional content, but marked
    # with reason "zero_freq" when frequency is 0.
    reason = "non_compositional" if corpus_freq > 0 else "zero_freq"
    verdict = "keep" if corpus_freq > 0 else "exclude"
    return MWEDisposition(
        verdict=verdict,
        reason=reason,
        status="keep",
        non_compositional=True,
    )
