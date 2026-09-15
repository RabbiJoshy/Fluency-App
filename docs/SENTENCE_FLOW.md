# The sentence flow

**The intended design.** Where the code differs, the code is wrong, not this.

Every stage below narrows the set of sentences, but they narrow for different
reasons, and confusing those reasons is what produces the recurring bugs:
a quality judgement made in a budget stage, or a budget enforced where a
judgement belongs.

---

## Stage 0 — Corpus snapshots

Immutable, content-hashed copies of OpenSubtitles and Tatoeba under `raw/`.
Never edited. A snapshot is not the corpus and not a pool; see NOMENCLATURE.md.

## Stage 1 — Harvest

**Purpose: do anything cheap here, because this stage reads millions of records
and is the slowest thing in the pipeline.**

Negative, irreversible gates only — form rules applied while scanning: too
short or long, truncated fragments, mid-sentence starts and ends, dialogue
turns, speaker labels, all-caps, bracketed annotations, missing inverted
punctuation, echoed target, identical sides. Plus a per-card budget cap on how
many candidates to retain.

The test for whether something belongs here: **is it cheap, and would you never
want the sentence back?** If it is expensive, or you might want it back later,
it does not belong at harvest.

## Stage 2 — Cleaning and tagging

One pass over the harvest output. **Exactly one thing rejects**: the alignment
floor, which drops garbage translations. Everything else *tags* — alignment
score, grammar constructions, variety, hardness band, length band, surface
position, translation length ratio.

Nothing is deleted. A rejected candidate keeps its row and gains a reason, so
the decision stays auditable and the floor stays revisable: when a card comes up
short, why a sentence is missing is exactly what is wanted.

## Stage 3 — The frozen pre-WSD set

Three hash-pinned documents per run, under
`raw/surfaces/<lang>/prewsd/<run-id>/`:

| document | key | holds |
|---|---|---|
| **ledger** | surface | verdict, lemma and provenance, tags, eligible sentence indices |
| **examples** | index | the sentences, in a fixed order, with sentence-intrinsic metadata |
| **pairs** | (card, sentence) | burden, difficulty, surface position |

A sentence's identity is its row index in `examples`, which is why the other
documents can reference it as an integer.

The pair metrics cannot be folded into `examples`: they are properties of the
*pairing*. One sentence costs 16.41 against `que` and 9.06 against `lo`,
because burden counts words harder than that card's rank.

**WSD reads this set plus the sense menu, and nothing else.** With no run
directory in scope, WSD structurally cannot re-harvest.

## Stage 4 — WSD selection

**Purpose: make disambiguation as easy as possible against a fixed
computational budget.**

This is a *cost* cap, not a filter. Nothing is excluded — unpicked sentences
remain in the set as overflow. The question is not "which sentences are best"
but **which sentences give the most reliable sense decisions per unit of
spend**: good alignment, moderate length, low grammar load, the target word
clearly placed, senses well separated.

**It must not bias the sense distribution.** This is the constraint that makes
the stage hard. Selecting for ease, register or difficulty is legitimate;
selecting in a way that systematically favours some senses over others is not,
because the resulting distribution then describes the selector rather than the
language. The failure is quiet: prefer short, easy, high-alignment sentences and
you will tend to over-sample dominant senses and under-sample rare ones, and the
deck will look less polysemous than the language actually is. Any criterion
added here should be checked for whether it correlates with sense frequency, not
only for whether it improves accuracy.

## Stage 5 — UI selection

**Purpose: vibes, under a memory constraint.**

Draws **only from sentences WSD actually disambiguated**. If WSD did not look at
it, the UI cannot show it.

The cap exists for payload size and is tiered by frequency rank: more examples
on the common, polysemous words at the front, fewer in the tail. Preferences
layer on top — European against Brazilian, register, and so on. Difficulty is
not re-derived here; that was decided upstream.

---

## Canonical examples — a parallel track

The dictionary's own illustration of a sense. **They bypass stages 1 to 4
entirely** — no harvest, no cleaning, no alignment, no WSD, no cost — because
the provider already bound them to a sense.

- **Exactly one per sense.** SpanishDict is effectively one-per-sense already,
  but 28% of Portuguese senses and 29% of Czech ones offer two or more, up to
  ten.
- **Filtered to proper sentences**: no quotations (literary citations), no
  collocations (patterns, not sentences), and English is required. Every
  criterion is provider-declared, never inferred from the text.
- **Completely independent of the UI cap.** The cap governs corpus examples
  only. A card showing twelve canonical sentences still gets its full corpus
  allocation.
- **Coverage is uneven, and that is accepted rather than compensated for**:
  es 99.4%, pt 48.3%, cs 34.3% of senses. A sense without one shows none.
- **They never count towards commonness.** Canonical examples are dictionary
  prose, not corpus evidence. They must never feed frequency ranks, frequency
  burden, hardness, or any statistic about how common a word or a sense is.
  They are illustrations, not observations; counting them would let the
  dictionary vote on what the language does.

---

## Two rules that hold throughout

**Prefer the provider's own declaration over inferring anything.** SpanishDict
answers a word it lacks by silently substituting a near-spelling. Trusting its
`spelling_suggestion` flag rather than a stem heuristic prevented 25 wrong
lemmas in one class of one language, including `llévatelo` → *llegar* and
`pásamelo` → *parar*.

**Events are facts; verdicts are policy.** Observations are appended and never
rewritten; keep, review and exclude are folded from them at read time. A
judgement is reversed by editing a policy table, not by re-running a stage.
