"""Resolve OpenSubtitles title_ids to human film and series names, offline.

OpenSubtitles stores an IMDb tconst without the ``tt`` prefix. The learner app
falls back to that identifier when no title is attached, which is the code the
card currently prints. This layer reads the IMDb dumps already pinned in the
workspace and writes only the titles a corpus actually cites.
"""

from __future__ import annotations

import gzip
from pathlib import Path
from typing import Any, Iterable, Iterator

from fluency.core.io import json_bytes
from fluency.harvest.sources.opensubtitles import OpenSubtitlesAdapter


def imdb_tconst(title_id: str) -> str:
    return f"tt{int(title_id):07d}"


def collect_title_ids_from_ids_file(path: Path) -> set[str]:
    found: set[str] = set()
    with path.open(encoding="utf-8", errors="replace") as stream:
        for line in stream:
            title_id = OpenSubtitlesAdapter.title_id_from_ids_line(line)
            if title_id:
                found.add(title_id)
    return found


def collect_title_ids_from_examples(examples: Iterable[dict[str, Any]]) -> set[str]:
    found: set[str] = set()
    for example in examples:
        title_id = example_title_id(example)
        if title_id:
            found.add(title_id)
    return found


def iter_deck_examples(deck: dict[str, Any]) -> Iterator[dict[str, Any]]:
    for card in deck.get("cards") or []:
        for example in card.get("examples") or []:
            if isinstance(example, dict):
                yield example


def example_title_id(example: dict[str, Any]) -> str:
    metadata = example.get("metadata") if isinstance(example.get("metadata"), dict) else {}
    source = metadata.get("source") if isinstance(metadata.get("source"), dict) else {}
    document = source.get("document") if isinstance(source.get("document"), dict) else {}
    title_id = document.get("title_id")
    if title_id is None:
        provenance = example.get("provenance")
        if isinstance(provenance, dict):
            title_id = provenance.get("title_id")
    text = str(title_id or "").strip()
    return text if text.isdigit() else ""


def _read_basics(path: Path, wanted_tconsts: set[str]) -> dict[str, tuple[str, str | None, str]]:
    found: dict[str, tuple[str, str | None, str]] = {}
    if not wanted_tconsts:
        return found
    with gzip.open(path, "rt", encoding="utf-8") as stream:
        next(stream)
        for line in stream:
            parts = line.split("\t")
            tconst = parts[0]
            if tconst not in wanted_tconsts:
                continue
            year = None if parts[5] == "\\N" else parts[5]
            found[tconst] = (parts[2], year, parts[1])
            if len(found) == len(wanted_tconsts):
                break
    return found


def resolve_source_titles(
    title_ids: Iterable[str],
    *,
    basics_path: Path,
    episodes_path: Path | None = None,
) -> dict[str, dict[str, Any]]:
    wanted = {title_id for title_id in title_ids if str(title_id).isdigit()}
    keys = {imdb_tconst(title_id): title_id for title_id in wanted}
    basics = _read_basics(basics_path, set(keys))
    resolved: dict[str, dict[str, Any]] = {}
    for tconst, (title, year, kind) in basics.items():
        record: dict[str, Any] = {"title": title, "type": kind}
        if year:
            record["year"] = year
        resolved[keys[tconst]] = record

    episode_tconsts = {
        tconst for tconst, meta in basics.items() if meta[2] == "tvEpisode"
    }
    if not episode_tconsts or episodes_path is None or not episodes_path.is_file():
        return resolved

    parents: dict[str, tuple[str, str | None, str | None]] = {}
    with gzip.open(episodes_path, "rt", encoding="utf-8") as stream:
        next(stream)
        for line in stream:
            parts = line.rstrip("\n").split("\t")
            if parts[0] not in episode_tconsts:
                continue
            parents[parts[0]] = (
                parts[1],
                None if parts[2] == "\\N" else parts[2],
                None if parts[3] == "\\N" else parts[3],
            )
            if len(parents) == len(episode_tconsts):
                break
    series_basics = _read_basics(basics_path, {parent for parent, *_ in parents.values()})
    for tconst, (parent, season, number) in parents.items():
        series = series_basics.get(parent)
        if not series:
            continue
        record = resolved[keys[tconst]]
        record["series"] = series[0]
        if series[1]:
            record["series_year"] = series[1]
        if season:
            record["season"] = season
        if number:
            record["episode"] = number
    return resolved


def build_source_titles_snapshot(
    title_ids: Iterable[str],
    *,
    basics_path: Path,
    episodes_path: Path | None,
    out_path: Path,
) -> dict[str, Any]:
    wanted = {title_id for title_id in title_ids if str(title_id).isdigit()}
    titles = resolve_source_titles(
        wanted, basics_path=basics_path, episodes_path=episodes_path
    )
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_bytes(json_bytes(titles))
    missing = sorted(wanted - set(titles))
    return {
        "requested": len(wanted),
        "resolved": len(titles),
        "missing": missing,
        "path": out_path,
        "titles": titles,
    }
