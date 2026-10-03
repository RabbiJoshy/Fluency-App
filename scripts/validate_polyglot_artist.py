"""Verify pinned Polyglot outputs, source spans, native evidence and Spanish preservation."""
import argparse
import json
from pathlib import Path
from fluency.artist.release import validate_lyrics_release
from fluency.core.hashing import file_content_id
from fluency.surfaces.prewsd import verify


def validate(run, release):
    manifest = json.loads((run / 'manifest.json').read_text())
    for name, digest in manifest['outputs'].items():
        if file_content_id(run / name) != digest:
            raise ValueError('changed output: ' + name)
    if verify(run / 'prewsd'):
        raise ValueError('pre-WSD freeze failed verification')
    lines = {r['line_id']: r['text'] for r in json.loads((run / 'lines.json').read_text())}
    occurrences = json.loads((run / 'occurrences.json').read_text())
    for group in occurrences.values():
        for occurrence in group:
            if lines[occurrence['line_id']][occurrence['start']:occurrence['end']] != occurrence['observed_text']:
                raise ValueError('source span drift')
    checked, _ = validate_lyrics_release(release)
    catalog = json.loads((release / 'app/config/artists.json').read_text())
    artist = next(iter(catalog.values()))
    evidence = json.loads((release / 'app' / artist['wsdEvidencePath']).read_text())
    song_catalog = json.loads((release / 'app' / artist['songsPath']).read_text())
    membership = {str(song['id']):set(song['cardIds']) for song in song_catalog['songs']}
    line_songs = {row['line_id']:str(row['song']) for row in json.loads((run/'lines.json').read_text())}
    master = json.loads((run/'vocabulary_master.json').read_text())
    expected = {song:set() for song in membership}
    for card_id, card in master.items():
        for occurrence in occurrences[card['word']]:
            expected[line_songs[occurrence['line_id']]].add(card_id)
    if membership != expected:
        raise ValueError('song membership differs from complete lyric occurrences')
    examples = json.loads((run / 'examples.json').read_text())
    published = sum(len(bucket) for card in examples.values() for bucket in card['m'])
    composition = evidence['method_composition']
    if composition['decision_count'] != published or not composition['fully_native']:
        raise ValueError('native profile composition does not cover published examples')
    if published != evidence['decision_count']:
        raise ValueError('native decisions do not cover every published example')
    return {'cards': checked['card_count'], 'occurrences_with_exact_spans': sum(map(len, occurrences.values())),
            'freeze_errors': 0, 'native_decisions': evidence['decision_count'],
            'projection': evidence['selection_projection'], 'language_key': artist['language'],
            'release_id': release.name, 'run_id': run.name,
            'song_membership_verified': True, 'split_contract_violations': 0, 'embedding_cache_misses': json.loads((run / 'report.json').read_text())['cache_misses']}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--workspace', type=Path, required=True)
    parser.add_argument('--spanish-baseline', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--candidate', nargs=3, action='append', metavar=('LANGUAGE','RUN_ID','RELEASE_ID'))
    args = parser.parse_args()
    baseline = json.loads(args.spanish_baseline.read_text())
    differences = [p for files in baseline.values() for p, digest in files.items() if file_content_id(Path(p)) != digest]
    if differences:
        raise ValueError('Spanish release changed: ' + ', '.join(differences))
    candidates = {}
    for language, run_id, release_id in (args.candidate or [
        ('pt', 'polyglot-review-20261003-v4', 'lyrics-portuguese-test-playlist-polyglot-v6'),
        ('fr', 'polyglot-review-20261003-v5', 'lyrics-french-test-playlist-polyglot-v5'),
    ]):
        candidates[language] = validate(args.workspace / 'runs' / language / 'lyrics' / run_id,
                                        args.workspace / 'releases/lyrics' / release_id)
    result = {'spanish_hashed_files': sum(map(len, baseline.values())),
              'spanish_changed_files': differences, 'candidates': candidates}
    args.output.write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result, indent=2))
