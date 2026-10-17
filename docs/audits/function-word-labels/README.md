# Automatic label bridge

Run from the repository root:

```sh
python3 research/function_word_audit/label_bridge.py
python3 research/function_word_audit/pilot.py
python3 -m unittest discover -s tests/function_word_audit -v
```

Read [the findings](report.md). The existing card preview has **Copy → Label trial**; this adds thirteen explicitly accepted fresh examples to the existing examples. It is not an automatic acceptance pipeline. All examples in the trial keep source text, translation and provenance. Pattern labels generate candidates; editorial review supplies acceptance and highlight spans.

## Evidence path

- `research/cascade/trouble-words/labeller_es.py` and `labeller_pt.py` contain parser/dictionary rules yielding `kind`, `value`, `gloss`, `rule`. Today's files may differ from the versions that produced retained releases.
- `src/fluency/release/run_candidate.py` carries `evidence.function_word` to example metadata and aggregates labels into roles/patterns with counts. Those groups do not have the new card pattern identities.
- `app/data/grammar-words/{pt,es}.json` holds the curated teaching formulas. The existing `allowed_lemmas` lists are not used as an executable assignment engine.
- This bridge reads pinned `source-candidates.json` release snapshots only. It does not rerun the parser or modify parked rule drafts, existing gold, or the holdout.

## Limits

334 examples are a capped, selected release sample, not a corpus-frequency denominator. Twenty-four fresh examples were editorially reviewed (two per word); thirteen were accepted. This deliberate diagnostic sample is not an accuracy estimate. Six of the 24 displayed patterns have no candidate from their own card's retained pool. That absence cannot establish that the rule cannot detect the usage: expand the pool and recover occurrence-level parse evidence next.

`findings.json` includes routing reasons, source records and review decisions. `sample-review.json` records explicit assistant editorial decisions and chunks. `trial.json` is isolated preview data. Production data is untouched.

## Occurrence-level follow-up

Read [the syntax report](syntax-report.md) and [the additional sample review](syntax-sample-report.md). The separate **Copy → Syntax trial** preview adds six reviewed examples using the adapter's generated spans verbatim. This variant starts from the original proposals, not the thirteen-example label trial.

```sh
# Optional one-time collection; explicitly reads development inputs only:
python3 research/function_word_audit/syntax_bridge.py --collect
# Rebuild from the pinned local subset:
python3 research/function_word_audit/syntax_bridge.py
python3 research/function_word_audit/syntax_trial.py
python3 research/function_word_audit/pilot.py
python3 -m unittest discover -s tests/function_word_audit -v
```

The cached subset covers 274 of 334 examples. The adapter yields 115 structural candidates and 219 abstentions, including 60 missing parses. It does not read census, gold, or holdout files. Missing cache entries remain unparsed; they are not treated as classifier failures.

Rules were developed after examining the earlier 24-case review, and refined after inspecting additional candidates. These are development diagnostics, not independent test accuracy. Twelve additional candidates were editorially reviewed: six entered the trial; six were withheld for semantic scope, fixed-expression or sentence-quality issues. This intentionally chosen sample does not estimate precision.

`syntax-findings.json` exposes focus token offsets, head/governor, parser identity, routing reasons, generated spans and source records. `parse-evidence.json` contains only the matched development subset with source hashes. `syntax-review.json` supplies acceptance decisions but no manual highlight strings. Production data and parked labeller drafts remain unchanged.
