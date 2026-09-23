"""Stream English-Wiktionary Kaikki JSONL into a closed sense menu."""

from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass
import gzip
import json
from pathlib import Path
import re
from typing import Any, Callable, Iterable, Iterator

from fluency.features.parenthetical import leading_parenthetical
from fluency.core.hashing import canonical_content_id, file_content_id
from fluency.languages.surfaces import (
    normalizer_for_language,
    typography_canonicalizer_for_language,
)
from fluency.features import SpecialistFeature
from fluency.features.metadata import METADATA_CONTRACT_VERSION
from fluency.features.wiktionary import (
    extract as extract_wiktionary_features,
    extract_surface_grammar,
    metadata_accounting,
)
from fluency.features.wiktionary_gloss import project_gloss
from fluency.menus import MenuAnalysis, SenseLeaf, build_analysis_id
from fluency.sense_menu.declared_menu import declared_entity_analyses, declared_gloss_analyses
from fluency.surfaces import trust as _trust
from fluency.surfaces.resolver import (
    ABSENT, COMPLETE_DUMP, DECLARED_GLOSS, ENTITY, EXPANSION, HEADWORDS, MENU,
    Headword, ProviderDeclaration,
)


ADAPTER_ID = "wiktionary-sense-menu/v1"
MENU_VERSION = "sense-menu/v1"
REPORT_VERSION = "sense-menu-report/v1"
FORM_TAGS = frozenset({"form-of", "alt-of"})


class KaikkiMenuError(ValueError):
    """Raised when a Kaikki snapshot cannot produce an exact menu."""


def _safe_surface(value: object, normalize: Callable[[str], str]) -> str | None:
    if not isinstance(value, str) or not value.strip():
        return None
    try:
        return normalize(value)
    except (TypeError, ValueError):
        return None


def _json_values(value: object) -> list[dict[str, Any]]:
    return [item for item in value if isinstance(item, dict)] if isinstance(value, list) else []


def _sense_tags(sense: dict[str, Any]) -> set[str]:
    raw = sense.get("tags")
    return {tag for tag in raw if isinstance(tag, str)} if isinstance(raw, list) else set()


def _glosses(sense: dict[str, Any], field: str = "glosses") -> list[str]:
    raw = sense.get(field)
    return [value.strip() for value in raw if isinstance(value, str) and value.strip()] if isinstance(raw, list) else []


@dataclass(frozen=True, slots=True)
class RedirectEdge:
    target: str
    target_parts_of_speech: frozenset[str]


def _redirect_edges(
    row: dict[str, Any],
    policy: dict[str, Any],
    *,
    source_surface: str,
    normalize: Callable[[str], str],
    canonicalize: Callable[[str], str],
) -> set[RedirectEdge]:
    redirects = policy["redirects"]
    raw_word = row.get("word")
    if redirects["require_source_case_match"] and (
        not isinstance(raw_word, str)
        or canonicalize(raw_word).strip() != source_surface
    ):
        return set()
    source_pos = row.get("pos")
    allowed = redirects["target_pos_by_source_pos"].get(source_pos)
    if not isinstance(allowed, list) or not allowed:
        return set()
    reject_tags = set(redirects["reject_tags"])
    allow_if_tags = set(redirects["allow_if_tags"])
    edges: set[RedirectEdge] = set()
    for sense in _json_values(row.get("senses")):
        tags = _sense_tags(sense)
        if not (tags & FORM_TAGS):
            continue
        if tags & reject_tags and not tags & allow_if_tags:
            continue
        for field in ("form_of", "alt_of"):
            for target in _json_values(sense.get(field)):
                normalized = _safe_surface(target.get("word"), normalize)
                if normalized is not None:
                    edges.add(RedirectEdge(normalized, frozenset(allowed)))
    return edges


