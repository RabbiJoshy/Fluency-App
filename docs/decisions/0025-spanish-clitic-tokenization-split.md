# Decision 0025 — Split Spanish attached clitics at tokenization (DRAFT)

**Status:** **Rejected in UNISON-2 (2026-10-08).** Splitting attached clitics at tokenization is rejected. Semantic reflexive slips (*irte* showing *ir*, *darte* showing *darse*) are solved directly in the unified WSD engine (`fluency.wsd`) via `ConstructionGate`, reflexive tag filtering, and candidate policy without altering surface card identity, invalidating learner progress, or requiring a full corpus re-harvest. Tokenization maintains `preserve_surface` per decision 0014 and Invariant 1.

## Proposal

Tokenize every *verified* enclitic surface as its host plus its pronouns:
`decírtelo` → `decir te lo`, `cógelo` → `coge lo`, `dele` → `dé le`,
`vayámonos` → `vayamos nos`. Frequencies, examples and menus merge into the host
surface. The pronouns count toward their own cards.

- **Verified** means `SpanishDictLemmaRule.enclitic_split`
  (`src/fluency/sense_menu/spanishdict_lemmas.py`): the stripped host is an exact
  form in SpanishDict's conjugation table, in the imperative, infinitive or
  gerund, of exactly one verb. Two candidate verbs (`vete`: *ir* | *ver*) → no
  split; the surface stays a card of its own.
- **Unconditional**, not "only when there is no menu" (proposal 0003 §8): if the
  split depended on menu coverage, card identity would move as more of
  SpanishDict was fetched, and learners' progress with it.
- **Into the bare host surface, not the lemma.** The host keeps the table's
  spelling (`dé`, never the preposition `de`). Folding `coge` into `coger` is
  the separate lemma merge Fast Track already offers.

## Outcome in UNISON-2
 
Splitting attached clitics at tokenization was rejected during UNISON-2.
The underlying motivation was addressing reflexive slips (*irte* picking *ir*
instead of *irse*, *darte* picking *darse* instead of *dar*). In UNISON-2,
these slips were eliminated directly in the unified WSD engine (`fluency.wsd`)
via the `ConstructionGate`, reflexive tag filtering, and candidate policy
adjustments without touching stage 01 tokenization or card identity.

Preserving existing tokenization preserves Invariant 1 (preserving learners'
study progress without migrating 1,167 cards) and avoids a costly SCAR-level
corpus re-harvest. Attached enclitics remain cards with menus provided by the
resolver's enclitic host rule.

## For and against

- **For:** one card per verb form instead of one per pronoun bundle; the ~70
  bundles that had no SpanishDict page stop existing as cards; examples and
  frequency concentrate where the learner can use them; French already does
  this (decision 0005), and lyrics routing's `clitic_merge` showed it works in
  production.
- **Against:** a learner sees `decírtelo` in a sentence but studies `decir`,
  `te` and `lo`; the bundle is a real unit of spoken Spanish. Progress on
  every split card must migrate (Invariant 1: preserve the substance, label
  both). The deck's rank-10,000 boundary moves.

## Numbers

Measured by `python scripts/mend_local.py --step clitics` against the 10k
inventory of run `20260914T223348Z-c35194bc` (report
`docs/mend/clitics-20260923T231844Z.md` (raw dump removed 2026-10-04; in git history before that date), every split listed in the `.json`):

| Measure | Value |
|---|---|
| verified enclitic surfaces in the 10k: cards removed, progress to migrate | **1,167** |
| kept whole because the surface is a word in its own right (its own SpanishDict entry is a non-verb, or it is itself a conjugation-table form: *dios*, *pelo*, *regalo*, *verme*) | 35 |
| hosts they merge into | **532** (397 already cards, 135 new) |
| slots freed for surfaces beyond rank 10,000 | **1,032** (first in: *continuemos*, *pelirroja*, *erección*, *luchas*, *odie*) |
| largest host rank gains | *deshacer* 9,853 → 1,472; *acostar* 9,597 → 1,404; *aleja* 8,455 → 1,209; *acompañar* 9,594 → 2,081 |

About one card in nine is an enclitic bundle, and most hosts are infinitives
(`sentarse`, `sentarme`, `sentarte` → *sentar*) that jump thousands of places
once their bundles count toward them. The pronouns' own cards (*me*, *te*, *se*,
*lo*) are already in the top 100 and barely move.

Two things to settle before adopting, both visible in the report:
- infinitive + *se* merges into the bare infinitive (*sentarse* → *sentar*):
  the pronominal verb loses its own card. The resolver still offers both
  menus, so meaning is not lost, but the card is.
- some verified forms are also lexicalised expressions (*date prisa*,
  *detente*); the guard keeps the ones the conjugation table lists whole.

## If adopted

1. `config/languages/es/tokenization.json`: attached clitics become
   `split_host_and_pronouns`, verified by the rule above.
2. A progress migration mapping each removed card to its host card, recorded
   as a labelled migration (Invariant 1).
3. The resolver's enclitic host rule stays: it catches whatever the split
   leaves (abstentions, lyrics forms outside the table).
