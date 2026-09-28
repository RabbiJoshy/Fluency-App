#!/usr/bin/env python3
"""Pick up to three example sentences for every form in a conjugation drill.

Reads a built drill deck (``app/conjugation/data/<lang>.js``) and a named
harvest pool (``<workspace>/pools/<lang>/<pool>/sentence-bank.jsonl``) and
writes ``app/conjugation/data/<lang>-examples.json``, which the drill fetches
the first time a learner asks to see sentences for a form.

Only sentences already harvested are used. The pool was gathered for the
vocabulary's surfaces, but a sentence harvested for *si* also carries whatever
verb forms it contains, so the common verbs in the common tenses are well
covered without scanning the corpus again. Forms the pool never saw get no
entry: the drill then offers no sentences for that card rather than a guess.

How many a form gets depends on how important its verb is (``QUOTAS``): up to
three for the commonest verbs, fewer further down. Matching is on the exact
form as a whole word (or word sequence for compound tenses), case-folded.
Homographs are accepted as they are -- *fue* may be *ir* or *ser*.

A sentence is kept only if it reads as one clean line with a plausible
translation (``clean_reason`` names why one is not). Among those, Tatoeba is
preferred over subtitles, then shorter and grammatically lighter sentences,
and a sentence is not repeated within one form.

A deck with a regional locale keeps to its variety, read by the harvest's own
``variety`` tagger: a European Portuguese deck drops sentences that sound
Brazilian and ranks European ones first. It also drops the Tatoeba preference,
because Tatoeba's Portuguese is overwhelmingly Brazilian.

Output is compact: the sentences are stored once in a list and each form
points at them by position. The pool ``sentence_id`` of each sentence goes to
a sidecar, ``<lang>-examples.ids.json``, in the same order: the drill never
loads it, and it traces every pick back to its harvest record.

Usage:
    python scripts/build_conjugation_examples.py --language es \
        --pool ../Fluency-Workspace/pools/es/es-10k-speech
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any, Iterable

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPOSITORY_ROOT / "src"))

from fluency.harvest.conditioning import grammar_load, length_ratio, variety  # noqa: E402

EXAMPLES_VERSION = "conjugation-examples/v1"

# (verbs ranked below this position, sentences per form). A verb's position is
# its place in the deck's frequency ordering.
QUOTAS: tuple[tuple[int, int], ...] = ((50, 3), (200, 2))
DEFAULT_QUOTA = 1

MIN_TOKENS = 3
MAX_TOKENS = 12
RATIO_RANGE = (0.5, 2.0)
PREFERRED_SOURCE = "tatoeba"
# Deck locale -> the variety its sentences should sound like, and the sources
# that pull the other way and so lose their preference.
LOCALE_VARIETY = {"pt-PT": "european", "pt-BR": "brazilian"}

_WORD = re.compile(r"\w+", re.UNICODE)
# Subtitle furniture and markup that make a line read as something other than
# a sentence: song marks, stage directions, speaker dashes mid-line, URLs.
_NOISE = re.compile(r"[♪♫#*_<>\[\]{}()|@/\\]|https?:|www\.|\d|\s-\s|--")


def quota_for(rank: int) -> int:
    for below, quota in QUOTAS:
        if rank < below:
            return quota
    return DEFAULT_QUOTA


def tokens(text: str) -> list[str]:
    return [t.casefold() for t in _WORD.findall(text)]


def clean_reason(target: str, translation: str) -> str | None:
    """Why a pair is not a clean example, or None when it is."""

    text = target.strip()
    if not text or not translation.strip():
        return "missing_text"
    count = len(tokens(text))
    if count < MIN_TOKENS:
        return "too_short"
    if count > MAX_TOKENS:
        return "too_long"
    if _NOISE.search(text) or _NOISE.search(translation):
        return "noise"
    if text.startswith("-") or text.startswith("..."):
        return "fragment"
    if not (text[0].isupper() or text[0] in "¿¡\"«"):
        return "fragment"
    if text[-1] not in ".?!\"»":
        return "fragment"
    if text.isupper():
        return "shouting"
    ratio = length_ratio(text, translation)
    if ratio is None or not RATIO_RANGE[0] <= ratio <= RATIO_RANGE[1]:
        return "translation_length"
    return None


def load_deck(path: Path) -> dict[str, Any]:
    raw = path.read_text(encoding="utf-8")
    return json.loads(raw[raw.index("(") + 1: raw.rindex(")")])


def deck_forms(deck: dict[str, Any]) -> dict[tuple[str, ...], int]:
    """Every distinct form as a token tuple, with the best rank of its verbs."""

    forms: dict[tuple[str, ...], int] = {}
    for rank, verb in enumerate(deck["verbs"]):
        for paradigm in verb["p"].values():
            for form in paradigm["f"]:
                key = tuple(tokens(form or ""))
                if key and rank < forms.get(key, rank + 1):
                    forms[key] = rank
    return forms


def sort_key(candidate: dict[str, Any], want: str | None, preferred: str | None) -> tuple:
    return (
        bool(want) and candidate["variety"] != want,
        bool(preferred) and candidate["source"] != preferred,
        candidate["grammar"],
        abs(candidate["tokens"] - 7),
        candidate["sentence_id"],
    )


def build_examples(
    deck: dict[str, Any],
    records: Iterable[dict[str, Any]],
    pool: dict[str, Any],
) -> tuple[dict[str, Any], list[str], dict[str, int]]:
    forms = deck_forms(deck)
    longest = max((len(key) for key in forms), default=1)
    language = deck["language"]
    want = LOCALE_VARIETY.get(deck.get("locale") or "")
    preferred = None if want else PREFERRED_SOURCE
    candidates: dict[tuple[str, ...], list[dict[str, Any]]] = defaultdict(list)
    rejected: dict[str, int] = defaultdict(int)

    for record in records:
        target = (record.get("target") or {}).get("text") or ""
        translation = (record.get("translation") or {}).get("text") or ""
        words = tokens(target)
        found = {
            tuple(words[i:i + n])
            for n in range(1, longest + 1)
            for i in range(len(words) - n + 1)
            if tuple(words[i:i + n]) in forms
        }
        if not found:
            continue
        reason = clean_reason(target, translation)
        kind = variety(target, language)[0]
        if not reason and want and kind not in (want, "neutral"):
            reason = "other_variety"
        if reason:
            rejected[reason] += 1
            continue
        entry = {
            "sentence_id": record["sentence_id"],
            "source": (record.get("source") or {}).get("name") or "",
            "target": target.strip(),
            "english": translation.strip(),
            "tokens": len(words),
            "grammar": grammar_load(target, language)[0],
            "variety": kind,
        }
        for key in found:
            candidates[key].append(entry)

    sources = [source["name"] for source in pool.get("sources", [])]
    sentences: list[list[Any]] = []
    sentence_ids: list[str] = []
    positions: dict[str, int] = {}
    chosen: dict[str, list[int]] = {}
    for key in sorted(candidates):
        picked: list[int] = []
        seen: set[str] = set()
        for entry in sorted(candidates[key], key=lambda c: sort_key(c, want, preferred)):
            normal = " ".join(tokens(entry["target"]))
            if normal in seen:
                continue
            seen.add(normal)
            if entry["sentence_id"] not in positions:
                positions[entry["sentence_id"]] = len(sentences)
                source = sources.index(entry["source"]) if entry["source"] in sources else -1
                sentences.append([entry["target"], entry["english"], source])
                sentence_ids.append(entry["sentence_id"])
            picked.append(positions[entry["sentence_id"]])
            if len(picked) >= quota_for(forms[key]):
                break
        chosen[" ".join(key)] = picked

    payload = {
        "examples_version": EXAMPLES_VERSION,
        "language": language,
        "deck": {"deck_version": deck.get("deck_version"), "source": deck.get("source")},
        "pool": {
            "pool_id": pool.get("pool_id"),
            "content_id": pool.get("content_id"),
            "sources": pool.get("sources", []),
        },
        "selection": {
            "quotas": [list(q) for q in QUOTAS] + [[None, DEFAULT_QUOTA]],
            "tokens": [MIN_TOKENS, MAX_TOKENS],
            "translation_ratio": list(RATIO_RANGE),
            "preferred_source": preferred,
            "variety": want,
        },
        "sentence_fields": ["target", "english", "source"],
        "sentences": sentences,
        "forms": chosen,
    }
    stats = {
        "forms": len(forms),
        "forms_with_examples": len(chosen),
        "sentences": len(sentences),
        **{f"rejected_{k}": v for k, v in sorted(rejected.items())},
    }
    return payload, sentence_ids, stats


def read_jsonl(path: Path) -> Iterable[dict[str, Any]]:
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                yield json.loads(line)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--language", required=True)
    parser.add_argument("--pool", required=True, type=Path, help="pool directory holding pool.json")
    parser.add_argument("--deck", type=Path, default=None)
    parser.add_argument("--out", type=Path, default=None)
    args = parser.parse_args()

    data_dir = REPOSITORY_ROOT / "app" / "conjugation" / "data"
    deck_path = args.deck or data_dir / f"{args.language}.js"
    out_path = args.out or data_dir / f"{args.language}-examples.json"
    deck = load_deck(deck_path)
    if deck["language"] != args.language:
        raise SystemExit(f"{deck_path} is a {deck['language']} deck, not {args.language}")
    pool = json.loads((args.pool / "pool.json").read_text(encoding="utf-8"))
    if pool.get("language") != args.language:
        raise SystemExit(f"{args.pool} is a {pool.get('language')} pool, not {args.language}")

    payload, sentence_ids, stats = build_examples(deck, read_jsonl(args.pool / "sentence-bank.jsonl"), pool)
    out_path.write_text(json.dumps(payload, ensure_ascii=False, separators=(",", ":")) + "\n", encoding="utf-8")
    ids_path = out_path.with_name(out_path.name.replace(".json", ".ids.json"))
    ids_path.write_text(json.dumps({
        "examples_version": EXAMPLES_VERSION,
        "pool_id": pool.get("pool_id"),
        "pool_content_id": pool.get("content_id"),
        "sentence_ids": sentence_ids,
    }, separators=(",", ":")) + "\n", encoding="utf-8")
    print(json.dumps({"out": str(out_path), "bytes": out_path.stat().st_size, **stats}, indent=2))


if __name__ == "__main__":
    main()