def _surface_grammar(row: dict[str, Any], normalize: Callable[[str], str]) -> dict[str, list[str]]:
    """Return {target headword: grammatical tags} from a row's form-of senses.

    ``_semantic_senses`` discards form-of senses because they carry no meaning,
    and with them goes Wiktionary's own analysis of the surface: ``diz`` is the
    third-person singular present indicative of ``dizer``. That is a fact about
    the surface, not about any sense, so it is kept on the analysis rather than
    on a leaf.

    It is worth keeping because it is the dictionary's grammatical claim in the
    dictionary's own tagset -- the mismatch that made the POS menu filter delete
    correct senses on common words does not arise here.
    """

    grammar: dict[str, list[str]] = {}
    for sense in _json_values(row.get("senses")):
        if not (_sense_tags(sense) & FORM_TAGS):
            continue
        tags = sorted(tag for tag in _sense_tags(sense) if tag not in FORM_TAGS)
        if not tags:
            continue
        for field in ("form_of", "alt_of"):
            for target in _json_values(sense.get(field)):
                word = target.get("word")
                if not isinstance(word, str) or not word.strip():
                    continue
                try:
                    key = normalize(word)
                except (TypeError, ValueError):
                    continue
                merged = set(grammar.get(key, ())) | set(tags)
                grammar[key] = sorted(merged)
    return grammar


def _semantic_senses(row: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        sense
        for sense in _json_values(row.get("senses"))
        if not (_sense_tags(sense) & FORM_TAGS) and _glosses(sense)
    ]


def _open_jsonl(path: Path):
    if path.suffix == ".gz":
        return gzip.open(path, "rt", encoding="utf-8")
    return path.open("r", encoding="utf-8")


def _iter_rows(path: Path, *, language_code: str) -> Iterator[dict[str, Any]]:
    with _open_jsonl(path) as stream:
        for line_number, line in enumerate(stream, start=1):
            try:
                row = json.loads(line)
            except json.JSONDecodeError as error:
                raise KaikkiMenuError(
                    f"Kaikki snapshot contains invalid JSON on line {line_number}"
                ) from error
            if not isinstance(row, dict):
                raise KaikkiMenuError(
                    f"Kaikki snapshot line {line_number} is not an object"
                )
            if row.get("lang_code") == language_code:
                yield row


_SEE_REFERENCE = re.compile(r"^See (?P<targets>[^.]+)\.$")


def _cross_references(sense: dict[str, Any]) -> list[dict[str, str]]:
    """Extract only Wiktionary's explicit ``See …`` sense redirects.

    These glosses are semantic links, not definitions. Keeping the match
    deliberately strict prevents ordinary glosses containing the verb “see”
    from becoming navigation controls in the app.
    """

    glosses = _glosses(sense)
    if len(glosses) != 1:
        return []
    match = _SEE_REFERENCE.fullmatch(glosses[0])
    if match:
        return [
            {"relation": "see", "target": target.strip()}
            for target in match.group("targets").split(",")
            if target.strip()
        ]
    projection = project_gloss(glosses[0])
    return [
        {"relation": reference.relation, "target": reference.target}
        for reference in projection.cross_references
    ]


def _display_gloss(sense: dict[str, Any]) -> str:
    glosses = _glosses(sense)
    return project_gloss(glosses[0]).display_text if glosses else ""


def _context(sense: dict[str, Any]) -> str:
    """Return a short disambiguating label, the equivalent of SpanishDict's context.

    SpanishDict publishes ``context`` on every sense; Wiktionary carries the same
    information but embedded in the prose. A nested sub-gloss is preferred when
    present, then the leading parenthetical of a raw gloss -- ``(interrogative)``,
    ``(relative)``, ``(only in subordinate clauses)`` -- then topic and qualifier
    labels. Deriving it lifts coverage from 16.5% to roughly 61% of senses, and
    the recovered labels are mostly grammatical rather than topical, which is the
    axis a bilingual dictionary's context field usually marks.
    """

    glosses = _glosses(sense)
    if len(glosses) > 1:
        return " | ".join(glosses[1:])
    for raw in _glosses(sense, "raw_glosses"):
        parenthetical = leading_parenthetical(raw, max_length=60)
        if parenthetical:
            return parenthetical
    topics = [value for value in sense.get("topics", []) if isinstance(value, str)]
    if topics:
        return ", ".join(topics)
    qualifier = sense.get("qualifier")
    if isinstance(qualifier, str) and qualifier.strip():
        return qualifier.strip()
    return ""


