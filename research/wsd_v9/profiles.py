"""Provider-neutral, target-anchored relation profiles for WSD research.

The two menu providers encode examples differently:

* SpanishDict puts ``original`` examples below a provider-specific metadata
  key (or directly on the legacy sense record).
* Wiktionary/Kaikki puts ``text`` examples directly in provider metadata and
  supplies character offsets for the bold target.

Those differences end here.  The extractor and rankers consume only the
``SourceExample`` and ``AnchoredFeatures`` records below.
"""

from __future__ import annotations

from collections import OrderedDict
from dataclasses import asdict, dataclass
import json
from pathlib import Path
import re
import unicodedata
from typing import Any, Iterable, Mapping, Sequence

import numpy as np


Meaning = tuple[str, str, str]


@dataclass(frozen=True, slots=True)
class SourceExample:
    text: str
    target_start: int | None = None
    target_end: int | None = None


@dataclass(frozen=True, slots=True)
class CandidateSense:
    surface_form: str
    provider: str
    part_of_speech: str
    headword: str
    sense_id: str
    translation: str
    definition: str
    context: str
    rank: int
    examples: tuple[SourceExample, ...]

    @property
    def meaning(self) -> Meaning:
        return (
            self.part_of_speech.upper(),
            self.translation or "<EMPTY>",
            self.headword.casefold(),
        )


@dataclass(frozen=True, slots=True)
class AnchoredFeatures:
    presence: frozenset[str]
    frame: frozenset[str]
    relation: frozenset[str]
    slots: tuple[tuple[str, tuple[str, ...]], ...]

    def to_json(self) -> dict[str, Any]:
        return {
            "presence": sorted(self.presence),
            "frame": sorted(self.frame),
            "relation": sorted(self.relation),
            "slots": {key: list(values) for key, values in self.slots},
        }


