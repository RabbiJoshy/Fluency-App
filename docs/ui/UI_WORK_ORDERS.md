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

Ordered by how much back-and-forth each one needs, not by subject. Nothing here
is handed off — the ones at the bottom simply need a conversation before they
need code, so they come last.

| # | Group | Cost | Needs Joshua? |
|---|---|---|---|
| 1 | Small UI polish | ✅ done 2026-09-20 | — |
| 2 | Example footer layout | ✅ done 2026-09-20 | — |
| 3 | Header and underline must agree | ✅ done 2026-09-20 | — |
| 4 | Portuguese cognate exclusions | ✅ done 2026-09-21 | — |
| 5 | The "jump to my level" bug | ✅ done 2026-09-21 | — |
| 6 | Example ordering | ✅ done | — |
| 7 | Merged-lemma policy | research | yes, throughout |
| 8 | Modals using the sides | ✅ done | — |
| 9 | Walkthrough / tutorial / about | ✅ done 2026-09-21 | — |
| 10 | URLs and routing | blocked on one decision | yes |
| 11 | Function words you cannot teach atomically | research, high stakes | yes |
| 12 | Sense metadata vocabulary | a conversation per family | yes, a whole pass |
| 13 | English inflections in translations (*solía*) | moved to `docs/open/conjugations.md` | — |

## Rules for every chat in this batch

1. **Check `git status` first.** Concurrent sessions are normal.
2. **One chat deploys at a time.** `gh-pages` and the two `dev_changelog.json`
   files are the contention points. Groups 2, 3, 6 and 7 all live in
   `flashcards.js` — write in parallel if you like, but do not deploy
   simultaneously.
3. **Cache busting needs three edits, not one.** Bumping `CACHE_NAME` alone
   is **not enough** — it clears the service worker's cache but not the
   browser's HTTP cache, which keys on the `?v=` tag. Changing an asset means:
   bump that asset's `?v=` (in `index.html`, `main.js` and the service-worker
   pre-cache list), bump **`main.js`'s own** `?v=` too (a cached `main.js`
   keeps importing the old URL), and bump `CACHE_NAME`. This cost three
   deploys to learn; the detail is under section 1.
   **Never reuse a tag another session has already chosen.** On 2026-09-21 a
   concurrent session had bumped `flashcards.js` to `20260921a` in its
   uncommitted working tree while also editing `flashcards.js`. Deploying under
   that same tag would have cached one session's file at a URL the other then
   ships different content under — and browsers would never re-fetch it. Pick
   the next letter. Whoever deploys second must bump again.
   **When a shared file holds someone else's uncommitted hunks**, do not
   `git add` it. Rebuild the file from `HEAD` with only your own edits
   applied, then stage that blob with `git hash-object -w` +
   `git update-index --cacheinfo`. Their work stays untouched in the tree.
4. **Deploy at the end of the response**, per the CLAUDE.md procedure.
   GitHub Pages took ~5 minutes per build before the prune below and ~40–100s
   after it. Poll for the new `?v=` tag rather than assuming it is live.
5. **`state.js` is imported under two different `?v=` tags** (`20260920a` from
   `main.js`/`index.html`, `20260825ak` from ~19 other modules), so the browser
   executes it **twice** — confirmed live. Everything it assigns is currently
   idempotent and the one piece that was not (`new Promise` for
   `progressReady`) is guarded. Unifying the tags means bumping every importing
   module's own tag in a cascade, because a cached module keeps importing the
   old URL. Worth doing deliberately one day; do not half-do it.
6. **Keep `gh-pages` lean.** Every Pages build re-checks-out, re-packages and
   re-uploads the *whole* site, so its size is a tax on every deploy. It held
   7.2GB of which 6.1GB was superseded releases nothing referenced; pruning
   to 1.8GB took a build from 5m05s to 1m35s. Publish only the releases
   `config/config.json` and `config/artists.json` name, plus one rollback.
   The workspace, not this branch, is the source of truth for releases.
   To find orphans: collect every `releases/...` path referenced from
   `config/*.json` and `js/*.js`, reduce to release directories (note
   **two** layouts — `releases/<lang>/<mode>/<id>` and
   `releases/lyrics/<id>`), and diff against what is on disk.

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

## 3. The header and the underline must agree — ✅ DONE 2026-09-20

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

Shipped. Both halves now read `resolveExampleOccurrence`, which answers with
the spelling the sentence actually carries. Enclitics peel (up to two, longest
first). When nothing declared occurs, the closest form by shared stem is taken
from the sentence — never under four letters, never across a tail longer than
three — and marked with a dashed underline saying it is the closest form, not
a recorded one.

