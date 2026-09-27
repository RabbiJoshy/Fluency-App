#!/usr/bin/env python3
"""Create the required human-review queue and WordNet comparison for one run."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import tarfile
import xml.etree.ElementTree as ET


def read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def wordnet_lemmas(archive: Path) -> set[str]:
    with tarfile.open(archive, "r:xz") as packed:
        members = [member for member in packed.getmembers() if member.name.endswith(".xml")]
        if len(members) != 1:
            raise ValueError(f"expected one WordNet XML member, found {len(members)}")
        stream = packed.extractfile(members[0])
        if stream is None:
            raise ValueError("WordNet XML member could not be opened")
        lemmas: set[str] = set()
        for _, element in ET.iterparse(stream, events=("end",)):
            if element.tag.endswith("Lemma"):
                written = element.attrib.get("writtenForm")
                if written:
                    lemmas.add(written.casefold())
            element.clear()
    return lemmas


def build(run: Path, wordnet: Path, output: Path) -> None:
    run = run.resolve()
    output.mkdir(parents=True, exist_ok=False)
    inventory = read_json(run / "stages/01_inventory/output/inventory.json")
    menu_report = read_json(run / "stages/02_sense_menu/output/report.json")
    candidates = read_json(run / "stages/03_sentence_harvest/output/candidates.json")
    sentences: dict[str, dict] = {}
    with (run / "stages/03_sentence_harvest/output/sentence-bank.jsonl").open(encoding="utf-8") as stream:
        for line in stream:
            row = json.loads(line)
            sentences[row["sentence_id"]] = row

    menu_by_card = {row["card_id"]: row for row in menu_report["per_surface"]}
    candidates_by_card = {row["card_id"]: row for row in candidates["cards"]}
    wn_lemmas = wordnet_lemmas(wordnet)
    counts = {"both": 0, "provider_only": 0, "wordnet_only": 0, "neither": 0}
    rescued: list[dict] = []
    queue: list[dict] = []
    for card in inventory["cards"]:
        menu = menu_by_card[card["card_id"]]
        provider_ready = menu["status"] == "ready"
        in_wordnet = card["surface_key"].casefold() in wn_lemmas
        bucket = (
            "both" if provider_ready and in_wordnet
            else "provider_only" if provider_ready
            else "wordnet_only" if in_wordnet
            else "neither"
        )
        counts[bucket] += 1
        if bucket == "wordnet_only":
            rescued.append({"rank": card["rank"], "surface": card["surface_key"]})
        sample_rows = []
        for candidate in candidates_by_card.get(card["card_id"], {}).get("candidates", [])[:3]:
            sentence = sentences[candidate["sentence_id"]]
            sample_rows.append(
                {
                    "sentence_id": candidate["sentence_id"],
                    "source": candidate["source"],
                    "target": sentence["target"]["text"],
                    "translation": sentence["translation"]["text"],
                }
            )
        queue.append(
            {
                "review_version": "language-onboarding-review/v1",
                "run_id": run.name,
                "language": inventory["language"],
                "rank": card["rank"],
                "card_id": card["card_id"],
                "surface": card["surface_key"],
                "provider_menu": {
                    "status": menu["status"],
                    "analysis_count": menu["analysis_count"],
                    "sense_count": menu["sense_count"],
                },
                "wordnet_direct_lemma": in_wordnet,
                "example_samples": sample_rows,
                "review": {
                    "status": "pending",
                    "decision": None,
                    "word_class": None,
                    "reason": None,
                    "reviewer": None,
                    "reviewed_at": None,
                },
                "allowed_decisions": [
                    "keep_provider_menu", "exclude_contamination", "class_tag",
                    "headword_override", "expansion", "entity",
                    "declared_one_sense", "curated_function_menu",
                ],
            }
        )
    comparison = {
        "comparison_version": "menu-source-comparison/v1",
        "run_id": run.name,
        "language": inventory["language"],
        "inventory_cards": len(queue),
        "provider_ready": menu_report["cards_ready"],
        "provider_no_menu": menu_report["cards_without_menu"],
        "wordnet_direct_lemma_matches": counts["both"] + counts["wordnet_only"],
        "coverage_buckets": counts,
        "provider_gaps_rescued_by_direct_wordnet_lemma": rescued,
        "warning": (
            "Direct lemma overlap is a comparison signal only. Inflected forms, function "
            "words and duplicate meanings require human review before any provider merge."
        ),
    }
    (output / "menu-comparison.json").write_text(
        json.dumps(comparison, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    with (output / "manual-review.jsonl").open("w", encoding="utf-8") as stream:
        for row in queue:
            stream.write(json.dumps(row, ensure_ascii=False) + "\n")
    summary = (
        f"# {inventory['language']} 2,000-card onboarding review\n\n"
        f"- Run: `{run.name}`\n"
        f"- Human decisions complete: **0/{len(queue)}**\n"
        f"- Provider menus: **{menu_report['cards_ready']}/{len(queue)}**\n"
        f"- Provider gaps: **{menu_report['cards_without_menu']}**\n"
        f"- Direct WordNet lemma overlap: **{comparison['wordnet_direct_lemma_matches']}/{len(queue)}**\n"
        f"- Provider gaps with a direct WordNet lemma: **{counts['wordnet_only']}**\n\n"
        "Release gate: every row in `manual-review.jsonl` must receive a human decision, "
        "with exceptions copied into versioned inventory adjudications or declared entries.\n"
    )
    (output / "README.md").write_text(summary, encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run", type=Path, required=True)
    parser.add_argument("--wordnet", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    build(args.run, args.wordnet, args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