@dataclass(frozen=True, slots=True)
class ProfileRecord:
    surface_form: str
    provider: str
    part_of_speech: str
    headword: str
    sense_id: str
    translation: str
    source_example: str | None
    status: str
    features: AnchoredFeatures | None

    def to_json(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["features"] = self.features.to_json() if self.features else None
        return payload


def deaccent(value: str) -> str:
    return "".join(
        character
        for character in unicodedata.normalize("NFD", value.casefold())
        if unicodedata.category(character) != "Mn"
    )


def _clean_lemma(value: str) -> str:
    value = deaccent(value).strip()
    # spaCy analyses enclitic forms such as ``tenerlo`` as ``tener él``.
    return value.split()[0] if value else value


def _legacy_spanishdict_menu(payload: Mapping[str, Any]) -> dict[str, tuple[CandidateSense, ...]]:
    cards: dict[str, tuple[CandidateSense, ...]] = {}
    for surface, analyses in payload.items():
        candidates: list[CandidateSense] = []
        rank = 0
        for analysis in analyses:
            for sense_id, sense in analysis.get("senses", {}).items():
                examples = tuple(
                    SourceExample(str(example["original"]).strip())
                    for example in sense.get("examples", []) or []
                    if isinstance(example, Mapping) and str(example.get("original") or "").strip()
                )
                candidates.append(
                    CandidateSense(
                        surface_form=surface,
                        provider="spanishdict",
                        part_of_speech=str(sense.get("pos") or ""),
                        headword=str(sense.get("headword") or surface),
                        sense_id=str(sense_id),
                        translation=str(sense.get("translation") or ""),
                        definition="",
                        context=str(sense.get("context") or ""),
                        rank=rank,
                        examples=examples,
                    )
                )
                rank += 1
        cards[surface] = tuple(candidates)
    return cards


def _normalized_examples(metadata: Mapping[str, Any]) -> tuple[SourceExample, ...]:
    provider_block = metadata.get("spanishdict")
    if isinstance(provider_block, Mapping):
        raw_examples = provider_block.get("examples", [])
        text_field = "original"
    else:
        raw_examples = metadata.get("examples", [])
        text_field = "text"

    examples: list[SourceExample] = []
    for example in raw_examples or []:
        if not isinstance(example, Mapping):
            continue
        text = str(example.get(text_field) or "").strip()
        if not text:
            continue
        start = end = None
        offsets = example.get("bold_text_offsets")
        if (
            isinstance(offsets, Sequence)
            and offsets
            and isinstance(offsets[0], Sequence)
            and len(offsets[0]) == 2
        ):
            start, end = (int(offsets[0][0]), int(offsets[0][1]))
        examples.append(SourceExample(text, start, end))
    return tuple(examples)


def _normalized_menu(payload: Mapping[str, Any]) -> dict[str, tuple[CandidateSense, ...]]:
    provider = str(payload.get("source_adapter") or "unknown").split("-sense-menu", 1)[0]
    cards: dict[str, tuple[CandidateSense, ...]] = {}
    for card in payload.get("cards", []):
        surface = str(card["surface_form"])
        candidates: list[CandidateSense] = []
        rank = 0
        for analysis in card.get("analyses", []):
            for sense in analysis.get("senses", []):
                metadata = sense.get("provider_metadata") or {}
                candidates.append(
                    CandidateSense(
                        surface_form=surface,
                        provider=provider,
                        part_of_speech=str(analysis.get("part_of_speech") or ""),
                        headword=str(analysis.get("headword") or surface),
                        sense_id=str(sense.get("sense_id") or ""),
                        translation=str(sense.get("translation") or ""),
                        definition=str(sense.get("definition") or ""),
                        context=str(metadata.get("context") or ""),
                        rank=rank,
                        examples=_normalized_examples(metadata),
                    )
                )
                rank += 1
        cards[surface] = tuple(candidates)
    return cards


def load_menu(path: Path) -> dict[str, tuple[CandidateSense, ...]]:
    payload = json.loads(path.read_text())
    if isinstance(payload, Mapping) and isinstance(payload.get("cards"), list):
        return _normalized_menu(payload)
    if isinstance(payload, Mapping):
        return _legacy_spanishdict_menu(payload)
    raise ValueError(f"unsupported sense-menu shape: {path}")


def group_meanings(
    candidates: Iterable[CandidateSense],
) -> "OrderedDict[Meaning, tuple[CandidateSense, ...]]":
    grouped: "OrderedDict[Meaning, list[CandidateSense]]" = OrderedDict()
    for candidate in candidates:
        grouped.setdefault(candidate.meaning, []).append(candidate)
    return OrderedDict((meaning, tuple(items)) for meaning, items in grouped.items())


def _target_terms(surface_form: str, headword: str) -> frozenset[str]:
    terms = {_clean_lemma(surface_form), _clean_lemma(headword)}
    head = _clean_lemma(headword)
    if head.endswith("se") and len(head) > 2:
        terms.add(head[:-2])
    return frozenset(term for term in terms if term)


def find_target_token(
    doc: Any,
    *,
    surface_form: str,
    headword: str,
    target_start: int | None = None,
    target_end: int | None = None,
) -> Any | None:
    if target_start is not None and target_end is not None:
        overlapping = [
            token
            for token in doc
            if token.idx < target_end and token.idx + len(token.text) > target_start
        ]
        if overlapping:
            return overlapping[0]

    exact = deaccent(surface_form)
    for token in doc:
        if deaccent(token.text) == exact:
            return token

    terms = _target_terms(surface_form, headword)
    for token in doc:
        if _clean_lemma(token.lemma_) in terms:
            return token
    return None


def _case_lemmas(token: Any) -> tuple[str, ...]:
    return tuple(
        sorted(
            {
                _clean_lemma(child.lemma_)
                for child in token.children
                if child.dep_ in {"case", "mark"} and _clean_lemma(child.lemma_)
            }
        )
    )


def extract_anchored_features(doc: Any, target: Any) -> AnchoredFeatures:
    presence = frozenset(
        f"lemma={_clean_lemma(token.lemma_)}"
        for token in doc
        if token.i != target.i
        and not token.is_punct
        and not token.is_space
        and _clean_lemma(token.lemma_)
    )

    frame: set[str] = {
        f"target_pos={target.pos_}",
        f"target_dep={target.dep_}",
    }
    relation: set[str] = set()
    slots: dict[str, set[str]] = {}

    def add_slot(key: str, lemma: str) -> None:
        if lemma:
            slots.setdefault(key, set()).add(lemma)

    if target.head.i != target.i:
        head = target.head
        head_lemma = _clean_lemma(head.lemma_)
        frame.add(f"head_pos={head.pos_}")
        frame.add(f"head_side={'left' if head.i < target.i else 'right'}")
        relation.add(f"head={target.dep_}:{head_lemma}")
        add_slot(f"head:{target.dep_}:{head.pos_}", head_lemma)

    for child in target.children:
        if child.is_punct:
            continue
        lemma = _clean_lemma(child.lemma_)
        frame.add(f"child={child.dep_}:{child.pos_}")
        relation.add(f"child={child.dep_}:{lemma}")
        add_slot(f"child:{child.dep_}:{child.pos_}", lemma)
        for case in _case_lemmas(child):
            frame.add(f"case_role={child.dep_}")
            relation.add(f"case={child.dep_}:{case}")
            add_slot(f"case:{child.dep_}", case)

    # Copulas and auxiliaries often attach to the content predicate instead of
    # governing it.  Its arguments are still the target's local frame.
    if target.dep_ in {"aux", "cop"} and target.head.i != target.i:
        predicate = target.head
        for sibling in predicate.children:
            if sibling.i == target.i or sibling.is_punct:
                continue
            lemma = _clean_lemma(sibling.lemma_)
            frame.add(f"predicate_child={sibling.dep_}:{sibling.pos_}")
            relation.add(f"predicate_child={sibling.dep_}:{lemma}")
            add_slot(f"predicate_child:{sibling.dep_}:{sibling.pos_}", lemma)
            for case in _case_lemmas(sibling):
                relation.add(f"predicate_case={sibling.dep_}:{case}")
                add_slot(f"predicate_case:{sibling.dep_}", case)

    return AnchoredFeatures(
        presence=presence,
        frame=frozenset(frame),
        relation=frozenset(relation),
        slots=tuple(
            (key, tuple(sorted(values))) for key, values in sorted(slots.items())
        ),
    )


def build_profiles(
    cards: Mapping[str, Sequence[CandidateSense]],
    *,
    nlp: Any,
    surfaces: Iterable[str] | None = None,
    batch_size: int = 128,
) -> list[ProfileRecord]:
    selected = list(surfaces) if surfaces is not None else list(cards)
    pending: list[tuple[CandidateSense, SourceExample]] = []
    records: list[ProfileRecord] = []

    for surface in selected:
        for candidate in cards.get(surface, ()):
            if not candidate.examples:
                records.append(
                    ProfileRecord(
                        surface_form=surface,
                        provider=candidate.provider,
                        part_of_speech=candidate.part_of_speech,
                        headword=candidate.headword,
                        sense_id=candidate.sense_id,
                        translation=candidate.translation,
                        source_example=None,
                        status="source_example_missing",
                        features=None,
                    )
                )
                continue
            pending.extend((candidate, example) for example in candidate.examples)

    docs = nlp.pipe((example.text for _, example in pending), batch_size=batch_size)
    for (candidate, example), doc in zip(pending, docs, strict=True):
        target = find_target_token(
            doc,
            surface_form=candidate.surface_form,
            headword=candidate.headword,
            target_start=example.target_start,
            target_end=example.target_end,
        )
        features = extract_anchored_features(doc, target) if target is not None else None
        records.append(
            ProfileRecord(
                surface_form=candidate.surface_form,
                provider=candidate.provider,
                part_of_speech=candidate.part_of_speech,
                headword=candidate.headword,
                sense_id=candidate.sense_id,
                translation=candidate.translation,
                source_example=example.text,
                status="ok" if features is not None else "target_not_located",
                features=features,
            )
        )
    return records


def profile_index(
    records: Iterable[ProfileRecord],
) -> dict[tuple[str, str], tuple[AnchoredFeatures, ...]]:
    grouped: dict[tuple[str, str], list[AnchoredFeatures]] = {}
    for record in records:
        if record.features is not None:
            grouped.setdefault((record.surface_form, record.sense_id), []).append(record.features)
    return {key: tuple(features) for key, features in grouped.items()}


def weighted_jaccard(
    left: frozenset[str],
    right: frozenset[str],
    idf: Mapping[str, float],
) -> float:
    if not left or not right:
        return 0.0
    union = left | right
    denominator = sum(idf.get(feature, 1.0) for feature in union)
    if denominator == 0:
        return 0.0
    return sum(idf.get(feature, 1.0) for feature in left & right) / denominator


def feature_idf(records: Iterable[ProfileRecord], family: str) -> dict[str, float]:
    documents = [
        getattr(record.features, family)
        for record in records
        if record.features is not None
    ]
    total = len(documents)
    counts: dict[str, int] = {}
    for document in documents:
        for feature in document:
            counts[feature] = counts.get(feature, 0) + 1
    return {
        feature: float(np.log((total + 1) / (count + 1)) + 1.0)
        for feature, count in counts.items()
    }


def slot_similarity(
    left: AnchoredFeatures,
    right: AnchoredFeatures,
    *,
    vector_for: Any,
) -> float:
    left_slots = dict(left.slots)
    right_slots = dict(right.slots)
    shared = sorted(set(left_slots) & set(right_slots))
    if not shared:
        return 0.0
    scores: list[float] = []
    for slot in shared:
        best = 0.0
        for left_lemma in left_slots[slot]:
            left_vector = vector_for(left_lemma)
            if left_vector is None:
                continue
            for right_lemma in right_slots[slot]:
                right_vector = vector_for(right_lemma)
                if right_vector is None:
                    continue
                similarity = float(left_vector @ right_vector)
                best = max(best, max(0.0, similarity))
        scores.append(best)
    return sum(scores) / len(scores)


def normalized_lexeme_vector(nlp: Any, lemma: str) -> np.ndarray | None:
    lexeme = nlp.vocab[lemma]
    if not lexeme.has_vector:
        return None
    vector = np.asarray(lexeme.vector, dtype=np.float32)
    norm = float(np.linalg.norm(vector))
    return vector / norm if norm else None


def summarize_profiles(records: Sequence[ProfileRecord]) -> dict[str, Any]:
    statuses: dict[str, int] = {}
    senses: set[tuple[str, str]] = set()
    senses_ok: set[tuple[str, str]] = set()
    providers: set[str] = set()
    for record in records:
        statuses[record.status] = statuses.get(record.status, 0) + 1
        key = (record.surface_form, record.sense_id)
        senses.add(key)
        providers.add(record.provider)
        if record.features is not None:
            senses_ok.add(key)
    return {
        "schema": "relation-profile-summary/v1",
        "providers": sorted(providers),
        "records": len(records),
        "senses": len(senses),
        "senses_with_usable_profile": len(senses_ok),
        "sense_profile_coverage": len(senses_ok) / len(senses) if senses else 0.0,
        "statuses": dict(sorted(statuses.items())),
        "feature_families": ["presence", "frame", "relation", "slots"],
    }


def write_jsonl(path: Path, rows: Iterable[Mapping[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")
