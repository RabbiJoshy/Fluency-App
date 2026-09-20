# Speech decks → lyrics: chat roadmap

Repo `Fluency-Next`. Workspace `Fluency-Workspace`. Old `Fluency/` is read-only.

**UI / app chats are usually not a row in this file.** They do not harvest, WSD, or compose decks unless this roadmap **names them as a blocker** (e.g. empty study sets after a release). They **should still read SCAR and the freeze / version index** so product work matches what is shipping (display-v4, MWEs on the component card, v13 vs v14). Do not invent a speech-pipeline job from a settings tweak.

Come-back list (shipped, still open): **`OPEN.md`**. Eventual direction (not shipped yet, e.g. Italian): **`LATER.md`**. Skim both. Do not start a job from either. Those are not WSD steps. **SETLIST** is on this file because that chat is running now.

**Every pipeline chat opens with:**

> This chat is **`<CODENAME>`**. Read this file from the top through **SCAR**, then only your section. Do not do another chat’s job.

Canonical path: **`CHAT_ROADMAP.md`** (repo root).  
Workspace-only copy: `../Fluency-Workspace/raw/surfaces/DECK_CHAT_ROADMAP.md` (keep in sync after edits).

**Hold.** Sequence below is the switchboard. Do not open MILL or QUARRY yet. When Joshua is happy with this file, redo **SIEVE**, then **MILL**.

Paste for the redo: `This chat is SIEVE. Read CHAT_ROADMAP.md through SCAR and the freeze section, then only SIEVE. FUSE snapshots as given. Audit how those phrases behave on the frozen v12 sentences. Output is a keep/drop overlay or a one-line source rule, plus v14 commit so a winning phrase can publish. Do not harvest. Do not ship.`

**FUSE** is complete: snapshots built for es/pt/cs, non-decomposition filter and dual-write in place, model profiles `*-v14-1.json` wired, and sense-menu overlay placeholder stub (`fluency.wsd.overlays`) created.

A first SIEVE attempt exists on disk (`mwe-*-2026-09-17-v14-sieve/`, commit flags, `SIGN_OFF.md`). Treat it as a draft until the redo signs off.

Related briefs:

- **FUSE** (MWE lists + code): `Fluency-Workspace/raw/surfaces/V14_MWE_PREP_PROMPT.md`
- **NEEDLE** (v13 word-menu, done): `Fluency-Workspace/raw/surfaces/V12_AUDIT_PROMPT.md`
- Ledger/sentence viewer: `Fluency-Workspace/raw/surfaces/audit.html` (expand a row for occurrence POS)
- **Open** (shipped, still imperfect): `OPEN.md` → writeups in `docs/open/`. Skim; do not invent a job.
- **Later** (eventual direction, not shipped): `LATER.md`. Skim; do not start Italian from it.

---

## SCAR — how the v12 production run failed

Not a chat. **Every chat reads this.** The v12 *scores* are usable. The *run procedure* is not to be copied.

An agent ran `run_v12_production.py` end to end. Three faults, all visible in `--dry-run`:

1. **It rewrote the 10,000-surface ledgers.**  
   `materialise_surfaces` ran **without** `--supply-only`. A 6,000-card deck run folded its narrower supply into `ledger.json` and wiped the extra 4,000 surfaces’ harvest picture. That has been **repaired**. Today’s ledger is **not** the ledger that produced v12. Do not reverse-engineer v12 from it.

2. **It harvested again when pools already existed.**  
   It followed `LATEST_V11` into a 3,000-card probe path and re-scanned corpora. Named **10,000-card** pools were already on disk (`fluency pools list`). The “10k files” WSD should have used are those pools + the 10k ledger, not a fresh harvest. Because harvest + cap-30 ranking decide *which* sentences WSD sees, a “same cap” rebuild **will not pick the same 30 lines**. That is expected. Do not treat v12’s sentence set as the 10k production set.

3. **Stage 04 did not pin ledger or pools.**  
   The WSD manifest hashes bundle, candidates, inventory, sense menu, sentence bank — **not** the two artifacts that chose the sentences. The **frozen pre-WSD directory** is the substitute: `raw/surfaces/<lang>/prewsd/<run-id>/`. Verify with `fluency.surfaces.prewsd.verify()`. There is no `raw/observations/` (it is `raw/surfaces/`).

**Rules that exist because of SCAR**

| If you are… | You must… |
|---|---|
| Materialising a deck smaller than the language inventory | `--supply-only` |
| Starting a production run | `--run-id` on an **existing named pool**, not `LATEST_V11` |
| Auditing WSD quality | Read **that run’s** `stages/04_wsd_assignments/` and **that run’s** `--prewsd`. Not the live app. Not `ledger.json` after another session touched it. |
| Unsure whether to harvest | **Do not harvest.** Lab work uses the freeze already on disk. |

Live app today is **display-v4** on **v12 WSD** (`es/pt-speech-v12-6000x10-display-v4`, `cs-speech-v12-4000x10-display-v4`). Display is not a classifier version.

---

