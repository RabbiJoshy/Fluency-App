"""Where the surface ledger lives, and what it is called.

The ledger is the per-language table that says a language is ready: one row per
surface, every column provenanced, the verdict a fold over recorded events
rather than a value anyone set. It is the contract the WSD stage, the cognate
work and any future language all read.

It was called ``surfaces.json`` / ``surface-view/v2`` while it was a byproduct.
The fallback below exists so a workspace written before the rename still reads;
it is not a second format.
"""

from __future__ import annotations

from pathlib import Path

LEDGER_VERSION = "surface-ledger/v1"

#: Read in order; the first that exists wins. New writes always use the first.
LEDGER_NAMES = ("ledger.json", "surfaces.json")


def ledger_dir(workspace: Path, language: str) -> Path:
    return Path(workspace) / "raw" / "surfaces" / language


def ledger_path(workspace: Path, language: str) -> Path:
    """The ledger to read for ``language``, preferring the current name."""

    directory = ledger_dir(workspace, language)
    for name in LEDGER_NAMES:
        candidate = directory / name
        if candidate.is_file():
            return candidate
    return directory / LEDGER_NAMES[0]


def ledger_write_path(workspace: Path, language: str) -> Path:
    """Where a fresh ledger is written. Always the current name."""

    return ledger_dir(workspace, language) / LEDGER_NAMES[0]
