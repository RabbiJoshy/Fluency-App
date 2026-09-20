# UI work orders — 2026-09-20 batch

Source: one long list from Joshua, 2026-09-20. **These are app/product jobs, not
pipeline jobs.** They are not rows in `CHAT_ROADMAP.md`. Read `REPO_MAP.md`
before exploring; never read `flashcards.js` or `style.css` in full.

Each group below is one chat's worth of work. Groups are ordered so that the
ones with no open questions come first. A group marked **BLOCKED** needs an
answer from Joshua before a chat opens it.

## Rules for every chat in this batch

1. **Check `git status` first.** Concurrent sessions are normal. As of writing,
   another session holds uncommitted work in `app/index.html`, `app/js/ui.js`,
   `app/js/auth.js`, `app/js/vocabulary-import.js` and a new
   `app/js/fast-track-preferences.js` (a Fast Track / Settings restructure).
   **Do not commit those files** unless your group owns them and that session
   has landed. If your change needs one of them, either wait or edit and hand
   the commit to whoever owns the file.
2. **Cache busting.** Bumping a `?v=` tag means editing `app/index.html`, which
   is currently contested. If you only changed `.js`/`.css`, bump
   `CACHE_NAME` in `app/service-worker.js` instead — the activate handler
   deletes the old shell cache, which re-fetches every asset regardless of tag.
3. **Deploy at the end of the response** (CLAUDE.md procedure: changelog in
   both `app/config/dev_changelog.json` and `config/dev_changelog.json`, commit
   on `main`, mirror into `/private/tmp/fluency-pages-deploy/` at both the root
   path and the `app/` path, push `gh-pages`).
4. **Only one chat should be deploying at a time.** `gh-pages` and the two
   changelog files are the contention points.

---

## Group 1 — Card surface hygiene  ✅ DONE 2026-09-20

Shipped in `898a2c9..` (see changelog 2026-09-20 19:20).

- Rarer-uses list scrolls by swipe. `.card` sets `touch-action: none` for
  swipe grading; `.phrase-summary-scroll` inherited it, so the browser's own
  scrolling was disabled and the scrollbar was the only handle. Now
  `touch-action: pan-y` + `overscroll-behavior: contain`, scrollbar hidden.
  **Any other in-card scroller has the same latent bug** — the pattern to copy
  is at `app/css/style.css` `.phrase-summary-scroll`.
- Surface form no longer moves vertically between senses. `#frontLemma`
  toggled `display`; it now keeps a reserved invisible slot whenever any sense
  on the card names a differing citation form
  (`cardLemmaSlotIsLoadBearing()` in `app/js/flashcards.js`).
- Sense metadata legibility floor: pills no longer go below 10px, grammar tier
  lifted off `--text-muted`.

---

## Group 2 — Example sentence: the right word, underlined

Files: `app/js/flashcards.js` only (~2667–2731, ~3155–3195, ~6400–6470).
No open questions. Biggest correctness win in the batch.

**The defect.** Two functions independently decide "which form is this
example about":

- the header uses `example.pooledFrom || card.representativeSurface ||
  card.targetWord` (`getMergedExampleContext`, ~3170) and
  `getDisplayedTargetHeadword` (~3184);
- the underline uses `example.surface || example.matched_surface ||
  example.pooledFrom || card.representativeSurface || card.targetWord`,
  keeping the first that literally occurs in the sentence
  (`getExampleOccurrenceSurface`, ~2685).

When `pooledFrom` is missing on a pooled example, the header falls back to the
representative surface (shows **buena**) while the sentence contains
**buenos** — and because no candidate matches, nothing gets underlined either.
That is the reported bug, from one cause.

**Fix.**
1. Resolve the occurrence surface **once**, and have the header read the
   resolved value. They must not be able to disagree.
2. Add a last-resort resolution step: when no declared candidate occurs in the
   sentence, scan the sentence for a morphological neighbour of the card
   surface (shared stem after stripping the inflectional tail) and use that.
   Mark it as inferred, so it can be told apart from a declared surface.
3. Enclitics (`verte` vs a sentence reading *ver* + clitic): strip the
   enclitic tail (`me te se lo la le nos os los las les`) from the card
   surface, match the stem, and underline stem and clitic as one span when
   adjacent. `exampleOccurrenceSurfaceRegex` already handles apostrophes and
   whitespace and is the right place to extend.

