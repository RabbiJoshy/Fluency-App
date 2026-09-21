# Nomenclature

Words worth using precisely, because each one below was confused for another at
some point and the confusion cost something. Use these when talking about the
system, including with an LLM.

## provider

**A sense-menu source.** SpanishDict and Wiktionary are providers. A provider
supplies the inventory of meanings a word may have, and the metadata attached to
them.

A provider is **not** a language and **not** a corpus:

| | |
|---|---|
| **provider** | where the *meanings* come from — SpanishDict, Wiktionary |
| **language** | `es`, `fr`, `pt` |
| **mode** | speech, lyrics, artist — where the *sentences* come from |
| **source** | ambiguous; avoid it. Say provider, corpus, or snapshot. |

The distinction matters because they do not line up. SpanishDict serves one
language. **Wiktionary serves French, Portuguese and everything after.** So a
change that works "for Portuguese" usually means it works for Wiktionary, which
is a much larger claim — and a change that works "for Spanish" often means only
SpanishDict, which is a much smaller one.

Ask *"is this provider-agnostic?"* rather than *"does this work for other
languages?"* — the second question hides which of the two you meant.

## provider parity

**The requirement that a concept exists for every provider that can express it.**
A signal, gate or feature built for SpanishDict alone is not finished; the
Wiktionary equivalent ships with it, or a recorded reason says why there is none.

Providers encode the same concept differently, so parity is achieved by adapters
rather than by sameness. The companion note is the worked example: SpanishDict
writes prose in `context` (`used with "de"`, 587 senses), Wiktionary emits a
structured `+obj` template (438 senses in Portuguese). One `companion` feature
family, two extractors, one gate that cannot tell which it is reading.

## contract, method, carriage

Three different claims about an artifact that sound like one:

- **contract** — the shape it speaks. "This release speaks v7's dual view."
- **method** — what computed the decisions inside it. "These were chosen by v7."
- **carriage** — how they got there. "These were migrated, not recomputed."

A release can speak v7's contract over decisions computed by v5 and carried
forward. Reading `retained_materialized_assignments` — a carriage label — as a
method claim once led to the conclusion that the Rosalía releases were stranded
on v5. They were not.

## adapter and engine

- **adapter** — absorbs the irregularity of one provider, corpus or frequency
  list, and emits a neutral contract. There are nine.
- **engine** — everything below the adapters: one WSD, one selection, one release
  path, shared by every language and mode.

"Put it in an adapter" means *this varies by provider or corpus*. "Put it in the
engine" means *this is the same everywhere*.

## the specificity ladder: leaf, glosskey, tuple, unresolved

How precisely a decision is published:

| | |
|---|---|
| **leaf** | the exact sense — *casa* = a dwelling |
| **glosskey** | the meaning, not the shade — *casa* = house |
| **tuple** | lemma and part of speech only — *casa* = a noun |
| **unresolved** | no claim; stays in the denominator, never renormalised away |

**Backing off** is moving down this ladder. Note that how much the middle rung is
worth is provider-dependent: `glosskey` is nearly inert on SpanishDict and
carries 16–22% of decisions on Wiktionary.

## budget and limit

- **budget** — a number that is *spent*. `wsd_budget_per_card` decides how many
  sentences reach a paid model.
- **limit** — a number that is merely enforced. `display_examples_per_card`
  costs bytes.

Only the spendable one is called a budget. Calling both a "cap" is what let a
change to the expensive number look like a change to the cheap one.

## pool

**A named, described set of harvested sentences.** Flat — no cards in it, so one
pool serves any inventory. Everything below a pool narrows within it, which is
why "every example on this card came from one pool" holds by construction.

## provider-agnostic, provider-specific, provider-shaped

Three states worth distinguishing when reviewing a change:

- **provider-agnostic** — works for any provider without knowing which. The
  engine, the contracts, a gate reading a feature family.
- **provider-specific** — knowingly tied to one, with the reason recorded.
  SpanishDict's `AUX` bridge is provider-specific because SpanishDict has no
  `AUX` category; that is a fact about SpanishDict, not a shortcut.
