#!/usr/bin/env python3
"""Targeted HEADWAY rollout from pinned v23 inputs; never activates or promotes.

Use existing pools/frozen sentences, rebuild corrected menus, re-score every
changed card offline, and carry unchanged assignments with explicit provenance.
Each step is resumable; old stages and releases are immutable.
"""
from __future__ import annotations
import argparse
import gc
from collections import Counter
from copy import deepcopy
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / 'src'))
from fluency.core.hashing import file_content_id
from fluency.core.workspace import Workspace
from fluency.surfaces.ledger import ledger_path
from fluency.surfaces.lemma_revision import stale_carried_analyses

SOURCES = {'es': '20261004T160042Z-fe49e477', 'pt': '20261004T160042Z-b4bc9acd'}
FREEZES = {'es': '20260914T223348Z-c35194bc-v2', 'pt': '20260914T222723Z-e43a0469-v2'}

def read(path):
    return json.loads(path.read_text())

def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=1) + '\n')

def carry(source, run, stage):
    src, dst = source / 'stages' / stage / 'output', run / 'stages' / stage / 'output'
    shutil.copytree(src, dst)
    manifest = read(dst / 'manifest.json')
    manifest['reused_from'] = str(src)
    write(dst / 'manifest.json', manifest)
    contract = read(run / 'stages' / stage / 'contract.json')
    contract.update(status='complete', output_directory='output',
                    completed_at=manifest.get('completed_at'),
                    manifest_content_id=file_content_id(dst / 'manifest.json'),
                    carried_note='HEADWAY: unchanged inventory and existing named-pool sentences; no harvest')
    write(run / 'stages' / stage / 'contract.json', contract)

def prepare(ws, lang, state_path, revision):
    from fluency.pipeline.planning import create_pipeline_plan
    from fluency.sense_menu.runner import build_sense_menu_stage
    if state_path.exists():
        state = read(state_path)
        print(f'{lang}: existing candidate run {state["run_id"]}', flush=True)
        return
    source = ws.root / 'runs' / lang / 'speech' / SOURCES[lang]
    ledger = read(ledger_path(ws.root, lang))['surfaces']
    old_menu = read(source / 'stages/02_sense_menu/output/sense-menu.json')
    targets = sorted(c['surface_form'] for c in old_menu['cards']
                     if stale_carried_analyses(c, ledger.get(c['surface_form'], {})))
    if not targets:
        raise ValueError('no superseded cards found')
    profile = read(source / 'profile.json')
    suffix = '' if revision == 1 else f'-r{revision}'
    profile['profile_id'] = f'{lang}-speech-v24-headway{suffix}-10000x30'
    profile['sense_menu']['resolver'] = {'surfaces': targets, 'carry_from_run': source.name}
    profile['scope']['note'] = 'HEADWAY: existing 10k inventory/pools; targeted source corrections and WSD only'
    freeze = ws.root / 'raw/surfaces' / lang / 'prewsd' / FREEZES[lang]
    pool = ws.root / 'pools' / lang / f'{lang}-10k-speech' / 'pool.json'
    inputs = [ledger_path(ws.root, lang), pool, source / 'profile.json',
              source / 'stages/02_sense_menu/output/sense-menu.json',
              source / 'stages/04_wsd_assignments/output/assignments.jsonl',
              *[freeze / x['path'] for x in read(freeze / 'manifest.json')['documents']]]
    profile['headway'] = {'source_run_id': source.name, 'named_pool': read(pool)['pool_id'],
                         'prewsd': str(freeze), 'inputs': {str(p): file_content_id(p) for p in inputs}}
    profile_path = REPO / 'config/pipelines' / lang / 'speech' / f'{profile["profile_id"]}.json'
    if profile_path.exists() and read(profile_path) != profile:
        raise ValueError('versioned profile already differs; create a new version')
    write(profile_path, profile)
    run = create_pipeline_plan(ws, profile)
    carry(source, run, '01_inventory')
    carry(source, run, '03_sentence_harvest')
    state = {'language': lang, 'source_run': source.name, 'run_id': run.name,
             'targets': targets, 'freeze': str(freeze), 'inputs': profile['headway']['inputs'],
             'release_id': f'{lang}-speech-v24-headway{suffix}-10000x30-slim',
             'prefix': lang + suffix}
    # Record first: a failed menu build is recoverable without creating another run.
    write(state_path, state)
    menus(ws, state)

