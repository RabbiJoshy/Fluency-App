"""A language pair learning its own sound correspondences, from spelling alone.

``CognatePolicy`` carries ``target_skeleton`` and ``known_skeleton``: ordered
rewrite rules mapping two orthographies onto a shared alphabet, so that Czech
``h`` can answer Polish ``g``. They work, and somebody has to write them. That
is the one part of this system that does not scale — a new pair scores badly
until a person sits down with both alphabets.

This module derives the same thing from data, with no rules, no IPA, no
pronunciation dictionary and no labelled cognates. Four steps:

    1. seed     take every candidate pair that already looks alike
    2. align    Levenshtein backtrace, giving aligned symbol pairs
    3. score    PMI per correspondence: how much more often does x meet y
                than chance would put them together?
    4. re-seed  rescore with what was learned, and learn again

Step 3 has one detail that decides whether this works at all. PMI must be
scaled across the **non-identity** correspondences only. Identity is already
free, and leaving it in the scale squashes every real correspondence against the
ceiling — measured, that is the difference between 0.53 and 0.62 recall, which
is the difference between a dud and a tier worth shipping.

What it finds on Czech/Polish, unsupervised:

    v>w (0.15)   l>ł (0.25)   h>g (0.35)   i>y (0.38)
    t>c (0.50)   z>s (0.53)   s>z (0.53)

Those are the hand-written rules, rediscovered. On its own this scores 0.616
recall where the hand table scores 0.614, at the same precision — and the two
still combine, because they are wrong about different words.

The seeding is unsupervised on purpose. Using known cognates as the seed would
make this a supervised model that cannot run for a pair with no cognate list,
which is exactly the pair it exists to serve.
"""

from __future__ import annotations

import json
import math
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Iterable, Mapping, Sequence


CORRESPONDENCE_SCHEMA = "sound-correspondences/v1"

# The alignment's stand-in for "nothing here". Never scored: an insertion or a
# deletion costs a full symbol whatever the pair, because a missing sound is
# missing however regular its neighbours are.
GAP = "∅"

# A correspondence seen fewer times than this is coincidence, not a rule.
DEFAULT_MINIMUM_COUNT = 5
# How alike two words must already look to be taken as evidence.
DEFAULT_SEED_THRESHOLD = 0.75
# The floor a correspondence can be discounted to. Not zero: a regular
# correspondence is cheap, never free, or two words differing only in it would
# be indistinguishable from the same word.
BEST_COST = 0.15


def align(left: Sequence[str], right: Sequence[str]) -> list[tuple[str, str]]:
    """Levenshtein backtrace as aligned symbol pairs, gaps included."""

    rows, columns = len(left), len(right)
    grid = [[0] * (columns + 1) for _ in range(rows + 1)]
    for row in range(rows + 1):
        grid[row][0] = row
    for column in range(columns + 1):
        grid[0][column] = column
    for row in range(1, rows + 1):
        for column in range(1, columns + 1):
            grid[row][column] = min(
                grid[row - 1][column] + 1,
                grid[row][column - 1] + 1,
                grid[row - 1][column - 1] + (left[row - 1] != right[column - 1]),
            )

    row, column = rows, columns
    pairs: list[tuple[str, str]] = []
    while row > 0 or column > 0:
        if (
            row > 0
            and column > 0
            and grid[row][column]
            == grid[row - 1][column - 1] + (left[row - 1] != right[column - 1])
        ):
            pairs.append((left[row - 1], right[column - 1]))
            row -= 1
            column -= 1
        elif row > 0 and grid[row][column] == grid[row - 1][column] + 1:
            pairs.append((left[row - 1], GAP))
            row -= 1
        else:
            pairs.append((GAP, right[column - 1]))
            column -= 1
    pairs.reverse()
    return pairs


