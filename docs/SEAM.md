# SEAM — Spanish and Portuguese audit, 2026-10-10

Scope: current default es-speech-v24-headway-r4-10000x30-slim and
pt-speech-v24-headway-r2-10000x30-slim. Decisions 0028 and 0029 remain unchanged.
No source correction, WSD, harvest, paid call, progress write or production promotion.
Other languages are deferred to the later SEAM/CONVOY pass.

## Findings and fixes

1. **Kept-apart titles.** `buildCardFormModel` previously treated one shown
   headword as sufficient to title a card as merged, ignoring contractions,
   frozen expressions and noun proof. It now uses `lemmaGroupKey` for the
   displayed merged title and production answer. Citation metadata remains
   available for lookup and conjugation. pt no → em becomes no; frozen é → ser
   becomes é; es hay stays hay, while hacerlo and déjalo still join hacer/dejar.
   That model patch was included in concurrent commit 3a573294 while SEAM was
   working; subsequent SEAM commits preserve the loading and tutorial work.
2. **Search.** Before SEAM edits, staging 703ea3dc cold search for dejalo showed
   an Examples-only result and opened a Verb/dejar card still labelled
   “Examples only · no matched sense.” Flipping showed let him / let it /
   leave it, so the complete omission described in HEADWAY is not reproducible
   for déjalo on this newer build. The stale pre-hydration `entry.examplesOnly`
   flag nevertheless suppresses its English-first cue. The popup now derives
   that flag from the loaded menu; genuinely empty menus remain examples-only.
   Pending search-list rows no longer claim to have no meanings.
   Regression tests open both cold and warm retained search entries, including
   a changed active-cache pointer and a genuinely empty menu.
3. **Noun evidence lost in default rollout.** Both default merge files carried
   zero approved noun merges, unlike v23's supplemental files. Recovered
   evidence is compared against each final HEADWAY menu and release's complete
   source references by the existing refresh/builder. Unsupported/mismatching
   menus remain blocked. New supporting files restore 315 es / 334 pt plural
   forms under the full existing exception rules (319 / 338 raw approved
   non-self noun verdicts; four per language remain protected by other rules).
   Immutable releases are untouched. Cache-safe `*-seam-v1.json` files replace
   only the es/pt config pointers; estimator pools were regenerated for the
   same decisions. Saved September/October dictionary evidence is reused.
4. **Hydration discards supplemental proof.** A row shard could overwrite a
   current supplemental noun verdict with its older original verdict. Hydration
   now keeps the overlay, saving the hydrated original for release changes.
   Regression verifies cold/loaded equality and restoration when the overlay
   is removed. No progress identities or learner records are rewritten.

## Sample: actual cards and expected policy

| Language / cards | Before | After / expected |
|---|---|---|
| es hacerlo, déjalo | merge into hacer, dejar | unchanged; corrected verbal analyses remain |
| es fue; sé | kept apart | unchanged: ser/ir; saber/ser and no sé |
| es está; hay | kept apart but could wear estar/haber in merge mode | surface titles está/hay; frozen expressions still protect them |
| es al, del | kept apart | unchanged contractions |
| es años/año, semanas/semana | separate: missing complete-menu proof | merge with recovered identical complete-menu proof |
| es libro/libros; gato/gatos | separate | remain separate: ambiguous menu / number restriction or incomplete evidence |
| pt no, do | kept apart; no could wear em | kept apart, titles no/do |
| pt foi/fui; é/és | kept apart | unchanged multiple entries/lemmas; verb ser remains separate from noun é |
| pt vamos | kept apart | unchanged interjection/verb and expression protections |
| pt conta/contar | separate | unchanged noun conta and verb contar |
| pt poder/poderes; ser/seres | separate | unchanged mixed dictionary entries |
| pt anos/ano, horas/hora | separate: missing complete-menu proof | merge with checked complete menus |