---

## Group 3 — Example sentence: chrome layout

Files: `app/js/flashcards.js` (~6510–6560, example footer), `app/css/style.css`.
No open questions.

- Provenance icon (IMDb etc.) moves to the **left** of the credit text.
- Pips strip and the provenance/credit text each get a hard half: pips own the
  left 50% or the right 50%, credit the other. They currently share a row and
  collide.
- Overflow: allow each side to squeeze to a floor, then truncate with
  ellipsis. Do not let either push the other out of the row.

---

## Group 4 — Example ordering: nudges, not rules  **partly BLOCKED**

File: `app/js/flashcards.js` `sortExamplesByRelevance()` (~1323–1390).

**What is there now.** A lexicographic cascade — `hasEnglish`, then
`wrongScore`, then `deckScore`, then `lenPenalty`, then `easiness`. Every
comparison is a hard gate: a single point of `wrongScore` outranks any amount
of everything below. This is exactly the deterministic rule set Joshua does not
want.

**What to build.** Replace the cascade with one weighted sum, keeping the same
inputs. Per-example fields already shipped in the release: `easiness`,
`english`, `spotify_available`, `is_variant`, plus the derived deck-overlap and
recent-mistake counts and `contentTokenCount`. Weights live in one object at
the top of the function so they can be tuned without touching logic.

**The three sentences (as requested):**

> It scores every candidate sentence on five numbers it already has — whether
> it has an English translation, how many words in it the learner has already
> met, how many it recently got wrong, its length against a comfortable window,
> and its easiness rank — and sorts by the weighted sum rather than by a
> priority order, so no single factor can dominate.
> The easiness and length weights are multiplied by a decay term that falls as
> the learner advances through the card's examples, so the first sentence is
> pulled hard toward short-and-easy and the tenth is barely pulled at all.
> Easiness is already personalised (known words are discounted), so the same
> decay also happens naturally as the learner gets stronger — a sentence stops
> counting as "hard" once its words are known, without any rule saying so.

**BLOCKED on Joshua:** whether to add per-example WSD confidence. It exists in
the data (`schemas/wsd-assignment.schema.json` has `confidence`, `raw_margin`,
`selected_score`, `runner_up_score`) but is **not** projected onto examples in
the release — `src/fluency/release/app_compat.py` copies `target`, `english`,
`source`, `assignment_method`, `example_id`, `easiness`, `metadata` and no
score. Adding it is a one-field projection change plus a deck rebuild. The app
has `meaning.confidence` only, which is per-sense, not per-example, so it
cannot stand in.

---

## Group 5 — Walkthrough / Tutorial / About: three things, not one  **BLOCKED**

Files: `app/js/about-example.js`, `app/index.html`, `app/css/style.css`.

Joshua's requirement, restated:

| Thing | Audience | Contains | Platform |
|---|---|---|---|
| **Tutorial** | people actually using the app | how to study, settings, modes | desktop + mobile, both first-class |
| **About** | employers / people being shown the app | what this is, how it was built; **links to** the walkthrough; does **not** contain the tutorial | desktop-first, must be comfortable on mobile |
| **Walkthrough** | someone being shown the app, not using it | a surface-level "here is what a card looks like" demo | either |

The walkthrough existed and appears to have been replaced by the tutorial at
some point. **BLOCKED:** a chat must first establish what `about-example.js`
currently renders and which of the three it actually is, and report back before
restructuring. Do not guess.

---

## Group 6 — Modals should use the sides  **BLOCKED on scope**

Desktop currently slides some in-set modals in from the left/right. Joshua
wants that treatment applied much more widely — synonyms, and pop-ups on the
main page too, not just inside an active set.

**BLOCKED:** needs a list of which surfaces become side panels. A chat should
enumerate the current modal inventory (`app/js/flashcards-modals.js` +
`.modal` ids in `app/index.html`) and propose the split, rather than convert
things speculatively.

---

## Group 7 — Top bar  **contested files**

- Flag and language name go back to sitting next to each other.
- Every icon in the main-page top bar gets larger.

Markup is in `app/index.html`, behaviour in `app/js/ui.js` — **both currently
held by the Fast Track session.** Hold this group until those land.

