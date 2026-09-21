# Decision 0024 — Merged-Lemma Policy and Card Frequency Display

Settles UI work order 7 (`docs/ui/UI_WORK_ORDERS.md`). Measured against the
shipped `es-speech-v15-10000x10` and `fr-speech-v7-dual-metadata-v5-20260918`
releases.

## Decision

1. **The unit of merging is the sense, not the surface.**
   A merged card is one lemma, holding every sense — from any surface — whose
   `headword` names that lemma. A surface with senses under two headwords
   contributes each sense to its own lemma card and appears on both.
   The frequency-weighted argmax in `assignedHeadwordOf` is retained for
   *display* (choosing a card's citation form) but is **no longer** what decides
   grouping.

2. **The lemma key excludes expression-child senses.**
   A phrase never forms a lemma key, whatever its WSD routing. Invariant
   (`deterministic_bypass`) and ambiguous (`competitive_wsd`) MWEs are both
   excluded, reusing `isExpressionChildMeaning` from `app/js/flashcards.js`
   rather than a second predicate. This follows from
   `docs/WSD_ARCHITECTURE.md` Invariant 4 — MWEs attach to the cards of their
   component surface forms — and Invariant 1, which forbids any non-surface
   identity. A surface left with no lemma key stands alone as its own card;
   absence is declared, not inferred.

3. **Senses are deduplicated on `source_reference`, never on `sense_id`.**
   `sense_id` is minted per surface and cannot collapse across forms.
   `source_reference` (`provider:lemma:sense`, e.g. `spanishdict-menu:dar:662`,
   `kaikki:en-de-fr-article-c3KuqgRJ`) is lemma-stable. Coverage is 100% on
   both the Spanish and French releases. The content signature
   `pos|translation|context` remains the fallback where a provider supplies
   neither.
   `knowledge.js`'s sense signature is **card-scoped by design** and must not
   be reused for merging.

4. **A displayed frequency is never split across lemmas.**
   The card shows the surface's own published figure. Long-press or tap
   itemises the real per-surface values (`unidos 69.3 · unido 12.5 · unir 8.0`)
   so the reader can audit what is counted. No derived or apportioned number
   reaches the screen.

5. **Deck ordering may use an apportioned total; display may not.**
   `pooled_frequency` sorts the merged deck (`app/js/vocab.js`). Where a surface
   contributes to more than one lemma, its count is apportioned by the senses'
   assigned share, smoothed as
   `weight = (evidence + α) / (total + α × senses)` so that thin evidence tends
   to an even split and an all-unassigned deck splits evenly without a special
   case. `α` is to be chosen from the measured evidence-count distribution.

6. **Overflow is handled by the existing rare-sense filter**, applied on top of
   the merged view. No new mechanism.

7. **Progress is untouched.** The lemma key is computed at load and never
   stored. Card progress stays keyed on `fullId` and bridged by normalised
   surface; item progress stays `<parentCardId>~k<ver>:<type>:<hash>`.

---

## Context & Rationale

### 1. Why the surface was the wrong unit

`lemmaGroupKey` grouped by a single argmax headword per surface, so every
surface had to pick one lemma. That forced choice was the sole source of the
policy's difficulty: it required a confidence threshold, a tie-break rule, and
an answer to "which sense decides?".

It also produced the reported *unidos* defect. Measured on the shipped EsPal
table (`app/data/speech-frequency/es.json`, per million):

| surface | value |
|---|---|
| unidos | 69.268 |
| unido  | 12.507 |
| unir   |  7.985 |
| unidas |  7.263 |
| unida  |  5.890 |

The visible *unir* paradigm totals ~140.9, of which the single surface *unidos*
is **49%** — overwhelmingly *Estados Unidos* and *estamos unidos*, not the verb.
Filing it under *unir* inflated the verb ninefold over its citation form.
*bueno* (1998.6 + 569.0 + 389.0 + 289.9 = 3246.5) is the contrasting case where
the group is genuinely one word and the sum is honest.

Merging senses removes the choice entirely: each sense already carries exactly
one headword.

### 2. Merging makes cards smaller, not larger

The concern was that a merged card, especially on a Wiktionary-backed language,
would accumulate senses. The opposite holds, because each surface was carrying
its own duplicate copy of the lemma's menu.

**Spanish — 10,000 surface cards → 6,492 lemma cards**

| | mean | median | p90 | p99 | max |
|---|---|---|---|---|---|
| before, shown senses | 3.1 | 3 | 6 | 10 | 30 |
| after, shown senses | 2.8 | 2 | 5 | 13 | 42 |
| before, incl. rare | 9.6 | 7 | 22 | 43 | 72 |
| after, incl. rare | 5.1 | 4 | 10 | 24 | 81 |

**French (Wiktionary) — 200 → 184 cards:** mean 5.9 → 4.1, median 4 → 3,
max 40 → 35. Proportionally it benefits more than Spanish, not less.

The ceiling rises (30 → 42 shown) while mean and median fall. That is the
entire cost of the change.

### 3. Why `sense_id` cannot be the dedup key

Deduplicating on `sense_id` reported *dar* as **1,637 distinct senses** — while
that card carries only **28 distinct translations**, with "to give" repeated
215 times across 43 surfaces. `sense_id` is hashed per surface.

`source_reference` embeds the lemma. On a 40-shard sample the *dar* rows
collapsed 74 → 24. The corrected distribution is the table above.

This is the one place where reusing an existing mechanism would have been
wrong: `knowledge.js:96` builds its sense key for knowledge items, whose
`itemId` is already parent-prefixed, so card-scoping is correct there and fatal
here.

### 4. The longest cards, and why the rare filter suffices

| Spanish lemma | shown | incl. rare |
|---|---|---|
| dar | 42 | 77 |
| hacer | 40 | 40 |
| salir | 37 | 81 |
| tener | 33 | 58 |
| echar | 28 | 38 |
| estar | 26 | 56 |

French worst case is *passer* at 35.

| threshold | Spanish lemma cards over it |
|---|---|
| > 8 shown | 140 (1.91%) |
| > 12 | 61 (0.83%) |
| > 20 | 15 (0.20%) |
| > 30 | 4 (0.05%) |

Capping the merged view at 8–12 leaves ~98% of cards untouched, and the
overflow population is the genuinely hardest vocabulary in the language. A card
reading "42 senses, showing the 12 commonest" is an honest statement about
*dar*.

### 5. Why phrases are excluded from the key

Grouping phrase senses by headword mints lemma cards named after the phrase,
because an MWE sense carries the phrase as its `headword`:

```
por favor     assembled from surfaces {favor, por, porfavor}
por qué       from {por, qué}
a base de, a bordo, a cargo, para siempre, del mundo …
```

Of 771 lemma cards whose shown senses were all phrases, **622 had a headword
containing a space**. Applying rule 2 reduces multiword lemma keys from 622 to
**2** (*el pentágono*, *no obstante*).

The shipped Spanish deck separates the two MWE populations cleanly by source
adapter, not by heuristic:

| type | source adapter | senses | routing |
|---|---|---|---|
| inventory MWE | `mwe-merged` | 682 | 567 `deterministic_bypass`, 115 `competitive_wsd` |
| dictionary PHRASE | `spanishdict-sense-menu/v1` | 276 | none (275 on the card's own word) |

Neither type is an identity. `CHAT_ROADMAP.md:215` (FUSE) states it directly —
*"Card id stays the surface"* — and the invariant/ambiguous distinction settled
across FUSE → SIEVE → MILL → CHISEL 1 → CHISEL 2 is a **routing** distinction
(does the phrase compete or bypass), carried into the UI as the expression
child card shipped in `c20ef55`. It is not a grouping distinction, and this
decision does not reopen it.

240 surfaces are left with no lemma key — *dame, dime, déjame, cállate,
buenas*. They stand alone, which is what Invariant 1 already requires:
*"Inflected forms, clitics, and contractions (`dame`, `deixa-me`, `pa'`)
retain their own progress cards."*

### 6. Why an apportioned frequency may sort but not display

Sense shares come from WSD over harvested sentences, and three things bound
their quality: small per-sense evidence counts; a harvest that is filtered
rather than sampled, so a sense absent from the menu can never receive
assignments; and WSD being optional, leaving pt/es unassigned releases at zero
throughout.

The comparison is not against truth but against present behaviour, which
assigns 100% of a surface's frequency to one lemma via the same noisy argmax.
Any smoothed split is closer. But no sense-level frequency exists anywhere in
the system — `speech-source-frequency/v1` is a flat surface→value map with no
POS or sense field — so a displayed split would assert precision the data
cannot support, contrary to Invariant 3 of `docs/INVARIANTS.md`. Ordering is
ordinal and tolerates the estimate; a printed number does not.

The same measurement answers the standing question in work order 7b, *why do
interjections have a frequency*: the list is surface-keyed and POS-blind, and
the surfaces are genuinely present — `ay` 162.6, `eh` 426.7, `oh` 1091.6 per
million. Card copy must therefore say it counts the spelling, not the sense.

### 7. Why progress is safe

`app/js/progress-identity.js:41` states the rule: *"identity is the observed
language surface, never mode, artist, lemma, POS or sense."* The lemma key is
rebuilt by `buildSeenLemmaSet` on every load and never persisted.

The key is consulted at one point only — step 4 of the seen-state ladder in
`app/js/ui.js`, which runs *after* a card's own progress row and its
related-id matches. A narrower key can therefore only withdraw *inherited*
seen-ness, never recorded progress. Because rule 1 can only make groups
smaller, the failure direction is "a word is shown again", never "a word is
marked learned that was not studied".

Two visible consequences follow and are accepted:

- Deck order changes. It already does: merge mode re-sorts the whole deck on
  `pooled_frequency` (`app/js/vocab.js`) and assigns `displayRank` by position.
  The estimated-level shortcut reads `item.rank`, the source corpus rank, so it
  is unaffected by the reorder.
- Where a group's elected representative changes, item-level knowledge progress
  does not follow, because `itemId` is parent-prefixed and the bridge in
  `getSpecificItemProgress` matches on surface, not across a lemma. A surface's
  sense-level detail stays with that surface.

---

## Consequences

- `lemmaGroupKey` returns a key per sense rather than one per item; bucketing,
  representative election, and seen-inheritance iterate instead of looking up
  once.
- The argmax confidence threshold, tie-break rules, and POS tie-break
  contemplated in earlier drafts of work order 7 are not needed and are not
  implemented.
- `sourceFrequency` on a merged card reverts to the surface's own value; the
  per-form breakdown is carried for the tooltip rather than collapsed to a
  count.

## Open

- `α` for rule 5, pending the per-sense evidence-count distribution.
- Whether the two surviving multiword keys warrant a rule or are accepted.
- Near-duplicate senses under the content-signature fallback are unmeasured on
  a provider that supplies no stable id; both releases examined here supply one.
