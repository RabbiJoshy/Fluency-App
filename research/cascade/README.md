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

## What shipped (staging `stg-d2d56600`; production waits on Josh's "promote")

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
