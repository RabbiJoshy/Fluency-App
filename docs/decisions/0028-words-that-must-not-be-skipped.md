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

## Exclude Cognates (`app/js/cognates.js`, `cognate-score/v3`)

A card is set aside only if **every sense it shows is a free cognate**. A sense
is free when all three hold:
- it is not an expression;
- one of the English words in its translation is a cognate of the sense's
  headword. With CogNet (es, pt, fr, nl, cs) that means CogNet pairs them.
  Without CogNet coverage (fi, or a headword CogNet lacks), the English word
  only has to be the translation itself;
- that word's surface score (decision 0027) reaches the language's cutoff.

The file is `surface → headword → English word → score`, built by
`fluency enrichment build-cognates --schema v3`. Czech's Polish scores ride along
unchanged in `carried`.

This replaces the per-word best-of-lemmas score and the look-alike gloss gate
(bench matched banco). No gender or false-friend list is used: the every-sense
test does that job.

Top-300 set-asides at the shipped cutoffs:

| | before | after |
|---|---|---|
| es | problema, idea, serio, familia | tres, idea, familia |
| pt | favor, nome, problema, parte, momento, caso, forma | nome, problema, carro, realmente |
| nl | 12 incl. over, even, heel, bang | vind, sorry, idee, zoon, probleem |
| fr | 12 incl. nous, plus, part, grand | famille |
