#!/usr/bin/env python3
"""Build the Casa preset from verified subtitle files, without WSD.

Raw subtitle downloads stay outside the repository. A manifest records their
URLs, checksums and episode numbers. Missing episodes require --allow-partial;
forced-only episodes always fail the build
before either published asset is replaced. Numbering uses the original 9+6
episodes for seasons 1–2, then Netflix parts 3–5 (8+8+10 episodes).
"""

import argparse
import hashlib
import importlib.util
import html
import json
import re
import subprocess
import zipfile
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXPECTED = {(season, episode) for season, count in enumerate((9, 6, 8, 8, 10), 1)
            for episode in range(1, count + 1)}
TIME = re.compile(r"(\d\d):(\d\d):(\d\d)[,.](\d{3})")
TOKEN = re.compile(r"[^\W_]+(?:['’\-][^\W_]+)*", re.UNICODE)
REVISION = "offline-30-episodes-v5-all-forms"


def milliseconds(value):
    hours, minutes, seconds, fraction = map(int, TIME.fullmatch(value).groups())
    return ((hours * 60 + minutes) * 60 + seconds) * 1000 + fraction


def parse_srt(data):
    """Keep repeated dialogue occurrences and join wrapped lines within a cue."""
    text = data.decode("utf-8-sig") if data.startswith(b"\xef\xbb\xbf") else None
    if text is None:
        try:
            text = data.decode("utf-8")
        except UnicodeDecodeError:
            text = data.decode("cp1252")
    cues = []
    for block in re.split(r"\n\s*\n", text.replace("\r\n", "\n").strip()):
        lines = block.splitlines()
        clock = next((i for i, line in enumerate(lines) if "-->" in line), None)
        if clock is None:
            continue
        times = TIME.findall(lines[clock])
        if len(times) != 2:
            raise ValueError("Invalid subtitle timestamp")
        start, end = [milliseconds(":".join(t[:3]) + "," + t[3]) for t in times]
        raw = html.unescape(re.sub(r"<[^>]*>|\{\\[^}]*\}", "", " ".join(lines[clock + 1:])))
        # Captions and music lyrics aren't spoken Spanish examples.
        if "♪" in raw or "♫" in raw:
            continue
        raw = re.sub(r"\[[^\]]*\]|\([^)]*\)", " ", raw)
        raw = re.sub(r"^\s*[A-ZÁÉÍÓÚÜÑ ]{2,}:\s*", "", raw)
        cleaned = re.sub(r"\s+", " ", re.sub(r"(^|\s)[–—-]\s*", r"\1", raw)).strip()
        if not TOKEN.search(cleaned) or re.fullmatch(r"UNA SERIE ORIGINAL DE NETFLIX", cleaned, re.I):
            continue
        if end <= start:
            raise ValueError("Subtitle cue has nonpositive duration")
        cues.append({"spanish": cleaned, "start_ms": start, "end_ms": end})
    return cues


def read_source(raw_root, record):
    path = raw_root / record["file"]
    data = path.read_bytes()
    if hashlib.sha256(data).hexdigest() != record["sha256"]:
        raise ValueError(f"Checksum mismatch: {path}")
    if record.get("member"):
        with zipfile.ZipFile(path) as archive:
            data = archive.read(record["member"])
    return data


def load_episodes(manifest, raw_root, allow_partial=False):
    episodes, seen = [], set()
    for record in manifest["episodes"]:
        key = record["season"], record["episode"]
        if key in seen or key not in EXPECTED:
            raise ValueError(f"Duplicate or unexpected episode: {key}")
        seen.add(key)
        cues = parse_srt(read_source(raw_root, record))
        # Reject trailers and forced subtitles containing only foreign dialogue.
        if len(cues) < 200 or max((c["end_ms"] for c in cues), default=0) < 30 * 60 * 1000:
            raise ValueError(f"Incomplete dialogue: {key}")
        episodes.append({"episode": f"S{key[0]:02}E{key[1]:02}", "lines": cues})
    missing = sorted(EXPECTED - seen)
    if missing and not allow_partial:
        raise ValueError("Missing episodes: " + ", ".join(f"S{s:02}E{e:02}" for s, e in missing))
    return sorted(episodes, key=lambda ep: ep["episode"])


