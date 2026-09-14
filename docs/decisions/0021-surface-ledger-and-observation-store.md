# Decision 0021 — The surface ledger, and the observation store beneath it

## Decision

Split what was one pipeline stage into three, and make the boundary between them
a *table* rather than a function call:

1. **Harvest** applies only cheap, irreversible gates and writes every sentence
   it keeps.
2. **Cleaning** narrows that set and tags what it rejected, without deleting it.
3. **WSD** reads a filtered view of the cleaning output and does nothing but
   disambiguate.

The artifact that carries a language across those boundaries is the **surface
ledger**: `<workspace>/raw/surfaces/<language>/ledger.json`, contract
`surface-ledger/v1`. One row per surface, every column provenanced.

A language is ready for WSD when its ledger is complete. That is the definition;
there is no second checklist.

## Why a table and not a filter chain

The previous shape ran the gates inline and kept only survivors. That made every
question about a missing word unanswerable — the evidence had been discarded by
the code that acted on it. Three separate investigations ended in "re-run the
harvest with logging", which costs the harvest.

Keeping the rejects with a reason attached costs a few megabytes per language
and answers the question from disk. It also makes the gates auditable *as
policy*: `audit_surfaces_html.py` renders the whole ledger as a filterable table,
and a bad gate is visible as a column rather than discoverable as an absence.

## Events are facts; verdicts are policy

`src/fluency/surfaces/events.py` is an append-only observation log, one JSONL per
language, deduplicated by content hash. An event says *what was observed* —
`accent_stripped_duplicate`, `dictionary_absent`, `lemma_resolved` — and never
what to do about it.

`src/fluency/surfaces/policy.py` folds the events for a surface into
`keep` / `review` / `exclude` **at read time**. Changing a judgement is editing
the policy table and re-materialising; it never rewrites history.

This separation was not theoretical. Every one of these was a policy error
corrected without re-observing anything:

| Observation | First policy | Corrected to | Why |
|---|---|---|---|
| `english_wordlist` | exclude | keep | web2 contains `no`, `la`, `es`, `para`, `dinero` — it convicted 30 of the commonest Spanish words |
| `accent_stripped_duplicate` | exclude | keep | `que`/`qué`, `el`/`él`, `ne`/`ně` are ordinary vocabulary, not typos |
| `lemma_is_headword` | veto | not a veto | it was conflated with `lemma_resolved` and pulled back `lady`, `house`, `when` |

Had the gates run inline, each of those would have been a re-harvest.

### Durable and run-scoped evidence

Events are partitioned. `DURABLE` observations are facts about the word
(`dictionary_absent`, `abbreviation_form`, an adjudication); `RUN_SCOPED` ones
are facts about one corpus pass (`capitalised_in_corpus`, `low_harvest_yield`).

Measured on the current three languages, **94–99% of events are durable**, which
is what makes a re-harvest cheap: it refills freed ranks, it does not rebuild
knowledge.

## Lemma authority is whoever supplies the menus

A lemma's job is to find a sense menu. A lemma from any other source may name a
headword the menu provider has never heard of — which reads as resolution and
resolves nothing.

So the **primary lemma column carries only the menu provider's headword**:

| Language | Authority | Fallbacks, in order |
|---|---|---|
| `es` | SpanishDict | surface cache → refetch → reverse conjugation → manual |
| `pt` | en.Wiktionary | closed-class headword → `form-of` → is-headword |
| `cs` | ČNK *word at a glance* | then the Wiktionary chain |

Every lemma carries `lemma_provenance` as a human-readable label — `spanishdict
headword`, `supplied by reverse conjugation`, `CNK word at a glance`, `manual`.
Non-authority lemmas are kept in `lemma_alternates` rather than discarded: they
are correct morphology and the cognate work wants them. They never lead.

**A single correct lemma is not derivable.** Four candidate orderings were tried;
each fixed one class and broke another (`es`→`ser` against `no`→`número`). The
ledger therefore ships an *ordered list*, authority first, and lets the consumer
decide how far down to read.

## Reverse conjugation leads only where the surface is known to be a verb

The authority order for Spanish is surface cache → refetch → reverse conjugation
→ clitic stripping. SpanishDict leads; reverse conjugation is a fallback. That
ordering is not arbitrary and was measured before being fixed.

Of 4,133 Spanish surfaces whose primary lemma is the surface itself, only 23
have a competing reverse-conjugation claim — and SpanishDict is right in all 23:

    chica -> chicar     coche -> cochar     para    -> par
    incluso -> incluir  minuto -> minutar   jamás   -> jamar

`chica` is a girl, not a form of *chicar*. Reverse conjugation over-generates:
it will invent an infinitive for almost any noun ending in `-a` or `-o`. Letting
it lead generally would corrupt four thousand cards to fix none.