## Two kinds of work (why “free” is a place, not a vibe)

**Lab** — reuse sentences and embeddings already paid for.

- Inputs: frozen prewsd + existing `assignments.jsonl` + embedding caches  
  `embeddings/{es,pt,cs}/exact-text-gemini-embedding-001.npz`
- Flags: `--prewsd <that run’s dir>`, `--offline-only`
- Cost: CPU only if occurrence POS is still `null` on the pair. Frozen tags
  live on `pairs.json` (`occurrence_pos`, pin `occurrence_pos_model`). **No**
  new Gemini if the cache hits.
- v14 on this freeze is **not** free. Phrase glosses need vectors, and a
  phrase on the menu pulls single-sense lines into scoring. Remaining
  uncached **sentences** after the 2026-09-17 run: es **0**, pt **16,121**,
  cs **15,096**. Print that count with `--offline-only` before paying.
- Safe to repeat. Does not change which 10k surfaces “production” will use later.

**Plant** — new sentences or new vectors.

- Harvest, `condition_pools`, materialise a **new** prewsd, Gemini on **uncached** strings, full-deck `wsd_execute`, compose, activate
- Irreversible stage outputs (new run id). Print spend **before** any paid call. Known bug: the spend guard reads harvest cap, not sample cap, and over-states ~6×.

A lab chat that harvests “to be thorough” repeats SCAR.

---

## Audit chats only (not FUSE, not the plant)

These four **audit**: **NEEDLE**, **SIEVE**, **SWEEP**, **VERSE**.

Same loop as NEEDLE: start tiny → find a pattern → small algo/profile change → **bigger sample** → repeat. Grow the word/line set until leftovers look like edges, not a new class. Then stop. You are the judge. Do not run the full production deck as the audit.

**Output is a new version**, created as new files (`*-v13-1`, SIEVE’s filter + `*-v14-1` membership, `*-v15-1`, `es-lyrics-v16-1`). Do not overwrite the previous profile. When you would be willing for Joshua to run that version on the full freeze, **that version is the deliverable**. Sign off in the chat (“v15 stands” / leftover classes listed). Plant chats (LOOM, MILL, QUARRY, KILN, GLASS) **run** a signed-off version; they do not grow an audit.

**FUSE is not this loop.** It settles membership policy and wiring. SIEVE is the growing sample for MWEs.

**Signed-off output (audit chats).** The chat is not done until these files (or the written “stands”) exist. New files only; never overwrite the previous version.

| Audit | Version name | Must exist |
|---|---|---|
| **NEEDLE** | speech **v13** | `config/wsd/models/{es,pt,cs}-v13-1.json` + a short leftover list. **Done.** |
| **SIEVE** | speech **v14** (filter on FUSE’s list) | Two-sentence filter + signed-off overlay `raw/mwe/mwe-*-2026-09-18-v14-sieve/` + `config/wsd/models/{es,pt,cs}-v14-1.json` (phrase commit + fallback + dual-write). Leftover list in `SIGN_OFF.md`. **Done.** |
| **SWEEP** | speech **v15** | `config/wsd/models/{es,pt,cs}-v15-1.json` **or** a written “v14 stands” (no profile change). Leftover list either way. |
| **VERSE** | lyrics **v16** | `config/wsd/models/es-lyrics-v16-1.json` (Wiktionary-route lyrics files if that mode exists). Do not overwrite `es-v7-1`. |

Sign-off sentence in the chat: “Joshua can run <version> on the full freeze. Leftovers: ….”

---

## Chat index

Say the bold name.

