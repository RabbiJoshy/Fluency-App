# Decision 0025 — Split Spanish attached clitics at tokenization (DRAFT)

**Status:** Draft by MEND, 2026-09-23. **Proposed, not decided.** For the next full
Spanish rebuild; Joshua decides. It would reverse part of decision 0014 and
`config/languages/es/tokenization.json` (`preserve_surface`,
`may_replace_surface_card: false`), so if adopted it says which invariant it
touches and how (Invariant 1).

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

## Why now is not the time

MEND fixed the empty clitic cards without touching identity: the resolver's
enclitic host rule gives each one its verb's menu. The split changes stage 01
(tokenization → frequencies → ranks), so it needs a re-harvest (a SCAR-level
decision), full WSD, and a progress migration. It belongs to the next full
Spanish rebuild, taken on its merits.

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
inventory of run `20260914T223348Z-c35194bc`; the report lists every split,
every host and every surface that would enter. **Pending the local run** —
the table below is filled from that report:

| Measure | Value |
|---|---|
| verified enclitic surfaces in the 10k (cards removed, progress to migrate) | _pending_ |
| hosts they merge into (already cards / new) | _pending_ |
| slots freed for surfaces beyond rank 10,000 | _pending_ |
| largest host rank gains | _pending_ |

## If adopted

1. `config/languages/es/tokenization.json`: attached clitics become
   `split_host_and_pronouns`, verified by the rule above.
2. A progress migration mapping each removed card to its host card, recorded
   as a labelled migration (Invariant 1).
3. The resolver's enclitic host rule stays: it catches whatever the split
   leaves (abstentions, lyrics forms outside the table).
