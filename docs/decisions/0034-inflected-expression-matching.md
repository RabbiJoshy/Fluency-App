# Decision 0034 — Verb-led expressions match in any inflection

26 October 2026. Follows decision 0033: every form of a word shares its card,
so an expression belongs to the word, not to the infinitive's spelling.

## Problem

The expression inventory attaches each entry to dictionary words (`dar certo`
on "dar" and "certo"), and the matcher looked entries up by the card's exact
surface. An inflected form never found its expressions, and the only inflecting
path (`flexibility` / `verbal_idiom`, a hand-written stem list, first word only)
was switched on by no entry in the current pt or es inventories. On the live
decks all 89 Portuguese verb-led expressions sat on the infinitive's card only
(Spanish 129 of 136). *La echo de menos cada día* was published as echar "to
have"; *Me di cuenta de que…* as dar "to come up with".

## Rule

`ExpressionInflector` (`src/fluency/wsd/multiword.py`) reads the Wiktionary verb
paradigm the reflexive tagger already builds (`fluency.reflexive.paradigms`,
`<workspace>/cache/reflexives/forms-<lang>.json`).

- **Inflecting** when the first word is a verb's dictionary form, optionally
  reflexive (`darse cuenta`, `dar-se conta`). The verb matches any form in its
  paradigm. Pronouns may be attached (*dei-me*, *dándome*, *darte*) or up to two
  may precede it (*não me dei conta*, *me lo di*); a reflexive expression needs
  a reflexive pronoun in one of those places, and only that pronoun joins the
  highlighted span.
- **Gaps**: up to two words between the verb and the rest (*echamos mucho de
  menos*, *tem nada a ver*), never across punctuation and never skipping a
  preposition. A rest that is a single preposition or short word (*ficar com*,
  *dar para*) allows no gap, so *ficou muito feliz com* is not *ficar com*.
- **Frozen** otherwise: *não é*, *quer dizer*, *será que*, *no sé* are already
  inflected forms and match exactly, as before.
- **Attach by word**: a form also looks up the expressions attached to its
  dictionary word (*deu* finds `dar certo`).

Expressions still compete with dictionary senses; nothing is vetoed, so
compositional entries (*ser de*, *ir de*) stay the WSD's to reject, as decided
in the module docstring. Inner agreement (*cuida da tua vida*) is not handled.

## Provenance

`fluency.speech.wsd_execute --expression-paradigms <forms-<lang>.json>` turns it
on; without it behaviour is unchanged. Each inflected match records the
paradigm's content id in its `multiword` evidence (`paradigm_content_id`).

## Measured on the live decks (published sentences only)

| Expression | Matched before | After | Cards |
|---|---|---|---|
| ficar com | 8 | 65 | 27 |
| tomar conta | 17 | 70 | 18 |
| echar de menos | 4 | 113 | 19 |
| darse cuenta | 0 | 103 | 24 |

Every verb-led expression: Portuguese 1,608 sentences on 503 cards gain one,
Spanish 2,233 on 557 cards; no sentence loses one. Those sentences need a WSD
re-run with the expression on their menus before a deck shows them.

Inventory frequencies (`corpus_freq`) were counted on exact strings and gate
indexing, so *dar-se conta* (pt, frequency 0) is still not offered. Recounting
with this matcher is a new inventory snapshot.
