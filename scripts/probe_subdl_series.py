#!/usr/bin/env python3
"""Measure authenticated SubDL discovery without modifying published decks.

Reads SUBDL_API_KEY from the environment or an ignored local .env file. Saves
catalogues outside the repository. Never writes the credential or request URL.
Returned releases still need identity, cut and alignment review before use.
"""
import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import time
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

SHOWS = {'casa-de-papel': ('1300185', 5), 'elite': ('1300491', 8)}
ENDPOINT = 'https://api.subdl.com/api/v1/subtitles'


def validate_catalogue(payload, parameters):
    results = payload.get('results') or []
    if not results or str(results[0].get('sd_id')) != str(parameters['sd_id']):
        raise RuntimeError('SubDL returned an unexpected show identity.')
    for release in payload.get('subtitles') or []:
        if (release.get('language') != parameters['languages']
                or release.get('season') != parameters['season_number']):
            raise RuntimeError('SubDL returned a release outside the requested language/season.')


def load_key(env_file):
    key = os.environ.get('SUBDL_API_KEY', '').strip()
    if not key and env_file.exists():
        for line in env_file.read_text().splitlines():
            name, sep, value = line.strip().removeprefix('export ').partition('=')
            if sep and name.strip() == 'SUBDL_API_KEY':
                key = value.strip().strip('\"\'')
    if not key:
        raise ValueError('Missing SUBDL_API_KEY: set it in the environment or local .env.')
    return key


def query(key, parameters):
    started = time.monotonic()
    request = Request(ENDPOINT + '?' + urlencode({'api_key': key, **parameters}),
                      headers={'Accept': 'application/json', 'User-Agent': 'Fluency-Subtitle-Probe/1'})
    try:
        with urlopen(request, timeout=30) as response:
            payload = json.load(response)
    except HTTPError as exc:
        # Exceptions can include the credential-bearing URL. Never print them.
        raise RuntimeError(f'SubDL HTTP {exc.code}; stopped without retrying.') from None
    except (URLError, TimeoutError, OSError, ValueError):
        raise RuntimeError('SubDL request failed or returned invalid JSON.') from None
    if not payload.get('status'):
        raise RuntimeError('SubDL rejected the request; check key validity and quota.')
    validate_catalogue(payload, parameters)
    return payload, round(time.monotonic() - started, 3)


def save_query(key, params, filename, output_dir, slug, summary):
    payload, seconds = query(key, params)
    encoded = json.dumps({'parameters': params, 'seconds': seconds,
                          'response': payload}, ensure_ascii=False, indent=2)
    (output_dir / filename).write_text(encoded.replace(key, '[REDACTED]') + '\n')
    releases = payload.get('subtitles', [])
    result = {'show': slug, 'season': params['season_number'], 'language': params['languages'],
              'seconds': seconds, 'releases': len(releases), 'limitReached': len(releases) >= 30,
              'packsOnly': bool(params.get('full_season')),
              'packMembers': sum(len(s.get('unpack_files') or []) for s in releases), 'file': filename}
    summary['queries'].append(result)
    print(json.dumps(result), flush=True)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output-dir', type=Path, required=True)
    parser.add_argument('--env-file', type=Path, default=Path('.env'))
    parser.add_argument('--show', choices=SHOWS, action='append')
    parser.add_argument('--season', type=int, action='append', help='Default: all numbered seasons')
    args = parser.parse_args()
    if args.season and any(season < 1 for season in args.season):
        parser.error('Season must be positive.')
    try:
        key = load_key(args.env_file)
    except ValueError as exc:
        parser.exit(2, str(exc) + '\n')
    args.output_dir.mkdir(parents=True, exist_ok=True)
    summary = {'startedAt': datetime.now(timezone.utc).isoformat(), 'queries': [],
               'scope': 'Up to 30 releases per season/language; not an exhaustive catalogue',
               'alignmentReviewed': False, 'publishedDecksChanged': False}
    try:
        for slug in args.show or SHOWS:
            sd_id, last_season = SHOWS[slug]
            for season in args.season or range(1, last_season + 1):
                for language in ('ES', 'EN'):
                    params = {'sd_id': sd_id, 'type': 'tv', 'season_number': season,
                              'languages': language, 'subs_per_page': 30,
                              'unpack': 1, 'releases': 1, 'comment': 1}
                    filename = f'{slug}-s{season:02}-{language.lower()}.json'
                    result = save_query(key, params, filename, args.output_dir, slug, summary)
                    if result['limitReached']:
                        save_query(key, {**params, 'full_season': 1},
                            filename.replace('.json', '-packs.json'), args.output_dir, slug, summary)
    except RuntimeError as exc:
        summary['error'] = str(exc)
        parser.exit(1, str(exc) + '\n')
    finally:
        (args.output_dir / 'summary.json').write_text(json.dumps(summary, indent=2) + '\n')


if __name__ == '__main__':
    main()
