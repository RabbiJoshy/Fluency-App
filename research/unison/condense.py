"""Shorter reading copies of the UNISON card views and blind sheets.

Used for Portuguese t02 onwards, to cut reading cost (Josh, 2026-10-08):

  view   each shown meaning keeps its first 2 examples (what the learner sees
         first) plus the 2 with the lowest WSD margin; the rest are counted.
  blind  menu glosses and ⟨context⟩ notes are clipped; nothing is removed,
         so every menu id is still there to label against.

Reads and writes ``<workspace>/reviews/unison/<release_id>/`` only:
``view-<chunk>.short.txt`` and ``blind-<chunk>.short.txt``.

  python research/unison/condense.py --language pt --chunk t02
"""

from __future__ import annotations

import argparse
import re
from pathlib import Path

from research.unison.cards import DEFAULT_WORKSPACE, RELEASES

KEEP_FIRST = 2
KEEP_LOW_MARGIN = 2
EXAMPLE = re.compile(r"^ {8}\d+\. ")
MARGIN = re.compile(r"\[[A-Z?]✓? (\d+\.\d+)")
MENU = re.compile(r"^(    m\d+ )(.*)$")


def clip(text: str, limit: int) -> str:
    return text if len(text) <= limit else text[: limit - 1] + "…"


def condense_view(lines: list[str]) -> list[str]:
    out: list[str] = []
    block: list[str] = []

    def flush() -> None:
        if not block:
            return
        def margin(line: str) -> float:
            m = MARGIN.search(line)
            return float(m.group(1)) if m else 9.0
        keep = set(range(min(KEEP_FIRST, len(block))))
        rest = sorted(range(KEEP_FIRST, len(block)), key=lambda i: margin(block[i]))
        keep.update(rest[:KEEP_LOW_MARGIN])
        out.extend(block[i] for i in sorted(keep))
        if len(block) > len(keep):
            out.append(f"        (+{len(block) - len(keep)} more)")
        block.clear()

    for line in lines:
        if EXAMPLE.match(line):
            block.append(line)
            continue
        flush()
        out.append(line)
    flush()
    return out


def condense_blind(lines: list[str]) -> list[str]:
    out = []
    for line in lines:
        m = MENU.match(line)
        if not m:
            out.append(line)
            continue
        body = m.group(2)
        gloss, _, context = body.partition("  ⟨")
        line = m.group(1) + clip(gloss, 110)
        if context:
            line += "  ⟨" + clip(context.rstrip("⟩"), 70) + "⟩"
        out.append(line)
    return out


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--language", required=True, choices=sorted(RELEASES))
    parser.add_argument("--chunk", required=True)
    parser.add_argument("--workspace", type=Path, default=DEFAULT_WORKSPACE)
    args = parser.parse_args()
    base = args.workspace / "reviews" / "unison" / RELEASES[args.language]
    for kind, fn in (("view", condense_view), ("blind", condense_blind)):
        src = base / f"{kind}-{args.chunk}.txt"
        dst = base / f"{kind}-{args.chunk}.short.txt"
        lines = src.read_text().splitlines()
        short = fn(lines)
        dst.write_text("\n".join(short) + "\n")
        print(f"{dst.name}: {len(lines)} -> {len(short)} lines, "
              f"{len(src.read_text())} -> {len(dst.read_text())} chars")


if __name__ == "__main__":
    main()
