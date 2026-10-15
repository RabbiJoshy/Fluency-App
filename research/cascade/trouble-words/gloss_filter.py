"""Which Wiktionary glosses a grammar-word label may show. Shared by every labeller.

Two kinds of gloss are not a meaning:
- notes about the entry ("form of", "inflection of", "Used other than figuratively or
  idiomatically: see a, ti.", "contraction of", "misspelling"): dropped;
- pointers to another entry ("alternative spelling of enseguida", "synonym of o tempo
  inteiro"): replaced by that entry's first gloss, or dropped when the target has none.
  Obsolete, archaic and dated spellings are not followed: in modern text the words are
  usually literal ("em quanto tempo" is not "enquanto").

An entry that has a literal-use note ("Used other than figuratively or idiomatically") is
usually meant literally in running text (*a ti* "to you", not "thank you"), so the whole
entry is dropped. A labeller keeps the idioms that dominate by listing them (IDIOMS).
"""

from __future__ import annotations

import json
import re

SKIP = re.compile(r"form of|inflection of|spelling of|synonym of|combined with|contraction of|misspelling|Used other than", re.I)
LITERAL = "Used other than figuratively or idiomatically"
POINTER = re.compile(r"^(?:(?:alternative|nonstandard|rare|informal)\s+)*"
                     r"(?:form|spelling)\s+of\s+(.+?)\s*$|^synonym of\s+(.+?)\s*$", re.I)


def target(gloss: str) -> str | None:
    m = POINTER.match(gloss)
    if not m:
        return None
    return re.sub(r"\s*\(.*$", "", m.group(1) or m.group(2)).strip(" .:;").lower()  # 'donde (“where”)' -> 'donde'


class Glosses:
    """First real gloss per headword in one Kaikki extract, for following pointers."""

    def __init__(self, path: str):
        self.first: dict[str, str] = {}
        self.idiom: dict[str, str] = {}  # entries with a literal-use note: their first idiomatic gloss
        for line in open(path):
            e = json.loads(line)
            w = e["word"].lower()
            glosses = [g for s in e.get("senses", []) for g in s.get("glosses", [])]
            gl = self._real(glosses)
            if gl and any(g.startswith(LITERAL) for g in glosses):
                self.idiom.setdefault(w, gl[0])
            if gl and w not in self.first:
                self.first[w] = gl[0]

    @staticmethod
    def _real(glosses):
        return [g for g in glosses if not target(g) and not SKIP.search(g)]

    def clean(self, glosses) -> list[str]:
        glosses = list(glosses)
        if any(g.startswith(LITERAL) for g in glosses):
            return []
        real = self._real(glosses)
        if real:
            return real
        for g in glosses:
            t = target(g)
            if t and t in self.first:
                return [self.first[t]]
        return []

    def senses(self, senses):
        """Clean each sense independently; entry notes cannot erase other senses.

        Audited es/pt callers opt in. Other languages retain clean's behaviour.
        """
        result = []
        for sense in senses:
            if set(sense.get("tags", [])) & {"obsolete", "archaic", "dated", "misspelling"}:
                continue
            result.extend(self.clean(sense.get("glosses", [])))
        return result
