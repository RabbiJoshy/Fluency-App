#!/usr/bin/env python3
"""Build French Turbo assets, word frequency rank list, and probe songs for Lyrics Translation Mode."""

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
FR_RELEASE = WORKSPACE / 'releases/fr/speech/fr-speech-v7-dual-metadata-v5-20260918/app'
FR_OPENSUBTITLES = WORKSPACE / 'raw/opensubtitles/opensubtitles-v2018-en-fr-2016plus/OpenSubtitles.en-fr.fr'
FR_KAIKKI = WORKSPACE / 'raw/wiktionary/enwiktionary-2026-08-05/kaikki.org-dictionary-French.jsonl'
TURBO_DIR = REPO_ROOT / 'app/turbo'

CURATED_FR_ENTITIES = {
    'stromae': {
        'query': 'stromae',
        'canonicalTitle': 'Stromae',
        'description': 'Belgian singer, rapper, and musician blending hip-hop, electropop, and Belgian chanson',
        'entityType': 'artist',
        'source': 'curated'
    },
    'édith piaf': {
        'query': 'édith piaf',
        'canonicalTitle': 'Édith Piaf',
        'description': "France's iconic national chanter, famed for 'La Vie en rose' and 'Non, je ne regrette rien'",
        'entityType': 'artist',
        'source': 'curated'
    },
    'edith piaf': {
        'query': 'edith piaf',
        'canonicalTitle': 'Édith Piaf',
        'description': "France's iconic national chanter, famed for 'La Vie en rose' and 'Non, je ne regrette rien'",
        'entityType': 'artist',
        'source': 'curated'
    },
    'angèle': {
        'query': 'angèle',
        'canonicalTitle': 'Angèle',
        'description': 'Popular Belgian pop singer-songwriter and musician',
        'entityType': 'artist',
        'source': 'curated'
    },
    'angele': {
        'query': 'angele',
        'canonicalTitle': 'Angèle',
        'description': 'Popular Belgian pop singer-songwriter and musician',
        'entityType': 'artist',
        'source': 'curated'
    },
    'indila': {
        'query': 'indila',
        'canonicalTitle': 'Indila',
        'description': 'French singer and songwriter celebrated for her dramatic, evocative hit "Dernière danse"',
        'entityType': 'artist',
        'source': 'curated'
    },
    'jacques brel': {
        'query': 'jacques brel',
        'canonicalTitle': 'Jacques Brel',
        'description': 'Belgian master of French chanson known for passionate, theatrical poetry and storytelling',
        'entityType': 'artist',
        'source': 'curated'
    },
    'céline dion': {
        'query': 'céline dion',
        'canonicalTitle': 'Céline Dion',
        'description': 'World-renowned Canadian vocalist with celebrated French-language classics by Jean-Jacques Goldman',
        'entityType': 'artist',
        'source': 'curated'
    },
    'celine dion': {
        'query': 'celine dion',
        'canonicalTitle': 'Céline Dion',
        'description': 'World-renowned Canadian vocalist with celebrated French-language classics by Jean-Jacques Goldman',
        'entityType': 'artist',
        'source': 'curated'
    },
    'aya nakamura': {
        'query': 'aya nakamura',
        'canonicalTitle': 'Aya Nakamura',
        'description': 'Malian-French global pop star acclaimed for blending Afrobeat, R&B, and Parisian slang',
        'entityType': 'artist',
        'source': 'curated'
    },
    'gims': {
        'query': 'gims',
        'canonicalTitle': 'Gims',
        'description': 'Congolese-French rapper and singer, former member of Sexion d\'Assaut and chart-topping solo artist',
        'entityType': 'artist',
        'source': 'curated'
    },
    'charles aznavour': {
        'query': 'charles aznavour',
        'canonicalTitle': 'Charles Aznavour',
        'description': 'Legendary French-Armenian singer, lyricist, and actor, crowned the French Frank Sinatra',
        'entityType': 'artist',
        'source': 'curated'
    },
    'zaz': {
        'query': 'zaz',
        'canonicalTitle': 'Zaz',
        'description': 'French singer-songwriter fusing chanson, acoustic jazz, and gypsy swing',
        'entityType': 'artist',
        'source': 'curated'
    },
    'joe dassin': {
        'query': 'joe dassin',
        'canonicalTitle': 'Joe Dassin',
        'description': 'Beloved French-American singer famous for infectious pop-chanson anthems like "Les Champs-Élysées"',
        'entityType': 'artist',
        'source': 'curated'
    },
    'serge gainsbourg': {
        'query': 'serge gainsbourg',
        'canonicalTitle': 'Serge Gainsbourg',
        'description': 'Seminal French singer-songwriter, poet, composer, and avant-garde cultural provocateur',
        'entityType': 'artist',
        'source': 'curated'
    },
    'paris': {
        'query': 'paris',
        'canonicalTitle': 'Paris',
        'description': 'Capital city of France, global center for art, fashion, gastronomy, and culture',
        'entityType': 'place',
        'source': 'curated'
    },
    'bruxelles': {
        'query': 'bruxelles',
        'canonicalTitle': 'Brussels',
        'description': 'Capital of Belgium and major Francophone cultural epicenter',
        'entityType': 'place',
        'source': 'curated'
    },
    'france': {
        'query': 'france',
        'canonicalTitle': 'France',
        'description': 'Country in Western Europe with rich musical, literary, and artistic traditions',
        'entityType': 'place',
        'source': 'curated'
    }
}

