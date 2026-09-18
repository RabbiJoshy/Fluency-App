# Speech decks → lyrics: chat roadmap

Repo `Fluency-Next`. Workspace `Fluency-Workspace`. Old `Fluency/` is read-only.

**UI / app chats are usually not a row in this file.** They do not harvest, WSD, or compose decks unless this roadmap **names them as a blocker** (e.g. empty study sets after a release). They **should still read SCAR and the freeze / version index** so product work matches what is shipping (display-v4, MWEs on the component card, v13 vs v14). Do not invent a speech-pipeline job from a settings tweak.

Named UI exception: **SETLIST** (live Spotify playlist → lyrics → Fluency persist → naive study deck). Brief: `docs/runbooks/live-playlist.md`. Not VERSE. Not “Match a Spotify playlist”.

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
| **MILL** | v14 lab decks | Run signed-off v14 on the **current** freeze. New run id; remaining embeds; compose; activate if Joshua says. | Lab sentences + declared spend | Ready to open (after SIEVE) |
| **QUARRY** | 10k supply | Correct 10k pools → new prewsd. `--supply-only`. | Plant (harvest only if pools missing) | After MILL (or skip if 6k/4k v14 is enough) |
| **KILN** | v14 WSD on 10k | Embed **new** strings; full-deck WSD with MWEs on. | Plant | After QUARRY freeze exists |
| **GLASS** | v14 10k decks | Import bundle, compose, validate, activate the 10k speech decks. | Plant (no model) | After KILN |
| **SWEEP** | v15 | Audit the **shipped v14** decks, including MWE. | Lab on **v14** freeze | After first v14 ship (MILL or GLASS) |
| **GRAFT** | lyrics overlays | Collect slang, fillers, and lyrics MWEs/words into overlay snapshots. | Lab / curation | After SWEEP (before VERSE) |
| **VERSE** | lyrics **v16** | Rebase on SWEEP (v15) + GRAFT overlays; lyrics WSD v16. Bad Bunny lyrics stack is **v7**. | Lab first, plant later | After GRAFT; may sit idle until then |
| **SETLIST** | live playlist UI | Spotify playlist → LRCLIB → worker persist → naive speech-overlay deck. No WSD. | UI | In progress (brief `docs/runbooks/live-playlist.md`) |

**Hold.** Redo SIEVE when Joshua signs this sequence. Then MILL. QUARRY is the later 10k expansion, not a blocker for seeing v14.

KILN waits until QUARRY’s freeze exists. Do not call the v12 freeze “v14 production 10k.”

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

1. **NEEDLE** already tuned the *word* menu (abstain when unlicensed). MWEs were parked on purpose.
2. **LOOM** (optional, parked) would run that word-menu on the same freeze and ship a v13 deck *without* idioms. Skip; wait for v14.
3. **FUSE** built the candidate idiom lists and wiring.
4. **SIEVE** watches those phrases on the frozen v12 sentences and signs off which ones pass (the filter). Also makes sure a winning phrase can actually publish. Not a deck.
5. **MILL** runs that signed-off v14 on the same v12 freeze (new run id; remaining embeds) and can put it on the app at today’s card counts.
6. **QUARRY** is the first time you care about “the 10k files.” New run id, named pools, `--supply-only`. New freeze. Different cap-30 set than v12. Expected. Optional if MILL’s 6k/4k v14 is enough for now.
7. **KILN** pays Gemini only for sentences that QUARRY freeze has and the cache does not. WSD with v14 profiles + SIEVE’s inventory.
8. **GLASS** puts that 10k run on the app as the v14 speech decks.
9. **SWEEP** (v15) reads those decks the way NEEDLE read v12: sample, pattern, small change. Now the menu *includes* MWEs, so idiom mistakes are in scope.
10. **GRAFT** collects domain-specific MWEs and single-word extra senses (Caribbean slang, reggaeton idioms, conversational fillers, elided locutions) into structured overlays via `fluency.wsd.overlays`, before lyrics WSD disambiguation.
11. **VERSE** is the lyrics WSD chat. Rebased on speech v15 (SWEEP) + domain overlays (GRAFT), producing **lyrics WSD v16**. Do not treat speech v12 as the method to ship.

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

