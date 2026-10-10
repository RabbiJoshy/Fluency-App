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


def companion_sense_weight(row: Mapping[str, Any], meaning: Mapping[str, Any]) -> float:
    if (meaning.get("unassigned") or meaning.get("exampleOnly")
            or str(meaning.get("pos") or "").upper() in {"SENSE_CYCLE", "EXAMPLE_ONLY"}
            or meaning.get("assignment_method") == "unassigned"):
        return 0
    frequency = meaning.get("frequency", meaning.get("percentage"))
    if frequency is not None and not float(frequency or 0) > 0:
        return 0
    counts = (row.get("wsd_distribution") or {}).get("published_leaf_counts")
    sense_id = meaning.get("sense_id") or meaning.get("senseId") or meaning.get("id")
    if counts is not None and sense_id:
        return max(0, float(counts.get(sense_id) or 0))
    return 1 if frequency is None else max(0, float(frequency or 0))


def companion_sense_construction(meaning: Mapping[str, Any], language: str = "es") -> dict[str, Any]:
    headword = normal_token(meaning.get("headword"))
    pos = str(meaning.get("pos") or meaning.get("part_of_speech") or "").upper()
    if pos not in {"VERB", "AUX"} and " VERB" not in pos:
        return {"base": headword, "pronominal": False, "shared": False}
    metadata = meaning.get("metadata") or {}
    contract = metadata.get("sense_metadata") or {}
    provider = metadata.get("sense_provider_metadata") or contract.get("source_metadata") or {}
    features = [*(metadata.get("specialist_features") or []), *(contract.get("features") or [])]
    marks = {normal_token(v) for v in [
        *(meaning.get("tags") or []), *(provider.get("tags") or []),
        *(f.get("value") for f in features if f.get("family") in {"construction", "grammar"}),
        *re.split(r"[,;]", str(meaning.get("context") or "")),
    ]}
    suffix = r"(?:ar|er|ir|or|ôr)(-?se)$" if language == "pt" else r"(?:ar|er|ir|ír)(se)$" if language == "es" else None
    match = re.search(suffix, headword) if suffix else None
    base = headword[:-len(match[1])] if match else headword
    passive = bool(marks & {"passive", "impersonal", "voice=passive"})
    tagged = bool(marks & {"pronominal", "reflexive", "reflexive=true", "pronominal verb", "reflexive verb"})
    pronominal = not passive and bool(match or tagged)
    shared = pronominal and not match and bool(marks & {"transitive", "ambitransitive", "ditransitive", "transitive verb"})
    return {"base": base, "pronominal": pronominal, "shared": shared}


def companion_definition_key(value: Any) -> str:
    # Unicode letters and numbers, matching the app's punctuation/space fold.
    return re.sub(r"[^\w]+|_+", " ", normal_token(value)).strip()


def companion_semantic_context(meaning: Mapping[str, Any]) -> str:
    grammar = {"transitive", "intransitive", "ambitransitive", "ditransitive", "pronominal", "reflexive",
               "transitive verb", "intransitive verb", "pronominal verb", "reflexive verb"}
    parts = [companion_definition_key(v) for v in re.split(r"[,;]", str(meaning.get("context") or ""))]
    return " ".join(v for v in parts if v and v not in grammar)


def companion_same_definition(a: Mapping[str, Any], b: Mapping[str, Any]) -> bool:
    gloss = companion_definition_key(a.get("translation") or a.get("meaning"))
    if not gloss or gloss != companion_definition_key(b.get("translation") or b.get("meaning")):
        return False
    ca, cb = companion_semantic_context(a), companion_semantic_context(b)
    return not ca or not cb or ca == cb


def detect_split_card_tuples(row: Mapping[str, Any], language: str = "es") -> dict[str, Any] | None:
    """Assigned senses only: substantial distinct lemmas, or two constructions.

    Polysemy: four lexical sense rows and >=10% assigned usage per major lemma.
    Pronominal: both constructions, independent of sense count/share, unless all
    represented pronominal definitions are shared with an ordinary reading.
    Three major lemmas produce three cards. HEADWAY owns provider lemma cleanup.
    """
    word = normal_token(row.get("word") or row.get("targetWord"))
    seen: set[str] = set()
    lex = []
    for m in row.get("meanings") or []:
        if not m or is_expression_sense(m, word) or companion_sense_weight(row, m) <= 0:
            continue
        sense_id = m.get("sense_id") or m.get("senseId") or m.get("id")
        if sense_id and sense_id in seen:
            continue
        if sense_id:
            seen.add(sense_id)
        lex.append(m)
    if not lex:
        return None
    def weight(ms):
        return sum(companion_sense_weight(row, m) for m in ms)
    total = weight(lex)
    groups: dict[str, list] = {}
    for m in lex:
        hw = companion_sense_construction(m, language)["base"] or word
        groups.setdefault(hw, []).append(m)
    def rounded_share(ms):
        # JS Math.round for positive numbers (Python round uses ties-to-even).
        return int(weight(ms) / total * 100 + 0.5) / 100
    def tuple_for(hw, ms, reflexive=False):
        tr = str(ms[0].get("translation") or ms[0].get("meaning") or "").strip()
        return {"headword": hw, "pos": str(ms[0].get("pos") or "X").upper(),
                "label": f"{hw} ({tr})", "meanings": ms, "share": rounded_share(ms), "isReflexive": reflexive}
    def result(kind, tuples, root=None):
        return {"kind": kind, **({"root": root} if root else {}), "tuples": tuples,
                "tuple1": tuples[0], "tuple2": tuples[1]}
    viable = sorted(((hw, ms) for hw, ms in groups.items() if weight(ms) / total >= 0.10 - 1e-9),
                    key=lambda pair: -weight(pair[1]))
    if len(lex) >= 4 and len(viable) >= 2:
        tuples = [tuple_for(hw, list(ms)) for hw, ms in viable]
        major = {hw for hw, _ in viable}
        for hw, ms in groups.items():
            if hw not in major:
                tuples[0]["meanings"].extend(ms)
        tuples[0]["share"] = rounded_share(tuples[0]["meanings"])
        return result("homograph", tuples)
    if language not in {"es", "pt"} or len(groups) != 1:
        return None
    root = next(iter(groups))
    info = [(m, companion_sense_construction(m, language)) for m in lex]
    plain = [m for m, flags in info if not flags["pronominal"] or flags["shared"]]
    pron = [m for m, flags in info if flags["pronominal"] and not flags["shared"]]
    if not plain or not pron:
        return None
    if all(any(companion_same_definition(m, b) for b in plain) for m in pron):
        return None
    pron_hw = normal_token(pron[0].get("headword")) or root
    display_pron = pron_hw if pron_hw != root else f"{root}-se" if language == "pt" else f"{root}se"
    return result("reflexive", [tuple_for(root, plain), tuple_for(display_pron, pron, True)], root)
