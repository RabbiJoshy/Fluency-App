#!/usr/bin/env python3
"""Resolve every surface to a lemma, from whatever source can say so.

Lemma resolution is evidence about a word, not a step of disambiguation, so it
belongs before WSD and in the surface store rather than inside the menu build.
SpanishDict in particular is a morphology source as much as a sense inventory:
its reverse-conjugation table alone names the lemma of 149,593 inflected forms.

Every source is recorded separately with its provider, because they disagree
and the disagreement is worth keeping: Wiktionary derives "assassinada" from
"assassinado" while a conjugation table would derive it from "assassinar", and
which is wanted depends on what is being asked.

    python scripts/observe_lemmas.py --workspace <ws> --language pt
"""

from __future__ import annotations

import argparse, json, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from fluency.surfaces.events import append, build_event, store_path  # noqa: E402

WIKTIONARY = {
    "pt": "enwiktionary-2026-08-20/kaikki.org-dictionary-Portuguese.jsonl",
    "es": "enwiktionary-2026-09-13/kaikki.org-dictionary-Spanish.jsonl",
    "cs": "enwiktionary-2026-09-06/kaikki.org-dictionary-Czech.jsonl",
}
SD = "raw/dictionaries/es/spanishdict/spanishdict-complete-menu-2026-08-23-v1"


def wiktionary_forms(path: Path) -> tuple[dict[str, set[str]], set[str]]:
    """surface -> lemma, from the form_of and alt_of links in the dump.

    Two things the naive reading gets wrong, both visible on the commonest
    words in Spanish.

    Wiktionary carries uppercase abbreviation entries beside ordinary words,
    and matching case-insensitively pulls their expansions in as though they
    were morphology: "no" came back as noroeste and número, "me" as muerte
    encefálica, "se" as sudeste, "al" as América Latina. The spelling is
    therefore matched exactly.

    And a surface that is its own headword is its own lemma, whatever else
    links to it. "una" really is the third person of unir and "para" of parar,
    but at ranks 15 and 22 of a subtitle list they are the article and the
    preposition, and a rare homograph must not displace the word being taught.
    """
    forms: dict[str, set[str]] = {}
    heads_exact: set[str] = set()
    # Closed-class words -- articles, pronouns, prepositions, conjunctions,
    # determiners, adverbs, interjections -- are not in practice inflected
    # forms of anything else. When one is its own headword it is its own lemma,
    # and a rare open-class homograph must not displace it: "una" is the third
    # person of unir and "para" of parar, but at ranks 15 and 22 of a subtitle
    # list they are the article and the preposition. An open-class surface is
    # left alone, so "es" still resolves to "ser".
    closed: set[str] = set()
    CLOSED_POS = {"article", "det", "pron", "prep", "conj", "adv", "intj",
                  "particle", "contraction", "postp"}
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            row = json.loads(line)
            word = row.get("word") or ""
            if not word:
                continue
            heads_exact.add(word)
            if (row.get("pos") or "") in CLOSED_POS:
                closed.add(word)
            for sense in row.get("senses") or []:
                for key in ("form_of", "alt_of"):
                    for item in sense.get(key) or []:
                        target = (item.get("word") or "").strip()
                        if target and target != word:
                            forms.setdefault(word, set()).add(target)
    # Note: an inflected form has a headword entry of its own -- that is how
    # form_of is expressed at all, the entry's word being the inflection and
    # its sense naming the lemma. Dropping every headword from the table
    # therefore deletes the resolutions worth having: "é" stopped resolving to
    # "ser" and "está" to "estar". Precedence is handled by ordering the
    # closed-class source first, not by deleting links.
    return forms, {w.lower() for w in heads_exact} | heads_exact, closed


