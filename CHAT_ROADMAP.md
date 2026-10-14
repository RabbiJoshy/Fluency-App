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

## Current direction (2026-10-12)

### Before the next release to users

| Codename | Focus |
|---|---|
| **SHOWCASE** | Tutorial, About and Walkthrough bug-free and matching the current card UX. Standing track, but must be current before the release. |
| **UPKEEP** | Learner-database legacy state cleanup (stage 0 rows, JST/JOSHUA). Repairs need Josh's explicit approval. |

### After the release

| Codename | Focus |
|---|---|
| **TERSE-2** | Listed by Josh 2026-10-12 for after the release. The first pass is in production (see Done); scope of a further pass not yet defined. |
| **INFLECT-3** | Second-look English polish on verb rows (subjunctives, modals), from real cards. |
| **HINGE** | Make the grammar-word labels (es/pt/cs/nl) permanent, checked and documented; starts after their promotion. |

### In parallel, independent of the release

| Codename | Focus |
|---|---|
| **TURBO / TURBO-STREAM** | In-client playlist ingestion and progressive streaming delivery (song mode). |

### Later: multilingual parity and expansion

ROLLCALL-2, CONVOY, INFLECT-CS, MIRROR-CS, DUTCH. Run after speech mode is proven end to end.

### Paused permanently

| Codename | Why |
|---|---|
| **ACCORDION** | Paused permanently by Josh 2026-10-12. Collapsible uses lists from `c94b87f8` stay as they are; no further design pass. Do not pick up. |

---

## Open

Everything open is listed here. If it is not in this table, it is done (below), paused permanently (ACCORDION, above) or an eventual direction (`LATER.md`).

