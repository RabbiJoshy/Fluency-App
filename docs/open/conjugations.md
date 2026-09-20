# Conjugate + English inflection

Writeup for the conjugations row in `OPEN.md`. Sources and adapters: `docs/migration/0010-conjugation-sources.md`.

This is not WSD. Card identity stays the observed surface. Join key is the sense-menu **headword**. Missing tables stay missing.

## What shipped

- Optional `conjugation-layer/v1` → `app/conjugations.json` on `*-conj` releases.
- Live Conjugate button where `conjugationsPath` is set: Spanish, Portuguese, Czech (v12), French (v4 decks / v3 tables). Dutch stays `null`.
- One English inflector in `app/js/reverse-cues.js`. The table is the morphology oracle (look up the surface, inflect the gloss). No `lemminflect`, no `conjugatedEnglishPath`.
- Inflect and highlight the **observed** surface, including merged-lemma study (`hablo` not `hablar`).
- 3sg English is **he/she**, not *they* (collides with 3pl) and not *he/she/it*.
- Dummy **it** only when the **selected** sense is a clock or weather copula (`used to express time`, `point in time` / `denote time`, `said of time`, `weather` / `of the weather` / `weather phenomenon`). 3sg only.
- Live overlay: GitHub Pages `0499eef`. App commit on `main`: `614cde1` (may still be local).

## Decisions to keep

- Do not walk tenses by hand. Do not restore verbecc ML or MorfFlex.
- Do not treat impersonal / “to exist” / “to be possible” / *falloir* as dummy *it*.
- First ~200 ranks were the quality bar for English glosses; later ranks matter less.
- Spanish `es` (rank 8) has no time pill in the v12 menu. Clock senses live on *era* / *fue* / *será*.
- `hay` / `há` already gloss as there-is / there-be; leave them.

## Come back to

- Not signed off. Joshua was not happy with the English side yet.
- Dummy *it* first-200 3sg cards: es *fue, era, hace, será*; pt *é, foi, era, faz*; fr *est, fait, était, sera*.
- Portuguese *chega* / *chegou* / *chegará* can false-hit “point in time” on an arrive-sense (after rank 500).
- Imperfect of English *be* still renders *was being* (clock wants *it was*).
- French `SENSE_CYCLE` inflection / headword is still weak.
- SpanishDict *hacer* time gloss is already finite (“it has been”); the inflector skips it.

## Reopen

Add **DRAWER** to `CHAT_ROADMAP.md` only while a chat is actually working. Until then it lives only in `OPEN.md`.

```
This chat is DRAWER. Read CHAT_ROADMAP.md through SCAR, then OPEN.md and docs/open/conjugations.md. Resume conjugation tables and table-lookup English inflection. Do not harvest. Do not WSD. Do not start MILL.
```