@dataclass(frozen=True, slots=True)
class Correspondences:
    """What one language pair costs to cross, learned rather than declared."""

    target_language: str
    known_language: str
    costs: Mapping[tuple[str, str], float]
    seed_count: int = 0
    rounds: int = 0

    def cost(self, left: str, right: str) -> float:
        if left == right:
            return 0.0
        return self.costs.get((left, right), 1.0)

    def similarity(self, left: str, right: str) -> float:
        """Normalised edit distance under the learned substitution costs."""

        if not left or not right:
            return 0.0
        previous = [float(column) for column in range(len(right) + 1)]
        for row, symbol_left in enumerate(left, 1):
            current = [float(row)]
            for column, symbol_right in enumerate(right, 1):
                current.append(
                    min(
                        previous[column] + 1.0,
                        current[column - 1] + 1.0,
                        previous[column - 1] + self.cost(symbol_left, symbol_right),
                    )
                )
            previous = current
        return max(0.0, 1.0 - previous[-1] / max(len(left), len(right)))

    def regular(self, limit: int = 20) -> list[tuple[str, str, float]]:
        """The cheapest correspondences, for reading and for the layer."""

        ranked = sorted(self.costs.items(), key=lambda item: item[1])
        return [(left, right, cost) for (left, right), cost in ranked[:limit]]

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema": CORRESPONDENCE_SCHEMA,
            "target_language": self.target_language,
            "known_language": self.known_language,
            "seed_count": self.seed_count,
            "rounds": self.rounds,
            # Tab-joined because a correspondence is a pair and JSON keys are
            # not. Tab cannot occur in a surface form.
            "costs": {f"{left}\t{right}": round(cost, 4) for (left, right), cost in self.costs.items()},
        }

    @classmethod
    def from_dict(cls, value: Mapping[str, Any]) -> "Correspondences":
        costs: dict[tuple[str, str], float] = {}
        for key, cost in (value.get("costs") or {}).items():
            left, _, right = str(key).partition("\t")
            if left and right:
                costs[(left, right)] = float(cost)
        return cls(
            target_language=str(value.get("target_language", "")),
            known_language=str(value.get("known_language", "")),
            costs=costs,
            seed_count=int(value.get("seed_count", 0)),
            rounds=int(value.get("rounds", 0)),
        )

    def write(self, path: Path | str) -> None:
        target = Path(path)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(
            json.dumps(self.to_dict(), ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )

    @classmethod
    def read(cls, path: Path | str) -> "Correspondences":
        return cls.from_dict(json.loads(Path(path).read_text(encoding="utf-8")))


def _tally(
    seeds: Iterable[tuple[str, str]],
    minimum_count: int,
) -> dict[tuple[str, str], float]:
    """PMI per non-identity correspondence, scaled into a cost in [BEST_COST, 1]."""

    joint: Counter[tuple[str, str]] = Counter()
    left_marginal: Counter[str] = Counter()
    right_marginal: Counter[str] = Counter()
    for left, right in seeds:
        for symbol_left, symbol_right in align(left, right):
            joint[(symbol_left, symbol_right)] += 1
            left_marginal[symbol_left] += 1
            right_marginal[symbol_right] += 1

    total = sum(joint.values())
    if not total:
        return {}

    scores: dict[tuple[str, str], float] = {}
    for (symbol_left, symbol_right), count in joint.items():
        if symbol_left == GAP or symbol_right == GAP:
            continue
        if symbol_left == symbol_right or count < minimum_count:
            continue
        expected = (left_marginal[symbol_left] / total) * (right_marginal[symbol_right] / total)
        if expected <= 0:
            continue
        scores[(symbol_left, symbol_right)] = math.log((count / total) / expected)

    if not scores:
        return {}
    highest = max(scores.values())
    lowest = min(scores.values())
    span = highest - lowest
    if span <= 0:
        # One correspondence, or several that are equally surprising. There is
        # no ranking to express, and every one of them cleared the count
        # threshold, so they are all regular. Scaling across a zero span would
        # instead price them all at a full substitution and withdraw the tier.
        return {pair: BEST_COST for pair in scores}
    return {
        pair: BEST_COST + (1.0 - BEST_COST) * (1.0 - (score - lowest) / span)
        for pair, score in scores.items()
    }


def learn_correspondences(
    candidates: Iterable[tuple[str, str]],
    *,
    target_language: str,
    known_language: str,
    baseline: Callable[[str, str], float],
    normalise: Callable[[str], str] = lambda word: word,
    seed_threshold: float = DEFAULT_SEED_THRESHOLD,
    minimum_count: int = DEFAULT_MINIMUM_COUNT,
    rounds: int = 2,
) -> Correspondences:
    """Learn a pair's correspondences from candidates that already look alike.

    ``baseline`` is the similarity used to choose the first seeds — the pair's
    existing orthographic measure. After the first round the learned costs join
    it, so a pair found only through a correspondence discovered in round one
    becomes evidence in round two. Two rounds is where the Czech/Polish table
    stopped growing; more is allowed and costs only time.
    """

    pool = [(normalise(target), normalise(known)) for target, known in candidates]
    pool = [(target, known) for target, known in pool if target and known]

    learned = Correspondences(
        target_language=target_language,
        known_language=known_language,
        costs={},
    )
    seeds: list[tuple[str, str]] = []
    for round_number in range(1, max(1, rounds) + 1):
        seeds = [
            (target, known)
            for target, known in pool
            if max(baseline(target, known), learned.similarity(target, known)) >= seed_threshold
        ]
        if not seeds:
            break
        learned = Correspondences(
            target_language=target_language,
            known_language=known_language,
            costs=_tally(seeds, minimum_count),
            seed_count=len(seeds),
            rounds=round_number,
        )
    return learned


def correspondences_path(config_root: Path, target_language: str, known_language: str) -> Path:
    """Beside the policy, because it is the same kind of thing: pair-specific,
    derived once, and read by every later run rather than recomputed."""

    return (
        Path(config_root)
        / "cognates"
        / "correspondences"
        / f"{target_language}-{known_language}.json"
    )


def load_correspondences(
    config_root: Path,
    target_language: str,
    known_language: str,
) -> Correspondences | None:
    """The learned table for a pair, or ``None`` where none has been derived.

    ``None`` rather than an empty table: absent means this tier never ran, which
    is a different statement from "ran and found no correspondences", and the
    coverage report says which.
    """

    path = correspondences_path(config_root, target_language, known_language)
    if not path.is_file():
        return None
    return Correspondences.read(path)
