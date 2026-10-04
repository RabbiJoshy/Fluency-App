#!/usr/bin/env python3
"""Tag every WSD-evaluated occurrence on a pronominal-pair card with fluency.reflexive.

A pair card is one whose menu offers both a pronominal and a non-pronominal
family: SpanishDict ``X`` beside ``Xse``, or Wiktionary senses with and
without the ``pronominal`` / ``reflexive=true`` tag. Only those cards can be
narrowed, so only their occurrences are parsed.

The occurrences are the (card, sentence) rows the source run's stage 04
evaluated: the inputs are frozen and the selection is deterministic, so a
rerun on the same freeze evaluates exactly these.

A sentence with no clitic-shaped word is ``NO_SE`` without a parse (on the
hand-labelled sets no such sentence was ever pronominal). Every other one is
parsed with the pinned parser and tagged by the detector.

    python scripts/build_reflexive_tags.py --language es \\
        --run-dir ../Fluency-Workspace/runs/es/speech/20261003T160000Z-v22-es \\
        --prewsd ../Fluency-Workspace/raw/surfaces/es/prewsd/20260914T223348Z-c35194bc-v2

Writes ``<workspace>/raw/reflexive/<lang>/tags-<run-id>.json``. Progress is
kept in ``<workspace>/cache/reflexives/tags-<lang>-<detector id>.jsonl`` so an
interrupted run resumes, and a changed detector never reuses old tags.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
import time
import warnings
from collections import Counter
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))

CLITICS = {"es": ("me", "te", "se", "nos", "os"), "pt": ("me", "te", "se", "nos", "vos")}
WORD = re.compile(r"[^\W\d_]+")
SCHEMA = "reflexive-tags/v1"


def has_clitic_shape(language: str, text: str) -> bool:
    clitics = CLITICS[language]
    return any(w in clitics or w.endswith(clitics) for w in WORD.findall(text.lower()))


def detector_id(language: str) -> str:
    """Content id of everything a tag depends on: detector code, priors, paradigms, parser."""
    import spacy
    from fluency import reflexive
    from fluency.reflexive.paths import DATA, PARADIGMS
    digest = hashlib.sha256()
    package = Path(reflexive.__file__).parent
    for path in sorted(package.glob("*.py")) + sorted(DATA.glob("*.json")):
        digest.update(path.name.encode() + path.read_bytes())
    digest.update((PARADIGMS / f"forms-{language}.json").read_bytes())
    model = reflexive.PARSERS[language]
    digest.update(f"{model}@{spacy.load(model, exclude=['ner']).meta['version']}".encode())
    return digest.hexdigest()[:16]


def pair_cards(menu: dict) -> set[str]:
    from fluency.speech.wsd_execute import build_analyses
    from fluency.wsd.languages.spanish import reflexive_families
    return {
        card["card_id"]
        for card in menu["cards"]
        if card["analyses"]
        and reflexive_families(build_analyses(card, menu_source_adapter=menu["source_adapter"]))
    }


def locate(surface: str, text: str) -> tuple[int, int] | None:
    match = re.search(r"(?<!\w)" + re.escape(surface) + r"(?!\w)", text, re.IGNORECASE)
    return (match.start(), match.end()) if match else None


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--language", required=True, choices=sorted(CLITICS))
    ap.add_argument("--run-dir", type=Path, required=True)
    ap.add_argument("--prewsd", type=Path, required=True)
    ap.add_argument("--workspace", type=Path, default=REPO.parent / "Fluency-Workspace")
    ap.add_argument("--batch-size", type=int, default=32)
    ap.add_argument("--limit", type=int, help="tag only the first N parse-needing texts (pilot)")
    args = ap.parse_args()
    warnings.filterwarnings("ignore")
    import spacy
    from fluency import reflexive

    lang = args.language
    stage = args.run_dir / "stages"
    menu = json.loads((stage / "02_sense_menu/output/sense-menu.json").read_text(encoding="utf-8"))
    pairs = pair_cards(menu)
    examples = json.loads((args.prewsd / "examples.json").read_text(encoding="utf-8"))
    cols = examples["columns"]
    text_of = {
        (sid if str(sid).startswith("sentence_") else f"sentence_{sid}"): text
        for sid, text in zip(cols["sentence_id"], cols["target"])
    }
    rows = []
    with (stage / "04_wsd_assignments/output/assignments.jsonl").open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row["card_id"] in pairs and row["status"] in ("assigned", "abstained"):
                rows.append((row["card_id"], row["surface_form"], row["sentence_id"]))
    print(f"{lang}: {len(pairs):,} pair cards, {len(rows):,} evaluated occurrences", flush=True)

    det = detector_id(lang)
    cache_path = args.workspace / "cache/reflexives" / f"tags-{lang}-{det}.jsonl"
    cache: dict[str, list] = {}
    if cache_path.exists():
        for line in cache_path.read_text(encoding="utf-8").split("\n"):
            if line.strip():
                record = json.loads(line)
                cache[record["k"]] = record["v"]
    print(f"detector {det}; {len(cache):,} cached tags in {cache_path.name}", flush=True)

    def key(surface: str, text: str) -> str:
        return hashlib.sha256(f"{surface}\x00{text}".encode()).hexdigest()[:24]

    todo: dict[str, list[tuple[str, str]]] = {}
    fresh: list[str] = []
    shortcut = unlocated = 0
    for _card, surface, sid in rows:
        text = text_of[sid]
        k = key(surface, text)
        if k in cache:
            continue
        if locate(surface, text) is None:
            cache[k] = ["BOTH", "unlocated"]
            fresh.append(k)
            unlocated += 1
        elif not has_clitic_shape(lang, text):
            cache[k] = ["NO_SE", "no clitic in sentence"]
            fresh.append(k)
            shortcut += 1
        else:
            todo.setdefault(text, []).append((surface, k))
    texts = list(todo)
    if args.limit:
        texts = texts[: args.limit]
    print(f"no-clitic shortcut {shortcut:,}, unlocated {unlocated:,}, texts to parse {len(texts):,}", flush=True)

    detector = reflexive.detector(lang)
    nlp = spacy.load(reflexive.PARSERS[lang], exclude=["ner"])
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    with cache_path.open("a", encoding="utf-8") as out:
        # Persist the parse-free decisions too, so a resume does not redo them.
        for k in fresh:
            out.write(json.dumps({"k": k, "v": cache[k]}, ensure_ascii=False) + "\n")
        start = time.time()
        for n, doc in enumerate(nlp.pipe(texts, batch_size=args.batch_size), 1):
            for surface, k in todo[doc.text]:
                span = locate(surface, doc.text)
                try:
                    label, why = detector.policy(doc, span)
                except Exception as error:  # a detector crash is an abstention, never a filter
                    label, why = "BOTH", f"detector error: {type(error).__name__}"
                cache[k] = [label, why]
                out.write(json.dumps({"k": k, "v": [label, why]}, ensure_ascii=False) + "\n")
            if n % 2000 == 0:
                out.flush()
                rate = n / (time.time() - start)
                print(f"  parsed {n:,}/{len(texts):,} ({rate:.1f}/s, ~{(len(texts) - n) / rate / 60:.0f} min left)",
                      flush=True)

    if args.limit:
        print("pilot only; no tag file written")
        return 0
    tags: dict[str, dict[str, list]] = {}
    counts: Counter = Counter()
    for card, surface, sid in rows:
        value = cache[key(surface, text_of[sid])]
        tags.setdefault(card, {})[sid] = value
        counts[value[0]] += 1
    out_path = args.workspace / "raw/reflexive" / lang / f"tags-{args.run_dir.name}.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps({
        "schema": SCHEMA,
        "language": lang,
        "source_run": args.run_dir.name,
        "prewsd": args.prewsd.name,
        "detector_id": det,
        "parser": reflexive.PARSERS[lang],
        "pair_cards": len(pairs),
        "counts": dict(counts),
        "tags": tags,
    }, ensure_ascii=False), encoding="utf-8")
    print(f"wrote {out_path}: {dict(counts)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