def add_translations(episodes, manifest, raw_root):
    """Attach full bilingual example groups without changing Spanish count text."""
    if not manifest.get('translationSources') and not manifest.get('recutTranslationSources'):
        return episodes
    if manifest.get('translationPolicy') != 'precision-timing-v1':
        raise ValueError('Unknown translation matching policy')
    spec = importlib.util.spec_from_file_location('series_precision', ROOT / 'scripts/audit_series_subtitle_sample.py')
    matcher = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(matcher)
    by_key = {ep['episode']: ep for ep in episodes}
    seen = set()
    for record in manifest.get('translationSources', []):
        key = f"S{record['season']:02}E{record['episode']:02}"
        if key in seen or key not in by_key:
            raise ValueError(f'Duplicate or absent translation episode: {key}')
        if record['season'] in manifest.get('translationExclusions', {}).get('seasons', []):
            raise ValueError(f'Translations are excluded for {key}')
        seen.add(key)
        episode = by_key[key]
        english = parse_srt(read_source(raw_root, record))
        if len(english) < 200:
            raise ValueError(f'Incomplete English subtitles: {key}')
        fit = matcher.fit_episode(episode['lines'], english)
        groups = matcher.accepted_groups(episode['lines'], english, fit)
        blocked = [r for r in manifest.get('blockedTranslations', []) if r['episode'] == key and r.get('sourceSha256', record['sha256']) == record['sha256']]
        for group in groups:
            if any(group['spanish_start'] < r['end'] and group['spanish_end'] > r['start'] for r in blocked):
                continue
            translation = {'spanish': group['spanish'], 'english': group['english'],
                           'start_ms': group['start_ms'], 'end_ms': group['end_ms'],
                           'source': record.get('page', record['url']),
                           'sourceSha256': record['sha256'], 'policy': manifest['translationPolicy']}
            for i in range(group['spanish_start'], group['spanish_end']):
                episode['lines'][i]['translation'] = translation
    return add_recut_translations(episodes, manifest, raw_root, matcher)


def dialogue_key(text):
    """Exact word identity; punctuation and subtitle wrapping may differ."""
    return tuple(TOKEN.findall(text.lower().replace('’', "'")))


def add_recut_translations(episodes, manifest, raw_root, matcher):
    """Bridge Netflix examples onto unique whole-cue spans in the original cut.

    Timing is checked within the Netflix bilingual pair, never between different
    edits. Only an exact, unique Spanish word sequence can cross the cut boundary.
    The original cues, occurrence counts and episode credits remain authoritative.
    """
    from collections import defaultdict
    index = defaultdict(list)
    for episode in episodes:
        if episode['episode'][:3] not in ('S01', 'S02'):
            continue
        lines = episode['lines']
        for start in range(len(lines)):
            text = []
            for end in range(start, min(start + 6, len(lines))):
                text.append(lines[end]['spanish'])
                key = dialogue_key(' '.join(text))
                if 6 <= len(key) <= 80:
                    index[key].append((episode, start, end + 1))
    seen = set()
    expected = {f'S{season:02}E{episode:02}' for season, count in ((1, 13), (2, 9))
                for episode in range(1, count + 1)}
    for record in manifest.get('recutTranslationSources', []):
        identity = record['episode']
        if identity in seen or identity not in expected or record['cut'] != 'netflix-13+9':
            raise ValueError(f'Duplicate or unknown recut translation source: {identity}')
        seen.add(identity)
        spanish = parse_srt(read_source(raw_root, record['spanish']))
        english = parse_srt(read_source(raw_root, record['english']))
        if min(len(spanish), len(english)) < 200:
            raise ValueError(f'Incomplete recut source: {identity}')
        groups = matcher.accepted_groups(spanish, english, matcher.fit_episode(spanish, english))
        for group in groups:
            if any(group['spanish_start'] < span['end'] and group['spanish_end'] > span['start']
                   for span in record.get('blockedSpans', [])):
                continue
            matches = index.get(dialogue_key(group['spanish']), [])
            if len(matches) != 1:
                continue
            episode, start, end = matches[0]
            lines = episode['lines'][start:end]
            if any(line.get('translation') for line in lines):
                continue
            translation = {
                'spanish': ' '.join(line['spanish'] for line in lines),
                'english': group['english'],
                'start_ms': lines[0]['start_ms'], 'end_ms': lines[-1]['end_ms'],
                'source': record['english']['page'],
                'sourceSha256': record['english']['sha256'],
                'spanishSourceSha256': record['spanish']['sha256'],
                'sourceEpisode': identity, 'sourceCut': record['cut'],
                'source_start_ms': group['start_ms'], 'source_end_ms': group['end_ms'],
                'policy': manifest['translationPolicy'], 'bridgePolicy': 'unique-exact-span-v1'
            }
            for line in lines:
                line['translation'] = translation
    return episodes


