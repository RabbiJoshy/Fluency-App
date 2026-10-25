#!/usr/bin/env python3
"""Compare local bilingual subtitle packs without changing published decks.

The source manifest supplies one Spanish ZIP and one or more English ZIPs.
Occurrence counts use all Spanish cues; only conservative full-group matches
supply translation examples. Human review is recorded separately.
"""
import argparse
from bisect import bisect_left, bisect_right
from collections import Counter
import hashlib
import importlib.util
import json
from pathlib import Path
import random
import re
import time
import zipfile

ROOT = Path(__file__).resolve().parents[1]


def load_module(name, file):
    spec = importlib.util.spec_from_file_location(name, ROOT / 'scripts' / file)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


builder = load_module('subtitle_builder', 'build_casa_de_papel.py')
aligner = load_module('subtitle_alignment', 'audit_casa_bilingual_alignment.py')


def fit_episode(spanish, english):
    """Choose a global scale/offset by repeated start AND end boundary support."""
    starts = [c['start_ms'] for c in english]
    best = (0, 1, 0)
    for scale in (1, 25 / 23.976, 23.976 / 25):
        bins = Counter()
        for cue in spanish:
            t = cue['start_ms'] * scale
            for j in range(bisect_left(starts, t - 600000), bisect_right(starts, t + 600000)):
                bins[round((starts[j] - t) / 50) * 50] += 1
        for offset, _ in bins.most_common(5):
            hits = 0
            for cue in spanish:
                t = cue['start_ms'] * scale + offset
                for j in range(bisect_left(starts, t - 150), bisect_right(starts, t + 150)):
                    if abs(english[j]['end_ms'] - cue['end_ms'] * scale - offset) <= 150:
                        hits += 1
                        break
            if hits > best[0]:
                best = hits, scale, offset
    return {'tight_boundary_support': best[0], 'scale': best[1], 'offset_ms': best[2]}


def load_pack(path):
    episodes = {}
    with zipfile.ZipFile(path) as archive:
        for name in archive.namelist():
            if not name.lower().endswith('.srt'):
                continue
            match = re.search(r'S(\d{1,2})E(\d{1,2})|\b(\d{1,2})x(\d{1,2})\b', name, re.I)
            if not match:
                raise ValueError(f'Unrecognised episode identity: {name}')
            season, episode = (match[1], match[2]) if match[1] else (match[3], match[4])
            key = f'S{int(season):02}E{int(episode):02}'
            if key in episodes:
                raise ValueError(f'Duplicate episode: {key}')
            cues = builder.parse_srt(archive.read(name))
            if len(cues) < 200 or max(c['end_ms'] for c in cues) < 1800000:
                raise ValueError(f'Incomplete/forced-only episode: {key}')
            episodes[key] = {'member': name, 'cues': cues}
    return episodes


def accepted_groups(spanish, english, fit):
    """Precision-first timing acceptance, with nearby independent support.

    Tight boundaries plus neighbouring non-overlapping groups support position.
    These tests establish timing evidence, not semantic translation quality.
    """
    if fit['tight_boundary_support'] < max(30, .35 * min(len(spanish), len(english))):
        return []
    offsets, _ = aligner.local_offsets(spanish, english, fit['offset_ms'], scale=fit['scale'])
    groups = aligner.align_groups(spanish, english, offsets=offsets, scale=fit['scale'],
                                  tolerance_ms=150, max_group=3, max_gap_ms=1200, max_duration_ms=12000)
    accepted = []
    for i, group in enumerate(groups):
        # At least one independent match within 15 seconds on each side.
        if i == 0 or i == len(groups) - 1:
            continue
        if group['start_ms'] - groups[i - 1]['end_ms'] > 15000:
            continue
        if groups[i + 1]['start_ms'] - group['end_ms'] > 15000:
            continue
        # Prefer informative examples; single-word replies don't need to raise coverage.
        if len(builder.TOKEN.findall(group['spanish'])) < 4:
            continue
        if len(builder.TOKEN.findall(group['english'])) < 3:
            continue
        accepted.append({**group, 'status': 'accepted-by-timing-rules'})
    return accepted


