"""The CogNet route: an authoritative pair list, read at surface level.

``features/cognates.py`` decides cognateness itself, from spelling and glosses.
This module does not decide it at all. It reads CogNet — 8.1M asserted cognate
pairs across 338 languages, sense-tagged through WordNet synsets — and asks a
narrower question: *given that these two words are cognate, will the learner
recognise this particular inflected form?*

That split is the whole point. A score here is

    form  x  (meaning_floor + meaning_weight x 1.0)

with the meaning axis pinned to 1.0 **by assertion**, because CogNet has already
established the semantic link and established it better than gloss overlap can.
The same combine() and the same per-pair cutoffs apply, so a CogNet score and a
scored-from-scratch score mean the same thing to the app and to the learner.

Three legs, each supplying what the others cannot:

    CogNet          which lemmas are cognate         (meaning, asserted)
    the lemma file  which lemma this surface is      (target side, surface -> lemma)
    the dictionary  which surfaces that lemma takes  (known side, lemma -> surfaces)

The third leg matters more than it looks. CogNet lists lemmas on both sides, so
comparing a Czech surface against a bare Polish lemma compares an inflected form
with a citation form and understates the match: ``bratra`` against ``brat``
fails the length guard outright, while ``bratra`` against ``brata`` does not.
Expanding the known side restores the comparison the learner actually makes.

The target side is where this route needs something ``features/cognates.py``
does not: an external lemmatiser. A surface-to-lemma relation is one-to-many, so
``lemma_share_floor`` gates it on corpus frequency — see the policy field.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Any, Iterable, Mapping

from fluency.features.correspondences import Correspondences
from fluency.features.cognates import (
    CognatePolicy,
    combine,
    form_score,
    passes_length_guard,
)


COGNET_SCORE_SCHEMA = "cognet-score/v1"

# CogNet concept ids are WordNet synset ids, whose first character is the part
# of speech. Mapped to the names the lemma file uses so the two can be compared.
CONCEPT_PARTS_OF_SPEECH = {
    "n": "noun",
    "v": "verb",
    "a": "adjective",
    "s": "adjective",
    "r": "adverb",
}


class CognetSourceError(ValueError):
    """A CogNet or lemma source is missing, or is not the shape it claims."""


# ------------------------------------------------------------- the lemma file


@dataclass(frozen=True, slots=True)
class LemmaAnalysis:
    """One reading of a surface, with how much of its use that reading covers."""

    lemma: str
    share: float
    parts_of_speech: frozenset[str]


def _analyses_of(record: Mapping[str, Any]) -> list[Mapping[str, Any]]:
    """The readings a record states, from whichever provider stated them.

    Two providers reach this field and they carry different detail. A corpus
    provider states an ``ipm`` per reading; a dictionary form-of provider states
    only the lemma. Reading the second as a frequency-less analysis keeps 2,615
    Czech surfaces that would otherwise be dropped for lacking a number the
    provider never claimed to have — absence declared, not inferred.
    """

    evidence = record.get("evidence")
    if not isinstance(evidence, Mapping):
        return []
    resolved = evidence.get("lemma_resolved")
    if not isinstance(resolved, Mapping):
        return []
    rows = [row for row in resolved.get("analyses") or [] if isinstance(row, Mapping)]
    if rows:
        return rows
    return [{"lemma": lemma} for lemma in resolved.get("lemmas") or [] if lemma]


def read_surface_lemmas(path: Path | str) -> dict[str, tuple[LemmaAnalysis, ...]]:
    """Read a surface-view file into surface -> its readings, frequency-weighted.

    The provider states each reading's ``ipm`` (instances per million), so a
    reading's share is its ipm over the surface's total. Where a provider states
    no frequency at all the readings are treated as equally likely rather than
    silently dropped — declaring the uncertainty, not inferring an answer.
    """

    source = Path(path)
    if not source.is_file():
        raise CognetSourceError(f"no surface-view file at {source}")
    payload = json.loads(source.read_text(encoding="utf-8"))
    surfaces = payload.get("surfaces")
    if not isinstance(surfaces, Mapping):
        raise CognetSourceError(f"{source} has no surfaces map")

    out: dict[str, tuple[LemmaAnalysis, ...]] = {}
    for surface, record in surfaces.items():
        if not isinstance(record, Mapping):
            continue
        rows = _analyses_of(record)
        if not rows:
            continue
        weights: dict[str, float] = {}
        parts: dict[str, set[str]] = {}
        for row in rows:
            lemma = str(row.get("lemma") or "").strip().lower()
            if not lemma:
                continue
            weights[lemma] = weights.get(lemma, 0.0) + float(row.get("ipm") or 0.0)
            parts.setdefault(lemma, set()).update(
                str(part) for part in (row.get("pos") or []) if part
            )
        if not weights:
            continue
        total = sum(weights.values())
        if total <= 0:
            # No frequency stated. Every reading is equally possible, which the
            # share floor will then reject unless there is only one of them.
            total = float(len(weights))
            weights = {lemma: 1.0 for lemma in weights}
        out[str(surface).strip().lower()] = tuple(
            sorted(
                (
                    LemmaAnalysis(lemma, weight / total, frozenset(parts.get(lemma, ())))
                    for lemma, weight in weights.items()
                ),
                key=lambda analysis: -analysis.share,
            )
        )
    return out


def read_ledger(path: Path | str) -> dict[str, tuple[LemmaAnalysis, ...]]:
    """Read a surface ledger, whose lemma has already been *elected*.

    The earlier surface-view file offered a bag of readings and left the choosing
    here, which is why ``lemma_share_floor`` exists: something had to stop a 6%
    reading speaking for a rank-3 word. A ledger states one ``lemma`` with its
    ``lemma_provenance``, so the election is already made, by a process that saw
    more evidence than a frequency ratio — Wiktionary headwords, form_of links,
    SpanishDict, reverse conjugation, and manual corrections.

    So the elected lemma takes the full share and alternates take none. They are
    still carried, because a surface that inflects two lemmas is a real thing and
    a per-sense exclusion will want them; they simply do not speak for the
    surface on their own.
    """

    source = Path(path)
    if not source.is_file():
        raise CognetSourceError(f"no surface ledger at {source}")
    payload = json.loads(source.read_text(encoding="utf-8"))
    surfaces = payload.get("surfaces")
    if not isinstance(surfaces, Mapping):
        raise CognetSourceError(f"{source} has no surfaces map")

    out: dict[str, tuple[LemmaAnalysis, ...]] = {}
    for surface, record in surfaces.items():
        if not isinstance(record, Mapping):
            continue
        if record.get("verdict") == "exclude":
            # The ledger has already ruled this surface out of the deck; scoring
            # it would publish a verdict on a card that will not exist.
            continue
        elected = str(record.get("lemma") or "").strip().lower()
        if not elected:
            continue
        parts = frozenset(str(p) for p in (record.get("part_of_speech") or []) if p)
        readings = [LemmaAnalysis(elected, 1.0, parts)]
        for alternate in record.get("lemma_alternates") or []:
            if not isinstance(alternate, Mapping):
                continue
            lemma = str(alternate.get("lemma") or "").strip().lower()
            if lemma and lemma != elected:
                readings.append(LemmaAnalysis(lemma, 0.0, parts))
        out[str(surface).strip().lower()] = tuple(readings)
    return out


# ------------------------------------------------------------------- the pairs


@dataclass(frozen=True, slots=True)
class CognetPair:
    known_lemma: str
    parts_of_speech: frozenset[str]


def read_pairs(path: Path | str) -> dict[str, tuple[CognetPair, ...]]:
    """Read an extracted CogNet pair file into target lemma -> known lemmas.

    The file is the three columns the extractor writes — target word, known
    word, concept part of speech — one pair per line.
    """

    source = Path(path)
    if not source.is_file():
        raise CognetSourceError(f"no CogNet pair file at {source}")

    collected: dict[str, dict[str, set[str]]] = {}
    with source.open(encoding="utf-8") as handle:
        for line in handle:
            columns = line.rstrip("\n").split("\t")
            if len(columns) < 2:
                continue
            target = columns[0].strip().lower()
            known = columns[1].strip().lower()
            if not target or not known:
                continue
            marker = columns[2].strip() if len(columns) > 2 else ""
            part = CONCEPT_PARTS_OF_SPEECH.get(marker)
            entry = collected.setdefault(target, {}).setdefault(known, set())
            if part:
                entry.add(part)
    return {
        target: tuple(
            sorted(
                (CognetPair(known, frozenset(parts)) for known, parts in knowns.items()),
                key=lambda pair: pair.known_lemma,
            )
        )
        for target, knowns in collected.items()
    }


# ----------------------------------------------------------------- the scoring


@dataclass(frozen=True, slots=True)
class CognetMatch:
    """Why one surface scored what it did, kept for the layer."""

    surface: str
    target_lemma: str
    lemma_share: float
    known_lemma: str
    known_surface: str
    form: float
    score: float

    def to_dict(self) -> dict[str, Any]:
        return {
            "surface": self.surface,
            "target_lemma": self.target_lemma,
            "lemma_share": round(self.lemma_share, 3),
            "known_lemma": self.known_lemma,
            "known_surface": self.known_surface,
            "form": round(self.form, 3),
            "score": round(self.score, 3),
            "meaning": 1.0,
            "meaning_source": "cognet",
        }


def candidate_lemmas(
    surface: str,
    analyses: Iterable[LemmaAnalysis],
    policy: CognatePolicy,
) -> list[LemmaAnalysis]:
    """The readings of a surface that may speak for it.

    A surface that is itself a lemma always speaks for itself at full share:
    the frequency split describes which *other* words it might also be, and a
    word is never a minority reading of itself.
    """

    kept = [
        analysis
        for analysis in analyses
        if analysis.share >= policy.lemma_share_floor or analysis.lemma == surface
    ]
    return sorted(kept, key=lambda analysis: -analysis.share)


def _parts_agree(left: frozenset[str], right: frozenset[str]) -> bool:
    """Unknown on either side is not disagreement — absence is not a verdict."""

    return not left or not right or bool(left & right)


def best_match(
    surface: str,
    analyses: Iterable[LemmaAnalysis],
    pairs: Mapping[str, tuple[CognetPair, ...]],
    known_forms: Mapping[str, frozenset[str]],
    policy: CognatePolicy,
    *,
    require_pos_agreement: bool = False,
    target_sounds: Iterable[str] = (),
    known_sounds: Mapping[str, frozenset[str]] | None = None,
    correspondences: Correspondences | None = None,
    target_glosses: frozenset[str] = frozenset(),
) -> CognetMatch | None:
    """The most recognisable form of any lemma CogNet says this is cognate with.

    Where the policy sets ``known_must_be_a_gloss`` — every English pair does —
    CogNet's assertion is not enough on its own. CogNet states *etymological*
    cognacy and this feature needs *transparency*, and the two part company
    exactly where English kept a rare doublet: Spanish ``casi`` is cognate with
    ``quasi``, ``amor`` with ``amour``, ``largo`` with ``largo``, ``fácil`` with
    ``facile``. All true, none of them words a learner gets for free. Requiring
    the candidate to be a whole gloss of the target restores the check the gloss
    route already had.
    """

    surface = surface.strip().lower()
    if len(surface) < policy.minimum_length:
        return None
    whole_glosses = {gloss.strip().lower() for gloss in target_glosses}

    best: CognetMatch | None = None
    for analysis in candidate_lemmas(surface, analyses, policy):
        for pair in pairs.get(analysis.lemma, ()):
            if policy.known_must_be_a_gloss and pair.known_lemma not in whole_glosses:
                continue
            if require_pos_agreement and not _parts_agree(
                analysis.parts_of_speech, pair.parts_of_speech
            ):
                continue
            # The lemma itself is always among its forms, so an absent entry
            # still compares the two citation forms rather than scoring nothing.
            for known_surface in known_forms.get(pair.known_lemma, frozenset({pair.known_lemma})):
                if not passes_length_guard(surface, known_surface, policy):
                    continue
                form = form_score(
                    surface,
                    known_surface,
                    policy,
                    target_sounds=target_sounds,
                    known_sounds=(known_sounds or {}).get(known_surface, ()),
                    correspondences=correspondences,
                )
                score = combine(form, 1.0, policy)
                if best is None or score > best.score:
                    best = CognetMatch(
                        surface=surface,
                        target_lemma=analysis.lemma,
                        lemma_share=analysis.share,
                        known_lemma=pair.known_lemma,
                        known_surface=known_surface,
                        form=form,
                        score=score,
                    )
    return best


def match_by_lemma(
    surface: str,
    analyses: Iterable[LemmaAnalysis],
    pairs: Mapping[str, tuple[CognetPair, ...]],
    known_forms: Mapping[str, frozenset[str]],
    policy: CognatePolicy,
    *,
    require_pos_agreement: bool = False,
    target_sounds: Iterable[str] = (),
    known_sounds: Mapping[str, frozenset[str]] | None = None,
    correspondences: Correspondences | None = None,
    target_glosses: frozenset[str] = frozenset(),
) -> dict[str, CognetMatch]:
    """One verdict per lemma this surface can be, rather than one per surface.

    The two halves of the score live at different levels and collapsing them to
    a single row per surface loses that. *Form* is a property of what is on the
    page, so it is measured surface to surface: ``hoteles`` against ``hotels``,
    not ``hotel`` against ``hotel``. *Cognateness* is a property of the word, so
    it is settled once at the lemma and not re-litigated for every inflection.

    Keying on (surface, lemma) is what lets both be true at once, and it retires
    the majority-reading gate: Czech ``je`` is být and oni, and rather than
    choosing between them each becomes a row. A caller wanting today's behaviour
    takes the best row for the surface; a caller wanting per-sense exclusion
    hides only the sense whose lemma lost.
    """

    out: dict[str, CognetMatch] = {}
    for analysis in analyses:
        # The share floor exists to stop a minority reading speaking for a whole
        # surface. Here nothing speaks for the whole surface -- each reading is
        # its own row -- so the gate has no work to do and would only delete
        # rows. The true share is restored on the match below, as data.
        match = best_match(
            surface,
            [replace(analysis, share=1.0)],
            pairs,
            known_forms,
            policy,
            require_pos_agreement=require_pos_agreement,
            target_sounds=target_sounds,
            known_sounds=known_sounds,
            correspondences=correspondences,
            target_glosses=target_glosses,
        )
        if match is not None:
            out[analysis.lemma] = replace(match, lemma_share=analysis.share)
    return out


def score_pairs(
    surface_lemmas: Mapping[str, tuple[LemmaAnalysis, ...]],
    pairs: Mapping[str, tuple[CognetPair, ...]],
    known_forms: Mapping[str, frozenset[str]],
    policy: CognatePolicy,
    *,
    require_pos_agreement: bool = False,
    target_sounds: Mapping[str, frozenset[str]] | None = None,
    known_sounds: Mapping[str, frozenset[str]] | None = None,
    correspondences: Correspondences | None = None,
    target_glosses: Mapping[str, frozenset[str]] | None = None,
) -> dict[str, dict[str, CognetMatch]]:
    """Every (surface, lemma) this route can speak for."""

    sounds = target_sounds or {}
    glosses = target_glosses or {}
    scored: dict[str, dict[str, CognetMatch]] = {}
    for surface, analyses in surface_lemmas.items():
        rows = match_by_lemma(
            surface,
            analyses,
            pairs,
            known_forms,
            policy,
            require_pos_agreement=require_pos_agreement,
            target_sounds=sounds.get(surface, ()),
            known_sounds=known_sounds,
            correspondences=correspondences,
            target_glosses=glosses.get(surface, frozenset()),
        )
        if rows:
            scored[surface] = rows
    return scored


def score_surfaces(
    surface_lemmas: Mapping[str, tuple[LemmaAnalysis, ...]],
    pairs: Mapping[str, tuple[CognetPair, ...]],
    known_forms: Mapping[str, frozenset[str]],
    policy: CognatePolicy,
    *,
    require_pos_agreement: bool = False,
    target_sounds: Mapping[str, frozenset[str]] | None = None,
    known_sounds: Mapping[str, frozenset[str]] | None = None,
    correspondences: Correspondences | None = None,
    target_glosses: Mapping[str, frozenset[str]] | None = None,
) -> dict[str, CognetMatch]:
    """Score every surface the lemma file knows about."""

    sounds = target_sounds or {}
    glosses = target_glosses or {}
    scored: dict[str, CognetMatch] = {}
    for surface, analyses in surface_lemmas.items():
        match = best_match(
            surface,
            analyses,
            pairs,
            known_forms,
            policy,
            require_pos_agreement=require_pos_agreement,
            target_sounds=sounds.get(surface, ()),
            known_sounds=known_sounds,
            correspondences=correspondences,
            target_glosses=glosses.get(surface, frozenset()),
        )
        if match is not None:
            scored[surface] = match
    return scored
