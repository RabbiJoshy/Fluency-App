#!/usr/bin/env python3
"""Resolve Spanish clitic-attached verb forms to their SpanishDict headword.

SpanishDict has no page for `díselo`, `llévatelo` or `vayámonos`, and that is
not a gap in its coverage -- it files the verb, not every enclitic bundle. The
lemma is still derivable: strip the pronouns, undo the stress accent the clitic
forced, and ask SpanishDict about what is left.

This is the same authority as any other Spanish lemma. The provenance says how
it was reached, so a reader can tell a headword SpanishDict stated from one
this script inferred.

    python scripts/resolve_clitic_lemmas.py --workspace <ws> [--apply]
"""

from __future__ import annotations

import argparse, json, sys, unicodedata
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from fluency.surfaces.events import append, build_event, store_path  # noqa: E402
from fluency.surfaces.ledger import ledger_path  # noqa: E402

SD = "raw/dictionaries/es/spanishdict/spanishdict-complete-menu-2026-09-15-v3"

# Ordered longest-first so `selo` is tried before `se`, and the two-slot bundles
# (dative + accusative) are stripped as one unit where they fuse.
CLITICS = (
    "melo", "mela", "melos", "melas",
    "telo", "tela", "telos", "telas",
    "selo", "sela", "selos", "selas",
    "noslo", "nosla", "noslos", "noslas",
    "oslo", "osla", "oslos", "oslas",
    "nos", "os", "les", "los", "las",
    "me", "te", "se", "le", "lo", "la",
)


def deaccent(word: str) -> str:
    """Drop combining accents, keeping ñ and ü, which are letters not stress."""

    keep = {"̃"}  # tilde of ñ
    out = []
    for ch in unicodedata.normalize("NFD", word):
        if unicodedata.combining(ch) and ch not in keep:
            continue
        out.append(ch)
    return unicodedata.normalize("NFC", "".join(out))


def candidates(surface: str) -> list[str]:
    """Every base form the surface could be, once its clitics are removed.

    Three repairs, each from a real form in the deck:

    - the clitic forces a written accent the bare verb does not carry
      (`acéptalo` -> `acepta`, not `acépta`)
    - first-person plural drops its final -s before `nos`
      (`vayámonos` -> `vayamos`, `larguémonos` -> `larguemos`)
    - some forms need no repair at all (`dense` -> `den`)
    """

    seen: list[str] = []
    stems = {surface}
    for _ in range(2):  # at most two clitic slots
        for stem in list(stems):
            for clitic in CLITICS:
                if stem.endswith(clitic) and len(stem) > len(clitic) + 1:
                    stems.add(stem[: -len(clitic)])
    stems.discard(surface)
    for stem in stems:
        for form in (stem, deaccent(stem), stem + "s", deaccent(stem) + "s"):
            if form and form not in seen:
                seen.append(form)
    return seen


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--workspace", type=Path, required=True)
    ap.add_argument("--apply", action="store_true",
                    help="write events; without it, only report")
    args = ap.parse_args()
    ws = args.workspace

    cache = json.loads((ws / SD / "surface_cache.json").read_text(encoding="utf-8"))
    reverse = json.loads((ws / SD / "conjugation_reverse.json").read_text(encoding="utf-8"))

    # Only reverse conjugation is consulted, and only an unambiguous answer is
    # taken. Two rules, each from a form this got wrong first:
    #
    # - A clitic attaches to a verb, so the base is always a verb form. Falling
    #   back to the general surface cache read `dele` as the preposition `de`
    #   and `estate` as the demonstrative `esta`.
    # - Where the base is ambiguous, abstain. `diselo` strips to `di`, which is
    #   imperative of *decir* and preterite of *dar*; taking whichever came
    #   first answered `dar`, confidently and wrongly.
    #
    # An abstention is cheap -- it lands in a short manual list. A wrong lemma
    # points a card at the wrong menu and looks resolved.
    heads: dict[str, set[str]] = {}
    for surface, entries in reverse.items():
        for entry in entries or []:
            lemma = (entry.get("lemma") or "").strip()
            if lemma:
                heads.setdefault(surface.lower(), set()).add(lemma)

    ledger = json.loads(ledger_path(ws, "es").read_text(encoding="utf-8"))
    targets = [s for s, r in ledger["surfaces"].items()
               if r["verdict"] == "keep" and not r.get("lemma")]

    events, resolved, ambiguous, unresolved = [], {}, {}, []
    for surface in sorted(targets):
        found = next((heads[c.lower()] for c in candidates(surface)
                      if c.lower() in heads), None)
        if not found:
            unresolved.append(surface)
            continue
        if len(found) > 1:
            ambiguous[surface] = sorted(found)
            continue
        hit = next(iter(found))
        resolved[surface] = hit
        events.append(build_event(
            surface=surface, language="es", phase="lemma",
            reason_code="lemma_resolved",
            observer="spanishdict-clitic-stripping",
            evidence={"lemmas": [hit], "provider": "spanishdict-clitic-stripping",
                      "note": "enclitic pronouns removed, stress accent undone, "
                              "base form looked up in SpanishDict"}))

    print(f"clitic-attached without a lemma: {len(targets)}")
    print(f"  resolved: {len(resolved)}")
    for surface, lemma in sorted(resolved.items()):
        print(f"    {surface:18s} -> {lemma}")
    print(f"  ambiguous base, left for manual: {len(ambiguous)}")
    for surface, options in sorted(ambiguous.items()):
        print(f"    {surface:18s} -> {' | '.join(options)}")
    print(f"  no verb base found: {len(unresolved)}")
    print("   ", " ".join(unresolved))

    if args.apply and events:
        n = append(store_path(ws, "es"), events)
        print(f"\nappended {n} events")
    elif not args.apply:
        print("\n(dry run; pass --apply to write events)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
