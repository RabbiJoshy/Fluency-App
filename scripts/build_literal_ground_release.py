#!/usr/bin/env python3
"""LITERAL-GROUND: rebuild only the closed-class preposition cards of a speech deck.

Carries stages 01-03 and every other card's Stage 04 rows from the current
candidate run (pt r3, es r5), runs <lang>-v25-1 WSD offline from the exact-text
cache on the preposition cards only, splices, and builds an inactive candidate
(pt r4, es r6). $0: --offline-only, and an occurrence whose multiword gloss has
no cached vector is not scored -- its previous row is carried instead.

    PYTHONPATH=src python scripts/build_literal_ground_release.py --language pt
"""
from __future__ import annotations

import argparse
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
from fluency.wsd.ground import load_ground_policy
from fluency.wsd.importer import import_wsd_assignments
from fluency.wsd.splice import carried_row, write_spliced_bundle

WORKSPACE = Path('/Users/joshuathomasamar/PycharmProjects/Fluency-Workspace')

PLANS = {
    'pt': {
        'source_run': '20261011T103622Z-4b660be3',
        'source_release': 'pt-speech-v24-headway-r3-10000x30-slim',
        'release_id': 'pt-speech-v25-literal-ground-r4-10000x30-slim',
        'profile_id': 'pt-speech-v25-literal-ground-r4-10000x30',
        'model_profile': 'pt-v25-1',
        'freeze': 'raw/surfaces/pt/prewsd/20260914T222723Z-e43a0469-v2',
        'reflexive_tags': 'raw/reflexive/pt/tags-20261010T161908Z-63f07fe8.json',
        'mwe': 'raw/mwe/mwe-pt-10k-sieve/mwe_merged.json',
        'snapshot': 'enwiktionary-2026-08-20',
        'extract': 'raw/wiktionary/enwiktionary-2026-08-20/kaikki.org-dictionary-Portuguese.jsonl',
    },
    'es': {
        'source_run': '20261011T121508Z-7b5b343c',
        'source_release': 'es-speech-v24-headway-r5-10000x30-slim',
        'release_id': 'es-speech-v25-literal-ground-r6-10000x30-slim',
        'profile_id': 'es-speech-v25-literal-ground-r6-10000x30',
        'model_profile': 'es-v25-1',
        'freeze': 'raw/surfaces/es/prewsd/20260914T223348Z-c35194bc-v2',
        'reflexive_tags': 'raw/reflexive/es/tags-20261010T153100Z-7f63c198.json',
        'mwe': 'raw/mwe/mwe-es-10k-sieve/mwe_merged.json',
        'snapshot': 'enwiktionary-2026-09-13',
        'extract': None,
    },
}


def read(path: Path) -> dict:
    return json.loads(path.read_text(encoding='utf-8'))