def menus(ws, state):
    from fluency.sense_menu.runner import build_sense_menu_stage
    lang = state['language']
    run = ws.root / 'runs' / lang / 'speech' / state['run_id']
    menu_path = run / 'stages/02_sense_menu/output/sense-menu.json'
    if not menu_path.exists():
        snapshot_id = read(run / 'profile.json')['sense_menu']['snapshot_id']
        snapshot = (ws.root / 'raw/dictionaries/es/spanishdict' / snapshot_id if lang == 'es' else
                    ws.root / 'raw/wiktionary' / snapshot_id / 'kaikki.org-dictionary-Portuguese.jsonl')
        build_sense_menu_stage(REPO, ws, run_id=run.name, language=lang, mode='speech',
                              dictionary_snapshot=snapshot, snapshot_id=snapshot_id)
    old = {c['card_id']: c for c in read(ws.root / 'runs' / lang / 'speech' / state['source_run'] /
                                       'stages/02_sense_menu/output/sense-menu.json')['cards']}
    new = read(menu_path)['cards']
    changes = []
    for c in new:
        b = old[c['card_id']]
        if c == b:
            continue
        if c['surface_form'] not in state['targets']:
            raise AssertionError(f'untargeted card changed: {c["surface_form"]}')
        changes.append({'surface': c['surface_form'], 'card_id': c['card_id'],
                        'before': b, 'after': c, 'wsd_action': 'rescore changed menu on same frozen occurrences'})
    report = {'changed_cards': len(changes), 'unchanged_cards': len(new)-len(changes),
              'max_wsd_occurrences': len(changes)*30, 'changes': changes}
    write(ws.root / 'raw/surfaces/headway' / f'{state.get("prefix", lang)}-menu-rollout-preview.json', report)
    print(f'{lang}: {len(changes)} menu cards changed, {len(new)-len(changes)} unchanged; '
          f'WSD upper bound {len(changes)*30} occurrences; frozen supply retained', flush=True)

def execute(ws, state, approved_usd=0):
    lang = state['language']
    run = ws.root / 'runs' / lang / 'speech' / state['run_id']
    source = ws.root / 'runs' / lang / 'speech' / state['source_run']
    preview = read(ws.root / 'raw/surfaces/headway' / f'{state.get("prefix", lang)}-menu-rollout-preview.json')
    targets = [c['surface'] for c in preview['changes']]
    bundle = ws.root / 'raw/surfaces/headway' / f'{state.get("prefix", lang)}-fresh-wsd.json'
    if bundle.exists():
        print(f'{lang}: fresh bundle exists; no repeat scoring', flush=True)
        return
    tags = ws.root / 'raw/reflexive' / lang / f'tags-{run.name}.json'
    env = {**os.environ, 'PYTHONPATH': str(REPO / 'src')}
    commands = []
    if not tags.exists():
        commands.append([sys.executable, str(REPO / 'scripts/build_reflexive_tags.py'),
                         '--workspace', str(ws.root), '--language', lang, '--run-dir', str(run),
                         '--assignment-source', str(source), '--prewsd', state['freeze'],
                         '--target-surfaces', *targets])
    commands.append([sys.executable, '-m', 'fluency.speech.wsd_execute', '--run-dir', str(run),
                     '--out', str(bundle), '--profile-id', f'{lang}-v23-1',
                     '--prewsd', state['freeze'], '--reflexive-tags', str(tags),
                     '--embedding-preview', str(ws.root / 'raw/surfaces/headway' / f'{lang}-embedding-preview.json'),
                     '--multiword-inventory', str(ws.root / 'raw/mwe' / f'mwe-{lang}-10k-sieve/mwe_merged.json'),
                     '--target-surfaces', *targets])
    if not approved_usd:
        commands[-1].append('--offline-only')
    else:
        preflight = ws.root / 'raw/surfaces/headway' / f'{lang}-embedding-preview.json'
        if not preflight.exists():
            raise ValueError('offline preflight required before paid execution')
        misses = read(preflight)
        # Conservative envelope includes 1000 overhead tokens/text and all retries.
        envelope = (misses['utf8_bytes'] + 1000 * misses['missing_count']) * .15 / 1_000_000 * 13
        if envelope > approved_usd:
            raise ValueError(f'projected conservative spend ${envelope:.3f} exceeds approval')
        print(f"Embedding preflight: {misses['missing_count']} texts, {misses['utf8_bytes']} UTF-8 bytes; conservative retry envelope ${envelope:.3f}; approval ${approved_usd:.2f}", flush=True)
    print(f'{lang}: targeted WSD on {len(targets)} cards; paid cache misses allowed: {bool(approved_usd)}', flush=True)
    for n, command in enumerate(commands):
        log = ws.root / 'raw/surfaces/headway' / f'{lang}-{run.name}-execute-{n}.log'
        with log.open('w') as f:
            code = subprocess.call(command, env=env, cwd=REPO, stdout=f, stderr=subprocess.STDOUT)
        print(log.read_text()[-4000:], flush=True)
        if code:
            raise SystemExit(f'{lang}: step failed ({code}); see {log}')

