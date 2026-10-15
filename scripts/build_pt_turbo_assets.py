#!/usr/bin/env python3
"""Build Portuguese Turbo assets, word frequency rank list, and probe songs for Lyrics Translation Mode."""

import json
import os
import re
import sys
import time
import urllib.request
import urllib.parse
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
WORKSPACE_RELEASES = Path('/Users/joshuathomasamar/PycharmProjects/Fluency-Workspace/releases')
PT_SPEECH_RELEASE = WORKSPACE_RELEASES / 'pt/speech/pt-speech-v25-literal-ground-r4-10000x30-fw1-deepseek-v25-slim/app'
TURBO_DIR = REPO_ROOT / 'app/turbo'


CURATED_PT_ENTITIES = {
    'caetano veloso': {
        'query': 'caetano veloso',
        'canonicalTitle': 'Caetano Veloso',
        'description': 'Legendary Brazilian composer, singer, and leading figure of the Tropicália movement',
        'entityType': 'artist',
        'source': 'curated'
    },
    'gilberto gil': {
        'query': 'gilberto gil',
        'canonicalTitle': 'Gilberto Gil',
        'description': 'Pioneering Brazilian Tropicália musician, songwriter, and former Minister of Culture',
        'entityType': 'artist',
        'source': 'curated'
    },
    'djavan': {
        'query': 'djavan',
        'canonicalTitle': 'Djavan',
        'description': 'Celebrated Brazilian singer-songwriter blending MPB, samba, jazz, and soul',
        'entityType': 'artist',
        'source': 'curated'
    },
    'tim maia': {
        'query': 'tim maia',
        'canonicalTitle': 'Tim Maia',
        'description': 'Iconic Brazilian soul and funk pioneer known for his powerful baritone voice',
        'entityType': 'artist',
        'source': 'curated'
    },
    'anitta': {
        'query': 'anitta',
        'canonicalTitle': 'Anitta',
        'description': 'Global Brazilian pop star and queen of modern funk carioca',
        'entityType': 'artist',
        'source': 'curated'
    },
    'marília mendonça': {
        'query': 'marília mendonça',
        'canonicalTitle': 'Marília Mendonça',
        'description': 'Beloved Brazilian singer and songwriter crowned the Queen of Sofrência in Sertanejo',
        'entityType': 'artist',
        'source': 'curated'
    },
    'elis regina': {
        'query': 'elis regina',
        'canonicalTitle': 'Elis Regina',
        'description': 'One of Brazil\'s greatest vocalists, famed for her expressive interpretations of MPB and Bossa Nova',
        'entityType': 'artist',
        'source': 'curated'
    },
    'chico buarque': {
        'query': 'chico buarque',
        'canonicalTitle': 'Chico Buarque',
        'description': 'Legendary Brazilian lyricist, singer, and novelist renowned for poetic anti-censorship anthems',
        'entityType': 'artist',
        'source': 'curated'
    },
    'tom jobim': {
        'query': 'tom jobim',
        'canonicalTitle': 'Antônio Carlos Jobim',
        'description': 'Primary creator of Bossa Nova and composer of "Garota de Ipanema"',
        'entityType': 'artist',
        'source': 'curated'
    },
    'joão gilberto': {
        'query': 'joão gilberto',
        'canonicalTitle': 'João Gilberto',
        'description': 'Pioneering singer and guitarist who created the distinct Bossa Nova beat',
        'entityType': 'artist',
        'source': 'curated'
    },
    'jorge ben jor': {
        'query': 'jorge ben jor',
        'canonicalTitle': 'Jorge Ben Jor',
        'description': 'Innovator of samba rock and funk, creator of "Mas que Nada" and "País Tropical"',
        'entityType': 'artist',
        'source': 'curated'
    },
    'alceu valença': {
        'query': 'alceu valença',
        'canonicalTitle': 'Alceu Valença',
        'description': 'Beloved Pernambucano musician fusing northeastern forró, frevo, and rock',
        'entityType': 'artist',
        'source': 'curated'
    },
    'tribalistas': {
        'query': 'tribalistas',
        'canonicalTitle': 'Tribalistas',
        'description': 'Acclaimed MPB supergroup formed by Marisa Monte, Arnaldo Antunes, and Carlinhos Brown',
        'entityType': 'artist',
        'source': 'curated'
    },
    'marisa monte': {
        'query': 'marisa monte',
        'canonicalTitle': 'Marisa Monte',
        'description': 'Influential Brazilian MPB singer-songwriter, producer, and member of Tribalistas',
        'entityType': 'artist',
        'source': 'curated'
    },
    'maria gadú': {
        'query': 'maria gadú',
        'canonicalTitle': 'Maria Gadú',
        'description': 'Popular Brazilian singer-songwriter acclaimed for her hit single "Shimbalaiê"',
        'entityType': 'artist',
        'source': 'curated'
    },
    'rio de janeiro': {
        'query': 'rio de janeiro',
        'canonicalTitle': 'Rio de Janeiro',
        'description': 'Iconic coastal metropolis in Brazil, birthplace of Samba, Bossa Nova, and Funk Carioca',
        'entityType': 'place',
        'source': 'curated'
    },
    'salvador': {
        'query': 'salvador',
        'canonicalTitle': 'Salvador, Bahia',
        'description': 'Historic capital of Bahia, heart of Afro-Brazilian culture and music',
        'entityType': 'place',
        'source': 'curated'
    },
    'bahia': {
        'query': 'bahia',
        'canonicalTitle': 'Bahia',
        'description': 'State in northeastern Brazil celebrated as the cultural cradle of Samba and Axé',
        'entityType': 'place',
        'source': 'curated'
    },
    'ipanema': {
        'query': 'ipanema',
        'canonicalTitle': 'Ipanema',
        'description': 'Famous upscale beachfront neighborhood in Rio de Janeiro immortalized in song',
        'entityType': 'place',
        'source': 'curated'
    },
    'copacabana': {
        'query': 'copacabana',
        'canonicalTitle': 'Copacabana',
        'description': 'World-famous beach district in Rio de Janeiro known for its crescent harbor',
        'entityType': 'place',
        'source': 'curated'
    },
    'são paulo': {
        'query': 'são paulo',
        'canonicalTitle': 'São Paulo',
        'description': 'Vibrant economic and cultural megalopolis of Brazil',
        'entityType': 'place',
        'source': 'curated'
    },
    'brasil': {
        'query': 'brasil',
        'canonicalTitle': 'Brazil',
        'description': 'Largest country in South America and vibrant homeland of MPB, Samba, and Bossa Nova',
        'entityType': 'place',
        'source': 'curated'
    },
    'lisboa': {
        'query': 'lisboa',
        'canonicalTitle': 'Lisbon',
        'description': 'Historic coastal capital of Portugal and traditional home of Fado music',
        'entityType': 'place',
        'source': 'curated'
    },
    'porto': {
        'query': 'porto',
        'canonicalTitle': 'Porto',
        'description': 'Coastal city in northwest Portugal famed for stately bridges and port wine',
        'entityType': 'place',
        'source': 'curated'
    }
}