- Job: new run on the v12 card set (`--supply-only` if you materialise). `wsd_execute` with `--prewsd` = the `-v2` dirs in the freeze section, `--profile-id *-v14-1`, `--multiword-inventory` = **SIEVE’s signed-off overlay**. Remaining sentence embeds after 2026-09-17: es 0, pt ~16k, cs ~15k (recount with `--offline-only`; the overlay may shrink this). Then `pipeline wsd-import`, compose, validate; activate only if Joshua says.
- **Output:** imported stage 04 on the new run + (if activated) live v14 speech decks at current card counts. Display still SENTENCE_FLOW.
- Free test: `--offline-only` must print the miss count and refuse before Gemini. Confirm you did not write a 6k ledger over the 10k inventory. Confirm the overlay path.
- Do not: harvest; skip `--supply-only`; start QUARRY; audit membership (that is SIEVE); treat `es-v14-freeze.json` as importable into the v12 run id

### QUARRY — 10k supply, new freeze

**This chat is QUARRY.**

- Job: for es, pt, cs: named 10k pools (`fluency pools list`). If a pool is missing, harvest **that** source into a **new** run id — never `LATEST_V11`. `condition_pools`. `materialise_surfaces --workspace $W --language LANG --run-id LANG=<run-id> --supply-only`. Freeze **this** run’s prewsd as pairs v2 (POS column present; fill tags before KILN or accept spaCy on `null`). Print `--dry-run` first.
- Free test: dry-run; `prewsd.verify()`; confirm ledger row count still 10k after materialise; confirm you did not write a 6k ledger; confirm `pairs.json` is `prewsd-pairs/v2`.
- Do not: audit idioms here; call Gemini; run full WSD; skip `--supply-only`

This is the step that **intentionally** diverges from v12’s sentence set.

### KILN — embed deltas + v14 WSD

**This chat is KILN.**

- Job: `wsd_execute` with `--prewsd` = **QUARRY’s** freeze (not the v12 `-v2` lab dirs), `--profile-id *-v14-1`, `--multiword-inventory` = **SIEVE overlays** (`mwe-*-2026-09-17-v14-sieve/`), `--execution-cap 30`. Gemini only for texts missing from the npz cache. POS from pairs when frozen. Then `pipeline wsd-import` (stage 04 reads assignments, not the bundle file sitting in `raw/wsd/`).
- Free test before spend: count uncached strings; print projected units; `--offline-only` on a **tiny** sample must refuse or no-op paid calls.
- Do not: harvest; materialise without `--supply-only`; reuse v12 prewsd and call it v14 production

### GLASS — v14 decks on the app

**This chat is GLASS.**

- Job: compose speech releases from KILN stage 04; validate; activate. Display still SENTENCE_FLOW (WSD-labelled ticks; one canonical per meaning on that card). If MILL already shipped v14 on the 6k/4k freeze, this is the 10k replacement, not a second first-v14.
- Free test: `fluency release validate`; load study sets locally (empty-set bug was skinny `meanings: []` — do not ship that).
- Do not: change WSD; “quick harvest” to fill ticks

### SWEEP — v15 audit of shipped v14 (MWEs in scope)

**This chat is SWEEP.** Audit chat: grow the sample on the **shipped v14** freeze (MWEs in scope). Output is **v15** (`*-v15-1` or written “v14 stands”) when leftovers are edges. Joshua runs full v15 after you sign off.

- Job: NEEDLE-style audit **on the shipped v14 freeze and v14 assignments** (MILL’s lab decks or GLASS’s 10k, whichever is live). Idiom mistakes count. Word-menu regressions count.
- **Output:** `config/wsd/models/{es,pt,cs}-v15-1.json` **or** written “v14 stands”, plus leftover list. Joshua runs full v15 only after that.
- Free test: `--prewsd` of the **GLASS/KILN run**, `--offline-only`. Not the live CDN copy.
- Do not: harvest to “see more MWEs”; start lyrics method here; reopen display-v4 archaeology

### GRAFT — lyrics & slang sense-menu overlays (before VERSE)

**This chat is GRAFT.** Domain & slang collection chat before lyrics WSD.
- Input Dossier: `docs/research/graft-source-dossier.md` (read this research dossier first for vetted candidate sources, taxonomy, and coverage before building snapshots).

Paste into that chat:

> You are **GRAFT**. Read `CHAT_ROADMAP.md` through SCAR, then only GRAFT. First, read `docs/research/graft-source-dossier.md` for the vetted source inventory and taxonomy. Your job is to collect domain-specific multi-word expressions and single-word extra senses (slang, regionalisms, conversational fillers, elided locutions) into structured overlays via `fluency.wsd.overlays` before VERSE runs lyrics disambiguation.

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

