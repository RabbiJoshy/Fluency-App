"""Recover display-only dictionary alternatives from the exact release menus.

Published releases stay immutable. No corpus examples, senses, frequencies or
progress identities change. Run with PYTHONPATH=src from the repository root.
"""
import hashlib
import json
import re
from pathlib import Path

from fluency.sense_menu.canonical import examples_of, is_proper


def matches(form, text):
    return bool(re.search(r"(?<!\w)" + re.escape(form) + r"(?!\w)", text, re.I))


def build(name, config, workspace):
    cfg = config['languages'][name]
    index = workspace / cfg['indexPath']
    manifest = json.loads((index.parent.parent / 'manifest.json').read_text())
    lang = manifest['language']
    menu_path = workspace / 'runs' / lang / 'speech' / manifest['wsd']['source_id'] / 'stages/02_sense_menu/output/sense-menu.json'
    menu = json.loads(menu_path.read_text())
    cards = {card['surface_form']: card for card in menu['cards']}
    rows = json.loads(index.read_text())
    exceptions = json.loads((Path('app') / cfg['mergeExceptionsPath']).read_text())
    assert (exceptions.get('built_from_release_id') or exceptions.get('release_id')) == manifest['release_id']
    groups, examples = {}, {}
    report = {'release_id': manifest['release_id'], 'cards': len(rows), 'original_mismatches': 0,
              'rescued_senses': 0, 'rescued_examples': [], 'multiple_examples': 0, 'missing_source_cards': []}
    for row in rows:
        key = exceptions['keys'].get(row['word'].lower())
        if key:
            groups.setdefault(key, []).append(row['word'])
        source = cards.get(row['word'])
        if source is None:
            report['missing_source_cards'].append(row['word'])
            continue
        senses = {(a['menu_analysis_id'], s['source_reference']): (a, s)
                  for a in source['analyses'] for s in a['senses']}
        for meaning in [*row.get('meanings', []), *row.get('unused_menu_senses', [])]:
            pair = senses.get((meaning.get('menu_analysis_id'), meaning.get('source_reference')))
            if not pair:
                continue  # Special expression rows have their own display path.
            analysis, sense = pair
            assert meaning['headword'] == analysis['headword']
            candidates = []
            chosen = meaning.get('canonical_example')
            if chosen:
                candidates.append(chosen)
            for ex in examples_of(sense):
                if not is_proper(ex):
                    continue
                normal = {
                    'text': (ex.get('text') or ex.get('original') or '').strip(),
                    'translation': (ex.get('english') or ex.get('translation') or ex.get('translated') or '').strip(),
                    'bold_text_offsets': ex.get('bold_text_offsets') or [],
                    'bold_translation_offsets': ex.get('bold_translation_offsets') or [],
                }
                if not any((x['text'], x['translation']) == (normal['text'], normal['translation']) for x in candidates):
                    candidates.append(normal)
            if len(candidates) > 1:
                report['multiple_examples'] += 1
            if chosen and not matches(row['word'], chosen['text']):
                report['original_mismatches'] += 1
                replacement = next((ex for ex in candidates if matches(row['word'], ex['text'])), None)
                if replacement:
                    report['rescued_senses'] += 1
                    if len(report['rescued_examples']) < 12:
                        report['rescued_examples'].append({'word': row['word'], 'before': chosen['text'], 'after': replacement['text']})
            # Preserve all candidates when there is a choice. A release can
            # suppress its first line as a duplicate elsewhere on the card.
            extras = candidates if len(candidates) > 1 or not chosen else []
            if extras:
                previous = examples.get(meaning['sense_id'])
                assert previous is None or {(x['text'], x['translation']) for x in previous} == {(x['text'], x['translation']) for x in extras}, meaning['sense_id']
                examples[meaning['sense_id']] = extras
    payload = {'schema': 'dictionary-example-alternatives/v1', 'release_id': manifest['release_id'],
               'source_menu_sha256': hashlib.sha256(menu_path.read_bytes()).hexdigest(),
               'index_sha256': hashlib.sha256(index.read_bytes()).hexdigest(),
               'examples': examples, 'groups': groups}
    path = Path('app/data/dictionary-examples') / f'{lang}-{manifest["release_id"]}-v1.json'
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, separators=(',', ':')) + '\n')
    report['asset_bytes'] = path.stat().st_size
    return path.as_posix().removeprefix('app/'), report


if __name__ == '__main__':
    config_path = Path('app/config/config.json')
    config_text = config_path.read_text()
    config = json.loads(config_text)
    workspace = Path('../Fluency-Workspace')
    reports = {}
    for name in ('spanish', 'portuguese'):
        path, report = build(name, config, workspace)
        old_path = config['languages'][name].get('dictionaryExamplesPath')
        if old_path:
            config_text = config_text.replace(json.dumps(old_path), json.dumps(path))
        else:
            anchor = '"mergeExceptionsPath": ' + json.dumps(config['languages'][name]['mergeExceptionsPath']) + ',\n      "coveragePath": null'
            assert anchor in config_text
            config_text = config_text.replace(anchor, anchor + ',\n      "dictionaryExamplesPath": ' + json.dumps(path), 1)
        reports[name] = report
        print(name, {k: len(v) if isinstance(v, list) else v for k, v in report.items() if k != 'rescued_examples'})
    config_path.write_text(config_text)
    report_path = workspace / 'audits/seam/canonical-form-audit.json'
    report_path.write_text(json.dumps(reports, ensure_ascii=False, indent=2) + '\n')