**A second cause was found underneath the first:** the occurrence regex was
the only comparison in `flashcards.js` that did not fold accents, though
`foldSurfaceForm` exists for exactly that. A card on *estás* matched nothing in
a line spelling it *estas*, which subtitles and lyrics do constantly — the same
visible symptom with no merged lemma involved. Now folded.

**Verification gap worth knowing:** 11 resolver cases pass, including
*buena/buenos* and *verte/ver*, and 22 consecutive live cards show header and
underline agreeing. But the merged-lemma path was **not** exercised on the live
site — study set 1 is all uninflected function words and guest mode has lemma
merging off, so no card in it carries `mergedLemma` or a pooled example. Anyone
touching Group 7 should confirm *unidos* and *buenos* by hand with Fast Track
lemma merging on.

---

## 4. Portuguese cognate exclusions — ✅ DONE 2026-09-21

Reported for Portuguese; it was not a Portuguese bug. The setup screen loads
the **skinny** index (`id`, `word`, `rank`, `surface_card_id`, `lemma`), so
`firstTranslation()` had nothing to read and every row's English column came
out blank on es, pt **and** cs. French looked right only because it is still on
the older single-file `vocabulary.index.json`, which ships `meanings` inline.
Fixed by hydrating from the fat row shards as rows scroll into view —
`mergeIndexRowPayload` assigns onto the very objects the list holds, so a shard
fetch fills `item.meanings` in place. Not eager: the excluded list runs to
thousands of words.

---

## 5. The "jump to my level" bug — ✅ DONE 2026-09-21

`progressData` starts as `{}` and is emptied again on every full (non-delta)
reply, so an empty map meant either "nothing learned" or "we have not looked
yet". `renderLevelSelector` and `renderRangeSelector` read the second as the
first: every set counted as fully unseen, `firstUnseen` resolved to 0, and the
learner landed on set 1 of level 1 — then the next render corrected it, which
is the glitch-and-refresh.

`window.progressDataLoaded` / `window.progressReady` are now that declaration,
settled on every exit path (cache, successful reply, failed reply, thrown
fetch, guest mode, restored guest session). Both renderers await it, capped at
four seconds and giving up once rather than once per render.

The Fast Track suspicion is covered: remembered Fast Track preferences are
reconciled from the same reply, before progress is marked loaded.

---

## 6. Example ordering — ✅ done (2026-09-21)

File: `app/js/flashcards.js`, `sortExamplesByRelevance()` and
`displayExamplesForSense()`.

Four keys compared in order, no weighted sum and no scoring cascade:

1. has an English translation
2. is a single sentence
3. WSD confidence tier — `cheap_leaf_choices_agree` > leaf > glosskey > tuple
4. reinforces a word missed in the last week

Ties keep deck order. The canonical dictionary example is the **second**
example; it leads only when no usable corpus line exists (1.1% of senses).

**The confidence question was answered from the data, not by a rebuild.** No
projection change was needed: `metadata.wsd.gemini_recommendation.reason` and
`metadata.wsd.supported_level` already ship on every example, and the app
already reads that object via `exampleWsdMeta()`. `schemas/wsd-assignment.schema.json`
has richer numbers (`confidence`, `raw_margin`) that are still unprojected, but
they buy little: `supported_level` alone moves the top pick in only 7.4% of
multi-example senses.

**Confidence must RANK, never GATE.** `cheap_leaf_choices_agree` covers about a
quarter of examples. Gating slot 1 on it pushes **79.8%** of cards onto a
dictionary first line; ranking by it leaves **1.1%** without a corpus line.
This is the single measurement that decided the design — do not undo it.

**The canonical example is not a neutral fallback.** Measured on v15: 90.7% of
meanings have one, but **9.3% run to two sentences** and only **44.6% contain
the card's own surface form** — so a canonical first line frequently shows
*bueno* for a *buenos* card with nothing to underline. That is why it sits
second.

**What was removed, and why it should not come back.**

- `easiness` — byte-identical to `metadata.selection_metrics.score` on all
  7,919 sampled examples. An opaque composite of frequency burden, length
  penalty and harder-token count. Worse, `ex.easiness || 999999` treated the
  **15.9%** scoring exactly `0.0` as missing and sorted the *easiest* lines
  last.
- the 6–14 token length window — the pipeline already caps length at 4–15 and
  already charges `length_penalty` into the score.
