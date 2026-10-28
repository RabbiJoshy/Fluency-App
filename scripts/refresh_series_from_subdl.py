#!/usr/bin/env python3
"""Download reviewed releases from probe_subdl_series catalogues.

No scraping or WSD. Keep the previously reviewed Casa fallback where the API
has no Spanish release. Writes candidate manifests to --output-dir for review;
it never publishes app assets. URLs saved here never include API credentials.
"""
import argparse
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import re
import time
from urllib.parse import urlsplit
from urllib.request import Request, urlopen
import zipfile

ROOT = Path(__file__).resolve().parents[1]
# Exact releases selected by identity, language, full-dialogue members and cut.
# SubDL's hi flag is unreliable on older uploads; inspect filenames as well.
SELECTIONS = {
    'casa-de-papel': [('s01-es', '2035033-1758135'), ('s02-es', '2115679-1758139'),
                      ('s04-es', '1578612-2179786'), ('s04-en', '1578523-2207301'),
                      ('s01-en-packs', '2034853-1781786')],
    'elite': [('s01-es', '2457152-2243025'), ('s01-en', '2457146-1857077'),
              ('s02-es', '1783188-2047835'), ('s02-en', '1783157-2047817'),
              ('s03-es', '1576505-2163198'), ('s03-en', '1576460-2226542')],
}


def resolve_members(expected, actual):
    """Use archive names when legacy API decoding loses accented characters.

    Match only unique full filenames; never infer episode identity from order.
    The original archive/hash stays authoritative for bytes and provenance.
    """
    resolved = []
    for name in expected:
        matches = [member for member in actual if member == name]
        if not matches and '\ufffd' in name:
            matches = [member for member in actual
                       if re.sub(r'[^\x00-\x7f]', '\ufffd', member) == re.sub(r'[^\x00-\x7f]', '\ufffd', name)]
        if len(matches) != 1 or matches[0] in resolved:
            raise ValueError('Pack member metadata is absent or ambiguous in archive')
        resolved.append(matches[0])
    if not resolved:
        raise ValueError('API returned no pack member metadata')
    return resolved


def download_release(catalogue, release_id, raw_root):
    payload = json.loads(catalogue.read_text())
    release = next(s for s in payload['response']['subtitles']
                   if urlsplit(s['url']).path == f'/subtitle/{release_id}.zip')
    path = urlsplit(release['url']).path
    url = 'https://dl.subdl.com' + path
    started = time.monotonic()
    # Public download endpoint; never copy credential-bearing URLs from API JSON.
    with urlopen(Request(url, headers={'User-Agent': 'Fluency-Subtitle-Probe/1'}), timeout=30) as response:
        data = response.read(20 * 1024 * 1024 + 1)
    if len(data) > 20 * 1024 * 1024:
        raise ValueError('Unexpectedly large subtitle archive')
    filename = f'api-20261028/{release_id}.zip'
    target = raw_root / filename
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(data)
    with zipfile.ZipFile(target) as archive:
        members = archive.namelist()
        expected = [m['name'] for m in release.get('unpack_files') or []]
        expected = resolve_members(expected, members)
    return {'file': filename, 'url': url, 'sha256': hashlib.sha256(data).hexdigest(),
            'page': 'https://subdl.com' + release['subtitlePage'],
            'catalogue': catalogue.name, 'release': release['release_name'],
            'seconds': round(time.monotonic() - started, 3), 'bytes': len(data),
            'members': expected}


def update_retained_record(record, raw_root, downloads):
    for source in downloads:
        if record['sha256'] == source['sha256']:
            if record.get('member') and record['member'] not in source['members']:
                raise ValueError('Retained member absent from refreshed archive')
            record.update({k: source[k] for k in ('file', 'url', 'page', 'sha256')})
            record['acquisition'] = 'subdl-api'
            return
    # Do not silently reclassify retained fallback files as freshly acquired.
    if hashlib.sha256((raw_root / record['file']).read_bytes()).hexdigest() != record['sha256']:
        raise ValueError('Retained source checksum mismatch')
    record['acquisition'] = 'retained-reviewed-fallback'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--catalogues', type=Path, required=True)
    parser.add_argument('--workspace', type=Path, required=True)
    parser.add_argument('--output-dir', type=Path, required=True)
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    report = {}
    for slug, selections in SELECTIONS.items():
        raw_root = args.workspace / ('raw/series/la-casa-de-papel' if slug == 'casa-de-papel'
                                     else 'raw/series/elite/20261025')
        downloads = [download_release(args.catalogues / f'{slug}-{suffix}.json', release_id, raw_root)
                     for suffix, release_id in selections]
        manifest = deepcopy(json.loads((ROOT / f'app/data/series/{slug}-sources.json').read_text()))
        manifest.update(retrievedAt='2026-10-28',
            acquisition='subdl-api-with-explicit-retained-fallbacks' if slug == 'casa-de-papel' else 'subdl-api',
            presetRevision='subdl-api-30-episodes-v7' if slug == 'casa-de-papel' else 'subdl-api-seasons1-3-v2-all-forms')
        if slug == 'elite':
            # Repeated refreshes replace the added seasons instead of appending
            # another copy of episodes or source-specific review exclusions.
            for field in ('episodes', 'translationSources'):
                manifest[field] = [r for r in manifest[field] if r['season'] == 1]
            manifest['blockedTranslations'] = [r for r in manifest['blockedTranslations']
                                                if r['episode'].startswith('S01')]
        for record in manifest['episodes'] + manifest.get('translationSources', []):
            update_retained_record(record, raw_root, downloads)
        for recut in manifest.get('recutTranslationSources', []):
            for language in ('spanish', 'english'):
                update_retained_record(recut[language], raw_root, downloads)
        if slug == 'elite':
            manifest.update(numbering='Netflix Seasons 1–3, episodes 1–8 each; representative sample.',
                            expectedEpisodeCounts=[8] * 8, sampleSeasons=[1, 2, 3])
            for source, (suffix, _) in zip(downloads, selections):
                season = int(suffix[1:3])
                if season == 1:
                    continue
                for member in source['members']:
                    match = re.search(r'S(\d{2})E(\d{2})', member, re.I)
                    if not match or int(match[1]) != season:
                        raise ValueError('Unexpected episode identity in season pack')
                    record = {k: source[k] for k in ('file', 'url', 'page', 'sha256')}
                    record.update(member=member, season=season, episode=int(match[2]), acquisition='subdl-api')
                    field = 'episodes' if suffix.endswith('-es') else 'translationSources'
                    manifest[field].append(record)
            season3_english = next(s for s in downloads if s['file'].endswith('1576460-2226542.zip'))
            manifest['blockedTranslations'].append({
                'episode': 'S03E02', 'start': 55, 'end': 56,
                'sourceSha256': season3_english['sha256'],
                'reason': 'English adds "Thanks anyway" without corresponding Spanish dialogue.'})
        report[slug] = {'downloads': downloads, 'episodes': len(manifest['episodes']),
                        'apiSpanishEpisodes': sum(r.get('acquisition') == 'subdl-api' for r in manifest['episodes'])}
        (args.output_dir / f'{slug}-sources.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n')
        print(slug, report[slug]['episodes'], 'episodes;', report[slug]['apiSpanishEpisodes'], 'via API', flush=True)
    (args.output_dir / 'acquisition.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')


if __name__ == '__main__':
    main()
