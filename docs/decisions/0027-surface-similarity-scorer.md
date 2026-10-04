# Decision 0027 — Surface similarity scorer

**Status: Settled (2026-10-03).** Replaced provisional `edit-distance/v1` with
`learner-align/v1`, resolving the missing cognates (*capitán/captain*, *número/number*)
without introducing false positives.


## Problem

Cognate mode asks two questions of a (deck word, English word) pair: *are they
cognates?* (CogNet, or the English word being the translation) and *does it
look the same on the page?* The second is the surface score, and its cutoff is
the one knob for how much cognate mode skips.

The original scorer (`legacy-max4/v1`) took the best of four readings, which
were Levenshtein and Jaro–Winkler, each on raw spelling and on rewritten
spelling. Measured on the English pairs:

| pair | Levenshtein | legacy best-of-four | reading |
|---|---|---|---|
| toho / the | 0.50 | 0.75 | not transparent |
| este / east | 0.50 | 0.85 | not transparent |
| musím / must | 0.60 | 0.85 | not transparent |
| tres / three | 0.60 | 0.88 | borderline |
| sensible / sensitive | 0.67 | 0.88 | partial false friend |
| comunicar / communicate | 0.73 | 0.91 | transparent (the rewrite *lowered* it to 0.55) |

- The maximum of several readings is always the most lenient one, so the cutoff
  means something different at every word length.
- Jaro–Winkler forgives any ending and rewards any shared opening, so it is far
  too generous on short words.
- es/pt rewrote `c→k` on the target side only, so the rewrite hurt real cognates.
  The maximum hid this.
- It was slow: pure Python, four calculations per pair, no caching.

## Decision

- Scorers are **pluggable**. One module each lives in
  `src/fluency/features/surface_scorers/`, declaring `SCORER_ID`, and they are
  discovered by listing the package. Every `config/cognates/<pair>.json` must
  name its `surface_scorer`, and a file without one is refused.
- `legacy-max4/v1` is the old code, moved as it was. No pair uses it now. It
  stays available for comparison. Czech–Polish moved off it once measured: on
  the cs v15 deck it matched nonsense (víc/wystarczająco, myslíš/iszli,
  všechno/wszechrzecz) that edit distance does not.
- `edit-distance/v1` is the stop-gap for every pair, English and Czech–Polish alike. It is one
  normalised Levenshtein, computed after these steps:
  - the pair's rewrite rules, applied to **both** words;
  - accents stripped;
  - the target's regular endings mapped to English (`ending_rules`: idad→ity,
    ción→tion, oso→ous, mente→ly);
  - doubled letters collapsed.

  The length guard is part of the score, and results are cached.
- The scorer id is recorded in every cognate file (`surface_scorer`).
- `learner-align/v1` (2026-10-03) replaces `edit-distance/v1`:
  - Natural consonant class discounts (labials, dentals, velars/sibilants, nasals, liquids) at 0.35 cost;
  - Length-gated vowel shift tolerance: discounted for words $\ge 5$, strictly penalized (1.0) on words $\le 4$ to block short false lookalikes (*este/east*, *toho/the*);
  - Damerau adjacent swaps and 3-character rotation/metathesis tolerance (*capitán/captain* jumps from 0.71 to 0.93);
  - Epenthesis tolerance for excrescent $b/p$ next to $m$ (*número/number* jumps from 0.67 to 0.78);
  - Measured across Spanish, Portuguese, Czech–Polish, and Czech–English on the first 2,000 cards: zero regressions, zero false positives admitted, and 16 (es), 30 (pt), 54 (cs-pl) obvious cognates recovered.


## What a replacement has to beat

`scripts/eval_surface_scorer.py --a edit-distance/v1 --b <candidate>` lists,
per language, the first-2000 words each scorer would skip that the other would
not. A candidate replaces the stop-gap only when those lists read better.

Open options, none tried here:
- **Learned correspondences.** `features/correspondences.py` already learns
  letter correspondences unsupervised. Trained on CogNet's English pairs it
  should find `-dad↔-ty` and the like without a hand list. It can only raise
  scores, so every cutoff would need recalibrating.
- **Pronunciation.** `features/phonetics.py` (panphon `dolgo_prime`) is built and
  switched off. It measures hearing, not reading.
- **Stemming.** Compare stems and ignore inflection. This needs a per-language
  ending list.
