"""Three stores, one format, read as a stack (proposal 0003 §4).

| Store | Holds | Lives in | Written by |
|---|---|---|---|
| language | speech facts and language-wide declarations | ``config/declared/<lang>/`` (git, reviewed) | pipeline chats, GRAFT |
| artist | only what differs for one artist | ``<workspace>/artists/<lang>/<artist>/declared/`` | Joshua, running an artist by hand |
| live | heuristic facts from users' playlists | a database behind SETLIST's worker | itself; people work the curation queue |

All three hold ``fluency.surfaces.declared`` entries. A consumer reads the
stores it is allowed, and the resolver filters them by scope and trust; the
narrowest scope wins, and two entries at the same scope are an error even
when they come from different stores. So a new kind of exception is added
once, not three times.

| Consumer | Stores | Trust floor (``config/surfaces/strategy.json``) |
|---|---|---|
| speech release | language | derived |
| hand-run artist release | language + that artist | derived |
| live playlist | language + that artist, if any + live | heuristic |

**Promotion** is the only way a fact moves up a trust level. It appends a new
entry at the higher trust -- optionally at a wider scope -- to the store that
should hold it, and never edits the entry it promotes, so what was guessed
and what was confirmed both survive (Invariant 3).

MEND builds the shape only. No artist layer or live store has content yet;
the live store's storage and curation queue are later work that plugs into
``LiveFactSource``.
"""

from __future__ import annotations

import json
from dataclasses import replace
from pathlib import Path
from typing import Iterable, Protocol, runtime_checkable

from fluency.surfaces import trust
from fluency.surfaces.declared import (
    SCHEMA, DeclaredEntry, DeclaredError, DeclaredRegistry, _entry,
)

LANGUAGE_STORE = Path("config/declared")


def artist_layer_dir(workspace: Path, language: str, artist: str) -> Path:
    return Path(workspace) / "artists" / language / artist / "declared"


@runtime_checkable
class LiveFactSource(Protocol):
    """Heuristic facts from live playlists. Word-level, shared, no user data."""

    def entries(self, language: str) -> Iterable[DeclaredEntry]: ...


class NoLiveFacts:
    """The live store until SETLIST's worker holds one."""

    def entries(self, language: str) -> Iterable[DeclaredEntry]:
        return ()


def _read_dir(directory: Path, language: str, store: str) -> list[DeclaredEntry]:
    out: list[DeclaredEntry] = []
    for path in sorted(directory.glob("*.json")) if directory.is_dir() else ():
        document = json.loads(path.read_text(encoding="utf-8"))
        if document.get("schema") != SCHEMA or document.get("language") != language:
            raise DeclaredError(f"{path}: expected {SCHEMA} for {language}")
        for raw in document.get("entries") or []:
            out.append(_entry(raw, language=language, source=f"{store}:{path.name}"))
    return out


def language_entries(repository_root: Path, language: str) -> list[DeclaredEntry]:
    return _read_dir(Path(repository_root) / LANGUAGE_STORE / language, language, "language")


def artist_entries(workspace: Path, language: str, artist: str) -> list[DeclaredEntry]:
    """An artist layer holds only that artist's facts; anything wider belongs higher up."""
    entries = _read_dir(artist_layer_dir(workspace, language, artist), language, f"artist/{artist}")
    for entry in entries:
        if entry.scope.get("artist") != artist:
            raise DeclaredError(
                f"{entry.entry_id}: an entry in {artist}'s layer must be scoped to artist {artist!r}; "
                "a fact true for every artist belongs in the language store")
    return entries


def stack(
    repository_root: Path,
    language: str,
    *,
    workspace: Path | None = None,
    artist: str | None = None,
    live: LiveFactSource | None = None,
) -> DeclaredRegistry:
    """One registry over the stores a consumer may read, in stack order."""
    entries = language_entries(repository_root, language)
    if artist:
        if workspace is None:
            raise DeclaredError("an artist layer lives in the workspace; pass workspace=")
        entries += artist_entries(workspace, language, artist)
    if live is not None:
        for entry in live.entries(language):
            if trust.accepts(trust.DERIVED, entry.trust):
                raise DeclaredError(
                    f"{entry.entry_id}: the live store holds heuristic facts; a verified one "
                    "is promoted into the language or artist store instead")
            entries.append(entry)
    return DeclaredRegistry(language, entries)


def promote(
    entry: DeclaredEntry,
    *,
    to_trust: str,
    author: str,
    reason: str,
    created_at: str,
    scope: dict[str, str] | None = None,
) -> DeclaredEntry:
    """A new entry at a higher trust (and optionally a wider scope). The old one is untouched."""
    trust.check(to_trust)
    if not trust.accepts(entry.trust, to_trust) or to_trust == entry.trust:
        raise DeclaredError(f"{entry.entry_id}: promotion must raise trust, not {entry.trust} -> {to_trust}")
    new_scope = dict(entry.scope if scope is None else scope)
    # Artist, song and playlist may be kept or dropped, never added or changed.
    # Mode is not a nesting level: a live guess confirmed becomes a lyrics or
    # language-wide fact, so it may change or be dropped.
    narrowing = {key: value for key, value in new_scope.items() if key != "mode"}
    widened = set(narrowing.items()) <= {(k, v) for k, v in entry.scope.items() if k != "mode"}
    if not widened:
        raise DeclaredError(f"{entry.entry_id}: promotion may keep or widen a scope, never narrow it")
    return replace(
        entry,
        entry_id=f"{entry.entry_id}~{to_trust}",
        trust=to_trust,
        scope=new_scope,
        author=author,
        reason=reason,
        created_at=created_at,
        payload={**dict(entry.payload), "promoted_from": entry.entry_id},
        source_file="",
    )


def append_entry(path: Path, entry: DeclaredEntry) -> None:
    """Add an entry to a store file without rewriting the entries already there."""
    path = Path(path)
    if path.exists():
        document = json.loads(path.read_text(encoding="utf-8"))
    else:
        document = {"schema": SCHEMA, "language": entry.language, "entries": []}
    if document.get("language") != entry.language:
        raise DeclaredError(f"{path}: holds {document.get('language')}, not {entry.language}")
    if any(raw.get("entry_id") == entry.entry_id for raw in document["entries"]):
        raise DeclaredError(f"{path}: already holds {entry.entry_id}")
    record = entry.to_dict()
    for key in ("language", "source_file"):
        record.pop(key, None)
    if not record.get("scope"):
        record.pop("scope", None)
    document["entries"].append(record)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(document, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