CURATED_FR_MWES = {
    'tout de suite': {'expression': 'tout de suite', 'translation': 'right away; immediately', 'source': 'curated'},
    'au fur et à mesure': {'expression': 'au fur et à mesure', 'translation': 'gradually; as one goes along', 'source': 'curated'},
    'en train de': {'expression': 'en train de', 'translation': 'in the middle of; in the process of', 'source': 'curated'},
    'avoir besoin de': {'expression': 'avoir besoin de', 'translation': 'to need', 'source': 'curated'},
    'avoir envie de': {'expression': 'avoir envie de', 'translation': 'to feel like; to want', 'source': 'curated'},
    'au lieu de': {'expression': 'au lieu de', 'translation': 'instead of', 'source': 'curated'},
    "d'ailleurs": {'expression': "d'ailleurs", 'translation': 'besides; by the way', 'source': 'curated'},
    'par exemple': {'expression': 'par exemple', 'translation': 'for example', 'source': 'curated'},
    "c'est-à-dire": {'expression': "c'est-à-dire", 'translation': 'that is to say; namely', 'source': 'curated'},
    'après tout': {'expression': 'après tout', 'translation': 'after all', 'source': 'curated'},
    'de rien': {'expression': 'de rien', 'translation': 'you are welcome', 'source': 'curated'},
    "s'il vous plaît": {'expression': "s'il vous plaît", 'translation': 'please', 'source': 'curated'},
    "s'il te plaît": {'expression': "s'il te plaît", 'translation': 'please', 'source': 'curated'},
    'ne me quitte pas': {'expression': 'ne me quitte pas', 'translation': 'do not leave me', 'source': 'curated'},
    'la vie en rose': {'expression': 'la vie en rose', 'translation': 'life through rose-colored glasses', 'source': 'curated'}
}

FR_ELISIONS = {
    "c'": 'ce',
    "j'": 'je',
    "d'": 'de',
    "l'": 'le',
    "m'": 'me',
    "n'": 'ne',
    "s'": 'se',
    "t'": 'te',
    "qu'": 'que',
    "jusqu'": 'jusque',
    "lorsqu'": 'lorsque',
    "puisqu'": 'puisque',
    "quoiqu'": 'quoique',
    "t'as": 'tu as',
    "t'es": 'tu es',
    'y a': 'il y a',
    "j'suis": 'je suis',
    'chuis': 'je suis',
    "p'tit": 'petit',
    "p'tite": 'petite',
    "d'jà": 'déjà'
}


