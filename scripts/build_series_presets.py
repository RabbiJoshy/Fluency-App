#!/usr/bin/env python3
"""Build complete surface-form Casa and Élite decks from retained local sources.

No WSD, embeddings, LLM or network calls. Entity lookup is an optional separate,
resumable build-time step; absent results never exclude vocabulary.
"""
import argparse
import json
from pathlib import Path
import subprocess
from urllib.parse import quote

import build_casa_de_papel as casa

ROOT = Path(__file__).resolve().parents[1]


def prepare(workspace):
    bundles = []
    for slug, raw in [('casa-de-papel', workspace / 'raw/series/la-casa-de-papel'),
                      ('elite', workspace / 'raw/series/elite/20261025')]:
        manifest = json.loads((ROOT / f'app/data/series/{slug}-sources.json').read_text())
        episodes = casa.add_translations(casa.load_episodes(manifest, raw, True), manifest, raw)
        inventory = json.loads((ROOT / 'app/data/speech-frequency/es-literal-ground-r6-fw1.json').read_text())['values']
        dialogue, deck = casa.build(episodes, inventory, manifest, include_all=True)
        if slug == 'elite':
            deck['presetRevision'] = 'offline-season1-v1-all-forms'
            dialogue['coverage'].update(complete=False, missing=[], scope='Season 1 sample',
                                        sampleComplete=len(episodes) == 8)
        bundles.append((slug, episodes, dialogue, deck))
    return bundles, inventory


def build_lexicon(bundles, inventory, snapshot, entity_results):
    # Use the shared dictionary adapter, with surface identities intact. Do not
    # add heuristic clitic splitting or run any of the online WSD stages.
    from fluency.core.identity import create_card_record
    from fluency.sense_menu.kaikki import KaikkiSenseMenuAdapter
    from fluency.sense_menu.config import load_sense_menu_language_policy
    words = sorted({w for _, _, _, deck in bundles for w in deck['surfaces']} - set(inventory))
    # Subtitle tokenisation folds case; license a title-case dictionary entry
    # only when that exact spelling was observed. All-caps abbreviations remain
    # separate so a normal word cannot inherit an unrelated acronym's menu.
    title_case = frozenset(token.lower().replace('’', "'")
        for _, episodes, _, _ in bundles for ep in episodes for line in ep['lines']
        for token in casa.TOKEN.findall(line['spanish'])
        if token[:1].isupper() and not token.isupper())
    policy = load_sense_menu_language_policy(ROOT, policy_id='es-wiktionary-v1', language='es')
    adapter = KaikkiSenseMenuAdapter(snapshot, language_code='es', language_policy=policy,
                                   title_case_headwords=title_case)
    bundle, report = adapter.build([create_card_record('es', w).to_dict() for w in words],
                                   snapshot_id='enwiktionary-2026-09-13')
    entries, menus, menu_ids = {}, {}, {}
    pos_names = {'adj': 'ADJ', 'adv': 'ADV', 'noun': 'NOUN', 'verb': 'VERB', 'name': 'PROPN',
                 'pron': 'PRON', 'prep': 'PREP', 'conj': 'CONJ', 'intj': 'INTJ', 'num': 'NUM'}
    for card in bundle['cards']:
        word = card['surface_form']
        meanings = []
        surface_grammar = {}
        for analysis in card['analyses']:
            for sense in analysis['senses']:
                if not sense.get('translation'):
                    continue
                provider = sense.get('provider_metadata', {})
                features = sense.get('metadata', {}).get('features', [])
                grammar_key = f'{analysis["headword"]}:{pos_names.get(analysis["part_of_speech"], analysis["part_of_speech"].upper())}'
                surface_grammar[grammar_key] = [f for f in features if f.get('family') == 'grammar']
                meanings.append({
                    'pos': pos_names.get(analysis['part_of_speech'], analysis['part_of_speech'].upper()),
                    'translation': sense['translation'], 'headword': analysis['headword'],
                    'context': provider.get('context', ''), 'sense_id': sense['sense_id'],
                    'source': 'wiktionary', 'source_reference': sense['source_reference'],
                    'source_url': f'https://en.wiktionary.org/wiki/{quote(analysis["headword"])}#Spanish',
                    'metadata': {'contract_version': 'sense-metadata/v1',
                                 'features': [f for f in features if f.get('family') != 'grammar'],
                                 'source_metadata': {'tags': provider.get('tags', []),
                                                     'regions': provider.get('regions', [])}},
                    'assignment_method': 'unassigned'
                })
        entity = entity_results.get(word, {})
        key = json.dumps(meanings, ensure_ascii=False, sort_keys=True)
        if key not in menu_ids:
            menu_ids[key] = f'menu-{len(menu_ids) + 1}'
            menus[menu_ids[key]] = meanings
        entries[word] = {'id': card['card_id'], 'meaningMenu': menu_ids[key],
                         'surfaceGrammar': surface_grammar,
                         'entity': entity.get('entity'),
                         'entityRecognition': entity.get('entityRecognition', 'local-registry-checked; remote-pending')}
    return {'version': 'all-forms-v1', 'source': 'English Wiktionary via Kaikki',
            'snapshot': 'enwiktionary-2026-09-13', 'snapshotSha256': adapter.snapshot_content_id,
            'license': 'CC BY-SA; individual entry history and attribution at source_url',
            'entries': entries, 'menus': menus}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--workspace', type=Path, required=True)
    parser.add_argument('--wiktionary', type=Path, required=True)
    args = parser.parse_args()
    bundles, inventory = prepare(args.workspace)
    entity_path = args.workspace / 'raw/series/series-entities-20261026.json'
    entity_results = json.loads(entity_path.read_text()) if entity_path.exists() else {}
    lexicon = build_lexicon(bundles, inventory, args.wiktionary, entity_results)
    (ROOT / 'app/data/series/spanish-lexicon.json').write_text(json.dumps(lexicon, ensure_ascii=False, separators=(',', ':'))+'\n')
    for slug, episodes, dialogue, deck in bundles:
        records = [{'title': ep['episode'], 'artist': deck['playlistName'],
                    'dialogueLines': [{'text': line['spanish']} for line in ep['lines']]} for ep in episodes]
        result = subprocess.run(['node', str(ROOT / 'scripts/annotate_offline_intake.mjs')],
            input=json.dumps({'records': records, 'speechSurfaces': list(inventory)}), text=True,
            capture_output=True, check=True)
        deck['intake'] = json.loads(result.stdout)
        result = subprocess.run(['node', str(ROOT / 'scripts/complete_series_deck.mjs')],
            input=json.dumps(deck), text=True, capture_output=True, check=True)
        deck = json.loads(result.stdout)
        for name, value in [(f'{slug}.json', dialogue), (f'{slug}-deck.json', deck)]:
            (ROOT / 'app/data/series' / name).write_text(json.dumps(value, ensure_ascii=False, separators=(',', ':'))+'\n')
        print(slug, len(episodes), 'episodes', deck['matchedCount'], 'cards', deck['vocabularySummary'], flush=True)


if __name__ == '__main__':
    main()
