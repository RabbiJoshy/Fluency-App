"""Compare the blind panel labels with what v23 chose.

Labels (``research/unison/labels/<lang>-blind.jsonl``) are written before v23's
choice is opened and are never revised afterwards. A v23 choice counts as right
when it is the gold label or one of the listed equally-right alternatives.
Special golds (``phrase:``, ``none:``, ``not_target:``) name something the menu
does not offer, so only a listed alternative can be right.

  python research/unison/compare_blind.py --language es [--chunk t01] [--show]
"""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_WORKSPACE = ROOT.parent / "Fluency-Workspace"
RELEASES = {"es": "es-speech-v23-10000x30-slim", "pt": "pt-speech-v23-10000x30-slim"}


def read_jsonl(path: Path) -> list[dict]:
    with open(path, encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def accepted_labels(label: dict) -> set[str]:
    accepted = set(label.get("alt") or [])
    if ":" not in label["gold"]:
        accepted.add(label["gold"])
    return accepted


def judge(label: dict, choice: dict) -> bool:
    return choice.get("label") in accepted_labels(label)


def norm_gloss(entry: dict | None) -> str:
    return " ".join(str((entry or {}).get("translation") or "").lower().split())


def judge_gloss(label: dict, choice: dict, menu: dict) -> bool:
    """Learner-visible: v23's sense shows the same headword and gloss as an accepted sense."""
    shown = (str(choice.get("headword") or "").lower(), " ".join(str(choice.get("translation") or "").lower().split()))
    return any((str(menu[l].get("headword") or "").lower(), norm_gloss(menu[l])) == shown
               for l in accepted_labels(label) if l in menu)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--language", required=True, choices=sorted(RELEASES))
    parser.add_argument("--workspace", type=Path, default=DEFAULT_WORKSPACE)
    parser.add_argument("--chunk", action="append", help="limit to these chunks (repeatable)")
    parser.add_argument("--show", action="store_true", help="print every disagreement")
    args = parser.parse_args()

    review = args.workspace / "reviews" / "unison" / RELEASES[args.language]
    keys = {k["id"]: k for k in read_jsonl(review / "blind-key.jsonl")}
    choices = {c["id"]: c for c in read_jsonl(review / "v23-choice.jsonl")}
    labels = read_jsonl(ROOT / "research" / "unison" / "labels" / f"{args.language}-blind.jsonl")
    if args.chunk:
        labels = [l for l in labels if keys[l["id"]]["chunk"] in args.chunk]

    tally = Counter()
    for label in labels:
        key, choice = keys[label["id"]], choices[label["id"]]
        right = judge(label, choice)
        tally["right" if right else "wrong"] += 1
        tally["gloss_right"] += right or judge_gloss(label, choice, key["menu"])
        tally[f"{label['conf']}:{'right' if right else 'wrong'}"] += 1
        if label["gold"].split(":", 1)[0] in ("phrase", "none", "not_target"):
            tally["special_gold"] += 1
        if args.show and not right:
            gold = key["menu"].get(label["gold"], {})
            gold_text = f"{gold.get('headword')}: {gold.get('translation')}" if gold else label["gold"]
            print(f"{label['id']}  #{key['rank']} {key['word']}  [{label['conf']}]\n"
                  f"    {key['text']}  |  {key['translation']}\n"
                  f"    gold {label['gold']} {gold_text}   v23 {choice.get('label')} {choice.get('headword')}: "
                  f"{choice.get('translation')}  (shown under {choice.get('displayed_under')})"
                  + (f"\n    note: {label['note']}" if label.get("note") else ""))
    total = tally["right"] + tally["wrong"]
    if total:
        print(f"{args.language}: {tally['right']}/{total} right = {tally['right'] / total:.1%}; "
              f"same gloss shown {tally['gloss_right']}/{total} = {tally['gloss_right'] / total:.1%}  "
              f"(sure {tally['sure:right']}/{tally['sure:right'] + tally['sure:wrong']}, "
              f"unsure {tally['unsure:right']}/{tally['unsure:right'] + tally['unsure:wrong']}; "
              f"special golds {tally['special_gold']})")


if __name__ == "__main__":
    main()
