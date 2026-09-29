# Decision 0028 — Words that must not be skipped (Merge Lemmas, Exclude Cognates)

Measured on the first 300 cards of es, pt, cs (v15-mend), fi (v12-wsd-r2), and
on fr and nl stage-02 menus (neither has a full release yet).

## Merge Lemmas (`app/js/vocab.js`, `lemma-merge-pure`)

A spelling keeps its own card if any of these holds:

1. **It names more than one headword** (fue → ser/ir). Unchanged.
2. **It is a contraction.** For SpanishDict this is a sense with POS
   `CONTRACTION` (al, del). For Wiktionary it is a sense glossed "contraction of
   X + Y", listed per language in `app/data/merge-exceptions/<lang>.json` by
   `scripts/build_merge_exceptions.py` (pt no, do, disso, pelo; fr au, aux).
3. **It shows an expression frozen on this exact form, and the form is not the
   lemma's own spelling.** *no sé* keeps sé and *muchas gracias* keeps muchas.
   *tener cuidado* on tener and *por favor* on favor do not: a construction
   headed by the lemma belongs on the merged card as a sense.

When the lemma's own spelling is a deck card, it hosts the merged card
(estar, not estaba).

Rejected:
- **An auxiliary-verb rule.** The local Wiktionary extracts carry no
  auxiliary category, and per-sense tags vary by language. Conjugation mode
  teaches forms.
- **Reading headwords from the full menu.** The cases it rescues (cs ty, fi
  missä, es sé) are WSD errors on the card itself, and they belong to a WSD fix.
- **Rank cutoffs and percentage thresholds.**

## Exclude Cognates (`app/js/cognates.js`, `cognate-score/v4`)

A card is set aside for a known language only if **every sense it shows is a
free cognate in that language**. The card's English translation is the pivot,
which is what makes this work for any pair. A sense is free for known language
L when all of these hold:

- it is not an expression;
- for some English word g in its translation, an L word **has that sense**. For
  English, the L word is g itself. For any other language, g is one of the L
  word's own live Wiktionary glosses;
- it is a **cognate**: CogNet pairs the L word with the sense's headword, where
  CogNet has the headword. Otherwise the shared gloss is the evidence, and for
  English g must also be a real English word;
- for a non-English L, **the L word's primary sense is one this card teaches**.
  This blocks false friends that share only a minor sense: Polish *czerstwy* is
  "stale" first and "fresh" far down, so Czech *čerstvý* stays. Likewise
  *dívka*/*dziwka*, *prachy*/*prochy*, *vysvětlit*/*wyświetlić*. English needs no
  such check, because the known word is the card's own gloss;
- its surface score (decision 0027) reaches L's cutoff.

The file is `surface → headword → English word → {language: score}`, with
`matches` naming the L word where it isn't g. It is built by
`fluency enrichment build-cognates --schema v4 --known en --known pl=<extract>`.
A new pair needs only a `config/cognates/<target>-<known>.json` and an
English-glossed extract.

The per-card verdicts the app uses before a Speech card's senses load, and the
merge keys, are trusted only for the release they were built from
(`built_from_release_id` / `release_id`). For any other release the app keeps
every card until the senses load.

This replaces the per-word best-of-lemmas score and the look-alike gloss gate
(which let bench match banco). No gender or false-friend list is used.

First-300 set-asides at the shipped cutoffs (en 0.75, or 0.80 for fr/nl; pl 0.80):

| | before | after |
|---|---|---|
| es | problema, idea, serio, familia | tres, idea, familia |
| pt | favor, nome, problema, parte, momento, caso, forma | nome, problema, carro, realmente |
| nl | 12, including over, even, heel, bang | vind, sorry, idee, zoon, probleem |
| fr | 12, including nous, plus, part, grand | famille |
| cs→en | problém, fakt | musí, fakt |
| cs→pl | 70 (per word; legacy scorer matched víc/wystarczająco, všechno/wszechrzecz) | 55: tak, ale, dobře, můj, musím, trochu, každý, … |

Known gap in cs→pl: it is conservative where Polish leads with a different
sense (*mluvit*/*mówić*, which is "say" first, stays in the deck).
