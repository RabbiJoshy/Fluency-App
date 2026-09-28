"""The app's card rules, computed ahead of time from a release's full rows.

Speech decks ship a skinny column index and load each card's senses only when
its study set is opened. Setup-time filtering (Merge Lemmas, Exclude Cognates)
runs before that, over cards with no senses, so any rule that reads senses has
to be decided here and shipped per surface. Each function mirrors one in the
app and must stay in step with it; ``tests/app/test_card_rules_parity.py``
runs both on the same rows.

    is_expression_sense   app/js/vocab.js  isExpressionSenseForLemma
    lemma_group_key       app/js/vocab.js  lemmaGroupKey (decision 0028)
    sense_alternatives    app/js/cognates.js senseAlternatives
    card_cognate          app/js/cognates.js cardSenseCognate
"""

from __future__ import annotations

import re
import unicodedata
from typing import Any, Iterable, Mapping

EXPRESSION_ROUTES = frozenset({"deterministic_bypass", "invariant", "competitive_wsd", "ambiguous"})
_TOKEN_SPLIT = re.compile(r"[^\w'’]+|[\d_]+")
_PARENTHETICAL = re.compile(r"\([^)]*\)")


def normal_token(value: Any) -> str:
    return unicodedata.normalize("NFC", str(value or "")).lower().strip()


def is_expression_sense(meaning: Mapping[str, Any], word: str) -> bool:
    pos = meaning.get("pos") or meaning.get("part_of_speech")
    if pos in ("MWE", "CLITIC"):
        return True
    metadata = meaning.get("metadata") or {}
    adapter = str(metadata.get("source_adapter") or meaning.get("source") or "")
    if "mwe-merged" in adapter.lower():
        return True
    if str(meaning.get("context") or "").lower() == "multiword expression":
        return True
    evidence = (metadata.get("multiword_evidence") or [None])[0] or {}
    route = (
        evidence.get("wsd_routing")
        or evidence.get("route")
        or meaning.get("wsd_routing")
        or meaning.get("route")
    )
    if route in EXPRESSION_ROUTES:
        return True
    if pos == "PHRASE":
        head = str(meaning.get("headword") or meaning.get("expression") or "").strip()
        if re.search(r"\s", head) and normal_token(head) != normal_token(word):
            return True
    return False


def lemma_headwords(row: Mapping[str, Any]) -> list[str]:
    word = str(row.get("word") or "")
    out: list[str] = []
    for meaning in row.get("meanings") or []:
        if not meaning.get("headword") or is_expression_sense(meaning, word):
            continue
        key = normal_token(meaning["headword"])
        if key and key not in out:
            out.append(key)
    return out


def _expression_tokens(value: Any) -> list[str]:
    return [token for token in _TOKEN_SPLIT.split(normal_token(value)) if token]


def lemma_group_key(row: Mapping[str, Any], contractions: Iterable[str] = ()) -> str:
    """'' keeps the spelling on its own card; otherwise the lemma it joins."""

    headwords = lemma_headwords(row)
    if len(headwords) > 1:
        return ""
    lemma = headwords[0] if headwords else normal_token(row.get("lemma"))
    if not lemma:
        return ""
    surface = normal_token(row.get("word"))
    meanings = row.get("meanings") or []
    if surface in set(contractions) or any(
        str(m.get("pos") or m.get("part_of_speech") or "").upper() == "CONTRACTION" for m in meanings
    ):
        return ""
    if surface and surface != lemma:
        for meaning in meanings:
            if not is_expression_sense(meaning, str(row.get("word") or "")):
                continue
            tokens = _expression_tokens(meaning.get("headword") or meaning.get("expression") or "")
            if len(tokens) > 1 and surface in tokens:
                return ""
    return lemma


def sense_alternatives(translation: str) -> set[str]:
    out: set[str] = set()
    for part in re.split(r"[,;]", _PARENTHETICAL.sub(" ", translation or "")):
        text = re.sub(r"\s+", " ", re.sub(r"[^a-z' ]+", " ", part.lower())).strip()
        text = re.sub(r"^(?:to|the|a|an)\s+", "", text)
        if text and " " not in text:
            out.add(text)
    return out


def card_cognate(
    row: Mapping[str, Any], by_headword: Mapping[str, Mapping[str, float]] | None
) -> tuple[float, str | None] | None:
    """The card's weakest shown sense: (closeness, deciding word), or None."""

    if not by_headword:
        return None
    word = str(row.get("word") or "")
    meanings = [
        m for m in row.get("meanings") or []
        if str(m.get("translation") or m.get("meaning") or "").strip()
    ]
    if not meanings:
        return None
    weakest: tuple[float, str | None] | None = None
    for meaning in meanings:
        best: tuple[float, str | None] = (0.0, None)
        if not is_expression_sense(meaning, word):
            headword = normal_token(meaning.get("headword"))
            buckets = (
                [by_headword.get(headword), by_headword.get("")]
                if headword
                else list(by_headword.values())
            )
            for alternative in sense_alternatives(str(meaning.get("translation") or meaning.get("meaning") or "")):
                for bucket in buckets:
                    score = float((bucket or {}).get(alternative, 0.0))
                    if score > best[0]:
                        best = (score, alternative)
        if weakest is None or best[0] < weakest[0]:
            weakest = best
        if weakest[0] == 0.0:
            break
    return weakest