def _regions(sense: dict[str, Any], policy: dict[str, Any]) -> list[str]:
    """Return regional usage labels, the equivalent of SpanishDict's regions.

    Which tags count as regional is language knowledge, not adapter knowledge, so
    the list comes from the sense-menu language policy. A language that declares
    none simply gets an empty list rather than a missing field.
    """

    known = policy.get("region_tags")
    if not isinstance(known, list) or not known:
        return []
    regions = {tag for tag in _sense_tags(sense) if tag in set(known)}
    for raw in _glosses(sense, "raw_glosses"):
        parenthetical = leading_parenthetical(raw)
        if not parenthetical:
            continue
        for region in known:
            if re.search(rf"(?<!\w){re.escape(region)}(?!\w)", parenthetical):
                regions.add(region)
    return sorted(regions)


def _sense_keys(sense: dict[str, Any]) -> tuple[str, ...]:
    """Return Wiktionary's own ``{{senseid}}`` values for one sense."""

    return tuple(
        value.strip()
        for value in sense.get("senseid", [])
        if isinstance(value, str) and value.strip()
    )


def _sense_id(
    sense: dict[str, Any],
    *,
    language_code: str,
    headword: str,
    part_of_speech: str,
    provider_id_collides: bool = False,
    sense_keys_collide: bool = False,
) -> tuple[str, str]:
    """Return one stable sense ID plus its provenance reference.

    Kaikki flattens a sense's ``senseid`` list to its FIRST entry and appends a
    counter when that collides, but it does not re-check the counter against IDs
    it has already emitted. Nested sub-senses therefore share one ``id``: all of
    ``não``'s sub-senses arrive as ``en-não-pt-adv-pt:not1``. This is observed in
    16 Portuguese and 20 French entries, on common words in both.

    Wiktionary's own identifiers are not ambiguous — the discarded tail of
    ``senseid`` separates them — so a collision falls back to the full list
    rather than to a hash. Content hashing remains the last resort for senses
    that carry no usable ``senseid``, and deliberately excludes the sense's
    ordinal so that reordering an entry cannot re-key a card.
    """

    provider_id = sense.get("id")
    has_provider_id = isinstance(provider_id, str) and bool(provider_id.strip())
    if has_provider_id and not provider_id_collides:
        return provider_id, f"kaikki:{provider_id}"

    keys = _sense_keys(sense)
    if provider_id_collides and keys and not sense_keys_collide:
        joined = "|".join(keys)
        derived = f"en-{headword}-{language_code}-{part_of_speech}-{joined}"
        return derived, f"kaikki-senseid:{derived}"

    identity = canonical_content_id(
        {
            "adapter": ADAPTER_ID,
            "headword": headword,
            "part_of_speech": part_of_speech,
            "sense_keys": list(keys),
            "glosses": _glosses(sense),
            "raw_glosses": _glosses(sense, "raw_glosses"),
            "tags": sorted(_sense_tags(sense)),
            "topics": sorted(
                value for value in sense.get("topics", []) if isinstance(value, str)
            ),
        }
    ).removeprefix("sha256:")
    fallback = f"sense_{identity[:32]}"
    return fallback, f"kaikki-content:{fallback}"


