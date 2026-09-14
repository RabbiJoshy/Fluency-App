# Runbook — bringing a language to a complete surface ledger

The ledger is the readiness contract: a language is ready for WSD when its
ledger is complete. See `docs/decisions/0021-surface-ledger-and-observation-store.md`
for why it is shaped this way, and `docs/NOMENCLATURE.md` for the vocabulary.

Throughout, `$W = ~/PycharmProjects/Fluency-Workspace` and commands run from
`Fluency-Next` with `.venv/bin/python`.

## The loop

Observe → materialise → audit → adjudicate → materialise again. Only the first
step touches the network; the rest are local and take seconds.

### 1. Observe

Derive events from what is already on disk — inventory, menus, dictionaries,
pools. Append-only and deduplicated by content hash, so re-running is safe.

```bash
.venv/bin/python scripts/backfill_surface_events.py --workspace $W --language LANG
.venv/bin/python scripts/observe_lemmas.py --workspace $W --language LANG
```

### 2. Materialise the ledger

Folds the event log through the policy table into `ledger.json`.

```bash
.venv/bin/python scripts/materialise_surfaces.py --workspace $W --language LANG
```

It prints the verdict split, lemma coverage, and how many surfaces have fewer
than ten eligible sentences. Those three numbers are the readiness check.

### 3. Audit

```bash
.venv/bin/python scripts/audit_surfaces_html.py --workspace $W --language LANG
```

Writes a self-contained HTML table (~9MB). Rows are collapsed; expanding one
shows six sentences. Filter by verdict, thin supply, tag, lemma state, rejects,
or no-sentences. Open it in a browser — it needs no server.

### 4. Adjudicate the review queue

Anything at `review` is waiting on a judgement. Record it as an event, with a
reason, rather than editing the ledger:

- `adjudicated_keep` — settles outright, overriding other evidence
- `adjudicated_exclude` — excludes

Standardised manual reasons for a lemma that no provider can supply: `english`,
`proper_name`, `not_spanish` (or the language equivalent), `abbreviation`.

Then re-run step 2. **The review queue should be empty before WSD.**

## Language-specific: refreshing the Spanish menu

Spanish menus come from a pinned SpanishDict snapshot. When surfaces are missing
from it, fetch and merge rather than weakening the coverage gate.

```bash
# 1. Fetch. Paced at 0.35s, fsync per word, resumable — rerun to continue.
.venv/bin/python scripts/fetch_spanishdict.py \
  --run-dir $W/runs/es/speech/$(cat $W/runs/es/speech/LATEST_V11) \
  --surfaces /path/to/surface-list.txt \
  --out $W/raw/dictionaries/es/spanishdict/refetch-lemmas.jsonl --every 250

# 2. Merge into a NEW snapshot directory. Defaults to every refetch-*.jsonl
#    present; name them explicitly only if you mean to exclude one.
.venv/bin/python scripts/merge_spanishdict_refetch.py --workspace $W
```

The merge recomputes `sha256` in `artifact.json` for changed files. **The menu
build verifies those hashes and will refuse a stale one** — that check is
correct, so fix the hash rather than bypassing it.

Rows flagged `spelling_substitution` or `entry_lang_not_spanish` are withheld
from the menu and recorded as evidence. A fuzzy match is never a menu.

## Gotchas that have each cost a session

- **A merge that silently skips a file looks exactly like a merge that worked.**
  The merge script once read one hardcoded refetch filename; it now defaults to
  globbing every `refetch-*.jsonl`.
- **Never `.lower()` when matching a dictionary.** Wiktionary files uppercase
  abbreviations beside ordinary words: `NO` → *noroeste*, `ME` → *muerte
  encefálica*. Match exact case.
- **An empty filter result means "no evidence", not "reject everything".**
  Reading it the second way turned the POS filter into a silent no-op on the
  commonest words.
- **A harvest that takes hours is a suspended laptop.** A real run is about four
  minutes. Measure before optimising.
