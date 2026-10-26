"""Mark near-duplicate senses that a learner could not tell apart as equivalent.

Wiktionary frequently creates separate sense entries for regional jurisdictions
(e.g. sheriff in England vs sheriff in the United States) or number inflections
(e.g. milhão 'million' vs milhões 'millions'). Senses are never deleted or merged,
and sense IDs never change. Instead, explicit equivalences are stamped on the
card and on each sense's provider_metadata for WSD and scoring to read.
"""

from __future__ import annotations

from collections import defaultdict
import re
from typing import Any

RULE_VERSION = "sense-equivalences/v1"

GEO_TERMS = frozenset({
    "england", "united states", "us", "uk", "britain", "british", "america", "american",
    "scotland", "scottish", "ireland", "irish", "australia", "australian",
    "brazil", "brazilian", "portugal", "portuguese", "moorish", "muslim", "canada", "canadian",
})

STOPWORDS = frozenset({
    "a", "an", "the", "and", "or", "of", "in", "on", "at", "to", "for", "with", "by", "from",
    "as", "is", "are", "was", "were", "be", "been", "being", "have", "has", "had", "do", "does",
    "did", "that", "this", "these", "those", "it", "its", "not", "no",
})


def _parse_gloss(text: str) -> tuple[str, str]:
    cleaned = str(text or "").strip()
    match = re.match(r"^([^(]+)(?:\((.*)\))?", cleaned)
    if not match:
        return cleaned.lower(), ""
    base = match.group(1).strip().lower()
    paren = (match.group(2) or "").strip().lower()
    return base, paren


def are_senses_equivalent(
    s1: dict[str, Any],
    s2: dict[str, Any],
    *,
    pos1: str = "",
    pos2: str = "",
) -> bool:
    """Return True if two senses under the same card are near-duplicates.

    Criteria:
    1. Part of speech must match.
    2. Senses must not have conflicting, non-overlapping domain topics.
    3. Either:
       a) Number inflection variant of the same noun (e.g. million vs millions).
       b) Identical base translation differing only by geographic/jurisdictional
          context (e.g. xerife: England vs US sheriff), an unelaborated sub-sense,
          or high parenthetical descriptor overlap.
    """
    p1 = (pos1 or s1.get("part_of_speech") or s1.get("pos") or "").strip().casefold()
    p2 = (pos2 or s2.get("part_of_speech") or s2.get("pos") or "").strip().casefold()
    if p1 != p2:
        return False

    # Check for domain / topic conflict
    d1 = set(s1.get("provider_metadata", {}).get("topics") or s1.get("domains") or [])
    d2 = set(s2.get("provider_metadata", {}).get("topics") or s2.get("domains") or [])
    if d1 and d2 and not (d1 & d2):
        return False

    g1 = s1.get("translation") or s1.get("meaning") or s1.get("gloss") or ""
    g2 = s2.get("translation") or s2.get("meaning") or s2.get("gloss") or ""
    b1, p1_text = _parse_gloss(g1)
    b2, p2_text = _parse_gloss(g2)

    if not b1 or not b2:
        return False

    # Rule 1: Number inflection variant between singular/plural (e.g. million vs millions)
    if p1 == "noun" and len(b1) > 3 and len(b2) > 3 and b1 != b2:
        if (
            b1.rstrip("s") == b2.rstrip("s")
            or (b1.endswith("es") and b1[:-2] == b2)
            or (b2.endswith("es") and b2[:-2] == b1)
        ):
            return True

    # Rule 2: Semicolon-delimited components match (e.g. "increasingly; more and more" vs "more and more; increasingly")
    parts1 = {p.strip() for p in b1.split(";") if p.strip()}
    parts2 = {p.strip() for p in b2.split(";") if p.strip()}
    if parts1 and parts1 == parts2:
        return True

    # Rule 3: Identical base translation
    if b1 == b2:
        words1 = set(re.findall(r"[a-z]+", p1_text)) - STOPWORDS
        words2 = set(re.findall(r"[a-z]+", p2_text)) - STOPWORDS
        has_geo = bool((words1 | words2) & GEO_TERMS)
        if has_geo:
            return True
        if not p1_text or not p2_text:
            return True
        overlap = len(words1 & words2)
        if overlap >= 2:
            return True

    return False


def find_card_equivalences(
    analyses: list[dict[str, Any]] | None = None,
    flat_senses: list[dict[str, Any] | tuple[dict[str, Any], str]] | None = None,
) -> list[list[str]]:
    """Return disjoint groups of equivalent sense IDs for one card."""
    all_senses: list[tuple[dict[str, Any], str]] = []
    if flat_senses is not None:
        for item in flat_senses:
            if isinstance(item, tuple):
                all_senses.append((item[0], str(item[1])))
            elif isinstance(item, dict):
                pos = str(item.get("part_of_speech") or item.get("pos") or "")
                all_senses.append((item, pos))
    elif analyses is not None:
        for analysis in analyses:
            pos = str(analysis.get("part_of_speech") or "")
            for sense in analysis.get("senses") or []:
                all_senses.append((sense, pos))

    if len(all_senses) < 2:
        return []

    # Build adjacency
    adj: dict[str, set[str]] = defaultdict(set)
    for i in range(len(all_senses)):
        s1, pos1 = all_senses[i]
        sid1 = s1.get("sense_id")
        if not sid1:
            continue
        for j in range(i + 1, len(all_senses)):
            s2, pos2 = all_senses[j]
            sid2 = s2.get("sense_id")
            if not sid2 or sid1 == sid2:
                continue
            if are_senses_equivalent(s1, s2, pos1=pos1, pos2=pos2):
                adj[sid1].add(sid2)
                adj[sid2].add(sid1)

    # Connected components
    visited: set[str] = set()
    components: list[list[str]] = []
    for sid in sorted(adj):
        if sid in visited:
            continue
        component: list[str] = []
        queue = [sid]
        visited.add(sid)
        while queue:
            curr = queue.pop(0)
            component.append(curr)
            for neighbor in sorted(adj[curr]):
                if neighbor not in visited:
                    visited.add(neighbor)
                    queue.append(neighbor)
        if len(component) >= 2:
            components.append(sorted(component))

    return components


def stamp_sense_equivalences(cards: list[dict[str, Any]]) -> None:
    """Stamp explicit, recorded equivalence groups on cards and senses in place."""
    for card in cards:
        analyses = card.get("analyses") or []
        components = find_card_equivalences(analyses)
        card["equivalences"] = components

        # Map each sense_id to its equivalent siblings
        equiv_map: dict[str, list[str]] = {}
        for group in components:
            group_set = set(group)
            for sid in group:
                equiv_map[sid] = sorted(group_set - {sid})

        for analysis in analyses:
            for sense in analysis.get("senses") or []:
                sid = sense.get("sense_id")
                meta = sense.setdefault("provider_metadata", {})
                meta["equivalent_sense_ids"] = equiv_map.get(sid, [])
