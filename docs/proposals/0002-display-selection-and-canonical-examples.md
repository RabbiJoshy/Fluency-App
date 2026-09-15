# Proposal 0002 — Display selection and canonical examples

**Scope: the display stage only.** Everything upstream is settled and frozen.

Read `docs/SENTENCE_FLOW.md` first; it is the intended lifecycle and this
proposal implements stage 5 of it. The four changes below are the standing
divergences between that document and the release builder. None is a v12
regression; v12 inherited all of them.

## Out of scope — do not touch

| | |
|---|---|
| harvest | `src/fluency/harvest/` |
| cleaning and tagging | `scripts/condition_pools.py`, `harvest/conditioning.py` |
| the surface ledger | `scripts/materialise_surfaces.py`, `surfaces/` |
| the frozen pre-WSD set | `surfaces/prewsd.py`, `raw/surfaces/<lang>/prewsd/` |
| WSD itself | `speech/wsd_execute.py`, `wsd/` |

Those produce a hash-pinned artifact set that WSD consumes and nothing else.
Changing them is a different piece of work with different risks. If a change
here seems to need a change there, stop and say so rather than reaching
upstream.

**In scope:** `src/fluency/release/run_candidate.py`, the deck schema,
`config/pipelines/<lang>/speech/*.json`, and the app's rendering of examples.

---

## 1. Display must draw only from sentences WSD disambiguated

**Now:** WSD spends its budget on the ledger's top 30 per card, then
`run_candidate.py` picks the displayed 10 from the **full pool** by form
penalty, ignoring which sentences WSD actually looked at. Two selectors, two
orderings, and the second silently overrides the first.

**Measured (Spanish v12):** 59,984 examples displayed, 43,132 assigned (71.9%).
That 28% is not WSD failing — it assigned a sense to **99.6%** of what it
evaluated. It is examples being shown that WSD never saw.

**Change:** restrict the candidate pool for display to sentences carrying a
`selected_sense_id`.

**Cost:** median sensed per card is 30 against a display limit of 10. Only 32
of 6,000 cards fall below 10, and 25 of those have **zero** because they have no
menu at all and were already shipping unassigned. The real cost is **7 cards**.

**Where:** `run_candidate.py`, the `pool = candidate_card.get("candidates", [])`
block and the four filling passes below it.

## 2. One canonical example per sense, as a first-class field

A canonical example is the dictionary's own illustration of a sense. It needs no
WSD — the provider already bound it to the sense — so it arrives outside the
corpus pipeline **and outside the display cap**. Every sense that has a proper
one shows it; a sense without one shows none, which is accepted rather than
compensated for.

**Now:** the examples ship, but as raw provider metadata under
`meaning.metadata.sense_metadata.source_metadata.spanishdict.examples` and
`meaning.metadata.sense_provider_metadata.spanishdict.examples`. Unfiltered,
uncapped, and not a display field. The app reads those paths only for metadata
pills and the tutorial.

**Change:** emit `meaning.canonical_example` — or None — using
`fluency.sense_menu.canonical.choose(sense)`, which already exists and is
tested. It returns a provider-neutral record (`text`, `translation`,
`bold_text_offsets`, `bold_translation_offsets`, `literal_meaning`, `tags`), so
the card never learns which dictionary answered.

`choose` filters on what the provider declares, never on a reading of the text:
`type: quotation` is a literary citation, `tags: [collocation]` is a pattern not
a sentence, and no English is unusable on a bilingual card.

**Coverage after filtering:** es 63,055 senses (99.4%), pt 15,610 (48.3%),
cs 2,920 (34.3%). Czech pays most because a quarter of its canonical examples
are collocations. Uneven coverage is expected; do not backfill it from the
corpus.

**Note:** `bold_text_offsets` marks where the headword sits, so the card can
highlight it. Worth rendering.

## 3. De-duplicate the provider metadata

**Measured:** `deck.json` for Spanish v12 is **220.9 MB**, of which **82 MB is
meaning metadata**. It ships **132,068** canonical example objects for 66,034
real ones — identical content on both paths above, for 63,055 meanings.

This is the largest single lever on the memory constraint, and it is larger
than the display cap it is being paid alongside. Ship one path, filtered, one
example per sense.

## 4. Make the display cap rank-tiered

**Now:** `display_examples_per_card: 10` — flat at every rank. 5,993 of 6,000
cards show exactly 10; the 7 short ones ran out of supply, not limit.

**The mechanism already exists.** `display_example_tiers` in
`src/fluency/pipeline/budget.py` accepts either an integer (one tier for all
ranks, which is what every profile currently sets) or a list of
`{"through_rank": N, "examples": M}` objects. Nothing needs building; a profile
needs to state tiers.

The intent is more examples on the common, polysemous words at the front and
fewer in the tail. Note that canonical examples already scale that way for
free — rank 1–100 averages 12.1 canonical sentences against 9.6 in the
2,001–6,000 tail — so the corpus tiering has less work to do than it appears.

---

## The invariant that must not be broken

**Canonical examples never count towards commonness.** They are dictionary
prose, not corpus evidence. They must never feed frequency ranks, frequency
burden, hardness bands, or any statistic about how common a word or a sense is.
They are illustrations, not observations; counting them would let the dictionary
vote on what the language does.

Concretely: a canonical example has no `easiness`, contributes nothing to
`wsd_distribution`, and is not a candidate in any selection that produces one.

## Acceptance

- Every displayed corpus example carries a `sense_id`, except on cards with no
  menu, where `assignment_status: unassigned` remains correct and honest.
- Each meaning carries at most one `canonical_example`, and exactly one wherever
  the provider supplies a proper one.
- No canonical example appears more than once in the deck.
- `deck.json` is materially smaller; report the before and after.
- No file listed under **Out of scope** is modified.
