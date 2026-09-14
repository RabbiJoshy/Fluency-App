"""An append-only record of what each stage learned about a surface.

Speech decisions used to live inside whichever stage made them, which works
while the pipeline is a line. It is not one. Evidence about a single surface
arrives from four places at four different times: a wordlist can say "out" is
English before anything runs, but only a harvest can say "dallas" is
capitalised in 100% of its 38 occurrences, and only a dictionary lookup can say
SpanishDict answered "comelo" when asked for "cogelo". A stage that has already
finished cannot be told something new.

An append-only log does not care in what order the truth arrives. Each observer
appends what it learned; nothing is recomputed to accommodate a late arrival;
and because the store is keyed by surface rather than by run, what was learned
about "dallas" in September is still known in December without refetching it.

This mirrors the lyrics lineage contract (fluency.lyrics.lineage) deliberately.
The subject there is a lyric token and here it is a surface, but the shape --
subject, phase, operation, evidence, content-addressed id -- is the same, and
two logs that answer the same question should not have two schemas.

Events are facts. Verdicts are not stored: see fluency.surfaces.policy. A fact
is true regardless of which deck reads it, whereas whether a proper noun
belongs in a deck differs by language and by mood, and burning that into the
record would mean re-deriving evidence every time the mood changed.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Iterable, Mapping

from fluency.core.hashing import canonical_content_id

EVENT_VERSION = "surface-observation/v1"

# When the thing was learned, not what it means.
PHASES = frozenset({"list", "harvest", "menu", "lemma", "clean", "review"})

# Every reason code an observer may emit. Codes are descriptions of evidence;
# none of them say what to do about it.
REASON_CODES = frozenset({
    # from the frequency list alone, before anything runs
    "english_wordlist",
    "foreign_frequency_list",
    "accent_stripped_duplicate",
    "abbreviation_form",
    # from the corpus, after a harvest
    "capitalised_in_corpus",
    "low_harvest_yield",
    # from the dictionary, after a menu build
    "dictionary_absent",
    "dictionary_entry_language",
    "dictionary_spelling_substitution",
    "dictionary_pos_gloss_mismatch",
    # from an external morphology source
    "lemma_resolved",
    "lemma_absent_from_dictionary",
    # someone settled the case by reading it. Adjudication carries its own
    # direction because the answer is as often "this is a word" as "it is not",
    # and a verdict that can only ever exclude is not a judgement.
    "human_review",
    "adjudicated_keep",
    "adjudicated_exclude",
})


# Most of what is learned about a surface is true of the word and not of the
# run that noticed it. "out" is an English word; "policii" is a form of
# "policie"; a reading that settled the case stays settled. None of that
# changes when a harvest is rerun, and treating the whole store as run-scoped
# would mean re-deriving facts that cannot have moved.
#
# Only two kinds genuinely depend on a run: what the corpus shows about how a
# surface is written, and how much of it there is. Even those are stable while
# the corpus snapshot is pinned -- rerunning the same harvest reproduces them --
# so they go stale only when a source snapshot changes.
DURABLE = frozenset({
    "english_wordlist",
    "foreign_frequency_list",
    "accent_stripped_duplicate",
    "abbreviation_form",
    "dictionary_absent",
    "dictionary_entry_language",
    "dictionary_spelling_substitution",
    "dictionary_pos_gloss_mismatch",
    "lemma_resolved",
    "lemma_absent_from_dictionary",
    "human_review",
    "adjudicated_keep",
    "adjudicated_exclude",
})
RUN_SCOPED = frozenset({"capitalised_in_corpus", "low_harvest_yield"})


def scope(reason_code: str) -> str:
    return "durable" if reason_code in DURABLE else "run_scoped"


def build_event(
    *,
    surface: str,
    language: str,
    phase: str,
    reason_code: str,
    observer: str,
    evidence: Mapping[str, Any] | None = None,
    run_id: str | None = None,
) -> dict[str, Any]:
    if phase not in PHASES:
        raise ValueError(f"unknown observation phase: {phase}")
    if reason_code not in REASON_CODES:
        raise ValueError(f"unknown reason code: {reason_code}")
    body = {
        "record_version": EVENT_VERSION,
        "subject": {"kind": "surface", "id": surface, "language": language},
        "phase": phase,
        "reason_code": reason_code,
        "observer": observer,
        "evidence": dict(evidence or {}),
        "run_id": run_id,
    }
    return {"event_id": "obs_" + canonical_content_id(body).removeprefix("sha256:")[:24], **body}


def append(path: Path, events: Iterable[Mapping[str, Any]]) -> int:
    """Append events, skipping any already recorded.

    The id is a hash of the body, so re-running an observer over unchanged
    inputs adds nothing. An observer that learns something new writes a new id.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    seen = {event["event_id"] for event in read(path)}
    written = 0
    with path.open("a", encoding="utf-8") as handle:
        for event in events:
            if event["event_id"] in seen:
                continue
            handle.write(json.dumps(event, ensure_ascii=False, sort_keys=True) + "\n")
            seen.add(event["event_id"])
            written += 1
    return written


def read(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    out = []
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                out.append(json.loads(line))
    return out


def by_surface(events: Iterable[Mapping[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    grouped: dict[str, list[dict[str, Any]]] = {}
    for event in events:
        grouped.setdefault(event["subject"]["id"], []).append(dict(event))
    return grouped


def store_path(workspace: Path, language: str) -> Path:
    return workspace / f"raw/surfaces/{language}/events.jsonl"
