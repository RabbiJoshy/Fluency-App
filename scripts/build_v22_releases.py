#!/usr/bin/env python3
"""Build and activate v22 Speech releases (pt, es, cs) reflecting the latest WSD & verbal MWE methodology.

Carries stages 01-03 from the v21 x30 runs, splices stage 04 with deterministic invariant
verbal MWEs from the 10k sieve snapshots, builds inactive run candidates, shards them with slim shards,
validates each bundle, and updates active.json and app/config/config.json.
"""

from __future__ import annotations

import argparse
import functools
import json
import os
from pathlib import Path
import shutil
import sys

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))

from fluency.core.workspace import Workspace
from fluency.release.example_shards import shard_app_examples
from fluency.release.index_shards import shard_app_index
from fluency.release.run_candidate import build_inactive_run_candidate
from fluency.release.validation import validate_release_bundle
from fluency.wsd.multiword import index_multiword_senses, multiword_analyses

shard_app_examples_slim = functools.partial(shard_app_examples, slim=True)
shard_app_index_slim = functools.partial(shard_app_index, slim=True)

CONFIGS = {
    "pt": {
        "source_run": "20261002T070314Z-a46fd4ad",
        "prewsd": "raw/surfaces/pt/prewsd/20260914T222723Z-e43a0469-v2/examples.json",
        "mwe_sieve": "raw/mwe/mwe-pt-10k-sieve/mwe_merged.json",
        "run_id": "20261003T160000Z-v22-pt",
        "release_id": "pt-speech-v22-10000x30-slim",
    },
    "es": {
        "source_run": "20260930T193248Z-ec3c710b",
        "prewsd": "raw/surfaces/es/prewsd/20260914T223348Z-c35194bc-v2/examples.json",
        "mwe_sieve": "raw/mwe/mwe-es-10k-sieve/mwe_merged.json",
        "run_id": "20261003T160000Z-v22-es",
        "release_id": "es-speech-v22-10000x30-slim",
    },
    "cs": {
        "source_run": "20260930T193251Z-2f3f53c3",
        "prewsd": "raw/surfaces/cs/prewsd/20260914T223828Z-ad405a28/examples.json",
        "mwe_sieve": "raw/mwe/mwe-cs-10k-sieve/mwe_merged.json",
        "run_id": "20261003T160000Z-v22-cs",
        "release_id": "cs-speech-v22-10000x30-slim",
    },
}


def splice_invariant_mwe(row: dict, text: str, mwe_index) -> str | None:
    """Turn ``row`` into a deterministic invariant-MWE assignment when one matches.

    Returns the expression spliced in, or None when the row is left alone.
    """
    surf = row.get("surface_form", "")
    card_id = row.get("card_id", "")
    if not (text and surf):
        return None
    matches = list(multiword_analyses(card_id=card_id, surface_form=surf, sentence=text, index=mwe_index))
    inv_matches = [
        m for m in matches
        if getattr(m[1], "wsd_routing", "") == "deterministic_bypass"
        or getattr(m[1], "route", "") == "invariant"
    ]
    if inv_matches:
        best_inv = max(inv_matches, key=lambda m: len(m[1].expression))
        analysis, entry, span = best_inv

        row["status"] = "assigned"
        row["decision_kind"] = "deterministic_default"
        row["decision_path"] = ["multiword"]
        row["menu_analysis_id"] = analysis.menu_analysis_id
        row["selected_sense_id"] = entry.entry_id
        row["selected_tuple"] = {"headword": entry.expression, "part_of_speech": "PHRASE"}
        row["emitted_level"] = "leaf"

        ev = row.setdefault("evidence", {})
        ev["reason"] = "deterministic_invariant_mwe"
        ev["decision_kind"] = "deterministic_invariant_mwe"
        ev["selected_multiword"] = entry.expression
        ev["wsd_routing"] = "deterministic_bypass"
        ev["flexibility"] = entry.flexibility
        ev["ui_role"] = entry.ui_role
        ev["verbal_idiom"] = entry.verbal_idiom
        ev["transparency"] = entry.transparency
        ev["template_gap_limit"] = entry.template_gap_limit
        ev["multiword_candidates"] = [
            {
                "expression": entry.expression,
                "expression_id": entry.entry_id,
                "menu_analysis_id": analysis.menu_analysis_id,
                "span": list(span),
                "sources": list(entry.sources),
                "corpus_frequency": entry.corpus_frequency,
                "translation": entry.translations[0],
                "additional_translations": list(entry.translations[1:]),
                "route": "invariant",
                "wsd_routing": "deterministic_bypass",
                "flexibility": entry.flexibility,
                "ui_role": entry.ui_role,
                "verbal_idiom": entry.verbal_idiom,
                "transparency": entry.transparency,
                "template_gap_limit": entry.template_gap_limit,
            }
        ]

        sp = row.setdefault("selection_projections", {})
        sp["mwe_augmented"] = {
            "emitted_level": "leaf",
            "menu_analysis_id": analysis.menu_analysis_id,
            "rank": 1,
            "raw_axis_margins": {"glosskey": 1.0, "leaf": 1.0, "tuple": 1.0},
            "raw_margin": None,
            "runner_up_score": None,
            "selected_score": 1.0,
            "selected_sense_id": entry.entry_id,
            "selected_tuple": {"headword": entry.expression, "part_of_speech": "PHRASE"},
            "source_kind": "multiword",
        }

        return entry.expression
    return None


