# Portuguese staging correction-loading check

Checked 22 October 2026 by Codex. Read-only verification; no WSD run or release rebuild.

## Finding

Staging's served `config/config.json` points to
`pt-speech-v25-literal-ground-r4-10000x30-fw1-deepseek-v25-finite-v1-slim`.
DeepSeek corrections are baked into this release's example assignments, rather
than fetched as a separate JavaScript sidecar at card-render time.

The served composition declares `DEEPSEEK v25` ahead of `NORMAL`, with 13,486
changed assignments from `deepseek-v25-20261014`. Its subsequent linked-finite-form
correction preserves example assignments and changes learner meanings/headwords.

## Evidence checked

- Compared all 13,486 rows in the workspace's
  `raw/wsd/pt/assigners/deepseek-v25-20261014/assignments.jsonl` against the corrected
  release's actual index-row and example shards, including positional meaning references. All 13,486 are
  represented and match the intended source sense; zero mismatches. Comparison
  normalizes the `kaikki:` / `kaikki-senseid:` source-reference prefixes and restores compact `i` sentence IDs exactly as the app loader does.
- Compared Git blob hashes for all 400 index-row and 400 example shards in the
  published `Fluency-Releases-pt` repository against the checked local corrected
  release: 800 matches, zero mismatches (published Git tree `e890c629dd646b1c42dc7c229b9f5b155e847c3c`).
- Fetched both shard types directly from GitHub Pages for
  `level-001-set-01`, `level-003-set-01`, and `level-007-set-03`:
  six byte-for-byte matches. These include the set containing `certeza`.
- Verified staging's served configuration, manifest and composition, rather than
  inferring the release from its name alone.

Machine-readable check output is local at `dist/pt-correction-check.json`;
the release checked is under `dist/pt-finite-staging/pt/speech/`.

## What this does not establish

These checks establish that the expected corrections were exported and published.
They do not establish linguistic accuracy, correct example-to-meaning rendering
inside a signed-in user's existing session, or freshness of that browser's cache.
The DeepSeek pass covered close embedding decisions on words 1–4,000; it did not
reclassify every Portuguese sentence. See `research/cascade/README.md`.

## Separate WSD pass

Start with the actual example sentences on `certeza`, then the reported verbs.
Trace each sentence through source menu, baseline assignment, DeepSeek override
(if any), release selection, exported positional meaning, and displayed row.
Separate bad assignments from source-menu problems, misleading prominence,
lemma merging, and display errors. Preserve this corrected release and its
DeepSeek precedence; do not rerun or rebuild the deck just to investigate.

`foram` and the four-sense companion threshold remain unchanged at the user's
explicit request. This display batch does not change WSD assignments or the
ranking of `certeza` senses.
