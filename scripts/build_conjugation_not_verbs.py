#!/usr/bin/env python3
"""List the drill forms that the vocabulary treats as something other than a verb.

The verb drill puts first the verbs a learner got wrong in the vocabulary
flashcards. A flashcard is a word as it appeared, so a missed *tuvimos* points
at *tener*. But *casa* is also a form of *casar*, *para* of *parar* and *entre*
of *entrar*, and a missed noun or preposition card should not pull a verb
forward.

This reads a built drill deck (``app/conjugation/data/<lang>.js``), the speech
vocabulary index the app ships for that language and the language's surface
ledger, and writes ``app/conjugation/data/<lang>-not-verbs.js``: the drill
forms (and infinitives) judged not to be verbs. The drill skips exactly those.
A word the vocabulary does not have, or one it only knows inside phrases, is
not listed, so it still counts: the list declares what is known to be
something else and assumes nothing about the rest.

A word is listed when either

* its card has no verb sense at all (*casa*, *para*, *entre*), or
* its verb senses are the minority and its ledger lemma is not one of the
  deck's verbs,

and in either case the ledger does not tag it ``verb``. The guards are there
because the Wiktionary releases (pt, cs) misassign plenty of verb forms:
*andavas* goes mostly to "apartment", *pomůžeme* only to the noun "help".
Their ledger rows still say ``andar`` and ``verb``. The lemma guard is not
enough on its own for the first case: Portuguese *casa* has ``casar`` as its
ledger lemma.

Sense weight is the WSD frequency, summed per part of speech across every
card for the word (homograph cards may be split). ``PHRASE`` senses are left
out, since a phrase says nothing about the word's own class. Where no sense
carries a frequency (a release without WSD), each sense counts once.

Usage:
    python scripts/build_conjugation_not_verbs.py --language es \
        --workspace ../Fluency-Workspace \
        --index ../Fluency-Workspace/releases/es/speech/<release>/app/vocabulary.index.json
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "app/conjugation/data"
sys.path.insert(0, str(ROOT / "src"))

from fluency.surfaces.ledger import ledger_path  # noqa: E402

IGNORED_POS = {"phrase"}


def pos_class(label: str) -> str:
    """Providers label senses differently: VERB (UD), "transitive verb" and
    "pronominal verb" (SpanishDict), "verb" (Wiktionary). All are verbs."""

    words = label.strip().lower().replace("_", " ").split()
    return "verb" if "verb" in words or "aux" in words else " ".join(words)


def load_deck(path: Path) -> dict[str, Any]:
    raw = path.read_text(encoding="utf-8")
    return json.loads(raw[raw.index("(") + 1: raw.rindex(")")])


def deck_words(deck: dict[str, Any]) -> set[str]:
    """Single-word forms and infinitives; compound forms never match a card."""

    words = set()
    for verb in deck["verbs"]:
        words.add(verb["h"].lower())
        for paradigm in verb["p"].values():
            for form in paradigm["f"]:
                if form and " " not in form:
                    words.add(form.lower())
    return words


def pos_weights(entries: list[dict[str, Any]]) -> dict[str, float]:
    meanings = [m for entry in entries for m in entry.get("meanings") or []
                if m.get("pos") and pos_class(m["pos"]) not in IGNORED_POS]
    weighted = any(float(m.get("frequency") or 0) > 0 for m in meanings)
    totals: dict[str, float] = defaultdict(float)
    for m in meanings:
        totals[pos_class(m["pos"])] += float(m.get("frequency") or 0) if weighted else 1.0
    return dict(totals)


def ledger_tags_verb(row: dict[str, Any] | None) -> bool:
    return bool(row) and any(pos_class(str(p)) == "verb" for p in row.get("part_of_speech") or [])


def ledger_lemma_is_drill_verb(row: dict[str, Any] | None, infinitives: set[str]) -> bool:
    return bool(row) and any(str(lemma).lower() in infinitives for lemma in row.get("lemmas") or [])


def is_not_verb(totals: dict[str, float], ledger_row: dict[str, Any] | None,
                infinitives: set[str]) -> bool:
    if not totals or ledger_tags_verb(ledger_row):
        return False  # nothing to judge by, or the ledger says verb outright
    verb = totals.get("verb", 0.0)
    if not verb:
        return True
    other = max((v for pos, v in totals.items() if pos != "verb"), default=0.0)
    return verb < other and not ledger_lemma_is_drill_verb(ledger_row, infinitives)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--language", required=True)
    parser.add_argument("--workspace", required=True, type=Path)
    parser.add_argument("--index", required=True, type=Path,
                        help="the release's app/vocabulary.index.json")
    args = parser.parse_args()

    deck = load_deck(DATA / f"{args.language}.js")
    forms = deck_words(deck)
    infinitives = {verb["h"].lower() for verb in deck["verbs"]}

    by_word: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for entry in json.loads(args.index.read_text(encoding="utf-8")):
        word = str(entry.get("word") or "").strip().lower()
        if word in forms:
            by_word[word].append(entry)

    ledger = json.loads(ledger_path(args.workspace, args.language).read_text(encoding="utf-8"))
    ledger_rows = {str(row.get("surface") or key).lower(): row
                   for key, row in ledger["surfaces"].items()}

    not_verbs = sorted(w for w, entries in by_word.items()
                       if is_not_verb(pos_weights(entries), ledger_rows.get(w), infinitives))
    release = args.index.parent.parent.name
    payload = {"language": args.language, "release": release, "words": not_verbs}
    out = DATA / f"{args.language}-not-verbs.js"
    out.write_text(
        "/* Built by scripts/build_conjugation_not_verbs.py from " + release + ". */\n"
        "window.registerConjugationNotVerbs && window.registerConjugationNotVerbs("
        + json.dumps(payload, ensure_ascii=False, separators=(",", ":")) + ");\n",
        encoding="utf-8",
    )
    print(f"{args.language}: {len(by_word)} drill forms are vocabulary words, "
          f"{len(not_verbs)} not verbs -> {out.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
