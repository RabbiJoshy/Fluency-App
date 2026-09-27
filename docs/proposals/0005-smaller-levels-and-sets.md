# Proposal 0005: 100-word levels, 25-card sets, estimates as levels

## Status

Agreed in conversation with Josh on 2026-09-27. Not started. No users besides
Josh, so no learner data needs preserving beyond his own progress, which is
keyed per card and is untouched by any of this.

**Implemented 2026-09-27.** Step 3 was settled differently from both options
below: Josh chose to have the app build Speech levels itself, like Lyrics
(`loadReleaseStudyStructure()` no longer applies release levels), because
frequency-cliff boundaries are deprecated and levels are now plain 100-card
bands. Nothing was republished; releases keep their `study-structure.json` as
published, and the app ignores its levels. This reverses decision 0009's
"release-owned levels" for the app. The builder defaults in
`study_structure.py` moved to 100 / 120 / 25 for any future release.

## Why

A level is ~200 words split into ten 20-card sets: ten squares to choose from,
and a level is passed only every ten sessions. Smaller levels make each one a
landmark reached every few sessions; four sets per level makes the choice
trivial. A set is meant to take 5–10 minutes (the set help sheet now says so).

## Decisions

| | Now | New |
|---|---|---|
| Words per level | 200 (target) | 100 (target) |
| Level cap | 80 | 120, so ~10k-card decks keep ~100-word levels |
| Cards per set | 20 | 25 → 4 sets per level |
| "Mark level as done" | Read-only leftover; skips levels at startup | Deleted |
| Level estimate | Shown as a word range; lands on the containing level | Shown as "Start at Level N"; still stored as a rank |

The estimate stays stored as a rank on purpose: a rank survives any future
change to level boundaries, and the level is derived from it on display. With
100-word levels the level is granular enough to show on its own.

Boundaries still snap to frequency cliffs within ±25%, so a level may be 87 or
112 words and its last set short. That is existing, harmless behaviour.

## Where each number lives

Levels have three builders; sets have one.

- **Speech levels** — release-owned. `src/fluency/release/study_structure.py`
  (`target_cards_per_level=200`, `maximum_levels=80`, `set_size=20`), called
  from `release/run_candidate.py`, written to each release's
  `app/study-structure.json`, loaded by `app/js/config.js`
  `loadReleaseStudyStructure()`.
- **Artist / lyrics levels** — app-side. `computeSmartLevelRanges()` in
  `app/js/ui.js` (`targetCardsPerLevel = 200`, `maximumLevelCount = 80`);
  `loadReleaseStudyStructure()` returns null in artist mode.
- **Playlist-live levels** — app-side, `ui.js` (`targetPerLevel = 200`).
- **Sets** — app-side for every mode: `STABLE_SET_SLOT_COUNT = 20` in `ui.js`
  slots each level's rank range. The release's own `sets` list is not what the
  setup screen renders, so the set size is an app-only change. Keep
  `study_structure.py`'s `set_size` in step for consistency.

Put the two numbers in one place in the app (a shared constant) rather than
editing three literals.

## Steps

1. **App constants.** 100-word levels and a 120 cap in `computeSmartLevelRanges`
   and the playlist-live builder; `STABLE_SET_SLOT_COUNT = 25`. Artist and
   playlist decks change on deploy.
2. **Delete mark-as-done.** `saveMarkedLevelDone`, `isLevelMarkedDone`,
   `markedDoneLevels` and their reads in `auth.js`, `ui.js`, `estimation.js`,
   `vocab.js`, `state.js`. The `doneLevels` meta written to the Progress
   sheet can be left in the sheet; the app simply stops reading it.
3. **Speech study structure.** Change the builder defaults to 100 / 120 / 25,
   then republish `study-structure.json` for the active speech releases
   (es, pt, cs 10k MEND; fi, nl, fr, pl as configured). Releases are
   immutable, so decide first between (a) a new release id per language via
   the normal build + `scripts/publish_release.py`, or (b) a sanctioned
   study-structure-only revision. Check `CHAT_ROADMAP.md` before publishing:
   no chat owns this today, and release publishing is plant work.
4. **Estimate as a level.** `estimation.js` result screen shows
   "Start at Level N" (derived from the rank against the active levels); the
   landing logic already opens the containing level.
5. **Copy that assumes 20.** The tutorial replica's "Learn 20 new cards" and
   set meta, the set help sheet, and anything that says "ten sets".
6. **Check.** The level picker with 40–120 levels; four set squares on a
   phone; resume ("Continue where you stopped") and completion routing into
   the next set and next level; the loading ring.

## Not changing

Card identity, progress records, Smart Skip, the review queue.