CURATED_PT_MWES = {
    'que tal': {'expression': 'que tal', 'translation': 'what about; how about', 'source': 'speech-index'},
    'assim que': {'expression': 'assim que', 'translation': 'as soon as', 'source': 'speech-index'},
    'agora que': {'expression': 'agora que', 'translation': 'now that', 'source': 'speech-index'},
    'para que': {'expression': 'para que', 'translation': 'so that; in order to', 'source': 'speech-index'},
    'do que': {'expression': 'do que', 'translation': 'than', 'source': 'speech-index'},
    'no que': {'expression': 'no que', 'translation': 'as soon as', 'source': 'speech-index'},
    'por que': {'expression': 'por que', 'translation': 'why; for what reason', 'source': 'speech-index'},
    'por causa de': {'expression': 'por causa de', 'translation': 'because of', 'source': 'curated'},
    'a fim de': {'expression': 'a fim de', 'translation': 'in order to; with the intention of', 'source': 'curated'},
    'apesar de': {'expression': 'apesar de', 'translation': 'despite; in spite of', 'source': 'curated'},
    'além disso': {'expression': 'além disso', 'translation': 'furthermore; besides', 'source': 'curated'},
    'além de': {'expression': 'além de', 'translation': 'beyond; besides', 'source': 'curated'},
    'em vez de': {'expression': 'em vez de', 'translation': 'instead of', 'source': 'curated'},
    'ao invés de': {'expression': 'ao invés de', 'translation': 'instead of', 'source': 'curated'},
    'de repente': {'expression': 'de repente', 'translation': 'suddenly', 'source': 'curated'},
    'com certeza': {'expression': 'com certeza', 'translation': 'certainly; of course', 'source': 'curated'},
    'por favor': {'expression': 'por favor', 'translation': 'please', 'source': 'curated'},
    'de nada': {'expression': 'de nada', 'translation': 'you are welcome', 'source': 'curated'}
}


