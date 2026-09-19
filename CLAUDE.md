# Fluency Next — AI reference

Local-first successor to Fluency. Python pipeline plus a transplanted vanilla-JS
app (`app/`, no framework or build step). Python 3.12; `.venv` is a symlink to
the old repository's virtualenv.

**Two roots.** Code, config, tests and compact release metadata live here. Large
corpora, model caches, runs, pools and generated releases live in
`../Fluency-Workspace` and never in git. `../Fluency` is the older repository,
still the live app; treat it as reference, not a target.

## Read first

**`CHAT_ROADMAP.md`** (repo root) — named chats for the live deck campaign
(FUSE, SIEVE, QUARRY, …). Concurrent sessions: read SCAR, then **only your
codename**. Do not invent a parallel job. Copy to
`../Fluency-Workspace/raw/surfaces/DECK_CHAT_ROADMAP.md` after edits.
UI/app chats: not a pipeline row unless named as a blocker; still skim it.

**`REPO_MAP.md`** — dense architecture map, pipeline dataflow, and frontend `window.*` globals registry. Consult this before running exploratory searches or reading large files.

**`docs/INVARIANTS.md`** — the five rules that constrain every change. Read
before altering architecture, contracts or provenance.

1. Migrate the shape, preserve the substance, label both.
2. Absence is declared, never inferred.
3. A run must not record what it did not verify.
4. Adapters absorb irregularity at the edges; the engine exists once.
5. A language or mode is added by creating files, not by editing lists.

Then `CHAT_ROADMAP.md` for **which chat is allowed to do what**, `docs/ROADMAP.md`
for the long migration plan, and `docs/decisions/` for why things are as they
are. `docs/reference/` holds WSD measurements carried over from the older
repository — read its README first, because those were taken on Spanish against
a SpanishDict menu and not all of them transfer.

## Words to use precisely

`docs/NOMENCLATURE.md` pins the vocabulary. The one that matters most:
**provider** means a *sense-menu source* — SpanishDict, Wiktionary — not a
language and not a corpus. SpanishDict serves one language; Wiktionary serves
French, Portuguese and everything after. **Provider parity** is the requirement
that a concept built for one provider ships with the other's equivalent.

Ask "is this provider-agnostic?" rather than "does this work for other
languages?" — the second hides which you meant.

It also names the app's parts (setup flow, study view, card faces, pills,
modals) and the four words that mean different things on screen and in the data:
`tag`, `context`, `source`, `level`.

## The readiness contract

**A language is ready for WSD when its surface ledger is complete.** The ledger
is `<workspace>/raw/surfaces/<lang>/ledger.json` (`surface-ledger/v1`): one row
per surface, carrying verdict, reason codes, tags, the authority lemma with its
provenance, alternates, and harvest/eligible/rejected sentence counts with ids.

Beneath it sits an **append-only observation store**. Events are facts
(`accent_stripped_duplicate`, `dictionary_absent`); verdicts are policy, folded
from those events **at read time** by `surfaces/policy.py`. Changing a judgement
edits the policy table and re-materialises — it never rewrites history. Several
reason codes have had their verdict inverted at zero cost because of this.

The pipeline is three stages split by **cost and reversibility**: harvest applies
cheap irreversible gates, cleaning narrows expensively and *tags* rejects rather
than deleting them, WSD only disambiguates.

Resolve the path with `fluency.surfaces.ledger.ledger_path()`, never as a
literal. Full detail in `docs/decisions/0021-surface-ledger-and-observation-store.md`;
the command sequence is `docs/runbooks/surface-ledger.md`.

## The load-bearing fact

**A card's identity is the observed surface form.** `card_id = f(language,
surface_key)` and nothing else — not the lemma, not a sense, not a rank.
Everything else is metadata hanging off it. Lemmas may be lookup or linguistic
detail; making one an identity breaks learner progress, and the surface-inventory
schema has no field for one.

## Shape

```
src/fluency/
  cli/            one module per command group, behind a registry
  core/           workspace, hashing, io, language naming
  languages/      one package per language; each declares LANGUAGE_CODE
  inventory/      4 frequency adapters   -> surface-inventory/v1
  sense_menu/     kaikki + spanishdict   -> sense-menu/v1
  harvest/        tatoeba + opensubtitles -> parallel-sentence/v1, and pools
  surfaces/       events.py (append-only log), policy.py (fold -> verdict),
                  ledger.py (path + contract)      -> surface-ledger/v1
  features/       provider-neutral sense features   (NOT under wsd/)
  menus.py        sense-menu contract                (NOT under wsd/)
  projections.py  release-facing view                (NOT under wsd/)
  nlp/            pinned POS model, resumable embedding store, model registry
  wsd/            the classifier: optional enrichment, runs two stages late
  release/        composition, validation, activation
config/           policies per language, mode, provider and model
app/              vanilla-JS client; see REPO_MAP.md for module & window.* registry
  js/card-metadata-pills.js  sense metadata, grammar chips & qualifiers
  js/flashcards.js           card rendering & flip (read targeted ranges, never in full)
```

The three marked *NOT under wsd/* are placed deliberately: a menu or a release
must build without the classifier importing. A test enforces it by blocking
`fluency.wsd` entirely and importing both.

## Pipeline

```
01 inventory → 02 sense_menu ┐
             → 03 harvest    ┴→ 04 wsd → 05 selection → 06 release
