#!/usr/bin/env python3
"""Build Spanish revision 5 candidate release with es-v24-1 WSD.

Carries verified stages 01, 02, 03 from es-speech-v24-headway-r4-10000x30,
runs fresh es-v24-1 WSD with soft evidence gating, semantic margin scoring,
and single-POS menu bypass on the 174 corrected HEADWAY cards, splices with
carried assignments, and builds an inactive candidate release:
es-speech-v24-headway-r5-10000x30-slim.
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
    ws = Workspace.load(Path('/Users/joshuathomasamar/PycharmProjects/Fluency-Workspace'))
    source = ws.root / 'runs/es/speech/20261010T153100Z-7f63c198'
    release_id = 'es-speech-v24-headway-r5-10000x30-slim'
    print(f"Creating pipeline plan for release: {release_id}...")

    # 1. Profile and Pipeline Plan
    profile = read(source / 'profile.json')
    profile['profile_id'] = 'es-speech-v24-headway-r5-10000x30'
    profile['wsd']['model_profile'] = 'es-v24-1'
    profile['wsd']['model_revisions']['occurrence_pos.model_revision'] = 'es_dep_news_trf@3.8.0'

    new_run = create_pipeline_plan(ws, profile)
    print(f"Initialized run {new_run.name} at {new_run}")

    # 2. Carry stages 01, 02, 03
    print("Carrying stages 01, 02, 03...")
    carry_stage(source, new_run, '01_inventory')
    carry_stage(source, new_run, '02_sense_menu')
    carry_stage(source, new_run, '03_sentence_harvest')

    # 3. Stage 04: Run fresh es-v24-1 WSD on the 174 corrected HEADWAY cards
    print("Running fresh es-v24-1 WSD on 174 HEADWAY cards...")
    state = read(ws.root / 'raw/surfaces/headway/es-r4-rollout-state.json')
    targets = state['targets']
    freeze = state['freeze']
    tags = ws.root / f'raw/reflexive/es/tags-{source.name}.json'
    mwe = ws.root / 'raw/mwe/mwe-es-10k-sieve/mwe_merged.json'
    cache = ws.root / 'embeddings/es/exact-text-gemini-embedding-001.npz'
    fresh_bundle_path = ws.root / 'raw/surfaces/headway' / f'es-r5-fresh-wsd-{new_run.name}.json'

    cmd = [
        sys.executable, '-m', 'fluency.speech.wsd_execute',
        '--run-dir', str(new_run),
        '--out', str(fresh_bundle_path),
        '--profile-id', 'es-v24-1',
        '--prewsd', str(freeze),
        '--reflexive-tags', str(tags),
        '--embedding-cache', str(cache),
        '--multiword-inventory', str(mwe),
        '--offline-only',
        '--skip-single-pos-menus',
        '--target-surfaces', *targets
    ]
    env = {**os.environ, 'PYTHONPATH': str(REPO / 'src')}
    t0 = time.time()
    subprocess.run(cmd, check=True, env=env, cwd=REPO)
    print(f"Fresh WSD execution finished in {time.time() - t0:.1f}s.")

    # 4. Splice fresh assignments with carried assignments from r4
    print("Splicing fresh assignments with carried r4 assignments...")
    fresh_bundle = read(fresh_bundle_path)
    src4 = source / 'stages/04_wsd_assignments/output'
    source_method = read(src4 / 'method.json')['method']
    source_report = read(src4 / 'report.json')
    menu_id = file_content_id(new_run / 'stages/02_sense_menu/output/sense-menu.json')
    changed_card_ids = {a['card_id'] for a in fresh_bundle['assignments']}
    print(f"Target changed cards count: {len(changed_card_ids)}")

    def carried_generator():
        with (src4 / 'assignments.jsonl').open() as f:
            for line in f:
                row = json.loads(line)
                if row['card_id'] not in changed_card_ids:
                    yield carried_row(
                        row,
                        source_run_id=source.name,
                        source_method=source_method,
                        sense_menu_content_id=menu_id,
                    )

    spliced_bundle_path = ws.root / 'raw/wsd/es' / f'headway-{new_run.name}-spliced.json'
    spliced_inputs = dict(fresh_bundle['inputs'])
    spliced_inputs['multiword_inventory'] = file_content_id(mwe)
    splice_report = write_spliced_bundle(
        spliced_bundle_path,
        run_id=new_run.name,
        language='es',
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
        language='es',
        mode='speech',
        bundle_path=spliced_bundle_path,
        streaming=True,
    )
    print("Stage 04 imported successfully.")

    # 5. Build Release Candidate
    print(f"Building candidate release {release_id}...")
    output = ws.root / 'releases/es/speech' / release_id
    if output.exists():
        print(f"Removing old candidate {output}...")
        shutil.rmtree(output)

    snapshot = 'enwiktionary-2026-09-13'
    metadata, layer_report = build_conjugation_layer(
        ws,
        sense_menu=new_run / 'stages/02_sense_menu/output/sense-menu.json',
        source_snapshot=ws.root / 'raw/conjugations/es/kaikki' / snapshot,
    )
    write(ws.root / 'raw/surfaces/headway/es-r5-conjugation-report.json', layer_report)

    output = build_inactive_run_candidate(
        ws,
        run_id=new_run.name,
        release_id=release_id,
        language='es',
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
        '--language', 'es',
        '--release-index', str(output / 'app/vocabulary.index.json'),
        '--sense-menu', str(new_run / 'stages/02_sense_menu/output/sense-menu.json'),
        '--out', str(output / 'app/merge-exceptions.json'),
    ]
    subprocess.run(command, check=True, env={**os.environ, 'PYTHONPATH': str(REPO / 'src')})

    print("Sharding app index and examples...")
    shard_app_index(output / 'app', slim=True)
    shard_app_examples(output / 'app', slim=True)
    print(f"Candidate release built, validated, and sharded at {output}!")


if __name__ == '__main__':
    main()