def _metadata(
    row: dict[str, Any],
    sense: dict[str, Any],
    policy: dict[str, Any] | None = None,
) -> dict[str, Any]:
    metadata: dict[str, Any] = {
        "part_of_speech": row.get("pos"),
        "tags": sorted(_sense_tags(sense)),
        "topics": [value for value in sense.get("topics", []) if isinstance(value, str)],
        "raw_glosses": _glosses(sense, "raw_glosses"),
        # Declared for every language so the shape does not vary by provider.
        # Empty is a statement that this language has no regional marking, not
        # an absence of the concept.
        "context": _context(sense),
        "regions": _regions(sense, policy or {}),
        "examples": [
            item for item in (sense.get("examples") or []) if isinstance(item, dict)
        ],
        "cross_references": _cross_references(sense),
        "info_templates": [
            item for item in (sense.get("info_templates") or []) if isinstance(item, dict)
        ],
    }
    for field in ("qualifier", "sense_index"):
        value = sense.get(field)
        if isinstance(value, (str, int)) and value != "":
            metadata[field] = value
    for field in ("etymology_number", "etymology_text"):
        value = row.get(field)
        if isinstance(value, (str, int)) and value != "":
            metadata[field] = value
    return metadata


def _specialist_features(
    sense: dict[str, Any],
    policy: dict[str, Any] | None = None,
    *,
    part_of_speech: str | None = None,
) -> tuple[SpecialistFeature, ...]:
    """Delegate to the provider-neutral extractor.

    Feature typing is deliberately not the dictionary reader's job: it changes
    for different reasons and on a different cadence, and its vocabulary is
    language policy rather than code.
    """

    contextual_sense = {**sense, "part_of_speech": part_of_speech}
    glosses = _glosses(sense)
    inline = project_gloss(glosses[0]).specialist_features if glosses else ()
    return tuple(dict.fromkeys((
        *extract_wiktionary_features(
            contextual_sense, tags=sorted(_sense_tags(sense)), policy=policy
        ),
        *inline,
    )))


