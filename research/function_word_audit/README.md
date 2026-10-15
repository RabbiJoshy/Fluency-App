# Function-word editorial audit

See [the review and results](../../docs/audits/function-word-pilot/README.md).

- `check.py`: standard-library, read-only scan of Spanish and Portuguese curated suites. JSON and Markdown go to stdout; adjustable `--rule-limit` and `--sentence-limit` default to 20 and 15. Findings are advisory, with zero-based pattern/example coordinates. No automated naturalness score.
- `pilot.py`: explicit editorial revisions and a complete review ledger; writes separate proposals and reports. Reuses the existing card-preview approach (standalone HTML, coloured chunks and deterministic example cycling), but reads the actual original/proposed data rather than copying example strings into the renderer.
- `preview.py`: self-contained side-by-side renderer; no build dependencies.
- `discover.py`: inventory/deck comparison; parses literal dictionaries with AST rather than running parked labellers. Normalises Unicode, case and whitespace, preserving accents. Logs source hashes and release card IDs. `--workspace` selects release storage, and `--out` selects an output directory.

Run `python3 -m unittest discover -s tests/function_word_audit -v` for focused checks. Nothing here imports or modifies the app's live function-word renderer, grammar suites or assignment rules.