| Codename | Version-ish | Job | Lab or plant | Status |
|---|---|---|---|---|
| **SCAR** | v12 incident | Shared memory. Not a chat. | — | Read always |
| **NEEDLE** | v13 algo | Word-menu abstain/commit. No MWEs. | Lab | Done (profiles `*-v13-1`) |
| **LOOM** | v13 decks | Run v13 on the **current** freeze. Ship optional. | Lab (POS from pairs; spaCy only on `null`) | Parked (skip; wait for v14) |
| **FUSE** | v14 MWE setup | MWE inventories, non-decomposition filter, dual-write, overlay stub. | Lab | Done (snapshots + profiles `*-v14-1`) |
| **SIEVE** | v14 filter | Watch FUSE phrases on frozen v12 lines; sign off which pass. | Lab | **Done** (signed off in `sieve-2026-09-18`; ready for MILL) |
| **MILL** | v14 lab decks | Run signed-off v14 on the **current** freeze. New run id; remaining embeds; compose; activate if Joshua says. | Lab sentences + declared spend | **Done** (deployed to live app under `flashcards-v480`) |
| **SWEEP** | speech **v15** | Audit the live v14 decks; tune WSD scoring & gating; sign off `*-v15-1`. | Lab on v14 freeze | **Done** (v14 stands; profiles `*-v15-1` written; ready for QUARRY) |
| **QUARRY** | 10k supply | Correct 10k pools → clitic de-phrasing → new prewsd freeze. `--supply-only`. | Plant (harvest only if pools missing) | **Done** (pools registered, clitics de-phrased, prewsd v2 frozen; ready for CHISEL 1) |
| **CHISEL 1** | 10k MWE baseline | Curate 3-axis overlay (wsd_routing, flexibility, ui_role) across 10k cards; sign off. | Lab on 10k freeze | **Done** (signed off in `mwe-*-10k-sieve`; ready for KILN 1) |
| **KILN 1** | 10k WSD baseline | Embed deltas; execute 10k WSD using `*-v15-1` + CHISEL 1 overlay. | Plant | **Done** (published Stage 04 across es, pt, cs; ready for CHISEL 2) |
| **CHISEL 2** | MWE tag refinement | Audit KILN 1 WSD outputs; discover additional axes/template bounds on real data. | Lab on KILN 1 output | **Done** (signed off in `raw/mwe/chisel-2`; ready for KILN 2) |
| **KILN 2** | Precision 10k WSD | Re-run/finalize WSD with CHISEL 2 refined MWE overlay before release. | Plant | **Done** (precision 10k WSD published to Stage 04 across es, pt, cs; ready for GLASS) |
| **GLASS** | v15 10k decks | Import bundle, compose, validate, activate the 10k speech decks. | Plant (no model) | Ready after KILN 2 |
| **GRAFT** | lyrics overlays | Collect slang, fillers, and lyrics MWEs/words into overlay snapshots. | Lab / curation | After GLASS (before VERSE) |
| **VERSE** | lyrics **v16** | Rebase on SWEEP (v15) + GRAFT overlays; lyrics WSD v16. Bad Bunny lyrics stack is **v7**. | Lab first, plant later | After GRAFT; may sit idle until then |
| **SETLIST** | live playlist UI | Spotify playlist → LRCLIB → worker persist → naive speech-overlay deck. No WSD. | beside WSD | In progress (brief `docs/runbooks/live-playlist.md`) |

**Hold.** Sequence: SIEVE done, MILL done, SWEEP done, QUARRY done, CHISEL 1 done, KILN 1 done, CHISEL 2 done, KILN 2 done. **GLASS is next** to compose and activate the 10,000-card speech releases. SETLIST does not wait on that hold.

KILN 1 executed on QUARRY’s freeze and CHISEL 1's 10k MWE overlay. Do not call the v12 freeze “v14 production 10k.”

---

## Beside WSD

This file’s index is the **WSD campaign**, including chats that have not started (SWEEP, QUARRY, …).

Product pieces that are not that campaign live in **`OPEN.md`**. SWEEP and QUARRY do not wait on them. When a non-WSD chat is actually running, name it here so it does not collide with SWEEP. Today that is **SETLIST**. When conjugations reopen, name that chat **DRAWER** for the duration of the work.

---

## Freeze identity (the two WSD objects)

WSD’s freeze is two files, not the live ledger:

| Object | File | Key | Holds |
|---|---|---|---|
| Sentences | `examples.json` | row index | text, translation, corpus metadata |
| Pairs | `pairs.json` (`prewsd-pairs/v2`) | (word, sentence index) | eligible order, burden, **occurrence POS** |

Occurrence POS is `(sentence, word, tagger) → UD tag`. Pin is `occurrence_pos_model` on the pairs document (`es_dep_news_trf@3.8.0`, `pt_core_news_lg@3.8.0`, unused for cs). JSON `null` = undeclared (execute may still tag). A string is frozen. New tagger pin → new freeze, do not overwrite.

Lab freeze for es/pt (v12 tags stamped; **do not rewrite the hashed v1 dirs**):

- es `raw/surfaces/es/prewsd/20260914T223348Z-c35194bc-v2`
- pt `raw/surfaces/pt/prewsd/20260914T222723Z-e43a0469-v2`

Backfill: `scripts/backfill_prewsd_occurrence_pos.py`. Viewer: `raw/surfaces/audit.html`. QUARRY writes a **new** run’s prewsd already in v2 (null POS until tagged, then freeze).

Lab `--prewsd` should be the **`-v2`** dirs above, not the v1 folders and not the v12 WSD run-id (those ids differ; that was SCAR).

---

## The sequence in plain language

You already have a **v12 freeze**: sentences + scores + embedding cache + sparse pair POS. That is the free lab.