def build_fr_turbo_assets():
    print('1. Building French vocabulary and frequency ranks...')
    
    # 1. Count speech frequencies from OpenSubtitles
    freq_counter = Counter()
    if FR_OPENSUBTITLES.exists():
        print(f'   Reading OpenSubtitles from {FR_OPENSUBTITLES}...')
        with open(FR_OPENSUBTITLES, 'r', encoding='utf-8') as f:
            for i, line in enumerate(f):
                if i >= 600000:
                    break
                words = re.findall(r"[a-zA-ZÀ-ÿœæ]+(?:['’\-][a-zA-ZÀ-ÿœæ]+)*", line.lower())
                freq_counter.update(words)
        print(f'   Counted {len(freq_counter)} unique words from OpenSubtitles.')

    top_freq_words = [w for w, _ in freq_counter.most_common(50000)]
    ranks_50k = {w: i + 1 for i, w in enumerate(top_freq_words)}

    # 2. Load Kaikki French definitions & morphology
    print(f'   Reading Kaikki French from {FR_KAIKKI}...')
    dictionary = {}
    lemmas_50k = {}

    # Pre-populate from official fr-speech release if present
    vocab_index_path = FR_RELEASE / 'vocabulary.index.json'
    if vocab_index_path.exists():
        with open(vocab_index_path, 'r', encoding='utf-8') as f:
            for card in json.load(f):
                w = card.get('word', '').strip().lower()
                if not w or w in dictionary:
                    continue
                meanings = card.get('meanings', [])
                top_trans = meanings[0].get('translation', '') if meanings else ''
                top_pos = meanings[0].get('pos', '') if meanings else ''
                dictionary[w] = {
                    'id': card.get('id', ''),
                    'rank': card.get('rank', ranks_50k.get(w, 99999)),
                    'polysemous': len(meanings) > 1,
                    'meaning_count': len(meanings),
                    'top_translation': top_trans,
                    'top_pos': top_pos,
                    'meanings': [
                        {'pos': m.get('pos', ''), 'translation': m.get('translation', ''), 'context': m.get('context', '')}
                        for m in meanings
                    ]
                }

    # Stream Kaikki to enrich dictionary and extract verb/noun lemma mappings
    line_count = 0
    with open(FR_KAIKKI, 'r', encoding='utf-8') as f:
        for line in f:
            line_count += 1
            if line_count % 150000 == 0:
                print(f'   Processed {line_count:,} Kaikki lines...')
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

            # Add to dictionary if not yet present and word is in frequent/known set
            if word not in dictionary and glosses:
                rank = ranks_50k.get(word)
                if rank and rank <= 12000:
                    dictionary[word] = {
                        'id': f'card_fr_{word}',
                        'rank': rank,
                        'polysemous': len(glosses) > 1,
                        'meaning_count': len(glosses),
                        'top_translation': glosses[0],
                        'top_pos': pos,
                        'meanings': [{'pos': pos, 'translation': g, 'context': ''} for g in glosses[:3]]
                    }

            # Map inflected forms to lemma
            for form_obj in entry.get('forms', []):
                form_text = form_obj.get('form', '').strip().lower()
                if form_text and form_text != word and ' ' not in form_text and len(form_text) < 30:
                    if form_text not in lemmas_50k:
                        lemmas_50k[form_text] = word

    print(f'   Final French dictionary: {len(dictionary):,} entries')
    print(f'   Final French lemma map: {len(lemmas_50k):,} inflected mappings')

    # Save assets
    turbo_assets = {
        'version': '2.0.0-turbo-fr',
        'language': 'fr',
        'builtAt': datetime.now(timezone.utc).isoformat(),
        'elisions': FR_ELISIONS,
        'mwes': CURATED_FR_MWES,
        'curatedEntities': CURATED_FR_ENTITIES,
        'dictionary': dictionary
    }

    assets_path = TURBO_DIR / 'fr_turbo_assets.json'
    with open(assets_path, 'w', encoding='utf-8') as f:
        json.dump(turbo_assets, f, ensure_ascii=False)
    print(f'   Saved {assets_path} ({os.path.getsize(assets_path):,} bytes)')

    data_50k = {
        'ranks': ranks_50k,
        'lemmas': lemmas_50k
    }
    data_50k_path = TURBO_DIR / 'fr_50k_data.json'
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


def build_fr_probe_songs():
    print('2. Building French probe songs with synchronized lyrics...')

    curated_tracks = [
        {'title': 'Papaoutai', 'artist': 'Stromae', 'spotifyId': '34dx8DACTJsc3rsJdaEIQw'},
        {'title': 'Alors on danse', 'artist': 'Stromae', 'spotifyId': '2GYHyAoLWpkxLVa4oYTVko'},
        {'title': 'La Vie en rose', 'artist': 'Édith Piaf', 'spotifyId': '2ALK3U3XsDzz85bynK1hnt'},
        {'title': 'Non, je ne regrette rien', 'artist': 'Édith Piaf', 'spotifyId': '5cgKosPPj5Cs9a2JQufUc1'},
        {'title': 'Balance ton quoi', 'artist': 'Angèle', 'spotifyId': '46cW6zufU9Woo11TLs2i6X'},
        {'title': 'Dernière danse', 'artist': 'Indila', 'spotifyId': '4lsOsGMzO1yCjGVucoWOZ1'},
        {'title': 'Ne me quitte pas', 'artist': 'Jacques Brel', 'spotifyId': '6IRA4KOVbtiGiTdYoEThJN'},
        {'title': "Pour que tu m'aimes encore", 'artist': 'Céline Dion', 'spotifyId': '6qlpXtA29VcxCNgLWR5IWx'},
        {'title': 'Les Champs-Élysées', 'artist': 'Joe Dassin', 'spotifyId': '4VWbPQUPvLes814r6T11Jz'},
        {'title': 'Je veux', 'artist': 'Zaz', 'spotifyId': '734dz1YaFITwawPpM25fSt'},
        {'title': 'La Bohème', 'artist': 'Charles Aznavour', 'spotifyId': '2o0hVSbnkdvDDKKVNaUxnB'},
        {'title': 'Djadja', 'artist': 'Aya Nakamura', 'spotifyId': '7sKDftgGirHWTVFMtJoDoh'},
        {'title': 'Bella', 'artist': 'GIMS', 'spotifyId': '1vELwZM3uBYWd8HrtddD4l'},
        {'title': 'La Javanaise', 'artist': 'Serge Gainsbourg', 'spotifyId': '3WJ1t0l8h8L0tP1k0v4z7c'}
    ]

    existing_path = TURBO_DIR / 'fr_probe_songs.json'
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
            # Fallback retry without diacritics
            clean_title = track['title'].replace('É', 'E').replace('é', 'e').replace('è', 'e').replace('ê', 'e')
            clean_artist = track['artist'].replace('É', 'E').replace('é', 'e').replace('è', 'e')
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
    print(f'   Saved {len(probe_songs)} French probe songs to {existing_path}')


if __name__ == '__main__':
    build_fr_turbo_assets()
    build_fr_probe_songs()
    print('French Turbo assets complete!')
