# Chat roadmap

Repo `Fluency-Next`. Workspace `../Fluency-Workspace`. Old `../Fluency` is read-only.

This file is the **switchboard**: what is open, which chat owns it, and the
rules every chat follows. It is not a diary. Completed jobs and the historical release snapshot are in
[the completed-work archive](docs/archive/chat-roadmap-completed-2026-10-14.md). The campaign history (NEEDLE →
MIRROR, every card, brief and paste) is archived at
`docs/archive/chat-roadmap-2026-10-04.md`. Read it only when a task names an
old codename.

**Every named chat opens with:**

> This chat is **`<CODENAME>`**. Read `CHAT_ROADMAP.md`, then only your row.
> (UNISON chats are `UNISON-1`, `-2`, `-3`; their row points to their brief.)
> Do not do another chat's job.

A chat that is not named here (UI polish, a bug) does not need a row. It must
not start a harvest, WSD run or release from a settings tweak.

After editing, copy this file to `../Fluency-Workspace/raw/surfaces/DECK_CHAT_ROADMAP.md`.

## Current direction (2026-10-14)

Finish a dependable Spanish/Portuguese speech release first. The source, WSD,
merging, first-pass verb English, cognates and study-session campaigns are closed;
do not restart HEADWAY, SEAM, TAGLINE, TERSE-2 or SETWISE just to release.

Recommended finish order:

1. Complete the account/sign-in and progress migration already being implemented
   in **Find standard password options**. Coordinate its migration with UPKEEP;
   do not run competing repairs. Live access and new destination accounts remain
   unresolved in that chat. Preserve the original snapshots and review concrete
   repair totals before applying live changes.
2. Finish UPKEEP's remaining inventory, state/scheduling checks and safe repairs;
   use STEWARD to verify admin/semiadmin roles and precise example flagging.
3. Run SHOWCASE against the final es/pt card UX, including grammar-word blocks,
   companion navigation, partly known meanings and Saved phrases.
4. Review the final staging build on desktop and a physical phone; confirm the
   production “que” case with actual saved progress, account sync/resume and the
   intended deck/assets. Recent card fixes and Saved/music UI are reported live
   by their owning chats. Older staging-only reports need checking against the
   final build, not automatic promotion of an old staging receipt.

Keep HINGE's visible accuracy checks (junk phrases, role wording, reflexive
consistency) in this review if a real es/pt defect is found. Full labeller migration,
new languages and Turbo need not delay the speech release. If any deck is rebuilt,
retaining its grammar-word labels is a release requirement.

## Open

Only unfinished work is listed below, separated by release relevance. A completed
assistant turn does not close a job that still awaits review, migration or a fix.
The three groups are planning categories, not instructions to start another chat's work.
Unnamed UI fixes can remain in their existing chats without becoming pipeline jobs.
Completed work and permanently paused ACCORDION live in the archive linked above.

### 1. Spanish / Portuguese — final fixes