```

`STAGE_INPUTS` in `pipeline/planning.py` is authoritative and it is a **diamond,
not a chain**: `sense_menu` and `sentence_harvest` are siblings, both reading only
the inventory. Changing a dictionary snapshot costs no corpus re-scan. Use
`stages_invalidated_by()`; do not reason from the numbering.

**Stages are immutable.** A stage with output refuses to be rebuilt — create a
new run instead. Run ids are `<timestamp>-<8 lowercase hex>`; `pt` or `00pt0001`
are rejected because they are not hex.

**WSD is optional.** A deck ships with every example marked explicitly
unassigned rather than blocking. Portuguese and Spanish both have such releases.

Languages with profiles or packages: `es`, `fr`, `pt`, `cs`, `nl`, `pl`. Modes: speech, lyrics, artist.

## Working with Josh

- **Token discipline on large files.** Consult `REPO_MAP.md` before exploring.
  Never read `flashcards.js` or `style.css` in full; inspect targeted line ranges.
  Do not grep raw dataset folders (`app/lyrics-audit/data/` or `research/**/results/`).
- **Verify before recommending.** Read the file, not the label. Repeated errors
  here came from trusting a name (`retained_materialized_assignments`), a
  constant (`SPACY_POS_MODEL`), or a single record (axis margins) and
  generalising. The distribution is usually one command away — measure it.
- **Long runs go in the background.** Corpus scans, embeddings and model
  downloads take minutes.
- **Spend is gated.** Anything calling a paid model prints projected units first.
  Known defect: the guard reads the harvest cap rather than the sampling cap and
  over-estimates roughly sixfold.
- **Name pipeline steps by file and purpose**, never by number alone.
- **Concurrent sessions are normal.** Check `git status` before committing;
  commit only your own paths. Others' uncommitted work is routinely present.
  Named jobs: **`CHAT_ROADMAP.md`** — do only your codename.
- **Deploy every UI change.** Any edit to files under `app/` must be committed
  on `main` and deployed to `gh-pages` at the end of the response — don't wait
  to be asked. Josh needs to see the result on the live site to judge it.
  Deploy procedure:
  1. **Record the change in changelog:** Before staging or committing, you MUST
     prepend an entry to **BOTH** `app/config/dev_changelog.json` and
     `config/dev_changelog.json`. The entry MUST include:
     - `"timestamp"`: exact ISO 8601 timestamp with timezone (e.g. `"2026-09-19T13:30:00+01:00"`)
     - `"date"`: formatted date/time with timezone (e.g. `"2026-09-19 13:30 BST"`)
     - `"agent"`: the name of the LLM agent making the change (`"Antigravity"`, `"Claude"`, `"Cursor"`, `"Codex"`, etc.)
     - `"summary"`: a concise human summary in normal text font describing the most recent change
     - `"detail"`: array of specific change bullets
     - `"commit"`: `"pending"` (or commit SHA)
     *Why:* The app's Settings → Developer tab renders this latest entry at the
     **very top of the section** so Josh can immediately verify what changed,
     who made the change, and whether the Service Worker cache is fresh or stale.
  2. `git add` only the files you changed (including changelog, bumped service worker
     and asset version tags). Do not stage other sessions' uncommitted work.
  3. Commit on `main` with a descriptive message and `git push origin main`.
  4. Copy each changed file into the gh-pages worktree at
     `/private/tmp/fluency-pages-deploy/`, writing to **both** the root path
     (e.g. `js/about-example.js`) and the `app/` mirror (e.g.
     `app/js/about-example.js`). Use `git show main:<path>` to get the
     committed version.
  5. Commit on `gh-pages` and `git push origin gh-pages`.
  Keep deploys surgical: only the files you touched, nothing else.
- **Don't rebuild what a pool already holds.** Named, described sentence pools
  live in `<workspace>/pools/<lang>/`; `fluency pools list` shows them.

## Commands

```bash
make test        # unittest discovery
PYTHONPATH=src .venv/bin/python -m pytest -q   # 879 pass, 4 known failures
python scripts/materialise_surfaces.py --workspace $W --language <lang>  # rebuild the ledger
python scripts/audit_surfaces_html.py  --workspace $W --language <lang>  # audit it in a browser
PYTHONPATH=src python -m fluency pipeline plan --profile config/pipelines/<lang>/speech/<profile>.json
PYTHONPATH=src python -m fluency pipeline inventory|sense-menu|harvest|wsd-import|build-run-release
PYTHONPATH=src python -m fluency pools list --language <lang>
PYTHONPATH=src python -m fluency release list|validate|activate --language <lang>
PYTHONPATH=src python -m fluency.speech.wsd_execute --run-dir <run> --out <bundle.json> --profile-id <id>
```

Every pipeline subcommand takes `--workspace`, and **`--language` defaults to
`fr`** — an easy omission that fails loudly but confusingly.

WSD writes a *bundle*; `pipeline wsd-import` publishes it into stage 04. The
release builder reads `stages/04_wsd_assignments/output/assignments.jsonl`, not
the bundle, so the import step is not optional.
