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

## Current direction (2026-10-10)

**Priority: make Spanish and Portuguese shippable first; other-language parity
comes later.** This is a changeable planning order, not a rigid queue or a new
authorisation to start another chat's work. Josh can reprioritise at any time.
The Open table's row order is not priority order. Existing job scopes remain;
complete their es/pt portion first and record deferred language work explicitly.

AIRLOCK is done: review proposed app and deck changes in staging before deliberate
production promotion, following the current deployment instructions.

| Suggested order | Work | Shipping focus / dependency |
|---|---|---|
| 1 | HEADWAY | Establish and correct es/pt lemma-analysis problems that affect shipped cards. Owns source analyses, not app merging policy. |
| 2 | SEAM | Check es/pt merging, kept-apart forms and titles. Auditing can overlap HEADWAY; finalise affected behaviour against corrected analyses. Other-language checks follow later, before their CONVOY rebuilds. |
| 3, starting alongside 1–2 | TOUCHPOINT | Check actual-phone usability and two-device progress early. Record gesture and sync outcomes separately; recheck affected behaviour if later UI changes invalidate the observations. |
| 4 | TERSE-2 | Make long/confusing pt definitions and equivalent es problems readable while preserving meaning and original source text. |
| 5 | LITERAL, focused first pass | Audit a small es/pt sample using the required frozen evidence. Only verified, material learner-visible gaps become pre-launch fixes; broader investigation need not hold up shipping. |
| 6 | Spanish/Portuguese release review | Review the candidate app and decks together in staging, resolve genuine launch blockers, and obtain Josh's approval for promotion. This is a release checkpoint, not a new implementation job or the full multilingual ROLLCALL. |

**Work alongside this sequence:**

- General UI fixes can proceed now. Coordinate card titles, merging, known counts
  and progress displays with SEAM; card-back content/layout with TERSE-2 and
  ACCORDION; swiping, grading and mobile interaction with TOUCHPOINT. Keep chat
  scopes distinct and avoid simultaneous edits to the same component. Review the
  combined result in staging before shipping.
- Decide ACCORDION after TERSE-2 clarifies the remaining layout problem. If the
  existing modal is satisfactory, defer it; an accordion is not an assumed blocker.
- TURBO can continue independently. Playlist uploads are a launch prerequisite
  only if Josh includes them in the immediate launch scope; that decision is not
  settled by calling TURBO the last big piece of the app.
- These priorities do not require unrelated audits or implementation to wait.
  The immediate shipping criteria are correct cards, understandable meanings,
  usable phone interaction and dependable saved progress, not completion of every
  open feature or research question.

**After es/pt shipping:** default attention order is ROLLCALL → CONVOY, then
BRIDGE and DUTCH as prioritised, with MIRROR-CS kept as separate research.
ROLLCALL establishes the current cross-language gaps; CONVOY uses that inventory
and checked SEAM rules rather than repeating the whole readiness audit. BRIDGE
can be developed before French completion, which gates the full es/fr experience
only. DUTCH needs its own readiness sign-off, not completion of all CONVOY work.
MIRROR-CS must not block unrelated Czech improvements. `LATER.md` stays eventual.

## Open

Everything open is listed here. If it is not in this table, it is either
done (below) or an eventual direction (`LATER.md`). Do not start work from
anywhere else.