Audit evidence: `../Fluency-Workspace/audits/seam/es-pt-audit.json`, enriched
menus, refresh reports and merge payloads in the same directory. It records
sample shown senses, noun reasons, and the complete 20,000-card key comparison.
Before supplemental recovery, all 20,000 loaded/cold keys matched and Python/JS
agreed. After recovery the same comparison still has zero mismatches: 3,879 es /
6,181 pt rows have nonempty keys; these are eligible rows, not unique cards.
This is deterministic policy parity, not a measured dictionary accuracy score.

## Decision 0024's remaining questions

- **α: superseded.** Decision 0028 keeps ambiguous surfaces apart instead of
  dividing their senses across lemma cards. Current `buildFilteredVocab` sums
  whole eligible surface counts and/or uses pooled example counts; no fractional
  splitting or smoothing parameter is needed.
- **Historical el pentágono / no obstante keys: resolved for es defaults.**
  Neither is a merge key; there are zero multiword es keys. pentágono remains
  a noun card and obstante is a phrase-only kept-apart card. Portuguese still
  has encima → em cima and supremo → supremo tribunal federal. These originate
  in ordinary adv/name headwords, not the app's expression routing. Record for
  HEADWAY source adjudication; do not broaden merging policy to disguise them.
  Other-language historical keys are deferred/unverified.
- **Content-signature near duplicates: still relevant but unverified for a
  provider without stable references.** Both current lexical providers supply
  source references on every shown lexical sense: zero missing lexical refs.
  There are 933 es / 811 pt fallback rows, confined to special/expression rows.
  Current `dedupeLemmaMenu` uses source_reference, then POS/translation/context
  without fuzzy collapsing. No evidence here establishes near-duplicate rates
  for a provider lacking identifiers; no new deduplication policy is introduced.

## Verification and remaining work

Initial combined app suite: 241 tests passed (27.868 seconds); subsequent new
asset-pair regression also passed. Staging deployment runs the final suite again.
Focused checks exercise title/production behaviour, Python/JS parity, cold/warm
search hydration, genuine missing menus, and noun-overlay release changes.

Staging browser review and final deployment identity are recorded below after
publication. The in-app browser crashed while switching languages during the
pre-change review; no learner progress was graded. This is an observation, not
an established app defect or a complete physical-device test.

Remaining: 79 es / 142 pt unresolved source surfaces stay with HEADWAY;
Portuguese contextual-tag filtering stays with TAGLINE. Broad cs/fi/fr auditing,
providers without stable references, and physical-phone/two-device checks are
not verified here. Phrase-list tightening remains deferred as instructed.

## Staging review, 2026-10-10

Build 246301a7 published successfully. Browser DOM confirms stamped
`main.js?v=stg-246301a7`. Cold Portuguese és search opened VERB ser with
“you are / you exist”, plus the noun é companion, without an Examples-only
card flag. Smart Skip with only Combine word forms enabled reports 6,871
cards, matching the full cold/loaded representative audit; its list shows
ano → anos/ano and hora → hora/horas. Screenshot:
`../Fluency-Workspace/audits/seam/staging-pt-es.jpg`.
Final build **b9467ace** is published and browser-reviewed in a fresh guest tab.
Cold és and dejalo result lists show their ranks without false Examples-only
labels. Opening and flipping shows “you are / you exist” and
“let him / let it / leave it”, respectively. Screenshots in the evidence folder:
`staging-pt-es-final.jpg` and `staging-es-dejalo-final.jpg`.
The final deployment suite passes all 243 app tests. All four hosted revised
merge/estimator assets match local bytes (`staging-bindings.json`). The normal
staging URL selects HEADWAY es r4 / pt r2; no candidate-query override is used.
The representative audit also verifies identical elected surface IDs and order
for full and cold menus: 7,729 es / 6,871 pt representatives before other filters.

An initial final-build reload took a long time to initialise in the in-app
browser. A fresh tab eventually loaded the correct stamped build without
warning/error console logs; the cause/duration was not measured. Earlier one-tab
crash and slow startup remain browser observations, not claims of a repaired app
problem. Physical phone and live two-device checks remain TOUCHPOINT's scope.
No production promotion was performed; Josh's approval is required.