class KaikkiSenseMenuAdapter:
    """Resolve direct and structured form-of entries without lemma-keyed cards."""

    def __init__(
        self,
        path: Path,
        *,
        language_code: str = "fr",
        gloss_language: str = "en",
        source_edition: str = "enwiktionary",
        language_policy: dict[str, Any] | None = None,
        max_redirect_hops: int = 5,
        external_lemmas: dict[str, list[str]] | None = None,
    ) -> None:
        self.path = path.resolve()
        if not self.path.is_file():
            raise KaikkiMenuError(f"Kaikki snapshot does not exist: {self.path}")
        if max_redirect_hops < 1:
            raise ValueError("max_redirect_hops must be positive")
        self.language_code = language_code
        self.gloss_language = gloss_language
        if source_edition != "enwiktionary" or gloss_language != "en":
            raise KaikkiMenuError(
                "the current French WSD profile requires English glosses from enwiktionary"
            )
        self.source_edition = source_edition
        if not isinstance(language_policy, dict):
            raise KaikkiMenuError("an explicit sense-menu language policy is required")
        self.language_policy = language_policy
        self._normalize = normalizer_for_language(language_code)
        self._canonicalize = typography_canonicalizer_for_language(language_code)
        self.max_redirect_hops = max_redirect_hops
        # Wiktionary can only redirect from a row it has. A heavily inflected
        # language leaves most surfaces with no row at all -- Czech Wiktionary
        # holds 68,420 headwords against a language that declines everything --
        # so the redirect graph never starts and the card gets no menu. An
        # external morphology source supplies the missing first hop: CNK says
        # "policii" is a form of "policie", and the builder can take it from
        # there. Measured on Czech: 4,294 cards with no menu, of which 3,920
        # resolve to a lemma Wiktionary does hold.
        self.external_lemmas = {
            surface: tuple(lemmas) for surface, lemmas in (external_lemmas or {}).items() if lemmas
        }
        self.snapshot_content_id = file_content_id(self.path)
        # Cards whose headword set comes from fluency.surfaces.resolver; every
        # other card is built exactly as before (see SpanishDict's adapter).
        self.resolver: Any = None
        self.resolver_surfaces: frozenset[str] = frozenset()
        self.external_provenance: dict[str, str] = {}

    def _collect(
        self,
        surfaces: set[str],
        extra_first_hops: dict[str, tuple[str, ...]] | None = None,
    ) -> tuple[
        dict[str, list[dict[str, Any]]],
        dict[str, dict[str, tuple[str, ...]]],
        dict[str, dict[str, set[str] | None]],
        dict[str, int],
    ]:
        rows_by_word: dict[str, list[dict[str, Any]]] = defaultdict(list)
        surface_grammar: dict[str, dict[str, list[str]]] = defaultdict(dict)
        paths: dict[str, dict[str, tuple[str, ...]]] = {
            surface: {surface: (surface,)} for surface in surfaces
        }
        allowed_positions: dict[str, dict[str, set[str] | None]] = {
            surface: {surface: None} for surface in surfaces
        }
        for surface in surfaces:
            hops = (*self.external_lemmas.get(surface, ()), *(extra_first_hops or {}).get(surface, ()))
            for lemma in hops:  # the missing first hop
                normalized = self._normalize(lemma)
                if normalized and normalized not in paths[surface]:
                    paths[surface][normalized] = (surface, normalized)
                    allowed_positions[surface][normalized] = None
        scanned: set[str] = set()
        rows_read = 0
        passes = 0

        for _ in range(self.max_redirect_hops + 1):
            wanted = {
                headword
                for by_headword in paths.values()
                for headword in by_headword
                if headword not in scanned
            }
            if not wanted:
                break
            passes += 1
            found: dict[str, list[dict[str, Any]]] = defaultdict(list)
            for row in _iter_rows(self.path, language_code=self.language_code):
                rows_read += 1
                word = _safe_surface(row.get("word"), self._normalize)
                if word in wanted:
                    found[word].append(row)
            for word in sorted(wanted):
                rows_by_word[word].extend(found.get(word, []))
            scanned.update(wanted)

            for surface, by_headword in paths.items():
                additions: dict[str, tuple[str, ...]] = {}
                for row in found.get(surface, []):
                    for target, tags in _surface_grammar(row, self._normalize).items():
                        merged = set(surface_grammar[surface].get(target, ())) | set(tags)
                        surface_grammar[surface][target] = sorted(merged)
                addition_positions: dict[str, set[str]] = defaultdict(set)
                for headword, path in tuple(by_headword.items()):
                    if len(path) > self.max_redirect_hops:
                        continue
                    for row in found.get(headword, []):
                        source_pos = row.get("pos")
                        allowed_source = allowed_positions[surface][headword]
                        if allowed_source is not None and source_pos not in allowed_source:
                            continue
                        for edge in sorted(
                            _redirect_edges(
                                row,
                                self.language_policy,
                                source_surface=headword,
                                normalize=self._normalize,
                                canonicalize=self._canonicalize,
                            ),
                            key=lambda item: (item.target, sorted(item.target_parts_of_speech)),
                        ):
                            target = edge.target
                            if target in path:
                                continue
                            candidate = (*path, target)
                            previous = by_headword.get(target) or additions.get(target)
                            if previous is None or candidate < previous:
                                additions[target] = candidate
                            addition_positions[target].update(edge.target_parts_of_speech)
                by_headword.update(additions)
                for target, positions in addition_positions.items():
                    previous = allowed_positions[surface].get(target)
                    if previous is None and target in allowed_positions[surface]:
                        continue
                    if previous is None:
                        allowed_positions[surface][target] = set(positions)
                    else:
                        previous.update(positions)

        return (
            dict(rows_by_word),
            paths,
            allowed_positions,
            dict(surface_grammar),
            {"passes": passes, "rows_read": rows_read},
        )

    def _card_analyses(
        self,
        card: dict[str, Any],
        surface: str,
        headwords: list[str],
        rows_by_word: dict[str, list[dict[str, Any]]],
        paths: dict[str, tuple[str, ...]],
        allowed_positions: dict[str, set[str] | None],
        surface_grammar: dict[str, dict[str, list[str]]],
        stamp: dict[str, Any] | None = None,
        headword_records: dict[str, dict[str, Any]] | None = None,
    ) -> list[MenuAnalysis]:
        """Menu analyses for one card from the rows of ``headwords``.

        The legacy path passes every headword its redirect paths reached; a
        resolved card passes the resolver's set and a ``stamp``. Unstamped
        output is byte-identical to what the builder produced before.
        """
        grouped: dict[tuple[str, str], list[tuple[dict[str, Any], dict[str, Any]]]] = defaultdict(list)
        entry_counts: dict[tuple[str, str], int] = defaultdict(int)
        for headword in headwords:
            for row in rows_by_word.get(headword, []):
                part_of_speech = row.get("pos")
                if not isinstance(part_of_speech, str) or not part_of_speech:
                    continue
                allowed = allowed_positions.get(headword)
                if allowed is not None and part_of_speech not in allowed:
                    continue
                semantic = _semantic_senses(row)
                if not semantic:
                    continue
                key = (headword, part_of_speech)
                entry_counts[key] += 1
                grouped[key].extend((row, sense) for sense in semantic)

        analyses: list[MenuAnalysis] = []
        for (headword, part_of_speech), row_senses in sorted(grouped.items()):
            source_key = f"{self.language_code}:{headword}:{part_of_speech}"
            analysis_grammar = extract_surface_grammar(
                surface_grammar.get(surface, {}).get(headword, []),
                policy=self.language_policy,
            )
            provider_id_counts: Counter[str] = Counter(
                sense["id"]
                for _, sense in row_senses
                if isinstance(sense.get("id"), str) and sense["id"].strip()
            )
            sense_key_counts: Counter[tuple[str, ...]] = Counter(
                _sense_keys(sense) for _, sense in row_senses
            )
            leaves: dict[str, SenseLeaf] = {}
            for row, sense in row_senses:
                glosses = _glosses(sense)
                raw_provider_id = sense.get("id")
                provider_id_collides = (
                    isinstance(raw_provider_id, str)
                    and provider_id_counts[raw_provider_id] > 1
                )
                sense_id, source_reference = _sense_id(
                    sense,
                    language_code=self.language_code,
                    headword=headword,
                    part_of_speech=part_of_speech,
                    provider_id_collides=provider_id_collides,
                    sense_keys_collide=sense_key_counts[_sense_keys(sense)] > 1,
                )
                leaf = SenseLeaf(
                    sense_id=sense_id,
                    translation=_display_gloss(sense),
                    definition=_context(sense),
                    source_reference=source_reference,
                    provider_metadata=_metadata(row, sense, self.language_policy),
                    specialist_features=tuple(dict.fromkeys((
                        *_specialist_features(
                            sense,
                            self.language_policy,
                            part_of_speech=part_of_speech,
                        ),
                        *analysis_grammar,
                    ))),
                    metadata_accounting=metadata_accounting(
                        {**sense, "part_of_speech": part_of_speech},
                        tags=sorted(_sense_tags(sense)),
                        policy=self.language_policy,
                    ),
                )
                previous = leaves.get(sense_id)
                if previous is not None and previous != leaf:
                    raise KaikkiMenuError(
                        f"provider sense ID is not unique: {sense_id}"
                    )
                leaves[sense_id] = leaf
            analysis = MenuAnalysis(
                menu_analysis_id=build_analysis_id(
                    card_id=card["card_id"],
                    source_adapter=ADAPTER_ID,
                    source_analysis_key=source_key,
                ),
                card_id=card["card_id"],
                surface_form=surface,
                headword=headword,
                part_of_speech=part_of_speech,
                source_adapter=ADAPTER_ID,
                source_analysis_key=source_key,
                senses=tuple(leaves[key] for key in sorted(leaves)),
                provider_metadata={
                    "resolution_path": list(paths.get(headword) or (surface, headword)),
                    "resolution": "direct" if headword == surface else "structured_form_of",
                    # Declared for every analysis; empty when the surface is
                    # the headword or the dictionary offers no analysis.
                    "surface_grammar": surface_grammar.get(surface, {}).get(headword, []),
                    "allowed_parts_of_speech": (
                        None
                        if allowed_positions.get(headword) is None
                        else sorted(allowed_positions[headword])
                    ),
                    "source_entry_count": entry_counts[(headword, part_of_speech)],
                    **({"resolver": {**stamp, **(headword_records or {}).get(headword, {})}}
                       if stamp else {}),
                },
            )
            analyses.append(analysis)
        return analyses

    def build(
        self,
        cards: Iterable[dict[str, Any]],
        *,
        snapshot_id: str,
    ) -> tuple[dict[str, Any], dict[str, Any]]:
        card_list = list(cards)
        by_surface: dict[str, dict[str, Any]] = {}
        for card in card_list:
            surface = _safe_surface(card.get("surface_key"), self._normalize)
            if surface is None or surface != card.get("surface_key"):
                raise KaikkiMenuError("inventory surface is not canonically normalized")
            if surface in by_surface:
                raise KaikkiMenuError(f"duplicate inventory surface: {surface}")
            by_surface[surface] = card

        extra: dict[str, tuple[str, ...]] = {}
        wanted = set(by_surface)
        if self.resolver is not None:
            # Rows are read in passes over the dump, so an override's headwords
            # and an expansion's target must be asked for up front.
            for surface in self.resolver_surfaces:
                heads = self.resolver.declared_headwords(surface)
                if heads:
                    extra[surface] = tuple(self._normalize(h) or h for h in heads)
                target = self.resolver.expansion_target(surface)
                if target:
                    wanted.add(target)
        rows_by_word, paths, allowed_positions, surface_grammar, scan = self._collect(
            wanted, extra
        )
        if self.resolver is not None and isinstance(self.resolver.source, KaikkiHeadwordSource):
            self.resolver.source.bind(rows_by_word, paths, allowed_positions,
                                      self.external_lemmas, self._normalize)
        menu_cards: list[dict[str, Any]] = []
        per_surface: list[dict[str, Any]] = []
        total_analyses = 0
        total_senses = 0

        for surface, card in by_surface.items():
            resolution = None
            if self.resolver is not None and surface in self.resolver_surfaces:
                resolution = self.resolver.resolve(surface)
            if resolution is None:
                analyses = self._card_analyses(
                    card, surface, sorted(paths[surface]), rows_by_word, paths[surface],
                    allowed_positions[surface], surface_grammar)
            elif resolution.strategy in (HEADWORDS, EXPANSION):
                target = resolution.expanded_to or surface
                records = {h.headword: {"headword_provenance": h.provenance, "headword_trust": h.trust,
                                        "headword_detail": h.detail or None}
                           for h in resolution.headwords}
                analyses = self._card_analyses(
                    card, surface, [h.headword for h in resolution.headwords], rows_by_word,
                    paths.get(target, {}), allowed_positions.get(target, {}), surface_grammar,
                    stamp=resolution.stamp(), headword_records=records)
            elif resolution.strategy == DECLARED_GLOSS:
                analyses = declared_gloss_analyses(card["card_id"], surface, resolution)
            elif resolution.strategy == ENTITY:
                analyses = declared_entity_analyses(card["card_id"], surface, resolution)
            else:
                analyses = []

            total_analyses += len(analyses)
            sense_count = sum(len(analysis.senses) for analysis in analyses)
            total_senses += sense_count
            menu_card = {
                "card_id": card["card_id"],
                "surface_form": surface,
                "analyses": [analysis.to_dict() for analysis in analyses],
            }
            surface_report = {
                "card_id": card["card_id"],
                "surface_form": surface,
                "analysis_count": len(analyses),
                "sense_count": sense_count,
                "status": "ready" if analyses else "no_menu",
            }
            if resolution is not None:
                menu_card["resolution"] = resolution.to_dict()
                surface_report.update(strategy=resolution.strategy, coverage=resolution.coverage,
                                      reason=resolution.reason or None)
            menu_cards.append(menu_card)
            per_surface.append(surface_report)

        payload = {
            "menu_version": MENU_VERSION,
            "metadata_contract": METADATA_CONTRACT_VERSION,
            "language": self.language_code,
            "gloss_language": self.gloss_language,
            "source_edition": self.source_edition,
            "source_adapter": ADAPTER_ID,
            "snapshot_id": snapshot_id,
            "snapshot_content_id": self.snapshot_content_id,
            "language_policy_id": self.language_policy.get("policy_id"),
            "language_policy_content_id": canonical_content_id(self.language_policy),
            "cards": menu_cards,
        }
        report = {
            "report_version": REPORT_VERSION,
            "language": self.language_code,
            "source_adapter": ADAPTER_ID,
            "source_edition": self.source_edition,
            "snapshot_id": snapshot_id,
            "snapshot_content_id": self.snapshot_content_id,
            "inventory_cards": len(card_list),
            "cards_ready": sum(item["status"] == "ready" for item in per_surface),
            "cards_without_menu": sum(item["status"] == "no_menu" for item in per_surface),
            "analysis_count": total_analyses,
            "sense_count": total_senses,
            "scan_passes": scan["passes"],
            "rows_read_across_passes": scan["rows_read"],
            "fallbacks": [],
            "per_surface": per_surface,
        }
        return payload, report