1. **NEEDLE** already tuned the *word* menu (abstain when unlicensed). MWEs were parked on purpose. (Done)
2. **LOOM** (optional, parked) would run that word-menu on the same freeze and ship a v13 deck *without* idioms. Skip; wait for v14.
3. **FUSE** built the candidate idiom lists and wiring. (Done)
4. **SIEVE** watched those phrases on the frozen v12 sentences and signed off the two-sentence filter. (Done)
5. **MILL** ran that signed-off v14 on the v12 freeze, separated Invariant vs Ambiguous MWEs, and deployed the decks to the live app (`flashcards-v480`). (Done)
6. **SWEEP** (v15) audits those live v14 decks on the 6k/4k freeze: tunes WSD scoring, gating, provider priors, and phrase winner overrides. Outputs `config/wsd/models/{es,pt,cs}-v15-1.json`.
7. **QUARRY** expands to the 10k supply. Named pools, single-word clitic de-phrasing (*déjalo* $\to$ *dejar*), and stamps the new 10k pre-WSD freeze (`pairs.json` v2).
8. **CHISEL** takes the new 10k freeze, curates and retags MWEs across the newly added 4,000 cards, verifies Invariant vs Ambiguous tags, and signs off on the 10k MWE overlay.
9. **KILN** executes full-deck WSD on the 10k freeze using the signed-off `v15` profile from SWEEP + CHISEL's 10k MWE overlay.
10. **GLASS** composes, validates, and activates the 10,000-card speech decks on v15.
11. **GRAFT** collects domain-specific MWEs and single-word extra senses (Caribbean slang, reggaeton idioms, conversational fillers, elided locutions) into structured overlays via `fluency.wsd.overlays`, before lyrics WSD disambiguation.
12. **VERSE** is the lyrics WSD chat. Rebased on speech v15 (SWEEP) + domain overlays (GRAFT), producing **lyrics WSD v16**. Do not treat speech v12 as the method to ship.

---

## Per-chat cards

### NEEDLE — v13 word-menu (done)

**This chat is NEEDLE.** Audit chat: grow the sample; output is **v13** when leftovers are edges.

- Brief: `V12_AUDIT_PROMPT.md`
- **Output:** `config/wsd/models/{es,pt,cs}-v13-1.json` (exists). Sign-off was leftover edges, not a full deck.
- Free test: sample v12 `assignments.jsonl` + `--prewsd` of  
  es `20260915T140557Z-3c7e70a9`, pt `20260915T130807Z-4120e951`, cs `20260915T162357Z-ca5c81cd`
- Do not: harvest, MWE on, full decks, overwrite v12 profiles

### LOOM — v13 full speech decks (optional, parked)

**This chat is LOOM.**

- Job: run `*-v13-1` on the **current** freeze (`…-v2` prewsd dirs in the freeze section); import; compose only if Joshua wants a v13 ship.
- Free test: `--dry-run` the execute command; confirm `--prewsd` hashes; confirm embedding cache path. POS is read from pairs when frozen; spaCy only on `null` cells.
- Do not: `materialise` without `--supply-only`; new harvest; `--multiword-inventory`; activate unless Joshua says so

Parked. Skip shipping v13; wait for MILL’s v14.

### FUSE — MWE setup (inventories + wiring)

**This chat is FUSE.** This is the chat that *sets up* MWEs for es, pt, and cs. It is not SIEVE, not QUARRY, not KILN.

- Brief (full): `Fluency-Workspace/raw/surfaces/V14_MWE_PREP_PROMPT.md` — includes Joshua’s original two points (*en serio* / v12 never offered MWEs; existence = non-decomposition; dual-write word-leaf). **Discussion + implementation.**
- Job: new snapshots (do not overwrite `mwe-merged-2026-08-23-v1`); Wiktionary-route **pt** and **cs** lists; compositional tags as policy; v14 profiles `*-v14-1`; `--multiword-inventory`; compete not veto; dual-write best **word-leaf** when an MWE wins. Card id stays the surface.
- **Output:** first `raw/mwe/` snapshots (not an overwrite of `mwe-merged-2026-08-23-v1`) + `config/wsd/models/{es,pt,cs}-v14-1.json` pointing at them. SIEVE audits next. Not a deck.
- Free test: unit tests; count keys; keep/drop examples (`en serio` keep, `muy serio` drop). Read **`-v2` prewsd** sentences to sanity-check keys. **No** harvest, **no** Gemini, **no** full `wsd_execute`.
- Do not: harvest; prefer-MWE ranking; full decks; treat NEEDLE leftovers (`unas`, `dele`) as MWEs; retag POS (already on pairs)

### SIEVE — v14 filter on FUSE’s list (redo)

**This chat is SIEVE.** Audit chat **after FUSE**. FUSE offered candidate phrases. You watch them on frozen v12 sentences and sign off which pass. MILL runs that version; you do not harvest and you do not ship.

Paste:

> This chat is SIEVE. Read CHAT_ROADMAP.md through SCAR and the freeze section, then only SIEVE. FUSE snapshots as given. Audit how those phrases behave on the frozen v12 sentences. Output is a keep/drop overlay or a one-line source rule, plus v14 commit so a winning phrase can publish. Do not harvest. Do not ship.