- deck-word overlap — at ~3.5k visible cards nearly every token is a deck word,
  so it was sentence length in disguise.
- `rankConfidentWsdExamples` sorted by relevance and then **re-sorted** by
  `supported_level`, discarding the first result. Two orderings were fighting.

**Still dead in the file:** `computePersonalEasiness()` (~784) and
`contentTokenCount()` (~908) now have no callers. Left in place deliberately —
`computePersonalEasiness` is the only thing that would answer whether a
sentence whose every other word is known should rank first or last (today it
returns `999999`, i.e. **last**, which is probably backwards for an example
illustrating the card you are studying). Note that `Data/Spanish/spanish_ranks.json`
**404s on the live site**, so `_spanishRanks` is null and that function was
already inert before this change.

**Verified live** on `https://rabbijoshy.github.io/Fluency-Next/`, Spanish
level 6, guest: first line single-sentence with the surface underlined, the
dictionary line second with its provenance icon and no source name, no new
console errors (the four 404s — `backend/secrets.json` ×2, `spanish_ranks.json`,
`Artists/spotify_tracks.json` — are all pre-existing).

**Measured effect:** across all 28,661 senses of the live v15 deck the first
line changes for 3.9%; 306 (1.07%) still lead with a multi-sentence line
because every example they have is one.

## 7. Merged-lemma policy — research, back-and-forth

Files: `app/js/flashcards.js`, `app/js/card-metadata-pills.js`. Read
`docs/INVARIANTS.md` first. Everything here follows from one thing: **identity
is the surface form, and the lemma merge is a view over it.** Group 3 has
landed, so the header and underline already agree.

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
evidence" caveat — extend that function rather than adding a second path.

**Also verify here:** Group 3's merged-lemma path was never exercised live
(study set 1 is all uninflected function words and guest mode has lemma merging
off). Confirm *unidos* and *buenos* by hand with Fast Track lemma merging on.

**Done when:** there is a written merge rule in `docs/decisions/`, *unidos*
behaves under it, and the frequency shown on a merged card is unambiguous about
what it counts.

---

## 8. Modals using the left and right sides — ✅ done (2026-09-21)