| Codename | Job | Status | Read |
|---|---|---|---|
| **SHOWCASE** | Ongoing / standing maintenance: keep the learner Tutorial (`app/js/tutorial.js`), visitor About modal (`#aboutProjectModal`), and interactive Walkthrough bug-free, accurate, and completely aligned with the latest card back layout and engine capabilities. Ensure replica cards match live card behavior (reveal, flip, spotlight rings, example cycling, rarer uses, Smart Skip, lyrics flow) across supported languages without regressions. Does not end; stays open as a standing UX alignment track. | Ongoing / standing maintenance. Pass completed 2026-10-13 (`f7eca56d`: tutorial copy tightened <= 180 chars, mobile full-bleed & unclipped scaling, walkthrough pin overlap fixes, About demo grid repair; verified on staging). Stays open. | `app/js/tutorial.js`; `app/js/routes.js`; `app/index.html`; `docs/decisions/0023-tutorial-walkthrough-about.md`; `docs/NOMENCLATURE.md` |
| **UPKEEP** | Audit and clean up historical, invalid and deprecated learner-database states across all users, production and staging. Establish the current schema and supported states first; distinguish valid history and compatibility data from obsolete active state. Start with explicit stage 0 plus a correct answer and no unresolved mistake, then inspect progress identities, settings, counts/timestamps, event/state consistency and sync watermarks for other verified legacy problems. Reconcile the Worker/client scheduling rules and identify any client or write path that can recreate invalid states; the cause of the existing stage-zero rows is unproven. Snapshot affected data, report per-user counts and concrete before/after examples, and prepare conservative, repeatable repairs that preserve card identities, answer counts and genuine historical evidence. JST was previously to remain untouched: obtain Josh's explicit approval for the concrete JST repair before applying it. Preserve its original snapshot and keep JOSHUA's deliberate synthetic scheduling distinguishable from genuine review history; do not rewrite append-only events or delete valid history merely because it is old. Verify current app loads, scheduling and full/delta sync after repairs; document every checked category, remaining compatibility requirement and unverified area rather than claiming all legacy data is gone from a partial audit. Follow AIRLOCK for app changes. | Joshua migration implemented in production 2026-10-14: 10,321 component rows verified, 8,695 known with a separate 28 October review date, 1,626 needing practice. Counts, histories, flags and settings unchanged. Shared client/Worker policy, answered-stage-zero guard and stale retry protection deployed; 291 tests pass. Actual read-handler full/delta checks pass against the live after-snapshot; physical phone round-trip unverified. JoshuaBackup/JP new logins not yet created; their and DRG archives remain intact. Broader historical counter differences preserved rather than inventing events. Evidence: workspace `audits/upkeep-20261014/report.md`. | `backend/worker/src/store.js`; `backend/worker/src/profiles.js`; `backend/worker/migrations/`; `app/js/progress.js`; `app/js/auth.js`; `app/js/sync-queue.js`; `app/js/offline-db.js`; workspace `research/jst-to-joshua/` (original snapshot, payloads and `verification_2026-10-10.json`); `docs/INVARIANTS.md` |
| **STEWARD** | Restore and verify the intended account privileges after account deletion/recreation: the test account has full admin access; Josh's everyday account and JP retain the normal learner experience plus extra flagging privileges (semiadmin). Audit the current permission model and surviving accounts/backups first; confirm which recreated identities own each role rather than assuming a username or copying full admin access onto a learner account. Coordinate with the account/sign-in migration and UPKEEP, preserve backups, and cover accounts not yet recreated. Make flagging easier, including a clear action to flag the currently displayed example as a WSD / wrong-meaning assignment issue rather than only flagging the word generally. Capture the exact example, target word, assigned sense and deck/release context; keep general word flags available. Verify ordinary-user, semiadmin and admin behavior in both the UI and backend, and that privileges survive sign-in/recreation as intended. | Not started. Requested by Josh 2026-10-14. Release follow-up; role/account mapping must be checked against the recreated accounts. | REPO_MAP.md; app/js/auth.js; app/js/passwordless-auth.js; app/js/flags.js; backend/worker/src/session-auth.js; backend/worker/src/profiles.js; UPKEEP row |

Other open release follow-ups in existing chats:

| Chat | What remains |
|---|---|
| **Find standard password options** | Account/sign-in implementation and approved migration plan; active. Coordinate with UPKEEP. |
| **Fix companion card navigation** | Confirm the partly known “que” case against actual production progress. Card fixes are live; timed-session endpoint design remains deferred. |
| **Refine vocabulary choice page** | Latest turn failed; keep open until its requested changes are confirmed finished. |
| Staging UI review chats | Confirm reviewed changes are present in the final release before closing staging-only threads. Their last reports alone do not establish promotion. |

#### Follow-ups that need not block the release

