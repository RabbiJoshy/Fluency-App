#!/usr/bin/env python3
"""Write a language's Merge Lemmas data: contractions, and each card's merge key.

Merge Lemmas folds a spelling into its lemma's card. A contraction must not
fold: Portuguese ``no`` is em + o and ``disso`` is de + isso, but the card's
senses only carry the lemma the menu resolved them to (em, de), so the app
cannot see that from the card. Wiktionary states it outright, as a sense
glossed "contraction of X + Y", and this script lifts that list out.

SpanishDict marks contractions with their own part of speech (al, del), so a
SpanishDict language needs no extract.

Speech decks load a card's senses only when its set is opened, and Merge
Lemmas decides at set-up, before that. So with ``--release-index`` the merge
key of every card in the release is computed here from its full senses, by the
app's own rule (``fluency.enrichments.card_rules.lemma_group_key``, decision
0028), and shipped as ``keys``: "" keeps the card on its own.

    python scripts/build_merge_exceptions.py --language pt \
        --extract <workspace>/raw/wiktionary/<snapshot>/kaikki.org-dictionary-Portuguese.jsonl \
        --release-index <workspace>/releases/pt/speech/<id>/app/vocabulary.index.json

Writes app/data/merge-exceptions/<language>.json.
"""

from __future__ import annotations

import argparse
import gzip
import json
import re
from pathlib import Path

from fluency.enrichments.card_rules import lemma_group_key, lemma_headwords, normal_token
from fluency.core.hashing import file_content_id
from fluency.sense_menu.noun_merge import RULE_VERSION, stamp_noun_merge

ROOT = Path(__file__).resolve().parents[1]
CONTRACTION = re.compile(r"^\s*contraction of\b", re.IGNORECASE)
# A contraction nobody uses any more is no reason to keep a live spelling apart.
DEAD_TAGS = {"obsolete", "archaic", "dated", "historical", "rare", "poetic", "dialectal"}


def contractions(extract: Path) -> list[str]:
    opener = gzip.open if str(extract).endswith(".gz") else open
    found: set[str] = set()
    with opener(extract, "rt", encoding="utf-8") as handle:
        for line in handle:
            if "ontraction of" not in line:
                continue
            entry = json.loads(line)
            word = str(entry.get("word") or "").strip().lower()
            if not word or " " in word:
                continue
            for sense in entry.get("senses") or []:
                if DEAD_TAGS & set(sense.get("tags") or []):
                    continue
                if any(CONTRACTION.match(str(gloss)) for gloss in sense.get("glosses") or []):
                    found.add(word)
                    break
    return sorted(found)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--language", required=True)
    parser.add_argument("--extract", type=Path, help="Wiktionary extract (not needed for SpanishDict)")
    parser.add_argument("--release-index", type=Path, help="release whose cards get a merge key")
    parser.add_argument("--sense-menu", type=Path, help="complete uninflected stage-02 menu for that release")
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    if args.sense_menu and not args.release_index:
        parser.error("--sense-menu requires --release-index")

    out = args.out or ROOT / "app" / "data" / "merge-exceptions" / f"{args.language}.json"
    words = contractions(args.extract) if args.extract else []
    keys = {}
    noun_verdicts = {}
    release = None
    if args.release_index:
        rows = json.loads(args.release_index.read_text(encoding="utf-8"))
        if args.sense_menu:
            menu = json.loads(args.sense_menu.read_text(encoding="utf-8"))
            if menu.get("language") != args.language:
                raise ValueError("sense menu language does not match --language")
            cards = menu["cards"]
            stamp_noun_merge(cards)
            by_id = {card["card_id"]: card for card in cards}
            for row in rows:
                card = by_id.get(row.get("surface_card_id"))
                if card is None or normal_token(card.get("surface_form")) != normal_token(row.get("word")):
                    raise ValueError("sense menu does not match the release's surface cards")
                if "noun_merge" in card:
                    if card["noun_merge"]["allowed"]:
                        senses = [*(row.get("meanings") or []), *(row.get("unused_menu_senses") or [])]
                        senses.extend(s for m in row.get("meanings") or [] for s in m.get("allSenses") or [])
                        references = {s["source_reference"] for s in senses if s.get("source_reference")
                                      and s["source_reference"] != "mwe-merged/v1"}
                        menu_references = {s["source_reference"] for a in card["analyses"]
                                           for s in a["senses"]}
                        if references != menu_references:
                            raise ValueError("approved noun menu does not match the release's complete source senses")
                    row["noun_merge"] = card["noun_merge"]
        noun_verdicts = {normal_token(row["word"]): row["noun_merge"] for row in rows
                         if row.get("word") and "noun_merge" in row}
        # Only rows whose senses name a headword: a headword-less row falls
        # back in the app to the lemma column the release ships, which the
        # full rows here do not carry.
        keys = {
            normal_token(row["word"]): lemma_group_key(row, words)
            for row in rows
            if row.get("word") and (lemma_headwords(row) or row.get("noun_merge"))
        }
        release = args.release_index.parent.parent.name
    payload = {
        "schema": "merge-exceptions/v3",
        "noun_merge_rule": RULE_VERSION,
        "language": args.language,
        "source": f"wiktionary:{args.extract.parent.name}/{args.extract.name}" if args.extract else None,
        "release_id": release,
        "contractions": words,
        # surface -> the lemma it merges into, "" for its own card
        "keys": keys,
        "noun_verdicts": noun_verdicts,
    }
    if args.release_index:
        payload["release_index_content_id"] = file_content_id(args.release_index)
    if args.sense_menu:
        payload["sense_menu_content_id"] = file_content_id(args.sense_menu)
        if menu.get("noun_merge_refresh"):
            payload["evidence"] = menu["noun_merge_refresh"]
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    separate = sum(1 for key in keys.values() if not key)
    print(f"{args.language}: {len(words)} contractions, {len(keys)} keys ({separate} own card) -> {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
