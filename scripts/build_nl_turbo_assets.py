#!/usr/bin/env python3
"""Build Dutch Turbo assets, word frequency rank list, and probe songs for Lyrics Translation Mode."""

import json
import os
import re
import sys
import time
import urllib.request
import urllib.parse
from datetime import datetime, timezone
from pathlib import Path
from collections import Counter

REPO_ROOT = Path(__file__).resolve().parent.parent
WORKSPACE = Path('/Users/joshuathomasamar/PycharmProjects/Fluency-Workspace')
NL_RELEASE = WORKSPACE / 'releases/nl/speech/nl-speech-cascade-proto2-6000x10/app'
NL_OPENSUBTITLES = WORKSPACE / 'raw/opensubtitles/opensubtitles-v2018-en-nl-2016plus/OpenSubtitles.en-nl.nl'
NL_KAIKKI = WORKSPACE / 'raw/wiktionary/enwiktionary-2026-09-09/kaikki.org-dictionary-Dutch.jsonl'
TURBO_DIR = REPO_ROOT / 'app/turbo'

CURATED_NL_ENTITIES = {
    'joost': {
        'query': 'joost',
        'canonicalTitle': 'Joost Klein',
        'description': 'Dutch musician, rapper, and artist famed for high-energy gabberpop and Eurovision anthem "Europapa"',
        'entityType': 'artist',
        'source': 'curated'
    },
    'joost klein': {
        'query': 'joost klein',
        'canonicalTitle': 'Joost Klein',
        'description': 'Dutch musician, rapper, and artist famed for high-energy gabberpop and Eurovision anthem "Europapa"',
        'entityType': 'artist',
        'source': 'curated'
    },
    'bløf': {
        'query': 'bløf',
        'canonicalTitle': 'BLØF',
        'description': 'Celebrated Dutch pop-rock band from Zeeland, known for anthems like "Zoutelande" and "Aan de kust"',
        'entityType': 'artist',
        'source': 'curated'
    },
    'blof': {
        'query': 'blof',
        'canonicalTitle': 'BLØF',
        'description': 'Celebrated Dutch pop-rock band from Zeeland, known for anthems like "Zoutelande" and "Aan de kust"',
        'entityType': 'artist',
        'source': 'curated'
    },
    'guus meeuwis': {
        'query': 'guus meeuwis',
        'canonicalTitle': 'Guus Meeuwis',
        'description': 'Beloved Dutch singer from Brabant famed for joyful Nederpop anthems and stadium concerts',
        'entityType': 'artist',
        'source': 'curated'
    },
    'suzan & freek': {
        'query': 'suzan & freek',
        'canonicalTitle': 'Suzan & Freek',
        'description': 'Acclaimed Dutch pop duo known for warm acoustic harmonies and radio hits like "Als het avond is"',
        'entityType': 'artist',
        'source': 'curated'
    },
    'andré hazes': {
        'query': 'andré hazes',
        'canonicalTitle': 'André Hazes',
        'description': 'Legendary Dutch folk singer and undisputed king of the levenslied (song of life)',
        'entityType': 'artist',
        'source': 'curated'
    },
    'andre hazes': {
        'query': 'andre hazes',
        'canonicalTitle': 'André Hazes',
        'description': 'Legendary Dutch folk singer and undisputed king of the levenslied (song of life)',
        'entityType': 'artist',
        'source': 'curated'
    },
    'goldband': {
        'query': 'goldband',
        'canonicalTitle': 'Goldband',
        'description': 'The Hague post-punk synthpop group celebrated for infectious club anthems like "Noodgeval"',
        'entityType': 'artist',
        'source': 'curated'
    },
    'doe maar': {
        'query': 'doe maar',
        'canonicalTitle': 'Doe Maar',
        'description': 'Pioneering Dutch pop/ska/reggae band that caused nationwide mania in the 1980s',
        'entityType': 'artist',
        'source': 'curated'
    },
    'snelle': {
        'query': 'snelle',
        'canonicalTitle': 'Snelle',
        'description': 'Dutch rapper, singer, and songwriter known for personal, melodic storytelling songs like "Reünie"',
        'entityType': 'artist',
        'source': 'curated'
    },
    'marco borsato': {
        'query': 'marco borsato',
        'canonicalTitle': 'Marco Borsato',
        'description': 'One of the most commercially successful Dutch vocalists in history',
        'entityType': 'artist',
        'source': 'curated'
    },
    'amsterdam': {
        'query': 'amsterdam',
        'canonicalTitle': 'Amsterdam',
        'description': 'Capital city of the Netherlands, world-famous for historic canals and cultural heritage',
        'entityType': 'place',
        'source': 'curated'
    },
    'brabant': {
        'query': 'brabant',
        'canonicalTitle': 'North Brabant',
        'description': 'Southern Dutch province celebrated for warmth, gezelligheid, and musical identity',
        'entityType': 'place',
        'source': 'curated'
    },
    'nederland': {
        'query': 'nederland',
        'canonicalTitle': 'Netherlands',
        'description': 'Country in Northwestern Europe known for low-lying delta landscapes, art, and music',
        'entityType': 'place',
        'source': 'curated'
    }
}