**The rule (Joshua's wording, widened after the first pass):** anything that
does not move you within your set opens at the side when there is room. A
task that takes your attention (sign-in, settings, imports, language picker,
Fast Track, end of deck) stays centred. **Rarer uses is the one exception on
the card:** it steps you onto a temporary card, so it is navigation, not a
panel — and it shares the card-chain code the MWE child-cards chat is
rebuilding. Revisit it once that lands.

The whole rule lives in **`app/js/side-dock.js`**, reached as
`window.sideDock`. Add a new panel there, not in its own module.

**The two sides (revised the same day, Joshua's model).**

| side | means | occupants |
|---|---|---|
| left | you and the app | **settings**, with anything opened from it stacked on top (saved words, Fast Track, progress, find word); otherwise progress, total progress, saved words, shortcuts, help |
| right | this card | dictionary, synonyms, conjugation, card data, lyric breakdown, rarer-sense knowledge, word search; on the setup page the word lists and cognate rules |

- **Spill:** when the right is taken and the left is free, the next right-hand
  panel opens on the left, so dictionary and conjugation read side by side.
  Both taken: it replaces the one on the right.
- **Settings owns the left:** opening it closes a card panel spilled there.
  It stays open across card changes and when you leave the set.
- **Stacking:** a sheet opened while settings is open sits on top of it
  (`data-dock-stack`, z-index 1010); closing it returns to settings. Saved
  words and Fast Track used to close settings first; they now leave it open
  when `sideDock.keepsSettingsOpen()`.
- **Card things** on either side close on a card change or flip to front.
- **Escape order:** right-hand panel, then the sheet stacked over settings,
  then other left sheets, then settings. Never leaves the set while one is
  open.
- **Mechanism:** `side-dock.js` decides and marks `data-dock="left|right"`;
  the CSS draws only the two positions. Per-id docking rules are gone —
  including the original 1360px block — because id selectors outrank an
  attribute-keyed side. The CSS lists the dockable ids inside `:is()` so it
  in turn outranks each modal's own id-level sizing.
- The language/mode picker ("Your learning settings") stays centred:
  changing it takes you out of your set.

**Setup page, ≥1024px.** No card to keep in view and ~110px gutters at 1360,
so reference sheets open as one right-hand sheet over the progress sidebar:
merged forms, skipped words, extras, saved words, cognate rules, progress,
total progress, help, shortcuts.

**Narrower windows and phones are unchanged:** conjugation full-screen,
panels inside the card, sheets centred and modal.

**How it works.** Card panels render inside the back face, where `.card-face`
clips them and the flip transform makes even `position: fixed` resolve
against the card. `sideDock.openCardPanel()` hosts them on `<body>` with
`.is-docked`; `stowCardPanel()` puts them back. Modals open through other
modules, so a `MutationObserver` per modal makes each claim its gutter as it
appears instead of editing every opener. `beforeBackRender(card)` runs in the
`backContent` swap: it drops hosted panels (they belong to the markup being
replaced) and, on a real card change, closes the card-bound modals.
`flipCard` calls `closeForFront()`.

**Dictionary and card data are audit-only** (`isAuditAccount`), so a guest
never sees them. **Synonyms data exists only in the lyrics decks**; v15
speech rows carry none.

**Testing notes for the next chat.**
- The browser pane is narrower than 1360px and cannot crop-zoom.
  `document.documentElement.style.zoom` distorts fixed-position geometry;
  shift with `transform: translateX(-Npx)` on `<html>` instead.
- A backgrounded pane (`document.hidden`) freezes CSS animations and
  `requestAnimationFrame`, so slide-ins read as off their resting place,
  desktop card navigation (which waits on `animationend`) never advances,
  and screenshots can be stale frames. Both slide-ins now commit their start
  state with `void panel.offsetWidth` rather than a frame for this reason.
- Test against a clean `HEAD` worktree with only your files overlaid; link
  `releases/` and `coverage/` from the gh-pages worktree to get deck data.
  `tests/app/test_product_shell.py` pins `main.js`, `style.css` and
  `CACHE_NAME` — bump it with every deploy.

## 9. Walkthrough / tutorial / about — ✅ DONE 2026-09-21

Done: `docs/decisions/0023-tutorial-walkthrough-about.md`. The three words are
pinned in `docs/NOMENCLATURE.md`. Original brief below.

Three separate things, currently confused.

| Thing | Audience | Contains | Platform |
|---|---|---|---|
| **Tutorial** | people actually using the app | how to study, settings, modes | desktop + mobile, both first-class |
| **About** | employers / people being shown the app | what this is, how it was built; **links to** the walkthrough; does **not** contain the tutorial | desktop-first, comfortable on mobile |
| **Walkthrough** | someone being shown the app, not using it | a surface-level "here is what a card looks like" demo | either |

The walkthrough existed and appears to have been replaced by the tutorial.
First establish what `app/js/about-example.js` renders today and which of the
three it actually is. Do not guess — guessing is how it got confused.

---

## 10. URLs and routing

The app has no real routing. Proposal: two addressable things — a deck position
(`/#/es/set/47`) and a word by surface key (`/#/es/w/unidos`), plus
`/#/es/artist/bad-bunny` and URLs for about/tutorial/walkthrough (which need
them to be shareable at all).

Blocked on one decision: should a shared link address a deck position or a
word? Given `card_id = f(language, surface_key)`, the word is the durable link
and the set is a convenience — but everything else follows from that answer.

Note `?speechRelease=<id>` already exists (`app/js/config.js` ~31) and points
the live app at any published release; it should survive whatever routing
replaces the current query handling.

---

## 11. Function words you cannot teach atomically

Spanish `lo` WSD is almost always wrong; `de`/`del` (and the a/an-shaped pairs)
probably want to be taught together with a rule. Two parts: a warning on
hard-to-translate function words, and a concept of a paired card that the
surface-keyed identity does not currently have. Read `docs/INVARIANTS.md`
before proposing anything. High stakes — these are the first words a beginner
meets, and `que` and `de` are literally study set 1.

---

## 12. Sense metadata vocabulary — a whole pass, one conversation per family

Editorial, not code. Does `2nd pl` help a learner? Which short metadata should
become an icon rather than a third line of tiny text? Which families are worth
showing at all? The legibility floor is already shipped (pills no longer go
below 10px, grammar tier lifted off `--text-muted`); this is about *what* is
shown, not whether it can be read.

---

## 13. English inflections in translations (*solía*)

Moved to `docs/open/conjugations.md` → *Come back to*, which is where the
English-inflection work lives (the DRAWER chat).

Correction to what this section said before: the defect is in the **app**, not
the sense-menu projection. The menu gloss is `to use to`; the app's inflector
(`finiteEnglishCue` in `app/js/reverse-cues.js`) turns every imperfect into
`was/were + -ing`, producing “he/she was using to”.
