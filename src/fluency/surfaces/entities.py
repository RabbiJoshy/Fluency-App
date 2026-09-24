"""Automated entity resolution via Wikipedia REST API.

Queries the Wikipedia search and summary APIs to verify proper nouns,
infer canonical entity types (person, place, brand, work, event, organisation),
and generate MEND-compliant declared entity entries with zero LLM spend.
"""

from __future__ import annotations

import json
import re
import urllib.parse
import urllib.request
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Mapping

from fluency.surfaces.declared import (
    ENTITY_TYPES,
    DeclaredEntry,
    _entry,
)
from fluency.surfaces import trust

DEFAULT_USER_AGENT = "FluencyApp/1.0 (entities@fluency.internal)"

# Heuristic category mappings from Spanish/English descriptions to canonical ENTITY_TYPES
_TYPE_PATTERNS: tuple[tuple[re.Pattern, str], ...] = (
    (
        re.compile(
            r"\b(municipio|ciudad|capital|departamento|isla|país|provincia|estado|región|"
            r"estadio|coliseo|arena|barrio|distrito|localidad|río|montaña|comuna|pueblo|"
            r"city|municipality|capital|country|state|stadium|island|neighborhood)\b",
            re.IGNORECASE,
        ),
        "place",
    ),
    (
        re.compile(
            r"\b(rapero|cantante|productor|músico|futbolista|actor|actriz|persona|político|"
            r"artista|compositor|escritor|poeta|deportista|boxeador|entrenador|"
            r"singer|rapper|musician|player|actor|actress|producer|artist|politician)\b",
            re.IGNORECASE,
        ),
        "person",
    ),
    (
        re.compile(
            r"\b(fabricante|marca|automóviles|empresa|compañía|corporación|automóvil|"
            r"automaker|brand|company|corporation|car model|luxury)\b",
            re.IGNORECASE,
        ),
        "brand",
    ),
    (
        re.compile(
            r"\b(álbum|canción|sencillo|disco|tema|película|novela|serie|libro|obra|"
            r"album|song|single|track|film|movie|novel|book)\b",
            re.IGNORECASE,
        ),
        "work",
    ),
    (
        re.compile(
            r"\b(festival|concierto|gira|torneo|campeonato|batalla|juegos|premiación|"
            r"tour|festival|concert|tournament|games|event)\b",
            re.IGNORECASE,
        ),
        "event",
    ),
    (
        re.compile(
            r"\b(organización|grupo|banda|dúo|asociación|partido|colectivo|orquesta|"
            r"group|band|duo|association|party|organisation|organization|orchestra)\b",
            re.IGNORECASE,
        ),
        "organisation",
    ),
)


def infer_entity_type(description: str, extract: str = "") -> str:
    """Infer the canonical entity_type from Wikipedia description or extract."""
    text = f"{description} {extract}"
    for pattern, entity_type in _TYPE_PATTERNS:
        if pattern.search(text):
            return entity_type
    return "other"


@dataclass(frozen=True)
class WikipediaEntity:
    query: str
    canonical_title: str
    description: str
    extract: str
    entity_type: str
    language: str

    def to_declared_entry(
        self,
        *,
        author: str = "wikipedia_resolver",
        reason: str = "verified_wikipedia_entity",
        scope: Mapping[str, str] | None = None,
        source_file: str = "wikipedia_auto.json",
    ) -> DeclaredEntry:
        clean_desc = (self.description or self.extract[:120]).strip()
        payload = {
            "entity_type": self.entity_type,
            "description": clean_desc,
            "canonical_title": self.canonical_title,
        }
        return DeclaredEntry(
            entry_id=f"{self.language}-entity-{re.sub(r'[^a-z0-9_-]', '-', self.query.casefold())}",
            kind="entity",
            language=self.language,
            surface=self.query,
            payload=payload,
            scope=dict(scope or {}),
            trust=trust.DERIVED,
            reason=reason,
            author=author,
            created_at=datetime.now(UTC).date().isoformat(),
            source_file=source_file,
        )


class WikipediaEntityResolver:
    """Resolves proper noun candidates to verified entities using Wikipedia APIs."""

    def __init__(
        self,
        cache_dir: Path | None = None,
        user_agent: str = DEFAULT_USER_AGENT,
        timeout: float = 6.0,
    ) -> None:
        self.cache_dir = Path(cache_dir) if cache_dir else None
        self.user_agent = user_agent
        self.timeout = timeout
        self._memory_cache: dict[tuple[str, str], WikipediaEntity | None] = {}
        if self.cache_dir:
            self.cache_dir.mkdir(parents=True, exist_ok=True)

    def _cache_path(self, query: str, language: str) -> Path | None:
        if not self.cache_dir:
            return None
        safe = re.sub(r"[^a-z0-9_-]", "_", query.casefold())
        return self.cache_dir / f"{language}_{safe}.json"

    def resolve(self, query: str, language: str = "es") -> WikipediaEntity | None:
        """Resolve a query string to a WikipediaEntity, or None if not found/unverified."""
        normalized_q = query.strip()
        if not normalized_q:
            return None

        cache_key = (language, normalized_q.casefold())
        if cache_key in self._memory_cache:
            return self._memory_cache[cache_key]

        disk_path = self._cache_path(normalized_q, language)
        if disk_path and disk_path.exists():
            try:
                data = json.loads(disk_path.read_text(encoding="utf-8"))
                if data is None:
                    self._memory_cache[cache_key] = None
                    return None
                entity = WikipediaEntity(**data)
                self._memory_cache[cache_key] = entity
                return entity
            except Exception:
                pass

        entity = self._fetch(normalized_q, language)
        self._memory_cache[cache_key] = entity

        if disk_path:
            try:
                if entity is None:
                    disk_path.write_text(json.dumps(None), encoding="utf-8")
                else:
                    disk_path.write_text(
                        json.dumps(
                            {
                                "query": entity.query,
                                "canonical_title": entity.canonical_title,
                                "description": entity.description,
                                "extract": entity.extract,
                                "entity_type": entity.entity_type,
                                "language": entity.language,
                            },
                            ensure_ascii=False,
                            indent=2,
                        ),
                        encoding="utf-8",
                    )
            except Exception:
                pass

        return entity

    def _fetch(self, query: str, language: str) -> WikipediaEntity | None:
        headers = {"User-Agent": self.user_agent}

        # Step 1: Search for the closest page title
        search_url = (
            f"https://{language}.wikipedia.org/w/api.php?action=query&list=search"
            f"&srsearch={urllib.parse.quote(query)}&srlimit=1&format=json"
        )
        try:
            req = urllib.request.Request(search_url, headers=headers)
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                data = json.loads(resp.read().decode("utf-8"))
            results = data.get("query", {}).get("search", [])
            if not results:
                return None
            title = str(results[0].get("title", "")).strip()
            if not title:
                return None
        except Exception:
            return None

        # Step 2: Fetch the page summary
        summary_url = f"https://{language}.wikipedia.org/api/rest_v1/page/summary/{urllib.parse.quote(title)}"
        try:
            req = urllib.request.Request(summary_url, headers=headers)
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                sum_data = json.loads(resp.read().decode("utf-8"))

            if sum_data.get("type") == "disambiguation":
                return None

            desc = str(sum_data.get("description") or "").strip()
            extract = str(sum_data.get("extract") or "").strip()
            if not desc and not extract:
                return None

            entity_type = infer_entity_type(desc, extract)
            return WikipediaEntity(
                query=query,
                canonical_title=title,
                description=desc,
                extract=extract,
                entity_type=entity_type,
                language=language,
            )
        except Exception:
            return None
