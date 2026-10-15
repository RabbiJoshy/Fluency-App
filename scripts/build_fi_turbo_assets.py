#!/usr/bin/env python3
"""Build Finnish Turbo assets, word frequency rank list, and probe songs for Lyrics Translation Mode."""

import gzip
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
FI_RELEASE = WORKSPACE / 'releases/fi/speech/fi-speech-v21-2000x30-slim/app'
FI_FREQUENCY = REPO_ROOT / 'app/data/speech-frequency/fi.json'
FI_KAIKKI = WORKSPACE / 'raw/wiktionary/enwiktionary-2026-09-26/kaikki.org-dictionary-Finnish.jsonl.gz'
TURBO_DIR = REPO_ROOT / 'app/turbo'

CURATED_FI_ENTITIES = {
    'käärijä': {
        'query': 'käärijä',
        'canonicalTitle': 'Käärijä',
        'description': 'Finnish rapper, singer, and songwriter who took the world by storm with "Cha Cha Cha"',
        'entityType': 'artist',
        'source': 'curated'
    },
    'kaarija': {
        'query': 'kaarija',
        'canonicalTitle': 'Käärijä',
        'description': 'Finnish rapper, singer, and songwriter who took the world by storm with "Cha Cha Cha"',
        'entityType': 'artist',
        'source': 'curated'
    },
    'behm': {
        'query': 'behm',
        'canonicalTitle': 'BEHM',
        'description': 'Multi-award-winning Finnish singer-songwriter celebrated for emotional folk-pop ballads like "Hei rakas"',
        'entityType': 'artist',
        'source': 'curated'
    },
    'haloo helsinki!': {
        'query': 'haloo helsinki!',
        'canonicalTitle': 'Haloo Helsinki!',
        'description': 'One of the most successful Finnish pop-rock bands in modern music history',
        'entityType': 'artist',
        'source': 'curated'
    },
    'haloo helsinki': {
        'query': 'haloo helsinki',
        'canonicalTitle': 'Haloo Helsinki!',
        'description': 'One of the most successful Finnish pop-rock bands in modern music history',
        'entityType': 'artist',
        'source': 'curated'
    },
    'jvg': {
        'query': 'jvg',
        'canonicalTitle': 'JVG',
        'description': 'Record-breaking Finnish rap duo famed for energetic summer anthems and stadium shows',
        'entityType': 'artist',
        'source': 'curated'
    },
    'antti tuisku': {
        'query': 'antti tuisku',
        'canonicalTitle': 'Antti Tuisku',
        'description': 'King of Finnish modern pop known for flamboyant performances and innovative dance tracks',
        'entityType': 'artist',
        'source': 'curated'
    },
    'jenni vartiainen': {
        'query': 'jenni vartiainen',
        'canonicalTitle': 'Jenni Vartiainen',
        'description': 'Acclaimed Finnish pop singer famed for cinematic, melancholic vocal masterpieces',
        'entityType': 'artist',
        'source': 'curated'
    },
    'ultra bra': {
        'query': 'ultra bra',
        'canonicalTitle': 'Ultra Bra',
        'description': 'Iconic 1990s Finnish indie pop ensemble revered for political, literary lyrics and brass arrangements',
        'entityType': 'artist',
        'source': 'curated'
    },
    'nightwish': {
        'query': 'nightwish',
        'canonicalTitle': 'Nightwish',
        'description': 'Legendary Finnish symphonic metal band from Kitee, internationally famous for epic compositions',
        'entityType': 'artist',
        'source': 'curated'
    },
    'helsinki': {
        'query': 'helsinki',
        'canonicalTitle': 'Helsinki',
        'description': 'Coastal capital city of Finland and epicenter of Finnish design, education, and music',
        'entityType': 'place',
        'source': 'curated'
    },
    'suomi': {
        'query': 'suomi',
        'canonicalTitle': 'Finland',
        'description': 'Nordic country celebrated for thousands of lakes, sauna culture, and unique Uralic language',
        'entityType': 'place',
        'source': 'curated'
    }
}

CURATED_FI_MWES = {
    'ottaa huomioon': {'expression': 'ottaa huomioon', 'translation': 'to take into account; to consider', 'source': 'curated'},
    'pitää paikkansa': {'expression': 'pitää paikkansa', 'translation': 'to hold true; to be correct', 'source': 'curated'},
    'kaiken kaikkiaan': {'expression': 'kaiken kaikkiaan', 'translation': 'all in all; altogether', 'source': 'curated'},
    'loppujen lopuksi': {'expression': 'loppujen lopuksi', 'translation': 'in the end; ultimately', 'source': 'curated'},
    'ennen kaikkea': {'expression': 'ennen kaikkea', 'translation': 'above all; first and foremost', 'source': 'curated'},
    'itse asiassa': {'expression': 'itse asiassa', 'translation': 'in fact; as a matter of fact', 'source': 'curated'},
    'ole hyvä': {'expression': 'ole hyvä', 'translation': 'you are welcome; here you go', 'source': 'curated'},
    'ei kestä': {'expression': 'ei kestä', 'translation': 'don\'t mention it; you are welcome', 'source': 'curated'},
    'mitä kuuluu': {'expression': 'mitä kuuluu', 'translation': 'how are you; what\'s up', 'source': 'curated'},
    'hyvää päivää': {'expression': 'hyvää päivää', 'translation': 'good day; hello', 'source': 'curated'}
}

FI_ELISIONS = {
    'mä': 'minä',
    'sä': 'sinä',
    'se': 'hän',
    'me': 'me',
    'te': 'te',
    'he': 'he',
    'oot': 'olet',
    'oon': 'olen',
    'onks': 'onko',
    'ei oo': 'ei ole',
    'mut': 'mutta',
    'sit': 'sitten',
    'nii': 'niin',
    'meiän': 'meidän',
    'teijän': 'teidän',
    'tollanen': 'tuollainen',
    'tällanen': 'tällainen'
}


