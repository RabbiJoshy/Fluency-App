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
import unicodedata
from pathlib import Path
from typing import Any, Iterable, Mapping

from fluency.core.hashing import file_content_id
from fluency.features.cognates import (
    COGNATE_SCORE_SCHEMA,
    CognatePolicy,
    build_known_index,
    expand_surfaces,
    form_score,
    gloss_alternatives,
    live_glosses,
    load_policy,
    normalise_gloss,
    read_relations,
    score_deck,
    strip_accents,
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
    import gzip

    opener = gzip.open if str(path).endswith(".gz") else open
    with opener(path, "rt", encoding="utf-8") as handle:
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


# The app payload's own version, separate from the layer's score_schema: adding
# `matches` changes what ships, not how a score is computed.
COGNATE_APP_SCHEMA = "cognate-score/v1.1"
COGNET_APP_SCHEMA = "cognate-score/v2.1"


def build_app_cognet(
    *,
    language: str,
    rows: Mapping[str, Mapping[str, Mapping[str, Any]]],
    thresholds: Mapping[str, float],
    built_from: str | None = None,
) -> dict[str, Any]:
    """The app-facing view of the (surface, lemma) route.

    ``rows`` is keyed known language -> surface -> lemma -> match.

    v1 shipped ``surface -> {language: score}``. v2 adds the lemma between them,
    because the two halves of a score are settled at different levels and the
    app needs both: the surface score to decide a card, and the per-lemma score
    to decide a sense on a card whose other senses stay.

    Card identity is untouched. The outer key is still the observed surface
    form, so nothing is looked up by lemma -- the lemma is a dimension of the
    verdict, never of the card.
    """

    scores: dict[str, dict[str, dict[str, float]]] = {}
    matches: dict[str, dict[str, dict[str, str]]] = {}
    for known_language, surfaces in rows.items():
        for surface, lemmas in surfaces.items():
            for lemma, match in lemmas.items():
                entry = scores.setdefault(surface, {}).setdefault(lemma, {})
                entry[known_language] = round(float(match["score"]), 3)
                # Same match, so the word and the number can never disagree.
                word = str(match.get("known_word") or "").strip()
                if word:
                    matches.setdefault(surface, {}).setdefault(lemma, {})[known_language] = word
    return {
        "schema": COGNET_APP_SCHEMA,
        "language": language,
        "known_languages": sorted(rows),
        "built_from_release_id": built_from,
        "thresholds": {code: float(value) for code, value in sorted(thresholds.items())},
        # surface -> lemma -> known language -> score
        "scores": {
            surface: {lemma: dict(sorted(langs.items())) for lemma, langs in sorted(lemmas.items())}
            for surface, lemmas in sorted(scores.items())
        },
        # surface -> lemma -> known language -> the word that produced that score
        "matches": {
            surface: {lemma: dict(sorted(langs.items())) for lemma, langs in sorted(lemmas.items())}
            for surface, lemmas in sorted(matches.items())
        },
    }


def merge_cognet_scores(
    layer: Mapping[str, Any],
    cognet_scores: Mapping[str, Mapping[str, Any]],
) -> dict[str, Any]:
    """Fold CogNet's asserted pairs into a scored layer, keeping the better of the two.

    The two routes fail in different directions and that is why both are kept.
    The gloss route reaches any word a dictionary defines, and misses where the
    two languages word a definition differently. CogNet reaches only what a
    curated list asserts, but on those it is right about the meaning in a way
    gloss overlap cannot be — measured on Czech, it abstains on every classic
    false friend (``čerstvý``, ``sklep``, ``chyba``, ``zapomenout``) while adding
    519 Polish and 185 English exclusions the gloss route never found.

    Merging on the higher score is safe precisely because both routes end in the
    same units: ``combine(form, meaning)`` against the same per-pair cutoff. The
    surviving record says which route produced it, so a surprising exclusion can
    always be traced to the evidence behind it.
    """

    merged: dict[str, dict[str, Any]] = {
        surface: {known: dict(match) for known, match in per_language.items()}
        for surface, per_language in layer.get("scores", {}).items()
    }
    for record in (m for p in merged.values() for m in p.values()):
        record.setdefault("meaning_source", "glosses")

    adopted: dict[str, int] = {}
    for known_language, scored in cognet_scores.items():
        taken = 0
        for surface, match in scored.items():
            record = dict(match)
            standing = merged.get(surface, {}).get(known_language)
            if standing is not None and float(standing["score"]) >= float(record["score"]):
                continue
            merged.setdefault(surface, {})[known_language] = record
            taken += 1
        adopted[known_language] = taken

    out = dict(layer)
    out["scores"] = merged
    coverage = {known: dict(value) for known, value in (layer.get("coverage") or {}).items()}
    for known_language, taken in adopted.items():
        entry = coverage.setdefault(known_language, {})
        entry["cognet_scored_surfaces"] = len(cognet_scores.get(known_language, {}))
        entry["cognet_adopted_surfaces"] = taken
    out["coverage"] = coverage
    out["known_languages"] = sorted(set(layer.get("known_languages", ())) | set(cognet_scores))
    out["routes"] = ["glosses", "cognet"]
    return out


def build_app_cognates(layer: Mapping[str, Any]) -> dict[str, Any]:
    """The app-facing view: surface -> {known language: score}, plus the word.

    The number decides; the word explains. They ship as sibling maps rather than
    as one object per leaf, so ``scores`` keeps the shape every existing reader
    expects and a file built before this change is still read correctly — it
    simply has no ``matches``.

    Shipping the word is not decoration. The app has no other way to name what a
    surface matched, and the gloss it fell back to is chosen by the sense menu,
    so it agreed with the score only by coincidence. ``matches[surface][known]``
    is taken from the same ``CognateMatch`` as ``scores[surface][known]``, which
    is what makes the pair true by construction. How form and meaning
    contributed stays in the layer, for auditing.
    """

    scores = {
        surface: {
            known: round(float(match["score"]), 3)
            for known, match in sorted(per_language.items())
        }
        for surface, per_language in sorted(layer.get("scores", {}).items())
    }
    matches = {
        surface: words
        for surface, per_language in sorted(layer.get("scores", {}).items())
        if (
            words := {
                known: str(match["known_word"])
                for known, match in sorted(per_language.items())
                if str(match.get("known_word") or "").strip()
            }
        )
    }
    # Each known language carries its own cutoff. The app never compares one
    # language's score with another's — it asks each in turn whether this word
    # is already free — so the numbers do not need a common scale.
    thresholds = {
        known: policy["default_threshold"]
        for known, policy in sorted(layer.get("policies", {}).items())
    }
    return {
        "schema": COGNATE_APP_SCHEMA,
        "language": layer["language"],
        "known_languages": list(layer["known_languages"]),
        "built_from_release_id": layer.get("built_from", {}).get("release_id"),
        "thresholds": thresholds,
        "scores": scores,
        # surface -> known language -> the word that produced that score
        "matches": matches,
    }


# ------------------------------------------------------------ the sense route

COGNATE_SENSE_SCHEMA = "cognate-score/v3"


def _normal_headword(value: Any) -> str:
    return unicodedata.normalize("NFC", str(value or "")).strip().lower()


def _single_word_alternatives(gloss: str) -> set[str]:
    # The app splits a card's translation its own way (card_rules mirrors
    # it); both readings are listed so every word the app asks about is here.
    from fluency.enrichments.card_rules import sense_alternatives

    ours = {text for text in gloss_alternatives(gloss) if text and " " not in text}
    return ours | sense_alternatives(gloss)


def build_app_cognates_by_sense(
    *,
    language: str,
    config_root: Path,
    raw_root: Path,
    release_rows: Iterable[Mapping[str, Any]] = (),
    target_extract: Path | None = None,
    surface_universe: set[str] | None = None,
    english_words: set[str] | None = None,
    score_floor: float = 0.6,
    release_id: str | None = None,
    carried: Mapping[str, Any] | None = None,
    surface_scorer: str | None = None,
) -> dict[str, Any]:
    """The per-sense map: surface -> headword -> English word -> closeness.

    A card is set aside only when *every* sense it shows is a free cognate, so
    the app needs a verdict per sense, not one number per word. A sense is
    identified the way the card shows it: by its headword and the English words
    its translation lists. So the map answers, for one surface and one
    headword, which English words are cognates of that headword and how close
    each looks to the surface on the page.

    Two questions, kept apart:

        is it a cognate?   CogNet, where CogNet knows the headword; otherwise
                           the English word being a whole gloss of the sense
                           (and a real English word, when a list is given)
        how close is it?   the pair's surface scorer, card surface vs the
                           English word -- the one knob, cut in the app

    ``carried`` is an existing v2 (surface, lemma) map whose non-English known
    languages ride along unchanged -- Czech read by a Polish speaker is not an
    English-gloss question, so it keeps the route and scorer it was calibrated
    on.

    Only pairs that pass the first question are listed, and only at or above
    ``score_floor`` so the file stays small while leaving the cutoff room to
    move. A (surface, headword, word) absent from the map is not a cognate.

    English only: the known word must be the translation itself, which is
    what makes this route safe against false friends.
    """

    policy = load_policy(config_root, language, "en")
    if surface_scorer:
        # Comparing scorers (scripts/eval_surface_scorer.py), never shipping.
        from dataclasses import replace

        policy = replace(policy, surface_scorer=surface_scorer)
    pairs = None
    if policy.cognet_pairs:
        from fluency.features.cognet import read_pairs

        pairs = read_pairs(Path(raw_root) / policy.cognet_pairs, target_column=policy.cognet_target_column)

    candidates: dict[str, dict[str, set[str]]] = {}

    def add(surface: str, headword: str, words: Iterable[str]) -> None:
        surface = _normal_headword(surface)
        if not surface or " " in surface:
            return
        bucket = candidates.setdefault(surface, {}).setdefault(_normal_headword(headword), set())
        bucket.update(words)

    rows = list(release_rows)
    universe = set(surface_universe or ())
    universe.update(_normal_headword(row.get("word")) for row in rows if row.get("word"))

    if target_extract is not None:
        relations = read_relations(
            _extract_entries(Path(target_extract)), policy, excluded_pos=EXCLUDED_TARGET_POS
        )
        for surface in universe:
            lemmas = set(relations.inflections.get(surface, ()))
            if surface in relations.lemma_glosses:
                lemmas.add(surface)
            for lemma in lemmas:
                for gloss in relations.lemma_glosses.get(lemma, ()):
                    add(surface, lemma, {gloss} if " " not in gloss else ())

    for row in rows:
        for meaning in row.get("meanings") or []:
            if not isinstance(meaning, Mapping):
                continue
            add(
                str(row.get("word") or ""),
                meaning.get("headword") or "",
                _single_word_alternatives(str(meaning.get("translation") or "")),
            )

    scores: dict[str, dict[str, dict[str, float]]] = {}
    routes = {"cognet": 0, "glosses": 0}
    for surface, by_headword in sorted(candidates.items()):
        if len(strip_accents(surface)) < policy.minimum_length:
            continue
        known_lemmas = set(by_headword) - {""}
        for headword, words in sorted(by_headword.items()):
            # A sense with no headword (older releases) may be any lemma the
            # surface has; CogNet is asked about each of them.
            asked = [headword] if headword else sorted(known_lemmas) or [surface]
            covered = [lemma for lemma in asked if pairs is not None and lemma in pairs]
            for word in sorted(words):
                if covered:
                    if not any(
                        word == pair.known_lemma for lemma in covered for pair in pairs[lemma]
                    ):
                        continue
                    route = "cognet"
                elif english_words is not None and word not in english_words:
                    continue
                else:
                    route = "glosses"
                score = form_score(surface, word, policy)
                if score < score_floor:
                    continue
                scores.setdefault(surface, {}).setdefault(headword, {})[word] = round(score, 3)
                routes[route] += 1

    # Speech decks load a card's senses only when its set opens, but set-up
    # filtering runs before that. So the card-level verdict for every release
    # row is decided here, by the same rule the app applies to loaded senses.
    from fluency.enrichments.card_rules import card_cognate

    cards: dict[str, list] = {}
    for row in rows:
        surface = _normal_headword(row.get("word"))
        verdict = card_cognate(row, scores.get(surface))
        if verdict is not None and verdict[0] > 0:
            cards[surface] = [round(verdict[0], 3), verdict[1]]

    carry = None
    if carried:
        if not str(carried.get("schema", "")).startswith("cognate-score/v2"):
            raise CognateLayerError("only a v2 (surface, lemma) map can be carried into v3")
        others = [code for code in carried.get("known_languages") or [] if code != "en"]
        carry = {
            "schema": carried["schema"],
            "known_languages": others,
            "thresholds": {code: carried["thresholds"][code] for code in others},
            "scores": _only_languages(carried.get("scores") or {}, others),
            "matches": _only_languages(carried.get("matches") or {}, others),
        }

    return {
        "schema": COGNATE_SENSE_SCHEMA,
        "language": language,
        "sense_languages": ["en"],
        "known_languages": ["en", *((carry or {}).get("known_languages") or [])],
        "carried": carry,
        "built_from_release_id": release_id,
        "surface_scorer": policy.surface_scorer,
        "score_floor": score_floor,
        "cognet": policy.cognet_pairs,
        "routes": routes,
        "thresholds": {"en": float(policy.default_threshold)},
        # surface -> headword -> English word -> closeness
        "scores": scores,
        # surface -> [weakest shown sense's closeness, its word], for the
        # release's own rows, used while a card's senses are not yet loaded
        "cards": cards,
    }


def _only_languages(by_surface: Mapping[str, Any], codes: list[str]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for surface, by_lemma in by_surface.items():
        for lemma, by_language in (by_lemma or {}).items():
            kept = {code: value for code, value in (by_language or {}).items() if code in codes}
            if kept:
                out.setdefault(surface, {})[lemma] = kept
    return out