- Job: `--offline-only` on the `-v2` freeze with `--multiword-inventory` = FUSE. Grow the sample. Sign off a keep/drop overlay **or** a one-line source rule (e.g. keep Wiktionary, drop one tag). Change `*-v14-1` commit so a phrase can publish. Do not overwrite `*-v13-1`.
- **Output:** signed-off overlay `raw/mwe/mwe-*-2026-09-18-v14-sieve/mwe_merged.json` + leftover list + `*-v14-1.json` commit flags pointing at that overlay. Sign-off doc: `raw/mwe/sieve-2026-09-18/SIGN_OFF.md`.
- Redo encoded FUSE's spoken rule: (1) SpanishDict collocations without Wiktionary backing are excluded as compositional noise; (2) Within Wiktionary, noun compounds (only POS is noun) are excluded as compositional; non-noun locutions with `corpus_freq > 0` are kept.
- Free test: `-v2` prewsd + v12 run-dir. Uncached counts printed via `--offline-only` (es 0 sentences / 5 glosses; pt 16,060 sentences / 13 glosses; cs 15,011 sentences / 2 glosses). Uncached strings wait for MILL.
- Do not: harvest; turn MWE on in v13 profiles; ship decks; start MILL; rewrite this brief to match extra work

MILL is next, after sign-off. QUARRY is the later 10k expansion.

### MILL — v14 on the v12 lab freeze (after SIEVE)

**This chat is MILL.** Plant chat between SIEVE and QUARRY. SIEVE already signed off the version. You run it on the **current** freeze and may ship. This is not SIEVE, not QUARRY, not KILN.

Paste:

> This chat is MILL. Read CHAT_ROADMAP.md through SCAR and the freeze section, then only MILL. Run signed-off v14 on the current freeze. Use SIEVE’s overlay, not FUSE’s unfiltered snapshot. New run id (v12 stage 04 already exists). Print uncached counts with `--offline-only` before any paid embed. Do not start QUARRY.

- Job: new run on the v12 card set (`--supply-only` if you materialise). `wsd_execute` with `--prewsd` = the `-v2` dirs in the freeze section, `--profile-id *-v14-1`, `--multiword-inventory` = **SIEVE’s signed-off overlay**.
  - **Spanish (`es-v14-1`)**: Runs in **full MWE competition mode** (`active_projection: "mwe_augmented"`) across all 1,544 kept locutions. 0 uncached sentences on `-v2` freeze ($0.00 spend, 100% offline cache hit).
  - **Portuguese & Czech (`pt-v14-1`, `cs-v14-1`)**: Recount uncached lines with `--offline-only`. For zero-spend offline testing, uncached lines fallback; otherwise print projected spend before any paid API embed (~$3.50 total).
  Then `pipeline wsd-import`, compose, validate; activate only if Joshua says.
- **Output:** imported stage 04 on the new run + live v14 speech decks deployed under `flashcards-v480`. Display SENTENCE_FLOW.
- **Status:** **Done.** Released candidate decks `es-speech-v14-6000x10`, `pt-speech-v14-6000x10`, `cs-speech-v14-4000x10` deployed to GitHub Pages.

### SWEEP — v15 algorithm audit on live v14 decks (Done)

**This chat is SWEEP.** Audit chat: grow the sample on the **live shipped v14** decks (deployed under `flashcards-v480` from MILL). Output is **speech v15** (`config/wsd/models/{es,pt,cs}-v15-1.json` or written “v14 stands”) when leftovers are edges.

- **Status:** **Done.** Audited targeted sample across es, pt, cs live v14 decks; zero false-positive contamination on invariant MWEs, sensible ambiguous competition wins, and clean polysemous single-word fallbacks. **v14 stands**. Model profiles `config/wsd/models/{es,pt,cs}-v15-1.json` written identical to v14 baseline. QUARRY is next.

### QUARRY — 10k supply, new freeze (After SWEEP)

**This chat is QUARRY.**

Paste:

> This chat is QUARRY. Read CHAT_ROADMAP.md through SCAR and the freeze section, then only QUARRY. Build named 10k pools for es, pt, cs (--supply-only). De-phrase single-word clitics before materialise_surfaces. Freeze this run's prewsd as pairs v2. Print --dry-run first. Do not call Gemini. Do not run full WSD.

- Job: for es, pt, cs: named 10k pools (`fluency pools list`). If a pool is missing, harvest **that** source into a **new** run id — never `LATEST_V11`. `condition_pools`.
  - **Single-Word Clitic De-Phrasing (es)**: Before/during `materialise_surfaces`, intercept single-token words tagged as `"PHRASE"` by SpanishDict (e.g. *déjalo*, *hazlo*, *dime*). Map them via Wiktionary `form_of` / enclitic pattern to their true verb lemma (*dejar*, *hacer*, *decir*) and POS `VERB`, ensuring single-word verbs are not misclassified as phrases and merge cleanly in lemma mode.
  - `materialise_surfaces --workspace $W --language LANG --run-id LANG=<run-id> --supply-only`. Freeze **this** run’s prewsd as pairs v2 (POS column present; fill tags before KILN or accept spaCy on `null`). Print `--dry-run` first.
