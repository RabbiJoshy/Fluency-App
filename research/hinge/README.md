# HINGE status — 14 October 2026

Josh changed the order: establish Portuguese special-word membership and card
design first. Example assignment may return later or move to another chat.

Assignment work is preserved, not signed off:

- Workspace `audits/hinge-20261014`: immutable input copies/hashes, parked diff,
  sentence-only review files, 651 development gold rows and 481 coverage gold rows.
- The 200-sentence holdout remains unlabelled and unscored.
- Parser and reflexive observations cover all 14,129 scoped examples.
- `paused-assignment-work/` preserves the current es/pt rule drafts separately.
- `tests/grammar_words/` has six passing context tests and the independent gold.
- Rule and comparison changes are drafts. Label-name agreement is not a semantic
  accuracy result. No release, staging deployment or production change occurred.

Current design cases: Portuguese **que, de, se, o, nos, naquele**. They cover
multiple grammatical uses, governed phrases, articles/clitics and contractions.
Do not resume example annotation or move the draft rules into production without
Josh asking to resume that work.
