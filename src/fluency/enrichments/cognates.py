"""Build a cognate layer: for one deck language, how transparent each surface
is to a speaker of each language the learner already reads.

The layer sits beside a release rather than inside it, and that placement is
deliberate. Cognate transparency is a property of ``(surface, language pair)``,
not of a particular deck — the same Czech word is equally recognisable to a
Polish reader whichever release it ships in. Keeping it out of the immutable
release also means adding a known language never re-cuts a deck.

The mapping is keyed by surface and by language, not by release. A score does
not expire when the deck changes: whether ``každý`` is free to a Polish reader
has nothing to do with which deck it ships in. A surface the mapping has not
seen is simply not excluded, and scores for surfaces the deck no longer carries
go unused — both cost at most one easy card. The release it was built from is
recorded as provenance, so you can tell what it was computed against, but it is
information rather than a gate.

The known side needs an English-glossed dictionary for the language the learner
reads. English itself needs none — the deck's glosses are already English, so
each gloss word stands as its own entry, and the same engine runs unchanged.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Iterable, Mapping

from fluency.core.hashing import file_content_id
from fluency.features.cognates import (
    COGNATE_SCORE_SCHEMA,
    CognatePolicy,
    build_known_index,
    expand_surfaces,
    live_glosses,
    load_policy,
    normalise_gloss,
    score_deck,
)


LAYER_VERSION = "cognate-layer/v1"

# Names carry no meaning to recognise, and an affix is not a word a learner
# meets on a card.
EXCLUDED_TARGET_POS = frozenset({
    "name", "prefix", "suffix", "infix", "affix", "character", "punct",
    "phrase", "prov", "abbrev", "symbol", "num",
})


class CognateLayerError(ValueError):
    """The inputs cannot produce a layer that could be trusted."""


def _target_glosses(index_rows: Iterable[Mapping[str, Any]], policy: CognatePolicy):
    """Surface -> the English senses the deck actually teaches for it.

    The release index is preferred over the raw dictionary here: it holds the
    senses that survived selection, which is what the learner will meet. A
    dictionary sense the deck never shows should not make a word count as
    already-known.
    """

    surfaces: dict[str, set[str]] = {}
    for row in index_rows:
        word = str(row.get("word") or "").strip().lower()
        if not word:
            continue
        glosses = surfaces.setdefault(word, set())
        for meaning in row.get("meanings") or []:
            if not isinstance(meaning, Mapping):
                continue
            for part in str(meaning.get("translation") or "").split(","):
                text = normalise_gloss(part)
                if text and len(text.split()) <= policy.gloss_maximum_words:
                    glosses.add(text)
    return {word: frozenset(glosses) for word, glosses in surfaces.items() if glosses}


def _extract_target_glosses(path: Path, policy: CognatePolicy, *, limit_to=None):
    """Surface -> its live English senses, taken from the language's own
    dictionary rather than from a deck.

    A cognate score belongs to ``(surface, language pair)``, so scoring only the
    surfaces one release happens to contain was a mistake: French's release is a
    200-card preview, and the map it produced could say nothing about the other
    49,800 words the language has. Reading the dictionary covers whatever a deck
    might later hold, which is also what makes the map survive a re-cut.

    Inflected surfaces are expanded in, because a card's identity is the surface
    form and a dictionary is organised around lemmas. Without that the two paths
    disagreed badly — the dictionary reached only 1,163 of Czech's 2,989 deck
    surfaces, so a wider map set aside fewer of the learner's own words than the
    narrow one did.

    ``limit_to`` bounds the work to a known surface universe — a published
    frequency list — when one is available.
    """

    return expand_surfaces(
        _extract_entries(path),
        policy,
        limit_to=limit_to,
        excluded_pos=EXCLUDED_TARGET_POS,
    )


def _english_index_entries(target: Mapping[str, frozenset[str]], english_words: set[str] | None = None):
    """Treat every English gloss word as its own dictionary entry.

    English is the pivot the deck already carries, so a Czech word is compared
    against the English words that translate it. Synthesising entries keeps one
    scoring engine rather than a second code path for the free case.
    """

    # A gloss is not guaranteed to be English. Wiktionary leaves target words
    # untranslated inside their own definitions, so a token lifted from a gloss
    # can be the very word it is supposed to be compared against — French nous,
    # dans and cette each scored 0.92 against themselves.
    #
    # Requiring a second surface to have produced the token held at deck scale
    # and collapsed at dictionary scale: across 84,000 French entries, nearly
    # any French word turns up in somebody's gloss. So when an English word list
    # is supplied, that decides what English is; the weaker rule is kept only
    # for the case where none is.
    sources: dict[str, set[str]] = {}
    for surface, glosses in target.items():
        for gloss in glosses:
            for token in gloss.split():
                sources.setdefault(token, set()).add(surface)

    for token, surfaces in sources.items():
        if english_words is not None:
            if token not in english_words:
                continue
        elif surfaces == {token}:
            continue
        yield {"word": token, "pos": "noun", "senses": [{"glosses": [token]}]}


def read_english_wordlist(path: Path) -> set[str]:
    """The first whitespace-separated field of each line, lowercased.

    Accepts a bare word list or any table whose first column is the word, which
    covers the pronunciation lists these are usually distributed as.
    """

    words: set[str] = set()
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        token = line.split("\t")[0].split()[0].strip().lower() if line.strip() else ""
        if token:
            words.add(token)
    if not words:
        raise CognateLayerError(f"no words in the English list at {path}")
    return words


def _extract_entries(path: Path):
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            try:
                yield json.loads(line)
            except json.JSONDecodeError as error:
                raise CognateLayerError(f"{path} is not a JSONL dictionary extract") from error


def build_cognate_layer(
    *,
    language: str,
    release_index: Path | None,
    known_extracts: Mapping[str, Path | None],
    config_root: Path,
    release_id: str,
    target_extract: Path | None = None,
    surface_universe: set[str] | None = None,
    english_words: set[str] | None = None,
) -> dict[str, Any]:
    """Score one deck's surfaces against every known language given.

    ``known_extracts`` maps a language code to its English-glossed dictionary
    extract, or to ``None`` for English, which needs none.
    """

    if not known_extracts:
        raise CognateLayerError("a cognate layer needs at least one known language")
    rows: list[Any] = []
    if target_extract is None:
        if release_index is None:
            raise CognateLayerError("a layer needs either a target extract or a release index")
        rows = json.loads(Path(release_index).read_text(encoding="utf-8"))
        if not isinstance(rows, list):
            raise CognateLayerError("release index must be a list of deck rows")

    scores: dict[str, dict[str, Any]] = {}
    coverage: dict[str, Any] = {}
    policies: dict[str, Any] = {}
    for known_language in sorted(known_extracts):
        policy = load_policy(config_root, language, known_language)
        target = (
            _extract_target_glosses(Path(target_extract), policy, limit_to=surface_universe)
            if target_extract is not None
            else _target_glosses(rows, policy)
        )
        extract = known_extracts[known_language]
        if known_language == "en" and extract is None:
            entries = _english_index_entries(target, english_words)
            source = {"kind": "deck_glosses", "content_id": None}
        else:
            if extract is None:
                raise CognateLayerError(
                    f"{known_language} needs a dictionary extract; only en may omit one"
                )
            entries = _extract_entries(Path(extract))
            source = {"kind": "wiktionary_extract", "content_id": file_content_id(Path(extract))}
        index = build_known_index(entries, policy)
        matched = score_deck(target, index)
        for surface, match in matched.items():
            scores.setdefault(surface, {})[known_language] = match.to_dict()
        coverage[known_language] = {
            "deck_surfaces": len(target),
            "scored_surfaces": len(matched),
            "known_entries": len(index.words),
            "source": source,
        }
        policies[known_language] = policy.to_dict()

    return {
        "layer_version": LAYER_VERSION,
        "score_schema": COGNATE_SCORE_SCHEMA,
        "language": language,
        "layer_kind": "cognates",
        # Card identity is the observed surface form, so that is the join key.
        # Nothing here is keyed by lemma or sense.
        "join_key": "surface",
        # Provenance, not a key: this says what the mapping was computed from,
        # and nothing looks the file up by it.
        "built_from": {
            "release_id": release_id,
            "target_source": "dictionary" if target_extract is not None else "release_index",
            "release_index_content_id": (
                None if release_index is None else file_content_id(Path(release_index))
            ),
        },
        "known_languages": sorted(known_extracts),
        "policies": policies,
        "coverage": coverage,
        "scores": scores,
    }


def build_app_cognates(layer: Mapping[str, Any]) -> dict[str, Any]:
    """The app-facing view: surface -> {known language: score}.

    The app only needs the number it thresholds. Which known word produced it,
    and how form and meaning contributed, stay in the layer for auditing — the
    same split the release makes everywhere else between what ships and what is
    kept to explain it.
    """

    scores = {
        surface: {
            known: round(float(match["score"]), 3)
            for known, match in sorted(per_language.items())
        }
        for surface, per_language in sorted(layer.get("scores", {}).items())
    }
    # Each known language carries its own cutoff. The app never compares one
    # language's score with another's — it asks each in turn whether this word
    # is already free — so the numbers do not need a common scale.
    thresholds = {
        known: policy["default_threshold"]
        for known, policy in sorted(layer.get("policies", {}).items())
    }
    return {
        "schema": COGNATE_SCORE_SCHEMA,
        "language": layer["language"],
        "known_languages": list(layer["known_languages"]),
        "built_from_release_id": layer.get("built_from", {}).get("release_id"),
        "thresholds": thresholds,
        "scores": scores,
    }