- Free test: dry-run; `prewsd.verify()`; confirm ledger row count still 10k after materialise; confirm you did not write a 6k ledger; confirm `pairs.json` is `prewsd-pairs/v2`.
- Do not: audit idioms here; call Gemini; run full WSD; skip `--supply-only`
- **Status:** **Done.** Registered named 10k pools (`es-10k-speech`, `pt-10k-speech`, `cs-10k-speech`). Single-word clitics de-phrased via `observe_lemmas/spanishdict-clitic-dephrased` with POS `["VERB"]` and primary lemma routed to the base verb (e.g. *déjalo* $\to$ *dejar*, *hazlo* $\to$ *hacer*, *dime* $\to$ *decir*). Frozen 10k pre-WSD artifact sets stamped with `prewsd-pairs/v2` (es `20260914T223348Z-c35194bc`, pt `20260914T222723Z-e43a0469`, cs `20260914T223828Z-ad405a28`) covering 10,000 cards each. Verified with `prewsd.verify()` (0 mismatches).

This is the step that **intentionally** diverges from v12’s sentence set.

### CHISEL — 10k MWE curation & retagging (After QUARRY)

**This chat is CHISEL.** Dedicated MWE inventory and retagging chat on the newly expanded 10,000-card freeze before KILN.

Paste:

> This chat is CHISEL. Read CHAT_ROADMAP.md through SCAR and the freeze section, then only CHISEL. Take QUARRY's newly frozen 10k pre-WSD set and curate the 10,000-card MWE overlay. Audit MWE attachments on ranks 6,001–10,000, verify Invariant vs Ambiguous routing tags, add desired tag axes (verbal idioms, flexibility), and sign off on raw/mwe/mwe-*-10k-sieve/mwe_merged.json. Do not run full WSD. Do not start KILN.

- Job: Audit candidate MWEs against the newly unlocked 4,000 cards in QUARRY's freeze. Finalize Invariant vs Ambiguous tags across all phrases so deterministic idioms bypass KILN competition. Verify token boundaries and longest-match span masking.
- **Output:** Signed-off 10k MWE overlays (`raw/mwe/mwe-*-10k-sieve/mwe_merged.json`) + sign-off doc.
- Free test: Validate overlay schema; confirm zero paid calls; test against QUARRY's `pairs.json`.
- Do not: Call Gemini embeddings; harvest new sentences; run full 10k WSD (that is KILN).
- **Status:** **Done.** Curated 10,000-card MWE overlays (`raw/mwe/mwe-*-10k-sieve/mwe_merged.json`), enriched with `verbal_idiom` and `flexibility` axes, finalized Invariant (1,063 es, 687 pt, 126 cs) vs Ambiguous routing tags, audited attachments on ranks 6,001–10,000 (recovering 14 Spanish orphan locutions), and updated `*-v15-1.json` model profiles. Sign-off doc written to `raw/mwe/chisel-10k/SIGN_OFF.md`. Ready for KILN.

### KILN 1 — embed deltas + v15 WSD on 10k baseline (Done)

**This chat was KILN 1.** Plant chat. Executed full 10k WSD on QUARRY's freeze using SWEEP's signed-off `*-v15-1` profiles and CHISEL 1's 10k MWE overlay across es, pt, and cs.

- **Status:** **Done.**
  - **Spanish (`es`)**: Run `20260914T223348Z-c35194bc` imported to `runs/es/speech/20260914T223348Z-c35194bc/stages/04_wsd_assignments/output`. (Assigned: 284,652, Abstained: 9,461, No-menu: 3,123, Cap-30 overflow: 148,995).
  - **Portuguese (`pt`)**: Run `20260914T222723Z-e43a0469` imported to `runs/pt/speech/20260914T222723Z-e43a0469/stages/04_wsd_assignments/output`. (Assigned: 285,332, Abstained: 11,585, No-menu: 683, Cap-30 overflow: 148,909).
  - **Czech (`cs`)**: Run `20260914T223828Z-ad405a28` imported to `runs/cs/speech/20260914T223828Z-ad405a28/stages/04_wsd_assignments/output`. (Assigned: 269,949, Abstained: 18,066, No-menu: 15,047, Cap-30 overflow: 152,199).
  All embedding caches 100% complete and offline. Ready for CHISEL 2 audit.

### CHISEL 2 — 10k MWE refinement & audit (After KILN 1)

**This chat is CHISEL 2.** Audit chat on the published Stage 04 assignments from KILN 1.

Paste:

> This chat is CHISEL 2. Read CHAT_ROADMAP.md through SCAR and the freeze section, then only CHISEL 2. Audit KILN 1's published Stage 04 WSD assignments across es, pt, and cs. Inspect MWE competition wins, check for false positives, verify verbal idiom template gap bounds, and refine the 10k MWE overlay. Do not run full WSD. Do not start KILN 2.