- **provider-shaped** — the bug. Written for one provider by accident, usually by
  asking "what does this provider give us?" instead of "what does the engine
  need, and how does each provider express it?"

The third looks like the second until someone checks.

## family, extractor, channel

The parts of a feature, which are easy to conflate:

- **family** — the kind of thing: `domain`, `register`, `construction`,
  `companion`. Defined once in `features/contract.py`, shared by every provider.
- **extractor** — the per-provider code that produces features of those families
  from that provider's own encoding. One per provider.
- **channel** — a family as consumed by a specialist or scorer. A channel may be
  enabled or disabled independently of whether the family is populated.

A family with no extractor on one side is a parity gap. A populated family with
no channel is captured-but-unused, which is where `surface_grammar` sits today.

## layer

**A per-word or per-card artifact joined onto the spine rather than produced by
it.** Conjugations are a layer; an enrichment is a layer. Distinct from a
**stage**, which is a step of the pipeline that every run performs.

"Add a layer" means a new optional join. "Add a stage" means changing the
pipeline for every language and mode.

## run, release, deck

- **run** — a directory of immutable stages under
  `<workspace>/runs/<language>/<mode>/<run-id>`. A run is the unit of work.
- **release** — what is published from a run, under `releases/`. Validated,
  activated by an explicit pointer, never edited in place.
- **deck** — `deck.json` inside a release: the app-facing cards. It is the
  *contents*, not the container.

"Rebuild the deck" is ambiguous. Say which: a new run, a new release from an
existing run, or a re-render of the deck file.

## candidate, assignment, example

Three narrowings, three words, and saying the wrong one hides a stage:

| | | Portuguese run |
|---|---|---:|
| **candidate** | a sentence retained for a card by the harvest | 12,000 |
| **assignment** | a candidate a classifier reached a decision on | 2,000 |
| **example** | an assignment selected to appear on the card | 600 |

Only the middle step costs money. See **budget**.

## snapshot

**An immutable, content-hashed copy of an external input**, under
`<workspace>/raw/`. A snapshot is not the thing it copies and not a set derived
from it:

- **corpus** — the upstream body of text (OpenSubtitles, Tatoeba)
- **snapshot** — a pinned copy of some of it, with hashes and licence
- **pool** — a named set of sentences harvested from a snapshot

## stage, not step

The pipeline has six **stages**, numbered and immutable. Avoid "step"; it drifts
between meaning a stage, a substep, and a CLI invocation. Name stages by name --
`sense_menu`, `sentence_harvest` -- rather than by number alone.

A stage with output refuses to be rebuilt. Create a new run instead.

## bundle

**A WSD executor's output file, before import.** A bundle is *not* stage 04.
`pipeline wsd-import` validates it and publishes it into
`stages/04_wsd_assignments/output/assignments.jsonl`, which is what the release
builder reads.

Skip the import and the release reports "no WSD stage was present" -- truthfully,
and confusingly, because the bundle exists.

## gate, filter, scorer

- **gate** — rejects on a checkable condition. The companion gate asks whether a
  required word is present.
- **filter** — narrows a set, usually by comparing attributes. The POS filter
  compares a tag against dictionary categories.
- **scorer** — ranks candidates by a continuous score. The gloss scorer.

The distinction is not pedantic. A gate's negative means *this is impossible*; a
filter's empty result means *nothing matched*, which must be read as **no
evidence** rather than **reject everything**. Reading it the second way is what
turned the POS filter into a silent no-op on the commonest words.

## abstain, unresolved, unassigned

Three ways of having no answer, at three different places:

- **abstain** — the classifier declined to choose. A property of a decision.
- **unresolved** — the lowest rung of the specificity ladder: a decision was
  made but nothing may be published. A property of a publication.
- **unassigned** — an example with no sense attached to it, because WSD did not
  run or did not reach it. A property of a card.

A deck can be entirely unassigned with no abstentions anywhere, which is what
every Portuguese release before WSD was.

## enrichment

**An optional per-word layer joined by headword or card, sitting beside the
pipeline rather than on it.** Conjugations are one; pronunciation would be.

