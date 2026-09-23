"""Hand-written facts about surfaces: one format, four kinds, scoped.

Proposal 0003 §4-§6. Everything a person writes down about a surface goes
through this one format, whichever way it later reaches a card:

- ``headwords``: the surface's menu lemma set, replacing what the provider
  declared (``atrevo`` -> ``atreverse``). Every headword must be a real
  dictionary entry, because the menu is built from those entries.
- ``gloss``: there is no dictionary entry; here is the meaning (``bum`` ->
  "boom"). Fills an empty menu at stage 02, or -- the same entry -- competes as
  an overlay sense at WSD time when the menu is not empty (GRAFT).
- ``expansion``: the surface stands for another surface (``ud`` -> ``usted``,
  lyrics ``pa'`` -> ``para``), whose headwords it then borrows.
- ``entity``: a name -- brand, place, person, work -- with a type and a
  one-line description; no senses, no WSD.

**Scope** says where an entry applies: language, then optionally mode, artist,
song, playlist. A missing field means "all". The narrowest matching entry wins,
and two matching entries equally narrow are an error, never a silent
precedence. **Trust** says how it was established (``fluency.surfaces.trust``);
hand-written entries are ``curated``.

Files are discovered, not registered (Invariant 5): every
``config/declared/<lang>/*.json`` is read, so GRAFT adds a list by creating a
file. The format lives outside ``fluency.wsd`` so a menu builds without the
classifier; ``fluency.wsd.overlays`` converts from it.
"""

from __future__ import annotations

import json
import unicodedata
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable, Mapping

from fluency.surfaces import trust

SCHEMA = "declared-entries/v1"
KINDS = ("headwords", "gloss", "expansion", "entity")
SCOPE_FIELDS = ("mode", "artist", "song", "playlist")
ENTITY_TYPES = ("brand", "place", "person", "work", "event", "organisation", "other")
# The tag a card shows (Resolution.word_class). Optional on an entry; the
# resolver infers one when it is missing.
WORD_CLASSES = (
    "vocabulary", "inflection", "enclitic", "abbreviation", "interjection",
    "onomatopoeia", "filler", "loanword", "slang", "entity", "name_fragment",
    "contamination",
)


def surface_key(text: str) -> str:
    return unicodedata.normalize("NFC", str(text)).strip().casefold()


@dataclass(frozen=True)
class Context:
    """Where a surface is being resolved: the consumer's side of a scope."""

    language: str
    mode: str | None = None
    artist: str | None = None
    song: str | None = None
    playlist: str | None = None


@dataclass(frozen=True)
class DeclaredEntry:
    entry_id: str
    kind: str
    language: str
    surface: str
    payload: Mapping[str, Any]
    scope: Mapping[str, str] = field(default_factory=dict)
    trust: str = trust.CURATED
    reason: str = ""
    author: str = ""
    created_at: str = ""
    source_file: str = ""

    @property
    def specificity(self) -> int:
        return sum(1 for key in SCOPE_FIELDS if self.scope.get(key))

    def applies_to(self, context: Context) -> bool:
        if context.language != self.language:
            return False
        return all(
            not self.scope.get(key) or self.scope.get(key) == getattr(context, key)
            for key in SCOPE_FIELDS
        )

    # Payload accessors, one per kind.
    @property
    def headwords(self) -> list[str]:
        return list(self.payload.get("headwords") or [])

    @property
    def senses(self) -> list[dict[str, str]]:
        return [dict(s) for s in self.payload.get("senses") or []]

    @property
    def expands_to(self) -> str:
        return str(self.payload.get("expands_to") or "")

    def to_dict(self) -> dict[str, Any]:
        return {
            "entry_id": self.entry_id, "kind": self.kind, "language": self.language,
            "surface": self.surface, "payload": dict(self.payload), "scope": dict(self.scope),
            "trust": self.trust, "reason": self.reason, "author": self.author,
            "created_at": self.created_at, "source_file": self.source_file,
        }


class DeclaredError(ValueError):
    pass