class KaikkiHeadwordSource:
    """Wiktionary (Kaikki) as a ``fluency.surfaces.resolver.HeadwordSource``.

    Provider parity with ``SpanishDictHeadwordSource``: the headword set is the
    entries the adapter's redirect paths reach that carry senses. Each is a
    Wiktionary statement -- the surface's own row, or a ``form_of`` chain -- or
    an external morphology source's first hop (CNK for Czech), which the
    ledger records with its provenance. All are ``provider`` trust: a published
    source stated them; we inferred none (proposal 0003 §10).

    Kaikki is a complete dump, so a surface with no sense-bearing entry is
    ``absent`` for that edition, never ``unfetched``. The source is bound to
    the adapter's scan inside ``build`` because rows are read in passes.
    """

    provider = "wiktionary"
    coverage_kind = COMPLETE_DUMP

    def __init__(self, external_provenance: dict[str, str] | None = None) -> None:
        self.external_provenance = dict(external_provenance or {})
        self._bound = False

    def bind(self, rows_by_word, paths, allowed_positions, external_lemmas, normalize) -> None:
        self.rows_by_word, self.paths, self.allowed = rows_by_word, paths, allowed_positions
        self.external = {surface: {normalize(l) or l for l in lemmas}
                         for surface, lemmas in (external_lemmas or {}).items()}
        self._bound = True

    def _has_senses(self, headword: str, allowed: set[str] | None = None) -> bool:
        return any(
            isinstance(row.get("pos"), str) and row.get("pos")
            and (allowed is None or row.get("pos") in allowed)
            and _semantic_senses(row)
            for row in self.rows_by_word.get(headword, [])
        )

    def declare(self, surface: str) -> ProviderDeclaration:
        if not self._bound:
            raise KaikkiMenuError("KaikkiHeadwordSource used before the adapter scanned the dump")
        heads = []
        for headword, path in sorted((self.paths.get(surface) or {}).items()):
            if not self._has_senses(headword, (self.allowed.get(surface) or {}).get(headword)):
                continue
            if headword == surface:
                provenance, detail, relation = "wiktionary-self", "", "self"
            elif len(path) == 2 and headword in self.external.get(surface, ()):
                provenance, relation = "external-lemma", "form"
                detail = self.external_provenance.get(surface, "ledger lemma")
            else:
                provenance, detail, relation = "wiktionary-form-of", " -> ".join(path), "form"
            heads.append(Headword(headword, provenance, _trust.PROVIDER, detail, relation))
        return ProviderDeclaration(surface, tuple(heads), MENU if heads else ABSENT,
                                   {"paths": len(self.paths.get(surface) or {})})

    def has_entry(self, headword: str, surface: str | None = None) -> bool:
        return self._has_senses(headword)
