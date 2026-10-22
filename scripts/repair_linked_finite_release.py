#!/usr/bin/env python3
"""Create an immutable successor with corrected verb-level learner cues.

No WSD is rerun. Card/sense identities, distributions, examples and function
word labels are retained. Source grammar is preserved as correction evidence.
"""
from __future__ import annotations

import argparse
from datetime import UTC, datetime
import json
from pathlib import Path
import shutil

from fluency.core.hashing import file_content_id
from fluency.release.index_shards import shard_app_index
from fluency.release.linked_finite_forms import correction_plan, repair_meaning
from fluency.release.validation import validate_release_bundle


def read(path):
    return json.loads(path.read_text())


def write(path, value):
    with path.open("w") as stream:
        json.dump(value, stream, ensure_ascii=False, separators=(",", ":"))
        stream.write("\n")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--destination", type=Path, required=True)
    parser.add_argument("--snapshot", type=Path, required=True)
    parser.add_argument("--glosses", type=Path, default=Path("config/learner-cues/pt-linked-finite-forms-v1.json"))
    args = parser.parse_args()
    source, destination = args.source.resolve(), args.destination.resolve()
    if destination.exists():
        raise ValueError("successor destination already exists")
    index = read(source / "app/vocabulary.index.json")
    old_ids = [(c["id"], c["surface_card_id"], [m.get("sense_id") for m in c["meanings"]]) for c in index]
    wanted = {m.get("source_sense_id") for c in index for m in c["meanings"]
              if "preterite/pluperfect indicative of " in m.get("translation", "")}
    rows = []
    with args.snapshot.open() as stream:
        for line in stream:
            row = json.loads(line)
            if any(s.get("id") in wanted for s in row.get("senses", [])):
                rows.append(row)
    plan = correction_plan(index, rows, read(args.glosses)["glosses"], read(source / "app/conjugations.json"))
    if not plan or len(plan) != len(wanted):
        raise ValueError(f"incomplete correction coverage: {len(plan)} / {len(wanted)}")
    for card in index:
        card["meanings"] = [repair_meaning(m, plan) for m in card["meanings"]]
        if any(m.get("sense_id") in plan for m in card["meanings"]):
            card.pop("lemma", None)  # regenerate the skinny lookup column
    assert old_ids == [(c["id"], c["surface_card_id"], [m.get("sense_id") for m in c["meanings"]]) for c in index]
    print(f"Correcting {len(plan)} readings on {len({p['surface'] for p in plan.values()})} cards", flush=True)
    shutil.copytree(source, destination, ignore=shutil.ignore_patterns("deck.json"))
    write(destination / "app/vocabulary.index.json", index)
    del index
    shard_app_index(destination / "app", slim=True)
    print("Updating deck and preserving example assignments", flush=True)
    deck = read(source / "deck.json")
    deck["release_id"] = destination.name
    changed = 0
    for card in deck["cards"]:
        for i, meaning in enumerate(card["meanings"]):
            if meaning.get("sense_id") in plan:
                card["meanings"][i] = repair_meaning(meaning, plan)
                changed += 1
    assert changed == len(plan)
    write(destination / "deck.json", deck)
    del deck
    now = datetime.now(UTC).isoformat()
    report = {"version": "linked-finite-form-release-correction/v1",
              "source_release": source.name, "release_id": destination.name,
              "snapshot_content_id": file_content_id(args.snapshot),
              "glosses_content_id": file_content_id(args.glosses),
              "created_at": now, "wsd_rerun": False,
              "readings": list(plan.values()),
              "preserved": ["card_ids", "sense_ids", "meaning_order", "example_assignments", "wsd_distributions", "function_word_labels", "progress_namespace"]}
    write(destination / "linked-finite-form-corrections.json", report)
    composition = read(destination / "composition.json")
    composition.update(release_id=destination.name, created_at=now, publication_status="inactive_audit")
    composition["learner_cue_correction"] = {
        "method": report["version"], "source_release": source.name,
        "report_path": "linked-finite-form-corrections.json",
        "report_content_id": file_content_id(destination / "linked-finite-form-corrections.json")}
    write(destination / "composition.json", composition)
    manifest = read(destination / "manifest.json")
    manifest.update(release_id=destination.name, created_at=now, publication_status="inactive_audit",
                    deck_content_id=file_content_id(destination / "deck.json"),
                    composition_content_id=file_content_id(destination / "composition.json"))
    manifest["app_contract"]["index_content_id"] = file_content_id(destination / "app/vocabulary.index.json")
    write(destination / "manifest.json", manifest)
    # Byte-identical examples include every positional meaning reference. The
    # table and grammar labels are carried, not rebuilt or guessed.
    for relative in ("app/vocabulary.examples.json", "app/study-structure.json", "app/conjugations.json"):
        assert file_content_id(source / relative) == file_content_id(destination / relative)
    print("Validating complete successor release", flush=True)
    validate_release_bundle(destination)
    print(f"Validated: {destination}", flush=True)


if __name__ == "__main__":
    main()
