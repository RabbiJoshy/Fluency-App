# Fluency Next — AI reference

Local-first successor to Fluency. Python pipeline plus a transplanted vanilla-JS
app (`app/`, no framework or build step). Python 3.12; `.venv` is a symlink to
the old repository's virtualenv.

**Two roots.** Code, config, tests and compact release metadata live here. Large
corpora, model caches, runs, pools and generated releases live in
`../Fluency-Workspace` and never in git. `../Fluency` is the older repository;
treat it as reference, not a target. The live app is built from this repo.

## Read first

**`CHAT_ROADMAP.md`** (repo root) — short: the **Open** table (the only open
work), what is live, what is done, and the pipeline rules. Named chats read it,
then **only their row**. Do not invent a parallel job or start work from
anything not in Open. Copy to `../Fluency-Workspace/raw/surfaces/DECK_CHAT_ROADMAP.md`
after edits. `LATER.md` is eventual direction, not work.

**`REPO_MAP.md`** — dense architecture map, pipeline dataflow, and frontend `window.*` globals registry. Consult this before running exploratory searches or reading large files.

**`docs/INVARIANTS.md`** — the five rules that constrain every change. Read
before altering architecture, contracts or provenance.

1. Migrate the shape, preserve the substance, label both.
2. Absence is declared, never inferred.
3. A run must not record what it did not verify.
4. Adapters absorb irregularity at the edges; the engine exists once.
5. A language or mode is added by creating files, not by editing lists.

Then `docs/decisions/` for why things are as they are. `docs/archive/` is
history (old campaign cards, proposals, migration audits): read a file there
only when a task names it, never as a source of open work. `docs/reference/` holds WSD measurements carried over from the older
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
  js/routes.js               shareable hash routes (#/es, #/es/w/<word>, #/artist/<slug>,
                             #/es/songs, #/es/live, #/es/conjugate[/<verb>], #/about,
                             #/tutorial, #/walkthrough).
                             Link with goToRoute/replaceRoute — never write ?artist=,
                             ?about= or ?playlistLive=; those are legacy and rewritten
                             on arrival.
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

Languages with packages: `es`, `pt`, `cs`, `fi`, `fr`, `nl`, `pl` (plus stubs for `it`, `ru`, `sv`). Live: es, pt, cs, fi, fr. Modes: speech, lyrics, artist.

## How Josh works

Condensed from `docs/archive/WORKING_WITH_JOSH.md` (~930 of his messages).
Quotes and reasons are there.

**Frame first.** Get the architecture running end to end before any one piece
is good. A placeholder is a legitimate answer when it unblocks structural work;
judge it by what it unblocks. Contracts make placeholders safe: if a component
can't be swapped later without a rewrite, say so now. **Label every
placeholder where he'll see it** (version and stamp runs; make stubs visible in
the deck). His most common bad surprise is "I thought we had changed that".
Preserve information even when nothing uses it yet. One target per pass: count
other problems, don't work on them. Show the small version first.

**Assumptions.** His provisional ones stay behind a swappable seam; his settled
ones are not reopened (say once if you disagree). Constraints you invented
(cost, parsimony) must be said out loud, in one line where they change the answer.

**Answering.** Answer the question asked, in the format asked, first; a length
limit is a hard limit; answer every numbered question. Conclusions, not working.
Plain English, no jargon; define a load-bearing term once, with an example.
Concrete examples (the actual card, row or output, and what it changed from).
When asked to choose, choose; otherwise at most one lean. Be candid about what a
number was measured on and whether that test can see the effect. Push back. His
messages are dictated: read through typos, ask only when the meaning is ambiguous.

**Cadence.** Report after each discrete unit of work; never chain two silently.
About ten lines: what was done, the number, a concrete example, next step or
decision. Bring decisions one at a time, close to the work. Stop and ask before
anything the brief doesn't name: changing a corpus or flag, spending money,
deleting, or fixing an unrelated bug. If you may have drifted, re-read the brief.
No handover prompts or paste-ready openers unless he asks.