CURATED_NL_MWES = {
    'aan het': {'expression': 'aan het', 'translation': 'be ...-ing (in progress)', 'source': 'curated'},
    'om te': {'expression': 'om te', 'translation': 'in order to', 'source': 'curated'},
    'als het ware': {'expression': 'als het ware', 'translation': 'as it were; so to speak', 'source': 'curated'},
    'in plaats van': {'expression': 'in plaats van', 'translation': 'instead of', 'source': 'curated'},
    'tot nu toe': {'expression': 'tot nu toe', 'translation': 'so far; until now', 'source': 'curated'},
    'van plan': {'expression': 'van plan', 'translation': 'planning; intending', 'source': 'curated'},
    'ten slotte': {'expression': 'ten slotte', 'translation': 'finally; in conclusion', 'source': 'curated'},
    'alsjeblieft': {'expression': 'alsjeblieft', 'translation': 'please; here you go', 'source': 'curated'},
    'alstublieft': {'expression': 'alstublieft', 'translation': 'please; here you go (formal)', 'source': 'curated'},
    'geen dank': {'expression': 'geen dank', 'translation': 'you are welcome; no problem', 'source': 'curated'},
    'hoe gaat het': {'expression': 'hoe gaat het', 'translation': 'how are you; how is it going', 'source': 'curated'}
}

NL_ELISIONS = {
    "'t": 'het',
    "'k": 'ik',
    "'s": 'des',
    "m'n": 'mijn',
    "z'n": 'zijn',
    "d'r": 'haar',
    "zo'n": 'zo een',
    "daar's": 'daar is',
    "wie's": 'wie is'
}


