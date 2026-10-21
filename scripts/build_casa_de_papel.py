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
import html
import json
import re
import zipfile
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXPECTED = {(season, episode) for season, count in enumerate((9, 6, 8, 8, 10), 1)
            for episode in range(1, count + 1)}
TIME = re.compile(r"(\d\d):(\d\d):(\d\d)[,.](\d{3})")
TOKEN = re.compile(r"[^\W_]+(?:['’\-][^\W_]+)*", re.UNICODE)
REVISION = "offline-30-episodes-v1"


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


def build(episodes, inventory, manifest):
    surfaces, candidates, token_count = {}, {}, 0
    for ep in episodes:
        for line in ep["lines"]:
            tokens = TOKEN.findall(line["spanish"].lower().replace("’", "'"))
            token_count += len(tokens)
            for word, count in Counter(tokens).items():
                if word not in inventory:
                    continue
                entry = surfaces.setdefault(word, {"count": 0, "lines": []})
                entry["count"] += count
                example = {"text": line["spanish"], "song": ep["episode"], "artist": "La Casa de Papel"}
                by_season = candidates.setdefault(word, {})
                choices = by_season.setdefault(ep["episode"][:3], [])
                if not any(e["text"] == example["text"] for e in choices):
                    choices.append(example)
                    choices.sort(key=lambda e: (not bool(re.search(r'[.!?…]["\u201d]?$' , e["text"])),
                                                 not 4 <= len(TOKEN.findall(e["text"])) <= 35))
                    del choices[5:]
    # Spread examples across the available seasons rather than filling every
    # common word with the first few lines of the first episode.
    for word, by_season in candidates.items():
        for i in range(5):
            for season in sorted(by_season):
                choices = by_season[season]
                if i < len(choices) and not any(e["text"] == choices[i]["text"] for e in surfaces[word]["lines"]):
                    surfaces[word]["lines"].append(choices[i])
                if len(surfaces[word]["lines"]) == 5:
                    break
            if len(surfaces[word]["lines"]) == 5:
                break
    actual = {ep["episode"] for ep in episodes}
    expected = {f"S{s:02}E{e:02}" for s, e in EXPECTED}
    coverage = {"episodes": len(episodes), "seasons": sorted({int(ep["episode"][1:3]) for ep in episodes}),
                "numbering": manifest["numbering"], "complete": actual == expected,
                "missing": sorted(expected - actual), "exampleTranslations": "unavailable"}
    dialogue = {"series_id": "la-casa-de-papel", "title": "La Casa de Papel", "language": "spanish",
                "episodes_count": len(episodes), "total_lines_count": sum(len(e["lines"]) for e in episodes),
                "coverage": coverage, "episodes": episodes}
    deck = {"id": "live", "presetRevision": REVISION, "sourceKind": "series",
            "playlistId": "la-casa-de-papel", "playlistName": "La Casa de Papel", "language": "spanish",
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
    inventory = json.loads((ROOT / "app/data/speech-frequency/es-literal-ground-r6-fw1.json").read_text())["values"]
    dialogue, deck = build(episodes, inventory, manifest)
    for name, value in [("casa-de-papel.json", dialogue), ("casa-de-papel-deck.json", deck)]:
        (ROOT / "app/data/series" / name).write_text(json.dumps(value, ensure_ascii=False, separators=(",", ":")) + "\n")
    print(f"{len(episodes)} episodes, {dialogue['total_lines_count']} cues, {deck['matchedCount']} words, {(deck['matchedCount'] + 99) // 100} levels")


if __name__ == "__main__":
    main()