def audit(raw_root, output_dir):
    start = time.perf_counter()
    manifest = json.loads((raw_root / 'sources.json').read_text())
    for source in manifest['sources']:
        if hashlib.sha256((raw_root / source['file']).read_bytes()).hexdigest() != source['sha256']:
            raise ValueError(f"Checksum mismatch: {source['file']}")
    es_source = next(s for s in manifest['sources'] if s['file'].startswith('spanish-'))
    spanish = load_pack(raw_root / es_source['file'])
    inventory = json.loads((ROOT / 'app/data/speech-frequency/es-literal-ground-r6-fw1.json').read_text())['values']
    counts = Counter(w for ep in spanish.values() for cue in ep['cues']
                     for w in builder.TOKEN.findall(cue['spanish'].lower().replace('’', "'")))
    vocabulary = {w: c for w, c in counts.items() if w in inventory}
    rows, all_groups, samples = [], {}, []
    for en_source in (s for s in manifest['sources'] if s['file'].startswith('english-')):
        english = load_pack(raw_root / en_source['file'])
        pack_groups = {}
        for key, source in sorted(spanish.items()):
            if key not in english:
                continue
            es, en = source['cues'], english[key]['cues']
            fit = fit_episode(es, en)
            groups = accepted_groups(es, en, fit)
            pack_groups[key] = groups
            covered_words = {w for g in groups for w in builder.TOKEN.findall(g['spanish'].lower().replace('’', "'"))}
            rows.append({'pack': en_source['file'], 'episode': key,
                         'spanish_member': source['member'], 'english_member': english[key]['member'],
                         'spanish_cues': len(es), 'english_cues': len(en), **fit,
                         'accepted_groups': len(groups),
                         'accepted_spanish_cues': sum(g['spanish_end'] - g['spanish_start'] for g in groups),
                         'study_surfaces_with_example': len(covered_words & vocabulary.keys())})
            # Same-release MZABI is the preselected primary, rather than whichever
            # pack happens to obtain the highest measured coverage.
            if 'mzabi' in en_source['file']:
                eligible = [g for g in groups if len(builder.TOKEN.findall(g['spanish'])) >= 5]
                rng = random.Random('elite-precision-review-' + key)
                for n, g in enumerate(rng.sample(eligible, min(12, len(eligible))), 1):
                    samples.append({'id': f'{key}-{n:02}', 'episode': key,
                                    **g, 'review': 'pending'})
        all_groups[en_source['file']] = pack_groups
    summary = {'series': manifest['series'], 'seasons_tested': sorted({k[:3] for k in spanish}),
               'spanish_episodes': len(spanish), 'spanish_cues': sum(len(e['cues']) for e in spanish.values()),
               'spanish_word_occurrences': sum(counts.values()), 'distinct_spanish_surfaces': len(counts),
               'matched_study_surfaces': len(vocabulary), 'study_levels_at_100_words': (len(vocabulary) + 99) // 100,
               'pack_download_seconds': manifest['batch_download_seconds'],
               'count_policy': 'all Spanish dialogue, independent of English match availability',
               'primary_pack': 'english-s1-mzabi.zip', 'packs': {}}
    for pack, groups in all_groups.items():
        matching = [r for r in rows if r['pack'] == pack]
        covered_words = {w for episode in groups.values() for g in episode
                         for w in builder.TOKEN.findall(g['spanish'].lower().replace('’', "'"))}
        summary['packs'][pack] = {'episodes': len(groups),
            'tight_boundary_support': sum(r['tight_boundary_support'] for r in matching),
            'accepted_groups': sum(r['accepted_groups'] for r in matching),
            'accepted_spanish_cues': sum(r['accepted_spanish_cues'] for r in matching),
            'study_surfaces_with_example': len(covered_words & vocabulary.keys())}
    summary['processing_seconds'] = round(time.perf_counter() - start, 3)
    output_dir.mkdir(parents=True, exist_ok=True)
    for name, data in [('summary', summary), ('episodes', rows), ('groups', all_groups),
                       ('review-sample', samples), ('vocabulary-counts', vocabulary)]:
        (output_dir / f'{name}.json').write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps(summary, indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--raw-root', type=Path, required=True)
    parser.add_argument('--output-dir', type=Path, required=True)
    args = parser.parse_args()
    audit(args.raw_root, args.output_dir)
