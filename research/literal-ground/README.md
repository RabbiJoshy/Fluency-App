# LITERAL-GROUND (2026-10-11)

Two WSD safeguards for es/pt speech, shipped as profiles `es-v25-1` / `pt-v25-1`
and candidate decks `pt-speech-v25-literal-ground-r4`, `es-speech-v25-literal-ground-r6`.
Only the preposition cards were re-run (pt de/do/da/dos/das/em/no/na/nos/nas,
es de/del); every other card is byte-identical to pt r3 / es r5. $0: WSD ran
`--offline-only` from the exact-text cache.

## What changed

**GROUND** (`src/fluency/wsd/ground.py`, `config/wsd/closed-class/<lang>.json`)

- A declared primary leaf per preposition (pt *de* "of (in relation to)", *em*
  "in; at"; es *de* "of", *del* "of the"). Declared, not menu order: SpanishDict
  lists *de* "from" first and the Wiktionary menu is sorted by sense id.
- Margin floor 0.025: a rival must beat the primary by that much.
- Governed bypass, *de* only: infinitive complement (*gostaria de fazer*), verb
  object (*precisa de dinheiro*, *lembrar de mim*), noun complement (*bolso da
  jaqueta*). Parsed with the pinned spaCy parser, closed-class occurrences only.
- A grounded leaf commits as a declared default (pt's rank-agreement would
  otherwise abstain on it).

**LITERAL** (`ExactTextGlossScorer`, `gloss.overlap_specificity`)

- The live English mechanism is the translation-overlap bonus, not the aligner
  (`LiteralGlossAlignmentCorrector` runs only in the old `*-v8-english-1`
  profiles). The bonus gave "except" and "except for" the same +0.04 on
  "Except for your wallet". Now a cue inside a longer cue that a sibling leaf
  of the same entry matched earns nothing. Same entry only: *hablar con ella* /
  "talk to her" must not hand the bonus to *hablarse* "to talk to".

## Measured

`labels.jsonl`: all 124 sample rows v25 changed, hand-judged (`score.py`).

| track | lang | rows | v25 right | v24 right | both ok | both wrong |
|---|---|---|---|---|---|---|
| GROUND | pt | 84 | 56 | 5 | 22 | 1 |
| GROUND | es | 26 | 10 | 2 | 13 | 1 |
| LITERAL | pt | 7 | 7 | 0 | 0 | 0 |
| LITERAL | es | 7 | 5 | 2 | 0 | 0 |

Rows whose card English changes: 94 — 78 better, 7 worse. Worse: *caiu da
ponte* (from→of, verb-object misparse), *no ônibus* (on→in; at), *em braile*,
*do que / acerca do* (of; about → of, same card text), es *amiga de Canadá*,
*vientos del sudoeste*, and two *parece* rows (SpanishDict files "looks like"
under physical similarity; English "looks like [clause]" means "seems").

pt *és* (TAGLINE regression) unchanged: 16 / 10 / 3 / 1.

## Tried and dropped (measured on the same sample)

- Primary for **por**, **para**, es **a / al / en**, pt **a**: overwrote real
  uses (personal *a*, *en junio*, *mudei para Boston*). Listed under
  `not_guarded` in the config files.
- Ignoring function-word cues ("from", "on", "the") in the overlap bonus: lost
  *é de Boston* "from" and *mosca no teto* "on"; turned *a* article rows into
  abstentions.
- A WSD-side minor-sense fold: the app already moves a sense under 10% of a
  card to Rarer uses (`MAIN_CARD_MIN_SHARE`, `app/js/vocab.js`), keeping the
  sentence's own sense. Folding in WSD changed meanings (*por semana* "per" → "for").

## Not done

- LITERAL is not rolled out deck-wide: ~2,700 es and ~1,500 pt cards have nested
  English variants. A full offline WSD re-run is $0 but was out of this brief.
- Seven pt occurrences whose multiword gloss has no cached vector kept their r3
  rows (`--offline-skip-missing`; listed in the splice report).
- pt *de* and es *del* lost a few one-example phrase rows: the old rows came from
  a run that evaluated 37 sentences; the current cap is 30.
