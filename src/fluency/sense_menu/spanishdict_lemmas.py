"""Which lemmas SpanishDict declares for a surface -- and nothing it merely suggests.

For Spanish, SpanishDict is the source of truth for lemmas, corrected only by a
hand-written ``headwords`` entry. A surface may have several lemmas (*condones* is
*condón* and a form of *condonar*); every one SpanishDict declares is kept, and
WSD chooses per sentence among the menus they bring.

What SpanishDict *declares* about a surface is narrow, and that is the point:

1. **Its own page for the exact surface**, when the page was not a spelling
   substitution and is a Spanish entry. On that page only two headwords count:
   one equal to the surface (ignoring case, ``¡¿!?`` and abbreviation dots, so
   ``¡Uy!`` is *uy* and ``Ud.`` is *ud*), and one the page states is the
   surface's conjugation or inflection. Any other headword is SpanishDict
   answering about a different word -- *tómatelo* answered with *tomate*,
   *cógelo* with *cómelo* -- and is recorded as rejected, never used.
2. **Its conjugation table**, an exact form -> verb lookup, consulted only where
   the page gave no lemma. Where the page answers, the page is SpanishDict's
   answer about that surface; the table would add an infinitive to nouns that
   happen to share a verb form's spelling (decision 0021: *chica*, *chicar*).
3. **Enclitic surfaces with no page lemma.** SpanishDict files the verb, not the
   bundle, so it has no page for *decírtelo*. Stripping the pronouns must leave
   an exact form of the table that is an imperative, infinitive or gerund of
   exactly one verb; otherwise the rule abstains. When the first pronoun is
   reflexive for that host, the pronominal headword (*quedarse*) is declared
   too, if SpanishDict files it.

A hand-written ``headwords`` entry (``fluency.surfaces.declared``) replaces
all of the above for its surface. Anything left unresolved is declared
``no_lemma`` and queued for one, never guessed.

Each lemma carries its trust (``fluency.surfaces.trust``): what SpanishDict
states is ``provider``; the enclitic rule's answer is ``derived``; an override
is ``curated``.
"""

from __future__ import annotations

import unicodedata
from dataclasses import dataclass
from typing import Any, Iterable, Mapping, Sequence

from fluency.surfaces import trust as _trust
from fluency.surfaces.resolver import (
    ABSENT, FETCHED_CACHE, MENU, UNFETCHED, Headword, ProviderDeclaration,
)

RULE_VERSION = "spanishdict-declared-lemma/v1"

OVERRIDE = "override"
PAGE_SELF = "spanishdict-page-self"
PAGE_RELATION = "spanishdict-page-declared-relation"
CONJUGATION_TABLE = "spanishdict-conjugation-table"
ENCLITIC_HOST = "spanishdict-conjugation-table-enclitic-host"
REFLEXIVE_HEADWORD = "spanishdict-pronominal-headword"

# Statuses. Only "override" and "declared" and "enclitic" carry lemmas.
STATUS_OVERRIDE = "override"
STATUS_DECLARED = "declared"
STATUS_ENCLITIC = "enclitic"
STATUS_ENCLITIC_AMBIGUOUS = "enclitic_ambiguous"
STATUS_NO_LEMMA = "no_lemma"

DECLARED_RELATIONS = frozenset({"conjugation", "inflection"})
HOST_MOODS = frozenset({"imperativo", "infinitivo", "gerundio"})
ENCLITICS = ("nos", "les", "los", "las", "os", "me", "te", "se", "le", "lo", "la")
REFLEXIVE_PERSONS = {"me": {"1s"}, "te": {"2s"}, "nos": {"1p"}, "os": {"2p"}, "se": {"3s", "3p"}}
_PUNCTUATION = str.maketrans("", "", "¡!¿?.")


def headword_key(text: str) -> str:
    """Comparison key for "is this headword the surface itself"."""
    return unicodedata.normalize("NFC", str(text)).translate(_PUNCTUATION).strip().casefold()


def deaccent(word: str) -> str:
    """Drop stress accents, keeping ñ and ü, which are letters rather than stress."""
    out = []
    for ch in unicodedata.normalize("NFD", word):
        if unicodedata.combining(ch) and ch not in {"̃", "̈"}:
            continue
        out.append(ch)
    return unicodedata.normalize("NFC", "".join(out))