def build_nl_turbo_assets():
    print('1. Building Dutch vocabulary and frequency ranks...')
    
    # Load 6,000 words from release
    vocab_index_path = NL_RELEASE / 'vocabulary.index.json'
    dictionary = {}
    ranks_50k = {}
    lemmas_50k = {}

    if vocab_index_path.exists():
        print(f'   Reading release vocabulary from {vocab_index_path}...')
        with open(vocab_index_path, 'r', encoding='utf-8') as f:
            cards = json.load(f)
        for i, card in enumerate(cards):
            w = card.get('word', '').strip().lower()
            if not w or w in dictionary:
                continue
            rank = card.get('rank', i + 1)
            ranks_50k[w] = rank
            meanings = card.get('meanings', [])
            top_trans = meanings[0].get('translation', '') if meanings else ''
            top_pos = meanings[0].get('pos', '') if meanings else ''
            dictionary[w] = {
                'id': card.get('id', f'card_nl_{w}'),
                'rank': rank,
                'polysemous': len(meanings) > 1,
                'meaning_count': len(meanings),
                'top_translation': top_trans,
                'top_pos': top_pos,
                'meanings': [
                    {'pos': m.get('pos', ''), 'translation': m.get('translation', ''), 'context': m.get('context', '')}
                    for m in meanings
                ]
            }

    # Count additional words from OpenSubtitles if available
    if NL_OPENSUBTITLES.exists():
        print(f'   Reading OpenSubtitles from {NL_OPENSUBTITLES}...')
        freq_counter = Counter()
        with open(NL_OPENSUBTITLES, 'r', encoding='utf-8') as f:
            for i, line in enumerate(f):
                if i >= 600000:
                    break
                words = re.findall(r"[a-zA-ZÀ-ÿœæ]+(?:['’\-][a-zA-ZÀ-ÿœæ]+)*", line.lower())
                freq_counter.update(words)
        curr_rank = len(ranks_50k) + 1
        for w, _ in freq_counter.most_common(50000):
            if w not in ranks_50k:
                ranks_50k[w] = curr_rank
                curr_rank += 1

    # Load Kaikki Dutch for inflections and extra headwords
    if NL_KAIKKI.exists():
        print(f'   Reading Kaikki Dutch from {NL_KAIKKI}...')
        line_count = 0
        with open(NL_KAIKKI, 'r', encoding='utf-8') as f:
            for line in f:
                line_count += 1
                try:
                    entry = json.loads(line)
                except Exception:
                    continue

                word = entry.get('word', '').strip().lower()
                if not word or ' ' in word or len(word) > 30:
                    continue

                pos = entry.get('pos', '')
                senses = entry.get('senses', [])
                glosses = [g for s in senses for g in s.get('glosses', []) if g]

                if word not in dictionary and glosses:
                    rank = ranks_50k.get(word)
                    if rank and rank <= 10000:
                        dictionary[word] = {
                            'id': f'card_nl_{word}',
                            'rank': rank,
                            'polysemous': len(glosses) > 1,
                            'meaning_count': len(glosses),
                            'top_translation': glosses[0],
                            'top_pos': pos,
                            'meanings': [{'pos': pos, 'translation': g, 'context': ''} for g in glosses[:3]]
                        }

                # Inflections mapping
                for form_obj in entry.get('forms', []):
                    form_text = form_obj.get('form', '').strip().lower()
                    if form_text and form_text != word and ' ' not in form_text and len(form_text) < 30:
                        if form_text not in lemmas_50k:
                            lemmas_50k[form_text] = word

    print(f'   Final Dutch dictionary: {len(dictionary):,} entries')
    print(f'   Final Dutch lemma map: {len(lemmas_50k):,} inflected mappings')

    turbo_assets = {
        'version': '2.0.0-turbo-nl',
        'language': 'nl',
        'builtAt': datetime.now(timezone.utc).isoformat(),
        'elisions': NL_ELISIONS,
        'mwes': CURATED_NL_MWES,
        'curatedEntities': CURATED_NL_ENTITIES,
        'dictionary': dictionary
    }

    assets_path = TURBO_DIR / 'nl_turbo_assets.json'
    with open(assets_path, 'w', encoding='utf-8') as f:
        json.dump(turbo_assets, f, ensure_ascii=False)
    print(f'   Saved {assets_path} ({os.path.getsize(assets_path):,} bytes)')

    data_50k = {
        'ranks': ranks_50k,
        'lemmas': lemmas_50k
    }
    data_50k_path = TURBO_DIR / 'nl_50k_data.json'
    with open(data_50k_path, 'w', encoding='utf-8') as f:
        json.dump(data_50k, f, ensure_ascii=False)
    print(f'   Saved {data_50k_path} ({os.path.getsize(data_50k_path):,} bytes)')


def fetch_lrclib_record(title, artist, retries=3):
    headers = {'User-Agent': 'Fluency/0.1 (https://github.com/JoshuaThomasAmar/Fluency-Next)'}
    query = urllib.parse.urlencode({'track_name': title, 'artist_name': artist})
    url = f'https://lrclib.net/api/search?{query}'

    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=12) as resp:
                data = json.load(resp)
                synced_item = next((x for x in data if x.get('syncedLyrics')), None)
                plain_item = next((x for x in data if x.get('plainLyrics')), None)
                chosen = synced_item or plain_item
                if chosen:
                    return {
                        'title': title,
                        'artist': artist,
                        'lyrics': chosen.get('plainLyrics') or '',
                        'syncedLyrics': chosen.get('syncedLyrics') or '',
                        'lrclibId': chosen.get('id'),
                        'lrclibDurationMs': int((chosen.get('duration') or 0) * 1000)
                    }
        except Exception as e:
            if attempt < retries - 1:
                time.sleep(2.5 * (attempt + 1))
            else:
                print(f'Failed fetching {artist} - {title}: {e}')
    return None