`scripts/resolve_clitic_lemmas.py` inverts that order, and only there. A clitic
attaches only to a verb, so the stripped base is known *a priori* to be a verb
form, and in that narrow case the usual hazard flips: the surface cache lists
conjugated forms under their own spelling — the self-headword inclusion that
won ~1,250 lemmas and was right to add — so consulting it first answered
`mírelo -> mire` and `llévenselo -> lleven`, conjugations presented as lemmas.

**The rule is conditional, not a ranking.** Reverse conjugation leads where the
surface is already known to be a verb form; SpanishDict leads everywhere else.

## What SpanishDict does with a word it does not have

The 82 clitic-attached surfaces did not come back empty. Measured over the
refetch: 68 fuzzy-matched a different word, 10 answered in English, 0 returned
nothing. SpanishDict substitutes the nearest spelling — roughly one character's
edit distance — and lands on a **real but unrelated verb**, which is the worst
kind of wrong because it is plausible:

| asked | answered about | would have given | correct |
|---|---|---|---|
| `llévatelo` | `llégatelo` | llegar | llevar |
| `mírelo` | `mínelo` | minar | mirar |
| `pásamelo` | `páramelo` | parar / parir | pasar |
| `haberles` | `hacerles` | hacer | haber |
| `verles` | `verdes` | verde | ver |

That is 25 wrong lemmas the `spelling_substitution` gate prevented in one class
of one language. The gate is not tidiness; it is the only thing between
`llévatelo` and *llegar*.

## Fuzzy matches are never evidence

SpanishDict answers a miss with a different word: *"Showing results for cómelo.
Search instead for cógelo."* An earlier stem heuristic tried to detect this and
would have wrongly rejected `fui`→`ser`.

The site states it itself, in `spelling_suggestion_was_requested`. The fetcher
records the flag and the merge withholds those rows from the menu. The rule
generalises: **prefer a provider's own declaration of uncertainty over inferring
it.**

## Alignment measures literalness, not correctness

LaBSE cosine was adopted as a translation-quality gate and then floored low, at
`0.30` by default, because a floor tuned for quality strips idiom:
`O fim está se aproximando.` → *The sands are running out.* is a correct
translation scoring `0.353`.

Per-language floors live in `config/harvest/languages/*.json`. Czech's `0.45` is
a **guess, not a measured sweep** — recorded here so it is not mistaken for one.

Heuristics rejected after measurement, so they are not re-proposed:

- **digit mismatch** — fired 17× and every hit was English spelling a number
- **run-together words** — flagged `extraordinariamente`, missed `Ababythatwould`
- **Czech diacritic stripping** — fires *more* on human-aligned Tatoeba (2.34%)
  than on subtitles (1.84%), so it measures the wrong thing

The method that made those calls is worth keeping: **Tatoeba as control.** A
human-aligned corpus gives any heuristic a free false-positive rate.

## The cap must take the best N, not an arbitrary N

Eligible sentence ids are ordered as the WSD cap will consume them, so the head
of that list is what gets scored and eventually what a learner sees. They were
ordered by hardness alone, easiest first.

That ordering put this first on `que`, rank 1, the commonest surface in Spanish:

    ¿el Que le qué?   ->   I'm sucking his what?

A misaligned subtitle pair, scoring **0.695** — comfortably above the 0.45
floor, because both sides are four-word questions and LaBSE reads the shape.
This is the literalness/correctness confusion in its second direction: the score
fails to convict a bad pair when both sides are short, since there is little
content and the embedding is dominated by form. Short sentences are where the
gate is blindest, and "easiest first" selects for short.

**41.6% of Spanish cards had a sentence scoring under 0.70 in their top ten**,
on data where every eligible sentence had already been scored. The score was
computed and then not used to order.

Alignment now leads, **banded at 0.05 rather than raw**: sorting on a continuous
score would let a 0.001 difference override easiness entirely, whereas within a
band the sentences are equally well aligned and the original intent — prefer
what a classifier finds easy — still decides.

| cards with a sub-0.70 sentence in their top ten | before | after |
|---|---:|---:|
| `es` | 41.6% | 0.6% |
| `pt` | — | 0.0% |
| `cs` | — | 0.1% |

## Consequences

- Downstream code reads `fluency.surfaces.ledger.ledger_path()`, never a literal
  filename. The resolver falls back to the pre-rename `surfaces.json` so an old
  workspace still reads; that is a migration affordance, not a second format.
- An excluded surface **keeps its row and loses its sentence ids**. It stays
  auditable and cannot be selected from.
- Observers currently run as a backfill script rather than inside the stages.
  `low_harvest_yield` is defined but never emitted. Both are open.