| Codename | Job | Status | Read |
|---|---|---|---|
| **INFLECT-3** | Second look at the English on es/pt verb rows after Josh has used the app; start from real cards on staging, not from `measure.mjs` (it counts cue strings; the card back already lifts definition brackets into sub-rows, which INFLECT-2 learned the hard way and reverted). Hardest cases, with sizes on es r5 / pt r3 (card/verb pairs): (1) **Subjunctive-only forms** (*sea*, *vaya*, *tenga*; pt *seja*, *vá*, *tenha*, *quiser*; 690 es, 611 pt). Josh rejected "that" and "may" because not every subjunctive is a *que*-clause; the row keeps plain present/past. Left: the "(s)/(es)" notation (*vaya* "I/he/she go(es)") and two-clause rows (*sea* "I am / he/she is"), and *-ra* forms that mean "would" (*quisiera* "I/he/she wanted", *pudiera*). The row cannot see which use it is; only the example sentence can. (2) **One row, several readings**: *vamos*, *mira*, *ven*, *haz* are a statement, a command or both; the two-thirds rule and the on-screen example decide, and *mira* shows "look!" beside "he/she watches" on one card. A per-example row is the real fix. (3) **Rows with no English**: pt *tenho/temos/tens* show the note "See ter de, ter que." and *vou/vai/vamos* "will; to be going to; forms the future tense" (99 pairs, pt only); es and pt modals (*puedo* "can", *debe* "should", 153 es, 164 pt rows) have no person. Wrong English first, so these were left. (4) ***gustar*-type verbs**: INFLECT-2 made *gusta* "it pleases", *encanta* "it delights", *duele* "it hurts"; true to the grammar but stiff, because *me gusta* is "I like it" and the row cannot carry *me*. Check how it feels. *importa* still shows SpanishDict's "he/she cares/minds" (a wrong-subject sense). (5) **Participles** read as bare "done", "been", "seen", "died" (*muerto*): right as participles, but cards use them as adjectives ("dead", "tired"). (6) **Commands ending on a bare preposition**: *mira* "look at!", *escute* "listen to!", *llévate* "take with one!" (26). (7) **Clock senses** with a first-person reading (pt *era* "I/it was"). Not English, so not here: wrong meaning or headword on the card (es *vamos* "to be" → "we are", *hace* "to think"; pt *vem/venha/veio* filed under `ver`, *tivesse* under `estar`: HEADWAY/TAGLINE), attached-pronoun infinitives (*hacerlo*, *verte*, 512 es pairs: companion cards), gloss length (TERSE-2). | Not started. Requested by Josh 2026-10-11 for when he returns from using the app; no deadline. Baseline is staging after INFLECT-2 (`reverse-cues.js` with the "it" rule). | `research/inflect/README.md`; `app/js/reverse-cues.js` (`chooseTableReadings`, `finiteEnglishCue`, `compressPronounCues`, `thirdPersonSubject`); `app/js/card-metadata-pills.js` (`projectWiktionaryGloss`: where definition brackets leave the row) |
| **HINGE** | Follow-up to the grammar-word labels shipped by CASCADE-WSD (rule labellers: parser + Wiktionary phrases, verb patterns, pronominal verbs; es/pt/cs/nl). **Make it permanent:** (1) move `research/cascade/trouble-words/labeller_*.py` into `src/fluency/` with tests using the hand-labelled sets as regression; (2) produce labels inside the pipeline (WSD stage or release builder) instead of the `fw-overlay` add-on, and until then make a es/pt/cs rebuild refuse to drop them; (3) rebuild Czech properly (labels were copied onto old-format rows without validation). **Accuracy:** (4) Spanish source: check whether our SpanishDict data has phrases, pronominal verbs and verb patterns, then choose SpanishDict or Wiktionary; (5) spot-check the Wiktionary phrases that actually appear on cards for junk; (6) confirm labeller *se* never contradicts the reflexive tagger; (7) native-speaker or blind check of a sample per language. **App:** (8) grammar-word block on the word page (`#/xx/w/<word>`); (9) review near-threshold cards and the 60% cut-off. **Docs:** (10) decision record (what qualifies, 60% cut-off, rules before WSD, what is Wiktionary vs handwritten) and NOMENCLATURE terms (grammar word, role, phrase). **Turbo-linked (may move to TURBO):** (11) French labeller, needed for the French/Turbo rehearsal; (12) labels for lyrics/artist decks and Turbo, deciding where the parser runs. | Not started; the grammar-word release is in production (2026-10-13). Listed by Josh 2026-10-13. Display-only stopgaps already live (`469908f6`): Wiktionary notes/pointers ("Used other than figuratively…", "spelling of…") hidden as phrase meanings, "(+ verb)" preposition chips merged. **Parked, uncommitted:** a labeller-level fix (`research/cascade/trouble-words/gloss_filter.py`, idiom keep-lists, tag `fw2` in `fw-overlay/overlay.py`) with fw2 labels in `<workspace>/raw/wsd/{es,pt,cs}/fw2-function-word-labels.json` (es 80 / pt 76 / cs 5 labels changed vs fw1, Dutch unchanged); review before using. | `research/cascade/README.md`; `research/cascade/trouble-words/`; `research/cascade/fw-overlay/`; `app/js/function-word-card.js` |