def build_fi_turbo_assets():
    print('1. Building Finnish vocabulary and frequency ranks...')
    
    # 1. Load speech frequencies from fi.json
    ranks_50k = {}
    if FI_FREQUENCY.exists():
        print(f'   Loading Finnish frequency from {FI_FREQUENCY}...')
        with open(FI_FREQUENCY, 'r', encoding='utf-8') as f:
            freq_data = json.load(f)
        sorted_items = sorted(freq_data.get('values', {}).items(), key=lambda x: x[1], reverse=True)
        ranks_50k = {w.lower(): idx + 1 for idx, (w, _) in enumerate(sorted_items)}
        print(f'   Loaded {len(ranks_50k):,} frequency ranks.')

    # 2. Load release vocabulary
    dictionary = {}
    lemmas_50k = {}

    vocab_index_path = FI_RELEASE / 'vocabulary.index.json'
    if vocab_index_path.exists():
        print(f'   Loading release cards from {vocab_index_path}...')
        with open(vocab_index_path, 'r', encoding='utf-8') as f:
            cards = json.load(f)
        for i, card in enumerate(cards):
            w = card.get('word', '').strip().lower()
            if not w or w in dictionary:
                continue
            rank = card.get('rank', ranks_50k.get(w, i + 1))
            if w not in ranks_50k:
                ranks_50k[w] = rank
            meanings = card.get('meanings', [])
            top_trans = meanings[0].get('translation', '') if meanings else ''
            top_pos = meanings[0].get('pos', '') if meanings else ''
            dictionary[w] = {
                'id': card.get('id', f'card_fi_{w}'),
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

    # 3. Stream Kaikki Finnish for morphology and extra vocabulary
    if FI_KAIKKI.exists():
        print(f'   Streaming Kaikki Finnish from {FI_KAIKKI}...')
        line_count = 0
        with gzip.open(FI_KAIKKI, 'rt', encoding='utf-8') as f:
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
                    if rank and rank <= 8000:
                        dictionary[word] = {
                            'id': f'card_fi_{word}',
                            'rank': rank,
                            'polysemous': len(glosses) > 1,
                            'meaning_count': len(glosses),
                            'top_translation': glosses[0],
                            'top_pos': pos,
                            'meanings': [{'pos': pos, 'translation': g, 'context': ''} for g in glosses[:3]]
                        }

                # Map noun cases and verb conjugations to lemma for known dictionary words
                if word in dictionary:
                    for form_obj in entry.get('forms', []):
                        form_text = form_obj.get('form', '').strip().lower()
                        if form_text and form_text != word and ' ' not in form_text and len(form_text) < 30:
                            if form_text not in lemmas_50k:
                                lemmas_50k[form_text] = word

    print(f'   Final Finnish dictionary: {len(dictionary):,} entries')
    print(f'   Final Finnish lemma map: {len(lemmas_50k):,} inflected mappings')

    turbo_assets = {
        'version': '2.0.0-turbo-fi',
        'language': 'fi',
        'builtAt': datetime.now(timezone.utc).isoformat(),
        'elisions': FI_ELISIONS,
        'mwes': CURATED_FI_MWES,
        'curatedEntities': CURATED_FI_ENTITIES,
        'dictionary': dictionary
    }

    assets_path = TURBO_DIR / 'fi_turbo_assets.json'
    with open(assets_path, 'w', encoding='utf-8') as f:
        json.dump(turbo_assets, f, ensure_ascii=False)
    print(f'   Saved {assets_path} ({os.path.getsize(assets_path):,} bytes)')

    data_50k = {
        'ranks': ranks_50k,
        'lemmas': lemmas_50k
    }
    data_50k_path = TURBO_DIR / 'fi_50k_data.json'
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


def build_fi_probe_songs():
    print('2. Building Finnish probe songs with synchronized lyrics...')

    curated_tracks = [
        {'title': 'Cha Cha Cha', 'artist': 'Käärijä', 'spotifyId': '5RX8T3EoTuXcybAxe6oPAw'},
        {'title': 'Hei rakas', 'artist': 'BEHM', 'spotifyId': '0tc8HGXosQDC8TTAaON1TP'},
        {'title': 'Tarkenee', 'artist': 'JVG', 'spotifyId': '3G9gUGRgM4lB2ebVPUcMKI'},
        {'title': 'Missä muruseni on', 'artist': 'Jenni Vartiainen', 'spotifyId': '4UtPYQoErxiBOT4DImpxcX'},
        {'title': 'Kuussa tuulee', 'artist': 'Haloo Helsinki!', 'spotifyId': '01A2B3C4D5E6F7G8H9I0J1'},
        {'title': 'Peto on irti', 'artist': 'Antti Tuisku', 'spotifyId': '12B3C4D5E6F7G8H9I0J1K2'},
        {'title': 'Maailman toisella puolen', 'artist': 'Haloo Helsinki!', 'spotifyId': '23C4D5E6F7G8H9I0J1K2L3'}
    ]

    existing_path = TURBO_DIR / 'fi_probe_songs.json'
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
            clean_title = track['title'].replace('ä', 'a').replace('ö', 'o').replace('!', '')
            clean_artist = track['artist'].replace('ä', 'a').replace('ö', 'o').replace('!', '')
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
    print(f'   Saved {len(probe_songs)} Finnish probe songs to {existing_path}')


if __name__ == '__main__':
    build_fi_turbo_assets()
    build_fi_probe_songs()
    print('Finnish Turbo assets complete!')
