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
    """surface -> lemma, from the form_of and alt_of links in the dump."""
    forms: dict[str, set[str]] = {}
    heads: set[str] = set()
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            row = json.loads(line)
            word = (row.get("word") or "").lower()
            if not word:
                continue
            heads.add(word)
            for sense in row.get("senses") or []:
                for key in ("form_of", "alt_of"):
                    for item in sense.get(key) or []:
                        target = (item.get("word") or "").lower()
                        if target and target != word:
                            forms.setdefault(word, set()).add(target)
    return forms, heads


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
        forms, headwords = wiktionary_forms(wikt)
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
                        {w: {w.lower()} for w in headwords}))

    events, resolved = [], set()
    for provider, table in sources:
        for surface in cards:
            lemmas = table.get(surface.lower())
            if not lemmas:
                continue
            resolved.add(surface)
            code = ("lemma_is_headword" if provider.startswith("enwiktionary-is-headword")
                    else "lemma_resolved")
            events.append(build_event(
                surface=surface, language=lang, phase="lemma",
                reason_code=code, observer=f"observe_lemmas/{provider}",
                evidence={"lemmas": sorted(lemmas)[:6], "provider": provider}))

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