A further TERSE-2 pass was requested for after release, but has no defined scope.
The shipped first pass remains closed; define a concrete follow-up before reopening.
The timed-session endpoint design also remains deferred in **Fix companion card navigation**.

### 2. Turbo / lyrics mode

| Codename | Job | Status | Read |
|---|---|---|---|
| **TURBO** | Live Spanish pipeline for a user-uploaded Spotify playlist: clean, normalise, tag and run fast WSD in the client/worker, then build a study deck immediately. Must not block the UI thread or break card progress. | **In progress** (`app/turbo/`). The last big piece of the app. Powered by the unified WSD decision logic and asset profile `config/wsd/models/es-turbo-v1.json`. Playlist ingest, worker and UI work continue. | `docs/runbooks/live-playlist.md` (SETLIST, which it builds on) |
| **TURBO-STREAM** | Design and build the lightweight online WSD ingestion pipeline for user-imported song playlists and custom decks (up to 100 songs / ~5,000 polysemous words / ~15,000–30,000 POS tags / ~50,000–100,000 WSD evaluations). Leverage single-POS menu bypass to skip 60%+ of tokens from POS tagging, sequential/lightweight tagging (e.g. Stanza BiLSTM or equivalent worker-compatible tagger at ~250–350 sent/sec), exact-text embedding cache lookups, and batched/multiprocessed pipeline execution to complete 100-song ingestion in under 2 minutes. Support progressive streaming updates (deck unlocks cards as songs finish) so the user never blocks waiting on the full import. | Not started; performance/progressive-delivery subtask of TURBO, not a separate pipeline. Hypothesised 2026-10-11 during TAGLINE POS and speed benchmarking. The under-two-minute goal, bypass proportions and throughput figures are hypotheses to validate end-to-end in the intended client/worker or service runtime, not established browser benchmarks or a mandated architecture. **Idea to discuss, not decided (raised 2026-10-12):** a declared function-word class. A per-language declared list (*que, de, se*, clitics, articles, contractions) might get no per-example LLM sense online: the card would show a fixed summary plus its phrase senses (*ter que*, *tener que ver con*), and those words would be disambiguated offline instead (~1,000 examples across ~30 words by LLM, minimal cost). Content words with idioms (*dar*) would stay in the cascade with a defined phrase list. Absence declared, not inferred (invariant 2). Josh wants to discuss it when TURBO-STREAM starts. **Turbo goal decided 2026-10-13 (CASCADE-WSD):** minimise sentences reaching WSD (menu-list surfaces only, clitics onto their base surface, grammar words by rules, example cap by senses and rank), one Qwen3-Embedding-0.6B embedding, LLM per word for the hardest few percent only; the French run is the Turbo rehearsal. Read `research/cascade/README.md` (Turbo goal) first. The es/pt hard-word router and DeepSeek spot check, with three open items for the hard-word list (noise check, exact-duplicate senses, retry), are in the same README. Evidence: `research/cascade/`. | `app/turbo/`; `docs/TAGLINE.md`; `CHAT_ROADMAP.md` row TURBO |

### 3. Other languages — reach parity

