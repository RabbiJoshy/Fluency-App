"""Freeze the UNISON audit panel and score runs against it.

``freeze`` writes ``research/unison/gold/<lang>-panel.jsonl`` from the hand
labels: the blind sample (``labels/<lang>-blind.jsonl``, stratum ``sample``, or
``seeded`` for chunk s01), and every example the audit found wrong with a gold
(``docs/unison/audit-300.jsonl``, stratum ``found_wrong``). Each item keeps the
gold as text (headword, POS, translation, context) as well as the menu sense id,
so it can be mapped again after a menu rebuild, and an ``accept`` list of sense
ids that count as right (gold plus equally-right alternatives; ``mwe:<phrase>``
for a phrase gold).

``score`` reads a run's stage 04 ``assignments.jsonl`` (or, with ``--v23``,
the choice frozen into the panel) and reports accuracy per stratum. Special
golds (``none:``, ``not_target:``, a phrase the menu lacks) are reported apart:
a run can only get them right through a listed alternative.

  python research/unison/score_panel.py freeze
  python research/unison/score_panel.py score --language pt --v23
  python research/unison/score_panel.py score --language es --assignments <run>/stages/04_wsd_assignments/output/assignments.jsonl
"""

from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_WORKSPACE = ROOT.parent / "Fluency-Workspace"
RELEASES = {"es": "es-speech-v23-10000x30-slim", "pt": "pt-speech-v23-10000x30-slim"}
LABELS = ROOT / "research" / "unison" / "labels"
GOLD = ROOT / "research" / "unison" / "gold"
AUDIT = ROOT / "docs" / "unison" / "audit-300.jsonl"
SPECIAL = ("phrase:", "none:", "not_target:")
# Audit causes where the example's sense pick is not what is wrong (gloss text,
# row layout, display); they stay in audit-300.jsonl but not in the panel.
NOT_A_PICK = {"junk_gloss", "sense_split_across_translations", "topic_chip_noise", "duplicated_context",
              "empty_row", "split_label_mismatch", "split_drops_expressions", "example_bucket_drift",
              "untranslated_sense"}


