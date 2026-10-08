# UNISON progress

Kept by the UNISON chats; see `BRIEF.md` for the rules. Newest first within
each section.

## Status

Part 1 (audit): not started.
Part 2 (one engine): waiting on part 1.
Part 3 (metadata): waiting on part 1.

## Decisions (approved by Josh)

- 2026-10-08: UNISON covers modes (speech, lyrics, TURBO) and providers
  (SpanishDict, Wiktionary), plus a metadata pass and a 300-card audit of es
  and pt. Audit first. UI changes wait until UNISON is done.

## Fix list

Set by Josh after part 1.

## Done before UNISON (2026-10-08)

- Wiktionary companion notes keep every alternative (`[with de or sobre]`),
  treat form alternatives as no requirement, and read a lone "a" as the
  preposition (`features/wiktionary.py`, 3bcf94ce). Not in any release until
  menus are rebuilt.
- Live display changes: 10% floor per subsense row; SpanishDict senses sharing a
  context group into one row; topic chips only when they distinguish rows.

## Found, not on the list

(Count and one example each.)
