# UI work orders — 2026-09-20 batch

One long list from Joshua, regrouped and **ordered fastest first**. Group 1 is
an afternoon; Group 7 is a conversation. The four items at the end are not work
orders at all — they are their own chats.

**App/product jobs, not pipeline jobs** — not rows in `CHAT_ROADMAP.md`. Read
`REPO_MAP.md` before exploring; never read `flashcards.js` or `style.css` in
full.

Already shipped and deployed (`ac894d4`), not repeated below: rarer-uses list
scrolls by swipe, surface form no longer jumps vertically between senses,
sense-metadata legibility floor.

## Reading the order

| # | Group | Cost | Needs Joshua? |
|---|---|---|---|
| 1 | Small UI polish | ✅ done 2026-09-20 | — |
| 2 | Example footer layout | ✅ done 2026-09-20 | — |
| 3 | Header and underline must agree | medium | no |
| 4 | Content that is wrong or unhelpful | medium | one editorial list |
| 5 | The "jump to my level" bug | unknown — investigation | no |
| 6 | Example ordering | medium + a deck rebuild | one decision |
| 7 | Merged-lemma policy | research, back-and-forth | yes, throughout |
| — | Four handbacks | slowest | own chat each |

## Rules for every chat in this batch

1. **Check `git status` first.** Concurrent sessions are normal.
2. **One chat deploys at a time.** `gh-pages` and the two `dev_changelog.json`
   files are the contention points. Groups 2, 3, 6 and 7 all live in
   `flashcards.js` — write in parallel if you like, but do not deploy
   simultaneously.
3. **Cache busting.** If you only changed `.js`/`.css`, bump `CACHE_NAME` in
   `app/service-worker.js` — the activate handler deletes the old shell cache,
   which re-fetches every asset regardless of `?v=` tag. Use that instead of
   editing `index.html` while `index.html` is contested.
4. **Deploy at the end of the response**, per the CLAUDE.md procedure.

---

## 1. Small UI polish — ✅ DONE 2026-09-20

Files: `app/index.html`, `app/js/ui.js`, `app/css/style.css`,
`app/js/flashcards-conj.js`.

Shipped and verified on the live site. Notes for whoever does Group 2:
bumping `CACHE_NAME` alone is **not** enough to get new CSS or JS served —
it clears the service worker's cache but not the browser's HTTP cache, which
keys on the URL including `?v=`. Bump the asset's `?v=` tag in
`app/index.html`, and if the asset is a module imported by `main.js`, bump
`main.js`'s tag too, or the cached `main.js` keeps importing the old URL.

- **Top bar:** flag and language name back to sitting next to each other; every
  icon in the main-page top bar larger.
- **Conjugation settings order:** verb type, how common, persons/tenses and
  Easy mode at the top; everything else under an **Advanced settings**
  disclosure.
- **Language colour trimmings:** bring the per-language colour scheme back as
  light trimmings on the main page. `applyLanguageColorTheme()` in `ui.js`
  already exists — establish what it still does before adding anything.

**Done when:** flag and language read as one unit, top-bar icons are visibly
larger, conjugation settings open on the four that matter with the rest folded
away, and the main page carries a hint of the language's colour.

---

## 2. Example footer layout — ✅ DONE 2026-09-20

Files: `app/js/flashcards.js` (~6510–6560), `app/css/style.css`. Self-contained.

- Provenance icon (IMDb etc.) moves to the **left** of the credit text.
- Pips strip and credit text each get a hard half — pips own the left 50% or
  the right 50%, credit the other. They currently share a row and collide.
- Overflow: each side squeezes to a floor, then truncates with ellipsis.
  Neither may push the other out of the row.

Shipped. Each half is capped at 50%; the tick strip squeezes through two
density tiers measured against the width it actually got, then clips with the
current tick scrolled into view. Ticks carry `flex: 0 0 auto` — without it the
strip compressed thirty ticks into slivers, measured as fitting, and the tiers
never engaged. Verified: 30 ticks go 355px → 237px → 208px and fit a desktop
half; at 375px they still overflow and clip with the current tick visible.

---

## 3. The header and the underline must agree — medium, no open questions

Files: `app/js/flashcards.js` (~2667–2731, ~3155–3195, ~6400–6470).

Safe to do **before** the merge-policy decision in Group 7: this is a "make two
functions agree" fix and is correct under any merge policy.