| Codename | Job | Status | Read |
|---|---|---|---|
| **HEADWAY** | Clean up surface-ledger analyses that treat phrases or inflected/clitic-attached forms as independent headwords. Keep genuine multiword expressions in the MWE layer; surface analyses should point to the actual lemma (e.g. SpanishDict `hay` → `haber`, `hacerlo` → `hacer`, retaining the attached-pronoun information). Audit SpanishDict and Wiktionary, including Portuguese candidates such as `vamos/ir` and `és/ser`; preserve genuinely distinct lemmas such as `ser/ir` and `conta/contar`. Investigate why the earlier phrase cleanup appears to have regressed, fix the source/import path so it stays fixed, and preview affected analyses before changing ledger data. | Corrected 293 es / 4,521 pt ledger surfaces; 79 es / 142 pt retain unresolved issues. Targeted fresh WSD completed on 174 es / 977 pt changed menus, using existing frozen sentences; other menus carry unchanged. Both final candidate decks are built and validated; final pt publication/review is underway after staging exposed a further form-POS import defect. Latest staging UI is preserved without an app redeploy. HEADWAY owns source analyses; SEAM checks existing merging policy and display against the candidates. Evidence: `docs/HEADWAY.md`; workspace `raw/surfaces/headway/`. | `src/fluency/surfaces/ledger.py`; `src/fluency/surfaces/resolver.py`; `src/fluency/sense_menu/spanishdict.py`; `src/fluency/sense_menu/spanishdict_lemmas.py`; `src/fluency/sense_menu/kaikki.py`; `docs/NOMENCLATURE.md` |
| **LITERAL** | Audit WSD choices where the supplied English translation determines which English gloss should be shown, even when the source-language meaning alone cannot distinguish the alternatives. Josh's historical example is "except" versus "except for": recover a real source word/menu/example if available, without inventing the original case. First establish what current code, active profiles and shipped frozen assignments already handle; do not assume the old idea is missing or solved because alignment code exists. Separate true source-language sense distinctions from English wording variants of the same meaning, and distinguish matching the English phrase from globally searching for a word anywhere in the translation. Trace the existing literal-gloss alignment corrector and its actual enablement across speech, lyrics and TURBO, for SpanishDict and Wiktionary. Build a small labelled sample of this failure class, including multiword glosses, overlapping cues, paraphrases, repeated words and missing/poor translations; report current behaviour and learner-visible errors. Determine whether reliable local phrase/token alignment, a deterministic gloss rule, or shared-meaning presentation is needed; do not make exact English wording the sole WSD authority for every word. Propose a targeted fix only for verified gaps, with fixes versus regressions and provenance; follow existing freeze/pool and spend rules. | Not started. Requested by Josh 2026-10-10 to check an idea remembered from months earlier; original date and current coverage unverified. | `src/fluency/wsd/alignment.py`; `src/fluency/wsd/runner.py`; `src/fluency/wsd/lyrics_adapter.py`; `config/wsd/models/`; `tests/wsd/test_alignment.py`; `tests/wsd/test_runner.py`; `docs/reference/wsd_open_threads.md` (aligned English lead; historical measurements); `docs/unison/PROGRESS.md`; TURBO row |
| **TURBO** | Live Spanish pipeline for a user-uploaded Spotify playlist: clean, normalise, tag and run fast WSD in the client/worker, then build a study deck immediately. Must not block the UI thread or break card progress. | **In progress** (`app/turbo/`). The last big piece of the app. Powered by the unified WSD decision logic and asset profile `config/wsd/models/es-turbo-v1.json`. Playlist ingest, worker and UI work continue. | `docs/runbooks/live-playlist.md` (SETLIST, which it builds on) |
| **MIRROR-CS** | Extend the reflexive/pronominal tagger (`src/fluency/reflexive/`) to Czech: 999 of 10,000 cs cards have both a plain and a *se*/*si* meaning. A research chat, not a port: Czech *se*/*si* are second-position clitics with one form for every person, so the person-agreement method behind ~99% in es/pt does not carry over. Needs a Czech parser (Stanza or UDPipe; **ask Josh before downloading**) and new hand-labelled Czech gold sets. No other language is worth extending to (fr deck too small, no pl deck, nl unpublished). | Not started. | `research/reflexives/FINDINGS.md`; reuse the eval harness in `research/reflexives/` |
| **TERSE-2** | Shorten over-long sense contexts and glosses on the card back. Portuguese (and every Wiktionary-provider language) shows Kaikki definitions word for word; e.g. pt *não*: "isn't · used to ask whether a person agrees with the proposition, rather than to ask for an unknown fact". There is no hand-written menu layer for pt. Decide the approach (length policy in the sense-menu adapter, a curated override file, or a model-shortened field with provenance) — provider-agnostic, and labelled per invariant 1 so the original text is kept. | Not started. Raised by Josh 2026-10-05. Versioned as TERSE-2 to prevent history confusion. | `config/sense_menu/providers/wiktionary-v1.json`; `docs/NOMENCLATURE.md` (provider, context) |
| **ACCORDION** | Design pass on whether to show rarer uses & nuances inline via an accordion on the mobile card back vs keeping them off-card in the existing modal (`#rareUsesModal`). Core motivation: hiding rare senses prevents learner confusion, avoids cluttering the card with unimportant meanings, and shields against inaccurate rare WSD assignments. Mobile space is heavily constrained by the active example sentence and Anki grading bar. A pure-UI scale wireframe mockup was produced comparing both: [rarer_uses_accordion_mockup.html](file:///Users/joshuathomasamar/.gemini/antigravity/brain/13564ff2-f373-41a9-881a-9d7c5bfb8bcf/rarer_uses_accordion_mockup.html). Dedicated follow-up chat to decide and implement if approved. | Not started. Wireframe drafted 2026-10-09. | `app/js/flashcards.js` (`renderSections`, `#rareUsesModal`); `app/css/style.css` (`.meanings-scroll`, `.meaning-row`); [Mockup](file:///Users/joshuathomasamar/.gemini/antigravity/brain/13564ff2-f373-41a9-881a-9d7c5bfb8bcf/rarer_uses_accordion_mockup.html) |
| **SEAM** | Audit Smart Skip's merging (Merge Lemmas): does it do what decision 0028 (verb forms, contractions, forms kept apart by a phrase built on them) and decision 0029 (noun plural/singular) say, does it give the same deck whether or not a set's senses have loaded, and does it work for every live language (es, pt, cs, fi, fr)? Audit before fixing, as UNISON-1 did: per language, a sample of merged and kept-apart cards, each with what it shows and what it should. Known so far (2026-10-10): (1) the phrase rule keeps very common forms apart on v23 (*está* for "dónde está", *es* for "es que"); Josh: the phrase list is the best there is, so tightening is later work, not this audit's fix; (2) a card can wear a lemma it is not filed under (pt *no* shows *em*; kept-apart *é* shows *ser*): the fix, titling from `lemmaGroupKey`, was held back on 2026-10-09 while the lists were stale and can go in now; (3) a few merge keys are phrases (pt *supremo* → "supremo tribunal federal", cs *navěky* → "na věky").  Reconcile the three leftover Open questions in decision 0024 against today's rules: whether the evidence-smoothing parameter α for frequency splitting is now superseded, whether the historical phrase keys (el pentágono, no obstante) still exist or need treatment, and whether providers without stable sense identifiers leave near-duplicate meanings under the content-signature fallback. Record each as resolved, superseded, still relevant with evidence, or unverified; do not revive an obsolete policy. | Not started. Requested by Josh 2026-10-10. Comes before CONVOY, so CONVOY rebuilds cs/fi/fr on checked rules. | `app/js/vocab.js` (`lemmaGroupKey`, `selectLemmaModeRepresentatives`, `buildCardFormModel`); `src/fluency/enrichments/card_rules.py`; `scripts/build_merge_exceptions.py`; `docs/decisions/0024-merged-lemma-policy-and-card-frequency.md`; `docs/decisions/0028-words-that-must-not-be-skipped.md`; `docs/decisions/0029-noun-number-merging.md`; `tests/app/test_card_rules_parity.py` |
| **CONVOY** | Bring Czech, Finnish and French up to the Spanish/Portuguese standard on everything, so no language lags the two Josh works on. Audit first: per language, list what es/pt have that it lacks, then rebuild each on the current engine and pipeline. Known gaps (2026-10-10): (1) none is on UNISON's single engine or the decision 0030 metadata contract; `scripts/check_stale_engine.py` says "OK" only because each is measured against its own old profile (cs-v21-1, fi-v21-1, fr-v7-1), and it reads es/pt as v22 from workspace `active.json` while the app serves v23; (2) Merge Lemmas lists were rebuilt as a quick patch (verbs merge again), but nouns stay separate because the plural/singular check (decision 0029) has only run for es/pt: 3,884 cs and 616 fi noun cards. Run `scripts/refresh_noun_merge_metadata.py` with a fresh Wiktionary menu, as pt did; (3) French is a 200-card stub (`fr-speech-v7-dual-metadata-v5-20260918`) whose senses carry no headwords, so Merge Lemmas has nothing to merge; (4) the phrase-lemma fix (11276edc) reaches them only when rebuilt. Czech reflexives stay with MIRROR-CS. | Not started. Requested by Josh 2026-10-10. es and pt remain the priority; this row keeps the rest level. `tests/app/test_merge_exceptions_current.py` blocks any deploy whose live deck lacks a current Merge Lemmas list, so each rebuilt deck needs its list rebuilt. | `docs/unison/PROGRESS.md` (what es/pt received); `docs/decisions/0029-noun-number-merging.md`; `docs/decisions/0030-sense-metadata-and-display-contract.md`; `scripts/check_stale_engine.py`; `scripts/build_merge_exceptions.py` |
| **TOUCHPOINT** | Check the app on an actual phone and verify progress moving between two real devices on the same profile. Review the swiping interaction itself: Josh reports grading swipes feel difficult and says this gesture dates from the app's original implementation roughly a year ago. Check required distance/speed, direction recognition, drag feedback, scrolling versus grading, accidental gestures, and ease of one-handed use; assess practical improvements from observed behaviour. Verify reveal/flip, both grading directions, and the first-swipe hint appearing and dismissing correctly. For progress sync, study on device A, confirm known/practice state and saved progress arrive on device B, then study on B and confirm they return to A; check profile selection, logout/return, and resume position. Keep physical-device observations separate from automated or emulated checks, record devices/browser versions, evidence and failures, and leave unavailable real-device checks explicitly unverified. These are remembered checks, not claims of an existing sync failure. | Not started. Requested by Josh 2026-10-10; follows the two unverified real-world checks from the 2026-10-08 UX audit, with swiping usability added. | `docs/UX_AUDIT_2026-10-08.md`; `docs/UX_AUDIT_IMPLEMENTATION_2026-10-08.md`; `app/js/flashcards.js` (touch/swipe handlers); `app/js/auth.js`; `app/js/sync-queue.js`; `app/js/progress.js`; `app/js/offline-db.js` |
| **ROLLCALL** | Re-audit the language readiness checklist against the current repository, workspace artifacts and app-served releases. The original candidate audit dates from 2026-09-26 and was last updated in git on 2026-09-27; do not assume its unchecked boxes are current. For every checklist item, record verified complete, still open, superseded, optional/eventual, or unverified, with dated evidence and exact release/artifact references. Cover every current language and reconcile older Spanish/French/Dutch/Italian/Finnish claims, including Czech and Portuguese which the original comparison omitted. Distinguish workspace active releases from what the app actually serves. Deliver an updated checklist and a concise list of genuine release blockers; assign actionable gaps to existing owners (DUTCH, CONVOY, SEAM, MIRROR-CS) or propose a new roadmap row, keeping Italian eventual under LATER.md. Audit only: no harvests, paid runs, downloads, rebuilds or activation. | Not started. Requested by Josh 2026-10-10 to revisit the old one-session checklist. | `docs/LANGUAGE_COMPLETION_CANDIDATE.md`; `docs/NL_FI_2000_RELEASE.md`; `docs/LANGUAGE_ONBOARDING.md`; `docs/INVARIANTS.md`; `app/config/`; workspace release manifests and review records; existing Open rows |
| **BRIDGE** | Add an option to Exclude Cognates that uses what the learner actually knows in another language they are learning, alongside the existing whole-known-language option. Start with Spanish and French, the two languages Josh is studying: a French word may be skipped when its matching Spanish word/meaning is already known in that learner's saved progress, and vice versa. Support the same approach for other pairs (e.g. Spanish and Portuguese), without assuming that studying a language means knowing its whole vocabulary. Reuse the existing cognate and sense-matching rules, preserving false-friend safeguards; define which recorded knowledge states qualify and how partial/sense-level knowledge maps across forms and merged cards. Make the setting understandable, keep skipped words available, and update eligibility as source-language knowledge changes without fabricating target-language study progress. Audit available progress and mapping data first, then build and verify the feature. French deck completion is needed for the full Spanish/French experience, but does not block building the feature and testing with available data; coordinate French release work with CONVOY. | Not started. Requested by Josh 2026-10-10. Initial pair Spanish/French; French deck completion is a rollout dependency, not a reason to defer implementation. | `app/js/cognates.js`; `app/js/knowledge.js`; `app/js/progress.js`; `app/js/progress-identity.js`; `app/js/fast-track-preferences.js`; `src/fluency/features/cognates.py`; `docs/decisions/0028-words-that-must-not-be-skipped.md`; CONVOY row |
| **DUTCH** | Ship the Dutch 2,000-card speech release: review the 122 ledger surfaces, finish the readiness checklist, activate. | Not started. Candidate `nl-speech-v1-2000x5-3-candidate` exists, inactive. | `docs/NL_FI_2000_RELEASE.md` → Dutch; `docs/LANGUAGE_COMPLETION_CANDIDATE.md` |

## Live today (2026-10-04)

| Mode | Release |
|---|---|
| Speech es, pt | `*-speech-v23-10000x30-slim` (reflexive-aware WSD, Wiktionary conjugations) |
| Speech cs | `cs-speech-v21-10000x30-slim` |
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