def build_nl_probe_songs():
    print('2. Building Dutch probe songs with synchronized lyrics...')

    curated_tracks = [
        {'title': 'Europapa', 'artist': 'Joost', 'spotifyId': '2GwiltcZtcfWw9t1M5j58E'},
        {'title': 'Zoutelande', 'artist': 'BLØF', 'spotifyId': '6aAJY5FYW0TMLsUe2T7x4p'},
        {'title': 'Brabant', 'artist': 'Guus Meeuwis', 'spotifyId': '0GiWi4EkPduFWHQyhiKpRB'},
        {'title': 'Als Het Avond Is', 'artist': 'Suzan & Freek', 'spotifyId': '3ciQQMSy1lKDqJbwU9l1LT'},
        {'title': 'Zij Gelooft In Mij', 'artist': 'André Hazes', 'spotifyId': '0nm88HUSs2TQghRSMVjmYQ'},
        {'title': 'Noodgeval', 'artist': 'Goldband', 'spotifyId': '2LcmbuYX7tyR4DWy3b273L'},
        {'title': 'Smoorverliefd', 'artist': 'Doe Maar', 'spotifyId': '1dsHyPC2GooTeavfxiOW9M'},
        {'title': 'Reünie', 'artist': 'Snelle', 'spotifyId': '306Z2K49dZ19jO4tT5YvQk'}
    ]

    existing_path = TURBO_DIR / 'nl_probe_songs.json'
    existing_songs = {}
    if existing_path.exists():
        try:
            with open(existing_path, 'r', encoding='utf-8') as f:
                for s in json.load(f):
                    existing_songs[(s['title'], s['artist'])] = s
        except Exception:
            pass

    probe_songs = []
    for track in curated_tracks:
        key = (track['title'], track['artist'])
        if key in existing_songs and existing_songs[key].get('syncedLyrics'):
            print(f"   [cached] {track['artist']} - {track['title']}")
            probe_songs.append(existing_songs[key])
            continue

        print(f"   Fetching LRCLIB: {track['artist']} - {track['title']}...")
        record = fetch_lrclib_record(track['title'], track['artist'])
        if not record:
            clean_title = track['title'].replace('Ø', 'O').replace('ø', 'o').replace('ü', 'u').replace('é', 'e')
            clean_artist = track['artist'].replace('Ø', 'O').replace('ø', 'o').replace('é', 'e')
            record = fetch_lrclib_record(clean_title, clean_artist)

        if record:
            song_entry = {
                'title': track['title'],
                'artist': track['artist'],
                'spotifyId': track['spotifyId'],
                'lyrics': record.get('lyrics') or '',
                'syncedLyrics': record.get('syncedLyrics') or '',
                'lrclibId': record.get('lrclibId'),
                'lrclibDurationMs': record.get('lrclibDurationMs') or 180000
            }
            probe_songs.append(song_entry)
            print(f"   ✓ Added {track['artist']} - {track['title']} ({record.get('lrclibDurationMs')}ms)")
        else:
            print(f"   ✗ Skipped {track['artist']} - {track['title']} (no lyrics found)")
        time.sleep(2.5)

    with open(existing_path, 'w', encoding='utf-8') as f:
        json.dump(probe_songs, f, ensure_ascii=False, indent=2)
    print(f'   Saved {len(probe_songs)} Dutch probe songs to {existing_path}')


if __name__ == '__main__':
    build_nl_turbo_assets()
    build_nl_probe_songs()
    print('Dutch Turbo assets complete!')
