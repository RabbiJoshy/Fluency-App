"""Read a SUBTLEX-NL export as surface counts, repairing its tokenizer at the edge.

SUBTLEX-NL is a better Dutch list than the FrequencyWords one because it kept
apostrophe words whole: ``'t``, ``'n``, ``z'n``, ``m'n`` and ``auto's`` are rows
of their own, where FrequencyWords counted ``z'n`` as ``z`` plus ``n``. Its own
tokenizer has three habits that would distort a surface ranking, so this
adapter undoes them here rather than letting them reach the inventory:

* Multi-word units are joined with ``_`` (``aan_het``, ``in_orde``,
  ``'s_nachts``) and their occurrences are *not* counted in the component
  words. Left alone, ``orde`` reads at a sixth of its FrequencyWords share.
  Each unit is split and its count added to every component.
* A sentence-final full stop sometimes stays on the token (``ben.``,
  ``niet.``). One trailing stop is removed and the count joins the bare word.
* Apostrophes arrive as an acute accent or a Windows-1252 byte decoded as a
  C1 control (``´t``, ``m\\x92n``). Those fold to the ASCII apostrophe.

Only ``Word`` and ``FREQcount`` are read. The other columns -- film counts,
CGN part of speech and lemma -- stay in the snapshot, unused, because lemma is
never card identity.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re

from fluency.languages.surfaces import normalizer_for_language


FREQUENCY_UNIT = "occurrences"

ADAPTER_ID = "subtlex-surface-frequency/v1"

_REQUIRED_COLUMNS = ("Word", "FREQcount")

# The published-list shape, plus a word that *starts* with an apostrophe:
# Dutch 't, 'n, 's, 'm, 'k are whole words, not fragments.
_SURFACE_PATTERN = re.compile(
    r"^(?:'[^\W\d_]+|[^\W\d_]+(?:['-][^\W\d_]+)*)$", re.UNICODE
)

# Apostrophe stand-ins seen in the export: acute accent, grave accent, and the
# Windows-1252 right quote (0x92) and dashes (0x96, 0x97) decoded as C1 controls.
_APOSTROPHE_REPAIRS = str.maketrans({"´": "'", "`": "'", "\u0092": "'"})
_LEADING_DASH_ARTIFACTS = "\u0096\u0097"


class SubtlexInventoryError(ValueError):
    """Raised when a SUBTLEX export cannot satisfy the pinned contract."""


@dataclass(frozen=True, slots=True)
class SubtlexReadResult:
    frequencies: dict[str, float]
    source_rows: int
    rejected_malformed: int
    rejected_empty_or_zero: int
    rejected_surface_shape: int
    duplicate_rows: int
    split_multiword_rows: int
    trailing_stop_rows: int
    apostrophe_repaired_rows: int


def read_subtlex(path: Path, *, language: str) -> SubtlexReadResult:
    """Return one summed count per normalized surface from a SUBTLEX TSV export."""

    normalize_surface = normalizer_for_language(language)
    frequencies: dict[str, float] = {}
    counters = dict.fromkeys(
        (
            "source_rows",
            "rejected_malformed",
            "rejected_empty_or_zero",
            "rejected_surface_shape",
            "duplicate_rows",
            "split_multiword_rows",
            "trailing_stop_rows",
            "apostrophe_repaired_rows",
        ),
        0,
    )

    def add(raw_surface: str, count: float) -> bool:
        if raw_surface.endswith(".") and len(raw_surface) > 1:
            stripped = raw_surface[:-1]
            if _SURFACE_PATTERN.fullmatch(stripped.lower()):
                raw_surface = stripped
                counters["trailing_stop_rows"] += 1
        try:
            surface = normalize_surface(raw_surface)
        except ValueError:
            return False
        if _SURFACE_PATTERN.fullmatch(surface) is None:
            return False
        if surface in frequencies:
            counters["duplicate_rows"] += 1
            frequencies[surface] += count
        else:
            frequencies[surface] = count
        return True

    try:
        stream = path.open(encoding="utf-8-sig")
    except FileNotFoundError as error:
        raise SubtlexInventoryError(f"SUBTLEX snapshot does not exist: {path}") from error

    with stream:
        header = stream.readline().rstrip("\n").split("\t")
        missing = [column for column in _REQUIRED_COLUMNS if column not in header]
        if missing:
            raise SubtlexInventoryError(
                f"snapshot is not the expected SUBTLEX export; missing: {missing}"
            )
        word_index = header.index("Word")
        count_index = header.index("FREQcount")
        for line in stream:
            line = line.rstrip("\n")
            if not line:
                continue
            counters["source_rows"] += 1
            cells = line.split("\t")
            if len(cells) != len(header):
                counters["rejected_malformed"] += 1
                continue
            try:
                count = float(cells[count_index])
            except ValueError:
                counters["rejected_malformed"] += 1
                continue
            raw = cells[word_index].strip()
            if not raw or count <= 0:
                counters["rejected_empty_or_zero"] += 1
                continue
            repaired = raw.translate(_APOSTROPHE_REPAIRS).lstrip(_LEADING_DASH_ARTIFACTS)
            if repaired != raw:
                counters["apostrophe_repaired_rows"] += 1
            if "_" in repaired:
                counters["split_multiword_rows"] += 1
                parts = [part for part in repaired.split("_") if part]
                accepted = [add(part, count) for part in parts]
                if not any(accepted):
                    counters["rejected_surface_shape"] += 1
                continue
            if not add(repaired, count):
                counters["rejected_surface_shape"] += 1

    if not frequencies:
        raise SubtlexInventoryError("SUBTLEX snapshot yielded no usable surfaces")
    return SubtlexReadResult(frequencies=frequencies, **counters)
