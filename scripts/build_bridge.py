#!/usr/bin/env python3
"""Build compact BRIDGE assets from exact releases using the existing v4 scorer.

No classifiers, services, progress writes or release activation are involved.
"""
import argparse
import json
from pathlib import Path

from fluency.enrichments.cognates import build_app_cognates_by_sense, _extract_entries
from fluency.features.verb_forms import read_verb_forms, compatible_forms
from fluency.enrichments.card_rules import is_expression_sense, sense_alternatives


def expanded_meanings(row):
    result = []
    for m in row.get('meanings', []):
        if m.get('pos') == 'SENSE_CYCLE' and m.get('allSenses'):
            for sense in m['allSenses']:
                result.append({**sense, 'pos': sense.get('pos') or m.get('cycle_pos') or 'X'})
        else:
            result.append(m)
    return result


def compact_meaning(m):
    return {k: m[k] for k in ('pos', 'translation', 'meaning', 'context', 'headword',
            'sense_id', 'sense_id_aliases', 'allSenses') if k in m}


def build(workspace, config_path, extracts, output):
    config = json.loads(config_path.read_text())
    forms = {code: read_verb_forms(_extract_entries(extract)) for code, extract in extracts.items()}
    releases = {}
    for name, cfg in config['languages'].items():
        if cfg.get('indexPath') and cfg.get('routeCode') in extracts:
            code = cfg['routeCode']
            path = workspace / cfg['indexPath']
            if not path.exists():
                raise FileNotFoundError(path)
            rows = json.loads(path.read_text())
            for row in rows:
                row['meanings'] = expanded_meanings(row)
            releases[code] = (name, cfg, rows)
    for target, (name, cfg, rows) in releases.items():
        known = {code: extract for code, extract in extracts.items()
                 if code != target and (Path('config/cognates') / f'{target}-{code}.json').exists()}
        if not known:
            continue
        release_id = Path(cfg['indexPath']).parent.parent.name
        mapping = build_app_cognates_by_sense(language=target, config_root=Path('config'),
            raw_root=workspace / 'raw', known_extracts=known, release_rows=rows,
            release_id=release_id)
        wanted = {code: {} for code in known}
        targets = {}
        verb_compatible = {}
        for row in rows:
            word = row['word'].strip().lower()
            scores = mapping['scores'].get(word, {})
            requirements = []
            verb_checks = {code: [] for code in known}
            for m in row.get('meanings', []):
                if not str(m.get('translation') or m.get('meaning') or '').strip():
                    continue
                requirement = []
                if not is_expression_sense(m, word):
                    headword = str(m.get('headword') or '').strip().lower()
                    keys = [headword, ''] if headword else sorted(scores)
                    for pivot in sorted(sense_alternatives(m.get('translation') or m.get('meaning'))):
                        for key in keys:
                            for code, score in scores.get(key, {}).get(pivot, {}).items():
                                if score < mapping['thresholds'][code]:
                                    continue
                                source = mapping['matches'].get(word, {}).get(key, {}).get(pivot, {}).get(code, pivot)
                                candidate = [code, source, pivot, score]
                                if candidate not in requirement:
                                    requirement.append(candidate)
                                wanted[code].setdefault(source, set()).add(pivot)
                requirements.append(requirement)
                if str(m.get('pos') or '').upper() in {'VERB', 'AUX'}:
                    target_signatures = forms[target].get(word, {}).get(str(m.get('headword') or word).lower(), set())
                    for code in known:
                        safe = any(candidate[0] == code and target_signatures & source_signatures
                            for candidate in requirement
                            for source_signatures in forms[code].get(candidate[1], {}).values())
                        verb_checks[code].append(safe)
            if any(verb_checks.values()):
                verb_compatible[word] = {code: all(checks) for code, checks in verb_checks.items() if checks}
            # Never publish a card whose unmatchable sense might be overlooked.
            if requirements and all(requirements):
                targets[word] = {'id': row['id'], 'requirements': requirements,
                    'meanings': [{**compact_meaning(m), 'verb': str(m.get('pos') or '').upper() in {'VERB', 'AUX'}, 'formSignatures': [list(v) for v in forms[target].get(word, {}).get(str(m.get('headword') or word).lower(), set())]} for m in row.get('meanings', []) if str(m.get('translation') or m.get('meaning') or '').strip()]}
        sources = {}
        source_releases = {}
        for code in known:
            if code not in releases:
                continue
            source_name, source_cfg, source_rows = releases[code]
            source_releases[code] = Path(source_cfg['indexPath']).parent.parent.name
            by_word = {}
            for row in source_rows:
                surface = row['word'].strip().lower()
                for m in row.get('meanings', []):
                    if is_expression_sense(m, surface):
                        continue
                    keys = {surface, str(m.get('headword') or '').strip().lower()}
                    pivots = sense_alternatives(m.get('translation') or m.get('meaning'))
                    for key in keys & wanted[code].keys():
                        if pivots & wanted[code][key]:
                            # Only a dictionary-evidenced corresponding verb
                            # form may supply a target verb's meaning. Keep the
                            # form evidence on the source candidate for runtime.
                            verb = str(m.get('pos') or '').upper() in {'VERB', 'AUX'}
                            card = {'progressEligible': not m.get('unassigned') and m.get('assignment_method') != 'unassigned' and (m.get('display_frequency', m.get('frequency')) is None or float(m.get('display_frequency', m.get('frequency')) or 0) > 0), 'verb': verb, 'formSignatures': [list(v) for v in forms[code].get(surface, {}).get(str(m.get('headword') or surface).lower(), set())], 'fullId': f'{code}0{row["id"]}', 'targetWord': row['word'],
                                'language': source_name, 'meanings': [{**compact_meaning(m), 'pos': str(m.get('pos') or 'X').upper()}]}
                            bucket = by_word.setdefault(key, [])
                            if card not in bucket:
                                bucket.append(card)
            sources[code] = by_word
        # Each candidate still requires recorded source knowledge at runtime;
        # unsupported/missing source senses cannot qualify.
        bundle = {'schema': 'bridge/v1', 'language': target, 'targetLanguage': name,
            'built_from_release_id': release_id, 'source_releases': source_releases,
            'thresholds': mapping['thresholds'], 'targets': targets, 'sources': sources, 'verb_compatible': verb_compatible,
            'method': 'cognate-score/v4 + dictionary-verb-forms/v1',
            'source_extracts': {code: f'{extract.parent.name}/{extract.name}' for code, extract in extracts.items()},
            'policy_files': [f'config/cognates/{target}-{code}.json' for code in known]}
        path = output / f'{target}.json'
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(bundle, ensure_ascii=False, separators=(',', ':')) + '\n')
        print(f'{target}: {len(targets)} potentially eligible cards; '
              f'{sum(len(v) for v in sources.values())} source words; {path.stat().st_size:,} bytes', flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--workspace', type=Path, required=True)
    parser.add_argument('--config', type=Path, default=Path('app/config/config.json'))
    parser.add_argument('--extract', action='append', required=True, help='code=path')
    parser.add_argument('--out', type=Path, default=Path('app/data/bridge'))
    args = parser.parse_args()
    build(args.workspace, args.config, {code: Path(path) for code, path in
        (item.split('=', 1) for item in args.extract)}, args.out)
