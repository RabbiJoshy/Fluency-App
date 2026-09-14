# Spanish/Portuguese WSD v8: implemented experiment

v8 is an additive experiment over the v7 closed-menu ranker. It does not use a
translator and does not replace v7: when a speech sentence already supplies an
English translation, a pinned local SimAlign model may correct the selected
leaf; with no translation or no unique strict alignment, v7's answer is kept.

## Repairs made before adding the English signal

- Spanish menu lookup now uses the existing reverse-conjugation table even when
  the surface was never fetched directly. Rebuilding the old 2,000-card
  inventory against the same pinned snapshot reduces `no_menu` from 480 to 314:
  166 cards recovered and zero previously ready cards lost.
- SpanishDict and Wiktionary now emit the same typed `grammar`, `companion`, and
  `functional` feature families. Plain semantic paraphrases are no longer
  mislabeled as domains.
- The candidate policy records explicit companion and grammar contradictions,
  but does not use the new leaf gates to change answers. A real-deck manual
  spot-check of their 15 changed cases found about 5 better, 9 worse and 1
  lateral, so activation was rejected. Portuguese records the same normalized
  evidence but not the Spanish-only `se` heuristic; common contractions are
  expanded locally. The older Spanish companion leaf-repair behavior remains.
- Wiktionary form-of morphology is preserved as normalized leaf evidence rather
  than being discarded with non-semantic form-of senses.

## Supplied-English specialist

Profiles `es-v8-english-1` and `pt-v8-english-1` enable a local-only,
revision-pinned multilingual word aligner. The corrector:

1. marks the exact source occurrence;
2. finds its strictly aligned English token or phrase;
3. intersects that text with literal English cues derived from the finite menu;
4. changes the result only when exactly one leaf owns the cue.

It never generates a translation, calls a translation service, invents a sense,
or changes an answer shared by two indistinguishable leaves. Its evidence stores
the cue, alignment method, and token pairs.

## Measurements and limits

- On the existing 199-item answerable Spanish hard panel, the strict alignment
  specialist fired on 40 items and was right on 38 (95% precision), producing
  11 fixes and 0 breaks against the old first-prior fallback. This is evidence
  for a high-precision specialist, not a combined v8 accuracy claim.
- The cached panel had only 18 items with every current v7 vector available. On
  that small, function-word-heavy slice, v7 and v8 were both 14/18 and alignment
  fired zero times. A full combined rerun needs a complete cached panel.
- Real-deck execution shape was checked on both providers: strict alignment
  fired on 13/20 cue-bearing Spanish occurrences and 14/20 Portuguese ones,
  always producing valid menu references. Portuguese meaning quality is not
  claimed without labels.
- The specialist cannot help when English is absent, alignment is uncertain, or
  sibling leaves share the same English wording. Pro-drop and loose paraphrases
  are common abstention cases.
- A direct 20-line real-deck spot-check using saved v7 scores changed 10 answers;
  all 10 changes were manually judged correct. It also abstained on four
  deliberately tempting wrong cues, but missed clear fixes for `quiere decir`,
  `hablar`, and `hecho`. This sample was deliberately opportunity-rich and is a
  behavior check, not a deck-wide accuracy estimate.

Frame evidence remains asymmetric: SpanishDict has only a handful of explicit
frames, while Portuguese Wiktionary has hundreds of parenthetical construction
notes. Those notes are now preserved in the normalized `construction` family,
but there is no active frame gate until a depth-sufficient, provider-matched
benchmark tests it. The `0.02` menu prior is retained pending a frequency-sampled
ablation; this change does not claim that prior is safe.

No artist dataset or release was modified by this experiment.