def write(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=1) + '\n', encoding='utf-8')


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


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--language', choices=sorted(PLANS), required=True)
    args = parser.parse_args()
    plan = PLANS[args.language]
    lang = args.language
    gc.disable()
    ws = Workspace.load(WORKSPACE)
    source = ws.root / 'runs' / lang / 'speech' / plan['source_run']
    out_dir = ws.root / 'raw/surfaces/literal-ground'

    policy_path = REPO / 'config/wsd/closed-class' / f'{lang}.json'
    policy = load_ground_policy(policy_path, content_id=file_content_id(policy_path))
    targets = sorted(policy.surfaces)

    profile = read(source / 'profile.json')
    profile['profile_id'] = plan['profile_id']
    profile['wsd']['model_profile'] = plan['model_profile']
    new_run = create_pipeline_plan(ws, profile)
    print(f"run {new_run.name}; targets {targets}")

    for stage in ('01_inventory', '02_sense_menu', '03_sentence_harvest'):
        carry_stage(source, new_run, stage)

    fresh_path = out_dir / f'{lang}-fresh-wsd-{new_run.name}.json'
    command = [
        sys.executable, '-m', 'fluency.speech.wsd_execute',
        '--run-dir', str(new_run),
        '--out', str(fresh_path),
        '--profile-id', plan['model_profile'],
        '--prewsd', str(ws.root / plan['freeze']),
        '--reflexive-tags', str(ws.root / plan['reflexive_tags']),
        '--embedding-cache', str(ws.root / 'embeddings' / lang / 'exact-text-gemini-embedding-001.npz'),
        '--multiword-inventory', str(ws.root / plan['mwe']),
        '--offline-only', '--offline-skip-missing',
        '--skip-single-pos-menus',
        '--target-surfaces', *targets,
    ]
    started = time.time()
    subprocess.run(command, check=True, env={**os.environ, 'PYTHONPATH': str(REPO / 'src')}, cwd=REPO)
    print(f"fresh WSD in {time.time() - started:.0f}s")

    fresh = read(fresh_path)
    unscored = {(row['card_id'], row['sentence_id']) for row in fresh.get('offline_unscored', ())}
    fresh_rows = [
        row for row in fresh['assignments']
        if (row['card_id'], row['sentence_id']) not in unscored
    ]
    fresh_cards = {row['card_id'] for row in fresh_rows}
    src4 = source / 'stages/04_wsd_assignments/output'
    source_method = read(src4 / 'method.json')['method']
    source_report = read(src4 / 'report.json')
    menu_id = file_content_id(new_run / 'stages/02_sense_menu/output/sense-menu.json')

    def carried():
        with (src4 / 'assignments.jsonl').open() as handle:
            for line in handle:
                row = json.loads(line)
                key = (row['card_id'], row['sentence_id'])
                # A whole non-target card, or one occurrence of a target card
                # that could not be scored offline: carry the previous decision.
                if row['card_id'] not in fresh_cards or key in unscored:
                    yield carried_row(
                        row,
                        source_run_id=source.name,
                        source_method=source_method,
                        sense_menu_content_id=menu_id,
                    )

    spliced_path = ws.root / 'raw/wsd' / lang / f'literal-ground-{new_run.name}-spliced.json'
    inputs = dict(fresh['inputs'])
    inputs['multiword_inventory'] = file_content_id(ws.root / plan['mwe'])
    report = write_spliced_bundle(
        spliced_path,
        run_id=new_run.name,
        language=lang,
        mode='speech',
        inputs=inputs,
        method=fresh['method'],
        sampling_policy=(source_report.get('occurrence_sampling') or {}).get('policy') or {},
        carried=carried(),
        fresh=fresh_rows,
        declared=(),
        progress=lambda message: print(message, flush=True),
    )
    report['offline_unscored_carried'] = sorted(f'{c}/{s}' for c, s in unscored)
    report['fresh_cards'] = len(fresh_cards)
    write(out_dir / f'{lang}-splice-report-{new_run.name}.json', report)
    print(f"splice: {report['rows_by_origin']}; {len(unscored)} unscored occurrences carried")

    import_wsd_assignments(
        ws, run_id=new_run.name, language=lang, mode='speech',
        bundle_path=spliced_path, streaming=True,
    )

    output = ws.root / 'releases' / lang / 'speech' / plan['release_id']
    if output.exists():
        shutil.rmtree(output)
    metadata, layer_report = build_conjugation_layer(
        ws,
        sense_menu=new_run / 'stages/02_sense_menu/output/sense-menu.json',
        source_snapshot=ws.root / 'raw/conjugations' / lang / 'kaikki' / plan['snapshot'],
    )
    write(out_dir / f'{lang}-conjugation-report-{new_run.name}.json', layer_report)
    output = build_inactive_run_candidate(
        ws,
        run_id=new_run.name,
        release_id=plan['release_id'],
        language=lang,
        mode='speech',
        conjugations_artifact_id=metadata.artifact_id,
        wsd_selection_projection='mwe_augmented',
        wsd_publication_projection='forced_leaf',
        memory_bounded=True,
    )
    validate_release_bundle(output)

    merge = [
        sys.executable, str(REPO / 'scripts/build_merge_exceptions.py'),
        '--language', lang,
        '--release-index', str(output / 'app/vocabulary.index.json'),
        '--sense-menu', str(new_run / 'stages/02_sense_menu/output/sense-menu.json'),
        '--out', str(output / 'app/merge-exceptions.json'),
    ]
    if plan['extract']:
        merge += ['--extract', str(ws.root / plan['extract'])]
    subprocess.run(merge, check=True, env={**os.environ, 'PYTHONPATH': str(REPO / 'src')})
    shard_app_index(output / 'app', slim=True)
    shard_app_examples(output / 'app', slim=True)
    print(f"built {output}")


if __name__ == '__main__':
    main()
