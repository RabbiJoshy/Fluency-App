# Independent sentence review — 18 October 2026

Start with [report.md](report.md). This is a fixed 48-sentence sample outside all previously selected card sentences and prior audit pools, drawn from the existing harvest corpus. It is not the reserved HINGE holdout and not a representative corpus-wide benchmark.

The two language reviews were produced independently by Sol agents, blinded to the matcher predictions. They are AI editorial review, not native-speaker gold. No production data changed.

Artifacts:
- `sample.json`: sampling policy, eligibility counts, source attribution and input hashes.
- `pt-blind.json`, `es-blind.json`: reviewer packets, with teaching patterns but no predictions.
- `pt-review.json`, `es-review.json`: pattern, naturalness, translation, chunk and standalone suitability judgments.
- `parses.json`, `predictions.json`: fresh model observations and frozen-rule predictions.
- `evaluation.json`, `review-queue.json`: reproducible routing with explicit reasons.

Rebuild the evaluation with `python3 research/function_word_audit/independent_evaluate.py`.
Fresh parsing requires the repository virtual environment: `.venv/bin/python research/function_word_audit/independent_predict.py`. It verifies frozen matcher/labeller hashes and does not read the reviews. Do not overwrite these results after tuning rules against this sample; use a new version/sample instead.
The sampler refuses to overwrite an existing sample. It hashes and scans the harvest banks, excludes all IDs from the full pinned card-selection files and normalized text of those sentences, then chooses four unique examples per word by deterministic hash ranking.

Routing is deliberately separate from publishing. `reviewed_ready` requires all editorial checks plus exact pattern/chunk agreement. This run has no rows in that category. A future publisher must not treat structural candidate status alone as permission to insert an example into a learner deck.
