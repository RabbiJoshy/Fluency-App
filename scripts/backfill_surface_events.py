#!/usr/bin/env python3
"""Record what the existing artifacts already know about each surface.

Everything here was learned during the September audits and then lived only in
a chat log: that "out" and "lady" are English sitting in a Portuguese list,
that SpanishDict answers "comelo" when asked for "cogelo", that "dallas" is
capitalised in every one of its 38 corpus occurrences and is glossed "to
scythe". Writing it into the store makes it survive the conversation.

Reads only artifacts already on disk -- no fetching, no model.

    python scripts/backfill_surface_events.py --workspace <ws> --language pt
"""

from __future__ import annotations

import argparse, json, re, sys, unicodedata
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from fluency.surfaces.events import append, build_event, store_path  # noqa: E402

WORDLIST = Path("/usr/share/dict/words")
CAPS_MIN_OCCURRENCES = 5
CAPS_THRESHOLD = 0.80


def deacc(word: str) -> str:
    return unicodedata.normalize("NFD", word.lower()).encode("ascii", "ignore").decode()


def latest_run(workspace: Path, language: str) -> Path | None:
    marker = workspace / f"runs/{language}/speech/LATEST_V11"
    if not marker.exists():
        return None
    return workspace / f"runs/{language}/speech/{marker.read_text().strip()}"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--workspace", type=Path, required=True)
    ap.add_argument("--language", required=True)
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    ws, lang = args.workspace, args.language

    run = latest_run(ws, lang)
    if run is None:
        print(f"{lang}: no LATEST_V11 run"); return 1
    stages = run / "stages"
    inv = json.loads((stages / "01_inventory/output/inventory.json").read_text())
    surfaces = {c["card_id"]: c["display_form"] for c in inv["cards"]}
    events = []

    def note(surface, phase, code, evidence):
        events.append(build_event(surface=surface, language=lang, phase=phase,
                                  reason_code=code, observer="backfill/v1",
                                  evidence=evidence, run_id=run.name))

    # 1. the list against an English wordlist, and against its own accented forms
    english = {l.strip().lower() for l in WORDLIST.open(encoding="utf-8", errors="ignore") if l.strip()}
    stripped = {}
    for form in surfaces.values():
        if deacc(form) != form.lower():
            stripped.setdefault(deacc(form), form.lower())
    for form in surfaces.values():
        low = form.lower()
        if low in english and deacc(low) == low:
            note(form, "list", "english_wordlist", {"wordlist": "web2"})
        if low in stripped:
            note(form, "list", "accent_stripped_duplicate",
                 {"accented_form": stripped[low]})
        if re.fullmatch(r"[a-zá-ú]{1,6}\.", low):
            note(form, "list", "abbreviation_form", {})

    # 2. the menu build: which surfaces the dictionary had nothing for
    menu_path = stages / "02_sense_menu/output/sense-menu.json"
    if menu_path.exists():
        menu = json.loads(menu_path.read_text())
        for card in menu.get("cards", []):
            if not (card.get("analyses") or card.get("headword_analyses") or []):
                form = surfaces.get(card["card_id"])
                if form:
                    note(form, "menu", "dictionary_absent", {"provider": "menu_build"})

    # 3. the corpus: capitalisation, which only a harvest can show
    harvest = stages / "03_sentence_harvest/output"
    if (harvest / "sentence-bank.jsonl").exists():
        bank = {}
        with (harvest / "sentence-bank.jsonl").open(encoding="utf-8") as fh:
            for line in fh:
                if line.strip():
                    row = json.loads(line)
                    bank[row["sentence_id"]] = (row.get("target") or {}).get("text", "") or ""
        cand = json.loads((harvest / "candidates.json").read_text())
        for card in cand["cards"]:
            form = surfaces.get(card["card_id"])
            if not form:
                continue
            pattern = re.compile(r"(?<!^)(?<![.!?]\s)\b(" + re.escape(form) + "|"
                                 + re.escape(form.capitalize()) + r")\b")
            caps = total = 0
            for item in card.get("candidates", [])[:40]:
                for match in pattern.finditer(bank.get(item["sentence_id"], "")):
                    total += 1
                    caps += match.group(1)[:1].isupper()
            if total >= CAPS_MIN_OCCURRENCES and caps / total > CAPS_THRESHOLD:
                note(form, "harvest", "capitalised_in_corpus",
                     {"capitalised": round(caps / total, 3), "occurrences": total})

    # 4. the Spanish refetch: the site's own verdicts
    refetch = ws / "raw/dictionaries/es/spanishdict/refetch-menuless.jsonl"
    if lang == "es" and refetch.exists():
        for line in refetch.open(encoding="utf-8"):
            row = json.loads(line)
            for flag in row.get("flags") or []:
                if flag.startswith("spelling_substitution:"):
                    note(row["word"], "menu", "dictionary_spelling_substitution",
                         {"answered_instead": flag.split(":", 1)[1], "provider": "spanishdict"})
                elif flag == "entry_lang_not_spanish":
                    note(row["word"], "menu", "dictionary_entry_language",
                         {"entry_lang": row.get("entry_lang"), "provider": "spanishdict"})

    # 5. the Czech scrape: lemma resolution, and lemmas the dictionary lacks
    scrape = ws / "raw/frequency/cnk-kontext/svk-cs.jsonl"
    if lang == "cs" and scrape.exists():
        heads = set()
        wikt = ws / "raw/wiktionary/enwiktionary-2026-09-06/kaikki.org-dictionary-Czech.jsonl"
        if wikt.exists():
            with wikt.open(encoding="utf-8") as fh:
                for line in fh:
                    try: heads.add(json.loads(line)["word"].lower())
                    except Exception: pass
        for line in scrape.open(encoding="utf-8"):
            row = json.loads(line)
            lemmas = [a["lemma"] for a in row["analyses"] if a.get("lemma")]
            if not lemmas:
                continue
            analyses = [
                {"lemma": a.get("lemma"),
                 "pos": [x for x in (a.get("pos_label") or []) if x],
                 "ipm": a.get("ipm")}
                for a in row["analyses"] if a.get("lemma")
            ][:6]
            note(row["word"], "lemma", "lemma_resolved",
                 {"lemmas": lemmas[:4],
                  "pos": sorted({p for a in analyses for p in a["pos"]}),
                  "analyses": analyses,
                  "provider": "cnk-word-at-a-glance"})
            if heads and not any(l.lower() in heads for l in lemmas):
                note(row["word"], "lemma", "lemma_absent_from_dictionary",
                     {"lemmas": lemmas[:4], "dictionary": "enwiktionary-cs"})

    path = store_path(ws, lang)
    import collections
    counts = collections.Counter(e["reason_code"] for e in events)
    print(f"{lang}: {len(events):,} observations over {len({e['subject']['id'] for e in events}):,} surfaces")
    for code, n in counts.most_common():
        print(f"   {code:<36} {n:>6,}")
    if args.dry_run:
        print("(dry run, nothing written)")
        return 0
    written = append(path, events)
    print(f"wrote {written:,} new to {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
