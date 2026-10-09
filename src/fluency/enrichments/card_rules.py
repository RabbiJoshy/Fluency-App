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
    proof = row.get("noun_merge")
    if proof is not None and not isinstance(proof, dict):
        return ""
    if isinstance(proof, dict):
        if proof.get("rule_version") != "noun-merge/v2" or proof.get("allowed") is not True:
            return ""
    meanings = row.get("meanings") or []
    dictionary_senses = [*meanings, *(row.get("unused_menu_senses") or [])]
    dictionary_senses.extend(s for m in meanings for s in m.get("allSenses") or [])
    if proof:
        for sense in dictionary_senses:
            pos = normal_token(sense.get("pos") or sense.get("part_of_speech"))
            if pos in {"phrase", "sense_cycle"} or is_expression_sense(sense, str(row.get("word") or "")):
                continue
            if (pos and "noun" not in pos.split()) or (
                sense.get("headword") and normal_token(sense["headword"]) != normal_token(proof.get("lemma"))
            ):
                return ""
    if not headwords and isinstance(row.get("merge_key"), str):
        return row["merge_key"]
    lemma = headwords[0] if headwords else normal_token((proof or {}).get("lemma") or row.get("lemma"))
    if not lemma:
        return ""
    surface = normal_token(row.get("word"))
    if proof and normal_token(proof.get("lemma")) != lemma:
        return ""
    if not proof and (not meanings or any(
        "noun" in str(m.get("pos") or m.get("part_of_speech") or "").lower().split()
        and not is_expression_sense(m, str(row.get("word") or "")) for m in dictionary_senses
    )):
        return ""
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
    row: Mapping[str, Any],
    by_headword: Mapping[str, Mapping[str, Mapping[str, float]]] | None,
    code: str,
    matches: Mapping[str, Mapping[str, Mapping[str, str]]] | None = None,
) -> tuple[float, str | None] | None:
    """The card's weakest shown sense in one known language:
    (closeness, the known word that decided it), or None."""

    if not by_headword:
        return None
    word = str(row.get("word") or "")
    meanings = [
        m for m in row.get("meanings") or []
        if str(m.get("translation") or m.get("meaning") or "").strip()
    ]
    if not meanings:
        return None
    matches = matches or {}
    weakest: tuple[float, str | None] | None = None
    for meaning in meanings:
        best: tuple[float, str | None] = (0.0, None)
        if not is_expression_sense(meaning, word):
            headword = normal_token(meaning.get("headword"))
            keys = [headword, ""] if headword else sorted(by_headword)
            for alternative in sorted(sense_alternatives(str(meaning.get("translation") or meaning.get("meaning") or ""))):
                for key in keys:
                    score = float(((by_headword.get(key) or {}).get(alternative) or {}).get(code, 0.0))
                    if score > best[0]:
                        known = ((matches.get(key) or {}).get(alternative) or {}).get(code) or alternative
                        best = (score, known)
        if weakest is None or best[0] < weakest[0]:
            weakest = best
        if weakest[0] == 0.0:
            break
    return weakest


def clean_headword(hw: Any) -> str:
    token = normal_token(hw)
    if token.endswith("se") and len(token) > 3:
        return token[:-2]
    return token


def detect_split_card_tuples(
    row: Mapping[str, Any],
    language: str = "es",
) -> dict[str, Any] | None:
    word = normal_token(row.get("word"))
    meanings = row.get("meanings") or []
    lex = [m for m in meanings if not is_expression_sense(m, word)]
    if len(lex) < 4:
        return None

    # Class 1: True Homograph (Distinct base headwords, e.g. ser vs ir, paso vs pasar)
    hws: dict[str, list[dict[str, Any]]] = {}
    for m in lex:
        hw = clean_headword(m.get("headword") or word)
        hws.setdefault(hw, []).append(m)

    collapsed: dict[str, list[dict[str, Any]]] = {}
    for hw, ms in hws.items():
        matched = False
        for c in collapsed:
            c_root = c.rstrip("osae")
            hw_root = hw.rstrip("osae")
            if c_root == hw_root and len(c_root) >= 3:
                collapsed[c].extend(ms)
                matched = True
                break
        if not matched:
            collapsed[hw] = ms

    total_len = len(lex)
    viable = {
        hw: ms for hw, ms in collapsed.items()
        if (len(ms) / total_len >= 0.14 and len(ms) >= 1)
    }
    if len(viable) >= 2:
        sorted_v = sorted(viable.items(), key=lambda x: len(x[1]), reverse=True)[:2]
        hw1, ms1 = sorted_v[0]
        hw2, ms2 = sorted_v[1]
        tr1 = ms1[0].get("translation") or ms1[0].get("meaning") or ""
        tr2 = ms2[0].get("translation") or ms2[0].get("meaning") or ""
        pos1 = str(ms1[0].get("pos") or "X").upper()
        pos2 = str(ms2[0].get("pos") or "X").upper()
        return {
            "kind": "homograph",
            "tuple1": {
                "headword": hw1,
                "pos": pos1,
                "label": f"{hw1} ({tr1})",
                "meanings": ms1,
                "share": round(len(ms1) / total_len, 2),
                "isReflexive": False,
            },
            "tuple2": {
                "headword": hw2,
                "pos": pos2,
                "label": f"{hw2} ({tr2})",
                "meanings": ms2,
                "share": round(len(ms2) / total_len, 2),
                "isReflexive": False,
            },
        }

    # Class 2: Pronominal / Reflexive Shift (Attested base vs pronominal headword)
    base_m = [m for m in lex if not normal_token(m.get("headword")).endswith("se")]
    refl_m = [m for m in lex if normal_token(m.get("headword")).endswith("se")]
    if len(base_m) >= 1 and len(refl_m) >= 1:
        base_hws = [normal_token(m.get("headword") or word) for m in base_m]
        refl_hws = [normal_token(m.get("headword")) for m in refl_m]
        # Find matching base and pronominal headword pair (e.g. hacer and hacerse, llamar and llamarse)
        matched_root = None
        for r_hw in refl_hws:
            r_base = r_hw[:-2] if r_hw.endswith("se") and len(r_hw) > 3 else None
            if r_base and (r_base in base_hws or r_base == word or any(b.startswith(r_base) for b in base_hws)):
                matched_root = r_base
                break
        if not matched_root and base_hws:
            # Fallback check: any base headword whose +se form matches a reflexive headword
            for b_hw in base_hws:
                if f"{b_hw}se" in refl_hws:
                    matched_root = b_hw
                    break

        if matched_root and (len(refl_m) / total_len >= 0.14):
            tr1 = base_m[0].get("translation") or base_m[0].get("meaning") or ""
            tr2 = refl_m[0].get("translation") or refl_m[0].get("meaning") or ""
            pos1 = str(base_m[0].get("pos") or "VERB").upper()
            pos2 = str(refl_m[0].get("pos") or "VERB").upper()
            return {
                "kind": "reflexive",
                "root": matched_root,
                "tuple1": {
                    "headword": matched_root,
                    "pos": pos1,
                    "label": f"{matched_root} ({tr1})",
                    "meanings": base_m,
                    "share": round(len(base_m) / total_len, 2),
                    "isReflexive": False,
                },
                "tuple2": {
                    "headword": f"{matched_root}se",
                    "pos": pos2,
                    "label": f"{matched_root}se ({tr2})",
                    "meanings": refl_m,
                    "share": round(len(refl_m) / total_len, 2),
                    "isReflexive": True,
                },
            }

    return None

