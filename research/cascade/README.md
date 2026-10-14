# CASCADE-WSD: findings and the Turbo goal (closed 2026-10-13)

Pilot: Dutch, English Wiktionary menus, run `runs/nl/speech/20261012T175838Z-76d34ee3`.
Benchmark detail: `nl-benchmark/README.md`. Labels are Claude's, not a native speaker's.

## What we learned

Accuracy on 377 random Dutch content-word sentences (±4 points at this size):

| approach | right | LLM share |
|---|---|---|
| DeepSeek V4.1 Flash on every sentence (batched, thinking off) | 96% | 100% |
| Cascade: Qwen3-Embedding-4B + e5-small, DeepSeek where they disagree | ~94% | ~30–34% |
| Gemini embedding alone | 85–88% | 0 |
| Qwen3-Embedding-8B / 4B alone (marked word + English) | 86 / 85% | 0 |
| Qwen3-Reranker-0.6B alone (reads sentence and gloss together; slower) | 83% | 0 |
| Qwen3-Embedding-0.6B alone (marked word + English) — the Turbo pick | 79% | 0 |
| e5-small alone (browser-sized) | 78% | 0 |
| first sense on the menu | 49% | 0 |

1. Embeddings add no accuracy over the LLM; they only save LLM calls.
2. Two embeddings that disagree are a better escalation signal than one model's margin,
   but catching most errors needs 25–35% of sentences escalated.
3. Per-word easiness measured offline predicts well (AUROC 0.74–0.78); menu shape alone
   does not (0.60–0.71). Words where the cheap model agreed 10/10 with DeepSeek are
   22–31% of polysemous words and are 95–98% right with the cheap model alone.
4. On the hard words (op, aan, er, te, zijn, dat), embeddings get 35–62% and DeepSeek 75%.
   These are grammar words, so we label them with rules instead (below).
5. Cost is negligible. Qwen on DeepInfra is $0.01–0.02 per million tokens. DeepSeek is
   about $0.03 per 1,000 sentences when batched by word. The full Dutch deck (38,520
   sentences: 66% the two embeddings agreed, 34% went to DeepSeek) cost cents.

## What shipped (production 2026-10-13: `a1cbe2d7`, compact display `469908f6`)

- Dutch prototype deck `nl-cascade-proto-2`, built with the cascade (`nl-proto/`).
- Grammar-word rule labellers (`trouble-words/labeller_{nl,es,pt,cs}.py`). These use a
  parser plus Wiktionary phrases, verb frames and pronominal verbs, and cover pronouns,
  determiners, prepositions, articles and particles. A card shows its grammar-word
  presentation when at least 60% of its sentences are labelled.

  | | Dutch | Spanish | Portuguese | Czech |
  |---|---|---|---|---|
  | Cards | 150 | 179 | 198 | 241 |
  | Spot check (100 random) | 98 | ~94 | 96 | ~95 |

  **French has no labeller yet.**
- The es/pt/cs grammar-word labels were added to the live decks without any other change
  (`fw-overlay/`; verified identical apart from the labels).

Come back to (Josh, 2026-10-13): Spanish grammar-word phrases, pronominal verbs and verb
patterns come from English Wiktionary, while Spanish card senses come from SpanishDict, so one
card mixes two dictionaries. This was inherited from the Dutch design, not compared. Check
whether our SpanishDict data has phrase entries before deciding; Wiktionary is acceptable meanwhile.

Left open: the role names in `app/js/function-word-card.js` are a draft waiting for Josh's
approval; the word route (`#/xx/w/…`) does not show the grammar-word block yet.

## The Turbo goal (decided by Josh 2026-10-13)

Turbo builds a deck from a user's upload of up to 100–200 songs. Cheap and fast per upload
matters more than the last few accuracy points; Josh expects embeddings, the algorithm and
LLMs to keep improving. So:

1. **Send as few sentences to WSD as possible. This is the main lever.**
   - Only surfaces with a menu in the ~10k list get WSD. A clitic form joins its base
     surface and uses that surface's menu (*decírtelo* → *decirte*).
   - Everything else gets a Wiktionary menu and no WSD.
   - The ceiling is about 15,000 surfaces per language.
   - Rules handle grammar words, so they need no model.
   - Words with one sense, or one sense for the parsed part of speech, skip WSD.
   - The number of examples per card follows the word's number of senses and its
     frequency rank, and rare words taper off.
   - Remove repeated lines (choruses) and cache songs other users have already uploaded.
2. **One embedding: Qwen3-Embedding-0.6B**, behind a setting so a better model can replace
   it with no rewrite. Menu glosses are embedded in advance, so only the new sentences are
   embedded during an upload. There is no second embedding in Turbo; offline decks may
   keep two (one local, one cheap online).
