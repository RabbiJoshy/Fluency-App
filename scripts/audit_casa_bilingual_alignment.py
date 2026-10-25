#!/usr/bin/env python3
"""Audit local Casa subtitle grouping; never replace published app assets.

Pairs are timing candidates, not semantic judgments. A multi-cue translation
belongs to the complete Spanish group, not to each fragment independently.
"""
import argparse
from bisect import bisect_left, bisect_right
from collections import Counter, defaultdict
import importlib.util
import hashlib
import json
from pathlib import Path
import zipfile

ROOT = Path(__file__).resolve().parents[1]


def local_offsets(spanish, english, baseline, *, scale=1, window_ms=300000):
    """Correct small local timing jumps only with repeated boundary evidence.

    Search within five seconds of the established episode offset. A change
    needs at least ten tight cue matches and a substantial gain over baseline;
    unmatched windows retain baseline rather than inventing an offset.
    """
    starts = [c['start_ms'] for c in english]
    windows = defaultdict(list)
    for i, cue in enumerate(spanish):
        windows[int(cue['start_ms'] // window_ms)].append(i)
    offsets, evidence = [baseline] * len(spanish), []
    for window, indices in windows.items():
        bins = Counter()
        for i in indices:
            t = spanish[i]['start_ms'] * scale
            for j in range(bisect_left(starts, t + baseline - 5000),
                           bisect_right(starts, t + baseline + 5000)):
                bins[round((starts[j] - t) / 50) * 50] += 1
        def support(offset):
            hits = 0
            for i in indices:
                cue = spanish[i]
                t = cue['start_ms'] * scale + offset
                for j in range(bisect_left(starts, t - 250), bisect_right(starts, t + 250)):
                    if abs(english[j]['end_ms'] - cue['end_ms'] * scale - offset) <= 350:
                        hits += 1
                        break
            return hits
        baseline_hits = support(baseline)
        candidates = [(support(offset), offset) for offset, _ in bins.most_common(5)]
        hits, chosen = max(candidates, default=(0, baseline))
        adopt = (hits >= max(10, len(indices) * .3)
                 and hits - baseline_hits >= max(8, len(indices) * .15)
                 and abs(chosen - baseline) >= 300)
        chosen = chosen if adopt else baseline
        for i in indices:
            offsets[i] = chosen
        evidence.append({'window_start_ms': window * window_ms, 'cues': len(indices),
                         'baseline_hits': baseline_hits, 'best_hits': hits,
                         'offset_ms': chosen, 'adjusted': adopt})
    return offsets, evidence


def align_groups(spanish, english, *, offset_ms=0, scale=1, tolerance_ms=500,
                 max_group=4, max_gap_ms=2000, max_duration_ms=20000, offsets=None):
    """Find disjoint monotonic groups, favouring coverage then small groups.

    Each transition consumes 1..max_group cues on both sides. Only close outer
    boundaries qualify. A sparse weighted-chain calculation allows omissions
    without shifting all later pairs or reusing an English cue.
    """
    if scale <= 0 or tolerance_ms < 0 or max_group < 1:
        raise ValueError('Invalid alignment parameters')
    for cues in (spanish, english):
        if any(c['end_ms'] <= c['start_ms'] for c in cues):
            raise ValueError('Invalid cue duration')
        if any(a['start_ms'] > b['start_ms'] for a, b in zip(cues, cues[1:])):
            raise ValueError('Cues must be ordered by start time')
    if offsets is not None and len(offsets) != len(spanish):
        raise ValueError('One offset is required per Spanish cue')
    en_starts = [c['start_ms'] for c in english]

    def spans(cues, start):
        for end in range(start + 1, min(len(cues), start + max_group) + 1):
            if end > start + 1 and cues[end - 1]['start_ms'] - cues[end - 2]['end_ms'] > max_gap_ms:
                break
            if cues[end - 1]['end_ms'] - cues[start]['start_ms'] > max_duration_ms:
                break
            yield end

    # Fenwick tree: best completed chain whose English end is <= a new start.
    tree = [(0.0, -1)] * (len(english) + 2)
    nodes, scheduled = [], defaultdict(list)

    def update(end, value):
        pos = end + 1
        while pos < len(tree):
            if value[0] > tree[pos][0]:
                tree[pos] = value
            pos += pos & -pos

    def query(end):
        pos, best = end + 1, (0.0, -1)
        while pos:
            if tree[pos][0] > best[0]:
                best = tree[pos]
            pos -= pos & -pos
        return best

    best = (0.0, -1)
    for i in range(len(spanish)):
        for en_end, value in scheduled.pop(i, []):
            update(en_end, value)
        current_offset = offsets[i] if offsets is not None else offset_ms
        start = spanish[i]['start_ms'] * scale + current_offset
        for j in range(bisect_left(en_starts, start - tolerance_ms),
                       bisect_right(en_starts, start + tolerance_ms)):
            previous_score, previous_node = query(j)
            for es_end in spans(spanish, i):
                if offsets is not None and offsets[es_end - 1] != current_offset:
                    continue
                end = spanish[es_end - 1]['end_ms'] * scale + current_offset
                for en_end in spans(english, j):
                    end_error = abs(english[en_end - 1]['end_ms'] - end)
                    if end_error > tolerance_ms:
                        continue
                    start_error = abs(en_starts[j] - start)
                    es_count, en_count = es_end - i, en_end - j
                    reward = es_count + en_count - .12 * (es_count + en_count - 2)
                    reward -= .2 * (start_error + end_error) / max(1, tolerance_ms)
                    score = previous_score + reward
                    node = len(nodes)
                    nodes.append((previous_node, i, es_end, j, en_end, start_error, end_error))
                    scheduled[es_end].append((en_end, (score, node)))
                    if score > best[0]:
                        best = (score, node)
    groups, node = [], best[1]
    while node >= 0:
        node, i, es_end, j, en_end, start_error, end_error = nodes[node]
        groups.append({'spanish_start': i, 'spanish_end': es_end,
                       'english_start': j, 'english_end': en_end,
                       'spanish': ' '.join(c['spanish'] for c in spanish[i:es_end]),
                       'english': ' '.join(c['spanish'] for c in english[j:en_end]),
                       'start_ms': spanish[i]['start_ms'],
                       'end_ms': spanish[es_end - 1]['end_ms'],
                       'start_error_ms': round(start_error), 'end_error_ms': round(end_error),
                       'status': 'timing-candidate'})
    return list(reversed(groups))


def measure_examples(deck, cue_groups, strict_cues):
    """Count selected examples separately from source cue coverage.

    Repeated identical text in an episode counts as available if at least one
    occurrence has a pair. A group provides an expanded example, not a promise
    that the original fragment has an independent English translation.
    """
    counts = Counter()
    by_word = {}
    for word, card in deck['surfaces'].items():
        available = []
        for example in card['lines']:
            key = example['song'], example['text']
            strict = key in strict_cues
            group = cue_groups.get(key)
            counts['examples'] += 1
            counts['strict_examples'] += strict
            counts['grouped_examples'] += group is not None
            counts['expanded_examples'] += bool(group and group['spanish'] != example['text'])
            if group:
                available.append(group)
        by_word[word] = bool(available)
    counts['cards'] = len(by_word)
    counts['cards_with_translation_candidate'] = sum(by_word.values())
    return dict(counts)


def audit(raw_root, output_dir):
    spec = importlib.util.spec_from_file_location('casa_builder', ROOT / 'scripts/build_casa_de_papel.py')
    builder = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(builder)
    provenance = json.loads((raw_root / 'sources.json').read_text())
    dialogue_path = ROOT / 'app/data/series/casa-de-papel.json'
    if hashlib.sha256(dialogue_path.read_bytes()).hexdigest() != provenance['dialogue_sha256']:
        raise ValueError('Spanish dialogue changed since the source audit; regenerate the baseline first')
    for record in provenance['english_sources']:
        if hashlib.sha256((raw_root / record['file']).read_bytes()).hexdigest() != record['sha256']:
            raise ValueError(f"English source checksum mismatch: {record['file']}")
    data = json.loads(dialogue_path.read_text())
    deck = json.loads((ROOT / 'app/data/series/casa-de-papel-deck.json').read_text())
    initial = {r['episode']: r for r in json.loads((raw_root / 'pairing-report.json').read_text())}
    strict_pairs = json.loads((raw_root / 'candidate-pairs.json').read_text())
    strict_cues = {(p['episode'], p['spanish']) for p in strict_pairs}
    output_dir.mkdir(parents=True, exist_ok=True)
    episodes, groups_by_episode, cue_groups = [], {}, {}
    single_cues = set()
    archives = {}
    try:
        for episode in data['episodes']:
            key, es = episode['episode'], episode['lines']
            row = initial[key]
            if key.startswith(('S01', 'S02', 'S04')):
                archive = 'subdl-s4-english-full.zip' if key.startswith('S04') else 'subdl-s1-english-bluray.zip'
                if archive not in archives:
                    archives[archive] = zipfile.ZipFile(raw_root / archive)
                en = builder.parse_srt(archives[archive].read(row['english_file']))
            else:
                en = builder.parse_srt((raw_root / row['english_file']).read_bytes())
            # Control comparison: same tolerance, no grouping and no local correction.
            singles = align_groups(es, en, offset_ms=row['offset_ms'], scale=row['scale'], max_group=1)
            for group in singles:
                single_cues.add((key, group['spanish']))
            offsets, evidence = local_offsets(es, en, row['offset_ms'], scale=row['scale'])
            groups = align_groups(es, en, offset_ms=row['offset_ms'], scale=row['scale'], offsets=offsets)
            covered = sum(g['spanish_end'] - g['spanish_start'] for g in groups)
            # Exact fragment translations are deliberately not manufactured.
            for group in groups:
                for i in range(group['spanish_start'], group['spanish_end']):
                    lookup = key, es[i]['spanish']
                    old = cue_groups.get(lookup)
                    if old is None or len(group['spanish']) < len(old['spanish']):
                        cue_groups[lookup] = group
            groups_by_episode[key] = groups
            kinds = Counter(f"{g['spanish_end']-g['spanish_start']}:{g['english_end']-g['english_start']}" for g in groups)
            episodes.append({**row, 'grouped_cues': covered, 'grouped_coverage': round(covered / len(es), 4),
                             'groups': len(groups), 'group_types': dict(kinds),
                             'single_cues_500ms': len(singles), 'offset_evidence': evidence})
            print(key, 'strict', row['tight_coverage'], 'grouped', round(covered / len(es), 3), flush=True)
    finally:
        for archive in archives.values():
            archive.close()
    summary = measure_examples(deck, cue_groups, strict_cues)
    single_summary = measure_examples(deck, {}, single_cues)
    all_translated_words = {word for groups in groups_by_episode.values() for group in groups
                            for word in builder.TOKEN.findall(group['spanish'].lower().replace('’', "'"))}
    summary.update({'single_examples_500ms': single_summary['strict_examples'],
                    'cards_with_candidate_after_reselecting_examples': len(set(deck['surfaces']) & all_translated_words),
                    'single_cues_500ms': sum(r['single_cues_500ms'] for r in episodes),
                    'spanish_cues': sum(r['spanish_cues'] for r in episodes),
                    'strict_cues': sum(r['tight_pairs'] for r in episodes),
                    'grouped_cues': sum(r['grouped_cues'] for r in episodes),
                    'status': 'timing feasibility only; semantic review required'})
    (output_dir / 'summary.json').write_text(json.dumps(summary, indent=2) + '\n')
    (output_dir / 'episodes.json').write_text(json.dumps(episodes, indent=2) + '\n')
    (output_dir / 'groups.json').write_text(json.dumps(groups_by_episode, ensure_ascii=False))
    print(json.dumps(summary, indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--raw-root', type=Path, required=True)
    parser.add_argument('--output-dir', type=Path, required=True)
    args = parser.parse_args()
    audit(args.raw_root, args.output_dir)