RELATION = {
    OVERRIDE: "override",
    PAGE_SELF: "self",
    PAGE_RELATION: "form",
    CONJUGATION_TABLE: "form",
    ENCLITIC_HOST: "enclitic",
    REFLEXIVE_HEADWORD: "enclitic",
}

TRUST = {
    OVERRIDE: _trust.CURATED,
    PAGE_SELF: _trust.PROVIDER,
    PAGE_RELATION: _trust.PROVIDER,
    CONJUGATION_TABLE: _trust.PROVIDER,
    ENCLITIC_HOST: _trust.DERIVED,
    REFLEXIVE_HEADWORD: _trust.DERIVED,
}


@dataclass(frozen=True)
class DeclaredLemma:
    lemma: str
    provenance: str
    detail: str = ""

    @property
    def trust(self) -> str:
        return TRUST[self.provenance]


@dataclass(frozen=True)
class LemmaResolution:
    surface: str
    status: str
    lemmas: tuple[DeclaredLemma, ...] = ()
    rejected_headwords: tuple[str, ...] = ()
    # The page answered, but SpanishDict's stated relation was not kept when it
    # was fetched, so a declared form cannot be told from a substitution. A
    # refetch that records the relation settles it.
    relation_unknown: tuple[str, ...] = ()
    page_state: str = "unfetched"  # answered | substituted | wrong_language | unfetched
    candidates: tuple[str, ...] = ()
    rule_version: str = RULE_VERSION

    @property
    def lemma_names(self) -> list[str]:
        return [item.lemma for item in self.lemmas]

    @property
    def needs_refetch(self) -> bool:
        """SpanishDict has not yet said, in a form we kept, what this surface is.

        True whatever the status: a lemma from the conjugation table alone for a
        never-fetched surface is SpanishDict's table, not its answer about the
        word -- *borda* is a form of *bordar* and, in every line, the noun
        (*por la borda*). And a page headword that is neither the surface nor
        a declared relation was stored by a scrape that did not keep relations,
        so asking again is how a redirect (*buen* -> bueno) is told from a
        substitution (*tómatelo* -> tomate).
        """
        return (self.page_state == "unfetched" or bool(self.relation_unknown)
                or bool(self.rejected_headwords))

    def to_dict(self) -> dict[str, Any]:
        return {
            "surface": self.surface,
            "status": self.status,
            "lemmas": [
                {"lemma": item.lemma, "provenance": item.provenance, "trust": item.trust,
                 "detail": item.detail}
                for item in self.lemmas
            ],
            "rejected_headwords": list(self.rejected_headwords),
            "relation_unknown": list(self.relation_unknown),
            "page_state": self.page_state,
            "candidates": list(self.candidates),
            "needs_refetch": self.needs_refetch,
            "rule_version": self.rule_version,
        }