---

## Group 8 — Conjugation mode settings order

File: wherever conjugation settings render (start from `app/js/ui.js`
`renderStudySettings()` and `app/js/flashcards-conj.js`).
No open questions.

Top: verb type, how common, persons/tenses, Easy mode. Everything else under an
**Advanced settings** disclosure. Note `ui.js` is contested — coordinate.

---

## Group 9 — Frequency semantics  **BLOCKED (one question is a measurement)**

Two things:

1. **Per lemma or per surface in merged-lemma mode?** The app already sums:
   `showFreqInfo` reads `data-frequency-forms` and says "total across N
   source-listed forms". So today it is per merged group. Joshua needs to
   decide whether that is right or whether the card should show the surface's
   own frequency with the group total as secondary.
2. **Why do interjections have a frequency?** *Not yet verified — measure, do
   not assert.* Frequency lists are surface-keyed and POS-blind, so the likely
   answer is that the interjection surface genuinely appears in the list. The
   distribution is one command away against the inventory artifact; check
   before writing any UI copy about it.

---

## Group 10 — Merged-lemma merge policy  **BLOCKED, design work**

Reported on *unidos*: merging lemmas for a surface form pulls together too
much. This falls out of keying on surface form and then merging lemmas, and
needs a policy decision (what may merge: same POS? same authority lemma? same
sense-menu headword?) before any code. Related to Group 2 and Group 9 — the
same merge decides which surface the header shows and which frequency is
summed. **Do not open this in parallel with Group 2.**

---

## Group 11 — Sense metadata vocabulary  **BLOCKED, editorial**

The legibility floor is shipped (Group 1). Open questions are editorial:
does `2nd pl` help a learner; which short metadata could become an icon rather
than a third line of tiny text; which families are worth showing at all.
Needs Joshua's judgement on the list, per family.

---

## Group 12 — "with infinitive" as a visual link

Joshua's idea: when a sense is marked *with infinitive*, give that marker a
colour and mark the infinitive in the example sentence the same way. It is a
good idea and it generalises — it is the same mechanism as the existing
SpanishDict usage-context highlight
(`highlightPossibleSpanishDictUsage`, `app/js/flashcards.js` ~2997), which
already carries the "possible realization, not proven evidence" caveat.
Build it as an extension of that function, keeping the same epistemic honesty.
Depends on Group 2 landing first (shared highlight path).

---

## Group 13 — Data/content jobs (not UI)

These need pipeline or content work, not app work. Listed here so they are not
lost; each needs its own decision before it becomes a job.

- **Spanish `lo` WSD is almost always wrong.** Proposal: a small per-language
  list of "hard to translate" function words that carry a warning on the card.
  These are exactly the words a beginner meets first, so the cost is high.
- **`de` / `del` taught together**, with a rule explaining the difference;
  likewise the a/an-shaped pairs. Needs a concept of a paired card, which the
  surface-keyed identity does not currently have — read
  `docs/INVARIANTS.md` before proposing anything.
- **`solía` English glosses are bad** ("he was using to"). Gloss-quality issue
  in the sense menu projection, not the app.
- **Portuguese cognate exclusions** do not show the English cognate in the
  excluded-words list, though other languages do. Start at
  `src/fluency/features/cognates.py` and the Fast Track exclusion list
  rendering. Likely a missing field for pt rather than a UI bug.

---

## Group 14 — URLs and routing  **BLOCKED, needs a decision**

The app has no real routing. See the proposal sent to Joshua 2026-09-20; it
needs his answer on whether deep links address a *deck position* or a *word*
before anything is built.

---

## Group 15 — Language colour scheme on the main page

Joshua wants the per-language colour theming back as light trimmings on the
main page. `applyLanguageColorTheme()` in `app/js/ui.js` already exists —
establish what it still does before adding anything. Contested file; hold.

---

## Group 16 — "Next set" / level jump bug

Reported: clicking through to the level you are on sometimes lands somewhere
odd, then glitches and refreshes, after which the boxes fill correctly.
Suspicion: the next-unseen-set search interacts badly with Fast Track
settings. **The Fast Track session is actively rewriting exactly this area** —
do not open this group until it lands, then reproduce against the new code.
