#!/usr/bin/env python3
"""Build Portuguese revision 3 candidate release incorporating pt-v24-1 WSD on és.

Carries all verified stages and assignments from pt-speech-v24-headway-r2-10000x30,
splices the fresh pt-v24-1 WSD assignments for és, and builds an inactive candidate release:
pt-speech-v24-headway-r3-10000x30-slim.
"""
from __future__ import annotations
import gc
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / 'src'))

from fluency.core.hashing import file_content_id
from fluency.core.workspace import Workspace
from fluency.enrichments.conjugations import build_conjugation_layer
from fluency.pipeline.planning import create_pipeline_plan
from fluency.release.example_shards import shard_app_examples
from fluency.release.index_shards import shard_app_index
from fluency.release.run_candidate import build_inactive_run_candidate
from fluency.release.validation import validate_release_bundle
from fluency.wsd.importer import import_wsd_assignments
from fluency.wsd.splice import carried_row, write_spliced_bundle


def read(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def write(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=1) + '\n', encoding="utf-8")


def carry_stage(source: Path, run: Path, stage: str) -> None:
    src = source / 'stages' / stage / 'output'
    dst = run / 'stages' / stage / 'output'
    if dst.exists():
        shutil.rmtree(dst)
    shutil.copytree(src, dst)
    manifest = read(dst / 'manifest.json')
    manifest['reused_from'] = str(src)
    write(dst / 'manifest.json', manifest)
    contract_path = run / 'stages' / stage / 'contract.json'
    contract = read(contract_path)
    contract.update(
        status='complete',
        output_directory='output',
        completed_at=manifest.get('completed_at'),
        manifest_content_id=file_content_id(dst / 'manifest.json'),
        carried_note='Carried from ' + source.name,
    )
    write(contract_path, contract)