@dataclass
class SpanishDictLemmaRule:
    """Apply the declared-lemma rule to one surface at a time, offline."""

    conjugation_reverse: Mapping[str, Any]
    known_headwords: frozenset[str] | set[str] = frozenset()

    def __post_init__(self) -> None:
        self._exact: dict[str, list[str]] = {}
        self._rows_deaccented: dict[str, list[dict[str, Any]]] = {}
        self.table_has_moods = False
        for form, rows in self.conjugation_reverse.items():
            if not isinstance(rows, list):
                continue
            for row in rows:
                if not isinstance(row, dict):
                    continue
                lemma = str(row.get("lemma") or "").strip()
                if not lemma:
                    continue
                exact = self._exact.setdefault(str(form).strip().casefold(), [])
                if lemma not in exact:
                    exact.append(lemma)
                self._rows_deaccented.setdefault(deaccent(str(form).strip().casefold()), []).append(row)
                if row.get("mood"):
                    self.table_has_moods = True

    # ------------------------------------------------------------------ page

    def _page(self, surface: str, page: Mapping[str, Any] | None, flags: Iterable[str]):
        flags = [str(flag) for flag in flags or ()]
        if any(flag.startswith("spelling_substitution") for flag in flags):
            return "substituted", [], [], []
        if page is None:
            return ("wrong_language" if "entry_lang_not_spanish" in flags else "unfetched"), [], [], []
        language = str(page.get("entry_lang") or "").strip()
        if (language and language != "es") or "entry_lang_not_spanish" in flags:
            return "wrong_language", [], [], []

        key = headword_key(surface)
        declared: list[DeclaredLemma] = []
        stated: dict[str, str] = {}
        unknown: list[str] = []
        for result in page.get("possible_results") or []:
            if isinstance(result, str):
                result = {"result": result}
            if not isinstance(result, dict):
                continue
            head = str(result.get("headword") or result.get("result") or "").strip()
            relation = str(result.get("heuristic") or "").strip().casefold()
            if not head:
                continue
            if relation in DECLARED_RELATIONS:
                stated[head] = relation
            elif not relation and headword_key(head) != key:
                unknown.append(head)

        rejected: list[str] = []
        seen: set[str] = set()

        def add(lemma: str, provenance: str, detail: str = "") -> None:
            if lemma not in seen:
                seen.add(lemma)
                declared.append(DeclaredLemma(lemma, provenance, detail))

        for analysis in page.get("dictionary_analyses") or []:
            head = str((analysis or {}).get("headword") or "").strip() if isinstance(analysis, dict) else ""
            if not head:
                continue
            if headword_key(head) == key:
                add(head, PAGE_SELF)
            elif head in stated:
                add(head, PAGE_RELATION, stated[head])
            elif head not in unknown and head not in rejected:
                rejected.append(head)
        for head, relation in stated.items():
            add(head, PAGE_RELATION, relation)
        unknown = [head for head in unknown if head not in seen]
        return "answered", declared, rejected, unknown

    # -------------------------------------------------------------- enclitics

    def _strip(self, surface: str) -> list[tuple[str, tuple[str, ...]]]:
        """Every (host, pronouns-after-host) split with up to three pronouns."""
        out: list[tuple[str, tuple[str, ...]]] = []
        frontier: list[tuple[str, tuple[str, ...]]] = [(surface.casefold(), ())]
        for _ in range(3):
            nxt = []
            for stem, tail in frontier:
                for clitic in ENCLITICS:
                    if stem.endswith(clitic) and len(stem) > len(clitic) + 1:
                        split = (stem[: -len(clitic)], (clitic,) + tail)
                        nxt.append(split)
                        out.append(split)
            frontier = nxt
        return out

    def _enclitic(self, surface: str) -> tuple[str, list[DeclaredLemma], list[str]]:
        matches: dict[str, list[tuple[str, dict[str, Any], tuple[str, ...]]]] = {}
        for host, pronouns in self._strip(surface):
            # First-person plural drops its -s before nos: vayámonos -> vayamos.
            bases = [host] + ([host + "s"] if pronouns[0] == "nos" else [])
            for base in bases:
                for row in self._rows_deaccented.get(deaccent(base), []):
                    mood = str(row.get("mood") or "").casefold()
                    if self.table_has_moods and mood not in HOST_MOODS:
                        continue
                    lemma = str(row.get("lemma")).strip()
                    matches.setdefault(lemma, []).append((base, row, pronouns))
        if not matches:
            return STATUS_NO_LEMMA, [], []
        if len(matches) > 1:
            return STATUS_ENCLITIC_AMBIGUOUS, [], sorted(matches)
        lemma, found = next(iter(matches.items()))
        base, row, pronouns = found[0]
        mood = str(row.get("mood") or "?")
        detail = f"{surface} = {base} + {'+'.join(pronouns)} ({mood})"
        lemmas = [DeclaredLemma(lemma, ENCLITIC_HOST, detail)]
        reflexive = self._reflexive(lemma, found)
        if reflexive:
            lemmas.append(DeclaredLemma(reflexive, REFLEXIVE_HEADWORD, detail))
        return STATUS_ENCLITIC, lemmas, [lemma]

    def _reflexive(self, lemma: str, found) -> str | None:
        """quedarse for quédatelo: the pronoun next to the host is reflexive.

        On an imperative the addressee is the subject, so a pronoun of the
        addressee's person can only be reflexive: quédate, vayámonos. On an
        infinitive or gerund the subject is not in the word, so me/te/nos/os
        cannot be told from an indirect object (decírtelo is "to tell it to
        you", not *decirse*). Only se is reflexive there.
        """
        pronominal = lemma + "se"
        if pronominal not in self.known_headwords:
            return None
        for _base, row, pronouns in found:
            first = pronouns[0]
            mood = str(row.get("mood") or "").casefold()
            if mood in {"infinitivo", "gerundio"}:
                if first == "se":
                    return pronominal
                continue
            if mood == "imperativo" and str(row.get("person") or "") in REFLEXIVE_PERSONS.get(first, ()):
                return pronominal
        return None

    # ------------------------------------------------------------------ public

    def resolve(
        self,
        surface: str,
        page: Mapping[str, Any] | None = None,
        flags: Iterable[str] = (),
        override: Sequence[str] | None = None,
    ) -> LemmaResolution:
        page_state, declared, rejected, unknown = self._page(surface, page, flags)
        if override:
            return LemmaResolution(
                surface, STATUS_OVERRIDE,
                tuple(DeclaredLemma(lemma, OVERRIDE) for lemma in override),
                tuple(rejected), tuple(unknown), page_state,
            )
        if declared:
            return LemmaResolution(surface, STATUS_DECLARED, tuple(declared),
                                   tuple(rejected), tuple(unknown), page_state)
        table = self._exact.get(surface.strip().casefold(), [])
        if table:
            return LemmaResolution(
                surface, STATUS_DECLARED,
                tuple(DeclaredLemma(lemma, CONJUGATION_TABLE) for lemma in table),
                tuple(rejected), tuple(unknown), page_state,
            )
        status, lemmas, candidates = self._enclitic(surface)
        return LemmaResolution(surface, status, tuple(lemmas), tuple(rejected),
                               tuple(unknown), page_state, tuple(candidates))


