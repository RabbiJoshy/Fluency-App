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