Bring the existing languages up to the final Spanish/Portuguese standard. Begin
with CONVOY's per-language gap audit; share the final es/pt acceptance checklist.
Keep Czech conjugation English and reflexives in their dedicated jobs. HINGE owns
shared grammar-word infrastructure; do not duplicate that work per language.

| Codename | Job | Status | Read |
|---|---|---|---|
| **CONVOY** | Bring Czech, Finnish and French up to the Spanish/Portuguese standard on everything, so no language lags the two Josh works on. Audit first: per language, list what es/pt have that it lacks, then rebuild each on the current engine and pipeline. Historical gap inventory (2026-10-10; revalidate against the Release snapshot before work): (1) none is on UNISON's single engine or the decision 0030 metadata contract; `scripts/check_stale_engine.py` says "OK" only because each is measured against its own old profile (cs-v21-1, fi-v21-1, fr-v7-1), and it reads es/pt as v22 from workspace `active.json` while the app serves v23; (2) Merge Lemmas lists were rebuilt as a quick patch (verbs merge again), but nouns stay separate because the plural/singular check (decision 0029) has only run for es/pt: 3,884 cs and 616 fi noun cards. Run `scripts/refresh_noun_merge_metadata.py` with a fresh Wiktionary menu, as pt did; (3) French is a 200-card stub (`fr-speech-v7-dual-metadata-v5-20260918`) whose senses carry no headwords, so Merge Lemmas has nothing to merge; (4) the phrase-lemma fix (11276edc) reaches them only when rebuilt. Czech reflexives stay with MIRROR-CS; Czech verb English stays with INFLECT-CS. | Not started. Requested by Josh 2026-10-10. es and pt remain the priority; this row keeps the rest level. `tests/app/test_merge_exceptions_current.py` blocks any deploy whose live deck lacks a current Merge Lemmas list, so each rebuilt deck needs its list rebuilt. | `docs/unison/PROGRESS.md` (what es/pt received); `docs/decisions/0029-noun-number-merging.md`; `docs/decisions/0030-sense-metadata-and-display-contract.md`; `scripts/check_stale_engine.py`; `scripts/build_merge_exceptions.py` |
| **BRIDGE-2** | Audit and fix verb cognate skipping and known-language selection, building on BRIDGE rather than duplicating it. A shared or similar infinitive must not automatically make every conjugated form skippable: check equivalent grammatical readings (person, number, tense, mood, and aspect where relevant), irregular forms and false friends. Investigate a smarter, conservative infinitive/regular-paradigm rule as an option, not an already agreed policy; missing morphology must not silently count as a match. Prioritise Czech/Polish and Spanish/Portuguese examples, with English as a regression control. Reproduce the setup bug where choosing Czech then being asked which other languages are known omits Polish even though Polish is available in cognate skipping. Align onboarding with the supported known-language/cognate options, including languages without a study deck. First establish what BRIDGE already handles and record only the remaining gaps; preserve target progress and the distinction between knowing a lemma and knowing a particular form. | Not started. Requested by Josh 2026-10-14. Other-language parity track; any confirmed es/pt false skips also belong in the final release review. | docs/BRIDGE_IMPLEMENTATION.md; app/js/cognates.js; app/js/language-profile.js; app/js/learning-profiles.js; tests/app/test_cognate_every_sense.py; tests/app/test_learning_profiles.py; config/cognates/ |
| **INFLECT-CS** | Czech verb rows show wrong or no English. INFLECT fixed this for es/pt; Czech was measured but not fixed. Only 1,356 of 3,035 Czech card/verb pairs get inflected English (es 82%, pt 96%), and some that do are wrong: (1) a perfective verb's "present" is a future, but the table does not record aspect: *řeknu* shows "I say" (should be "I'll say"), *uvidíme* "we see", *přijde* "he/she comes"; (2) the table stores the Czech past (l-form) in its participle slot, so it gets English participle wording: *udělal* "done" (should be "did"), *přišel* "come" ("came"); (3) the app serves Czech an old table (`cs-speech-v12-4000x10-conj`, 404 verbs, present and command only, because `kaikki_conjugations.py` reads Czech that way), so 503 pairs have no table and 1,096 pairs never match (feminine/plural past *všimla*, *umřeli*; negated *neznáme*; future *bude*). The fix is mostly a new Czech conjugation table from Wiktionary for the live deck's verbs, with full past forms and aspect, attached as a successor release (`conjugation_attach.py`, no harvest or WSD), then a small change in `reverse-cues.js` (perfective present → future, l-form → simple past, *ne-* → "don't/not"). Stage it; production needs Josh's approval. Reflexives stay with MIRROR-CS. | Not started. Requested by Josh 2026-10-11; measured 2026-10-11 on `cs-speech-v22-10000x30-slim` with `research/inflect/measure.mjs`. | `research/inflect/README.md`; `app/js/reverse-cues.js` (`conjugationTableCue`, `TENSE_KIND`); `src/fluency/enrichments/kaikki_conjugations.py` (`FULL_PARADIGMS`); `src/fluency/release/conjugation_attach.py`; `app/js/flashcards-conj.js` (Czech table shows Present and Imperative only) |
| **MIRROR-CS** | Extend the reflexive/pronominal tagger (`src/fluency/reflexive/`) to Czech: 999 of 10,000 cs cards have both a plain and a *se*/*si* meaning. A research chat, not a port: Czech *se*/*si* are second-position clitics with one form for every person, so the person-agreement method behind ~99% in es/pt does not carry over. Needs a Czech parser (Stanza or UDPipe; **ask Josh before downloading**) and new hand-labelled Czech gold sets. No other language is worth extending to (fr deck too small, no pl deck, nl unpublished). | Not started. | `research/reflexives/FINDINGS.md`; reuse the eval harness in `research/reflexives/` |
| **ROLLCALL-2** | Full retrospective audit of the complete language readiness checklist across all live and candidate languages (es, pt, cs, fi, fr, nl) against final production standards. Audit only: no harvests or rebuilds. | Not started. Positioned after speech mode and next-language pilot are proven end-to-end. | `docs/LANGUAGE_COMPLETION_CANDIDATE.md`; `docs/NL_FI_2000_RELEASE.md`; `docs/INVARIANTS.md`; app configs |