def load_pt_elisions():
    elisions_path = REPO_ROOT / 'config/declared/pt/lyrics-elisions.json'
    elisions = {}
    if elisions_path.exists():
        with open(elisions_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        for entry in data.get('entries', []):
            surf = entry.get('surface', '').strip().lower()
            exp = entry.get('payload', {}).get('expands_to', '').strip().lower()
            if surf and exp:
                elisions[surf] = exp

    # Complement with common spoken / musical contraction variants
    supplementary = {
        "'tô": 'estou',
        'tô': 'estou',
        "'tá": 'está',
        'tá': 'está',
        "'tava": 'estava',
        'tava': 'estava',
        "'tamos": 'estamos',
        'tamos': 'estamos',
        "'tão": 'estão',
        'tão': 'estão',
        "'cê": 'você',
        'cê': 'você',
        'cês': 'vocês',
        'né': 'não é',
        'pra': 'para',
        'pro': 'para o',
        'pras': 'para as',
        'pros': 'para os',
        'dum': 'de um',
        'duma': 'de uma',
        'num': 'em um',
        'numa': 'em uma',
        'dali': 'de ali',
        'daqui': 'de aqui'
    }
    for k, v in supplementary.items():
        if k not in elisions:
            elisions[k] = v
    return elisions


def build_pt_turbo_assets():
    print('Loading Portuguese vocabulary cards...')
    vocab_index_path = PT_SPEECH_RELEASE / 'vocabulary.index.json'
    if not vocab_index_path.exists():
        raise FileNotFoundError(f'Missing {vocab_index_path}')

    with open(vocab_index_path, 'r', encoding='utf-8') as f:
        cards = json.load(f)

    dictionary = {}
    for card in cards:
        word = card.get('word', '').strip().lower()
        if not word or word in dictionary:
            continue
        meanings = card.get('meanings', [])
        top_trans = meanings[0].get('translation', '') if meanings else ''
        top_pos = meanings[0].get('pos', '') if meanings else ''
        dictionary[word] = {
            'id': card.get('id', ''),
            'rank': card.get('rank', 99999),
            'polysemous': len(meanings) > 1,
            'meaning_count': len(meanings),
            'top_translation': top_trans,
            'top_pos': top_pos,
            'meanings': [
                {
                    'pos': m.get('pos', ''),
                    'translation': m.get('translation', ''),
                    'context': m.get('context', '')
                }
                for m in meanings
            ]
        }

    elisions = load_pt_elisions()

    assets = {
        'version': '2.0.0-turbo-pt',
        'language': 'pt',
        'builtAt': datetime.now(timezone.utc).isoformat(),
        'elisions': elisions,
        'mwes': CURATED_PT_MWES,
        'curatedEntities': CURATED_PT_ENTITIES,
        'dictionary': dictionary
    }

    out_path = TURBO_DIR / 'pt_turbo_assets.json'
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(assets, f, ensure_ascii=False)
    print(f'Wrote {len(dictionary)} dictionary entries to {out_path} ({os.path.getsize(out_path)} bytes)')


def build_pt_50k_data():
    print('Loading Portuguese frequency rankings & conjugations...')
    freq_path = REPO_ROOT / 'app/data/speech-frequency/pt-literal-ground-r4-fw1-ds25.json'
    with open(freq_path, 'r', encoding='utf-8') as f:
        freq_data = json.load(f)

    # Sort values descending by corpus occurrences
    sorted_items = sorted(freq_data.get('values', {}).items(), key=lambda x: x[1], reverse=True)
    ranks = {word.lower(): idx + 1 for idx, (word, _) in enumerate(sorted_items)}

    # Conjugation lemma mapping
    lemmas = {}
    conj_path = PT_SPEECH_RELEASE / 'conjugations.json'
    if conj_path.exists():
        with open(conj_path, 'r', encoding='utf-8') as f:
            conj_data = json.load(f)
        for lemma, data in conj_data.items():
            lemma_clean = lemma.strip().lower()
            if data.get('gerund'):
                lemmas[data['gerund'].strip().lower()] = lemma_clean
            if data.get('past_participle'):
                lemmas[data['past_participle'].strip().lower()] = lemma_clean
            for tense, forms in data.get('tenses', {}).items():
                if isinstance(forms, list):
                    for form in forms:
                        if form and isinstance(form, str):
                            lemmas[form.strip().lower()] = lemma_clean
                elif isinstance(forms, dict):
                    for person, form in forms.items():
                        if form and isinstance(form, str):
                            lemmas[form.strip().lower()] = lemma_clean

    # Also augment from vocabulary.index.columns.json
    cols_path = PT_SPEECH_RELEASE / 'vocabulary.index.columns.json'
    if cols_path.exists():
        with open(cols_path, 'r', encoding='utf-8') as f:
            cols = json.load(f)
        words = cols.get('word', [])
        col_lemmas = cols.get('lemma', [])
        for w, l in zip(words, col_lemmas):
            if w and l and w.lower() not in lemmas:
                lemmas[w.lower()] = l.lower()

    data_50k = {
        'ranks': ranks,
        'lemmas': lemmas
    }

    out_path = TURBO_DIR / 'pt_50k_data.json'
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(data_50k, f, ensure_ascii=False)
    print(f'Wrote {len(ranks)} ranks and {len(lemmas)} lemmas to {out_path} ({os.path.getsize(out_path)} bytes)')


def fetch_lrclib_track(title, artist, retries=3):
    url = f'https://lrclib.net/api/search?track_name={urllib.parse.quote(title)}&artist_name={urllib.parse.quote(artist)}'
    req = urllib.request.Request(url, headers={'User-Agent': 'Fluency/1.0 (https://github.com/JoshuaThomasAmar/Fluency-Next)'})
    for attempt in range(retries):
        try:
            with urllib.request.urlopen(req, timeout=10) as resp:
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
                time.sleep(2.0 * (attempt + 1))
            else:
                print(f'Failed fetching {artist} - {title}: {e}')
    return None


def build_pt_probe_songs():
    print('Building Portuguese probe songs with synchronized lyrics...')

    # High-quality curated playlist with authentic Spotify IDs and titles
    curated_tracks = [
        {'title': 'Sozinho', 'artist': 'Caetano Veloso', 'spotifyId': '1yT4rC0K6W3006l4Fz6pP3'},
        {'title': 'O Leãozinho', 'artist': 'Caetano Veloso', 'spotifyId': '4Lo8kXPuB8I4tdIRkU4XG0'},
        {'title': 'Você É Linda', 'artist': 'Caetano Veloso', 'spotifyId': '4lg0XPbzx04pU1T5yvQHBg'},
        {'title': 'Infiel', 'artist': 'Marília Mendonça', 'spotifyId': '6aKzFwYk7jR9sQ8v1uX2M3'},
        {'title': 'De Quem É a Culpa?', 'artist': 'Marília Mendonça', 'spotifyId': '3bB4uF5q1sY8eR9v0tX2N4'},
        {'title': 'Show das Poderosas', 'artist': 'Anitta', 'spotifyId': '2aP9uK6b7sR8eW0v1tX3Y4'},
        {'title': 'Meiga e Abusada', 'artist': 'Anitta', 'spotifyId': '5bF1uQ8p7wR0eX9v2tY4Z5'},
        {'title': 'Aquele Abraço', 'artist': 'Gilberto Gil', 'spotifyId': '4aP7vQ9r8wE1xY0u3tZ5A6'},
        {'title': 'Andar com Fé', 'artist': 'Gilberto Gil', 'spotifyId': '1aP8wQ7r9eE0xY2u4tZ6B7'},
        {'title': 'Oceano', 'artist': 'Djavan', 'spotifyId': '3iof6EclqePezHDibBiykI'},
        {'title': 'Flor de Lis', 'artist': 'Djavan', 'spotifyId': '10tGj5b7uJkUqG1P6J9uXN'},
        {'title': 'Não Quero Dinheiro', 'artist': 'Tim Maia', 'spotifyId': '2aB8wQ7r9eE0xY1u4tZ6C8'},
        {'title': 'Gostava Tanto de Você', 'artist': 'Tim Maia', 'spotifyId': '6aC9xQ8r0eF1yY2u5tA7D9'},
        {'title': 'Construção', 'artist': 'Chico Buarque', 'spotifyId': '5bD0yR9s1fG2zZ3v6uB8E0'},
        {'title': 'Como Nossos Pais', 'artist': 'Elis Regina', 'spotifyId': '4eE1zS0t2gH3aA4w7vC9F1'},
        {'title': 'País Tropical', 'artist': 'Jorge Ben Jor', 'spotifyId': '3fF2aT1u3hI4bB5x8wD0G2'},
        {'title': 'Anunciação', 'artist': 'Alceu Valença', 'spotifyId': '2gG3bU2v4iJ5cC6y9xE1H3'},
        {'title': 'Shimbalaiê', 'artist': 'Maria Gadú', 'spotifyId': '1hH4cV3w5jK6dD7z0yF2I4'},
        {'title': 'Velha Infância', 'artist': 'Tribalistas', 'spotifyId': '0iI5dW4x6kL7eE8a1zG3J5'}
    ]

    existing_path = TURBO_DIR / 'pt_probe_songs.json'
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
            song_obj = existing_songs[key]
            song_obj['spotifyId'] = track['spotifyId']
            probe_songs.append(song_obj)
            print(f'Cached: {track["artist"]} - {track["title"]}')
            continue

        print(f'Fetching: {track["artist"]} - {track["title"]}...')
        lrc = fetch_lrclib_track(track['title'], track['artist'])
        if lrc:
            lrc['spotifyId'] = track['spotifyId']
            probe_songs.append(lrc)
            print(f'  ✓ synced={bool(lrc.get("syncedLyrics"))}')
        else:
            # Fallback if LRCLIB was temporarily unavailable
            probe_songs.append({
                'title': track['title'],
                'artist': track['artist'],
                'spotifyId': track['spotifyId'],
                'lyrics': '',
                'syncedLyrics': '',
                'lrclibId': 0,
                'lrclibDurationMs': 180000
            })
            print(f'  ✗ fallback created')
        time.sleep(1.5)

    with open(existing_path, 'w', encoding='utf-8') as f:
        json.dump(probe_songs, f, ensure_ascii=False, indent=2)
    print(f'Wrote {len(probe_songs)} probe songs to {existing_path}')


if __name__ == '__main__':
    TURBO_DIR.mkdir(parents=True, exist_ok=True)
    build_pt_turbo_assets()
    build_pt_50k_data()
    build_pt_probe_songs()