def build_release_for_lang(ws: Workspace, lang: str) -> Path:
    cfg = CONFIGS[lang]
    source_run = ws.root / f"runs/{lang}/speech/{cfg['source_run']}"
    new_run = ws.root / f"runs/{lang}/speech/{cfg['run_id']}"
    release_id = cfg["release_id"]

    print(f"\n==================== Building v22 Release for {lang.upper()} ====================")
    print(f"Source run: {source_run.name} -> New run: {new_run.name}")

    # 1. Setup new run directory
    if new_run.exists():
        shutil.rmtree(new_run)
    new_run.mkdir(parents=True)

    for f in ["manifest.json", "plan.json", "profile.json"]:
        if (source_run / f).exists():
            shutil.copy2(source_run / f, new_run / f)

    profile = json.loads((new_run / "profile.json").read_text(encoding="utf-8"))
    profile["profile_id"] = f"{lang}-speech-v22-10000x30"
    (new_run / "profile.json").write_text(json.dumps(profile, indent=2), encoding="utf-8")

    man = json.loads((new_run / "manifest.json").read_text(encoding="utf-8"))
    man["run_id"] = cfg["run_id"]
    (new_run / "manifest.json").write_text(json.dumps(man, indent=2), encoding="utf-8")

    # Carry stages 01-03
    (new_run / "stages").mkdir()
    for s in ["01_inventory", "02_sense_menu", "03_sentence_harvest"]:
        shutil.copytree(source_run / "stages" / s, new_run / "stages" / s)

    # Setup stage 04
    src4 = source_run / "stages/04_wsd_assignments"
    dst4 = new_run / "stages/04_wsd_assignments"
    dst4.mkdir()
    shutil.copytree(src4 / "output", dst4 / "output")
    if (src4 / "contract.json").exists():
        shutil.copy2(src4 / "contract.json", dst4 / "contract.json")

    # Setup stage 05 with empty output
    dst5 = new_run / "stages/05_example_selection"
    dst5.mkdir()
    shutil.copy2(source_run / "stages/05_example_selection/contract.json", dst5 / "contract.json")

    # 2. Splice stage 04 assignments with invariant MWEs
    print("Loading PreWSD sentences...")
    pw_path = ws.root / cfg["prewsd"]
    pw_data = json.loads(pw_path.read_text(encoding="utf-8"))
    targets = pw_data["columns"]["target"]
    sids = pw_data["columns"]["sentence_id"]
    sid_to_target = dict(zip(sids, targets))

    print(f"Loading MWE sieve from {cfg['mwe_sieve']}...")
    mwe_data = json.loads((ws.root / cfg["mwe_sieve"]).read_text(encoding="utf-8"))
    mwe_index = index_multiword_senses(mwe_data)

    print("Splicing stage 04 assignments...")
    assign_path = dst4 / "output/assignments.jsonl"
    temp_assign = dst4 / "output/assignments.temp.jsonl"

    mwe_updates: dict[str, int] = {}
    total_rows = 0
    updated_rows = 0

    with open(assign_path, encoding="utf-8") as fin, open(temp_assign, "w", encoding="utf-8") as fout:
        for line in fin:
            total_rows += 1
            row = json.loads(line)
            sid = row.get("sentence_id", "").replace("sentence_", "")
            text = sid_to_target.get(sid)

            spliced = splice_invariant_mwe(row, text, mwe_index)
            if spliced:
                updated_rows += 1
                mwe_updates[spliced] = mwe_updates.get(spliced, 0) + 1

            fout.write(json.dumps(row, ensure_ascii=False) + "\n")

    os.replace(temp_assign, assign_path)
    print(f"Splice complete: {total_rows:,} rows scanned, {updated_rows:,} updated to invariant MWEs.")
    print(f"Top MWEs updated for {lang}:")
    for k, v in sorted(mwe_updates.items(), key=lambda x: -x[1])[:10]:
        print(f"  {k}: {v}")

    # 3. Build inactive run candidate
    cand_dir = ws.root / f"releases/{lang}/speech/{release_id}"
    if cand_dir.exists():
        shutil.rmtree(cand_dir)

    print(f"Building candidate release {release_id}...")
    out = build_inactive_run_candidate(
        ws,
        run_id=cfg["run_id"],
        release_id=release_id,
        language=lang,
        mode="speech",
        wsd_selection_projection="mwe_augmented",
        wsd_publication_projection="forced_leaf",
    )

    print("Validating bundle...")
    validate_release_bundle(out)

    print("Sharding app index and examples (slim)...")
    shard_app_index_slim(out / "app")
    shard_app_examples_slim(out / "app")

    # 4. Activate release in workspace
    active_path = ws.root / f"releases/{lang}/speech/active.json"
    active_data = {
        "language": lang,
        "manifest_path": f"{release_id}/manifest.json",
        "manifest_version": "active-release/v1",
        "mode": "speech",
        "release_id": release_id,
    }
    active_path.write_text(json.dumps(active_data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Activated {release_id} in {active_path.name}")

    return out


def update_app_config(release_ids: dict[str, str]) -> None:
    config_file = REPO / "app/config/config.json"
    cfg = json.loads(config_file.read_text(encoding="utf-8"))

    lang_keys = {
        "es": "spanish",
        "pt": "portuguese",
        "cs": "czech",
    }

    for lang, rel_id in release_ids.items():
        k = lang_keys.get(lang)
        if not k or k not in cfg.get("languages", {}):
            continue
        entry = cfg["languages"][k]
        entry["indexPath"] = f"releases/{lang}/speech/{rel_id}/app/vocabulary.index.json"
        entry["examplesPath"] = f"releases/{lang}/speech/{rel_id}/app/vocabulary.examples.json"
        entry["studyStructurePath"] = f"releases/{lang}/speech/{rel_id}/app/study-structure.json"
        entry["releaseManifestPath"] = f"releases/{lang}/speech/{rel_id}/manifest.json"
        entry["releaseCompositionPath"] = f"releases/{lang}/speech/{rel_id}/composition.json"
        print(f"Updated app/config/config.json for {k} -> {rel_id}")

    config_file.write_text(json.dumps(cfg, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--languages", nargs="+", choices=["pt", "es", "cs"], default=["pt", "es", "cs"])
    args = ap.parse_args()

    ws = Workspace.load(REPO.parent / "Fluency-Workspace")
    built_releases = {}

    for lang in args.languages:
        out = build_release_for_lang(ws, lang)
        built_releases[lang] = CONFIGS[lang]["release_id"]
        print(f"SUCCESS: {built_releases[lang]} is built, validated, sharded, and activated.")

    update_app_config(built_releases)
    print("\nALL RELEASES SUCCESSFULLY BUILT AND CONFIGURED.")


if __name__ == "__main__":
    main()
