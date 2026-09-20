#!/usr/bin/env python3
"""Resolve SpanishDict single-word clitic forms tagged as PHRASE to their verb lemma.

SpanishDict scraped many enclitic imperative and gerund forms (e.g. déjalo,
hazlo, dime, cállate) as standalone entries with POS tagged as "PHRASE".
Because SpanishDict surface cache outranks other sources, these forms ended up
with the unstripped clitic form as their lemma, empty/broken POS, and were
treated as phrase-like entries rather than verbs.

This script intercepts those single-token clitics, resolves them to their true
verb lemma and POS VERB with clear provenance, and appends durable observation
events to events.jsonl.

    python scripts/resolve_single_word_clitics.py --workspace <ws> [--apply]
"""

from __future__ import annotations

import argparse, json, sys, unicodedata
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from fluency.surfaces.events import append, build_event, store_path  # noqa: E402
from fluency.surfaces.ledger import ledger_path  # noqa: E402

SD = "raw/dictionaries/es/spanishdict/spanishdict-complete-menu-2026-09-15-v3"

CLITICS = (
    "selos", "selas", "melos", "melas", "noslo", "nosla", "telos", "telas",
    "selo", "sela", "melo", "mela", "telo", "tela", "nos", "los", "las",
    "les", "me", "te", "se", "lo", "la", "le", "os",
)

EXPLICIT_OVERRIDES = {
    "vete": "ir",
    "vámonos": "ir",
    "vamos": "ir",
    "fuimos": "ir",
    "viste": "ver",
}


def deaccent(word: str) -> str:
    keep = {"\u0303"}  # tilde of ñ
    out = []
    for ch in unicodedata.normalize("NFD", word):
        if unicodedata.combining(ch) and ch not in keep:
            continue
        out.append(ch)
    return unicodedata.normalize("NFC", "".join(out))


def strip_clitic_candidates(surface: str) -> list[str]:
    seen: list[str] = []
    stems = {surface}
    for _ in range(2):
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
    events_path = store_path(ws, "es")

    heads: dict[str, set[str]] = {}
    for surface, entries in reverse.items():
        for entry in entries or []:
            lemma = (entry.get("lemma") or "").strip()
            if lemma:
                heads.setdefault(surface.lower(), set()).add(lemma)

    wikt_lemmas: dict[str, list[str]] = {}
    if events_path.exists():
        for line in open(events_path, encoding="utf-8"):
            if not line.strip():
                continue
            ev = json.loads(line)
            if ev.get("reason_code") == "lemma_resolved" and "enwiktionary-form-of" in (ev.get("observer") or ""):
                w = ev.get("subject", {}).get("id")
                lems = ev.get("evidence", {}).get("lemmas", [])
                if w and lems:
                    wikt_lemmas[w] = [l.split()[0] for l in lems]

    ledger = json.loads(ledger_path(ws, "es").read_text(encoding="utf-8"))
    surfaces = ledger.get("surfaces", {})

    ranks = {s: r.get("rank") for s, r in surfaces.items() if r.get("rank")}

    events = []
    dephrased = []
    for surface, entry in sorted(surfaces.items()):
        if entry.get("verdict") != "keep":
            continue
        if " " in surface:
            continue
        sd = cache.get(surface)
        if not sd:
            continue
        analyses = sd.get("dictionary_analyses") or []
        is_sd_phrase = bool(analyses) and all(
            all(str(s.get("pos", "")).upper() == "PHRASE" for s in a.get("senses", []))
            for a in analyses if a.get("senses")
        )
        has_clitic = any(surface.endswith(c) and len(surface) > len(c) + 1 for c in CLITICS)
        if not (is_sd_phrase and has_clitic):
            continue

        target_lemma = EXPLICIT_OVERRIDES.get(surface)
        if not target_lemma:
            w_lems = wikt_lemmas.get(surface) or []
            if w_lems:
                sorted_w = sorted(w_lems, key=lambda l: ranks.get(l, 10**9))
                target_lemma = sorted_w[0]
        if not target_lemma:
            found = next((heads[c.lower()] for c in strip_clitic_candidates(surface)
                          if c.lower() in heads), None)
            if found:
                sorted_f = sorted(found, key=lambda l: ranks.get(l, 10**9))
                target_lemma = sorted_f[0]

        if not target_lemma:
            print(f"  unresolved clitic phrase: {surface}")
            continue

        ev = build_event(
            surface=surface,
            language="es",
            phase="lemma",
            reason_code="lemma_resolved",
            observer="observe_lemmas/spanishdict-clitic-dephrased",
            evidence={
                "lemmas": [target_lemma],
                "pos": ["VERB"],
                "priority": 0,
                "provider": "spanishdict-clitic-dephrased",
                "note": (
                    f"Intercepted from SpanishDict PHRASE classification; "
                    f"mapped to root verb lemma '{target_lemma}' and POS VERB "
                    f"with original SpanishDict headword preserved as alternate"
                ),
                "spanishdict_original_pos": "PHRASE",
            },
        )
        events.append(ev)
        dephrased.append((surface, entry.get("rank"), entry.get("lemma"), target_lemma))

    print(f"Single-word clitics intercepted: {len(events)}")
    for surface, rank, old_lemma, new_lemma in sorted(dephrased, key=lambda x: x[1] or 99999)[:30]:
        print(f"  rank {rank:>4}: {surface:14s} -> {new_lemma:12s} (was: {old_lemma})")

    if args.apply and events:
        n = append(store_path(ws, "es"), events)
        print(f"\nAppended {n} durable events to {store_path(ws, 'es')}")
    elif not args.apply:
        print("\n(Dry run; pass --apply to record events)")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