def build(episodes, inventory, manifest, *, include_all=False):
    title = manifest.get('title', 'La Casa de Papel')
    series_id = manifest.get('seriesId', 'la-casa-de-papel')
    surfaces, candidates, token_count = {}, {}, 0
    for ep in episodes:
        for line in ep["lines"]:
            tokens = TOKEN.findall(line["spanish"].lower().replace("’", "'"))
            token_count += len(tokens)
            for word, count in Counter(tokens).items():
                if not include_all and word not in inventory:
                    continue
                entry = surfaces.setdefault(word, {"count": 0, "lines": []})
                entry["count"] += count
                translated = line.get('translation')
                example = {"text": translated['spanish'] if translated else line["spanish"],
                           "song": ep["episode"], "artist": title}
                if translated:
                    example.update(english=translated['english'], start_ms=translated['start_ms'],
                                   end_ms=translated['end_ms'], translationSource=translated['source'],
                                   translationPolicy=translated['policy'])
                by_season = candidates.setdefault(word, {})
                choices = by_season.setdefault(ep["episode"][:3], [])
                if not any(e["text"] == example["text"] for e in choices):
                    choices.append(example)
                    choices.sort(key=lambda e: (not bool(e.get('english')), not bool(re.search(r'[.!?…]["\u201d]?$' , e["text"])),
                                                 not 4 <= len(TOKEN.findall(e["text"])) <= 35))
                    del choices[5:]
    # Translated examples first, with season diversity within each priority tier.
    for word, by_season in candidates.items():
        selected = surfaces[word]['lines']
        for translated in (True, False):
            tiers = {season: [e for e in choices if bool(e.get('english')) == translated]
                     for season, choices in by_season.items()}
            for i in range(5):
                for season in sorted(tiers):
                    choices = tiers[season]
                    if i < len(choices) and len(selected) < 5 and not any(e['text'] == choices[i]['text'] for e in selected):
                        selected.append(choices[i])
    actual = {ep["episode"] for ep in episodes}
    expected = {f"S{s:02}E{e:02}" for s, e in EXPECTED}
    coverage = {"episodes": len(episodes), "seasons": sorted({int(ep["episode"][1:3]) for ep in episodes}),
                "numbering": manifest["numbering"], "complete": actual == expected,
                "missing": sorted(expected - actual), "exampleTranslations": "unavailable"}
    translated_groups = {(ep['episode'], line['translation']['start_ms'], line['translation']['end_ms'])
                         for ep in episodes for line in ep['lines'] if line.get('translation')}
    if translated_groups:
        coverage.update(exampleTranslations='partial', translatedEpisodes=len({g[0] for g in translated_groups}),
                        translatedGroups=len(translated_groups), translationPolicy=manifest['translationPolicy'],
                        cardsWithTranslatedExamples=sum(any(e.get('english') for e in row['lines']) for row in surfaces.values()))
    dialogue = {"series_id": series_id, "title": title, "language": "spanish",
                "episodes_count": len(episodes), "total_lines_count": sum(len(e["lines"]) for e in episodes),
                "coverage": coverage, "episodes": episodes}
    deck = {"id": "live", "presetRevision": REVISION, "sourceKind": "series",
            "playlistId": series_id, "playlistName": title, "language": "spanish",
            "builtAt": manifest["retrievedAt"], "trackCount": len(episodes), "lyricsTrackCount": len(episodes),
            "tokenCount": token_count, "matchedCount": len(surfaces), "coverage": coverage, "surfaces": surfaces}
    return dialogue, deck


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--raw-root", type=Path, required=True)
    parser.add_argument("--allow-partial", action="store_true", help="Publish an explicitly labelled partial sample")
    args = parser.parse_args()
    manifest = json.loads(args.manifest.read_text())
    episodes = load_episodes(manifest, args.raw_root, args.allow_partial)
    episodes = add_translations(episodes, manifest, args.raw_root)
    inventory = json.loads((ROOT / "app/data/speech-frequency/es-literal-ground-r6-fw1.json").read_text())["values"]
    dialogue, deck = build(episodes, inventory, manifest, include_all=True)
    records = [{"title": ep["episode"], "artist": "La Casa de Papel",
                "dialogueLines": [{"text": line["spanish"]} for line in ep["lines"]]} for ep in episodes]
    annotation = subprocess.run(["node", str(ROOT / "scripts/annotate_offline_intake.mjs")],
                                input=json.dumps({"records": records, "speechSurfaces": list(inventory)}),
                                text=True, capture_output=True, check=True)
    deck["intake"] = json.loads(annotation.stdout)
    completed = subprocess.run(["node", str(ROOT / "scripts/complete_series_deck.mjs")],
                               input=json.dumps(deck), text=True, capture_output=True, check=True)
    deck = json.loads(completed.stdout)
    for name, value in [("casa-de-papel.json", dialogue), ("casa-de-papel-deck.json", deck)]:
        (ROOT / "app/data/series" / name).write_text(json.dumps(value, ensure_ascii=False, separators=(",", ":")) + "\n")
    print(f"{len(episodes)} episodes, {dialogue['total_lines_count']} cues, {deck['matchedCount']} words, {(deck['matchedCount'] + 99) // 100} levels")


if __name__ == "__main__":
    main()