class SpanishDictHeadwordSource:
    """SpanishDict as a ``fluency.surfaces.resolver.HeadwordSource``.

    Reads a pinned snapshot only. SpanishDict is a fetched cache, so a surface
    it was never asked about is ``unfetched``, not ``absent``.
    """

    provider = "spanishdict"

    def __init__(
        self,
        rule: SpanishDictLemmaRule,
        surface_cache: Mapping[str, Any],
        headword_cache: Mapping[str, Any],
        flags: Mapping[str, Sequence[str]] | None = None,
    ) -> None:
        self.coverage_kind = FETCHED_CACHE
        self.rule = rule
        self.surface_cache = surface_cache
        self.headword_cache = headword_cache
        self.flags = flags or {}

    def page(self, surface: str) -> Mapping[str, Any] | None:
        page = self.surface_cache.get(surface)
        return page if isinstance(page, dict) else None

    def lemmas(self, surface: str) -> LemmaResolution:
        return self.rule.resolve(surface, self.page(surface), self.flags.get(surface, ()))

    def declare(self, surface: str) -> ProviderDeclaration:
        found = self.lemmas(surface)
        heads = tuple(Headword(item.lemma, item.provenance, item.trust, item.detail,
                               RELATION[item.provenance])
                      for item in found.lemmas)
        if heads:
            coverage = MENU
        elif found.page_state == "unfetched":
            coverage = UNFETCHED
        else:
            coverage = ABSENT
        return ProviderDeclaration(surface, heads, coverage, {
            "rule_version": found.rule_version,
            "status": found.status,
            "page_state": found.page_state,
            "rejected_headwords": list(found.rejected_headwords),
            "relation_unknown": list(found.relation_unknown),
            "enclitic_candidates": list(found.candidates),
            "needs_refetch": found.needs_refetch,
        })

    def page_analyses(self, surface: str, headword: str) -> list[dict[str, Any]]:
        """The surface page's own analyses under ``headword`` (self or declared relation)."""
        page = self.page(surface) or {}
        return [a for a in page.get("dictionary_analyses") or []
                if isinstance(a, dict) and str(a.get("headword") or "").strip() == headword]

    def has_entry(self, headword: str, surface: str | None = None) -> bool:
        if isinstance(self.headword_cache.get(headword), dict):
            return True
        return bool(surface and self.page_analyses(surface, headword))
