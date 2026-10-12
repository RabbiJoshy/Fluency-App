#!/usr/bin/env python3
"""Bake Spotify track ids and LRCLIB line timings into the lyrics-view catalogue.

The 30 catalogue songs in ``app/turbo/probe_songs.json`` carry only
``{title, artist, lyrics}``. Song translation mode can play a line on Spotify
only when a song has a 22-character ``spotifyId`` and per-line times, so this
does the lookup once, offline, instead of at every page load.

* ``spotifyId`` comes from the lyrics release's ``spanish-test-playlist``
  ``songs.json`` -- the same 30 songs -- matched on title *and* artist.
* ``syncedLyrics`` comes from LRCLIB. A candidate is accepted only when its
  words overlap the catalogue lyrics (``--min-overlap``), so a live cut, a
  remix or a different song with the same title is rejected rather than baked.

Nothing is invented: a song with no id, or no accepted synced record, is left
exactly as it was and listed in the report. LRCLIB times belong to one
recording; the app compares ``lrclibDurationMs`` with Spotify's reported
duration at play time and stops the fill when they disagree.

    python scripts/bake_probe_timings.py --workspace ../Fluency-Workspace --dry-run
    python scripts/bake_probe_timings.py --workspace ../Fluency-Workspace
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import time
import unicodedata
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
DEFAULT_PROBE = REPO / "app" / "turbo" / "probe_songs.json"
DEFAULT_RELEASE = "lyrics-all-artists-v20"
IDS_RELATIVE = Path("app/Artists/es/spanish-test-playlist/songs.json")
LRCLIB = "https://lrclib.net/api"
HEADERS = {"Lrclib-Client": "Fluency/0.1 (https://github.com/RabbiJoshy/Fluency-Next)"}
TRACK_ID = re.compile(r"^[A-Za-z0-9]{22}$")
LRC_TAG = re.compile(r"\[\d{1,3}:\d{2}(?:\.\d{1,3})?\]")


def fold(text: str) -> str:
    """Lower-case, accent-free, letters and digits only."""
    base = unicodedata.normalize("NFKD", text.lower())
    return re.sub(r"[^a-z0-9]", "", base.encode("ascii", "ignore").decode())


def words(text: str) -> set[str]:
    base = unicodedata.normalize("NFKD", text.lower()).encode("ascii", "ignore").decode()
    return {w for w in re.findall(r"[a-z0-9]+", base) if len(w) > 1}


def title_variants(title: str) -> list[str]:
    """The title as written, then without a ' - Remix' / ' - Live at ...' tail."""
    out = [title]
    head = re.split(r"\s+[-–—]\s+", title)[0].strip()
    if head and head != title:
        out.append(head)
    return out


def load_ids(release_dir: Path) -> dict[tuple[str, str], str]:
    path = release_dir / IDS_RELATIVE
    payload = json.loads(path.read_text("utf-8"))
    songs = payload["songs"] if isinstance(payload, dict) and "songs" in payload else payload
    ids: dict[tuple[str, str], str] = {}
    for song in songs:
        track = song.get("spotifyTrackId") or ""
        if TRACK_ID.match(track):
            ids[(fold(song.get("title", "")), fold(song.get("artist", "")))] = track
    return ids


def find_id(ids: dict[tuple[str, str], str], title: str, artist: str) -> str | None:
    return ids.get((fold(title), fold(artist)))


def get_json(path: str, params: dict[str, str], retries: int = 2):
    url = f"{LRCLIB}/{path}?{urllib.parse.urlencode(params)}"
    for attempt in range(retries + 1):
        try:
            request = urllib.request.Request(url, headers=HEADERS)
            with urllib.request.urlopen(request, timeout=20) as response:
                return json.load(response)
        except urllib.error.HTTPError as err:
            if err.code == 404:
                return []
            if attempt == retries:
                raise
        except (urllib.error.URLError, TimeoutError):
            if attempt == retries:
                raise
        time.sleep(1.5 * (attempt + 1))
    return []


def candidates(title: str, artist: str) -> list[dict]:
    """LRCLIB records for the song, de-duplicated by id."""
    primary = artist.split(",")[0].strip()
    found: dict[int, dict] = {}
    for variant in title_variants(title):
        for params in (
            {"track_name": variant, "artist_name": primary},
            {"q": f"{variant} {primary}"},
        ):
            for record in get_json("search", params) or []:
                if isinstance(record, dict) and record.get("id") is not None:
                    found.setdefault(record["id"], record)
    return list(found.values())


def overlap(catalogue_words: set[str], record: dict) -> float:
    """Share of the catalogue's words that the record's text also contains."""
    text = LRC_TAG.sub(" ", record.get("syncedLyrics") or "")
    if not catalogue_words or not text.strip():
        return 0.0
    return len(catalogue_words & words(text)) / len(catalogue_words)


def last_timestamp(record: dict) -> float:
    stamps = [int(m.group(1)) * 60 + float(m.group(2))
              for m in re.finditer(r"\[(\d{1,3}):(\d{2}(?:\.\d{1,3})?)\]", record.get("syncedLyrics") or "")]
    return max(stamps) if stamps else 0.0


def credible(record: dict) -> bool:
    """A stated duration that the record's own timestamps can sit inside.

    LRCLIB holds many copies of one lyric with junk durations (80 s for a
    189 s song, 930 s for a 242 s one), so a duration is believed only when the
    last timestamp falls within it and it does not trail on for over a minute.
    """
    duration, last = record.get("duration"), last_timestamp(record)
    return bool(duration) and last <= duration + 2 and duration <= last + 60


def choose(song: dict, records: list[dict], min_overlap: float) -> dict:
    """The dominant cut of the song among LRCLIB's duplicates.

    Records are first held to the catalogue's own words (the version we show),
    then to credible durations; the largest group of records agreeing on length
    (within 2 s) is taken as the studio cut, and within it the most common
    last-timestamp. The report names the rival cuts so they can be listened to.
    """
    catalogue_words = words(song.get("lyrics", ""))
    synced = [r for r in records if (r.get("syncedLyrics") or "").strip() and not r.get("instrumental")]
    scored = [(overlap(catalogue_words, r), r) for r in synced]
    scored = [p for p in scored if p[0] >= min_overlap]
    if not scored:
        return {}
    top = max(score for score, _ in scored)
    tier = [r for score, r in scored if score >= top - 0.02 and credible(r)]
    if not tier:
        return {}
    clusters: list[list[dict]] = []
    for record in sorted(tier, key=lambda r: r["duration"]):
        if clusters and record["duration"] - clusters[-1][-1]["duration"] <= 2:
            clusters[-1].append(record)
        else:
            clusters.append([record])
    clusters.sort(key=lambda c: (-len(c), c[0]["duration"]))
    cluster = clusters[0]
    stamps = [round(last_timestamp(r)) for r in cluster]
    modal = max(set(stamps), key=lambda v: (stamps.count(v), -v))
    record = min((r for r in cluster if round(last_timestamp(r)) == modal), key=lambda r: r["id"])
    durations = sorted(r["duration"] for r in cluster)
    return {"record": record, "overlap": top, "agreeing": len(cluster),
            "duration_ms": int(round(durations[len(durations) // 2] * 1000)),
            "rivals": [(round(c[0]["duration"]), len(c)) for c in clusters[1:4]]}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--workspace", required=True, type=Path)
    parser.add_argument("--release", default=DEFAULT_RELEASE)
    parser.add_argument("--probe", type=Path, default=DEFAULT_PROBE)
    parser.add_argument("--min-overlap", type=float, default=0.6)
    parser.add_argument("--pause", type=float, default=0.4, help="seconds between songs")
    parser.add_argument("--dry-run", action="store_true", help="report only; do not write")
    args = parser.parse_args()

    release_dir = args.workspace / "releases" / "lyrics" / args.release
    ids = load_ids(release_dir)
    songs = json.loads(args.probe.read_text("utf-8"))

    rows = []
    for index, song in enumerate(songs):
        title, artist = song.get("title", ""), song.get("artist", "")
        track = find_id(ids, title, artist)
        try:
            pick = choose(song, candidates(title, artist), args.min_overlap)
        except (urllib.error.URLError, TimeoutError) as err:
            print(f"  LRCLIB unreachable for {title!r}: {err}", file=sys.stderr)
            pick = {}
        chosen = pick.get("record")
        row = {"i": index, "title": title, "artist": artist, "id": bool(track),
               "synced": bool(chosen), "overlap": round(pick.get("overlap", 0.0), 2),
               "lines": len(LRC_TAG.findall(chosen["syncedLyrics"])) if chosen else 0,
               "duration_s": round(pick.get("duration_ms", 0) / 1000),
               "agreeing": pick.get("agreeing", 0), "rivals": pick.get("rivals", [])}
        rows.append(row)
        # A song that cannot play keeps its plain lyrics: a synced record would
        # swap the displayed lines for nothing the learner can use.
        if track:
            song["spotifyId"] = track
            if chosen:
                song["syncedLyrics"] = chosen["syncedLyrics"]
                song["lrclibId"] = chosen["id"]
                song["lrclibDurationMs"] = pick["duration_ms"]
        time.sleep(args.pause)

    width = max(len(r["title"]) for r in rows)
    print(f"{'#':>2}  {'title':<{width}}  id  sync  overlap  lines  dur  agree  rival cuts (s x records)")
    for r in rows:
        print(f"{r['i']:>2}  {r['title']:<{width}}  {'Y' if r['id'] else '-':>2}  "
              f"{'Y' if r['synced'] else '-':>4}  {r['overlap']:>7.2f}  {r['lines']:>5}  "
              f"{r['duration_s']:>3}  {r['agreeing']:>5}  "
              f"{', '.join(f'{d}x{n}' for d, n in r['rivals'])}")
    both = sum(1 for r in rows if r["id"] and r["synced"])
    print(f"\n{len(rows)} songs: {sum(r['id'] for r in rows)} with a Spotify id, "
          f"{sum(r['synced'] for r in rows)} with accepted synced lyrics, "
          f"{both} playable with timing.")

    if args.dry_run:
        print("dry run: nothing written")
        return 0
    args.probe.write_text(json.dumps(songs, ensure_ascii=False, indent=2) + "\n", "utf-8")
    print(f"wrote {args.probe}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
