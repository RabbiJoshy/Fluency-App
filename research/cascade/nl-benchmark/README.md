# Dutch WSD benchmark (CASCADE-WSD), 2026-10-12

Pilot run `runs/nl/speech/20261012T175838Z-76d34ee3`, English Wiktionary menus.
Labels by Claude, not by a native speaker.

## Labels

- `labels-random.jsonl`: 160 items. A random card with at least two senses, then a
  random eligible sentence (`sample_r.py`, seed 20261012). Labelled blind to any model
  or parser. This is the fair estimate of deck accuracy.
- `labels-hard.jsonl`: 52 items on op, aan, er, te, zijn, dat, chosen by Stanza parse
  to include separable verbs, er-splits and fixed phrases. Not blind (parse visible).
- `verdict`: `fits` | `closest` (no exact sense, nearest one is gold) | `gap` (no
  sense fits) | `unclear` (excluded). Accuracy counts fits + closest.
- `gold_sense_ids` is every sense a learner would not be misled by. 20 golds were
  widened after adjudicating model picks (flagged in `note`). A pick whose displayed
  gloss is identical to a gold gloss also counts as right (`evaluate.correct`).
- Specs (`spec_r.txt`, `spec_hard.txt`) are the hand-written source; `build*.py`
  turn them into the JSONL. They need `$NL_SCRATCH/cache.pkl` from `dump.py`.

## Scorers

`embed_score.py <model>`: cosine(query, gloss) as in production
(`wsd_execute.GlossScorer`), with three queries: `nl` (Dutch sentence, the
production input), `en` (English subtitle), `inst` (Dutch with the target marked
`<<…>>` plus the English, behind the model's instruction format). `score.py`: LaBSE
and the Qwen3 0.6B reranker. `evaluate.py`/`compare.py`: accuracy with and without a
Stanza POS gate. `pairs.py`: escalation when two models disagree.

Results: `results-embeddings.txt`, `results-escalation.txt`. Spend for the whole
comparison: about $0.004 (Gemini $0.003, DeepInfra under $0.002).

## Findings (random stratum, 400 words, n=377 scorable; ±4 points at this size)

Labels: 400 random words (`sample_r.py` 160 + `sample_r2.py` 240), verdicts 357 fits,
20 closest, 20 gap, 3 unclear. Hard stratum unchanged (48 scorable).

| model (best input) | right of 377 | $/1M tokens | runs |
|---|---|---|---|
| DeepSeek V4.1 Flash (LLM, every sentence) | 363 (96%) | ~$0.08 per 1,000 sentences | API |
| gemini-embedding-001, marked + English | 88% | 0.15 | Google API |
| gemini-embedding-001, Dutch sentence (production input) | 85% | 0.15 | Google API |
| Qwen3-Embedding-8B, marked + English | 86% | 0.01 | DeepInfra |
| Qwen3-Embedding-4B, marked + English | 85% | 0.02 | DeepInfra |
| Qwen3-Reranker-0.6B (cross-encoder), marked + English | 83% | free local | local |
| EmbeddingGemma-300m / LaBSE, English | 81% | free local | either |
| bge-m3 / gte-multilingual-base, English | 80% | free local | either |
| e5-small, marked + English | 78% | free local | local, browser-sized |
| first sense on the menu | 49% | – | – |

1. Gemini stays the best embedding; marked word + English is a free gain over the
   production input. No cheap embedding matches it.
2. The LLM alone is better than any cascade: embeddings add no accuracy, they only
   save LLM calls (`cascades.py`, `results-cascades.txt`).
3. Escalation by two-model disagreement beats a model's own margin, but needs
   25–35% of sentences escalated to catch most errors.
4. Per-word easiness (`word_agreement.py`, `results-word-agreement.txt`): for each
   word, 10 further sentences answered by DeepSeek (reference) and by a cheap model.
   Menu shape alone predicts badly (`easiness.py`, AUROC 0.60–0.71); the measured
   agreement rate predicts well (AUROC 0.74–0.78). Words where the cheap model agreed
   on 10/10 are 22–31% of polysemous words, and there the cheap model is 95–98%
   right on the held-out sentence. Routing those words to the cheap model and the
   rest to DeepSeek gives 95–96% (DeepSeek everywhere: 96.3%).
5. On the hard 48, every embedding gets 35–62%, DeepSeek 75%.

Spend for everything here: about $0.20 (DeepSeek $0.17, Gemini ~$0.03, DeepInfra < $0.01).