def _entry(raw: Mapping[str, Any], *, language: str, source: str) -> DeclaredEntry:
    entry_id = str(raw.get("entry_id") or "").strip()
    where = f"{source}: {entry_id or '<no entry_id>'}"
    kind = raw.get("kind")
    if not entry_id:
        raise DeclaredError(f"{where}: entry_id is required")
    if kind not in KINDS:
        raise DeclaredError(f"{where}: kind must be one of {', '.join(KINDS)}")
    surface = str(raw.get("surface") or "").strip()
    if not surface:
        raise DeclaredError(f"{where}: surface is required")
    missing = [key for key in ("reason", "author", "created_at") if not str(raw.get(key) or "").strip()]
    if missing:
        raise DeclaredError(f"{where}: provenance missing: {', '.join(missing)}")
    scope = {key: str(value) for key, value in (raw.get("scope") or {}).items() if value}
    unknown = set(scope) - set(SCOPE_FIELDS)
    if unknown:
        raise DeclaredError(f"{where}: unknown scope fields {sorted(unknown)}")
    level = trust.check(str(raw.get("trust") or trust.CURATED))
    payload = dict(raw.get("payload") or {})
    if payload.get("class") and payload["class"] not in WORD_CLASSES:
        raise DeclaredError(f"{where}: class must be one of {', '.join(WORD_CLASSES)}")
    if kind == "headwords":
        heads = [str(h).strip() for h in payload.get("headwords") or [] if str(h).strip()]
        if not heads:
            raise DeclaredError(f"{where}: headwords entry needs at least one headword")
        payload["headwords"] = heads
    elif kind == "gloss":
        senses = payload.get("senses") or []
        if not senses or not all(str((s or {}).get("translation") or "").strip() for s in senses):
            raise DeclaredError(f"{where}: gloss entry needs senses, each with a translation")
    elif kind == "expansion":
        if not str(payload.get("expands_to") or "").strip():
            raise DeclaredError(f"{where}: expansion entry needs expands_to")
    elif kind == "entity":
        if payload.get("entity_type") not in ENTITY_TYPES or not payload.get("description"):
            raise DeclaredError(f"{where}: entity needs entity_type ({', '.join(ENTITY_TYPES)}) and description")
    return DeclaredEntry(
        entry_id=entry_id, kind=kind, language=language, surface=surface, payload=payload,
        scope=scope, trust=level, reason=str(raw["reason"]), author=str(raw["author"]),
        created_at=str(raw["created_at"]), source_file=source,
    )


class DeclaredRegistry:
    """Every declared entry for one language, looked up by surface and context."""

    def __init__(self, language: str, entries: Iterable[DeclaredEntry] = ()) -> None:
        self.language = language
        self.entries: list[DeclaredEntry] = []
        self._by_surface: dict[str, list[DeclaredEntry]] = {}
        seen: set[str] = set()
        for entry in entries:
            if entry.entry_id in seen:
                raise DeclaredError(f"duplicate entry_id {entry.entry_id}")
            seen.add(entry.entry_id)
            self.entries.append(entry)
            self._by_surface.setdefault(surface_key(entry.surface), []).append(entry)
        self._check_collisions()

    def _check_collisions(self) -> None:
        """Two entries of one kind, one surface and one scope can never both apply."""
        for surface, entries in self._by_surface.items():
            keys: dict[tuple, str] = {}
            for entry in entries:
                key = (entry.kind, tuple(sorted(entry.scope.items())))
                if key in keys:
                    raise DeclaredError(
                        f"{surface!r}: {keys[key]} and {entry.entry_id} declare the same "
                        f"{entry.kind} at the same scope")
                keys[key] = entry.entry_id

    @classmethod
    def load(cls, root: Path, language: str) -> "DeclaredRegistry":
        """Read every ``<root>/<language>/*.json``. A missing directory is an empty registry."""
        entries: list[DeclaredEntry] = []
        directory = Path(root) / language
        for path in sorted(directory.glob("*.json")) if directory.is_dir() else ():
            document = json.loads(path.read_text(encoding="utf-8"))
            if document.get("schema") != SCHEMA or document.get("language") != language:
                raise DeclaredError(f"{path}: expected {SCHEMA} for {language}")
            for raw in document.get("entries") or []:
                entries.append(_entry(raw, language=language, source=path.name))
        return cls(language, entries)

    def select(self, surface: str, kind: str, context: Context, minimum_trust: str) -> DeclaredEntry | None:
        """The narrowest entry of ``kind`` that applies, if its trust is accepted."""
        matching = [
            entry for entry in self._by_surface.get(surface_key(surface), [])
            if entry.kind == kind and entry.applies_to(context) and trust.accepts(minimum_trust, entry.trust)
        ]
        if not matching:
            return None
        matching.sort(key=lambda entry: entry.specificity, reverse=True)
        if len(matching) > 1 and matching[0].specificity == matching[1].specificity:
            raise DeclaredError(
                f"{surface!r}: {matching[0].entry_id} and {matching[1].entry_id} both apply "
                f"at the same scope for {context}")
        return matching[0]

    def surfaces(self, kind: str | None = None) -> set[str]:
        return {surface_key(e.surface) for e in self.entries if kind is None or e.kind == kind}
