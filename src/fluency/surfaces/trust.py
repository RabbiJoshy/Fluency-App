"""How a fact about a surface was established, and who may use it.

Four levels, strongest first. A consumer declares the weakest it accepts, and
the resolver hands it nothing below that.

- ``curated``: a person read it -- a hand-written override, gloss or entity, or
  an ``adjudicated_*`` event.
- ``provider``: the provider stated it -- SpanishDict's page for the exact
  surface, its conjugation table, a Wiktionary ``form_of``.
- ``derived``: a deterministic rule of ours reached it from provider data,
  checked its own answer and abstains on ambiguity -- the enclitic host rule.
- ``heuristic``: a cheap guess with nothing verifying it. Live playlists only,
  shown as provisional (proposal 0003 §4).

``provider`` sits apart from ``derived`` because they fail differently: a
provider statement is wrong only when the provider is, and is corrected by an
override; a derived answer is wrong when our rule is, and is corrected by
fixing the rule.
"""

from __future__ import annotations

CURATED, PROVIDER, DERIVED, HEURISTIC = "curated", "provider", "derived", "heuristic"
LEVELS = (CURATED, PROVIDER, DERIVED, HEURISTIC)
_RANK = {level: index for index, level in enumerate(LEVELS)}


def check(level: str) -> str:
    if level not in _RANK:
        raise ValueError(f"unknown trust level: {level!r} (expected one of {', '.join(LEVELS)})")
    return level


def accepts(minimum: str, level: str) -> bool:
    """Whether a consumer whose floor is ``minimum`` may use a ``level`` fact."""
    return _RANK[check(level)] <= _RANK[check(minimum)]