Enrichments are per-*word* facts. A sense menu holds per-*sense* facts. Putting a
per-word fact in the sense menu duplicates it across every leaf and ties a
pre-WSD fact to a structure that exists to enumerate meanings.

## native, migrated

- **native** — a decision computed in this run.
- **migrated** — a decision computed earlier and carried into the current
  contract by a bridge.

Both are legitimate to ship. `wsd/provenance.py` reports the split per release,
because "this deck is on v7" is true of a fully migrated deck in a way that
misleads. See **contract, method, carriage**.

## tuning set, holdout

- **tuning set** — data you look at repeatedly while developing. You fit to it,
  deliberately or not.
- **holdout** — data you touch once, at the end, to find out whether it worked.

Once a set has been tuned on it is not a holdout again. **Rosalía was tuned on
during v7**, so it is a regression check -- did this break what worked -- rather
than a score. Portuguese has never been tuned on.

## the surface ledger

**The per-language table that says a language is ready.**
`<workspace>/raw/surfaces/<language>/ledger.json`, contract `surface-ledger/v1`.
One row per surface: verdict, reason codes, tags, lemma and its provenance,
alternates, part of speech, and the harvest/eligible/rejected sentence counts
with their ids.

A language is **ready for WSD when its ledger is complete**. That is the whole
definition. WSD, cognate mapping and any future language read the ledger rather
than reconstructing what it contains.

It was called `surfaces.json` / `surface-view/v2` while it was a byproduct. Do
not call it a view: a view is derived and disposable, and this is the contract.
Read its path from `fluency.surfaces.ledger.ledger_path()`, never as a literal.

## event, verdict

The two halves of the ledger, which must not be conflated:

- **event** — an observation, appended to `events.jsonl` and never rewritten.
  *What was seen.* `accent_stripped_duplicate`, `dictionary_absent`.
- **verdict** — `keep` / `review` / `exclude`, computed by folding a surface's
  events through the policy table **at read time**. *What to do about it.*

**Events are facts; verdicts are policy.** Changing a judgement means editing
`policy.py` and re-materialising — never editing history. Several reason codes
have had their verdict inverted after the fact at no cost because of this.

## durable, run-scoped

Two kinds of evidence, partitioned in `events.py`:

- **durable** — a fact about the word. Survives a re-harvest. 94–99% of events.
- **run-scoped** — a fact about one corpus pass: `capitalised_in_corpus`,
  `low_harvest_yield`. Expires with the run that saw it.

This is why a re-harvest is cheap. It refills freed ranks; it does not rebuild
knowledge. Saying "the store is stale after a re-harvest" overstates it by
roughly twentyfold.

## authority

**The provider entitled to supply a language's primary lemma** — which is
always whoever supplies that language's *sense menus*, because a lemma's job is
to find a menu. SpanishDict for `es`; Wiktionary for `pt`; ČNK then Wiktionary
for `cs`.

A lemma from a non-authority source is not wrong, it is **unusable for its
purpose**: it may name a headword the menu provider has never heard of, which
reads as resolution and resolves nothing. Those go to `lemma_alternates`, kept
because they are correct morphology, and they never lead.

## harvest, cleaning, WSD

The three stages, split by *cost and reversibility* rather than by topic:

| | | |
|---|---|---|
| **harvest** | cheap, irreversible gates | keeps everything that passes |
| **cleaning** | expensive narrowing | tags rejects, deletes nothing |
| **WSD** | disambiguation only | reads a filtered view of the ledger |

"It's a harvest gate" is a claim about *cost*, not about correctness. A test
that is right but slow belongs in cleaning. A test that is cheap but discards
evidence you may want back belongs nowhere.

## alignment score

**A LaBSE cosine between a sentence and its translation.** It measures
**literalness, not correctness** — a correct idiomatic translation scores low
(`The sands are running out.` at `0.353`). Floors are set to catch garbage, not
to rank quality, which is why they sit near `0.30`–`0.45` rather than high.

Do not call it a quality score; that reading is what first set the floor at
`0.67` and stripped idiom.