Two functions independently decide which form an example is about:

- header: `example.pooledFrom || card.representativeSurface || card.targetWord`
  (`getMergedExampleContext` ~3170, `getDisplayedTargetHeadword` ~3184)
- underline: `example.surface || example.matched_surface || example.pooledFrom
  || card.representativeSurface || card.targetWord`, keeping the first that
  literally occurs in the sentence (`getExampleOccurrenceSurface` ~2685)

When `pooledFrom` is missing on a pooled example the header falls back to the
representative surface (shows **buena**) while the sentence reads **buenos** —
and no candidate matches, so nothing underlines either. Both halves of the
reported bug, one cause.

**Fix.** Resolve the occurrence surface **once** and have the header read the
resolved value, so they cannot disagree. Add a last-resort step: when no
declared candidate occurs in the sentence, find a morphological neighbour of
the card surface (shared stem after stripping the inflectional tail) and mark
it as inferred rather than declared.

**Enclitics** (`verte` against a sentence reading *ver* + clitic): strip the
enclitic tail (`me te se lo la le nos os los las les`), match the stem, and
underline stem + clitic as one span when adjacent.
`exampleOccurrenceSurfaceRegex` already handles apostrophes and whitespace and
is the right place to extend.

**Done when:** cycling examples on a merged card always shows the form the
sentence actually contains, and that form is always underlined — check
*buena/buenos* and *verte* specifically.

---

## 4. Content that is wrong or unhelpful — medium, one editorial list needed

Not code bugs; the data or the editorial choice is wrong. Grouped because each
needs a judgement about what the learner should see, and none needs much code.

- **`solía` English glosses are bad** ("he was using to"). Gloss-quality issue
  in the sense-menu projection, not in the app.
- **Portuguese cognate exclusions** do not show the English cognate in the
  excluded-words list, though other languages do. Start at
  `src/fluency/features/cognates.py` and the Fast Track exclusion-list
  rendering — likely a missing field for pt rather than a UI bug.
- **Sense metadata vocabulary** — *needs Joshua's list before coding.* Does
  `2nd pl` help a learner? Which short metadata should become an icon rather
  than a third line of tiny text? Which families are worth showing at all? The
  legibility floor is already shipped; this is about *what* is shown.

**Done when:** the two data bugs are fixed and there is an agreed list of which
metadata families ship, which become icons, and which are dropped.

---

## 5. The "jump to my level" bug — investigation, unknown depth

Standalone. Reported: clicking through to the level you are on sometimes lands
somewhere odd, then glitches and refreshes, after which the boxes fill
correctly. Suspected interaction between the next-unseen-set search and Fast
Track settings.

Start at `app/js/progress.js` and `app/js/vocab.js`
(`ensureIndexRowsForRange()`, `prefetchStudySetPayload()`). The Fast Track
session has been rewriting this area — reproduce against the landed code, not
against what is on disk mid-edit. Placed here rather than earlier because the
size is genuinely unknown until it reproduces.

**Done when:** the jump lands on the right set first time, with no refresh and
no boxes filling in late. Reproduce before fixing — do not fix by guess.

---

## 6. Example ordering: nudges, not rules — one decision, maybe a deck rebuild

File: `app/js/flashcards.js` `sortExamplesByRelevance()` (~1323–1390).

What exists now is a **lexicographic cascade** — `hasEnglish`, then
`wrongScore`, then `deckScore`, then `lenPenalty`, then `easiness`. Every
comparison is a hard gate: one point of `wrongScore` outranks any amount of
everything below it. Exactly the deterministic rule set Joshua does not want.

Replace with a single weighted sum over the same inputs, weights in one object
at the top of the function so they can be tuned without touching logic. The
three-sentence description, as requested:

> It scores every candidate on five numbers it already has — has an English
> translation, how many words the learner has met, how many they recently got
> wrong, length against a comfortable window, and easiness rank — and sorts by
> the weighted sum, so no single factor dominates.
> The easiness and length weights are multiplied by a decay that falls as the
> learner advances through the card's examples, so the first sentence is pulled
> hard toward short-and-easy and the tenth barely at all.
> Easiness is already personalised (known words discounted), so "too hard"
> quietly stops applying as the learner gets stronger, without any rule saying
> so.