def _priority(provider: str) -> int:
    """How much a source's answer is worth when several disagree.

    A closed-class word that is its own headword is its own lemma and nothing
    outranks that: articles, pronouns and prepositions are not inflections of
    anything, so "una" is the article and not the third person of unir.
    Morphological resolution comes next, because that is what a lemma is for:
    "es" to ser, "é" to ser, "jsem" to být. A bare headword entry is the
    fallback -- it says only that the string is documented, which is also true
    of the letter "e".
    """
    if "closed-class-headword" in provider:
        return 0
    if "is-headword" in provider:
        return 2
    return 1


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--workspace", type=Path, required=True)
    ap.add_argument("--language", required=True)
    args = ap.parse_args()
    ws, lang = args.workspace, args.language

    view = json.loads((ws / f"raw/surfaces/{lang}/surfaces.json").read_text())
    cards = {w for w, r in view["surfaces"].items() if r["rank"]}

    sources: list[tuple[str, dict[str, set[str]]]] = []
    headwords: set[str] = set()

    wikt = ws / "raw/wiktionary" / WIKTIONARY[lang]
    if wikt.exists():
        forms, headwords, closed_class = wiktionary_forms(wikt)
        # Recorded before every other source, so a closed-class word keeps its
        # own lemma rather than a conjugation table's homograph.
        if closed_class:
            sources.append((f"enwiktionary-closed-class-headword:{wikt.parent.name}",
                            {w: {w} for w in closed_class}))
        sources.append((f"enwiktionary-form-of:{wikt.parent.name}", forms))

    if lang == "es":
        reverse = json.loads((ws / SD / "conjugation_reverse.json").read_text())
        table: dict[str, set[str]] = {}
        for surface, entries in reverse.items():
            for entry in entries or []:
                lemma = (entry.get("lemma") or "").lower()
                if lemma:
                    table.setdefault(surface.lower(), set()).add(lemma)
        sources.append(("spanishdict-reverse-conjugation", table))

        cache = json.loads((ws / SD / "surface_cache.json").read_text())
        heads: dict[str, set[str]] = {}
        for surface, entry in cache.items():
            for analysis in entry.get("dictionary_analyses") or []:
                head = (analysis.get("headword") or "").strip().lower()
                if head and head != surface.lower():
                    heads.setdefault(surface.lower(), set()).add(head)
        sources.append(("spanishdict-surface-cache", heads))

        refetch = ws / "raw/dictionaries/es/spanishdict/refetch-menuless.jsonl"
        if refetch.exists():
            fresh: dict[str, set[str]] = {}
            for line in refetch.open(encoding="utf-8"):
                row = json.loads(line)
                for analysis in row.get("analyses") or []:
                    head = (analysis.get("headword") or "").strip().lower()
                    if head and head != row["word"].lower():
                        fresh.setdefault(row["word"].lower(), set()).add(head)
            sources.append(("spanishdict-refetch-2026-09-14", fresh))

    # A surface that is itself a headword is its own lemma. It never appears in
    # a form_of table, so counting it as unresolved makes the file look far less
    # conclusive than it is: "casa" needs no resolution, it IS the lemma.
    if headwords:
        sources.append((f"enwiktionary-is-headword:{wikt.parent.name}",
                        {w: {w} for w in headwords}))

    events, resolved = [], set()
    for provider, table in sources:
        for surface in cards:
            lemmas = table.get(surface) or table.get(surface.lower())
            if not lemmas:
                continue
            resolved.add(surface)
            code = ("lemma_is_headword" if "headword" in provider
                    else "lemma_resolved")
            events.append(build_event(
                surface=surface, language=lang, phase="lemma",
                reason_code=code, observer=f"observe_lemmas/{provider}",
                evidence={"lemmas": sorted(lemmas)[:6], "provider": provider,
                          "priority": _priority(provider)}))

    written = append(store_path(ws, lang), events)
    print(f"{lang}: {len(cards):,} cards")
    for provider, table in sources:
        hits = sum(1 for s in cards if table.get(s.lower()))
        print(f"   {provider:<44} {hits:>6,}")
    print(f"   {'ANY SOURCE':<44} {len(resolved):>6,} ({100*len(resolved)/len(cards):.1f}%)")
    print(f"   {'still unresolved':<44} {len(cards)-len(resolved):>6,}")
    print(f"   wrote {written:,} new events")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
