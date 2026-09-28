"""Surface scorers: how alike two written words look, one module per method.

A cognate policy names the scorer it uses (``surface_scorer``), so a pair can
move to a better method by editing its own file, and a new method is added by
creating a module here. Nothing lists the scorers: they are found by walking
this package, and each module declares the id it answers to.

Every scorer has the same shape::

    SCORER_ID = "name/v1"
    def score(target_word, known_word, policy, *, target_sounds=(),
              known_sounds=(), correspondences=None) -> float

The current default for English pairs, ``edit-distance/v1``, is provisional and
its owner is not satisfied with it. See
``docs/decisions/0027-surface-similarity-scorer.md`` for why, and for what a
replacement has to beat (``scripts/eval_surface_scorer.py``).
"""

from __future__ import annotations

import importlib
import pkgutil
from functools import lru_cache
from types import ModuleType


class UnknownScorerError(ValueError):
    """A policy names a surface scorer no module in this package declares."""


@lru_cache(maxsize=None)
def _scorers() -> dict[str, ModuleType]:
    found: dict[str, ModuleType] = {}
    for info in pkgutil.iter_modules(__path__):
        module = importlib.import_module(f"{__name__}.{info.name}")
        scorer_id = getattr(module, "SCORER_ID", None)
        if not scorer_id:
            continue
        if scorer_id in found:
            raise UnknownScorerError(f"two modules declare surface scorer {scorer_id}")
        found[scorer_id] = module
    return found


def available_scorers() -> tuple[str, ...]:
    return tuple(sorted(_scorers()))


def get_scorer(scorer_id: str) -> ModuleType:
    try:
        return _scorers()[scorer_id]
    except KeyError:
        raise UnknownScorerError(
            f"no surface scorer {scorer_id!r}; available: {', '.join(available_scorers())}"
        ) from None