**Engineering.** Fix error classes, not the one word he named. The baseline is
the thing to beat, not defend. Check upstream before building detection: the
recurring bug is a right answer computed and then discarded downstream. Test
harnesses are a few hundred labelled items, and you label them yourself. Don't
silently drop something agreed. Cheap and fast at scale is a product
requirement: expensive one-off offline work is fine, expensive per-sentence
online work is not. **Done** means a described, tested change shown to improve
named examples he can look at, not a commit or a passing test on its own.

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
- **Stage every change for review (AIRLOCK workflow).** Any edit to files under `app/`
  or candidate decks must reach **STAGING** (`https://fluency-staging.pages.dev/`) so Josh
  can review proposed changes in the full app on his laptop and actual phone while production
  remains stable and usable.
  **Do NOT push or deploy directly to production `main` without Josh's explicit approval.**
  Production (`https://rabbijoshy.github.io/Fluency-App/`) is updated only via deliberate
  promotion of the reviewed staging build.
  
  Staging procedure:
  1. **Record the change in changelog:** Before staging or committing, you MUST
     prepend an entry to `app/config/dev_changelog.json` (the only copy; the
     root `config/dev_changelog.json` was retired 2026-10-06). The entry MUST include:
     - `"timestamp"`: exact ISO 8601 timestamp with timezone (e.g. `"2026-10-10T14:00:00+01:00"`)
     - `"date"`: formatted date/time with timezone (e.g. `"2026-10-10 14:00 BST"`)
     - `"agent"`: the name of the LLM agent making the change (`"Antigravity"`, `"Claude"`, `"Cursor"`, `"Codex"`, etc.)
     - `"summary"`: a concise human summary in normal text font describing the most recent change
     - `"detail"`: array of specific change bullets
     - `"commit"`: `"pending"` (or commit SHA)
     *Why:* The app's Settings → Developer tab renders this latest entry at the
     **very top of the section** so Josh can immediately verify what changed,
     who made the change, and whether the Service Worker cache is fresh or stale.
     Keep at most the newest 30 entries (the tab shows 5; git keeps the rest).
  2. **Do not bump `?v=` tags or `CACHE_NAME`.** The staging/production builds stamp every tag,
     `ASSET_VERSION` and `CACHE_NAME` automatically (`scripts/build_pages_site.py`),
     so every deploy busts the cache. Run the app tests:
     `PYTHONPATH=src python3 -m unittest discover -s tests/app -t .`
  3. `git add` only the files you changed. Do not stage other sessions'
     uncommitted work. Commit.
  4. **Publish to Staging:** Run `make stage` (or `python3 scripts/deploy_staging.py`).
     This builds the staging site with isolated storage (`fluency-offline-staging`),
     namespaced sync (`stg_*`), and staging service-worker cache busting, then deploys
     it to Cloudflare Pages: `https://fluency-staging.pages.dev/`.
  5. **Review:** Josh reviews the changes in the full app on his laptop and actual phone.
  6. **Deliberate Promotion to Production:** When Josh explicitly approves promoting the
     reviewed version, run `make promote` (or `python3 scripts/promote_to_production.py`).
     Promotion verifies the exact reviewed commit SHA and pushes it to `main`, triggering
     `.github/workflows/deploy-pages.yml`. Unrelated commits made after staging are
     detected and blocked from silently entering production. Direct production deploys
     via `scripts/deploy.py` remain as an internal engine, but `make stage` + `make promote`
     is the required workflow for proposed product changes.
- **Releases are not on `gh-pages`.** The app is repo `RabbiJoshy/Fluency-App`
  (served at `rabbijoshy.github.io/Fluency-App/`; it was `Fluency-Next`, and a
  tiny `Fluency-Next` repo now only forwards old links). Release files live in
  one repo per first path segment, `RabbiJoshy/Fluency-Releases-<segment>`
  (es, pt, cs, fi, fr, lyrics), branch `gh-pages`, served at
  `rabbijoshy.github.io/Fluency-Releases-<segment>/…`. Config keeps naming them
  `releases/<segment>/…`; `app/js/release-host.js` maps that onto the segment's
  site. Publish with `python3 scripts/publish_release.py --segment <seg>
  --release <workspace release dir>` **before** pointing config at it; it
  uploads only new files and replaces `gh-pages` with one commit. Never add
  `releases/` to the app's `gh-pages`. A new language needs a new repo (Josh
  creates it; the first publish turns its Pages on). Decision 0026 has the why.
  The old combined `Fluency-Releases` repo is retired; do not publish there.
- **Don't rebuild what a pool already holds.** Named, described sentence pools
  live in `<workspace>/pools/<lang>/`; `fluency pools list` shows them.

## Commands

```bash
make test        # unittest discovery
PYTHONPATH=src .venv/bin/python -m pytest -q   # 1287 pass, 0 failures (2026-10-04)
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
