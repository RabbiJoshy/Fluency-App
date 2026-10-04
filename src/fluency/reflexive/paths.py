"""Where the reflexive tagger finds its inputs.

Paradigm tables are generated from the Wiktionary (Kaikki) dumps by
``fluency.reflexive.paradigms`` and live in the workspace, never in git.
Per-lemma priors are small and ship in ``data/``.
"""

from __future__ import annotations

import os
from pathlib import Path

HERE = Path(__file__).resolve().parent
DATA = HERE / "data"
# <repo>/src/fluency/reflexive -> <repo>/.. is where the workspace sits.
PARADIGMS = Path(
    os.environ.get(
        "FLUENCY_REFLEXIVE_PARADIGMS",
        HERE.parents[3] / "Fluency-Workspace" / "cache" / "reflexives",
    )
)