def read_jsonl(path: Path) -> list[dict]:
    with open(path, encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def sense_text(entry: dict) -> dict:
    return {k: entry.get(k) for k in ("label", "sense_id", "menu_analysis_id", "headword", "pos", "translation", "context")}


def resolve(label: str, menu: dict) -> dict | str:
    return label if label.startswith(SPECIAL) else sense_text(menu[label])


def accept_ids(gold: str, alt: list[str], menu: dict) -> list[str]:
    out = [menu[l]["sense_id"] for l in [gold, *alt] if l in menu]
    # stage 04 names a selected phrase "mwe:<headword>"; the menu gives it a sense id
    out += ["mwe:" + menu[l]["headword"] for l in [gold, *alt] if l in menu and menu[l]["pos"] == "PHRASE"]
    if gold.startswith("phrase:"):
        out.append("mwe:" + gold.removeprefix("phrase:").split(" = ")[0].strip())
    return sorted(set(out))


def freeze(workspace: Path) -> None:
    GOLD.mkdir(parents=True, exist_ok=True)
    audit = read_jsonl(AUDIT)
    for lang, release in RELEASES.items():
        review = workspace / "reviews" / "unison" / release
        cards = {c["card_id"]: c for c in read_jsonl(review / "cards.jsonl")}
        menus = {cid: {m["label"]: m for m in c["menu"]} for cid, c in cards.items()}
        keys = {k["id"]: k for k in read_jsonl(review / "blind-key.jsonl")}
        choices = {c["id"]: c for c in read_jsonl(review / "v23-choice.jsonl")}
        items = []
        for lab in read_jsonl(LABELS / f"{lang}-blind.jsonl"):
            key, choice = keys[lab["id"]], choices[lab["id"]]
            menu = menus[key["card_id"]]
            items.append({
                "id": lab["id"], "language": lang, "stratum": "seeded" if key["chunk"] == "s01" else "sample",
                "chunk": key["chunk"], "rank": key["rank"], "word": key["word"], "card_id": key["surface_card_id"],
                "sentence_id": key["sentence_id"], "text": key["text"], "translation": key["translation"],
                "gold": resolve(lab["gold"], menu), "alt": [resolve(a, menu) for a in lab.get("alt", []) if a in menu],
                "accept": accept_ids(lab["gold"], lab.get("alt", []), menu),
                "v23": {"label": choice.get("label"), "sense_id": (menu.get(choice.get("label")) or {}).get("sense_id"),
                        "selected": (choice.get("evidence") or {}).get("selected"), "shown": choice.get("displayed_under")},
                "conf": lab.get("conf"), "note": lab.get("note", ""),
            })
        n = 0
        for rec in audit:
            if rec["language"] != lang or "gold" not in rec or rec["cause"] in NOT_A_PICK:
                continue
            card = cards[rec["card_id"]]
            menu = menus[rec["card_id"]]
            golds = rec["gold"] if isinstance(rec["gold"], dict) else {s: rec["gold"] for s in rec["sentence_ids"]}
            for sid, label in golds.items():
                ex = card["examples"].get(sid, {})
                ev = card["evidence"].get(sid, {})
                n += 1
                items.append({
                    "id": f"{lang}-fw-{n:04d}", "language": lang,
                    "stratum": "seeded" if rec["chunk"] == "s01" else "found_wrong",
                    "chunk": rec["chunk"], "rank": rec["rank"], "word": rec["word"], "card_id": card["surface_card_id"],
                    "sentence_id": sid, "text": ex.get("t"), "translation": ex.get("e"),
                    "gold": resolve(label, menu), "alt": [resolve(a, menu) for a in rec.get("alt", []) if a in menu],
                    "accept": accept_ids(label, rec.get("alt", []), menu),
                    "v23": {"sense_id": ev.get("selected"), "shown": rec["shows"]},
                    "cause": rec["cause"], "layer": rec["layer"], "note": rec.get("note", ""),
                })
        path = GOLD / f"{lang}-panel.jsonl"
        with open(path, "w", encoding="utf-8") as handle:
            for item in items:
                handle.write(json.dumps(item, ensure_ascii=False) + "\n")
        print(f"{path.relative_to(ROOT)}: {len(items)} items {dict(Counter(i['stratum'] for i in items))}")


def load_run(path: Path, card_ids: set[str]) -> dict:
    out: dict[tuple, str | None] = {}
    marker = '"card_id":"'
    with open(path, encoding="utf-8") as handle:
        for line in handle:
            at = line.find(marker)
            if at < 0 or line[at + len(marker):line.find('"', at + len(marker))] not in card_ids:
                continue
            row = json.loads(line)
            out[(row["card_id"], str(row.get("sentence_id", "")).removeprefix("sentence_"))] = row.get("selected_sense_id")
    return out


def score(language: str, assignments: Path | None, use_v23: bool) -> None:
    items = read_jsonl(GOLD / f"{language}-panel.jsonl")
    run = None if use_v23 else load_run(assignments, {i["card_id"] for i in items})
    tally: dict[str, Counter] = defaultdict(Counter)
    by_cause: dict[str, Counter] = defaultdict(Counter)
    for item in items:
        special = isinstance(item["gold"], str)
        group = item["stratum"] + (" (special gold)" if special else "")
        chosen = item["v23"]["sense_id"] if use_v23 else run.get((item["card_id"], item["sentence_id"]))
        right = chosen in item["accept"]
        tally[group]["right" if right else "wrong"] += 1
        if run is not None and chosen is None and (item["card_id"], item["sentence_id"]) not in run:
            tally[group]["missing"] += 1
        if item.get("cause"):
            by_cause[item["cause"]]["right" if right else "wrong"] += 1
    source = "v23 (frozen choice)" if use_v23 else str(assignments)
    print(f"{language} panel scored against {source}")
    for group in sorted(tally):
        c = tally[group]
        total = c["right"] + c["wrong"]
        extra = f", {c['missing']} not in run" if c["missing"] else ""
        print(f"  {group:<32} {c['right']:>5}/{total:<5} = {100 * c['right'] / total:5.1f}%{extra}")
    if by_cause and not use_v23:
        print("  found_wrong by cause (now right / total):")
        for cause, c in sorted(by_cause.items(), key=lambda kv: -(kv[1]["right"] + kv[1]["wrong"])):
            print(f"    {cause:<34} {c['right']}/{c['right'] + c['wrong']}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="cmd", required=True)
    f = sub.add_parser("freeze")
    f.add_argument("--workspace", type=Path, default=DEFAULT_WORKSPACE)
    s = sub.add_parser("score")
    s.add_argument("--language", required=True, choices=sorted(RELEASES))
    s.add_argument("--assignments", type=Path)
    s.add_argument("--v23", action="store_true", help="score the v23 choice frozen into the panel")
    args = parser.parse_args()
    if args.cmd == "freeze":
        freeze(args.workspace)
    elif not args.v23 and not args.assignments:
        parser.error("score needs --assignments or --v23")
    else:
        score(args.language, args.assignments, args.v23)


if __name__ == "__main__":
    main()