**Open question — per-example WSD confidence.** It exists in the data
(`schemas/wsd-assignment.schema.json`: `confidence`, `raw_margin`,
`selected_score`, `runner_up_score`) but is **not** projected onto examples:
`src/fluency/release/app_compat.py` copies `target`, `english`, `source`,
`assignment_method`, `example_id`, `easiness`, `metadata` and no score. The app
has `meaning.confidence` only, which is per-sense and cannot stand in. Adding
it is a one-field projection change plus a deck rebuild — which is why this
group sits below the ones that ship the same day.

**Done when:** the cascade is gone, every weight lives in one editable object,
and the first sentence on a fresh card is noticeably shorter and easier than
the fifth without the order being obviously rigged.

---

## 7. Merged-lemma policy — research, back-and-forth, slowest in this file

Files: `app/js/flashcards.js`, `app/js/card-metadata-pills.js`. Read
`docs/INVARIANTS.md` first. Everything here follows from one thing: **identity
is the surface form, and the lemma merge is a view over it.** Do Group 3 first;
this group assumes the header and underline already agree.

### 7a. The merge policy (decide before writing code)

Reported on *unidos*: merging lemmas for one surface pulls together too much.
What is allowed to merge — same POS? same authority lemma? same sense-menu
headword? Propose options to Joshua with examples from real cards before
changing behaviour.

### 7b. Frequency: per lemma or per surface?

The app already sums — `showFreqInfo` reads `data-frequency-forms` and says
"total across N source-listed forms", so today it is per merged group. Once 7a
settles, decide whether the card shows the surface's own frequency with the
group total as secondary, or keeps the sum.

**Why do interjections have a frequency?** *Not verified — measure, do not
assert.* Frequency lists are surface-keyed and POS-blind, so the likely answer
is that the surface genuinely appears in the list. Check against the inventory
artifact before writing any UI copy about it.

### 7c. "with infinitive" as a visual link

When a sense is marked *with infinitive*, colour the marker and mark the
infinitive in the example the same way. Same mechanism as the existing
SpanishDict usage-context highlight (`highlightPossibleSpanishDictUsage`
~2997), which already carries the honest "possible realization, not proven
evidence" caveat — extend that function rather than adding a second path. It
shares the highlight code Group 3 rewrites, so it must come after it.

**Done when:** there is a written merge rule in `docs/decisions/`, *unidos*
behaves under it, and the frequency shown on a merged card is unambiguous
about what it counts.

---

## Handed back to Joshua — own chat each, slowest of all

Long, need real back-and-forth, not coupled to anything above. Deliberately
**not** work orders. Roughly in increasing order of how much conversation they
need.

1. **Modals using the left and right sides.** Desktop slides some in-set modals
   in from the sides; Joshua wants that far more widely — synonyms, and
   pop-ups on the main page too. Needs an enumerated modal inventory
   (`app/js/flashcards-modals.js` + `.modal` ids in `index.html`) and an agreed
   split before converting anything.
2. **Walkthrough / tutorial / about.** Three separate things, currently
   confused. Tutorial = users, desktop and mobile both first-class. About =
   employers, desktop-first but comfortable on mobile, *links to* the
   walkthrough, contains no tutorial. Walkthrough = shallow "here is what a
   card looks like" demo. The walkthrough existed and appears to have been
   replaced by the tutorial. Any chat must first establish what
   `about-example.js` renders today and which of the three it is.
3. **URLs and routing.** The app has no real routing. Proposal sent
   2026-09-20: two addressable things — a deck position (`/#/es/set/47`) and a
   word by surface key (`/#/es/w/unidos`), plus `/#/es/artist/bad-bunny` and
   URLs for about/tutorial/walkthrough. Blocked on one decision: should a
   shared link address a deck position or a word? Given
   `card_id = f(language, surface_key)`, the word is the durable link and the
   set is a convenience — but everything else follows from that answer.
4. **Function words you cannot teach atomically.** Spanish `lo` WSD is almost
   always wrong; `de`/`del` (and the a/an-shaped pairs) probably want to be
   taught together with a rule. Two parts: a warning on hard-to-translate
   function words, and a concept of a paired card that the surface-keyed
   identity does not currently have. Read `docs/INVARIANTS.md` before
   proposing anything. High stakes — these are the first words a beginner
   meets.