#### Dutch release (expansion within the language track)

Dutch is expansion rather than parity for an already shipped speech language.
Keep its existing candidate and readiness review separate from CONVOY.

| Codename | Job | Status | Read |
|---|---|---|---|
| **DUTCH** | Ship the Dutch 2,000-card speech release: review the 122 ledger surfaces, finish the readiness checklist, activate. | Not started. Candidate `nl-speech-v1-2000x5-3-candidate` exists, inactive. | `docs/NL_FI_2000_RELEASE.md` → Dutch; `docs/LANGUAGE_COMPLETION_CANDIDATE.md` |

## Rules for every pipeline chat

These exist because of **SCAR**: the v12 production run rewrote the 10k ledgers,
re-harvested when pools existed, and did not pin the artifacts that chose its
sentences. Full account in the archive.

| If you are… | You must… |
|---|---|
| Materialising a deck smaller than the language inventory | `--supply-only` |
| Starting a production run | `--run-id` on an **existing named pool** (`fluency pools list`) |
| Auditing WSD quality | Read **that run's** `stages/04_wsd_assignments/` and its frozen `prewsd/<run-id>/`, not the live app or a ledger another session touched |
| Unsure whether to harvest | **Do not harvest.** Use the freeze already on disk. |

- `--language` defaults to `fr` in the CLI. Pass it every time.
- Audits grow a sample and sign off a **new** version file; plant chats run that
  version. Do not overwrite a previous profile; old profiles are release provenance.
- Provider ≠ language. Parity means SpanishDict **and** Wiktionary.
- Absence is declared. A run does not record what it did not verify.
- `git status` before committing; stage only your paths.
- Long briefs live beside the data (`../Fluency-Workspace/raw/surfaces/…`). This file only points.
