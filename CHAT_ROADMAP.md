# Chat roadmap

Repo `Fluency-Next`. Workspace `../Fluency-Workspace`. Old `../Fluency` is read-only.

This file is the **switchboard**: what is open, which chat owns it, and the
rules every chat follows. It is not a diary. The campaign history (NEEDLE →
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

## Current direction (2026-10-11)

**Priority sequence:**
1. **Close out WSD & data foundations on Spanish & Portuguese.**
2. **UI & study flow polish in parallel (can proceed in any order without blocking).**
3. **Pilot New WSD Architecture (Cheap Embeddings + Tiny LLM Cascade) on next language (Dutch or French).**
4. **Multilingual parity & expansion (deferred to the end).**

---

### Track 1: WSD & Language Data Sequence (Strict Dependency Chain)
These chats directly affect assignments, menus, and deck semantics. Run in this order:

| Step | Codename | Status / Focus |
|---|---|---|
| **WSD-1** | **HEADWAY → SEAM** | Complete for Spanish/Portuguese (confirmed by Josh, 2026-10-11). Remaining source adjudications and other-language merging audits are deferred follow-ups; do not repeat the completed campaigns. |
| **WSD-2** | **LITERAL-GROUND** | Staged 2026-10-11 for review: candidate decks `pt-speech-v25-literal-ground-r4` and `es-speech-v25-literal-ground-r6` (only pt de/do/da/dos/das/em/no/na/nos/nas and es de/del re-run; all other cards identical to r3/r5). On 124 hand-judged changed sentences: 78 better, 7 worse where the card English changes. por/para/es a/al/en left unguarded (measured worse). LITERAL overlap fix verified on the sample, not rolled out deck-wide. Evidence: `research/literal-ground/README.md`. Production approval pending. |
| **WSD-3** | **Es/Pt Release Review** | Final staging audit of Spanish & Portuguese candidate decks together before production promotion. |

*(TAGLINE completed: Stanza pt tagger, soft evidence gating, single-POS bypass, pt-r3 active in production config, es-r5 and lyrics v20 deployed to staging.)*

---

### Track 2: UI & Interaction Polish (Prioritised for Speech Mode Launch)
TOUCHPOINT is complete. The remaining items are ordered by what should be done soonest to release Spanish & Portuguese speech mode:

| Priority | Codename | Focus / Role in Speech Launch | Status |
|---|---|---|---|
| **Done** | **TOUCHPOINT** | Code-led swipe and scrolling audit; fixes tested and staged. | **Complete** (staged, 252 tests pass). |
| **UI-1** | **TERSE-2** | Conservative trimming of long card-back definitions, with full original text available in the information dialog. | Implemented and verified on Staging (`78548470`; 261 tests pass). Awaiting Josh’s visual review; production promotion pending. |
| **UI-2** | **SHOWCASE** | Ongoing / standing maintenance: keep the Tutorial (`app/js/tutorial.js`), About section (`#aboutProjectModal`), and Walkthrough bug-free, aligned with latest card UX, and up to date across languages. | Ongoing / Queued. |
| *Parallel* | **SETWISE** | **Investigation**: evaluate whether changing study set selection (2 boxes vs 4 boxes, session length choice: 25 vs 50 cards) is a good idea. Can run in parallel; if approved, implementation would come before ACCORDION. | Investigation queued. |
| **UI-3** | **ACCORDION** | Rarer uses & nuances presentation on card back. | Collapsible lists live (`c94b87f8`); quick visual check. |
| **UI-4** | **INFLECT-3** | Second-look English polish on verb rows (subjunctives, modals). | Waiting for Josh's app usage on staging. |
| *Parallel* | **UPKEEP** | Learner DB legacy state cleanup (stage 0 rows, JST/JOSHUA). | Awaiting explicit approval; independent of speech launch. |
| *Parallel* | **TURBO / TURBO-STREAM** | In-client playlist ingestion & progressive streaming delivery. | In progress; song mode feature, independent of speech launch. |

---

### Track 3: Next Language Pilot (New WSD Architecture: Cheap Embeddings + Tiny LLM Cascade)
*Run after Track 1 is complete, before full-scale multilingual expansion.*

| Step | Codename | Focus |
|---|---|---|
| **PILOT-1** | **ROLLCALL-1** | Lightweight pre-flight readiness checklist for onboarding a new language (surface ledger, dictionary snapshot, sentence bank). Verify whether Dutch or French is ready to process first. |
| **PILOT-2** | **CASCADE-WSD** | Implement and test the Smart Cascade WSD architecture on the chosen pilot language (Dutch or French): (1) Monosemous bypass; (2) Pre-embedding ambiguity router / closed-class rule; (3) Cheap/fast vector embeddings for the 95% middle tier; (4) Selective escalation of the ~3–5% ambiguous tail to a tiny, fast LLM (DeepSeek/Qwen 1.5B–8B). Compare accuracy, speed, and cost against heavy embeddings. |

---

### Track 4: Multilingual Parity & Long-term Expansion
*Run after Speech Mode is complete and proven end-to-end.*

| Codename | Focus |
|---|---|
| **ROLLCALL-2** | Full multilingual audit of all shipped languages (es, pt, cs, fi, fr, nl) against final production standards. |
| **CONVOY** | Bring Czech, Finnish, and French up to full Spanish/Portuguese engine and metadata parity. |
| **INFLECT-CS** | Czech verb table Wiktionary attachment and natural English cues. |
| **MIRROR-CS** | Research Czech reflexive/pronominal clitic tagging (*se/si*). |
| **DUTCH** | Final activation and release of Dutch 2,000-card speech deck. |
| **BRIDGE** | Cross-language cognate exclusion (Spanish ↔ French, etc.). |

---

## Open

Everything open is listed here. If it is not in this table, it is either done (below) or an eventual direction (`LATER.md`).

| Codename | Job | Status | Read |
|---|---|---|---|
| **LITERAL-GROUND** | Combined surgical WSD safeguards: (1) **GROUND**: Strictly targeted fix for high-frequency closed-class function words (prepositions & particles: es/pt *de*, *a*, *en*, *em*, *por*, *para*). Closed-class function words have near-zero topical semantic content; pure sentence-level embedding similarity cannot reliably separate functional/governed uses from rare idiomatic senses (e.g. pt *de* "in (wearing)" winning on *lembrar-se de* by 0.006 margin). Add primary sense prior / minimum margin floor (0.025), syntactically governed-verb bypass, and active-card qualification threshold. (2) **LITERAL**: Audit WSD choices where supplied English translation determines which English gloss should be shown (e.g. "except" vs "except for"). Trace existing literal-gloss alignment corrector and translation overlap bonus on a small labelled sample (~20 cards). **Explicit non-goal**: Do NOT expand into wide open-class WSD or full-deck re-embeddings. Test on small labelled set, regenerate targeted menus ($0 spend), package candidate releases (`pt r4`, `es r6`), and stage for immediate review. | Ready to start. Combined 2026-10-11 by Josh to close out Spanish & Portuguese WSD safeguards together in one fast pass. | `src/fluency/speech/wsd_execute.py`; `src/fluency/wsd/runner.py`; `src/fluency/wsd/alignment.py`; `src/fluency/wsd/languages/`; `src/fluency/wsd/sampling.py` |
| **TERSE-2** | Shared client trimming keeps whole translations, usage restrictions and sense distinctions. Fixes broken parentheses (*galáxia*, *certidão*), preserves pre-reform spelling targets (*electricidade* → “pre-reform spelling of eletricidade”), and restores alternatives/negation (*que fosse* → “even; only”; Spanish “it’s not that”). Full original gloss/context and transformation provenance remain available in the information dialog. | Implemented and deployed 2026-10-11, commit `78548470` on `codex/terse-2`; shared Staging version verified in browser. 261 app tests pass. Audited pt r3 / es r5, including 30 longest distinct glosses and contexts per deck; Portuguese final glosses over 84 chars fell 140 → 94. Awaiting Josh’s visual review; production promotion pending. | `research/terse/README.md`; `app/js/card-metadata-pills.js`; [Staging review](https://fluency-staging.pages.dev/?ptRelease=pt-speech-v24-headway-r3-10000x30-slim&esRelease=es-speech-v24-headway-r5-10000x30-slim) |
| **SHOWCASE** | Ongoing / standing maintenance: keep the learner Tutorial (`app/js/tutorial.js`), visitor About modal (`#aboutProjectModal`), and interactive Walkthrough bug-free, accurate, and completely aligned with the latest card back layout and engine capabilities. Ensure replica cards match live card behavior (reveal, flip, spotlight rings, example cycling, rarer uses, Smart Skip, lyrics flow) across supported languages without regressions. Does not end; stays open as a standing UX alignment track. | Ongoing / standing maintenance. Added 2026-10-11 by Josh. | `app/js/tutorial.js`; `app/js/routes.js`; `app/index.html`; `docs/decisions/0023-tutorial-walkthrough-about.md`; `docs/NOMENCLATURE.md` |
| **ACCORDION** | Design pass on whether to show rarer uses & nuances inline via an accordion on the mobile card back vs keeping them off-card in the existing modal (`#rareUsesModal`). Core motivation: hiding rare senses prevents learner confusion, avoids cluttering the card with unimportant meanings, and shields against inaccurate rare WSD assignments. Mobile space is heavily constrained by the active example sentence and Anki grading bar. A pure-UI scale wireframe mockup was produced comparing both: [rarer_uses_accordion_mockup.html](file:///Users/joshuathomasamar/PycharmProjects/Fluency-Next/rarer_uses_accordion_mockup.html). Dedicated follow-up chat to decide and implement if approved. | Reconciliation/review needed. Original wireframe dates from 2026-10-09, but c94b87f8 (2026-10-11) already implements collapsible uses lists. Check current behaviour against the original aim and TERSE-2 before deciding what remains; full design acceptance is unverified. | `app/js/flashcards.js` (`renderSections`, `#rareUsesModal`); `app/css/style.css` (`.meanings-scroll`, `.meaning-row`); [Mockup](file:///Users/joshuathomasamar/PycharmProjects/Fluency-Next/rarer_uses_accordion_mockup.html) |
| **INFLECT-3** | Second look at the English on es/pt verb rows after Josh has used the app; start from real cards on staging, not from `measure.mjs` (it counts cue strings; the card back already lifts definition brackets into sub-rows, which INFLECT-2 learned the hard way and reverted). Hardest cases, with sizes on es r5 / pt r3 (card/verb pairs): (1) **Subjunctive-only forms** (*sea*, *vaya*, *tenga*; pt *seja*, *vá*, *tenha*, *quiser*; 690 es, 611 pt). Josh rejected "that" and "may" because not every subjunctive is a *que*-clause; the row keeps plain present/past. Left: the "(s)/(es)" notation (*vaya* "I/he/she go(es)") and two-clause rows (*sea* "I am / he/she is"), and *-ra* forms that mean "would" (*quisiera* "I/he/she wanted", *pudiera*). The row cannot see which use it is; only the example sentence can. (2) **One row, several readings**: *vamos*, *mira*, *ven*, *haz* are a statement, a command or both; the two-thirds rule and the on-screen example decide, and *mira* shows "look!" beside "he/she watches" on one card. A per-example row is the real fix. (3) **Rows with no English**: pt *tenho/temos/tens* show the note "See ter de, ter que." and *vou/vai/vamos* "will; to be going to; forms the future tense" (99 pairs, pt only); es and pt modals (*puedo* "can", *debe* "should", 153 es, 164 pt rows) have no person. Wrong English first, so these were left. (4) ***gustar*-type verbs**: INFLECT-2 made *gusta* "it pleases", *encanta* "it delights", *duele* "it hurts"; true to the grammar but stiff, because *me gusta* is "I like it" and the row cannot carry *me*. Check how it feels. *importa* still shows SpanishDict's "he/she cares/minds" (a wrong-subject sense). (5) **Participles** read as bare "done", "been", "seen", "died" (*muerto*): right as participles, but cards use them as adjectives ("dead", "tired"). (6) **Commands ending on a bare preposition**: *mira* "look at!", *escute* "listen to!", *llévate* "take with one!" (26). (7) **Clock senses** with a first-person reading (pt *era* "I/it was"). Not English, so not here: wrong meaning or headword on the card (es *vamos* "to be" → "we are", *hace* "to think"; pt *vem/venha/veio* filed under `ver`, *tivesse* under `estar`: HEADWAY/TAGLINE), attached-pronoun infinitives (*hacerlo*, *verte*, 512 es pairs: companion cards), gloss length (TERSE-2). | Not started. Requested by Josh 2026-10-11 for when he returns from using the app; no deadline. Baseline is staging after INFLECT-2 (`reverse-cues.js` with the "it" rule). | `research/inflect/README.md`; `app/js/reverse-cues.js` (`chooseTableReadings`, `finiteEnglishCue`, `compressPronounCues`, `thirdPersonSubject`); `app/js/card-metadata-pills.js` (`projectWiktionaryGloss`: where definition brackets leave the row) |
| **SETWISE** | **Investigation**: evaluate whether changing study set selection on the landing page is a good idea. Investigate comparing the current four 25-card progress boxes with two 50-card boxes or one level progress bar. Explore separating progress grouping from session length, with a visible 25-card / 50-card choice (roughly 5 / 10 minutes), a remembered preference, and immediate Study action. Assess trade-offs: user friction, psychological milestone size, resume behaviour, Smart Skip interactions, and saved-progress compatibility. Can be conducted in parallel as an investigation; if approved, implementation would come before ACCORDION. Bring concrete analysis and UX wireframe options to Josh before touching code. | Investigation queued. Requested by Josh 2026-10-11; two boxes with an inline session-length choice is an initial hypothesis to evaluate, not an approved redesign. Current four-box layout remains until decided. | `app/js/ui.js` (`renderRangeSelector` and study-set selection); `app/css/style.css` (`#step4`, `.study-set-dot`); `app/index.html` (Choose a Set) |
| **TURBO** | Live Spanish pipeline for a user-uploaded Spotify playlist: clean, normalise, tag and run fast WSD in the client/worker, then build a study deck immediately. Must not block the UI thread or break card progress. | **In progress** (`app/turbo/`). The last big piece of the app. Powered by the unified WSD decision logic and asset profile `config/wsd/models/es-turbo-v1.json`. Playlist ingest, worker and UI work continue. | `docs/runbooks/live-playlist.md` (SETLIST, which it builds on) |
| **TURBO-STREAM** | Design and build the lightweight online WSD ingestion pipeline for user-imported song playlists and custom decks (up to 100 songs / ~5,000 polysemous words / ~15,000–30,000 POS tags / ~50,000–100,000 WSD evaluations). Leverage single-POS menu bypass to skip 60%+ of tokens from POS tagging, sequential/lightweight tagging (e.g. Stanza BiLSTM or equivalent worker-compatible tagger at ~250–350 sent/sec), exact-text embedding cache lookups, and batched/multiprocessed pipeline execution to complete 100-song ingestion in under 2 minutes. Support progressive streaming updates (deck unlocks cards as songs finish) so the user never blocks waiting on the full import. | Not started; performance/progressive-delivery subtask of TURBO, not a separate pipeline. Hypothesised 2026-10-11 during TAGLINE POS and speed benchmarking. The under-two-minute goal, bypass proportions and throughput figures are hypotheses to validate end-to-end in the intended client/worker or service runtime, not established browser benchmarks or a mandated architecture. | `app/turbo/`; `docs/TAGLINE.md`; `CHAT_ROADMAP.md` row TURBO |
| **ROLLCALL-1** | Pre-flight readiness check for the next language pilot (Dutch vs French). Audit available assets: surface ledger status (Dutch has 122 review surfaces, French currently has 0 ledger / 200-card stub), dictionary snapshots, sentence banks, and token counts. Establish exact prerequisites to declare the pilot language ready for ingestion. | Not started. Designed 2026-10-11 as the fast entry gate before testing the new WSD cascade. | `docs/NL_FI_2000_RELEASE.md`; `docs/LANGUAGE_ONBOARDING.md`; `raw/surfaces/` |
| **CASCADE-WSD** | Pilot and benchmark the new hybrid WSD architecture on the chosen pilot language (Dutch or French): (1) Zero-cost monosemous bypass; (2) Data-driven / closed-class ambiguity router; (3) Cheap/lightweight vector embeddings for the 95% middle tier; (4) Selective escalation of the ~3–5% ambiguous tail to a tiny, fast LLM (DeepSeek / Qwen 1.5B–8B). Validate accuracy, latency, and cost reduction against the heavy Gemini embedding baseline. | Not started. Formulated 2026-10-11 following function-word disambiguation analysis. | `src/fluency/speech/wsd_execute.py`; `src/fluency/wsd/runner.py`; `config/wsd/models/` |
| **MIRROR-CS** | Extend the reflexive/pronominal tagger (`src/fluency/reflexive/`) to Czech: 999 of 10,000 cs cards have both a plain and a *se*/*si* meaning. A research chat, not a port: Czech *se*/*si* are second-position clitics with one form for every person, so the person-agreement method behind ~99% in es/pt does not carry over. Needs a Czech parser (Stanza or UDPipe; **ask Josh before downloading**) and new hand-labelled Czech gold sets. No other language is worth extending to (fr deck too small, no pl deck, nl unpublished). | Not started. | `research/reflexives/FINDINGS.md`; reuse the eval harness in `research/reflexives/` |
| **CONVOY** | Bring Czech, Finnish and French up to the Spanish/Portuguese standard on everything, so no language lags the two Josh works on. Audit first: per language, list what es/pt have that it lacks, then rebuild each on the current engine and pipeline. Historical gap inventory (2026-10-10; revalidate against the Release snapshot before work): (1) none is on UNISON's single engine or the decision 0030 metadata contract; `scripts/check_stale_engine.py` says "OK" only because each is measured against its own old profile (cs-v21-1, fi-v21-1, fr-v7-1), and it reads es/pt as v22 from workspace `active.json` while the app serves v23; (2) Merge Lemmas lists were rebuilt as a quick patch (verbs merge again), but nouns stay separate because the plural/singular check (decision 0029) has only run for es/pt: 3,884 cs and 616 fi noun cards. Run `scripts/refresh_noun_merge_metadata.py` with a fresh Wiktionary menu, as pt did; (3) French is a 200-card stub (`fr-speech-v7-dual-metadata-v5-20260918`) whose senses carry no headwords, so Merge Lemmas has nothing to merge; (4) the phrase-lemma fix (11276edc) reaches them only when rebuilt. Czech reflexives stay with MIRROR-CS; Czech verb English stays with INFLECT-CS. | Not started. Requested by Josh 2026-10-10. es and pt remain the priority; this row keeps the rest level. `tests/app/test_merge_exceptions_current.py` blocks any deploy whose live deck lacks a current Merge Lemmas list, so each rebuilt deck needs its list rebuilt. | `docs/unison/PROGRESS.md` (what es/pt received); `docs/decisions/0029-noun-number-merging.md`; `docs/decisions/0030-sense-metadata-and-display-contract.md`; `scripts/check_stale_engine.py`; `scripts/build_merge_exceptions.py` |
| **INFLECT-CS** | Czech verb rows show wrong or no English. INFLECT fixed this for es/pt; Czech was measured but not fixed. Only 1,356 of 3,035 Czech card/verb pairs get inflected English (es 82%, pt 96%), and some that do are wrong: (1) a perfective verb's "present" is a future, but the table does not record aspect: *řeknu* shows "I say" (should be "I'll say"), *uvidíme* "we see", *přijde* "he/she comes"; (2) the table stores the Czech past (l-form) in its participle slot, so it gets English participle wording: *udělal* "done" (should be "did"), *přišel* "come" ("came"); (3) the app serves Czech an old table (`cs-speech-v12-4000x10-conj`, 404 verbs, present and command only, because `kaikki_conjugations.py` reads Czech that way), so 503 pairs have no table and 1,096 pairs never match (feminine/plural past *všimla*, *umřeli*; negated *neznáme*; future *bude*). The fix is mostly a new Czech conjugation table from Wiktionary for the live deck's verbs, with full past forms and aspect, attached as a successor release (`conjugation_attach.py`, no harvest or WSD), then a small change in `reverse-cues.js` (perfective present → future, l-form → simple past, *ne-* → "don't/not"). Stage it; production needs Josh's approval. Reflexives stay with MIRROR-CS. | Not started. Requested by Josh 2026-10-11; measured 2026-10-11 on `cs-speech-v22-10000x30-slim` with `research/inflect/measure.mjs`. | `research/inflect/README.md`; `app/js/reverse-cues.js` (`conjugationTableCue`, `TENSE_KIND`); `src/fluency/enrichments/kaikki_conjugations.py` (`FULL_PARADIGMS`); `src/fluency/release/conjugation_attach.py`; `app/js/flashcards-conj.js` (Czech table shows Present and Imperative only) |
| **ROLLCALL-2** | Full retrospective audit of the complete language readiness checklist across all live and candidate languages (es, pt, cs, fi, fr, nl) against final production standards. Audit only: no harvests or rebuilds. | Not started. Positioned after speech mode and next-language pilot are proven end-to-end. | `docs/LANGUAGE_COMPLETION_CANDIDATE.md`; `docs/NL_FI_2000_RELEASE.md`; `docs/INVARIANTS.md`; app configs |
| **BRIDGE** | Add an option to Exclude Cognates that uses what the learner actually knows in another language they are learning, alongside the existing whole-known-language option. Start with Spanish and French, the two languages Josh is studying: a French word may be skipped when its matching Spanish word/meaning is already known in that learner's saved progress, and vice versa. Support the same approach for other pairs (e.g. Spanish and Portuguese), without assuming that studying a language means knowing its whole vocabulary. Reuse the existing cognate and sense-matching rules, preserving false-friend safeguards; define which recorded knowledge states qualify and how partial/sense-level knowledge maps across forms and merged cards. Make the setting understandable, keep skipped words available, and update eligibility as source-language knowledge changes without fabricating target-language study progress. Audit available progress and mapping data first, then build and verify the feature. French deck completion is needed for the full Spanish/French experience, but does not block building the feature and testing with available data; coordinate French release work with CONVOY. | Not started. Requested by Josh 2026-10-10. Initial pair Spanish/French; French deck completion is a rollout dependency, not a reason to defer implementation. | `app/js/cognates.js`; `app/js/knowledge.js`; `app/js/progress.js`; `app/js/progress-identity.js`; `app/js/fast-track-preferences.js`; `src/fluency/features/cognates.py`; `docs/decisions/0028-words-that-must-not-be-skipped.md`; CONVOY row |
| **DUTCH** | Ship the Dutch 2,000-card speech release: review the 122 ledger surfaces, finish the readiness checklist, activate. | Not started. Candidate `nl-speech-v1-2000x5-3-candidate` exists, inactive. | `docs/NL_FI_2000_RELEASE.md` → Dutch; `docs/LANGUAGE_COMPLETION_CANDIDATE.md` |
| **UPKEEP** | Audit and clean up historical, invalid and deprecated learner-database states across all users, production and staging. Establish the current schema and supported states first; distinguish valid history and compatibility data from obsolete active state. Start with explicit stage 0 plus a correct answer and no unresolved mistake, then inspect progress identities, settings, counts/timestamps, event/state consistency and sync watermarks for other verified legacy problems. Reconcile the Worker/client scheduling rules and identify any client or write path that can recreate invalid states; the cause of the existing stage-zero rows is unproven. Snapshot affected data, report per-user counts and concrete before/after examples, and prepare conservative, repeatable repairs that preserve card identities, answer counts and genuine historical evidence. JST was previously to remain untouched: obtain Josh's explicit approval for the concrete JST repair before applying it. Preserve its original snapshot and keep JOSHUA's deliberate synthetic scheduling distinguishable from genuine review history; do not rewrite append-only events or delete valid history merely because it is old. Verify current app loads, scheduling and full/delta sync after repairs; document every checked category, remaining compatibility requirement and unverified area rather than claiming all legacy data is gone from a partial audit. Follow AIRLOCK for app changes. | Not started. Requested by Josh 2026-10-10. Last successful read-only check: JST alone had 3,217 frozen known rows at stage 0 (1,555 words, 1,662 lemmas); both JOSHUA copies matched all 10,211 intended rows and 11 fast-track settings, with no level-done settings. Migration 0008 remains unapplied and would currently affect only JST. A later query failed with Cloudflare authorization error 7403; refresh counts before repair. | `backend/worker/src/store.js`; `backend/worker/src/profiles.js`; `backend/worker/migrations/`; `app/js/progress.js`; `app/js/auth.js`; `app/js/sync-queue.js`; `app/js/offline-db.js`; workspace `research/jst-to-joshua/` (original snapshot, payloads and `verification_2026-10-10.json`); `docs/INVARIANTS.md` |

## Release snapshot (2026-10-11)

Speech selections below were checked against the served production
`https://rabbijoshy.github.io/Fluency-App/app/config/config.json` on 2026-10-11.
Lyrics/artist entries are carried forward and were not re-audited. Local config
may contain another chat's unpublished candidate. Spanish successor WSD staging
is in progress; do not label it production until the served config confirms it.
The local staging receipt records `15d15686`; a direct staging-config request
returned HTTP 403 during this audit, so latest staging contents were not independently
verified. Existing staging browser evidence remains recorded in each job's brief.

| Mode | Release |
|---|---|
| Speech es | `es-speech-v24-headway-r4-10000x30-slim` (corrected lemmas, targeted WSD, Wiktionary conjugations) |
| Speech pt | `pt-speech-v24-headway-r3-10000x30-slim` (TAGLINE successor to HEADWAY r2) |
| Speech cs | `cs-speech-v22-10000x30-slim`; conjugation attachment remains `cs-speech-v12-4000x10-conj` |
| Speech fi | `fi-speech-v21-2000x30-slim` |
| Speech fr | `fr-speech-v7-dual-metadata-v5-20260918` |
| Lyrics es | v20 (Bad Bunny, test playlist); Rosalía and Young Miko carried from v18 |
| Artist fr, pt | Polyglot test releases |

Conjugations come wholly from Wiktionary in every language (verbecc and Jehle
removed, 2026-10-04).

## Done

Treated as finished. Each could be improved; reopening one means giving it a
new row above, not editing this list.

| Codename | What it delivered |
|---|---|
| TOUCHPOINT | Completed 2026-10-11 under Josh’s narrowed code-audit scope: consistent 50px grading and feedback, direction locking, scrollport separation, button-started drags, cancellation/multiple-touch cleanup, duplicate-grade protection, single click-owned flips and gesture-only hint dismissal. 252 app tests passed; Spanish/Portuguese cards, phrase panels and long backs reviewed at phone widths. Published to staging in `ed368cdb` and final follow-up `15d15686`; layout, button positions/actions and saved-progress rules preserved. Physical-phone feel and native scrolling movement remain unverified after browser interruption; two-device sync/resume checks deferred at Josh’s request. Production promotion still requires explicit approval. Evidence: `docs/TOUCHPOINT.md`. |
| HEADWAY | Spanish/Portuguese source-correction campaign complete, confirmed by Josh 2026-10-11: corrected 293 es / 4,521 pt ledger surfaces, targeted WSD and corrected default-deck/cache rollout. Later TAGLINE releases supersede the original candidates. The 79 es / 142 pt unresolved source entries remain recorded as deferred adjudications, not a reason to repeat the completed campaign. Evidence: `docs/HEADWAY.md`. |
| SEAM | Spanish/Portuguese merging logic and card behaviour complete, confirmed by Josh 2026-10-11: verified verb/noun rules and loaded/cold parity across 20,000 cards; fixed kept-apart titles and search Examples-only flags; restored checked noun merges and retained dictionary alternatives; canonical examples now follow the studied form. Required app checks passed; changes reached staging. Final canonical-example visual review remains with Es/Pt Release Review; production approval is still required. Czech/Finnish/French audits, identifier-less-provider checks and remaining phrase-shaped source keys are deferred follow-ups. Evidence: `docs/SEAM.md`. |
| TAGLINE | Contextual POS tagging & WSD safeguards: verified Portuguese *és* letter-noun root cause; implemented Stanza UPOS tagger (`stanza-pt-default@1.14.0`), soft evidence gating (`constraint_mode="soft_gate"`, `pos_penalty=0.06`), and single-POS bypass (`--skip-single-pos-menus`). Shipped candidate speech releases `pt-speech-v24-headway-r3-10000x30-slim` (active in production config) and `es-speech-v24-headway-r5-10000x30-slim` (staged); built and deployed lyrics release `lyrics-all-artists-v20` via `es-lyrics-v24-1` on staging. |
| AIRLOCK | Production and staging environments established. Staging published at https://fluency-staging.pages.dev/ with complete browser/backend storage isolation, candidate deck review, repeatable staging publication (`make stage`), deliberate promotion (`make promote`), and updated agent instructions in `CLAUDE.md`. |
| UNISON | Three-part unification campaign (UNISON-1 audit of 300 es/pt cards, UNISON-2 unified engine & profiles across speech/lyrics/TURBO, UNISON-3 metadata contract decision 0030, Kaikki parity & deployed speech releases). |
| NEEDLE, FUSE, SIEVE, MILL, SWEEP | v13–v15 speech WSD algorithm and the MWE overlay |
| QUARRY, CHISEL 1–2, KILN 1–2, GLASS | 10k supply, MWE curation, 10k speech decks |
| MEND | The word-database structure: surface facts, scopes, trust tiers, shared resolver |
| GRAFT, VERSE, CHORUS | Lyrics overlays and lyrics WSD v16–v18. Lyrics v20 builds its menus through the shared resolver (proposal 0004's menu step) |
| POLYGLOT | Artist mode across languages; French and Portuguese test releases |
| SETLIST | Spotify playlist → LRCLIB → naive study deck |
| GLEAN | MWE re-harvest for Merge Lemmas (decision 0028) |
| KINDRED | Cognates for any language pair; `learner-align/v1` scorer (decision 0027) |
| DRAWER | Conjugation tables and their English glosses |
| INFLECT | Conjugated verb rows read as natural English (pass 1 `46ef386b`, pass 2 `e0b5c1c2`): no spurious commands, imperfect as simple past, English spelling, bracket-aware clauses; Spanish *-se* rows and agreeing participles inflect; the conjugation table finds *-se* forms. Attached object pronouns (*verte* → "to see you") were left to the companion-card work |
| INFLECT-2 | Verb rows describe the word: one reading (statement unless the card's sentences or the example are commands), person never follows the example (`9c60a320`, `fa94c9bc`); verbs only a thing can do say "it" (*pasa* "it happens", *gusta* "it pleases"); es r5 115 rows, pt r3 64, 0 gained or lost. A pt definition-bracket change was tried and reverted: the card already shows those as sub-rows |
| MIRROR | Speech v23 (es, pt): reflexive tagging as a WSD filter; Wiktionary-only conjugations. Keep `research/reflexives/` (eval harness + gold sets): it is how any change to the tagger is re-checked |
| — | Function words (*lo*, *de*, *que*): curated sense grouping in the app, not WSD |
| — | Smaller levels and sets (100-card levels, 25-card sets) |
| — | Release hosting split per language (decision 0026); the old combined `Fluency-Releases` repo was pruned to a README and archived on 2026-10-04 |

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