def import_rows(ws, state):
    from fluency.wsd.importer import import_wsd_assignments
    from fluency.wsd.splice import carried_row, write_spliced_bundle
    lang = state['language']
    run = ws.root / 'runs' / lang / 'speech' / state['run_id']
    if (run / 'stages/04_wsd_assignments/output/assignments.jsonl').exists():
        print(f'{lang}: stage 04 already imported')
        return
    source = ws.root / 'runs' / lang / 'speech' / state['source_run']
    fresh = read(ws.root / 'raw/surfaces/headway' / f'{state.get("prefix", lang)}-fresh-wsd.json')
    preview = read(ws.root / 'raw/surfaces/headway' / f'{state.get("prefix", lang)}-menu-rollout-preview.json')
    changed = {c['card_id'] for c in preview['changes']}
    src4 = source / 'stages/04_wsd_assignments/output'
    method, report = read(src4 / 'method.json')['method'], read(src4 / 'report.json')
    menu_id = file_content_id(run / 'stages/02_sense_menu/output/sense-menu.json')
    def carried():
        with (src4 / 'assignments.jsonl').open() as f:
            for line in f:
                row = json.loads(line)
                if row['card_id'] not in changed:
                    yield carried_row(row, source_run_id=source.name, source_method=method,
                                      sense_menu_content_id=menu_id)
    path = ws.root / 'raw/wsd' / lang / f'headway-{run.name}-spliced.json'
    report_path = ws.root / 'raw/surfaces/headway' / f'{state.get("prefix", lang)}-splice-report.json'
    if path.exists() and report_path.exists():
        splice_report = read(report_path)
    else:
        splice_report = write_spliced_bundle(path, run_id=run.name, language=lang, mode='speech',
            inputs=fresh['inputs'], method=fresh['method'],
            sampling_policy=(report.get('occurrence_sampling') or {}).get('policy') or {},
            carried=carried(), fresh=fresh['assignments'], declared=(), progress=lambda s: print(s, flush=True))
        write(report_path, splice_report)
    import_wsd_assignments(ws, run_id=run.name, language=lang, mode='speech', bundle_path=path, streaming=True)
    print(f'{lang}: complete assignment bundle imported; {splice_report["rows_by_origin"]}', flush=True)

def release(ws, state):
    from fluency.enrichments.conjugations import build_conjugation_layer
    from fluency.release.run_candidate import build_inactive_run_candidate
    from fluency.release.validation import validate_release_bundle
    from fluency.release.index_shards import shard_app_index
    from fluency.release.example_shards import shard_app_examples
    lang = state['language']
    run = ws.root / 'runs' / lang / 'speech' / state['run_id']
    output = ws.root / 'releases' / lang / 'speech' / state['release_id']
    if output.exists():
        raise ValueError('candidate already exists; validate it, do not overwrite')
    snapshot = 'enwiktionary-2026-09-13' if lang == 'es' else 'enwiktionary-2026-08-20'
    metadata, layer_report = build_conjugation_layer(ws,
        sense_menu=run / 'stages/02_sense_menu/output/sense-menu.json',
        source_snapshot=ws.root / 'raw/conjugations' / lang / 'kaikki' / snapshot)
    write(ws.root / 'raw/surfaces/headway' / f'{lang}-conjugation-report.json', layer_report)
    output = build_inactive_run_candidate(ws, run_id=run.name, release_id=state['release_id'],
        language=lang, mode='speech', conjugations_artifact_id=metadata.artifact_id,
        wsd_selection_projection='mwe_augmented', wsd_publication_projection='forced_leaf',
        memory_bounded=True)
    validate_release_bundle(output)
    command = [sys.executable, str(REPO / 'scripts/build_merge_exceptions.py'),
               '--language', lang, '--release-index', str(output / 'app/vocabulary.index.json'),
               '--sense-menu', str(run / 'stages/02_sense_menu/output/sense-menu.json'),
               '--out', str(output / 'app/merge-exceptions.json')]
    if lang == 'pt':
        command.extend(['--extract', str(ws.root / 'raw/wiktionary' /
            read(run / 'profile.json')['sense_menu']['snapshot_id'] /
            'kaikki.org-dictionary-Portuguese.jsonl')])
    subprocess.run(command, check=True, env={**os.environ, 'PYTHONPATH': str(REPO / 'src')})
    shard_app_index(output / 'app', slim=True)
    shard_app_examples(output / 'app', slim=True)
    print(f'{lang}: inactive candidate built/validated/sharded: {output}', flush=True)

def main():
    # Large acyclic JSON bundles otherwise trigger repeated full-heap scans.
    # This short-lived rollout process releases its heap on exit.
    gc.disable()
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--workspace', type=Path, required=True)
    ap.add_argument('--language', choices=SOURCES, required=True)
    ap.add_argument('--revision', type=int, default=1)
    ap.add_argument('--spend-approved-usd', type=float, default=0)
    ap.add_argument('--step', choices=['prepare','menus','wsd','import','release'], required=True)
    args = ap.parse_args()
    ws = Workspace.load(args.workspace.resolve())
    suffix = '' if args.revision == 1 else f'-r{args.revision}'
    path = ws.root / 'raw/surfaces/headway' / f'{args.language}{suffix}-rollout-state.json'
    if args.step == 'prepare':
        prepare(ws, args.language, path, args.revision)
    else:
        state = read(path)
        for input_path, expected in state['inputs'].items():
            if file_content_id(Path(input_path)) != expected:
                raise ValueError(f'pinned input changed: {input_path}; prepare a new revision')
        if args.step == 'wsd':
            execute(ws, state, args.spend_approved_usd)
        else:
            {'menus': menus, 'import': import_rows, 'release': release}[args.step](ws, state)
if __name__ == '__main__':
    main()