| Codename | Job | Status | Read |
|---|---|---|---|
| **SHOWCASE** | Ongoing / standing maintenance: keep the learner Tutorial (`app/js/tutorial.js`), visitor About modal (`#aboutProjectModal`), and interactive Walkthrough bug-free, accurate, and completely aligned with the latest card back layout and engine capabilities. Ensure replica cards match live card behavior (reveal, flip, spotlight rings, example cycling, rarer uses, Smart Skip, lyrics flow) across supported languages without regressions. Does not end; stays open as a standing UX alignment track. | Ongoing / standing maintenance. Pass completed 2026-10-13 (`f7eca56d`: tutorial copy tightened <= 180 chars, mobile full-bleed & unclipped scaling, walkthrough pin overlap fixes, About demo grid repair; verified on staging). Stays open. | `app/js/tutorial.js`; `app/js/routes.js`; `app/index.html`; `docs/decisions/0023-tutorial-walkthrough-about.md`; `docs/NOMENCLATURE.md` |
| **UPKEEP** | Audit and clean up historical, invalid and deprecated learner-database states across all users, production and staging. Establish the current schema and supported states first; distinguish valid history and compatibility data from obsolete active state. Start with explicit stage 0 plus a correct answer and no unresolved mistake, then inspect progress identities, settings, counts/timestamps, event/state consistency and sync watermarks for other verified legacy problems. Reconcile the Worker/client scheduling rules and identify any client or write path that can recreate invalid states; the cause of the existing stage-zero rows is unproven. Snapshot affected data, report per-user counts and concrete before/after examples, and prepare conservative, repeatable repairs that preserve card identities, answer counts and genuine historical evidence. JST was previously to remain untouched: obtain Josh's explicit approval for the concrete JST repair before applying it. Preserve its original snapshot and keep JOSHUA's deliberate synthetic scheduling distinguishable from genuine review history; do not rewrite append-only events or delete valid history merely because it is old. Verify current app loads, scheduling and full/delta sync after repairs; document every checked category, remaining compatibility requirement and unverified area rather than claiming all legacy data is gone from a partial audit. Follow AIRLOCK for app changes. | Read-only snapshot audit completed 2026-10-13; live check rejected with Cloudflare authorization error 7403. Restored Joshua snapshot has 10,288 rows, no frozen stage-zero state and no invalid counts/timestamps; archived JST has 3,217 frozen rows. Local scoped repair rehearsal preserves counts/history. Remaining: fresh production/staging inventory, 12 residual JST settings, five Joshua state/event counter differences, Worker/client schedule mismatch and write-conflict reproduction; no live repairs applied. D1 warning at 77% written quota: defer bulk writes until reset at 2026-10-14 00:00 UTC. Full evidence and limitations: workspace `audits/upkeep-20261013/report.md`. | `backend/worker/src/store.js`; `backend/worker/src/profiles.js`; `backend/worker/migrations/`; `app/js/progress.js`; `app/js/auth.js`; `app/js/sync-queue.js`; `app/js/offline-db.js`; workspace `research/jst-to-joshua/` (original snapshot, payloads and `verification_2026-10-10.json`); `docs/INVARIANTS.md` |
| **INFLECT-3** | Second look at the English on es/pt verb rows after Josh has used the app; start from real cards on staging, not from `measure.mjs` (it counts cue strings; the card back already lifts definition brackets into sub-rows, which INFLECT-2 learned the hard way and reverted). Hardest cases, with sizes on es r5 / pt r3 (card/verb pairs): (1) **Subjunctive-only forms** (*sea*, *vaya*, *tenga*; pt *seja*, *vá*, *tenha*, *quiser*; 690 es, 611 pt). Josh rejected "that" and "may" because not every subjunctive is a *que*-clause; the row keeps plain present/past. Left: the "(s)/(es)" notation (*vaya* "I/he/she go(es)") and two-clause rows (*sea* "I am / he/she is"), and *-ra* forms that mean "would" (*quisiera* "I/he/she wanted", *pudiera*). The row cannot see which use it is; only the example sentence can. (2) **One row, several readings**: *vamos*, *mira*, *ven*, *haz* are a statement, a command or both; the two-thirds rule and the on-screen example decide, and *mira* shows "look!" beside "he/she watches" on one card. A per-example row is the real fix. (3) **Rows with no English**: pt *tenho/temos/tens* show the note "See ter de, ter que." and *vou/vai/vamos* "will; to be going to; forms the future tense" (99 pairs, pt only); es and pt modals (*puedo* "can", *debe* "should", 153 es, 164 pt rows) have no person. Wrong English first, so these were left. (4) ***gustar*-type verbs**: INFLECT-2 made *gusta* "it pleases", *encanta* "it delights", *duele* "it hurts"; true to the grammar but stiff, because *me gusta* is "I like it" and the row cannot carry *me*. Check how it feels. *importa* still shows SpanishDict's "he/she cares/minds" (a wrong-subject sense). (5) **Participles** read as bare "done", "been", "seen", "died" (*muerto*): right as participles, but cards use them as adjectives ("dead", "tired"). (6) **Commands ending on a bare preposition**: *mira* "look at!", *escute* "listen to!", *llévate* "take with one!" (26). (7) **Clock senses** with a first-person reading (pt *era* "I/it was"). Not English, so not here: wrong meaning or headword on the card (es *vamos* "to be" → "we are", *hace* "to think"; pt *vem/venha/veio* filed under `ver`, *tivesse* under `estar`: HEADWAY/TAGLINE), attached-pronoun infinitives (*hacerlo*, *verte*, 512 es pairs: companion cards), gloss length (TERSE-2). | Not started. Requested by Josh 2026-10-11 for when he returns from using the app; no deadline. Baseline is staging after INFLECT-2 (`reverse-cues.js` with the "it" rule). | `research/inflect/README.md`; `app/js/reverse-cues.js` (`chooseTableReadings`, `finiteEnglishCue`, `compressPronounCues`, `thirdPersonSubject`); `app/js/card-metadata-pills.js` (`projectWiktionaryGloss`: where definition brackets leave the row) |
| **TURBO** | Live Spanish pipeline for a user-uploaded Spotify playlist: clean, normalise, tag and run fast WSD in the client/worker, then build a study deck immediately. Must not block the UI thread or break card progress. | **In progress** (`app/turbo/`). The last big piece of the app. Powered by the unified WSD decision logic and asset profile `config/wsd/models/es-turbo-v1.json`. Playlist ingest, worker and UI work continue. | `docs/runbooks/live-playlist.md` (SETLIST, which it builds on) |
| **TURBO-STREAM** | Design and build the lightweight online WSD ingestion pipeline for user-imported song playlists and custom decks (up to 100 songs / ~5,000 polysemous words / ~15,000–30,000 POS tags / ~50,000–100,000 WSD evaluations). Leverage single-POS menu bypass to skip 60%+ of tokens from POS tagging, sequential/lightweight tagging (e.g. Stanza BiLSTM or equivalent worker-compatible tagger at ~250–350 sent/sec), exact-text embedding cache lookups, and batched/multiprocessed pipeline execution to complete 100-song ingestion in under 2 minutes. Support progressive streaming updates (deck unlocks cards as songs finish) so the user never blocks waiting on the full import. | Not started; performance/progressive-delivery subtask of TURBO, not a separate pipeline. Hypothesised 2026-10-11 during TAGLINE POS and speed benchmarking. The under-two-minute goal, bypass proportions and throughput figures are hypotheses to validate end-to-end in the intended client/worker or service runtime, not established browser benchmarks or a mandated architecture. **Idea to discuss, not decided (raised 2026-10-12):** a declared function-word class. A per-language declared list (*que, de, se*, clitics, articles, contractions) might get no per-example LLM sense online: the card would show a fixed summary plus its phrase senses (*ter que*, *tener que ver con*), and those words would be disambiguated offline instead (~1,000 examples across ~30 words by LLM, minimal cost). Content words with idioms (*dar*) would stay in the cascade with a defined phrase list. Absence declared, not inferred (invariant 2). Josh wants to discuss it when TURBO-STREAM starts. **Turbo goal decided 2026-10-13 (CASCADE-WSD):** minimise sentences reaching WSD (menu-list surfaces only, clitics onto their base surface, grammar words by rules, example cap by senses and rank), one Qwen3-Embedding-0.6B embedding, LLM per word for the hardest few percent only; the French run is the Turbo rehearsal. Read `research/cascade/README.md` (Turbo goal) first. Evidence: `research/cascade/`. | `app/turbo/`; `docs/TAGLINE.md`; `CHAT_ROADMAP.md` row TURBO |
| **HINGE** | Follow-up to the grammar-word labels shipped by CASCADE-WSD (rule labellers: parser + Wiktionary phrases, verb patterns, pronominal verbs; es/pt/cs/nl). **Make it permanent:** (1) move `research/cascade/trouble-words/labeller_*.py` into `src/fluency/` with tests using the hand-labelled sets as regression; (2) produce labels inside the pipeline (WSD stage or release builder) instead of the `fw-overlay` add-on, and until then make a es/pt/cs rebuild refuse to drop them; (3) rebuild Czech properly (labels were copied onto old-format rows without validation). **Accuracy:** (4) Spanish source: check whether our SpanishDict data has phrases, pronominal verbs and verb patterns, then choose SpanishDict or Wiktionary; (5) spot-check the Wiktionary phrases that actually appear on cards for junk; (6) confirm labeller *se* never contradicts the reflexive tagger; (7) native-speaker or blind check of a sample per language. **App:** (8) grammar-word block on the word page (`#/xx/w/<word>`); (9) review near-threshold cards and the 60% cut-off. **Docs:** (10) decision record (what qualifies, 60% cut-off, rules before WSD, what is Wiktionary vs handwritten) and NOMENCLATURE terms (grammar word, role, phrase). **Turbo-linked (may move to TURBO):** (11) French labeller, needed for the French/Turbo rehearsal; (12) labels for lyrics/artist decks and Turbo, deciding where the parser runs. | Not started; the grammar-word release is in production (2026-10-13). Listed by Josh 2026-10-13. Display-only stopgaps already live (`469908f6`): Wiktionary notes/pointers ("Used other than figuratively…", "spelling of…") hidden as phrase meanings, "(+ verb)" preposition chips merged. **Parked, uncommitted:** a labeller-level fix (`research/cascade/trouble-words/gloss_filter.py`, idiom keep-lists, tag `fw2` in `fw-overlay/overlay.py`) with fw2 labels in `<workspace>/raw/wsd/{es,pt,cs}/fw2-function-word-labels.json` (es 80 / pt 76 / cs 5 labels changed vs fw1, Dutch unchanged); review before using. | `research/cascade/README.md`; `research/cascade/trouble-words/`; `research/cascade/fw-overlay/`; `app/js/function-word-card.js` |
| **MIRROR-CS** | Extend the reflexive/pronominal tagger (`src/fluency/reflexive/`) to Czech: 999 of 10,000 cs cards have both a plain and a *se*/*si* meaning. A research chat, not a port: Czech *se*/*si* are second-position clitics with one form for every person, so the person-agreement method behind ~99% in es/pt does not carry over. Needs a Czech parser (Stanza or UDPipe; **ask Josh before downloading**) and new hand-labelled Czech gold sets. No other language is worth extending to (fr deck too small, no pl deck, nl unpublished). | Not started. | `research/reflexives/FINDINGS.md`; reuse the eval harness in `research/reflexives/` |
| **CONVOY** | Bring Czech, Finnish and French up to the Spanish/Portuguese standard on everything, so no language lags the two Josh works on. Audit first: per language, list what es/pt have that it lacks, then rebuild each on the current engine and pipeline. Historical gap inventory (2026-10-10; revalidate against the Release snapshot before work): (1) none is on UNISON's single engine or the decision 0030 metadata contract; `scripts/check_stale_engine.py` says "OK" only because each is measured against its own old profile (cs-v21-1, fi-v21-1, fr-v7-1), and it reads es/pt as v22 from workspace `active.json` while the app serves v23; (2) Merge Lemmas lists were rebuilt as a quick patch (verbs merge again), but nouns stay separate because the plural/singular check (decision 0029) has only run for es/pt: 3,884 cs and 616 fi noun cards. Run `scripts/refresh_noun_merge_metadata.py` with a fresh Wiktionary menu, as pt did; (3) French is a 200-card stub (`fr-speech-v7-dual-metadata-v5-20260918`) whose senses carry no headwords, so Merge Lemmas has nothing to merge; (4) the phrase-lemma fix (11276edc) reaches them only when rebuilt. Czech reflexives stay with MIRROR-CS; Czech verb English stays with INFLECT-CS. | Not started. Requested by Josh 2026-10-10. es and pt remain the priority; this row keeps the rest level. `tests/app/test_merge_exceptions_current.py` blocks any deploy whose live deck lacks a current Merge Lemmas list, so each rebuilt deck needs its list rebuilt. | `docs/unison/PROGRESS.md` (what es/pt received); `docs/decisions/0029-noun-number-merging.md`; `docs/decisions/0030-sense-metadata-and-display-contract.md`; `scripts/check_stale_engine.py`; `scripts/build_merge_exceptions.py` |
| **INFLECT-CS** | Czech verb rows show wrong or no English. INFLECT fixed this for es/pt; Czech was measured but not fixed. Only 1,356 of 3,035 Czech card/verb pairs get inflected English (es 82%, pt 96%), and some that do are wrong: (1) a perfective verb's "present" is a future, but the table does not record aspect: *řeknu* shows "I say" (should be "I'll say"), *uvidíme* "we see", *přijde* "he/she comes"; (2) the table stores the Czech past (l-form) in its participle slot, so it gets English participle wording: *udělal* "done" (should be "did"), *přišel* "come" ("came"); (3) the app serves Czech an old table (`cs-speech-v12-4000x10-conj`, 404 verbs, present and command only, because `kaikki_conjugations.py` reads Czech that way), so 503 pairs have no table and 1,096 pairs never match (feminine/plural past *všimla*, *umřeli*; negated *neznáme*; future *bude*). The fix is mostly a new Czech conjugation table from Wiktionary for the live deck's verbs, with full past forms and aspect, attached as a successor release (`conjugation_attach.py`, no harvest or WSD), then a small change in `reverse-cues.js` (perfective present → future, l-form → simple past, *ne-* → "don't/not"). Stage it; production needs Josh's approval. Reflexives stay with MIRROR-CS. | Not started. Requested by Josh 2026-10-11; measured 2026-10-11 on `cs-speech-v22-10000x30-slim` with `research/inflect/measure.mjs`. | `research/inflect/README.md`; `app/js/reverse-cues.js` (`conjugationTableCue`, `TENSE_KIND`); `src/fluency/enrichments/kaikki_conjugations.py` (`FULL_PARADIGMS`); `src/fluency/release/conjugation_attach.py`; `app/js/flashcards-conj.js` (Czech table shows Present and Imperative only) |
| **ROLLCALL-2** | Full retrospective audit of the complete language readiness checklist across all live and candidate languages (es, pt, cs, fi, fr, nl) against final production standards. Audit only: no harvests or rebuilds. | Not started. Positioned after speech mode and next-language pilot are proven end-to-end. | `docs/LANGUAGE_COMPLETION_CANDIDATE.md`; `docs/NL_FI_2000_RELEASE.md`; `docs/INVARIANTS.md`; app configs |
| **DUTCH** | Ship the Dutch 2,000-card speech release: review the 122 ledger surfaces, finish the readiness checklist, activate. | Not started. Candidate `nl-speech-v1-2000x5-3-candidate` exists, inactive. | `docs/NL_FI_2000_RELEASE.md` → Dutch; `docs/LANGUAGE_COMPLETION_CANDIDATE.md` |

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
| Speech cs | `cs-speech-v22-10000x30-slim`; conjugation attachment remains `cs-speech-v12-4000x10-conj`; coverage shares rebuilt for all 10,000 v22 words (2026-10-12, `app/coverage/cs/coverage.json`) |
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
| CASCADE-WSD | Dutch pilot of cheap-embedding + LLM WSD, closed 2026-10-13. DeepSeek V4.1 Flash alone 96%, Qwen3-4B + e5-small cascade ~94% with ~34% of sentences to the LLM, any embedding alone 78–88%. Grammar-word rule labellers for nl/es/pt/cs (150/179/198/241 cards, spot checks 94–98%; not French), added to the live es/pt/cs decks unchanged otherwise, and Dutch prototype deck `nl-cascade-proto-2`; in production 2026-10-13 (`a1cbe2d7`); compact card display with the contraction parts beside the word in production (`469908f6`). Role names in `app/js/function-word-card.js` are a draft for Josh's approval. Findings and the Turbo goal: `research/cascade/README.md`. |
| — | Performance audit, 2026-10-12, in production (`827537fb`). (1) Staging only: Cloudflare Pages answered missing files with `index.html` plus a relative `modulepreload` Link header, so each missing file (`Artists/spotify_tracks.json`; `coverage/cs/coverage.json`, never copied to staging) preloaded `…/js/main.js` one folder deeper without end: ~500 requests and ~17 MB a minute per open tab, the laptop heat. Fixed by a staging-only `404.html` in `scripts/build_pages_site.py`; production (GitHub Pages) was never affected. (2) Smart Skip worked out the learner's known languages once per word (~140,000 storage reads) and recomputed `collectExtras` about a dozen times per deck open; both now held for one pass of work and dropped on any setting change. Czech setup work while a deck opens ~800 → ~460 ms; the remaining cost is several full deck passes in setup (`buildFilteredVocab`, `applyCognateScores`), not restructured. (3) The home screen prefetches the offered session's rows and example shards: Go ~2.5 s → ~0.2 s. (4) Level coverage looked shares up by headword (*ten*) instead of surface (*to*): 6,286 of 10,000 Czech cards read the wrong share (level 1 showed 32.0%, true 43.9%). Czech coverage rebuilt for all 10,000 v22 words and now shipped from the repo (`app/coverage/cs/`). (5) The hidden loading spinner no longer animates. Checked and left: `data/source_titles.json` is 273 KB compressed, ~9 ms to parse, once per app load. Idle study view, card flips (<5 ms) and memory (~21 MB) were already fine. |
| BRIDGE | Exclude Cognates using what the learner knows in another language they study (es/fr/pt bundles), with a shared account language profile, opt-in per-target transfer, false-friend and cross-language verb-form safeguards; no target progress fabricated. In production 2026-10-12. Full French experience still depends on CONVOY. Evidence: `docs/BRIDGE_IMPLEMENTATION.md`. |
| SETWISE-2 | Learn New vs Practise with sessions chosen by time (5 min / 10 min / No limit), four Go states for a level (new / ask / no new left / mastered), Practise showing when words come back, quieter level badge. In production 2026-10-12 (`827537fb`). Evidence: `docs/SETWISE.md` (SETWISE-2 section). |
| SETWISE (v1) | One continuous level progress bar over 100-card levels, up-to-20-card sessions with Another 20, within-level estimation wording; resumes, Smart Skip and saved progress preserved. In production 2026-10-12. Evidence: `docs/SETWISE.md`. |
| Track 1 (WSD & language data) | HEADWAY → SEAM, LITERAL-GROUND, Es/Pt Release Review: all done, closed 2026-10-11. |
| ROLLCALL-1 | Pilot-language audit, 2026-10-11, $0. Dutch over French: Dutch has a complete 2,000-surface ledger (1,878 keep / 122 review), 95% Wiktionary menu coverage and a 78k-sentence bank; French has no ledger, a 200-card live deck and plausible future menu upgrades (Larousse/Le Robert), which would invalidate labels. Dutch menu locked to English Wiktionary: no non-Wiktionary Dutch menu was ever used or quality-tested (old repo was Wiktionary too); Open Dutch WordNet was compared on coverage only (fills 13 of 101 gaps). Prerequisite list is in the CASCADE-WSD row. |
| LITERAL-GROUND | Closed-class preposition guards for es/pt speech, in production 2026-10-11 (`78548470`): pt `pt-speech-v25-literal-ground-r4`, es `es-speech-v25-literal-ground-r6`; only pt de/do/da/dos/das/em/no/na/nos/nas and es de/del re-run. Declared primary leaf + 0.025 margin floor, governed bypass for de. 124 hand-judged changed sentences: 78 better, 7 worse where card English changes. por/para/es a/al/en deliberately unguarded. The "except/except for" overlap fix is verified on the sample but left for CASCADE-WSD, not rolled out deck-wide; `research/literal-ground/labels.jsonl` is a ready regression set for it. Evidence: `research/literal-ground/README.md`. |
| TERSE-2 | Shared client trimming of long glosses and contexts that keeps whole translations, restrictions and sense distinctions; full original text in the information dialog. In production 2026-10-11 (`78548470`). Evidence: `research/terse/README.md`. |
| Es/Pt Release Review | Josh reviewed the staged es/pt speech decks and approved promotion 2026-10-11; Track 1 closed. |
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