- Job: Audit real Stage 04 assignments across es (`20260914T223348Z-c35194bc`), pt (`20260914T222723Z-e43a0469`), and cs (`20260914T223828Z-ad405a28`). Identify overeager MWE attachments, verify enclitic/clitic behavior in verbal idioms, tune template gap tolerances and boundary constraints on real sentence scores.
- **Output:** Refined 5-axis 10k MWE overlays (`raw/mwe/mwe-*-10k-sieve/mwe_merged.json`) + sign-off doc (`raw/mwe/chisel-2/SIGN_OFF.md`).
- **Status:** **Done.** Audited KILN 1 Stage 04 assignments across es, pt, and cs. Enriched overlays with 5-axis schema (`wsd_routing`, `flexibility`, `ui_role`, `transparency`, `template_gap_limit`), promoted 42 Spanish, 25 Portuguese, and 5 Czech unambiguous 100%-winning expressions to `deterministic_bypass`, hardened regex precision for *dar*, *pôr*, and *mít*, calibrated template gap limits (0–3 tokens) on real sentence scores, and signed off in `raw/mwe/chisel-2/SIGN_OFF.md`. Ready for KILN 2.
- Free test: Inspection scripts on Stage 04 JSON files; dry-run MWE matchers on disputed sentences. Zero Gemini spend.
- Do not: Call Gemini embeddings; harvest new sentences; run full 10k WSD.

### KILN 2 — Precision 10k WSD (Done)

**This chat was KILN 2.** Plant chat. Re-ran precision 10k WSD on QUARRY's freeze using SWEEP's signed-off `*-v15-1` profiles and CHISEL 2's refined 5-axis MWE overlays (`raw/mwe/mwe-*-10k-sieve/mwe_merged.json`), and re-imported Stage 04 across es, pt, and cs.

- **Status:** **Done.**
  - **Spanish (`es`)**: Run `20260914T223348Z-c35194bc` re-imported into `runs/es/speech/20260914T223348Z-c35194bc/stages/04_wsd_assignments/output`. Multiword inventory `sha256:9c0bb06061202042a2b29c29625a8d55dd01c60f5ef99f2be752360070bbacb5`. (Assigned: 284,653, Abstained: 9,461, No-menu: 3,122, Cap-30 overflow: 148,995).
  - **Portuguese (`pt`)**: Run `20260914T222723Z-e43a0469` re-imported into `runs/pt/speech/20260914T222723Z-e43a0469/stages/04_wsd_assignments/output`. Multiword inventory `sha256:cf13cc27cf567ee17401fa857e260240d6b4e23c3a4f697c2d6f3c5a6e3f6af0`. (Assigned: 285,332, Abstained: 11,585, No-menu: 683, Cap-30 overflow: 148,909).
  - **Czech (`cs`)**: Run `20260914T223828Z-ad405a28` re-imported into `runs/cs/speech/20260914T223828Z-ad405a28/stages/04_wsd_assignments/output`. Multiword inventory `sha256:e94d39d20b82ffe83a373bc0fdf35a14d87a8372ff2c677c8030500a6c819aa5`. (Assigned: 269,949, Abstained: 18,066, No-menu: 15,047, Cap-30 overflow: 152,199).
  All embeddings 100% offline cache hit ($0.00 spend; 0 API calls). Final Stage 04 assignments ready for GLASS release composition.

### GLASS — v15 10k decks on the app (After KILN)

**This chat is GLASS.**

- Job: compose 10,000-card speech releases from KILN stage 04; validate; activate. Display still SENTENCE_FLOW (WSD-labelled ticks; one canonical per meaning on that card).
- Free test: `fluency release validate`; load study sets locally (empty-set bug was skinny `meanings: []` — do not ship that).
- Do not: change WSD; “quick harvest” to fill ticks

### GRAFT — lyrics & slang sense-menu overlays (before VERSE)

**This chat is GRAFT.** Domain & slang collection chat before lyrics WSD.
- Input Dossier: `docs/dossiers/graft-source-dossier.md` (shared working dossier; check its status and vet sources before building snapshots).

Paste into that chat:

> You are **GRAFT**. Read `CHAT_ROADMAP.md` through SCAR, then only GRAFT. First, read `docs/dossiers/graft-source-dossier.md` and check its status, source inventory, and taxonomy. Your job is to collect domain-specific multi-word expressions and single-word extra senses (slang, regionalisms, conversational fillers, elided locutions) into structured overlays via `fluency.wsd.overlays` before VERSE runs lyrics disambiguation.

- Job: Harvest/curate domain expressions (Caribbean slang like *guagua*, *vaina*; reggaeton idioms; conversational discourse fillers like *o sea*; lyrics contractions). Map them to component surface cards. Build reproducible overlay snapshots under `raw/overlays/` adhering to the `SenseMenuOverlay` interface in `fluency.wsd.overlays`.
- **Output:** Structured overlay snapshot (e.g. `raw/overlays/lyrics/es-lyrics-overlays.json`) ready for injection into `WSDComponents.overlay_provider`.
- Free test: Load overlays into `CompositeOverlayProvider`, assert candidates attach to target cards, verify unit tests pass with zero Gemini spend.
- Do not: Run full lyrics WSD (that is VERSE); harvest new audio/lyrics corpora without spec.

### VERSE — lyrics WSD v16 (after SWEEP + GRAFT)

**This chat is VERSE.** Audit chat once v15 and GRAFT overlays exist: grow lyrics samples; output is **lyrics WSD v16** when leftovers are edges. Until then, park. Joshua may **rename the existing lyrics-design chat**.

Paste into that chat:

