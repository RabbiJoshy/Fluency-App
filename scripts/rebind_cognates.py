#!/usr/bin/env python3
"""Rebind an app cognates file (cognate-score/v4) to a new release of the same deck.

The app trusts a file's per-card verdicts only for `built_from_release_id`
(decision 0028). When a release changes which senses cards show but not which
cards exist, the language-level `scores` table stays valid: a score depends
only on (surface, headword, English word). This keeps the committed table,
adds scores only for (surface, headword) pairs the new release shows and the
previous one did not, and recomputes the per-card verdicts with the app's rule.
Pairs the previous build scored are never rescored: it may have used inputs
(extracts, an English word list, surface lists) this script does not have.

    python scripts/rebind_cognates.py --language es \\
        --committed app/cognates/es/cognates.json \\
        --previous-index <ws>/releases/es/speech/<built-from id>/app/vocabulary.index.json \\
        --release-index <ws>/releases/es/speech/<id>/app/vocabulary.index.json \\
        --release-id <id> --known en [--known pl=<extract>]

Check first that rebinding to the release the file was built from reproduces
its `cards` exactly: `--check` with --release-index equal to --previous-index.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))

from fluency.core.io import json_bytes  # noqa: E402
from fluency.core.workspace import Workspace  # noqa: E402
from fluency.enrichments.card_rules import card_cognate  # noqa: E402
from fluency.enrichments.cognates import _normal_headword, build_app_cognates_by_sense  # noqa: E402


def pairs(rows) -> set[tuple[str, str]]:
    return {(_normal_headword(row.get("word")), meaning.get("headword") or "")
            for row in rows for meaning in row.get("meanings") or [] if isinstance(meaning, dict)}


def merge(base: dict, extra: dict, allowed: set[tuple[str, str]]) -> tuple[dict, int]:
    """surface -> headword -> word -> language -> value; extra adds allowed pairs only."""
    out = json.loads(json.dumps(base))
    conflicts = 0
    for surface, by_head in extra.items():
        for head, by_word in by_head.items():
            if (surface, head) not in allowed:
                continue
            for word, by_lang in by_word.items():
                slot = out.setdefault(surface, {}).setdefault(head, {}).setdefault(word, {})
                for lang, value in by_lang.items():
                    if lang in slot and slot[lang] != value:
                        conflicts += 1
                    slot[lang] = value
    return out, conflicts


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--language", required=True)
    ap.add_argument("--committed", type=Path, required=True)
    ap.add_argument("--previous-index", type=Path, required=True,
                    help="the release the committed file was built from")
    ap.add_argument("--release-index", type=Path, required=True)
    ap.add_argument("--release-id", required=True)
    ap.add_argument("--known", action="append", default=[])
    ap.add_argument("--workspace", type=Path, default=REPO.parent / "Fluency-Workspace")
    ap.add_argument("--out", type=Path)
    ap.add_argument("--check", action="store_true", help="compare recomputed cards with the committed ones")
    args = ap.parse_args()

    committed = json.loads(args.committed.read_text(encoding="utf-8"))
    rows = json.loads(args.release_index.read_text(encoding="utf-8"))
    new_pairs = pairs(rows) - pairs(json.loads(args.previous_index.read_text(encoding="utf-8")))
    known = {}
    for item in args.known or ["en"]:
        code, _, extract = item.partition("=")
        known[code] = Path(extract) if extract else None
    fresh = build_app_cognates_by_sense(
        known_extracts=known, language=args.language, config_root=REPO / "config",
        raw_root=Workspace.load(args.workspace.resolve()).root / "raw",
        release_rows=rows, release_id=args.release_id)
    scores, score_conflicts = merge(committed["scores"], fresh["scores"], new_pairs)
    matches, match_conflicts = merge(committed.get("matches") or {}, fresh.get("matches") or {}, new_pairs)
    cards: dict[str, dict[str, list]] = {}
    for row in rows:
        surface = _normal_headword(row.get("word"))
        for code in committed["known_languages"]:
            verdict = card_cognate(row, scores.get(surface), code, matches.get(surface))
            if verdict is not None and verdict[0] > 0:
                cards.setdefault(surface, {})[code] = [round(verdict[0], 3), verdict[1]]
    print(f"{args.language}: new (surface, headword) pairs {len(new_pairs)}, conflicts "
          f"{score_conflicts}/{match_conflicts}, surfaces {len(committed['scores'])} -> {len(scores)}, "
          f"cards {len(committed.get('cards') or {})} -> {len(cards)}")
    if args.check:
        old = committed.get("cards") or {}
        diff = sorted(k for k in set(old) | set(cards) if old.get(k) != cards.get(k))
        print(f"{args.language}: recomputed cards {'IDENTICAL to' if not diff else 'DIFFER from'} the committed file"
              + (f"; first differences {[(k, old.get(k), cards.get(k)) for k in diff[:6]]}" if diff else ""))
        return 1 if diff else 0
    payload = {**committed, "built_from_release_id": args.release_id, "scores": scores,
               "matches": matches, "cards": cards}
    out = args.out or args.committed
    out.write_bytes(json_bytes(payload))
    print(f"wrote {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