3. **The LLM handles only the hardest few percent, chosen by word, not by sentence.** Each
   word's menu goes to the LLM once, with all its sentences, from a hard-word list measured
   offline. Per-sentence LLM calls are not acceptable online. The answer can arrive after
   the deck opens and replace the embedding's pick.
4. **The French run is the Turbo rehearsal.** It is built under these rules (0.6B, no second
   embedding, rules, example cap, LLM per word on a fixed budget) and measured on a
   hand-labelled French benchmark of about 400 sentences. It reports:
   - accuracy with 0.6B alone, and with the LLM on hard words;
   - how many sentences actually reach WSD, which gives the cost of a 200-song upload.

   Prerequisites: a French grammar-word labeller and a French ledger at pilot size.

**Measured, 2026-10-12:** Qwen3-Embedding-0.6B alone is 79% on the random set (4B: 85%)
and 44% on the hard words. Not yet measured: 0.6B with the per-word hard list sent to the LLM,
which is the Turbo configuration; it needs a 0.6B per-word agreement file (`word_agreement.py`).

## Hard-word list: es/pt router and spot check (2026-10-12)

A first cut at the offline hard-word list, on Spanish and Portuguese. `router.py` predicts
per word how often the embedding margin (best sense minus runner-up) falls in the
narrowest quarter, from features known before embedding: senses still live after the POS
filter (by far the strongest), share decided without embeddings, largest single-POS
menu, closed-class share. Gradient boosting, cross-validated R² 0.29. Top families: es
verb + clitic imperatives (*dígales*, *llévenlo*), *estar*/*poder* forms, demonstratives;
pt *em*/*de*/*a* contractions, *ter*/*ser*/*levar*/*querer*.

78 closest calls from 16 families went to DeepSeek V4.1 Flash, thinking off
(`compare.py`, one sentence per call; `batched.py`, one menu with ~6 sentences per call).
Batched was better and cheaper ($0.058 per 1,000 sentences, peak): against the shipped
embedding pick, DeepSeek better 31, embeddings better 2, same 36, inseparable 9 (mostly
menu gaps: *darse vuelta*, *levar a sério*, *cuanto más*). Wins are senses carried by
grammar (auxiliary, passive, *ter que*, possession, indirect object). Judged by Claude,
not blind (`verdicts.json`, `spotcheck.html`).

Open, for whoever builds the Turbo hard-word list:
1. **Noise check.** Each setting ran once; repeat the single-sentence run (under a cent)
   to see how often DeepSeek changes its answer unprompted before reading the 7-vs-1
   batched-vs-single difference as real.
2. **Exact-duplicate senses.** The es *decir* menu lists every sense twice (VERB and
   transitive verb), so near-zero margins there are ties between identical text and
   inflate the router's list. Measure the margin against the best sense with different
   text. Do not cluster near-duplicates: Josh, a duplicate is a property of the
   sentence-sense pair, not of the menu.
3. **Retry missing answers.** One of 156 batched sentences came back with no answer.

## Ranked assigners: DEEPSEEK v25 on Portuguese (2026-10-14)

A temporary "ideal state" for the Portuguese deck while WSD improves, built so it cannot
leak into the method. `src/fluency/release/ranked_assigners.py`: a release takes each
example's sense from the first assigner in a declared order (`--assigner-order`), where
`NORMAL` is the run's own stage 04 and anything else is a sparse `wsd-assigner/v1`
directory under `<workspace>/raw`. Examples are still chosen from NORMAL (stage 05 is
unchanged); only the senses shown on them move. Nothing is written to any run, so no later
run can carry an LLM pick forward as a WSD decision. A later `NORMAL v26 > DEEPSEEK v25`
order lets an improved algorithm take over.

Portuguese, `pt-speech-v25-literal-ground-r4-10000x30-fw1-deepseek-v25-slim`, order
`DEEPSEEK v25 > NORMAL v25`:

- Calibration (1,500 sentences, random by margin band): DeepSeek disagreement is flat at
  ~50% across the narrowest 30% of margins, 41% at 30–40%, 23% at 40–60%, 3% at the top.
- Pass (`oneoff_pt.py`): words 1–4,000, narrowest 40% of margins, rule-decided rows
  excluded: 34,577 sentences, 3,813 calls batched by word, $1.48 at peak rates.
  16,561 meaning changes; Claude's judgement of 60: 30 better, 5 worse, 25 too close.
- Head-to-head check (`duel.py`): the two senses only, random order. On the judged 60 it
  kept all 30 better and rejected 4 of 5 worse. Kept 13,486 of 16,561 changes; $0.75.
- Assigner: `<workspace>/raw/wsd/pt/assigners/deepseek-v25-20261014` (13,486 rows),
  written by `scripts/write_wsd_assigner.py`.
- Release: same 282,300 examples as the live fw1 release; 13,486 differ in sense only.
  Side files rebound (`-ds25`); cognate verdicts recomputed (5,149 → 5,060 cards).