def main():
    gc.disable()
    ws_root = Path('/Users/joshuathomasamar/PycharmProjects/Fluency-Workspace')
    ws = Workspace.load(ws_root)
    source_run_id = '20261010T161908Z-63f07fe8'
    source = ws.root / 'runs/pt/speech' / source_run_id
    
    release_id = 'pt-speech-v24-headway-r3-10000x30-slim'
    print(f"Creating pipeline plan for release: {release_id}...")

    # 1. Profile and Pipeline Plan
    profile = read(source / 'profile.json')
    profile['profile_id'] = 'pt-speech-v24-headway-r3-10000x30'
    profile['wsd']['model_profile'] = 'pt-v24-1'
    profile['wsd']['model_revisions']['occurrence_pos.model_revision'] = 'stanza-pt-default@1.14.0'
    
    # Clean up any partial run folder from previous attempt if it exists
    old_partial = ws.root / 'runs/pt/speech/20261011T103350Z-v24-pt-r3'
    if old_partial.exists():
        shutil.rmtree(old_partial)

    new_run = create_pipeline_plan(ws, profile)
    print(f"Initialized run {new_run.name} at {new_run}")

    # 2. Carry stages 01, 02, 03
    print("Carrying stages 01, 02, 03...")
    carry_stage(source, new_run, '01_inventory')
    carry_stage(source, new_run, '02_sense_menu')
    carry_stage(source, new_run, '03_sentence_harvest')

    # 3. Stage 04: Splice fresh és assignments with carried assignments
    print("Splicing WSD assignments (carrying 9,999 cards, fresh pt-v24-1 WSD for 'és')...")
    fresh_path = Path('/Users/joshuathomasamar/.gemini/antigravity/brain/ebf72b87-a305-4bf1-9380-3888894cbbf7/scratch/wsd_pt_v24_test')
    fresh_bundle = read(fresh_path)
    
    src4 = source / 'stages/04_wsd_assignments/output'
    source_method = read(src4 / 'method.json')['method']
    source_report = read(src4 / 'report.json')
    menu_id = file_content_id(new_run / 'stages/02_sense_menu/output/sense-menu.json')

    # Find the card_id for és
    es_card_id = None
    menu_cards = read(new_run / 'stages/02_sense_menu/output/sense-menu.json')['cards']
    for card in menu_cards:
        if card['surface_form'] == 'és':
            es_card_id = card['card_id']
            break
    if not es_card_id:
        raise ValueError("Could not find card_id for 'és'")
    print(f"Target 'és' card_id: {es_card_id}")

    def carried_generator():
        with (src4 / 'assignments.jsonl').open() as f:
            for line in f:
                row = json.loads(line)
                if row['card_id'] != es_card_id:
                    yield carried_row(
                        row,
                        source_run_id=source.name,
                        source_method=source_method,
                        sense_menu_content_id=menu_id,
                    )

    spliced_bundle_path = ws.root / 'raw/wsd/pt' / f'headway-{new_run.name}-spliced.json'
    spliced_inputs = dict(fresh_bundle['inputs'])
    mwe_inventory_path = ws.root / 'raw/mwe/mwe-pt-10k-sieve/mwe_merged.json'
    spliced_inputs['multiword_inventory'] = file_content_id(mwe_inventory_path)
    splice_report = write_spliced_bundle(
        spliced_bundle_path,
        run_id=new_run.name,
        language='pt',
        mode='speech',
        inputs=spliced_inputs,
        method=fresh_bundle['method'],
        sampling_policy=(source_report.get('occurrence_sampling') or {}).get('policy') or {},
        carried=carried_generator(),
        fresh=fresh_bundle['assignments'],
        declared=(),
        progress=lambda s: print(s, flush=True),
    )
    print(f"Splice report: {splice_report['rows_by_origin']}")

    print("Importing complete assignment bundle into stage 04...")
    import_wsd_assignments(
        ws,
        run_id=new_run.name,
        language='pt',
        mode='speech',
        bundle_path=spliced_bundle_path,
        streaming=True,
    )
    print("Stage 04 imported successfully.")

    # 4. Build Release Candidate
    print(f"Building candidate release {release_id}...")
    output = ws.root / 'releases/pt/speech' / release_id
    if output.exists():
        print(f"Removing old candidate {output}...")
        shutil.rmtree(output)

    snapshot = 'enwiktionary-2026-08-20'
    metadata, layer_report = build_conjugation_layer(
        ws,
        sense_menu=new_run / 'stages/02_sense_menu/output/sense-menu.json',
        source_snapshot=ws.root / 'raw/conjugations/pt/kaikki' / snapshot,
    )
    write(ws.root / 'raw/surfaces/headway/pt-r3-conjugation-report.json', layer_report)

    output = build_inactive_run_candidate(
        ws,
        run_id=new_run.name,
        release_id=release_id,
        language='pt',
        mode='speech',
        conjugations_artifact_id=metadata.artifact_id,
        wsd_selection_projection='mwe_augmented',
        wsd_publication_projection='forced_leaf',
        memory_bounded=True,
    )
    print(f"Validating release bundle {output}...")
    validate_release_bundle(output)

    print("Building merge exceptions...")
    command = [
        sys.executable, str(REPO / 'scripts/build_merge_exceptions.py'),
        '--language', 'pt',
        '--release-index', str(output / 'app/vocabulary.index.json'),
        '--sense-menu', str(new_run / 'stages/02_sense_menu/output/sense-menu.json'),
        '--out', str(output / 'app/merge-exceptions.json'),
        '--extract', str(ws.root / 'raw/wiktionary' / snapshot / 'kaikki.org-dictionary-Portuguese.jsonl'),
    ]
    subprocess.run(command, check=True, env={**os.environ, 'PYTHONPATH': str(REPO / 'src')})

    print("Sharding app index and examples...")
    shard_app_index(output / 'app', slim=True)
    shard_app_examples(output / 'app', slim=True)
    print(f"Candidate release built, validated, and sharded at {output}!")


if __name__ == '__main__':
    main()
