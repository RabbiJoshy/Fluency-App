#!/usr/bin/env python3
"""Build a recent, line-aligned OpenSubtitles snapshot from an OPUS Moses ZIP."""

from __future__ import annotations

import argparse
from contextlib import ExitStack
import hashlib
from itertools import zip_longest
import json
import os
from pathlib import Path
import shutil
import zipfile


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def year_from_ids(raw: bytes) -> int | None:
    parts = raw.split(b"\t", 2)
    if len(parts) < 2:
        return None
    segments = parts[1].split(b"/")
    if len(segments) < 3 or not segments[1].isdigit():
        return None
    year = int(segments[1])
    return year if 1800 <= year <= 2100 else None


def build(
    archive: Path,
    output: Path,
    *,
    target_language: str,
    translation_language: str,
    minimum_year: int,
    snapshot_id: str,
) -> Path:
    archive = archive.expanduser().resolve()
    output = output.expanduser().resolve()
    if output.exists():
        raise FileExistsError(f"snapshot destination already exists: {output}")
    output.mkdir(parents=True)
    prefix = f"OpenSubtitles.{translation_language}-{target_language}"
    members = {
        "translation": f"{prefix}.{translation_language}",
        "target": f"{prefix}.{target_language}",
        "ids": f"{prefix}.ids",
    }
    partials = {key: output / f"{name}.partial" for key, name in members.items()}
    finals = {key: output / name for key, name in members.items()}
    rows_seen = 0
    rows_retained = 0
    first_year: int | None = None
    newest_year: int | None = None
    try:
        with zipfile.ZipFile(archive) as zipped, ExitStack() as stack:
            inputs = {key: stack.enter_context(zipped.open(name)) for key, name in members.items()}
            outputs = {key: stack.enter_context(path.open("wb")) for key, path in partials.items()}
            for rows in zip_longest(inputs["translation"], inputs["target"], inputs["ids"]):
                if any(row is None for row in rows):
                    raise ValueError("OPUS target, translation and ids members are not line-aligned")
                rows_seen += 1
                year = year_from_ids(rows[2])
                if year is None or year < minimum_year:
                    continue
                outputs["translation"].write(rows[0])
                outputs["target"].write(rows[1])
                outputs["ids"].write(rows[2])
                rows_retained += 1
                first_year = year if first_year is None else min(first_year, year)
                newest_year = year if newest_year is None else max(newest_year, year)
                if rows_seen % 5_000_000 == 0:
                    print(f"scanned {rows_seen:,}; retained {rows_retained:,}", flush=True)
        if not rows_retained:
            raise ValueError(f"no aligned rows found from {minimum_year} onward")
        for key in members:
            os.replace(partials[key], finals[key])
        metadata = {
            "snapshot_version": "opensubtitles-aligned-snapshot/v1",
            "snapshot_id": snapshot_id,
            "target_language": target_language,
            "translation_language": translation_language,
            "license": (
                "OPUS OpenSubtitles v2018; subtitles from OpenSubtitles.org. "
                "Use requires a visible link to http://www.opensubtitles.org/ in reports "
                "and publications produced with the data."
            ),
            "attribution": (
                "OpenSubtitles.org via OPUS (Lison & Tiedemann 2016, "
                "OpenSubtitles2016: Extracting Large Parallel Corpora from Movie and TV "
                "Subtitles, LREC 2016)"
            ),
            "source_url": "https://opus.nlpl.eu/OpenSubtitles-v2018.php",
            "source_archive": {
                "url": (
                    "https://object.pouta.csc.fi/OPUS-OpenSubtitles/v2018/moses/"
                    f"{translation_language}-{target_language}.txt.zip"
                ),
                "sha256": sha256(archive),
                "bytes": archive.stat().st_size,
            },
            "recency": {
                "minimum_year": minimum_year,
                "first_year": first_year,
                "newest_year": newest_year,
                "source_rows": rows_seen,
                "aligned_pairs": rows_retained,
            },
            "slice_note": (
                f"Every aligned row whose OPUS provenance path records year >= {minimum_year}; "
                "relative order and line alignment are preserved."
            ),
        }
        (output / "snapshot.json").write_text(
            json.dumps(metadata, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
    except Exception:
        shutil.rmtree(output)
        raise
    print(f"Built {snapshot_id}: {rows_retained:,}/{rows_seen:,} aligned rows")
    return output


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--archive", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--target-language", required=True)
    parser.add_argument("--translation-language", default="en")
    parser.add_argument("--minimum-year", type=int, required=True)
    parser.add_argument("--snapshot-id", required=True)
    args = parser.parse_args()
    build(
        args.archive,
        args.output,
        target_language=args.target_language,
        translation_language=args.translation_language,
        minimum_year=args.minimum_year,
        snapshot_id=args.snapshot_id,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