## card identity

**The observed surface form.** `card_id = f(language, surface_key)` and nothing
else. Not the lemma, not a sense, not a rank.

---

# The app

Names taken from the elements that exist, so a request maps to something
findable. Where a name below is a class or id, it is quoted as such.

## setup flow, study view

The app has two phases, and "the app" alone rarely distinguishes them:

- **setup flow** — everything before cards appear. In order: the **language
  tabs** (`#languageTabs`), the **level selector** (`#levelSelector`), the
  **extra-category selector**, and the **range selector** (`#rangeSelector`).
- **study view** — the card and its controls.

"Change the level screen" is ambiguous; say level selector or range selector.

## card, face, container

- **card** (`.card`) — one word being studied.
- **card container** (`.card-container`) — the frame it sits in, including
  swipe/scrub behaviour.
- **front** and **back** — the two faces. The front carries the surface and
  meanings; the back carries examples and detail.
- **card details** (`.card-details`) — the expandable detail region on the back.
- **card meta** (`.card-meta-*`) — the "Card data" modal, an audit view of
  provenance. Not part of the card face; say "card data modal" for it.

## on the card

- **lemma line** (`.card-lemma`) — the headword display.
- **meanings** (`.card-meanings-front`) — the list of senses shown. Each may
  carry a **context** (`.meaning-context`) and a **usage pill**
  (`.meaning-usage-pill`).
- **example block** — one example sentence with its parts: **sentence text**
  (`.example-sentence-text`), **word highlight** (`.example-word-highlight`),
  and, in artist mode, **song credit** and **vocalist credit**.
- **pills** — the small inline labels. **POS pills** (`.pos-pill-*`) mark
  part-of-speech state including `unassigned`; **selection** and **source pills**
  sit inline near the example.

Say "the pill on the meaning" or "the POS pill", not "the tag" -- tag means
something else in the data layer.

## modals

Each has an id ending `Modal`: settings, stats, help, find-word, estimation,
cognate-rules, song-set, vocabulary-import, card-tutorial, walkthrough,
about-project, auth. Name the modal, not "the popup".

## tutorial, walkthrough, About — three things, three audiences

These were one module (`about-example.js`) for a while and the words drifted
into each other. They are not interchangeable.

| word | for | what it is | opened from | code |
|---|---|---|---|---|
| **tutorial** | learners using the app | guided, one element at a time; starts from the setup screen; owns the flip; explains Lyrics mode on its own slide. Desktop and phone both first-class. | "?" button, first run, Settings → How to Study, the in-study prompt | `tutorial.js`, `#cardTutorialModal`, `.card-tutorial-*` |
| **walkthrough** | visitors — employers, anyone being shown the app | two screens (three on a phone), whole faces labelled at once, so a five-second look still lands. No setup, no instructions. | **only** About | `walkthrough.js`, `#walkthroughModal`, `.walkthrough-*` |
| **About** | visitors | what the app is and how it was built. Desktop-first, comfortable on a phone. **Links** the walkthrough; never contains or opens the tutorial. | landing page, `#/about` (legacy `?about=1` is rewritten on arrival), Settings | `about.md`, `#aboutProjectModal` |

Both the tutorial and the walkthrough draw the same **replica card**
(`card-replica.js`, `.card-replica`): real demo entries in the live card's own
markup. The replica belongs to neither.

A learner-facing string that says "walkthrough", or an About link that opens
the tutorial, is a bug.

Note **card actions popup** (`.card-actions-popup`) is a popup, not a modal --
it is anchored to the card rather than covering the screen.

## words that mean different things in the app and the data

| word | in the app | in the data |
|---|---|---|
| **tag** | a pill or label on screen | a Wiktionary sense tag (`reflexive`, `Brazil`) |
| **context** | the grey text under a meaning | the `context` field, derived per provider |
| **source** | the source pill crediting a sentence | ambiguous -- say provider, corpus or snapshot |
| **level** | a CEFR band in the level selector | not a data concept |

When asking for a change, saying which side you mean removes most of the
ambiguity: "the context line on the card" versus "the context field in the menu".
