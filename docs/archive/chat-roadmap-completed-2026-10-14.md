# Completed roadmap and historical release snapshot

Archived 2026-10-14. The release snapshot below is historical, not a claim
about today’s served releases. Closed work stays closed; new follow-ups need
a new open row.

## Permanently paused

ACCORDION was paused permanently by Josh on 2026-10-12. The collapsible uses
lists from c94b87f8 remain; do not restart the design pass.

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

