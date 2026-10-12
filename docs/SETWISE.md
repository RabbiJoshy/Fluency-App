# SETWISE — level progress and short sessions

Approved in the SETWISE chat, 2026-10-11: retain the 100-card target level size,
replace selectable fixed sets with a single continuous bar, and start sessions of
up to 20 eligible cards immediately. No session-size picker. Existing small-deck
and oversized-deck level exceptions remain supported.

## Behaviour

- The visible bar aggregates the whole level by status: each colour appears once,
  with no four-way divisions or rank patches. Internal 25-position regions remain
  for estimation and old-session compatibility. Filters never move level boundaries.
- Show work remaining first: New → Practice → Known → Estimated familiar → Skipped.
  The legend follows the same order. Use the Portuguese level accent green for known,
  vivid yellow for practice, white for new, violet for estimated familiarity and
  slate for skipped. Legend text uses primary ink; both themes share the palette.
- Go selects new cards in existing vocabulary order within the selected level.
  When no new cards remain, offer practice, then clearly labelled Study again.
- Cap constructed cards at 20; keep companion pairs together, allowing 19 cards
  when a pair would cross the batch boundary. A shorter final batch is valid.
- Completion recounts progress and offers Another 20 (or the smaller tail), then
  the next level. New sessions do not automatically continue.
- Keep known, practice, new, skipped, and estimated-familiar states distinct.
  Level completion means no eligible new cards remain, not durable mastery.
- Estimation retains its within-level recognition regions and saved source-rank
  cutoff. Describe placement approximately (beginning, quarter, halfway, end).
  Opening a recommendation selects its containing level, without starting it.
- Exact resumes retain IDs, order and position. New snapshots also record that
  their range represents a whole-level session; old snapshots remain readable.
- Guest answers advance sessions in tab memory only, scoped to source/language;
  they do not write cloud progress or new persistent learning records.

## Changes and validation

Selection, loading, progress history, completion, resume, help and tutorial exit
now use sessions rather than selected set numbers/ranges. Card rank metadata and
card identities remain intact. Worker sync schemas and SRS stage rules are unchanged.

Validation: app unittest suite, behavioural checks for batches crossing old set
boundaries, short tails, companion pairs, estimated/skipped progress, guest scope,
and same-level continuation. Estimation checks preserve rank placement and await
level rendering without selecting a removed set button. Resume checks cover new
snapshot metadata and the updated welcome screen. Browser review and staging
receipt are recorded after publication below.

Browser verification (local full app, real Spanish release): 390px landing and
320px return-to-menu view, with no page-width overflow; a 20-card session with
20 history entries; exact resume at card index 5 with all 20 IDs unchanged;
completion followed by Another 20 beginning at source rank 21. Guest test only:
no real learner account or cloud answers were changed. Physical-device feel and
two-device sync remain unverified.

## SETWISE-2 — Learn New vs Practise, chosen by time (2026-10-12)

Agreed with Josh 2026-10-12, built the same night for staging review.

- **Session length, not card count.** Go and Practise share one remembered length:
  5 min, 10 min or No limit (`app/js/session-plan.js`, `localStorage`
  `fluencySessionLengthV1`, default 5 min). Time becomes a card count at a fixed
  assumed pace — 15 s per new card, 10 s per practice card — so 5 min is 20 new or
  30 practice cards. No learner's speed is measured or stored (Josh's call).
- **Go has four level states** (`levelState` on `__studySessionContext`):
  `new` starts at once; `choice` (Practise words outnumber new words left, and at
  least `LEVEL_CHOICE_MIN_PRACTICE` = 10, a guess to check) asks "practise these
  or learn the new", once per level until reload; `met` (no new words, some in
  Practise) offers practise, next level, or a quiet "Redo anyway"; `done` (no new,
  nothing waiting) offers next level or redo, and says when the first words come
  back. Practise here means the level's own cards (`studyMode: 'review'`).
- **Redo** is only reachable from those screens, as a text link. Most learners will
  never see them: Learn New moves forward and never lands on a finished level.
- **Practise** (was Practice Errors) is the language-wide queue. It shows
  "14 waiting · 12 more tomorrow", or when empty "Nothing to practise. 12 words come
  back tomorrow, 30 more this week." Return times are rough (`in 3 hours`,
  `tomorrow`, `on Thursday`) because a due time is only last-correct plus N days.
  With the schedule paused it says only mistakes come back.
- **Completion**: "Keep going · 5 min" (or "· last N") replaces "Another 20";
  finishing a level reports how many words wait in Practise. Guests are not told
  words come back, since their answers are not saved.
- **Badge**: word range only ("Words 1–100" with a small label); "of N levels"
  replaces it while scrubbing and for a second after; the deck size moved to the
  Choose a Level help.

Not changed: Smart Skip decks still build 20 cards; Smart Skipped and estimated
cards never enter Practise; SRS rules, sync and card identities are untouched.

Validation: app unittest suite (270) including session-plan unit checks and the
four level states in `tests/app/study_session_checks.cjs`. Local browser (guest,
real Spanish release, simulated progress — nothing written): all three screens,
10 min → 40-card session, completion label, Practise with and without a queue,
375 px width with no overflow.