> You are **VERSE**. Speech **v15** (SWEEP) is the speech baseline; **GRAFT** provides domain overlays. Output is **lyrics WSD v16**. Audit: tiny sample → pattern → change → bigger sample until leftovers are edges; that version is the deliverable. Speech v12 was a sketch. Live Bad Bunny stays lyrics v7 until you replace it. Park until SWEEP and GRAFT sign off. Read `CHAT_ROADMAP.md` SCAR, **Audit chats only**, and VERSE.

- Job: take that chat’s already-written change list, **rewrite it against v15 + GRAFT overlays** (MWEs, slang/filler overlays, abstain, freeze POS-on-pairs, display-v4 rules as they apply to lyrics). Keep lyrics-specific machinery (elision, restored target for the tagger, Spotify spans, formulaic lines).
- **Output:** `config/wsd/models/es-lyrics-v16-1.json` (create; do not overwrite v7). Sign-off when leftovers are edges.
- Free test until v15/GRAFT exist: re-read v7 lyrics assignments / audit bundles; do not run a production lyrics WSD; do not harvest speech.
- Do not: block FUSE/GLASS; implement “the next run” from v12 speech; activate a lyrics release in a quick look; treat Czech-no-tagger as MWE.

### SETLIST — live playlist study (UI, not lyrics WSD)

**This chat is SETLIST.** Production Music & lyrics path from a playlist the learner is listening to now. Not published-artist catalogs. Not VERSE.

Paste into that chat:

> This chat is **SETLIST**. Read `CHAT_ROADMAP.md` through SCAR, then only `docs/runbooks/live-playlist.md`. Finish the production live-playlist path: Spotify playlist → lyrics → Fluency persist → study deck. Do not harvest. Do not WSD. Do not merge Live playlist with “Match a Spotify playlist”.

- Job: learner picks Live playlist, Spotify songs resolve on screen, lyrics save to the Fluency worker for a named user, a naive speech-overlay deck opens in place.
- **Output:** that path working on the live GitHub Pages app. Brief is `docs/runbooks/live-playlist.md`.
- Do not: harvest; run lyrics WSD; merge the three music picker rows; treat Daily Mix 403s as the product; reopen Genius/dump research.

---

## Ground rules for every chat

- `--language` defaults to `fr` in the CLI. Pass `es` / `pt` / `cs` every time.
- Audit chats (NEEDLE, SIEVE, SWEEP, VERSE): grow the sample; **stop only when the signed-off output table in “Audit chats only” exists.** Plant chats do not audit.
- Provider ≠ language. Parity means SpanishDict **and** Wiktionary, not “other languages later.”
- `git status` before commit; only your paths. No conjugation pickles, no `verbecc.log`.
- Do not read `flashcards.js` or `style.css` in full.
- Absence is declared. A run does not record what it did not verify.
- Concurrent chats are normal. FUSE must not edit files SIEVE owns without saying so; MILL owns the lab v14 run; KILN owns the 10k production run dir.

## What success looks like

| Milestone | You can point at |
|---|---|
| After NEEDLE | `*-v13-1.json` (done) |
| After FUSE | first `raw/mwe/` snapshots + `*-v14-1.json` + `overlays.py` (done) |
| After SIEVE | signed-off overlay + `*-v14-1.json` (redo; draft on disk is not this) |
| After MILL | es/pt/cs speech decks from the v12 lab freeze + those MWEs |
| After GLASS | es/pt/cs speech decks from 10k supply + those MWEs |
| After SWEEP | `*-v15-1.json` or written “v14 stands” |
| After GRAFT | `raw/overlays/` snapshots (slang, fillers, lyrics expressions) |
| After VERSE | `es-lyrics-v16-1.json` (Bad Bunny stays v7 until that ships) |

---

## How to keep this process (next campaign)

This file is the **switchboard**, not a diary. The migration plan stays `docs/ROADMAP.md`.

1. **One named chat, one job.** Codename in the index. First paste: `This chat is NAME. Read CHAT_ROADMAP.md through SCAR (or the current incident), then only your section.`
2. **Incident at the top** (SCAR). Every later chat reads why the last production run is not to be copied.
3. **Audit vs plant.** Audits grow a sample and sign off a **new version file**. Plant chats run that version. Do not mix.
4. **Outputs are paths.** A chat is unfinished until the table row exists. Create files; do not overwrite the previous profile.
5. **Long briefs live beside the data** (`Fluency-Workspace/raw/surfaces/…_PROMPT.md`). This file only points.
6. **When the campaign ends**, add a new incident if something went wrong, archive old codenames as Done, add the next index rows. Do not start a parallel undocumented chat for the same job.
7. **After you edit this file**, copy it to `../Fluency-Workspace/raw/surfaces/DECK_CHAT_ROADMAP.md` so workspace-only agents see it.
8. **Open** is `OPEN.md` (shipped, still imperfect). **Later** is `LATER.md` (eventual direction). Neither is a WSD step. Name a non-WSD chat in this file only while it is running (today: SETLIST).
